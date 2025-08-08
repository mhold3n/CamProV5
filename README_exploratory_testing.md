# CamProV5 Exploratory Testing

This document provides instructions for using the one-click exploratory testing script for CamProV5.

## Overview

The `start_exploratory_testing.ps1` PowerShell script provides a convenient one-click solution for running exploratory testing sessions with CamProV5. It automates the process of setting up the testing environment and starting an exploratory testing session with agentic AI assistance.

> **Important**: For proper in-the-loop testing, a graphical user interface (GUI) is required. The script will automatically check for and install PyQt5 if it's not already installed. PyQt5 is necessary to display the actual UI components that you'll interact with during testing.

## What the Script Does

1. **Terminates Previous Testing Instances**:
   - Finds and kills any Python processes running CamProV5 testing modules to ensure a clean testing environment

2. **Sets Up the Testing Environment**:
   - Checks if PyQt5 is installed and installs it if needed
   - Offers to verify PyQt5 is working correctly by displaying a test window
   - Creates the necessary directories if they don't exist:
     - `test_results/in_the_loop`
     - `test_results/in_the_loop/scenarios`
   - Creates the agent configuration file (`agent_config.json`) if it doesn't exist
   - Creates default test scenarios if they don't exist:
     - Parameter Validation Test
     - Visualization Responsiveness Test

3. **Runs Exploratory Testing**:
   - Launches the exploratory testing session with a 30-minute duration
   - Displays a GUI for user interaction (if PyQt5 is installed)
   - Provides feedback on the progress
   - Handles errors gracefully
   - Saves session data and generates a report

## How to Use the Script

1. **Prerequisites**:
   - PowerShell 5.0 or later
   - Python with the CamProV5 project installed
   - Appropriate permissions to create files and directories in the project folder

2. **Running the Script**:
   - Open PowerShell
   - Navigate to the CamProV5 project directory:
     ```powershell
     cd D:\Development\engine\CamProV5
     ```
   - Run the script:
     ```powershell
     .\start_exploratory_testing.ps1
     ```
   - Alternatively, right-click on the script in File Explorer and select "Run with PowerShell"

3. **During the Testing Session**:
   - Follow the agent's guidance for exploratory testing
   - The agent will suggest areas to explore and provide feedback
   - Press Ctrl+C to end the session early if needed

4. **After the Testing Session**:
   - Check the `test_results/in_the_loop` directory for session data and reports
   - Review the generated report (named `report_test_session_[TIMESTAMP].md`)
   - Analyze the insights and observations from the testing session

## Customization

You can modify the script to change:

- The testing duration by changing the `$duration` variable (default: 30 minutes)
- The base directory by changing the `$baseDir` variable
- The agent configuration settings in the `$agentConfig` object

## Troubleshooting

If you encounter any issues:

1. **No GUI Appears**: The most common reason for not seeing a GUI is that PyQt5 is not installed. The script attempts to install it automatically, but if that fails:
   ```powershell
   pip install PyQt5
   ```
   After installing PyQt5, run the script again. A visible GUI is essential for in-the-loop testing as it allows you to interact with the application.

2. **Script Execution Policy**: If PowerShell prevents the script from running due to execution policy, you may need to run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

3. **Python Not Found**: Ensure Python is installed and in your PATH

4. **Missing Modules**: If any Python modules are missing, install them using pip:
   ```powershell
   pip install -r requirements.txt
   ```

5. **Permission Issues**: Ensure you have write permissions to the CamProV5 directory

## Why a GUI is Essential for In-the-Loop Testing

In-the-loop testing requires human interaction with the application's user interface. Without a visible GUI:

1. You cannot interact with UI components like forms, buttons, and visualizations
2. You cannot observe the application's behavior in response to your inputs
3. The agent cannot monitor your interactions with the UI

The script now automatically checks for and installs PyQt5 to ensure you have a proper GUI for testing. If you see a message like "Using mock UI implementation" or "No visible GUI will be displayed", it means PyQt5 is not installed correctly, and you should install it manually using the command above.

## Output Files

The script generates the following files:

- `test_results/in_the_loop/session_test_session_[TIMESTAMP].json`: Contains the raw session data
- `test_results/in_the_loop/report_test_session_[TIMESTAMP].md`: Contains a human-readable report with insights and observations