# CamPro GUI Setup and Usage Guide

This document provides a comprehensive guide for setting up and using both the PyQt and Kotlin GUIs for the CamPro application. It includes commands for building, running, and testing both GUIs, as well as instructions for recompiling and testing when changes are made to the Rust FEA engine or the Kotlin GUI.

## Table of Contents

1. [PyQt GUI Setup and Usage](#pyqt-gui-setup-and-usage)
2. [Kotlin GUI Setup and Usage](#kotlin-gui-setup-and-usage)
3. [Rust FEA Engine Integration](#rust-fea-engine-integration)
4. [Testing Workflow](#testing-workflow)
5. [Troubleshooting](#troubleshooting)

## PyQt GUI Setup and Usage

The PyQt GUI is the default interface for the CamPro application. It's implemented in Python and uses the PyQt5 library.

### 1. Install PyQt5

```powershell
# Install PyQt5 using pip
pip install PyQt5
```

**Terminal-friendly command:**
```powershell
pip install PyQt5
```

### 2. Verify PyQt5 Installation

```powershell
# Verify PyQt5 installation
python -c "import PyQt5; print('PyQt5 is installed')"

# Run the PyQt5 test script (if available)
python D:\Development\engine\CamProV5\test_pyqt5.py
```

**Terminal-friendly command:**
```powershell
python -c "import PyQt5; print('PyQt5 is installed')" ; python D:\Development\engine\CamProV5\test_pyqt5.py
```

### 3. Run the PyQt GUI

```powershell
# Run the PyQt GUI directly
python -m campro.main

# Or use the exploratory testing script (which will use PyQt by default)
cd D:\Development\engine\CamProV5
.\start_exploratory_testing.ps1
# When prompted, choose 'n' when asked to use the Kotlin UI
```

**Terminal-friendly commands:**
```powershell
# Option 1: Run PyQt GUI directly
python -m campro.main

# Option 2: Use exploratory testing script
cd D:\Development\engine\CamProV5 ; .\start_exploratory_testing.ps1
```

### 4. Testing Changes to the PyQt GUI

After making changes to the PyQt GUI code:

```powershell
# Run the PyQt GUI to test your changes
python -m campro.main

# Or run the exploratory testing script
cd D:\Development\engine\CamProV5
.\start_exploratory_testing.ps1
```

**Terminal-friendly commands:**
```powershell
# Option 1: Run PyQt GUI directly
python -m campro.main

# Option 2: Use exploratory testing script
cd D:\Development\engine\CamProV5 ; .\start_exploratory_testing.ps1
```

## Kotlin GUI Setup and Usage

The Kotlin GUI is an alternative interface implemented using Compose for Desktop. It provides a more modern UI experience and is the production UI for the application.

### 1. Build the Kotlin UI

```powershell
# Navigate to the project root directory
cd D:\Development\engine\CamProV5

# Build the desktop application
.\gradlew :desktop:build
```

**Terminal-friendly command:**
```powershell
cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:build
```

This will create a JAR file at `desktop\build\libs\CamProV5-desktop.jar`.

### 2. Run the Kotlin UI

```powershell
# Run the Kotlin UI directly
cd D:\Development\engine\CamProV5
.\gradlew :desktop:run

# Run with testing mode
.\gradlew :desktop:run --args="--testing-mode"

# Run with agent mode
.\gradlew :desktop:run --args="--enable-agent"

# Or use the exploratory testing script
.\start_exploratory_testing.ps1
# When prompted, choose 'y' when asked to use the Kotlin UI
```

**Terminal-friendly commands:**
```powershell
# Option 1: Run Kotlin UI directly
cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:run

# Option 2: Run with testing mode
cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:run --args="--testing-mode"

# Option 3: Run with agent mode
cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:run --args="--enable-agent"

# Option 4: Use exploratory testing script
cd D:\Development\engine\CamProV5 ; .\start_exploratory_testing.ps1
```

### 3. Testing Changes to the Kotlin UI

After making changes to the Kotlin UI code:

```powershell
# Rebuild the desktop application
cd D:\Development\engine\CamProV5
.\gradlew :desktop:clean :desktop:build

# Run the Kotlin UI to test your changes
.\gradlew :desktop:run

# Or run the exploratory testing script
.\start_exploratory_testing.ps1
# When prompted, choose 'y' when asked to use the Kotlin UI
```

**Terminal-friendly commands:**
```powershell
# Option 1: Rebuild and run
cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:clean :desktop:build ; .\gradlew :desktop:run

# Option 2: Use exploratory testing script
cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:clean :desktop:build ; .\start_exploratory_testing.ps1
```

## Rust FEA Engine Integration

The Rust FEA (Finite Element Analysis) engine is the computational core of the CamPro application. It's integrated with both the PyQt and Kotlin GUIs.

### 1. Recompile the Rust FEA Engine

```powershell
# Navigate to the Rust engine directory
cd D:\Development\engine\CamProV4\camprofw\rust

# Build the Rust engine
cargo build --release
```

**Terminal-friendly command:**
```powershell
cd D:\Development\engine\CamProV4\camprofw\rust ; cargo build --release
```

### 2. Testing Changes to the Rust FEA Engine

After making changes to the Rust FEA engine:

```powershell
# Rebuild the Rust engine
cd D:\Development\engine\CamProV4\camprofw\rust
cargo build --release

# Run tests for the Rust engine
cargo test

# Run the PyQt GUI to test integration
cd D:\Development\engine\CamProV5
python -m campro.main

# Or run the Kotlin UI to test integration
.\gradlew :desktop:run
```

**Terminal-friendly commands:**
```powershell
# Option 1: Rebuild and test
cd D:\Development\engine\CamProV4\camprofw\rust ; cargo build --release ; cargo test

# Option 2: Rebuild and test with PyQt GUI
cd D:\Development\engine\CamProV4\camprofw\rust ; cargo build --release ; cargo test ; cd D:\Development\engine\CamProV5 ; python -m campro.main

# Option 3: Rebuild and test with Kotlin UI
cd D:\Development\engine\CamProV4\camprofw\rust ; cargo build --release ; cargo test ; cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:run
```

## Testing Workflow

The CamPro application includes a comprehensive testing framework that supports in-the-loop testing with both the PyQt and Kotlin GUIs.

### 1. Run the Exploratory Testing Script

```powershell
# Navigate to the project root directory
cd D:\Development\engine\CamProV5

# Run the exploratory testing script
.\start_exploratory_testing.ps1
```

**Terminal-friendly command:**
```powershell
cd D:\Development\engine\CamProV5 ; .\start_exploratory_testing.ps1
```

The script will:
1. Check if PyQt5 is installed and install it if needed
2. Check if the Kotlin UI is available
3. Prompt you to choose which UI to use for testing
4. Set up the testing environment
5. Launch the chosen UI in testing mode
6. Connect the agent to the UI for monitoring and assistance

### 2. Testing with the PyQt GUI

```powershell
# Run the exploratory testing script with PyQt
cd D:\Development\engine\CamProV5
.\start_exploratory_testing.ps1
# When prompted, choose 'n' when asked to use the Kotlin UI

# Or run the testing module directly with PyQt
python -m campro.testing.start_agent_session --duration 30
```

**Terminal-friendly commands:**
```powershell
# Option 1: Use exploratory testing script
cd D:\Development\engine\CamProV5 ; .\start_exploratory_testing.ps1
# When prompted, choose 'n' when asked to use the Kotlin UI

# Option 2: Run testing module directly
cd D:\Development\engine\CamProV5 ; python -m campro.testing.start_agent_session --duration 30
```

### 3. Testing with the Kotlin UI

```powershell
# Ensure the Kotlin UI is built
cd D:\Development\engine\CamProV5
.\gradlew :desktop:build

# Run the exploratory testing script with Kotlin UI
.\start_exploratory_testing.ps1
# When prompted, choose 'y' when asked to use the Kotlin UI

# Or run the testing module directly with Kotlin UI
python -m campro.testing.start_agent_session --duration 30 --use-kotlin-ui
```

**Terminal-friendly commands:**
```powershell
# Option 1: Build and use exploratory testing script
cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:build ; .\start_exploratory_testing.ps1
# When prompted, choose 'y' when asked to use the Kotlin UI

# Option 2: Build and run testing module directly
cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:build ; python -m campro.testing.start_agent_session --duration 30 --use-kotlin-ui
```

## Troubleshooting

### PyQt5 Installation Issues

If you encounter issues installing or using PyQt5:

```powershell
# Verify Python installation
python --version

# Try reinstalling PyQt5
pip uninstall PyQt5
pip install PyQt5

# Check if PyQt5 is installed correctly
python -c "import PyQt5; print('PyQt5 is installed')"

# Run the PyQt5 test script
python D:\Development\engine\CamProV5\test_pyqt5.py
```

**Terminal-friendly commands:**
```powershell
# Verify and reinstall PyQt5
python --version ; pip uninstall -y PyQt5 ; pip install PyQt5

# Verify installation and run test script
python -c "import PyQt5; print('PyQt5 is installed')" ; python D:\Development\engine\CamProV5\test_pyqt5.py
```

### Kotlin UI Build Issues

If you encounter issues building or running the Kotlin UI:

```powershell
# Verify Java installation
java -version

# Clean the build directory
cd D:\Development\engine\CamProV5
.\gradlew :desktop:clean

# Rebuild with verbose output
.\gradlew :desktop:build --info

# Check if the JAR file was created
dir desktop\build\libs
```

**Terminal-friendly commands:**
```powershell
# Verify Java and clean build
java -version ; cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:clean

# Rebuild with verbose output and check result
cd D:\Development\engine\CamProV5 ; .\gradlew :desktop:build --info ; dir desktop\build\libs
```

### Rust Engine Build Issues

If you encounter issues building the Rust engine:

```powershell
# Verify Rust installation
rustc --version
cargo --version

# Clean the build directory
cd D:\Development\engine\CamProV4\camprofw\rust
cargo clean

# Rebuild with verbose output
cargo build --release -v

# Check if the library was created
dir target\release
```

**Terminal-friendly commands:**
```powershell
# Verify Rust installation
rustc --version ; cargo --version

# Clean, rebuild, and verify
cd D:\Development\engine\CamProV4\camprofw\rust ; cargo clean ; cargo build --release -v ; dir target\release
```

### Testing Script Issues

If you encounter issues with the exploratory testing script:

```powershell
# Check if the script exists
dir D:\Development\engine\CamProV5\start_exploratory_testing.ps1

# Run the script with verbose output
cd D:\Development\engine\CamProV5
.\start_exploratory_testing.ps1 -Verbose

# Try running the testing module directly
python -m campro.testing.start_agent_session --duration 30
```

**Terminal-friendly commands:**
```powershell
# Check script and run with verbose output
dir D:\Development\engine\CamProV5\start_exploratory_testing.ps1 ; cd D:\Development\engine\CamProV5 ; .\start_exploratory_testing.ps1 -Verbose

# Run testing module directly
cd D:\Development\engine\CamProV5 ; python -m campro.testing.start_agent_session --duration 30
```

---

This guide should help you set up and use both the PyQt and Kotlin GUIs for the CamPro application. If you encounter any issues not covered in the troubleshooting section, please refer to the project documentation or contact the development team.