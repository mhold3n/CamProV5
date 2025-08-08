"""
Script for creating test scenarios for in-the-loop testing with agentic AI.

This script provides functionality to create and manage test scenarios
for in-the-loop testing with agentic AI.
"""

import os
import json
import argparse
from pathlib import Path
from campro.utils.logging import info, error

def create_default_scenarios():
    """
    Create default test scenarios for in-the-loop testing.
    
    This function creates a set of default test scenarios that cover
    common testing areas for the CamProV5 application.
    
    Returns:
        list: The created scenarios
    """
    print_message("Creating default test scenarios...")
    
    try:
        # Define paths
        base_dir = Path("D:/Development/engine/CamProV5")
        scenarios_dir = base_dir / "test_results" / "in_the_loop" / "scenarios"
        
        # Ensure the scenarios directory exists
        os.makedirs(scenarios_dir, exist_ok=True)
        
        # Define default scenarios
        scenarios = [
            {
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
            },
            {
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
            },
            {
                "name": "Error Handling Test",
                "steps": [
                    "Enter invalid characters in numeric fields",
                    "Enter extremely large values",
                    "Enter zero values where not allowed",
                    "Try to generate animation with invalid parameters"
                ],
                "expected_outcomes": [
                    "Clear error messages for invalid inputs",
                    "Appropriate handling of extreme values",
                    "Validation prevents animation with invalid parameters"
                ]
            }
        ]
        
        # Save each scenario to a file
        for i, scenario in enumerate(scenarios, 1):
            scenario_file = scenarios_dir / f"scenario_{i}.json"
            with open(scenario_file, 'w') as f:
                json.dump(scenario, f, indent=4)
            print_message(f"Created scenario file: {scenario_file}")
        
        print_message(f"Created {len(scenarios)} default scenarios")
        return scenarios
        
    except Exception as e:
        error(f"Error creating default scenarios: {e}", target="campro.testing.create_scenarios")
        return []

def create_custom_scenario(name, steps, expected_outcomes):
    """
    Create a custom test scenario.
    
    Args:
        name (str): The name of the scenario
        steps (list): The steps to follow in the scenario
        expected_outcomes (list): The expected outcomes of the scenario
        
    Returns:
        dict: The created scenario
    """
    try:
        # Define paths
        base_dir = Path("D:/Development/engine/CamProV5")
        scenarios_dir = base_dir / "test_results" / "in_the_loop" / "scenarios"
        
        # Ensure the scenarios directory exists
        os.makedirs(scenarios_dir, exist_ok=True)
        
        # Create the scenario
        scenario = {
            "name": name,
            "steps": steps,
            "expected_outcomes": expected_outcomes
        }
        
        # Generate a unique filename based on the scenario name
        safe_name = name.lower().replace(" ", "_")
        scenario_file = scenarios_dir / f"{safe_name}.json"
        
        # Save the scenario to a file
        with open(scenario_file, 'w') as f:
            json.dump(scenario, f, indent=4)
            
        print_message(f"Created custom scenario: {name}")
        print_message(f"Saved to file: {scenario_file}")
        
        return scenario
        
    except Exception as e:
        error(f"Error creating custom scenario: {e}", target="campro.testing.create_scenarios")
        return None

def list_scenarios():
    """
    List all available test scenarios.
    
    Returns:
        list: The names of all available scenarios
    """
    try:
        # Define paths
        base_dir = Path("D:/Development/engine/CamProV5")
        scenarios_dir = base_dir / "test_results" / "in_the_loop" / "scenarios"
        
        # Check if the scenarios directory exists
        if not os.path.exists(scenarios_dir):
            print_message(f"Scenarios directory not found: {scenarios_dir}")
            return []
            
        # Get all JSON files in the scenarios directory
        scenario_files = [f for f in os.listdir(scenarios_dir) if f.endswith('.json')]
        
        if not scenario_files:
            print_message("No scenarios found.")
            return []
            
        # Load each scenario and extract its name
        scenarios = []
        for file_name in scenario_files:
            file_path = scenarios_dir / file_name
            try:
                with open(file_path, 'r') as f:
                    scenario = json.load(f)
                    if 'name' in scenario:
                        scenarios.append((scenario['name'], file_path))
            except Exception as e:
                error(f"Error loading scenario file {file_path}: {e}", target="campro.testing.create_scenarios")
                
        # Sort scenarios by name
        scenarios.sort(key=lambda x: x[0])
        
        # Print the list of scenarios
        print_message("Available scenarios:")
        for i, (name, path) in enumerate(scenarios, 1):
            print_message(f"{i}. {name} ({path})")
            
        return [name for name, _ in scenarios]
        
    except Exception as e:
        error(f"Error listing scenarios: {e}", target="campro.testing.create_scenarios")
        return []

def print_message(message):
    """
    Print a message to the console.
    
    Args:
        message (str): The message to print
    """
    # Use the logging system
    info(message, target="campro.testing.create_scenarios")

def main():
    """
    Main function to create test scenarios.
    """
    parser = argparse.ArgumentParser(description="Test Scenario Creation Tool")
    
    # Add arguments
    parser.add_argument("--default", action="store_true", help="Create default scenarios")
    parser.add_argument("--list", action="store_true", help="List available scenarios")
    parser.add_argument("--create", action="store_true", help="Create a custom scenario")
    parser.add_argument("--name", type=str, help="Name of the custom scenario")
    parser.add_argument("--steps", type=str, help="Comma-separated list of steps for the custom scenario")
    parser.add_argument("--outcomes", type=str, help="Comma-separated list of expected outcomes for the custom scenario")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Print header
    print_message("Test Scenario Creation Tool")
    print_message("==========================")
    print_message("")
    
    # Handle arguments
    if args.default:
        print_message("Creating default scenarios...")
        scenarios = create_default_scenarios()
        print_message(f"Created {len(scenarios)} default scenarios")
    elif args.list:
        print_message("Listing available scenarios...")
        list_scenarios()
    elif args.create:
        if not args.name:
            print_message("Error: --name is required when using --create")
            return
            
        if not args.steps:
            print_message("Error: --steps is required when using --create")
            return
            
        if not args.outcomes:
            print_message("Error: --outcomes is required when using --create")
            return
            
        # Parse steps and outcomes
        steps = [step.strip() for step in args.steps.split(",")]
        outcomes = [outcome.strip() for outcome in args.outcomes.split(",")]
        
        print_message(f"Creating custom scenario: {args.name}")
        print_message(f"Steps: {steps}")
        print_message(f"Expected outcomes: {outcomes}")
        
        scenario = create_custom_scenario(args.name, steps, outcomes)
        
        if scenario:
            print_message(f"Successfully created custom scenario: {args.name}")
        else:
            print_message(f"Failed to create custom scenario: {args.name}")
    else:
        # No arguments provided, show help
        print_message("This tool helps you create and manage test scenarios")
        print_message("for in-the-loop testing with agentic AI.")
        print_message("")
        print_message("Options:")
        print_message("  --default: Create default scenarios")
        print_message("  --list: List available scenarios")
        print_message("  --create --name NAME --steps STEPS --outcomes OUTCOMES: Create a custom scenario")
        print_message("")
        print_message("Examples:")
        print_message("  python -m campro.testing.create_scenarios --default")
        print_message("  python -m campro.testing.create_scenarios --list")
        print_message('  python -m campro.testing.create_scenarios --create --name "My Test" --steps "Step 1,Step 2" --outcomes "Outcome 1,Outcome 2"')

if __name__ == "__main__":
    main()