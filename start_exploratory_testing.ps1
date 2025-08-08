# start_exploratory_testing.ps1
# One-click script for CamProV5 exploratory testing

# Set the base directory
$baseDir = "D:\Development\engine\CamProV5"
$testingModule = "campro.testing"
$mainModule = "campro.main"

Write-Host "CamProV5 Exploratory Testing" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
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

# Step 2: Set up the testing environment
Write-Host "Step 2: Setting up testing environment..." -ForegroundColor Yellow

# Check if PyQt5 is installed and install it if needed
Write-Host "  Checking for PyQt5..." -ForegroundColor Gray
Write-Host "  (PyQt5 is required for displaying a GUI during in-the-loop testing)" -ForegroundColor Gray
$pyqt5Installed = python -c "try: import PyQt5; print('PyQt5 is installed'); exit(0)\nexcept ImportError: print('PyQt5 is not installed'); exit(1)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  PyQt5 is not installed. Installing PyQt5..." -ForegroundColor Yellow
    Write-Host "  This may take a few minutes..." -ForegroundColor Yellow
    pip install PyQt5
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  PyQt5 installed successfully." -ForegroundColor Green
        Write-Host "  You will now see a GUI when running the in-the-loop testing." -ForegroundColor Green
        
        # Offer to test PyQt5 installation
        $testPyQt5 = Read-Host "  Would you like to verify PyQt5 is working correctly? (y/n)"
        if ($testPyQt5 -eq "y") {
            Write-Host "  Running PyQt5 test. A window should appear..." -ForegroundColor Yellow
            python $baseDir\test_pyqt5.py
            Write-Host "  PyQt5 test completed." -ForegroundColor Green
        }
    } else {
        Write-Host "  Failed to install PyQt5. The application will use a mock UI implementation." -ForegroundColor Red
        Write-Host "  WARNING: Without PyQt5, no GUI will appear, making in-the-loop testing impossible." -ForegroundColor Red
        Write-Host "  To install PyQt5 manually, run: pip install PyQt5" -ForegroundColor Red
        
        $continue = Read-Host "  Do you want to continue without a GUI? (y/n)"
        if ($continue -ne "y") {
            Write-Host "  Exiting script. Please install PyQt5 and try again." -ForegroundColor Yellow
            exit 1
        }
        Write-Host "  Continuing with mock UI (no visible GUI will appear)..." -ForegroundColor Yellow
    }
} else {
    Write-Host "  PyQt5 is already installed." -ForegroundColor Green
    Write-Host "  You will see a GUI when running the in-the-loop testing." -ForegroundColor Green
    
    # Offer to test PyQt5 installation
    $testPyQt5 = Read-Host "  Would you like to verify PyQt5 is working correctly? (y/n)"
    if ($testPyQt5 -eq "y") {
        Write-Host "  Running PyQt5 test. A window should appear..." -ForegroundColor Yellow
        python $baseDir\test_pyqt5.py
        Write-Host "  PyQt5 test completed." -ForegroundColor Green
    }
}

# Ensure the testing directories exist
$testResultsDir = Join-Path -Path $baseDir -ChildPath "test_results\in_the_loop"
$scenariosDir = Join-Path -Path $testResultsDir -ChildPath "scenarios"

if (-not (Test-Path $testResultsDir)) {
    Write-Host "  Creating directory: $testResultsDir" -ForegroundColor Gray
    New-Item -Path $testResultsDir -ItemType Directory -Force | Out-Null
}

if (-not (Test-Path $scenariosDir)) {
    Write-Host "  Creating directory: $scenariosDir" -ForegroundColor Gray
    New-Item -Path $scenariosDir -ItemType Directory -Force | Out-Null
}

# Create agent_config.json if it doesn't exist
$configFile = Join-Path -Path $testResultsDir -ChildPath "agent_config.json"
if (-not (Test-Path $configFile)) {
    Write-Host "  Creating agent configuration file..." -ForegroundColor Gray
    $agentConfig = @{
        agent = @{
            observation_frequency = 1.0
            suggestion_threshold = 0.7
            learning_mode = $true
        }
        testing = @{
            results_dir = $testResultsDir
            session_timeout = 1800
            auto_save = $true
            auto_save_interval = 300
        }
        ui = @{
            components_to_monitor = @(
                "ParameterInputForm"
                "CycloidalAnimationWidget"
                "PlotCarouselWidget"
                "DataDisplayPanel"
            )
        }
    }
    
    $agentConfig | ConvertTo-Json -Depth 4 | Set-Content -Path $configFile
    Write-Host "  Agent configuration file created." -ForegroundColor Green
} else {
    Write-Host "  Agent configuration file already exists." -ForegroundColor Green
}

