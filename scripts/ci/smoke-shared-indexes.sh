#!/usr/bin/env bash
set -euo pipefail
# CI smoke: create tiny archives, write manifest using file:// URLs, run setup and update scripts
ROOT="$(pwd)"
WORK="$ROOT/.smoke-shared-indexes"
rm -rf "$WORK" && mkdir -p "$WORK/artifacts" "$ROOT/.junie/config"
# create tiny content
mkdir -p "$WORK/content/.shared-indexes" "$WORK/content/ij-shared-indexes-tool-data" "$WORK/content/ij-shared-indexes-tool-cli/bin"
echo "ok" > "$WORK/content/.shared-indexes/index.info"
# Add minimal placeholder so zip has content
echo "ok" > "$WORK/content/ij-shared-indexes-tool-data/.keep"
echo "ok" > "$WORK/content/ij-shared-indexes-tool-cli/bin/ijSharedIndexesTool"
# zip them with error handling
echo "Creating ZIP files..."
( cd "$WORK/content/.shared-indexes" && zip -qr "$WORK/artifacts/shared.zip" . ) || { echo "Failed to create shared.zip" >&2; exit 1; }
echo "Created shared.zip"
( cd "$WORK/content/ij-shared-indexes-tool-data" && zip -qr "$WORK/artifacts/tool-data.zip" . ) || { echo "Failed to create tool-data.zip" >&2; exit 1; }
echo "Created tool-data.zip"
( cd "$WORK/content/ij-shared-indexes-tool-cli" && zip -qr "$WORK/artifacts/cli.zip" . ) || { echo "Failed to create cli.zip" >&2; exit 1; }
echo "Created cli.zip"

sha() { 
  local file="$1"
  [[ -f "$file" ]] || { echo "File not found for hash calculation: $file" >&2; exit 1; }
  if command -v sha256sum >/dev/null; then 
    sha256sum "$file"|awk '{print $1}'
  else 
    shasum -a 256 "$file"|awk '{print $1}'
  fi
}
SHA_SHARED=$(sha "$WORK/artifacts/shared.zip")
SHA_DATA=$(sha "$WORK/artifacts/tool-data.zip")
SHA_CLI=$(sha "$WORK/artifacts/cli.zip")

# Create the .sha256 checksum files that setup/update scripts expect
echo "Creating checksum files for compatibility..."
echo "$SHA_SHARED" > "$WORK/artifacts/shared.zip.sha256"
echo "$SHA_DATA" > "$WORK/artifacts/tool-data.zip.sha256" 
echo "$SHA_CLI" > "$WORK/artifacts/cli.zip.sha256"

# Verify checksum files were created
for checksum_file in "$WORK/artifacts/"*.sha256; do
    if [[ -f "$checksum_file" ]]; then
        echo "Created checksum file: $(basename "$checksum_file")"
    else
        echo "ERROR: Failed to create checksum file: $checksum_file" >&2
        exit 1
    fi
done

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
IR="$(cd "$ROOT/.." && pwd)"
bash scripts/setup-shared-indexes.sh --install-root "$IR" --download-manifest "$ROOT/.junie/config/ci-shared-indexes.yaml" --yes --quiet
# Run update to version ci-smoke-1
bash scripts/update-shared-indexes.sh --install-root "$IR" --manifest "$ROOT/.junie/config/ci-shared-indexes.yaml" --version ci-smoke-1 --set-current --rollback-on-fail --yes --quiet
# Validate aliases
for d in .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli; do
  [[ -L "$ROOT/$d" ]] || { echo "alias missing $d" >&2; exit 1; }
  tgt1=$(readlink "$ROOT/$d")
  expected1="$IR/$d"
  [[ "$tgt1" == "$expected1" ]] || { echo "repo link not pointing to install-root alias for $d: $tgt1 (expected $expected1)" >&2; exit 1; }
  [[ -L "$IR/$d" ]] || { echo "install-root alias missing for $d: $IR/$d" >&2; exit 1; }
  tgt2=$(readlink "$IR/$d")
  [[ "$tgt2" == "${d}-ci-smoke-1" ]] || { echo "install-root alias not pointing to version for $d: $tgt2" >&2; exit 1; }
  [[ -d "$IR/${d}-ci-smoke-1" ]] || { echo "version dir missing: $IR/${d}-ci-smoke-1" >&2; exit 1; }
done
echo "[SMOKE] OK"
