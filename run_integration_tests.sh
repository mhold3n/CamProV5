#!/bin/bash
# CamProV5 Integration Tests Runner - Unix/macOS version
# This script runs the Phase 3 integration tests and collects the results

set -e

# Create results directory if it doesn't exist
TEST_RESULTS_DIR="./test_results"
mkdir -p "$TEST_RESULTS_DIR"

# Create timestamp for this test run
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
TEST_RUN_DIR="$TEST_RESULTS_DIR/integration_test_run_$TIMESTAMP"
mkdir -p "$TEST_RUN_DIR"

# Log file for test output
LOG_FILE="$TEST_RUN_DIR/integration_test_log.txt"

# Function to log messages to both console and log file
log_message() {
    echo "$1"
    echo "$1" >> "$LOG_FILE"
}

# Log system information
log_message "CamProV5 Integration Tests - Phase 3"
log_message "========================================"
log_message "Date: $(date)"
log_message "System Information:"

if [[ "$OSTYPE" == "darwin"* ]]; then
    log_message "  OS: macOS $(sw_vers -productVersion 2>/dev/null || echo unknown)"
    log_message "  CPU: $(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown)"
    log_message "  Cores: $(sysctl -n hw.physicalcpu 2>/dev/null || echo unknown)"
    log_message "  Logical Processors: $(sysctl -n hw.logicalcpu 2>/dev/null || echo unknown)"
    MEM_GB=$( (sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.2f", $1/1024/1024/1024}') )
    log_message "  Memory: ${MEM_GB:-unknown} GB"
elif [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "linux"* ]]; then
    if command -v lsb_release >/dev/null 2>&1; then
        log_message "  OS: $(lsb_release -d | cut -f2)"
    else
        log_message "  OS: Linux $(uname -r)"
    fi
    log_message "  CPU: $(grep 'model name' /proc/cpuinfo 2>/dev/null | head -1 | cut -d: -f2 | xargs)"
    if command -v nproc >/dev/null 2>&1; then
        log_message "  Cores: $(nproc)"
    fi
    if command -v free >/dev/null 2>&1; then
        log_message "  Memory: $(free -g | awk '/^Mem:/{print $2}') GB"
    fi
fi

log_message "========================================"
log_message ""

# Ensure Python environment is set up
log_message "Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    log_message "Error: Python not found in PATH"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
log_message "  Python: $PYTHON_VERSION"

# Check required packages
REQUIRED_PACKAGES=("numpy" "matplotlib" "toml")
for package in "${REQUIRED_PACKAGES[@]}"; do
    ver=$($PYTHON_CMD -c "import importlib; m=importlib.import_module('$package'); print(getattr(m, '__version__', 'unknown'))" 2>/dev/null) || true
    if [ -z "$ver" ]; then
        log_message "Error: Required Python package '$package' not found"
        exit 1
    else
        log_message "  $package: $ver"
    fi
done

# Ensure Rust environment is set up
log_message "Checking Rust environment..."
RUST_AVAILABLE=true
if ! command -v rustc &> /dev/null; then
    log_message "Warning: Rust not found in PATH. Native components will be skipped."
    log_message "Please install Rust from https://rustup.rs/ to enable native FEA tests."
    RUST_AVAILABLE=false
fi

if [ "$RUST_AVAILABLE" = true ]; then
    RUST_VERSION=$(rustc --version)
    CARGO_VERSION=$(cargo --version)
    log_message "  Rust: $RUST_VERSION"
    log_message "  Cargo: $CARGO_VERSION"
fi

# Run the integration tests
log_message ""
log_message "Starting integration tests..."
log_message "This may take some time. Please be patient."
log_message ""

# Run the Python integration test script if it exists
if [ -f "./tests/test_integration.py" ]; then
    $PYTHON_CMD ./tests/test_integration.py 2>&1 | tee -a "$LOG_FILE"
else
    log_message "Warning: ./tests/test_integration.py not found. Skipping Python integration tests."
fi

# Copy the test results to our test run directory if they exist
if [ -d "./test_results/integration_test_test_integration" ]; then
    cp -r "./test_results/integration_test_test_integration" "$TEST_RUN_DIR/"
fi

# Copy the log file if it exists
if [ -f "integration_test.log" ]; then
    cp "integration_test.log" "$TEST_RUN_DIR/"
fi

log_message ""
log_message "Integration tests completed!"
log_message "Results saved to: $TEST_RUN_DIR"

# Create a summary report
SUMMARY_FILE="$TEST_RUN_DIR/integration_test_summary.md"

cat > "$SUMMARY_FILE" << 'EOF'
# CamProV5 Integration Test Summary

## Overview
This report summarizes the integration tests for the CamProV5 project.
Tests were run as part of Phase 3 (Integration Testing).

## System Information
- OS: $OSTYPE
- Test Run Directory: $TEST_RUN_DIR

## Test Categories

### Workflow Integration
- Python design to Rust simulation workflow
- Parameter passing between languages
- Result consistency across the pipeline

### Error Handling
- Invalid parameter handling
- Missing file handling
- Invalid format handling

### Performance
- Execution time for various test cases
- Memory usage during simulation

## Test Cases
- Default parameters
- High RPM case
- Low lift case
- High lift case
- Asymmetric case
- Short dwell case
- Edge case: minimum values

## Detailed Results
For detailed results, please see the test output files in the test run directory.

## Next Steps
1. Review the test results to identify any issues
2. Address any failures or warnings
3. Finalize the documentation for the complete system
EOF

log_message "Summary report created: $SUMMARY_FILE"
log_message ""
log_message "Phase 3 integration testing complete!"
