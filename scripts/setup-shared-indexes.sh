#!/usr/bin/env bash
set -euo pipefail

# CamProV5 — Shared Indexes setup (Option A: repository-local symlinks)
# Now supports manifest download/population, checksum verification, verify/untrack flags,
# and quiet/yes UX improvements.
#
# Usage:
#   bash scripts/setup-shared-indexes.sh [--install-root PATH] [--create-missing] \
#       [--download-manifest PATH] [--download-url URL]... [--checksum SHA256] \
#       [--verify] [--untrack] [--yes] [--quiet]
#
# Env overrides:
#   SHARED_INDEXES_MANIFEST   default path to manifest if --download-manifest not given

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OVERRIDE_INSTALL_ROOT=""
CREATE_MISSING=false
DOWNLOAD_MANIFEST="${SHARED_INDEXES_MANIFEST:-}"
DOWNLOAD_URLS=()
CHECKSUM_OVR=""
VERIFY=false
UNTRACK=false
YES=false
QUIET=false
DRY_RUN=false

# Directories to manage
DIRS=(
  ".shared-indexes"
  "ij-shared-indexes-tool-data"
  "ij-shared-indexes-tool-cli"
)

log() { $QUIET && return 0; echo "$@"; }
warn() { echo "$@" >&2; }
err() { echo "$@" >&2; exit 1; }
confirm() {
  $YES && return 0
  read -r -p "$1 [y/N]: " ans || true
  ans_lower="$(printf '%s' "${ans:-}" | tr '[:upper:]' '[:lower:]')"
  [[ "$ans_lower" == "y" || "$ans_lower" == "yes" ]]
}
usage() {
  cat <<EOF
Usage: $0 [--install-root PATH] [--create-missing] [--download-manifest PATH] [--download-url URL]... [--checksum SHA256] [--verify] [--untrack] [--yes] [--quiet] [--dry-run]

Options:
  --install-root PATH     Override INSTALL_ROOT directory (skips 'github' name check)
  --create-missing        Create missing target directories under INSTALL_ROOT
  --download-manifest F   YAML/JSON manifest describing assets to fetch (default: env SHARED_INDEXES_MANIFEST or .junie/config/shared-indexes.yaml if present)
  --download-url URL      Additional asset URL(s) to fetch (placed under INSTALL_ROOT; requires manifest or naming convention)
  --checksum SHA256       Expected SHA256 for a single URL (when one --download-url is used)
  --verify                Perform dereference read-probe of targets and report
  --untrack               Run 'git rm -r --cached' on protected dirs (guarded)
  --yes                   Assume 'yes' for confirmations
  --quiet                 Reduce output
  -h, --help              Show this help
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-root) [[ $# -ge 2 ]] || { usage; err "--install-root requires a path"; }; OVERRIDE_INSTALL_ROOT="$2"; shift 2 ;;
    --create-missing) CREATE_MISSING=true; shift ;;
    --download-manifest) [[ $# -ge 2 ]] || { usage; err "--download-manifest requires a file"; }; DOWNLOAD_MANIFEST="$2"; shift 2 ;;
    --download-url) [[ $# -ge 2 ]] || { usage; err "--download-url requires a URL"; }; DOWNLOAD_URLS+=("$2"); shift 2 ;;
    --checksum) [[ $# -ge 2 ]] || { usage; err "--checksum requires a value"; }; CHECKSUM_OVR="$2"; shift 2 ;;
    --verify) VERIFY=true; shift ;;
    --untrack) UNTRACK=true; shift ;;
    --yes) YES=true; shift ;;
    --quiet) QUIET=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; err "Unknown option: $1" ;;
  esac
done

# Default manifest path if not provided
if [[ -z "$DOWNLOAD_MANIFEST" && -f "$REPO_ROOT/.junie/config/shared-indexes.yaml" ]]; then
  DOWNLOAD_MANIFEST="$REPO_ROOT/.junie/config/shared-indexes.yaml"
fi

log "== CamProV5 Shared Indexes Setup =="
log "REPO_ROOT: $REPO_ROOT"

# Compute INSTALL_ROOT
if [[ -n "$OVERRIDE_INSTALL_ROOT" ]]; then
  INSTALL_ROOT="$(cd "$OVERRIDE_INSTALL_ROOT" && pwd)"
  log "INSTALL_ROOT (override): $INSTALL_ROOT"
else
  PARENT="$(cd "$REPO_ROOT/.." && pwd)"
  BASENAME="$(basename "$PARENT")"
  lower_basename="$(printf '%s' "$BASENAME" | tr '[:upper:]' '[:lower:]')"
  if [[ "$lower_basename" != "github" ]]; then
    err "Expected repo to be under a parent directory named 'github', but found '$BASENAME'. Move repo or use --install-root."
  fi
  INSTALL_ROOT="$PARENT"
  log "INSTALL_ROOT (detected): $INSTALL_ROOT"
fi
[[ -d "$INSTALL_ROOT" ]] || err "INSTALL_ROOT does not exist: $INSTALL_ROOT"

