# CamProV5 Cross-Platform Development Setup

This project supports development on both Windows and macOS/Linux systems.

## Prerequisites

### All Platforms
- JDK 17 or later
- Python 3.8+ with required packages (see `requirements.txt`)
- Rust and Cargo (latest stable version)

### Platform-Specific Installation

#### Windows
1. JDK: Download from https://adoptium.net/
2. Python: Download from https://python.org or Microsoft Store
3. Rust: Download from https://rustup.rs/

#### macOS
```bash
# Using Homebrew
brew install openjdk@17 python rust
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install openjdk-17-jdk python3 python3-pip
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Building and Running

### Packaging with Compose Desktop (DMG, MSI, DEB)

Build installers on each OS runner or locally on that OS:
- macOS: `./gradlew :desktop:package`
- Windows: `./gradlew :desktop:package`
- Linux: `./gradlew :desktop:package`

Artifacts location:
- `desktop/build/compose/binaries/main/*/*/*`

Notes:
- Installer metadata includes application name, version, and vendor (set in `desktop/build.gradle.kts`).
- For signing/notarization or icons, extend `nativeDistributions { windows { } macOS { } linux { } }`.

### Shadow fat JAR

Build a runnable fat JAR:
- `./gradlew :desktop:shadowJar`

Run locally:
- `java -jar desktop/build/libs/CamProV5-desktop-*-all.jar`

### Native build flags and tests

- `-DincludeNative=true` enables building/copying Rust libraries and includes tests tagged `native`.
- `-DnativeClean=true` forces a clean native rebuild.

Examples:
- Build desktop with native: `./gradlew :desktop:build -DincludeNative=true`
- Run tests with native: `./gradlew :desktop:test -DincludeNative=true`

### JNI loading and FEA_ENGINE_LIB_DIR

When `-DincludeNative=true` is used:
- Gradle sets `FEA_ENGINE_LIB_DIR` to the built resources directory automatically (see `desktop/build.gradle.kts`).
- If running outside Gradle, set:
  - `FEA_ENGINE_LIB_DIR=desktop/build/resources/main/native/<os>/<arch>`

### Option 1: Use Gradle Wrapper (Recommended)
```bash
# Unix/macOS
./gradlew build
# Windows Command Prompt
gradlew.bat build
```

### Option 2: Platform-Specific Scripts

#### Windows
```powershell
./run_integration_tests.ps1
```

#### macOS/Linux
```bash
./run_integration_tests.sh
```

#### Universal (Auto-detect platform)
```bash
./run_integration_tests
```

## Environment Variables

Gradle will attempt to auto-detect the JDK. If it cannot, set JAVA_HOME:

### Windows
```cmd
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.16.8-hotspot
```

### macOS
```bash
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home
```

### Linux
```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

## Python Dependencies

Install Python dependencies on all platforms:
```bash
pip install -r requirements.txt          # Windows (may also be 'py -m pip ...')
pip3 install -r requirements.txt         # macOS/Linux
```

## Troubleshooting

### JDK Issues
- Ensure JAVA_HOME points to a JDK (not JRE)
- Verify with: `java -version` and `javac -version`

### Python Issues
- Use `python3` instead of `python` on macOS/Linux
- Consider a virtual environment

### Rust Issues
- Restart your terminal after installing Rust
- Verify with: `rustc --version` and `cargo --version`

## Notes
- gradle.properties has been updated to remove hardcoded Windows paths and now relies on Gradle auto-detection or JAVA_HOME.
- A Bash version of the integration test runner is available as `run_integration_tests.sh`.
- A universal runner `run_integration_tests` auto-detects platform and chooses the appropriate script.


## JetBrains Shared Indexes (Option A: repository-local symlinks)

Goal: keep large JetBrains Shared Indexes outside the repo under a stable install root named "github", and expose them inside the repo via links so IDEs/scripts work unchanged.

Managed directories (created outside the repo, linked inside):
- .shared-indexes
- ij-shared-indexes-tool-data
- ij-shared-indexes-tool-cli

Post-clone setup (one-time per machine):
- macOS/Linux:
  - Populate and link via manifest: `bash scripts/setup-shared-indexes.sh --download-manifest .junie/config/shared-indexes.yaml --yes`
  - Override root or create missing targets:
    - `bash scripts/setup-shared-indexes.sh --install-root "/absolute/path/to/github" --create-missing --yes`
- Windows (PowerShell):
  - Populate and link via manifest: `pwsh -File scripts/setup-shared-indexes.ps1 -DownloadManifest .junie/config/shared-indexes.yaml -Yes`
  - With override: `pwsh -File scripts/setup-shared-indexes.ps1 -InstallRoot "C:\\path\\to\\github" -CreateMissing -Yes`

Useful flags (bash/PowerShell equivalents):
- `--install-root` / `-InstallRoot` — override INSTALL_ROOT
- `--create-missing` / `-CreateMissing` — create empty targets
- `--download-manifest` / `-DownloadManifest` — YAML/JSON manifest with assets and checksums
- `--verify` / `-Verify` — dereference probe after linking
- `--yes` / `-Yes`, `--quiet` / `-Quiet` — non-interactive, reduced output
- `--untrack` / `-Untrack` — remove any accidentally tracked protected dirs

Updating to a new version (atomic switch):
- macOS/Linux: `bash scripts/update-shared-indexes.sh --version v2025.09.08 --manifest .junie/config/shared-indexes.yaml --set-current --yes`
- Windows: `pwsh -File scripts/update-shared-indexes.ps1 -Version v2025.09.08 -Manifest .junie/config/shared-indexes.yaml -SetCurrent -Yes`

Assumptions and behavior:
- By default, the repo directory CamProV5 should be under a parent folder named github (e.g., .../Documents/github/CamProV5). The scripts detect INSTALL_ROOT as that parent and validate the name.
- Any real directories with these names inside the repo are moved to INSTALL_ROOT, then replaced by symlinks (macOS/Linux) or symlinks/junctions (Windows).
- Links use relative targets so the repo can be moved within the INSTALL_ROOT without breaking.
- If targets are missing, the scripts still create links and print a warning; you can populate the folders later.

Untracking (only if these folders were previously committed):
```bash
git rm -r --cached .shared-indexes ij-shared-indexes-tool-data ij-shared-indexes-tool-cli
git commit -m "chore(shared-indexes): move to INSTALL_ROOT and link from repo"
```

Guardrails:
- CI workflow `.github/workflows/guard-shared-indexes.yml` prevents adding shared-index content to the repo.
- Optional pre-commit hooks: set `git config core.hooksPath .githooks` to enable.

Notes:
- Windows symbolic links require Developer Mode or admin privileges; the script falls back to directory junctions automatically.
- If IntelliJ cached old paths, use File > Invalidate Caches / Restart once after switching.
- See `docs/SharedIndexes.md` for a deeper guide, manifest example, and troubleshooting.

Advanced options:
- Rollback: add `--rollback-on-fail` (bash) / `-RollbackOnFail` (ps1) when switching aliases to restore previous state on errors.
- Integrity: checksum precedence is CLI > manifest > sidecar .sha256; optional GPG verification if `.asc` signature is present and `gpg` is installed.
- Manifest templating: URLs may contain `{{channel}}` and `{{version}}`; channel defaults to `$SHARED_INDEXES_CHANNEL` or `stable`, version defaults to `--version` or `$SHARED_INDEXES_VERSION`.
- CI: workflow `shared-indexes-smoke.yml` runs tiny end-to-end checks on Ubuntu and Windows.
- Helpers: run `scripts/dev/check-idea-shared-indexes.sh|ps1` to see alias targets and scan IDEA logs.
