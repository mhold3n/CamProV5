# CamProV5 Integration Tests Runner
# This script runs the Phase 3 integration tests and collects the results

# Create results directory if it doesn't exist
$testResultsDir = ".\test_results"
if (-not (Test-Path $testResultsDir)) {
    New-Item -ItemType Directory -Path $testResultsDir
}

# Create timestamp for this test run
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$testRunDir = Join-Path $testResultsDir "integration_test_run_$timestamp"
New-Item -ItemType Directory -Path $testRunDir

# Log file for test output
$logFile = Join-Path $testRunDir "integration_test_log.txt"

# Function to log messages to both console and log file
function Log-Message {
    param (
        [string]$message
    )
    
    Write-Host $message
    Add-Content -Path $logFile -Value $message
}

# Log system information
Log-Message "CamProV5 Integration Tests - Phase 3"
Log-Message "========================================"
Log-Message "Date: $(Get-Date)"
Log-Message "System Information:"
Log-Message "  OS: $((Get-CimInstance Win32_OperatingSystem).Caption)"
Log-Message "  CPU: $((Get-CimInstance Win32_Processor).Name)"
Log-Message "  Cores: $((Get-CimInstance Win32_Processor).NumberOfCores)"
Log-Message "  Logical Processors: $((Get-CimInstance Win32_Processor).NumberOfLogicalProcessors)"
Log-Message "  Memory: $([math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)) GB"
Log-Message "========================================"
Log-Message ""

# Ensure Python environment is set up
Log-Message "Checking Python environment..."
try {
    $pythonVersion = python --version
    Log-Message "  Python: $pythonVersion"
    
    # Check required packages
    $requiredPackages = @("numpy", "matplotlib", "toml")
    foreach ($package in $requiredPackages) {
        $checkPackage = python -c "import $package; print(f'  $package: {$package.__version__}')"
        Log-Message $checkPackage
    }
} catch {
    Log-Message "Error checking Python environment: $_"
    Log-Message "Please ensure Python is installed with the required packages."
    exit 1
}

# Ensure Rust environment is set up
Log-Message "Checking Rust environment..."
try {
    $rustVersion = rustc --version
    $cargoVersion = cargo --version
    Log-Message "  Rust: $rustVersion"
    Log-Message "  Cargo: $cargoVersion"
} catch {
    Log-Message "Error checking Rust environment: $_"
    Log-Message "Please ensure Rust and Cargo are installed."
    exit 1
}

# Run the integration tests
Log-Message ""
Log-Message "Starting integration tests..."
Log-Message "This may take some time. Please be patient."
Log-Message ""

try {
    # Run the Python integration test script
    $testOutput = python .\tests\test_integration.py
    $testOutput | ForEach-Object { Log-Message $_ }
    
    # Copy the test results to our test run directory
    Copy-Item -Path ".\test_results\integration_test_test_integration" -Destination $testRunDir -Recurse -ErrorAction SilentlyContinue
    
    # Copy the log file
    Copy-Item -Path "integration_test.log" -Destination $testRunDir -ErrorAction SilentlyContinue
    
    Log-Message ""
    Log-Message "Integration tests completed!"
    Log-Message "Results saved to: $testRunDir"
} catch {
    Log-Message "Error running integration tests: $_"
    exit 1
}

# Create a summary report
$summaryFile = Join-Path $testRunDir "integration_test_summary.md"

@"
# CamProV5 Integration Test Summary

## Overview
This report summarizes the integration tests for the CamProV5 project.
Tests were run on $(Get-Date) as part of Phase 3 (Integration Testing).

## System Information
- OS: $((Get-CimInstance Win32_OperatingSystem).Caption)
- CPU: $((Get-CimInstance Win32_Processor).Name)
- Cores: $((Get-CimInstance Win32_Processor).NumberOfCores)
- Logical Processors: $((Get-CimInstance Win32_Processor).NumberOfLogicalProcessors)
- Memory: $([math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)) GB

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
"@ | Out-File -FilePath $summaryFile

Log-Message "Summary report created: $summaryFile"
Log-Message ""
Log-Message "Phase 3 integration testing complete!"