# Helpers
_is_link() { [[ -L "$1" ]]; }
sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}';
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}';
  else err "No sha256 tool found (sha256sum or shasum)"; fi
}
_download() { # url dest
  if $DRY_RUN; then log "[dry-run] download $1 -> $2"; return 0; fi
  if command -v curl >/dev/null 2>&1; then curl -fsSL "$1" -o "$2";
  elif command -v wget >/dev/null 2>&1; then wget -q "$1" -O "$2";
  else err "Neither curl nor wget is available"; fi
}
_extract() { # archive dest_dir
  local arc="$1"; local dst="$2"; if $DRY_RUN; then log "[dry-run] extract $arc -> $dst"; return 0; fi; mkdir -p "$dst"
  case "$arc" in
    *.zip) command -v unzip >/dev/null 2>&1 || err "unzip not available"; unzip -q -o "$arc" -d "$dst" ;;
    *.tar.gz|*.tgz) tar -xzf "$arc" -C "$dst" ;;
    *.tar.zst|*.tzst)
      if tar --help 2>/dev/null | grep -q -- '--zstd'; then tar --zstd -xf "$arc" -C "$dst"; 
      elif command -v zstd >/dev/null 2>&1; then zstd -d < "$arc" | tar -xf - -C "$dst"; else err "zstd support is required to extract $arc"; fi ;;
    *.tar) tar -xf "$arc" -C "$dst" ;;
    *) err "Unsupported archive format: $arc" ;;
  esac
}

# Manifest parsers
# Outputs assets as lines: dir|url|sha256
parse_manifest_assets() {
  local file="$1"; [[ -f "$file" ]] || return 0
  case "$file" in
    *.json)
      if command -v python3 >/dev/null 2>&1; then
        python3 - "$file" <<'PY'
import json,sys
p=sys.argv[1]
with open(p,'r',encoding='utf-8') as f:
    j=json.load(f)
assets=j.get('assets',[])
for a in assets:
    d=a.get('dir'); u=a.get('url'); s=a.get('sha256','')
    if d and u:
        print(f"{d}|{u}|{s}")
PY
      else
        echo "JSON manifest provided but python3 not available" >&2; return 1
      fi
      ;;
    *)
      awk '
        BEGIN{dir="";url="";sha=""}
        /^\s*-\s*dir:/ { gsub(/\r/,"",$0); dir=$2 }
        /^\s*url:/ { url=$2 }
        /^\s*sha256:/ { sha=$2 }
        { if (dir!="" && url!="" && ($0 ~ /sha256:/ || $0 ~ /^\s*-\s*dir:/)) { print dir"|"url"|"sha; url=""; sha="" } }
        END{ if (dir!="" && url!="") print dir"|"url"|"sha" }
      ' "$file" | sed 's/"//g'
      ;;
  esac
}
# Outputs expected markers as lines: dir|relative_path
parse_manifest_expected_files() {
  local file="$1"; [[ -f "$file" ]] || return 0
  case "$file" in
    *.json)
      if command -v python3 >/dev/null 2>&1; then
        python3 - "$file" <<'PY'
import json,sys
p=sys.argv[1]
with open(p,'r',encoding='utf-8') as f:
    j=json.load(f)
exp=j.get('expectedFiles',{})
for d,files in exp.items():
    for f in files or []:
        print(f"{d}|{f}")
PY
      else
        return 0
      fi
      ;;
    *)
      awk '
        BEGIN{exp=0;dir=""}
        /^\s*expectedFiles:/ {exp=1; next}
        exp && /^\s*[A-Za-z0-9._-]+:/ { dir=$1; sub(":","",dir); gsub(/^\s+|\s+$/,"",dir); next }
        exp && /^\s*-\s*/ { f=$2; print dir"|"f; next }
        exp && /^\s*assets:/ {exp=0}
      ' "$file" | sed 's/"//g'
      ;;
  esac
}

any_target_exists=false
for d in "${DIRS[@]}"; do [[ -d "$INSTALL_ROOT/$d" ]] && any_target_exists=true; done

