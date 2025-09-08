#!/usr/bin/env bash
set -euo pipefail

# CI guard: prevent tracking JetBrains Shared Indexes directories or contents
# Protected paths
PROTECTED=(
  ".shared-indexes"
  "ij-shared-indexes-tool-data"
  "ij-shared-indexes-tool-cli"
)

fail=false

# Check if any of the protected directories themselves are tracked
if git ls-files -s -- "${PROTECTED[@]}" | grep -q .; then
  echo "[GUARD] Tracked protected top-level entries detected under: ${PROTECTED[*]}" >&2
  fail=true
fi

# Check for any files nested under those directories
if git ls-files | grep -E '^(\.shared-indexes|ij-shared-indexes-tool-data|ij-shared-indexes-tool-cli)/' -q; then
  echo "[GUARD] Tracked files found inside protected directories (.shared-indexes/, ij-shared-indexes-tool-data/, ij-shared-indexes-tool-cli/)." >&2
  fail=true
fi

if [[ "$fail" == true ]]; then
  cat >&2 <<'MSG'
Guard check failed.
Do not commit JetBrains Shared Indexes or tool data into the repository.

Remediation:
  - Ensure these entries are ignored in .gitignore (already configured).
  - Untrack any accidentally added files:
      git rm -r --cached .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli
      git commit -m "chore(shared-indexes): untrack protected directories"
  - Use scripts/setup-shared-indexes.sh|ps1 to create links to INSTALL_ROOT.
MSG
  exit 1
fi

echo "[GUARD] OK: No tracked files under protected shared-index directories."