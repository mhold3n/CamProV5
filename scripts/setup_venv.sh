#!/usr/bin/env bash
set -euo pipefail

# Setup a local virtual environment using Python 3.12 and install the repo in editable mode.
# Usage: bash scripts/setup_venv.sh

PY312=${PY312_PATH:-/usr/local/bin/python3.12}
if [[ ! -x "$PY312" ]]; then
  # Fallbacks
  if command -v python3.12 >/dev/null 2>&1; then
    PY312=$(command -v python3.12)
  else
    echo "Error: Python 3.12 not found. Install it (e.g. via Homebrew: brew install python@3.12) or set PY312_PATH=/full/path/to/python3.12"
    exit 1
  fi
fi

# Create or clear venv
if [[ -d .venv ]]; then
  echo "Clearing existing .venv with Python 3.12..."
  "$PY312" -m venv --clear .venv
else
  echo "Creating .venv with Python 3.12..."
  "$PY312" -m venv .venv
fi

# Activate and upgrade tooling
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip setuptools wheel

# Install this project in editable mode using PEP 517/660 (pyproject.toml)
pip install -e .

# Optional: install dev extras if requested
if [[ "${INSTALL_DEV_EXTRAS:-0}" == "1" ]]; then
  pip install -e .[dev]
fi

# Print verification info
python - <<'PY'
import sys, platform
print("Python:", sys.version)
print("Implementation:", platform.python_implementation())
print("Executable:", sys.executable)
try:
    import campro
    print("campro module:", campro.__file__)
except Exception as e:
    print("campro import failed:", e)
PY

cat <<'INFO'

Next steps:
1) In IntelliJ IDEA / PyCharm, set the project interpreter to: .venv/bin/python
2) Reopen the project or Invalidate Caches if imports still look unresolved.
3) To reinstall after changes: source .venv/bin/activate && pip install -e .
INFO
