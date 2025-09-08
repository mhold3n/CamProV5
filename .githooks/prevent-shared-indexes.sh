#!/usr/bin/env bash
# Pre-commit hook to prevent committing JetBrains Shared Indexes content
# Install with: git config core.hooksPath .githooks

set -euo pipefail

protected_regex='^(\.shared-indexes|ij-shared-indexes-tool-data|ij-shared-indexes-tool-cli)/'

staged=$(git diff --cached --name-only)
if echo "$staged" | grep -E "$protected_regex" -q; then
  echo "Commit blocked: files under protected shared-indexes paths detected:" >&2
  echo "" >&2
  echo "$staged" | grep -E "$protected_regex" >&2 || true
  cat >&2 <<'MSG'

Do not commit JetBrains Shared Indexes or tool data.
Remediation:
  - Unstage offending files: git reset HEAD -- <paths>
  - Add to .gitignore (already present) and remove from index:
      git rm -r --cached .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli
  - Use scripts/setup-shared-indexes.sh|ps1 to create links to INSTALL_ROOT.
MSG
  exit 1
fi

exit 0
