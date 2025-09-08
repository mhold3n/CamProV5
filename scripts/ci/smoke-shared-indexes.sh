#!/usr/bin/env bash
set -euo pipefail
# CI smoke: create tiny archives, write manifest using file:// URLs, run setup and update scripts
ROOT="$(pwd)"
WORK="$ROOT/.smoke-shared-indexes"
rm -rf "$WORK" && mkdir -p "$WORK/artifacts" "$ROOT/.junie/config"
# create tiny content
mkdir -p "$WORK/content/.shared-indexes" "$WORK/content/ij-shared-indexes-tool-data" "$WORK/content/ij-shared-indexes-tool-cli/bin"
echo "ok" > "$WORK/content/.shared-indexes/index.info"
echo "ok" > "$WORK/content/ij-shared-indexes-tool-cli/bin/ijSharedIndexesTool"
# zip them
( cd "$WORK/content/.shared-indexes" && zip -qr "$WORK/artifacts/shared.zip" . )
( cd "$WORK/content/ij-shared-indexes-tool-data" && zip -qr "$WORK/artifacts/tool-data.zip" . )
( cd "$WORK/content/ij-shared-indexes-tool-cli" && zip -qr "$WORK/artifacts/cli.zip" . )
sha() { if command -v sha256sum >/dev/null; then sha256sum "$1"|awk '{print $1}'; else shasum -a 256 "$1"|awk '{print $1}'; fi }
SHA_SHARED=$(sha "$WORK/artifacts/shared.zip")
SHA_DATA=$(sha "$WORK/artifacts/tool-data.zip")
SHA_CLI=$(sha "$WORK/artifacts/cli.zip")
# manifest
cat > "$ROOT/.junie/config/ci-shared-indexes.yaml" <<YAML
installRootName: github
expectedFiles:
  .shared-indexes:
    - index.info
  ij-shared-indexes-tool-cli:
    - bin/ijSharedIndexesTool
assets:
  - dir: .shared-indexes
    url: file://$WORK/artifacts/shared.zip
    sha256: $SHA_SHARED
  - dir: ij-shared-indexes-tool-data
    url: file://$WORK/artifacts/tool-data.zip
    sha256: $SHA_DATA
  - dir: ij-shared-indexes-tool-cli
    url: file://$WORK/artifacts/cli.zip
    sha256: $SHA_CLI
YAML
# Run setup to populate and link (INSTALL_ROOT is parent named github in CI? override to workspace)
bash scripts/setup-shared-indexes.sh --install-root "$ROOT" --download-manifest "$ROOT/.junie/config/ci-shared-indexes.yaml" --yes --quiet
# Run update to version ci-smoke-1
bash scripts/update-shared-indexes.sh --install-root "$ROOT" --manifest "$ROOT/.junie/config/ci-shared-indexes.yaml" --version ci-smoke-1 --set-current --rollback-on-fail --yes --quiet
# Validate aliases
for d in .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli; do
  [[ -L "$ROOT/$d" ]] || { echo "alias missing $d" >&2; exit 1; }
  tgt=$(readlink "$ROOT/$d")
  [[ "$tgt" == "$d-ci-smoke-1" ]] || { echo "alias not pointing to version for $d: $tgt" >&2; exit 1; }
  [[ -d "$ROOT/${d}-ci-smoke-1" ]] || { echo "version dir missing: $ROOT/${d}-ci-smoke-1" >&2; exit 1; }
done
echo "[SMOKE] OK"