# If no targets exist and manifest/urls provided, download & extract
if [[ "$any_target_exists" == false && ( -n "${DOWNLOAD_MANIFEST}" || ${#DOWNLOAD_URLS[@]} -gt 0 ) ]]; then
  log "No targets present under INSTALL_ROOT; attempting to download assets..."
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT

  # From manifest
  if [[ -n "$DOWNLOAD_MANIFEST" ]]; then
    while IFS='|' read -r dir url sha; do
      [[ -n "$dir" && -n "$url" ]] || continue
      log "Downloading $dir from $url"
      arc="$tmpdir/$(basename "$url")"; _download "$url" "$arc"
      if [[ -n "$sha" && "$sha" != "sha" ]]; then
        calc=$(sha256_file "$arc"); [[ "$calc" == "$sha" ]] || err "Checksum mismatch for $url"
      fi
      dest="$INSTALL_ROOT/$dir"; mkdir -p "$dest"; _extract "$arc" "$dest"
      # basic validation: has at least one file/dir
      if ! $DRY_RUN; then
        if ! find "$dest" -mindepth 1 -print -quit >/dev/null; then err "Extraction produced empty directory: $dest"; fi
        # optional expected markers from manifest
        while IFS='|' read -r edir emark; do
          [[ "$edir" == "$dir" ]] || continue
          if [[ ! -e "$dest/$emark" ]]; then warn "Expected marker missing for $dir: $emark"; fi
        done < <(parse_manifest_expected_files "$DOWNLOAD_MANIFEST")
      fi
    done < <(parse_manifest_assets "$DOWNLOAD_MANIFEST")
  fi
  # From single URL fallback
  if [[ ${#DOWNLOAD_URLS[@]} -eq 1 ]]; then
    url="${DOWNLOAD_URLS[0]}"; arc="$tmpdir/$(basename "$url")"; _download "$url" "$arc"
    if [[ -n "$CHECKSUM_OVR" ]]; then calc=$(sha256_file "$arc"); [[ "$calc" == "$CHECKSUM_OVR" ]] || err "Checksum mismatch for $url"; fi
    # Require naming convention dir-archive? fallback to .shared-indexes
    dest="$INSTALL_ROOT/.shared-indexes"; mkdir -p "$dest"; _extract "$arc" "$dest"
  elif [[ ${#DOWNLOAD_URLS[@]} -gt 1 ]]; then
    warn "Multiple --download-url provided but no mapping; please use --download-manifest. Skipping extra URLs."
  fi
fi

# Phase 2: Migrate any in-repo copies and create links
for d in "${DIRS[@]}"; do
  SRC="$REPO_ROOT/$d"; TGT="$INSTALL_ROOT/$d"
  if [[ -e "$SRC" && ! -L "$SRC" ]]; then
    if [[ -d "$SRC" ]]; then
      if ! $YES && ! confirm "Move existing repo directory '$d' to INSTALL_ROOT?"; then warn "Skipped moving $d"; else
        if $DRY_RUN; then log "[dry-run] move $SRC -> $TGT"; else
          log "Moving real directory from repo: $d -> INSTALL_ROOT"; mkdir -p "$TGT"
          shopt -s dotglob nullglob; mv "$SRC"/* "$TGT"/ 2>/dev/null || true; shopt -u dotglob nullglob; rmdir "$SRC" || true
        fi
      fi
    else
      if $DRY_RUN; then log "[dry-run] remove file $SRC"; else log "Removing non-link file in repo: $d"; rm -f "$SRC"; fi
    fi
  elif [[ -L "$SRC" || -f "$SRC" ]]; then if $DRY_RUN; then log "[dry-run] remove existing $SRC"; else rm -rf "$SRC"; fi; fi

  if [[ ! -d "$TGT" ]]; then
    if $CREATE_MISSING; then if $DRY_RUN; then log "[dry-run] mkdir -p $TGT"; else log "Creating missing target directory: $TGT"; mkdir -p "$TGT"; fi; else warn "Target missing (will link anyway): $TGT"; fi
  fi

  REL_TO_INSTALL="../$(basename "$INSTALL_ROOT")"; LINK_TARGET="$REL_TO_INSTALL/$d"
  if $DRY_RUN; then log "[dry-run] link $REPO_ROOT/$d -> $LINK_TARGET"; else log "Linking $d -> $LINK_TARGET"; ln -snf "$LINK_TARGET" "$REPO_ROOT/$d"; fi

  if ! $DRY_RUN; then
    if _is_link "$REPO_ROOT/$d"; then $QUIET || echo "OK: $d is a symlink"; else err "Failed to create symlink for $d"; fi
  fi

  if $VERIFY && ! $DRY_RUN; then
    if [[ -d "$TGT" ]]; then any=$(find "$TGT" -type f -maxdepth 1 -print -quit 2>/dev/null || true); if [[ -n "${any:-}" ]]; then head -c 0 "$REPO_ROOT/$d/$(basename "$any")" >/dev/null 2>&1 || true; else warn "Target appears empty: $TGT"; fi fi
  fi

done

if $UNTRACK; then
  # ensure repo clean for index operations
  if ! git diff --quiet || ! git diff --cached --quiet; then warn "Working tree not clean; skipping --untrack. Commit or stash changes and rerun with --untrack"; else
    if $YES || confirm "Run git rm -r --cached on protected directories?"; then
      if $DRY_RUN; then
        log "[dry-run] git rm -r --cached .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli && git commit -m 'chore(shared-indexes): untrack protected directories'"
      else
        git rm -r --cached .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli || true
        git commit -m "chore(shared-indexes): untrack protected directories" || true
      fi
    fi
  fi
fi

$QUIET || cat <<SUMMARY

Summary:
- Repo links created/updated for: ${DIRS[*]}
- INSTALL_ROOT: $INSTALL_ROOT
- Use a manifest to populate targets: --download-manifest .junie/config/shared-indexes.yaml
- If these folders were previously tracked in Git, you can use --untrack (with --yes) to remove from index.

Next steps:
- Start IntelliJ IDEA and open the project. Indexing should use shared indexes located in INSTALL_ROOT.
- If the IDE cached old paths, consider File > Invalidate Caches / Restart once.
SUMMARY
