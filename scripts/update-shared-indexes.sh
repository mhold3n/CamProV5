#!/usr/bin/env bash
set -euo pipefail

# CamProV5 — Update JetBrains Shared Indexes (versioned, atomic switch)
# Downloads assets from a manifest/URLs, extracts into versioned folders under INSTALL_ROOT,
# then updates the stable aliases (symlinks) to point to the new version.
#
# Usage:
#   bash scripts/update-shared-indexes.sh --version <v> [--manifest PATH] [--install-root PATH] \
#     [--set-current] [--rollback-on-fail] [--yes] [--quiet]
#
# Env overrides:
#   SHARED_INDEXES_MANIFEST

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION=""
MANIFEST="${SHARED_INDEXES_MANIFEST:-}"
OVERRIDE_INSTALL_ROOT=""
SET_CURRENT=false
ROLLBACK_ON_FAIL=false
YES=false
QUIET=false

DIRS=( ".shared-indexes" "ij-shared-indexes-tool-data" "ij-shared-indexes-tool-cli" )

log(){ $QUIET && return 0; echo "$@"; }
warn(){ echo "$@" >&2; }
err(){ echo "$@" >&2; exit 1; }
confirm(){ 
  $YES && return 0
  read -r -p "$1 [y/N]: " a || true
  a_lower="$(printf '%s' "${a:-}" | tr '[:upper:]' '[:lower:]')"
  [[ "$a_lower" == "y" || "$a_lower" == "yes" ]]
}

usage(){ cat <<EOF
Usage: $0 --version <v> [--manifest PATH] [--install-root PATH] [--set-current] [--rollback-on-fail] [--checksum SHA256] [--yes] [--quiet]

Options:
  --version v            Version label to use for directories (<dir>-<version>)
  --manifest PATH        YAML/JSON manifest defining assets (default: env or .junie/config/shared-indexes.yaml)
  --install-root PATH    Override INSTALL_ROOT (otherwise parent must be named 'github')
  --set-current          Update <dir> alias to point to <dir>-<version>
  --rollback-on-fail     Attempt rollback of alias changes if a later step fails
  --checksum SHA256      Expected checksum for single-URL use or to override manifest/sidecar
  --yes                  Assume 'yes' to confirmations
  --quiet                Reduce output
  -h, --help             Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2;;
    --manifest) MANIFEST="$2"; shift 2;;
    --install-root) OVERRIDE_INSTALL_ROOT="$2"; shift 2;;
    --set-current) SET_CURRENT=true; shift;;
    --rollback-on-fail) ROLLBACK_ON_FAIL=true; shift;;
    --checksum) CHECKSUM_CLI="$2"; shift 2;;
    --yes) YES=true; shift;;
    --quiet) QUIET=true; shift;;
    -h|--help) usage; exit 0;;
    *) usage; err "Unknown option: $1";;
  esac
done

[[ -n "$VERSION" ]] || { usage; err "--version is required"; }

# compute INSTALL_ROOT
if [[ -n "$OVERRIDE_INSTALL_ROOT" ]]; then
  INSTALL_ROOT="$(cd "$OVERRIDE_INSTALL_ROOT" && pwd)"; log "INSTALL_ROOT (override): $INSTALL_ROOT"
else
  PARENT="$(cd "$REPO_ROOT/.." && pwd)"; BASENAME="$(basename "$PARENT")"
  lower_basename="$(printf '%s' "$BASENAME" | tr '[:upper:]' '[:lower:]')"
  [[ "$lower_basename" == github ]] || err "Expected parent directory named 'github' but found '$BASENAME' (or use --install-root)"
  INSTALL_ROOT="$PARENT"; log "INSTALL_ROOT (detected): $INSTALL_ROOT"
fi
[[ -d "$INSTALL_ROOT" ]] || err "INSTALL_ROOT does not exist: $INSTALL_ROOT"

# default manifest
if [[ -z "$MANIFEST" && -f "$REPO_ROOT/.junie/config/shared-indexes.yaml" ]]; then MANIFEST="$REPO_ROOT/.junie/config/shared-indexes.yaml"; fi
[[ -n "$MANIFEST" && -f "$MANIFEST" ]] || warn "No manifest provided; update script will only switch aliases if versioned dirs already exist."

