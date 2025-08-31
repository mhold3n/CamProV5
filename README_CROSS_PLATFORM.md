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
