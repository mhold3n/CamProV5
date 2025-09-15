#!/usr/bin/env bash
set -euo pipefail
# Full shared-indexes suite: reset state, run smoke (creates artifacts, setup+update to ci-smoke-1),
# then perform another update to ci-smoke-2 and verify final aliases. Intended to be idempotent.
#
# Usage:
#   bash scripts/run-shared-indexes-suite.sh [--install-root PATH] [--verbose]
#
# Notes:
# - INSTALL_ROOT defaults to the parent directory of the repo (same as other scripts),
#   but you can override for local testing with --install-root.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OVERRIDE_INSTALL_ROOT=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-root) OVERRIDE_INSTALL_ROOT="$2"; shift 2;;
    --verbose|-v) VERBOSE=true; shift;;
    -h|--help)
      cat <<EOF
Usage: $0 [--install-root PATH] [--verbose]

This resets shared-indexes state in the repo and install-root, then runs the full
smoke test (setup + update to ci-smoke-1) and performs an additional update to
ci-smoke-2 verifying aliases.
EOF
      exit 0;;
    *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done

if [[ -n "$OVERRIDE_INSTALL_ROOT" ]]; then
  IR="$(cd "$OVERRIDE_INSTALL_ROOT" && pwd)"
else
  IR="$(cd "$ROOT/.." && pwd)"
fi

log(){ $VERBOSE && echo "$@" || true; }

# 1) Reset any previous state
log "[RESET] Repo: $ROOT"
log "[RESET] Install root: $IR"
# Clean repo links/dirs
for d in .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli; do
  if [[ -L "$ROOT/$d" || -d "$ROOT/$d" ]]; then
    rm -rf "$ROOT/$d" || true
    log "Removed repo path: $d"
  fi
  # Also remove any odd leftovers like 'dir:' from earlier runs
  if [[ -d "$ROOT/dir:" ]]; then rm -rf "$ROOT/dir:"; fi
  if [[ -d "$ROOT/dir:-ci-smoke-1" ]]; then rm -rf "$ROOT/dir:-ci-smoke-1"; fi
done
# Clean install-root aliases and any ci-smoke-* version dirs
for d in .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli; do
  if [[ -L "$IR/$d" || -d "$IR/$d" ]]; then rm -rf "$IR/$d" || true; log "Removed install-root alias: $IR/$d"; fi
  for vd in "$IR/${d}-ci-smoke-"*; do
    [[ -e "$vd" ]] || continue
    rm -rf "$vd" || true
    log "Removed version dir: $vd"
  done
done
# Clean working dirs and CI manifest
rm -rf "$ROOT/.smoke-shared-indexes" "$ROOT/.junie/config/ci-shared-indexes.yaml" 2>/dev/null || true

# 2) Run the smoke test (builds tiny archives, runs setup+update to ci-smoke-1, validates aliases)
log "[RUN] smoke-shared-indexes.sh"
if $VERBOSE; then
  bash -x "$ROOT/scripts/ci/smoke-shared-indexes.sh"
else
  bash "$ROOT/scripts/ci/smoke-shared-indexes.sh"
fi

# 3) Additional verification: run setup --verify to probe targets via repo links
log "[VERIFY] setup --verify"
bash "$ROOT/scripts/setup-shared-indexes.sh" --install-root "$IR" --verify --yes --quiet

# 4) Update to a new version (ci-smoke-2) using the same CI manifest and verify aliases
log "[RUN] update to ci-smoke-2"
bash "$ROOT/scripts/update-shared-indexes.sh" \
  --install-root "$IR" \
  --manifest "$ROOT/.junie/config/ci-shared-indexes.yaml" \
  --version ci-smoke-2 \
  --set-current \
  --rollback-on-fail \
  --yes \
  --quiet

# 5) Verify aliases now point to -ci-smoke-2 and version dirs exist
for d in .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli; do
  [[ -L "$ROOT/$d" ]] || { echo "alias missing in repo: $d" >&2; exit 1; }
  tgt1=$(readlink "$ROOT/$d"); expected1="$IR/$d"
  [[ "$tgt1" == "$expected1" ]] || { echo "repo link not pointing to install-root alias for $d: $tgt1 (expected $expected1)" >&2; exit 1; }
  [[ -L "$IR/$d" ]] || { echo "install-root alias missing for $d: $IR/$d" >&2; exit 1; }
  tgt2=$(readlink "$IR/$d")
  [[ "$tgt2" == "${d}-ci-smoke-2" ]] || { echo "install-root alias not pointing to version for $d: $tgt2" >&2; exit 1; }
  [[ -d "$IR/${d}-ci-smoke-2" ]] || { echo "version dir missing: $IR/${d}-ci-smoke-2" >&2; exit 1; }
  # markers
  if [[ "$d" == ".shared-indexes" ]]; then
    [[ -f "$IR/${d}-ci-smoke-2/index.info" ]] || { echo "marker missing: index.info in $IR/${d}-ci-smoke-2" >&2; exit 1; }
  fi
  if [[ "$d" == "ij-shared-indexes-tool-cli" ]]; then
    [[ -f "$IR/${d}-ci-smoke-2/bin/ijSharedIndexesTool" ]] || { echo "marker missing: cli tool in $IR/${d}-ci-smoke-2" >&2; exit 1; }
  fi
done

echo "[SUITE] OK — shared indexes setup, update, and smoke verification passed"