sha256_file(){ if command -v sha256sum>/dev/null; then sha256sum "$1"|awk '{print $1}'; else shasum -a 256 "$1"|awk '{print $1}'; fi }
_download(){ if command -v curl>/dev/null; then curl -fsSL "$1" -o "$2"; elif command -v wget>/dev/null; then wget -q "$1" -O "$2"; else err "curl/wget not available"; fi }
_fetch_sidecar_sha256(){
  local url="$1"
  local arc="$2"
  local side="${arc}.sha256"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${url}.sha256" -o "$side" || true
  elif command -v wget >/dev/null 2>&1; then
    wget -q "${url}.sha256" -O "$side" || true
  fi
  if [[ -f "$side" ]]; then awk '{print $1}' "$side"; fi
}
_verify_gpg(){ local arc="$1"; if command -v gpg >/dev/null 2>&1; then if [[ -f "${arc}.asc" ]]; then gpg --verify "${arc}.asc" "$arc" >/dev/null 2>&1 || err "GPG signature verification failed for $arc"; fi else warn "gpg not found; skipping signature verification for $arc"; fi }
_extract(){ local arc="$1" dst="$2"; mkdir -p "$dst"; case "$arc" in
  *.zip) unzip -q -o "$arc" -d "$dst";;
  *.tar.gz|*.tgz) tar -xzf "$arc" -C "$dst";;
  *.tar.zst|*.tzst) if tar --help|grep -q -- --zstd; then tar --zstd -xf "$arc" -C "$dst"; elif command -v zstd>/dev/null; then zstd -d < "$arc" | tar -xf - -C "$dst"; else err "zstd needed"; fi;;
  *.tar) tar -xf "$arc" -C "$dst";;
  *) err "Unsupported archive: $arc";; esac }

parse_manifest_assets(){ local file="$1"; [[ -f "$file" ]] || return 0
  local plat
  case "$(uname -s)-$(uname -m)" in
    Darwin-*) plat="darwin-x64";;
    Linux-*) plat="linux-x64";;
    MINGW*|MSYS*|CYGWIN*) plat="windows-x64";;
    *) plat="linux-x64";;
  esac
  local channel="${SHARED_INDEXES_CHANNEL:-stable}"
  local ver_token="$VERSION"; [[ -n "${SHARED_INDEXES_VERSION:-}" ]] && ver_token="$SHARED_INDEXES_VERSION"
  # Try platform-aware section first
  if grep -q '^platforms:' "$file"; then
    awk -v PLAT="$plat" '
      BEGIN{inplat=0;inassets=0;dir="";url="";sha=""}
      /^[[:space:]]*platforms:/ {inplat=0; next}
      { if ($0 ~ "^[[:space:]]*" PLAT ":") {inplat=1; next} }
      { if (inplat && $0 ~ /^[[:space:]]*assets:/) {inassets=1; next} }
      { if (inplat && inassets && $0 ~ /^[[:space:]]*-[[:space:]]*dir:/) {dir=$3} }
      { if (inplat && inassets && $0 ~ /^[[:space:]]*url:/) {url=$2} }
      { if (inplat && inassets && $0 ~ /^[[:space:]]*sha256:/) {sha=$2} }
      { if (inplat && inassets && dir!="" && url!="" && ($0 ~ /sha256:/ || $0 ~ /^[[:space:]]*-[[:space:]]*dir:/)) { print dir"|"url"|"sha; url=""; sha="" } }
    ' "$file" | sed 's/"//g' | sed "s/{{channel}}/${channel}/g" | sed "s/{{version}}/${ver_token}/g"
    return 0
  fi
  # Fallback: flat assets
  awk '
    BEGIN{d="";u="";s=""}
    /^[[:space:]]*-[[:space:]]*dir:/ { d=$3 }
    /^[[:space:]]*url:/ { u=$2 }
    /^[[:space:]]*sha256:/ { s=$2 }
    { if (d!="" && u!="" && ($0 ~ /sha256:/ || $0 ~ /^[[:space:]]*-[[:space:]]*dir:/)) { print d"|"u"|"s; u=""; s="" } }
    END{ if (d!="" && u!="") print d"|"u"|"s }
  ' "$file" | sed 's/"//g'
}

# Outputs expected markers as lines: dir|relative_path
parse_manifest_expected_files(){
  local file="$1"
  [[ -f "$file" ]] || return 0
  awk '
    BEGIN{ine=0;dir=""}
    /^[[:space:]]*expectedFiles:/ {ine=1; next}
    ine && /^[[:space:]]*[A-Za-z0-9._-]+:/ { dir=$1; sub(":","",dir); next }
    ine && /^[[:space:]]*-\s*/ { f=$2; print dir"|"f; next }
    ine && /^[[:space:]]*assets:/ {ine=0}
  ' "$file" | sed 's/"//g'
}

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# Note: removed associative array for macOS Bash 3.2 compatibility

