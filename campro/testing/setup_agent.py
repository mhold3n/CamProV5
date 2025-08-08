"""
Setup script for the in-the-loop testing environment with agentic AI.

This script prepares the testing environment by:
1. Creating necessary directories for test results
2. Setting up configuration files
3. Initializing the agent controller
"""

import os
import json
from pathlib import Path
from campro.utils.logging import info, error

def setup_testing_environment():
    """
    Set up the testing environment for in-the-loop testing.
    
    This function:
    1. Creates the test_results/in_the_loop directory if it doesn't exist
    2. Creates the test_results/in_the_loop/scenarios directory if it doesn't exist
    3. Creates a sample agent_config.json file
    4. Creates sample scenario files
    
    Returns:
        bool: True if setup was successful, False otherwise
    """
    print_message("Setting up in-the-loop testing environment with agentic AI...")
    
    try:
        # Define paths
        base_dir = Path("D:/Development/engine/CamProV5")
        results_dir = base_dir / "test_results" / "in_the_loop"
        scenarios_dir = results_dir / "scenarios"
        config_file = results_dir / "agent_config.json"
        
        # Create directories
        print_message(f"Creating test results directory: {results_dir}")
        os.makedirs(results_dir, exist_ok=True)
        
        print_message(f"Creating scenarios directory: {scenarios_dir}")
        os.makedirs(scenarios_dir, exist_ok=True)
        
        # Create configuration file
        print_message(f"Creating configuration file: {config_file}")
        agent_config = {
            "agent": {
                "observation_frequency": 1.0,
                "suggestion_threshold": 0.7,
                "learning_mode": True
            },
            "testing": {
                "results_dir": str(results_dir),
                "session_timeout": 1800,
                "auto_save": True,
                "auto_save_interval": 300
            },
            "ui": {
                "components_to_monitor": [
                    "ParameterInputForm",
                    "CycloidalAnimationWidget",
                    "PlotCarouselWidget",
                    "DataDisplayPanel"
                ]
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(agent_config, f, indent=4)
        
        # Create sample scenarios
        print_message("Creating sample scenarios")
        
        # Scenario 1: Parameter Validation Test
        scenario1_file = scenarios_dir / "scenario_1.json"
        scenario1 = {
            "name": "Parameter Validation Test",
            "steps": [
                "Enter negative value for base_circle_radius",
                "Observe error message",
                "Enter valid value",
                "Proceed to next parameter"
            ],
            "expected_outcomes": [
                "Error message displayed for negative value",
                "Form accepts valid value",
                "Focus moves to next field"
            ]
        }
        
        with open(scenario1_file, 'w') as f:
            json.dump(scenario1, f, indent=4)
            
        # Scenario 2: Visualization Responsiveness Test
        scenario2_file = scenarios_dir / "scenario_2.json"
        scenario2 = {
            "name": "Visualization Responsiveness Test",
            "steps": [
                "Set base_circle_radius to 10",
                "Set rolling_circle_radius to 5",
                "Set tracing_point_distance to 3",
                "Click 'Generate Animation' button",
                "Observe animation",
                "Change parameters and regenerate"
            ],
            "expected_outcomes": [
                "Animation renders within 2 seconds",
                "Animation accurately reflects parameters",
                "UI remains responsive during rendering"
            ]
        }
        
        with open(scenario2_file, 'w') as f:
            json.dump(scenario2, f, indent=4)
        
        print_message("\nTesting environment setup complete!")
        print_message("You can now start in-the-loop testing with:")
        print_message("python -m campro.testing.start_agent_session")
        
        return True
        
    except Exception as e:
        error(f"Error setting up testing environment: {e}", target="campro.testing.setup_agent")
        return False

def print_message(message):
    """
    Print a message to the console.
    
    Args:
        message (str): The message to print
    """
    # Use the logging system
    info(message, target="campro.testing.setup_agent")

def main():
    """
    Main function to set up the testing environment.
    """
    setup_testing_environment()

if __name__ == "__main__":
    main()