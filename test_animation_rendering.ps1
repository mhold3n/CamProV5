# test_animation_rendering.ps1
# Script to test the animation rendering implementation

# Set the base directory
$baseDir = "D:\Development\engine\CamProV5"
$testingModule = "campro.testing"
$mainModule = "campro.main"

Write-Host "CamProV5 Animation Rendering Test" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Kill any previous testing instances
Write-Host "Step 1: Terminating any previous testing instances..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | 
                   Where-Object { $_.CommandLine -like "*$mainModule*" -or $_.CommandLine -like "*$testingModule*" }

if ($pythonProcesses) {
    foreach ($process in $pythonProcesses) {
        Write-Host "  Terminating process: $($process.Id)" -ForegroundColor Gray
        Stop-Process -Id $process.Id -Force
    }
    Write-Host "  Previous testing instances terminated." -ForegroundColor Green
} else {
    Write-Host "  No previous testing instances found." -ForegroundColor Green
}

# Step 2: Check for Kotlin UI
Write-Host "Step 2: Checking for Kotlin UI..." -ForegroundColor Yellow

# Check if the Kotlin UI desktop JAR exists
$kotlinUIJar = Join-Path -Path $baseDir -ChildPath "desktop\build\libs\CamProV5-desktop.jar"
$kotlinUIAvailable = $false

if (Test-Path $kotlinUIJar) {
    # Check if Java is available
    try {
        $javaVersion = java -version 2>&1
        Write-Host "  Kotlin UI is available." -ForegroundColor Green
        Write-Host "  You can use the Kotlin UI for testing." -ForegroundColor Green
        $kotlinUIAvailable = $true
        $useKotlinUI = $true
        Write-Host "  Will use Kotlin UI for testing." -ForegroundColor Green
    } catch {
        Write-Host "  Java is not available. Cannot use Kotlin UI." -ForegroundColor Yellow
        Write-Host "  Falling back to PyQt5 for GUI." -ForegroundColor Yellow
        $useKotlinUI = $false
    }
} else {
    Write-Host "  Kotlin UI is not available." -ForegroundColor Yellow
    Write-Host "  Falling back to PyQt5 for GUI." -ForegroundColor Yellow
    $useKotlinUI = $false
}

# Step 3: Test with different parameters
Write-Host "Step 3: Testing animation with different parameters..." -ForegroundColor Yellow

# Define test parameters
$testParameters = @(
    @{
        "base_circle_radius" = "25.0"
        "max_lift" = "10.0"
        "cam_duration" = "180.0"
        "rise_duration" = "90.0"
        "dwell_duration" = "45.0"
        "fall_duration" = "90.0"
    },
    @{
        "base_circle_radius" = "35.0"
        "max_lift" = "15.0"
        "cam_duration" = "180.0"
        "rise_duration" = "90.0"
        "dwell_duration" = "45.0"
        "fall_duration" = "90.0"
    },
    @{
        "base_circle_radius" = "20.0"
        "max_lift" = "8.0"
        "cam_duration" = "180.0"
        "rise_duration" = "60.0"
        "dwell_duration" = "60.0"
        "fall_duration" = "60.0"
    }
)

# Create a temporary directory for test results
$testResultsDir = Join-Path -Path $baseDir -ChildPath "test_results\animation_test"
if (-not (Test-Path $testResultsDir)) {
    New-Item -Path $testResultsDir -ItemType Directory -Force | Out-Null
}

# Create a test configuration file
$testConfigFile = Join-Path -Path $testResultsDir -ChildPath "test_config.json"
$testConfig = @{
    "test_parameters" = $testParameters
    "test_duration" = 30
    "test_mode" = "animation"
}
$testConfig | ConvertTo-Json -Depth 4 | Set-Content -Path $testConfigFile

# Step 4: Run the tests
Write-Host "Step 4: Running animation tests..." -ForegroundColor Yellow

# Change to the base directory
Set-Location -Path $baseDir