# Create default scenarios if they don't exist
$scenario1File = Join-Path -Path $scenariosDir -ChildPath "scenario_1.json"
$scenario2File = Join-Path -Path $scenariosDir -ChildPath "scenario_2.json"

if (-not (Test-Path $scenario1File)) {
    Write-Host "  Creating default scenarios..." -ForegroundColor Gray
    
    # Parameter Validation Test
    $scenario1 = @{
        name = "Parameter Validation Test"
        steps = @(
            "Enter negative value for base_circle_radius"
            "Observe error message"
            "Enter valid value"
            "Proceed to next parameter"
        )
        expected_outcomes = @(
            "Error message displayed for negative value"
            "Form accepts valid value"
            "Focus moves to next field"
        )
    }
    
    $scenario1 | ConvertTo-Json -Depth 4 | Set-Content -Path $scenario1File
    
    # Visualization Responsiveness Test
    $scenario2 = @{
        name = "Visualization Responsiveness Test"
        steps = @(
            "Set base_circle_radius to 10"
            "Set rolling_circle_radius to 5"
            "Set tracing_point_distance to 3"
            "Click 'Generate Animation' button"
            "Observe animation"
            "Change parameters and regenerate"
        )
        expected_outcomes = @(
            "Animation renders within 2 seconds"
            "Animation accurately reflects parameters"
            "UI remains responsive during rendering"
        )
    }
    
    $scenario2 | ConvertTo-Json -Depth 4 | Set-Content -Path $scenario2File
    Write-Host "  Default scenarios created." -ForegroundColor Green
} else {
    Write-Host "  Default scenarios already exist." -ForegroundColor Green
}

Write-Host "  Testing environment setup complete." -ForegroundColor Green

# Step 3: Check for Kotlin UI
Write-Host "Step 3: Checking for Kotlin UI..." -ForegroundColor Yellow

# Check if the Kotlin UI desktop JAR exists
$kotlinUIJar = Join-Path -Path $baseDir -ChildPath "desktop\build\libs\CamProV5-desktop.jar"
$kotlinUIAvailable = $false

if (Test-Path $kotlinUIJar) {
    # Check if Java is available
    try {
        $javaVersion = java -version 2>&1
        Write-Host "  Kotlin UI is available." -ForegroundColor Green
        Write-Host "  You can use the Kotlin UI for in-the-loop testing." -ForegroundColor Green
        $kotlinUIAvailable = $true
        
        # Offer to test Kotlin UI installation
        $testKotlinUI = Read-Host "  Would you like to use the Kotlin UI for testing? (y/n)"
        if ($testKotlinUI -eq "y") {
            $useKotlinUI = $true
            Write-Host "  Will use Kotlin UI for testing." -ForegroundColor Green
        } else {
            $useKotlinUI = $false
            Write-Host "  Will use PyQt5 for testing." -ForegroundColor Green
        }
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

# Step 4: Run exploratory testing
Write-Host "Step 4: Starting exploratory testing session..." -ForegroundColor Yellow

# Change to the base directory
Set-Location -Path $baseDir

# Define the duration for the testing session (in minutes)
$duration = 30

Write-Host "  Launching exploratory testing session (duration: $duration minutes)" -ForegroundColor Gray
Write-Host "  Press Ctrl+C to end the session early" -ForegroundColor Gray
Write-Host ""

# Run the exploratory testing session
try {
    if ($useKotlinUI) {
        python -m campro.testing.start_agent_session --duration $duration --use-kotlin-ui
    } else {
        python -m campro.testing.start_agent_session --duration $duration
    }
    Write-Host "  Testing session completed successfully." -ForegroundColor Green
} catch {
    Write-Host "  Error running testing session: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Exploratory testing completed!" -ForegroundColor Cyan
Write-Host "Check the test_results/in_the_loop directory for session data and reports." -ForegroundColor Cyan