# CamProV5

Multi-platform project combining Desktop (Kotlin/Compose), Android, Python tooling, Rust engines, and C++ components.

## Modules Overview
- desktop: Kotlin/Compose Desktop application
- android: Android application module
- camprofw/rust: Rust crates (e.g., fea-engine)
- cpp: Native C++ components
- campro, layouts: Python packages and templates

See [README_CROSS_PLATFORM.md](README_CROSS_PLATFORM.md) for environment setup and cross-platform details.

## Building
- JVM/Desktop: `./gradlew :desktop:build`
- Android (CI/CLI): `./gradlew :android:assembleDebug`
- Rust: `cargo test` inside each crate (e.g., camprofw/rust/fea-engine)
- Python: `pip install -r requirements.txt && pytest`

## Python environment (venv + editable install)
To use the Python tools with a clean setup and proper import resolution:

1) Create a Python 3.12 virtualenv and install the repo in editable mode
- macOS/Linux:
  - `bash scripts/setup_venv.sh`
  - The script requires Python 3.12 at `/usr/local/bin/python3.12` or on PATH as `python3.12`. Override with `PY312_PATH=/full/path/to/python3.12`.

2) Select the interpreter in IntelliJ IDEA/PyCharm
- Set the project interpreter to `.venv/bin/python`.

3) Verify
- `python scripts/verify_campro.py` (after activating the venv) prints the Python version and `campro` module path.

Notes
- This repository now ships a `pyproject.toml` (PEP 517/621). `pip install -e .` uses modern editable installs (PEP 660) and avoids legacy `setup.py develop`.
- On Apple Silicon, prefer an arm64 Python 3.12 to get native wheels; otherwise, ensure interpreter and wheels are consistently x86_64.

## Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Support and Security
For help, see [SUPPORT.md](SUPPORT.md). For responsible disclosure, see [SECURITY.md](SECURITY.md).

## License
See [LICENSE](LICENSE).