if [[ -f "${MANIFEST:-}" ]]; then
  while IFS='|' read -r dir url sha; do
    [[ -n "$dir" && -n "$url" ]] || continue
    arc="$TMP/$(basename "$url")"; log "Downloading $dir: $url"; _download "$url" "$arc"
    # Integrity: precedence CHECKSUM_CLI > manifest sha > sidecar
    side=$(_fetch_sidecar_sha256 "$url" "$arc" || true)
    want="${CHECKSUM_CLI:-${sha:-${side:-}}}"
    if [[ -n "${want:-}" ]]; then calc=$(sha256_file "$arc"); [[ "$calc" == "$want" ]] || err "Checksum mismatch for $url"; fi
    _verify_gpg "$arc"
    verDir="$INSTALL_ROOT/${dir}-${VERSION}"; work="$TMP/${dir}-${VERSION}"
    mkdir -p "$work"; _extract "$arc" "$work"
    if ! find "$work" -mindepth 1 -print -quit >/dev/null; then err "Empty extraction for $dir"; fi
    # optional expected markers from manifest
    while IFS='|' read -r edir emark; do
      [[ "$edir" == "$dir" ]] || continue
      if [[ ! -e "$work/$emark" ]]; then warn "Expected marker missing for $dir: $emark"; fi
    done < <(parse_manifest_expected_files "$MANIFEST")
    # move into place atomically
    if [[ -e "$verDir" ]]; then
      warn "Version directory exists: $verDir"
    else
      mv "$work" "$verDir"
    fi
  done < <(parse_manifest_assets "$MANIFEST")
fi

# Switch aliases if requested (transactional with rollback)
if $SET_CURRENT; then
  ROLLBACK_ENABLED=$ROLLBACK_ON_FAIL
  set -E
  declare -a ALIASES PREV_TYPE PREV_TARGET BACKUP_PATH APPLIED
  idx=0
  rollback_handler(){
    warn "Update failed; initiating rollback..."
    for ((i=${#APPLIED[@]}-1; i>=0; i--)); do
      a="${ALIASES[$i]}"; pt="${PREV_TYPE[$i]}"; pv="${PREV_TARGET[$i]}"; bp="${BACKUP_PATH[$i]}"
      if [[ -L "$a" || -d "$a" ]]; then rm -rf "$a" || true; fi
      case "$pt" in
        symlink) ln -s "$pv" "$a" 2>/dev/null || true;;
        dir) mv "$bp" "$a" 2>/dev/null || true;;
        absent) ;; 
      esac
    done
    err "Rolled back alias updates due to failure"
  }
  if $ROLLBACK_ENABLED; then trap rollback_handler ERR; fi
  for d in "${DIRS[@]}"; do
    verDir="$INSTALL_ROOT/${d}-${VERSION}"
    [[ -d "$verDir" ]] || { warn "Missing versioned directory for $d ($verDir); skipping alias"; continue; }
    alias="$INSTALL_ROOT/$d"
    ALIASES[$idx]="$alias"; PREV_TYPE[$idx]="absent"; PREV_TARGET[$idx]=""; BACKUP_PATH[$idx]="";
    if [[ -L "$alias" ]]; then PREV_TYPE[$idx]="symlink"; PREV_TARGET[$idx]="$(readlink "$alias")"; rm -f "$alias";
    elif [[ -d "$alias" ]]; then PREV_TYPE[$idx]="dir"; BACKUP_PATH[$idx]="${alias}.__backup_$(date +%s%N)"; mv "$alias" "${BACKUP_PATH[$idx]}"; PREV_TARGET[$idx]="${BACKUP_PATH[$idx]}"; fi
    ln -s "${d}-${VERSION}" "$alias"
    APPLIED[$idx]="$alias"; ((idx++))
    log "Alias updated: $d -> ${d}-${VERSION}"
  done
  # success: cleanup backups
  if ((${#BACKUP_PATH[@]})); then for bp in "${BACKUP_PATH[@]}"; do [[ -n "$bp" ]] && rm -rf "$bp" || true; done; fi
  trap - ERR
fi

log "Update complete for version $VERSION"
