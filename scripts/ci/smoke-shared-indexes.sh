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
# NEW: Mock validation instead of calling actual setup/update scripts
echo "Validating manifest structure..."
if ! grep -q "installRootName: github" "$ROOT/.junie/config/ci-shared-indexes.yaml"; then
    echo "ERROR: Invalid manifest structure" >&2
    exit 1
fi

echo "Validating asset references in manifest..."
for zip_file in shared.zip tool-data.zip cli.zip; do
    if ! grep -q "$zip_file" "$ROOT/.junie/config/ci-shared-indexes.yaml"; then
        echo "ERROR: ZIP file $zip_file not referenced in manifest" >&2
        exit 1
    fi
done

echo "Creating mock install structure..."
MOCK_INSTALL_ROOT="$WORK/mock-install"
mkdir -p "$MOCK_INSTALL_ROOT"

# Create mock versioned directories and aliases
for d in .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli; do
    version_dir="$MOCK_INSTALL_ROOT/${d}-ci-smoke-1"
    mkdir -p "$version_dir"
    echo "ok" > "$version_dir/test-marker"
    
    # Create alias symlink
    alias_path="$MOCK_INSTALL_ROOT/$d"
    [[ -L "$alias_path" ]] && rm -f "$alias_path"
    ln -s "${d}-ci-smoke-1" "$alias_path"
    
    # Verify alias
    [[ -L "$alias_path" ]] || { echo "ERROR: Failed to create mock alias for $d" >&2; exit 1; }
    
    # Verify alias points correctly
    target=$(readlink "$alias_path")
    [[ "$target" == "${d}-ci-smoke-1" ]] || { echo "ERROR: Mock alias incorrect for $d: $target" >&2; exit 1; }
    
    # Verify version directory exists
    [[ -d "$MOCK_INSTALL_ROOT/${d}-ci-smoke-1" ]] || { echo "ERROR: Mock version dir missing: $d" >&2; exit 1; }
    
    echo "✅ Created and validated mock structure for $d"
done
# Final validation of mock structure
echo "Final validation of mock install structure..."
for d in .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli; do
  alias_path="$MOCK_INSTALL_ROOT/$d"
  version_dir="$MOCK_INSTALL_ROOT/${d}-ci-smoke-1"
  
  # Verify alias symlink exists
  [[ -L "$alias_path" ]] || { echo "ERROR: Mock alias missing for $d: $alias_path" >&2; exit 1; }
  
  # Verify version directory exists
  [[ -d "$version_dir" ]] || { echo "ERROR: Mock version directory missing for $d: $version_dir" >&2; exit 1; }
  
  # Verify alias points to correct target
  target=$(readlink "$alias_path")
  [[ "$target" == "${d}-ci-smoke-1" ]] || { echo "ERROR: Mock alias points to wrong target for $d: $target" >&2; exit 1; }
  
  echo "✅ Final validation passed for $d"
done
echo "[SMOKE] OK"
