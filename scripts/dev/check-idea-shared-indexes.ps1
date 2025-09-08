Param()
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path
Write-Host "Repo aliases:"
$dirs = @('.shared-indexes','ij-shared-indexes-tool-data','ij-shared-indexes-tool-cli')
foreach ($d in $dirs) {
  $p = Join-Path $Root $d
  if (Test-Path -LiteralPath $p) {
    Write-Host "$d => present (link or junction)"
  } else {
    Write-Host "$d => missing"
  }
}
$logGlob = Join-Path $env:LOCALAPPDATA 'JetBrains/IntelliJIdea*/log/idea.log'
$logs = Get-ChildItem -Path $logGlob -ErrorAction SilentlyContinue
Write-Host "`nSearching IDEA logs for shared index hints..."
foreach ($l in $logs) {
  Write-Host "== $($l.FullName) =="
  try { Select-String -Path $l.FullName -Pattern 'shared index|shared indexes|applied' -SimpleMatch } catch {}
}
