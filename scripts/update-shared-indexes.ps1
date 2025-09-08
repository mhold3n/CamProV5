param(
  [Parameter(Mandatory=$true)][string]$Version,
  [string]$Manifest,
  [string]$InstallRoot,
  [switch]$SetCurrent,
  [switch]$RollbackOnFail,
  [string]$Checksum,
  [switch]$Yes,
  [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

function Write-Log { param([string]$msg) if (-not $Quiet) { Write-Host $msg } }
function Write-Warn { param([string]$msg) Write-Warning $msg }
function Fail { param([string]$msg) Write-Error $msg; exit 1 }

function Get-RepoRoot {
  $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  return (Resolve-Path (Join-Path $ScriptDir '..')).Path
}

function Get-InstallRoot([string]$RepoRoot, [string]$Override) {
  if ([string]::IsNullOrWhiteSpace($Override)) {
    $Parent = (Resolve-Path (Join-Path $RepoRoot '..')).Path
    $Base = Split-Path -Leaf $Parent
    if ($Base -ne 'github') { Fail "Expected parent directory named 'github' but found '$Base' (use -InstallRoot to override)" }
    Write-Log "INSTALL_ROOT (detected): $Parent"
    return $Parent
  } else {
    $p = (Resolve-Path $Override).Path
    Write-Log "INSTALL_ROOT (override): $p"
    return $p
  }
}

function Get-SHA256([string]$File) { (Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLower() }
function Download-File([string]$Url, [string]$OutFile) { Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing -TimeoutSec 180 }
function Get-SidecarChecksum([string]$Url,[string]$Arc){
  $side = "$Arc.sha256"
  try { Invoke-WebRequest -Uri ($Url + '.sha256') -OutFile $side -UseBasicParsing -TimeoutSec 60 } catch {}
  if (Test-Path -LiteralPath $side) { (Get-Content -LiteralPath $side -Raw).Split(' ',[System.StringSplitOptions]::RemoveEmptyEntries)[0] }
}
function Verify-GpgSignature([string]$Archive){
  $asc = "$Archive.asc"
  if (Test-Path -LiteralPath $asc) {
    $gpg = Get-Command gpg -ErrorAction SilentlyContinue
    if ($gpg) {
      $p = Start-Process -FilePath $gpg.Source -ArgumentList @('--verify', $asc, $Archive) -NoNewWindow -PassThru -Wait
      if ($p.ExitCode -ne 0) { Fail "GPG signature verification failed for $Archive" }
    } else { Write-Warn "gpg not found; skipping signature verification for $Archive" }
  }
}
function Extract-Archive([string]$Archive, [string]$DestDir) {
  New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
  if ($Archive -match '\.zip$') { Expand-Archive -LiteralPath $Archive -DestinationPath $DestDir -Force }
  elseif ($Archive -match '\.(tar\.gz|tgz)$') { tar -xzf $Archive -C $DestDir }
  elseif ($Archive -match '\.(tar\.zst|tzst)$') {
    $tarHelp = & tar --help 2>$null
    if ($tarHelp -match '--zstd') { & tar --zstd -xf $Archive -C $DestDir }
    else { Fail "zstd support is required to extract $Archive (install zstd or use .zip/.tar.gz)" }
  }
  elseif ($Archive -match '\.tar$') { tar -xf $Archive -C $DestDir }
  else { Fail "Unsupported archive format: $Archive" }
}

function Parse-ManifestAssets([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return @() }
  if ($Path.ToLower().EndsWith('.json')) {
    $json = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    if ($null -ne $json.assets) { return $json.assets }
    return @()
  }
  $plat = if ($IsWindows) { 'windows-x64' } else { if ($PSVersionTable.Platform -eq 'Unix') { if ((uname -s) -match 'Darwin') { 'darwin-x64' } else { 'linux-x64' } } else { 'linux-x64' } }
  $channel = if ($env:SHARED_INDEXES_CHANNEL) { $env:SHARED_INDEXES_CHANNEL } else { 'stable' }
  $verToken = if ($env:SHARED_INDEXES_VERSION) { $env:SHARED_INDEXES_VERSION } else { $Version }
  $lines = Get-Content -LiteralPath $Path
  $hasPlatforms = ($lines | Select-String -SimpleMatch 'platforms:' -Quiet)
  if ($hasPlatforms) {
    $assets = @(); $inPlat=$false; $inAssets=$false; $dir=$null; $url=$null; $sha=$null
    foreach ($raw in $lines) {
      $line = $raw.Trim()
      if ($line -match '^platforms:') { $inPlat=$false; $inAssets=$false; continue }
      if ($line -match ('^' + [regex]::Escape($plat) + ':')) { $inPlat=$true; $inAssets=$false; continue }
      if ($inPlat -and $line -match '^assets:') { $inAssets=$true; continue }
      if ($inPlat -and $inAssets -and $line -match '^-\s*dir:\s*(.+)$') { $dir = $Matches[1].Trim('"'); continue }
      if ($inPlat -and $inAssets -and $line -match '^url:\s*(.+)$') { $url = $Matches[1].Trim('"'); continue }
      if ($inPlat -and $inAssets -and $line -match '^sha256:\s*(.+)$') { $sha = $Matches[1].Trim('"'); continue }
      if ($inPlat -and $inAssets -and $dir -and $url -and ($line -match '^sha256:' -or $line -match '^-\s*dir:')) {
        $u = $url.Replace('{{channel}}',$channel).Replace('{{version}}',$verToken)
        $assets += [pscustomobject]@{ dir=$dir; url=$u; sha256=$sha }
        $url=$null; $sha=$null
      }
    }
    if ($assets.Count -gt 0) { return $assets }
  }
  # Fallback: flat assets
  $assets = @(); $dir=$null; $url=$null; $sha=$null
  foreach ($raw in $lines) {
    $line = $raw.Trim()
    if ($line -match '^-\s*dir:\s*(.+)$') { if ($dir -and $url) { $assets += [pscustomobject]@{ dir=$dir; url=$url; sha256=$sha }; $url=$null; $sha=$null }; $dir = $Matches[1].Trim('"') }
    elseif ($line -match '^url:\s*(.+)$') { $url = $Matches[1].Trim('"') }
    elseif ($line -match '^sha256:\s*(.+)$') { $sha = $Matches[1].Trim('"') }
  }
  if ($dir -and $url) { $assets += [pscustomobject]@{ dir=$dir; url=$url; sha256=$sha } }
  return $assets
}

$RepoRoot = Get-RepoRoot
if (-not $Manifest) {
  $defaultManifest = Join-Path $RepoRoot '.junie/config/shared-indexes.yaml'
  $envManifest = $env:SHARED_INDEXES_MANIFEST
  if ($envManifest) { $Manifest = $envManifest } elseif (Test-Path -LiteralPath $defaultManifest) { $Manifest = $defaultManifest }
}
$INSTALL_ROOT = Get-InstallRoot -RepoRoot $RepoRoot -Override $InstallRoot
if (-not (Test-Path -LiteralPath $INSTALL_ROOT -PathType Container)) { Fail "INSTALL_ROOT does not exist: $INSTALL_ROOT" }

$dirs = @('.shared-indexes','ij-shared-indexes-tool-data','ij-shared-indexes-tool-cli')

$tmp = New-Item -ItemType Directory -Path ([IO.Path]::Combine([IO.Path]::GetTempPath(), 'cpv5-update-' + [Guid]::NewGuid()))
$created = @{}
try {
  if ($Manifest -and (Test-Path -LiteralPath $Manifest)) {
    $assets = Parse-ManifestAssets -Path $Manifest
    foreach ($a in $assets) {
      if (-not $a.dir -or -not $a.url) { continue }
      $arc = Join-Path $tmp.FullName ([IO.Path]::GetFileName($a.url))
      Write-Log "Downloading $($a.dir): $($a.url)"
      Download-File -Url $a.url -OutFile $arc
      # Integrity precedence: CLI -Checksum > manifest sha256 > sidecar
      $side = Get-SidecarChecksum -Url $a.url -Arc $arc
      $want = if ($Checksum) { $Checksum.ToLower() } elseif ($a.sha256) { $a.sha256.ToLower() } elseif ($side) { $side.ToLower() } else { $null }
      if ($want) { $calc = Get-SHA256 -File $arc; if ($calc -ne $want) { Fail "Checksum mismatch for $($a.url)" } }
      Verify-GpgSignature -Archive $arc
      $verDir = Join-Path $INSTALL_ROOT ("$($a.dir)-$Version")
      if (-not (Test-Path -LiteralPath $verDir)) {
        $work = Join-Path $tmp.FullName ("$($a.dir)-$Version")
        New-Item -ItemType Directory -Path $work -Force | Out-Null
        Extract-Archive -Archive $arc -DestDir $work
        $hasContent = Get-ChildItem -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $hasContent) { Fail "Empty extraction for $($a.dir)" }
        Move-Item -LiteralPath $work -Destination $verDir -Force
      } else {
        Write-Warn "Version directory already exists: $verDir"
      }
      $created[$a.dir] = $verDir
    }
  } else {
    Write-Warn "No manifest provided; will only switch aliases if versioned directories already exist."
  }

  if ($SetCurrent) {
    $states = @()
    try {
      foreach ($d in $dirs) {
        $verDir = Join-Path $INSTALL_ROOT ("$d-$Version")
        if (-not (Test-Path -LiteralPath $verDir -PathType Container)) { Write-Warn "Missing versioned directory: $verDir"; continue }
        $alias = Join-Path $INSTALL_ROOT $d
        $state = [pscustomobject]@{ Alias=$alias; PrevType='Absent'; PrevTarget=$null; BackupPath=$null; Applied=$false }
        if (Test-Path -LiteralPath $alias) {
          $item = Get-Item -LiteralPath $alias -Force
          if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            $state.PrevType = 'Symlink'
            try { $state.PrevTarget = (Get-Item -LiteralPath $alias).Target } catch { $state.PrevTarget = (Split-Path -Leaf $verDir) }
            Remove-Item -LiteralPath $alias -Force -Recurse -ErrorAction SilentlyContinue
          } else {
            $state.PrevType = 'Directory'
            $state.BackupPath = "$alias.__backup_$(Get-Date -UFormat %s)"
            Move-Item -LiteralPath $alias -Destination $state.BackupPath -Force
          }
        }
        $linked = $false
        try {
          New-Item -ItemType SymbolicLink -Path $alias -Target (Split-Path -Leaf $verDir) -Force | Out-Null
          $linked = $true
        } catch { Write-Warn "Symlink failed for $d; attempting junction" }
        if (-not $linked) {
          $cmd = "mklink /J `"$alias`" `"$verDir`""
          $p = Start-Process -FilePath cmd.exe -ArgumentList "/c $cmd" -NoNewWindow -PassThru -Wait
          if ($p.ExitCode -ne 0) { throw "Failed to create junction for $d (cmd exit $($p.ExitCode))" }
        }
        $state.Applied = $true
        $states += $state
        Write-Log "Alias updated: $d -> $($verDir | Split-Path -Leaf)"
      }
    } catch {
      if ($RollbackOnFail) {
        Write-Warn "Update failed; initiating rollback..."
        foreach ($s in ($states | Sort-Object -Property Alias -Descending)) {
          if (-not $s.Applied) { continue }
          if (Test-Path -LiteralPath $s.Alias) { try { Remove-Item -LiteralPath $s.Alias -Force -Recurse } catch {} }
          switch ($s.PrevType) {
            'Symlink' { try { New-Item -ItemType SymbolicLink -Path $s.Alias -Target $s.PrevTarget -Force | Out-Null } catch {} }
            'Directory' { if ($s.BackupPath -and (Test-Path -LiteralPath $s.BackupPath)) { try { Move-Item -LiteralPath $s.BackupPath -Destination $s.Alias -Force } catch {} } }
          }
        }
        Fail "Rolled back alias updates due to failure"
      } else { throw }
    }
    # success cleanup
    foreach ($s in $states) { if ($s.BackupPath -and (Test-Path -LiteralPath $s.BackupPath)) { try { Remove-Item -LiteralPath $s.BackupPath -Recurse -Force } catch {} } }
  }
}
finally {
  try { Remove-Item -LiteralPath $tmp.FullName -Recurse -Force -ErrorAction SilentlyContinue | Out-Null } catch {}
}

Write-Log "Update complete for version $Version"