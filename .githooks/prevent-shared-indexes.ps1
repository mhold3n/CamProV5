Param()
$ErrorActionPreference = 'Stop'

# Pre-commit hook to prevent committing JetBrains Shared Indexes content
# Install with: git config core.hooksPath .githooks

function Get-StagedFiles {
  git diff --cached --name-only
}

$protected = @(
  '^\.shared-indexes/',
  '^ij-shared-indexes-tool-data/',
  '^ij-shared-indexes-tool-cli/'
)

$staged = Get-StagedFiles
$violations = @()
foreach ($p in $protected) {
  $matches = $staged | Where-Object { $_ -match $p }
  if ($matches) { $violations += $matches }
}

if ($violations.Count -gt 0) {
  Write-Host "Commit blocked: files under protected shared-indexes paths detected:" -ForegroundColor Red
  $violations | Sort-Object -Unique | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
  Write-Host "" 
  Write-Host @'
Do not commit JetBrains Shared Indexes or tool data.
Remediation:
  - Unstage offending files: git reset HEAD -- <paths>
  - Remove from index and keep ignored:
      git rm -r --cached .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli
  - Use scripts/setup-shared-indexes.sh|ps1 to create links to INSTALL_ROOT.
'@
  exit 1
}

exit 0
