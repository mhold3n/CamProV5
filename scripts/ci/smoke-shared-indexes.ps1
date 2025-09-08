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
# zip
Compress-Archive -Path (Join-Path $Work 'content/.shared-indexes/*') -DestinationPath (Join-Path $Work 'artifacts/shared.zip') -Force
Compress-Archive -Path (Join-Path $Work 'content/ij-shared-indexes-tool-data/*') -DestinationPath (Join-Path $Work 'artifacts/tool-data.zip') -Force
Compress-Archive -Path (Join-Path $Work 'content/ij-shared-indexes-tool-cli/*') -DestinationPath (Join-Path $Work 'artifacts/cli.zip') -Force
function Get-SHA256([string]$f){ (Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash.ToLower() }
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
# setup
pwsh -File scripts/setup-shared-indexes.ps1 -InstallRoot $Root -DownloadManifest (Join-Path $Root '.junie/config/ci-shared-indexes.yaml') -Yes -Quiet
# update
pwsh -File scripts/update-shared-indexes.ps1 -InstallRoot $Root -Manifest (Join-Path $Root '.junie/config/ci-shared-indexes.yaml') -Version ci-smoke-1 -SetCurrent -RollbackOnFail -Yes -Quiet
# validate
$dirs = @('.shared-indexes','ij-shared-indexes-tool-data','ij-shared-indexes-tool-cli')
foreach ($d in $dirs) {
  $alias = Join-Path $Root $d
  if (-not (Test-Path -LiteralPath $alias)) { throw "alias missing $d" }
  $leaf = "$d-ci-smoke-1"
  # On Windows alias may be junction -> just verify version directory exists
  if (-not (Test-Path -LiteralPath (Join-Path $Root $leaf))) { throw "version dir missing: $leaf" }
}
Write-Host "[SMOKE] OK"