# Run the tests with Kotlin UI or PyQt5
try {
    if ($useKotlinUI) {
        Write-Host "  Running tests with Kotlin UI..." -ForegroundColor Gray
        Write-Host "  Test 1: Default parameters" -ForegroundColor Gray
        python -m campro.testing.start_agent_session --duration 30 --use-kotlin-ui --test-config $testConfigFile --test-param-index 0
        
        Write-Host "  Test 2: Larger cam" -ForegroundColor Gray
        python -m campro.testing.start_agent_session --duration 30 --use-kotlin-ui --test-config $testConfigFile --test-param-index 1
        
        Write-Host "  Test 3: Different timing" -ForegroundColor Gray
        python -m campro.testing.start_agent_session --duration 30 --use-kotlin-ui --test-config $testConfigFile --test-param-index 2
    } else {
        Write-Host "  Running tests with PyQt5..." -ForegroundColor Gray
        Write-Host "  Test 1: Default parameters" -ForegroundColor Gray
        python -m campro.testing.start_agent_session --duration 30 --test-config $testConfigFile --test-param-index 0
        
        Write-Host "  Test 2: Larger cam" -ForegroundColor Gray
        python -m campro.testing.start_agent_session --duration 30 --test-config $testConfigFile --test-param-index 1
        
        Write-Host "  Test 3: Different timing" -ForegroundColor Gray
        python -m campro.testing.start_agent_session --duration 30 --test-config $testConfigFile --test-param-index 2
    }
    Write-Host "  Animation tests completed successfully." -ForegroundColor Green
} catch {
    Write-Host "  Error running animation tests: $_" -ForegroundColor Red
    exit 1
}

# Step 5: Test fallback mode
Write-Host "Step 5: Testing fallback mode..." -ForegroundColor Yellow

# Create a backup of the native library if it exists
$nativeLibDir = Join-Path -Path $baseDir -ChildPath "desktop\src\main\resources\native\windows\x86_64"
$nativeLib = Join-Path -Path $nativeLibDir -ChildPath "campro_motion.dll"
$backupLib = Join-Path -Path $nativeLibDir -ChildPath "campro_motion.dll.bak"

if (Test-Path $nativeLib) {
    Write-Host "  Backing up native library..." -ForegroundColor Gray
    Copy-Item -Path $nativeLib -Destination $backupLib -Force
    Remove-Item -Path $nativeLib -Force
    
    try {
        Write-Host "  Running test in fallback mode..." -ForegroundColor Gray
        if ($useKotlinUI) {
            python -m campro.testing.start_agent_session --duration 30 --use-kotlin-ui --test-config $testConfigFile --test-param-index 0
        } else {
            python -m campro.testing.start_agent_session --duration 30 --test-config $testConfigFile --test-param-index 0
        }
        Write-Host "  Fallback mode test completed successfully." -ForegroundColor Green
    } catch {
        Write-Host "  Error running fallback mode test: $_" -ForegroundColor Red
    } finally {
        # Restore the native library
        Write-Host "  Restoring native library..." -ForegroundColor Gray
        Copy-Item -Path $backupLib -Destination $nativeLib -Force
        Remove-Item -Path $backupLib -Force
    }
} else {
    Write-Host "  Native library not found. Already in fallback mode." -ForegroundColor Yellow
    
    try {
        Write-Host "  Running test in fallback mode..." -ForegroundColor Gray
        if ($useKotlinUI) {
            python -m campro.testing.start_agent_session --duration 30 --use-kotlin-ui --test-config $testConfigFile --test-param-index 0
        } else {
            python -m campro.testing.start_agent_session --duration 30 --test-config $testConfigFile --test-param-index 0
        }
        Write-Host "  Fallback mode test completed successfully." -ForegroundColor Green
    } catch {
        Write-Host "  Error running fallback mode test: $_" -ForegroundColor Red
    }
}

# Step 6: Performance test
Write-Host "Step 6: Running performance test..." -ForegroundColor Yellow

# Create a performance test configuration
$perfTestConfigFile = Join-Path -Path $testResultsDir -ChildPath "perf_test_config.json"
$perfTestConfig = @{
    "test_parameters" = $testParameters[0]
    "test_duration" = 60
    "test_mode" = "performance"
    "frame_rate_target" = 60
}
$perfTestConfig | ConvertTo-Json -Depth 4 | Set-Content -Path $perfTestConfigFile

try {
    Write-Host "  Running performance test..." -ForegroundColor Gray
    if ($useKotlinUI) {
        python -m campro.testing.start_agent_session --duration 60 --use-kotlin-ui --test-config $perfTestConfigFile
    } else {
        python -m campro.testing.start_agent_session --duration 60 --test-config $perfTestConfigFile
    }
    Write-Host "  Performance test completed successfully." -ForegroundColor Green
} catch {
    Write-Host "  Error running performance test: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Animation rendering tests completed!" -ForegroundColor Cyan
Write-Host "Check the test_results/animation_test directory for test data and reports." -ForegroundColor Cyan