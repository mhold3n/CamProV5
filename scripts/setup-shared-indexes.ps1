param(
  [string]$InstallRoot,
  [switch]$CreateMissing,
  [string]$DownloadManifest,
  [string[]]$DownloadUrl,
  [string]$Checksum,
  [switch]$Verify,
  [switch]$Untrack,
  [switch]$Yes,
  [switch]$Quiet,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# CamProV5 — Shared Indexes setup (Option A: repository-local links on Windows)
# Now supports manifest download/population, checksum verification, verify/untrack flags,
# and quiet/yes/dry-run UX improvements.
# Usage examples:
#   pwsh -File scripts/setup-shared-indexes.ps1 -DownloadManifest .junie/config/shared-indexes.yaml -Yes

function Write-Log { param([string]$msg) if (-not $Quiet) { Write-Host $msg } }
function Write-Warn { param([string]$msg) Write-Warning $msg }
function Fail { param([string]$msg) Write-Error $msg; exit 1 }
function Confirm-Action { param([string]$Prompt) if ($Yes) { return $true } $resp = Read-Host "$Prompt [y/N]"; return ($resp -match '^(y|yes)$') }

function Is-Link {
  param([string]$Path)
  try {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path -Force
    return ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
  } catch { return $false }
}

function Get-RepoRoot {
  $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  return (Resolve-Path (Join-Path $ScriptDir '..')).Path
}

function Get-InstallRoot([string]$RepoRoot, [string]$Override) {
  if ([string]::IsNullOrWhiteSpace($Override)) {
    $Parent = (Resolve-Path (Join-Path $RepoRoot '..')).Path
    $Base = Split-Path -Leaf $Parent
    if ($Base -ne 'github') { Fail "Expected repo to be under a parent directory named 'github', but found '$Base'. Move the repo or pass -InstallRoot C:\\path\\to\\github" }
    Write-Log "INSTALL_ROOT (detected): $Parent"
    return $Parent
  } else {
    $p = (Resolve-Path $Override).Path
    Write-Log "INSTALL_ROOT (override): $p"
    return $p
  }
}

function Get-SHA256([string]$File) {
  (Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLower()
}

function Download-File([string]$Url, [string]$OutFile) {
  if ($DryRun) { Write-Log "[dry-run] download $Url -> $OutFile"; return }
  Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing -TimeoutSec 180
}

function Extract-Archive([string]$Archive, [string]$DestDir) {
  if ($DryRun) { Write-Log "[dry-run] extract $Archive -> $DestDir"; return }
  New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
  if ($Archive -match '\.zip$') {
    Expand-Archive -LiteralPath $Archive -DestinationPath $DestDir -Force
  } elseif ($Archive -match '\.(tar\.gz|tgz)$') {
    tar -xzf $Archive -C $DestDir
  } elseif ($Archive -match '\.(tar\.zst|tzst)$') {
    # Try tar with --zstd, else require zstd
    $tarHelp = & tar --help 2>$null
    if ($tarHelp -match '--zstd') {
      & tar --zstd -xf $Archive -C $DestDir
    } else {
      Fail "zstd support is required to extract $Archive (install zstd or use .zip/.tar.gz)"
    }
  } elseif ($Archive -match '\.tar$') {
    tar -xf $Archive -C $DestDir
  } else {
    Fail "Unsupported archive format: $Archive"
  }
}

function Parse-ManifestAssets([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return @() }
  if ($Path.ToLower().EndsWith('.json')) {
    $json = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    if ($null -ne $json.assets) { return $json.assets }
    return @()
  }
  # Naive YAML: find lines for - dir:, url:, sha256:
  $assets = @()
  $dir = $null; $url = $null; $sha = $null
  Get-Content -LiteralPath $Path | ForEach-Object {
    $line = $_.Trim()
    if ($line -match '^-\s*dir:\s*(.+)$') { if ($dir -and $url) { $assets += [pscustomobject]@{ dir=$dir; url=$url; sha256=$sha }; $url=$null; $sha=$null }
      $dir = $Matches[1].Trim('"') }
    elseif ($line -match '^url:\s*(.+)$') { $url = $Matches[1].Trim('"') }
    elseif ($line -match '^sha256:\s*(.+)$') { $sha = $Matches[1].Trim('"') }
  }
  if ($dir -and $url) { $assets += [pscustomobject]@{ dir=$dir; url=$url; sha256=$sha } }
  return $assets
}

$RepoRoot = Get-RepoRoot
Write-Log "== CamProV5 Shared Indexes Setup =="
Write-Log "REPO_ROOT: $RepoRoot"

if (-not $DownloadManifest) {
  $defaultManifest = Join-Path $RepoRoot '.junie/config/shared-indexes.yaml'
  $envManifest = $env:SHARED_INDEXES_MANIFEST
  if ($envManifest) { $DownloadManifest = $envManifest } elseif (Test-Path -LiteralPath $defaultManifest) { $DownloadManifest = $defaultManifest }
}

$InstallRoot = Get-InstallRoot -RepoRoot $RepoRoot -Override $InstallRoot
if (-not (Test-Path -LiteralPath $InstallRoot -PathType Container)) { Fail "INSTALL_ROOT does not exist: $InstallRoot" }

$dirs = @('.shared-indexes','ij-shared-indexes-tool-data','ij-shared-indexes-tool-cli')

# If none of the targets exist and manifest or URL provided, download and extract
$anyTarget = $false
foreach ($d in $dirs) { if (Test-Path -LiteralPath (Join-Path $InstallRoot $d)) { $anyTarget = $true } }
if (-not $anyTarget -and (($DownloadManifest) -or ($DownloadUrl -and $DownloadUrl.Count -gt 0))) {
  Write-Log "No targets under INSTALL_ROOT; attempting to download assets..."
  $tmp = New-Item -ItemType Directory -Path ([IO.Path]::Combine([IO.Path]::GetTempPath(), [Guid]::NewGuid().ToString()))
  try {
    if ($DownloadManifest) {
      $assets = Parse-ManifestAssets -Path $DownloadManifest
      foreach ($a in $assets) {
        if (-not $a.dir -or -not $a.url) { continue }
        $arc = Join-Path $tmp.FullName ([IO.Path]::GetFileName($a.url))
        Write-Log "Downloading $($a.dir) from $($a.url)"
        if (-not $DryRun) { Download-File -Url $a.url -OutFile $arc }
        if ($a.sha256) {
          $calc = Get-SHA256 -File $arc
          if ($calc -ne $a.sha256.ToLower()) { Fail "Checksum mismatch for $($a.url)" }
        }
        $dest = Join-Path $InstallRoot $a.dir
        Extract-Archive -Archive $arc -DestDir $dest
        # Validate non-empty
        if (-not $DryRun) {
          $hasContent = Get-ChildItem -LiteralPath $dest -Recurse -Force -ErrorAction SilentlyContinue | Select-Object -First 1
          if (-not $hasContent) { Fail "Extraction produced empty directory: $dest" }
        }
      }
    }
    if ($DownloadUrl -and $DownloadUrl.Count -eq 1) {
      $url = $DownloadUrl[0]
      $arc = Join-Path $tmp.FullName ([IO.Path]::GetFileName($url))
      Write-Log "Downloading from $url"
      if (-not $DryRun) { Download-File -Url $url -OutFile $arc }
      if ($Checksum) { $calc = Get-SHA256 -File $arc; if ($calc -ne $Checksum.ToLower()) { Fail "Checksum mismatch for $url" } }
      $dest = Join-Path $InstallRoot '.shared-indexes'
      Extract-Archive -Archive $arc -DestDir $dest
    } elseif ($DownloadUrl -and $DownloadUrl.Count -gt 1) {
      Write-Warn "Multiple -DownloadUrl provided without mapping; use -DownloadManifest. Skipping extra URLs."
    }
  } finally {
    if (-not $DryRun) { Remove-Item -LiteralPath $tmp.FullName -Recurse -Force -ErrorAction SilentlyContinue | Out-Null }
  }
}

foreach ($d in $dirs) {
  $src = Join-Path $RepoRoot $d
  $tgt = Join-Path $InstallRoot $d

  if ((Test-Path -LiteralPath $src -PathType Container) -and -not (Is-Link $src)) {
    if (-not $Yes -and -not (Confirm-Action "Move existing repo directory '$d' to INSTALL_ROOT?")) { Write-Warn "Skipped moving $d" }
    else {
      Write-Log "Moving real directory in repo: $d —> INSTALL_ROOT"
      if (-not $DryRun) { New-Item -ItemType Directory -Path $tgt -Force | Out-Null }
      if (-not $DryRun) {
        Get-ChildItem -LiteralPath $src -Force -ErrorAction SilentlyContinue | ForEach-Object { Move-Item -LiteralPath $_.FullName -Destination $tgt -Force -ErrorAction SilentlyContinue }
        Remove-Item -LiteralPath $src -Force -Recurse -ErrorAction SilentlyContinue
      }
    }
  } elseif (Test-Path -LiteralPath $src) {
    if (-not $DryRun) { Remove-Item -LiteralPath $src -Force -Recurse -ErrorAction SilentlyContinue }
  }

  if (-not (Test-Path -LiteralPath $tgt) -and $CreateMissing) {
    Write-Log "Creating missing target directory: $tgt"
    if (-not $DryRun) { New-Item -ItemType Directory -Path $tgt -Force | Out-Null }
  } elseif (-not (Test-Path -LiteralPath $tgt)) {
    Write-Warn "Target directory missing (will link anyway): $tgt"
  }

  # Try SymbolicLink (relative target)
  $rel = "..\\" + (Split-Path -Leaf $InstallRoot) + "\\$d"
  Write-Log "Linking $d -> $rel"
  $linked = $false
  if (-not $DryRun) {
    try {
      New-Item -ItemType SymbolicLink -Path $src -Target $rel -Force | Out-Null
      $linked = $true
    } catch {
      Write-Warn "SymbolicLink failed for $d, attempting directory junction"
    }
    if (-not $linked) {
      # Fallback: directory junction with absolute target
      $cmd = "mklink /J `"$src`" `"$tgt`""
      $p = Start-Process -FilePath cmd.exe -ArgumentList "/c $cmd" -NoNewWindow -PassThru -Wait
      if ($p.ExitCode -ne 0) { Fail "Failed to create junction for $d (cmd exit $($p.ExitCode))" }
    }
  }

  # Validate
  if (-not $DryRun) {
    if (-not (Test-Path -LiteralPath $src)) { Fail "Failed to create link for $d" } else { if (-not $Quiet) { Write-Host "OK: link created for $d" } }
  }

  if ($Verify) {
    if (Test-Path -LiteralPath $tgt -PathType Container) {
      $file = Get-ChildItem -LiteralPath $tgt -File -Force -ErrorAction SilentlyContinue | Select-Object -First 1
      if ($null -ne $file) { try { Get-Content -LiteralPath (Join-Path $src $file.Name) -TotalCount 0 -ErrorAction SilentlyContinue | Out-Null } catch {} }
      else { Write-Warn "Target appears empty: $tgt" }
    }
  }
}

if ($Untrack) {
  $dirty = ($null -ne (git diff --name-only)) -or ($null -ne (git diff --cached --name-only))
  if ($dirty) { Write-Warn "Working tree not clean; skipping -Untrack. Commit or stash and rerun." }
  else {
    if ($Yes -or (Confirm-Action "Run git rm -r --cached on protected directories?")) {
      if (-not $DryRun) { git rm -r --cached .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli | Out-Null; git commit -m "chore(shared-indexes): untrack protected directories" | Out-Null }
    }
  }
}

if (-not $Quiet) {
  Write-Host ""
  Write-Host "Summary:"
  Write-Host "- Repo links created/updated for: $($dirs -join ', ')"
  Write-Host "- INSTALL_ROOT: $InstallRoot"
  Write-Host "- Populate or update shared indexes by placing contents under INSTALL_ROOT with the same folder names, or using the manifest flags."
}
