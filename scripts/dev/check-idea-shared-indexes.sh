#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "Repo aliases:"
for d in .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli; do
  if [[ -L "$ROOT/$d" ]]; then echo "$d -> $(readlink "$ROOT/$d")"; else echo "$d is not a symlink"; fi
done
# Try common IntelliJ log locations (macOS/Linux)
LOG=""
if [[ "$(uname -s)" == "Darwin" ]]; then
  LOG="$HOME/Library/Logs/JetBrains/IntelliJIdea*/idea.log"
else
  LOG="$HOME/.cache/JetBrains/IntelliJIdea*/log/idea.log"
fi
shopt -s nullglob
echo "\nSearching IDEA logs for shared index hints..."
for f in $LOG; do
  echo "== $f =="
  grep -Ei 'shared index|shared indexes|applied' "$f" || true
done
