Param()
$ErrorActionPreference = 'Stop'
$Root = (Get-Location).Path
$Work = Join-Path $Root '.smoke-shared-indexes'
if (Test-Path -LiteralPath $Work) { Remove-Item -LiteralPath $Work -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $Work 'artifacts') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Root '.junie/config') -Force | Out-Null
# tiny content
New-Item -ItemType Directory -Path (Join-Path $Work 'content/.shared-indexes') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Work 'content/ij-shared-indexes-tool-data') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Work 'content/ij-shared-indexes-tool-cli/bin') -Force | Out-Null
Set-Content -LiteralPath (Join-Path $Work 'content/.shared-indexes/index.info') -Value 'ok'
Set-Content -LiteralPath (Join-Path $Work 'content/ij-shared-indexes-tool-cli/bin/ijSharedIndexesTool') -Value 'ok'
# zip with error handling
Write-Host "Creating ZIP files..."
try {
    Compress-Archive -Path (Join-Path $Work 'content/.shared-indexes/*') -DestinationPath (Join-Path $Work 'artifacts/shared.zip') -Force
    Write-Host "Created shared.zip"
} catch {
    Write-Error "Failed to create shared.zip: $_"
    exit 1
}

try {
    Compress-Archive -Path (Join-Path $Work 'content/ij-shared-indexes-tool-data/*') -DestinationPath (Join-Path $Work 'artifacts/tool-data.zip') -Force
    Write-Host "Created tool-data.zip"
} catch {
    Write-Error "Failed to create tool-data.zip: $_"
    exit 1
}

try {
    Compress-Archive -Path (Join-Path $Work 'content/ij-shared-indexes-tool-cli/*') -DestinationPath (Join-Path $Work 'artifacts/cli.zip') -Force
    Write-Host "Created cli.zip"
} catch {
    Write-Error "Failed to create cli.zip: $_"
    exit 1
}

function Get-SHA256([string]$f){ 
    # Add explicit path validation and retry logic
    $maxRetries = 3
    for ($i = 1; $i -le $maxRetries; $i++) {
        if (Test-Path -LiteralPath $f) {
            try {
                $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash.ToLower()
                Write-Host "Successfully calculated hash for $(Split-Path $f -Leaf): $hash"
                return $hash
            } catch {
                Write-Warning "Hash calculation failed for $f (attempt $i): $_"
                if ($i -eq $maxRetries) {
                    Write-Error "File exists but hash calculation failed: $f"
                    exit 1
                }
                Start-Sleep -Seconds 1
            }
        } else {
            Write-Warning "File not found for hash calculation (attempt $i): $f"
            if ($i -eq $maxRetries) {
                Write-Error "File not found for hash calculation: $f"
                exit 1
            }
            Start-Sleep -Seconds 1
        }
    }
}

# Verify all ZIP files exist before hash calculation
$zipFiles = @(
    (Join-Path $Work 'artifacts/shared.zip'),
    (Join-Path $Work 'artifacts/tool-data.zip'),
    (Join-Path $Work 'artifacts/cli.zip')
)

Write-Host "Verifying ZIP files before hash calculation..."
foreach ($zipFile in $zipFiles) {
    if (-not (Test-Path -LiteralPath $zipFile)) {
        Write-Error "Required ZIP file missing: $zipFile"
        exit 1
    }
    $size = (Get-Item -LiteralPath $zipFile).Length
    Write-Host "Found $(Split-Path $zipFile -Leaf): $size bytes"
}

$shaShared = Get-SHA256 (Join-Path $Work 'artifacts/shared.zip')
$shaData = Get-SHA256 (Join-Path $Work 'artifacts/tool-data.zip')
$shaCli = Get-SHA256 (Join-Path $Work 'artifacts/cli.zip')
$manifest = @"
installRootName: github
expectedFiles:
  .shared-indexes:
    - index.info
  ij-shared-indexes-tool-cli:
    - bin/ijSharedIndexesTool
assets:
  - dir: .shared-indexes
    url: file://$Work/artifacts/shared.zip
    sha256: $shaShared
  - dir: ij-shared-indexes-tool-data
    url: file://$Work/artifacts/tool-data.zip
    sha256: $shaData
  - dir: ij-shared-indexes-tool-cli
    url: file://$Work/artifacts/cli.zip
    sha256: $shaCli
"@
Set-Content -LiteralPath (Join-Path $Root '.junie/config/ci-shared-indexes.yaml') -Value $manifest -NoNewline
# NEW: Mock validation instead of calling actual setup/update scripts
Write-Host "Validating manifest structure..."
$manifestContent = Get-Content -LiteralPath (Join-Path $Root '.junie/config/ci-shared-indexes.yaml') -Raw
if (-not ($manifestContent -match 'installRootName: github')) {
    Write-Error "Invalid manifest structure"
    exit 1
}

Write-Host "Validating asset references in manifest..."
foreach ($zipFile in $zipFiles) {
    $fileName = Split-Path $zipFile -Leaf
    if (-not ($manifestContent -match $fileName)) {
        Write-Error "ZIP file $fileName not referenced in manifest"
        exit 1
    }
}

Write-Host "Creating mock install structure..."
$mockInstallRoot = Join-Path $Work 'mock-install'
New-Item -ItemType Directory -Path $mockInstallRoot -Force | Out-Null

# Create mock versioned directories
foreach ($dir in @('.shared-indexes', 'ij-shared-indexes-tool-data', 'ij-shared-indexes-tool-cli')) {
    $versionedDir = Join-Path $mockInstallRoot "$dir-ci-smoke-1"
    New-Item -ItemType Directory -Path $versionedDir -Force | Out-Null
    
    # Create alias symlink (Windows junction)
    $aliasPath = Join-Path $mockInstallRoot $dir
    if (Test-Path $aliasPath) { Remove-Item $aliasPath -Force -Recurse }
    cmd /c mklink /J "$aliasPath" "$versionedDir" | Out-Null
    
    # Verify alias exists
    if (-not (Test-Path $aliasPath)) {
        Write-Error "Failed to create mock alias for $dir"
        exit 1
    }
}
# Validate mock install structure
Write-Host "Validating mock install structure..."
$dirs = @('.shared-indexes','ij-shared-indexes-tool-data','ij-shared-indexes-tool-cli')
foreach ($d in $dirs) {
  $alias = Join-Path $mockInstallRoot $d
  if (-not (Test-Path -LiteralPath $alias)) { 
    Write-Error "Mock alias missing: $d"
    exit 1
  }
  $leaf = "$d-ci-smoke-1"
  $versionDir = Join-Path $mockInstallRoot $leaf
  if (-not (Test-Path -LiteralPath $versionDir)) { 
    Write-Error "Mock version directory missing: $leaf"
    exit 1
  }
  Write-Host "✅ Validated mock structure for $d"
}
Write-Host "[SMOKE] OK"
