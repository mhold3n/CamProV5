# CamProV5 Performance Benchmarks Runner
# This script runs the Phase 2 performance benchmarks and collects the results

# Create results directory if it doesn't exist
$resultsDir = ".\benchmark_results"
if (-not (Test-Path $resultsDir)) {
    New-Item -ItemType Directory -Path $resultsDir
}

# Create timestamp for this benchmark run
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$benchmarkDir = Join-Path $resultsDir "benchmark_run_$timestamp"
New-Item -ItemType Directory -Path $benchmarkDir

# Log file for benchmark output
$logFile = Join-Path $benchmarkDir "benchmark_log.txt"

# Function to log messages to both console and log file
function Log-Message {
    param (
        [string]$message
    )
    
    Write-Host $message
    Add-Content -Path $logFile -Value $message
}

# Log system information
Log-Message "CamProV5 Performance Benchmarks - Phase 2"
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

# Change to the Rust project directory
Set-Location -Path ".\camprofw\rust\fea-engine"

# Run the benchmarks
Log-Message "Starting benchmarks..."
Log-Message "This may take some time. Please be patient."
Log-Message ""

try {
    # Run cargo bench with output to both console and log file
    $benchmarkOutput = cargo bench --bench motion_law_benchmarks -- --verbose
    $benchmarkOutput | ForEach-Object { Log-Message $_ }
    
    # Copy the Criterion results to our benchmark directory
    Copy-Item -Path ".\target\criterion" -Destination $benchmarkDir -Recurse
    
    Log-Message ""
    Log-Message "Benchmarks completed successfully!"
    Log-Message "Results saved to: $benchmarkDir"
} catch {
    Log-Message "Error running benchmarks: $_"
    exit 1
}

# Return to the original directory
Set-Location -Path "..\..\.."

# Create a summary report
$summaryFile = Join-Path $benchmarkDir "benchmark_summary.md"

@"
# CamProV5 Performance Benchmark Summary

## Overview
This report summarizes the performance benchmarks for the CamProV5 motion law implementation.
Benchmarks were run on $(Get-Date) as part of Phase 2 (Performance Validation).

## System Information
- OS: $((Get-CimInstance Win32_OperatingSystem).Caption)
- CPU: $((Get-CimInstance Win32_Processor).Name)
- Cores: $((Get-CimInstance Win32_Processor).NumberOfCores)
- Logical Processors: $((Get-CimInstance Win32_Processor).NumberOfLogicalProcessors)
- Memory: $([math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)) GB

## Benchmark Categories

### Single-Threaded Performance
- Displacement calculation
- Velocity calculation
- Acceleration calculation
- Jerk calculation
- Boundary condition calculation

### Parallel Scaling Efficiency
- Parallel displacement calculation
- Parallel velocity calculation
- Parallel acceleration calculation
- Parallel jerk calculation
- Boundary conditions calculation
- Kinematic analysis

### Memory Usage Patterns
- Memory usage for large kinematic analysis
- Memory usage for large boundary condition calculations

### Numerical Stability
- Displacement stability over extended time periods
- Velocity stability over extended time periods
- Acceleration stability over extended time periods

## Detailed Results
For detailed results, please see the Criterion output in the `criterion` directory.

## Next Steps
1. Analyze the benchmark results to identify any performance bottlenecks
2. Implement optimizations based on the benchmark results
3. Proceed to Phase 3 (Integration Testing)
"@ | Out-File -FilePath $summaryFile

Log-Message "Summary report created: $summaryFile"
Log-Message ""
Log-Message "Phase 2 benchmarking complete!"