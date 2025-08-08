"""
Script for starting an in-the-loop testing session with agentic AI.

This script launches the CamProV5 application in testing mode
and connects the agentic AI to monitor and assist with the testing.
"""

import os
import json
import time
import argparse
import importlib
import subprocess
from pathlib import Path
from .agent import AgentController
from .bridge import KotlinUIBridge
from campro.utils.logging import info, error, warn

def start_agent_session(scenario_name=None, duration_minutes=30, config_path=None, use_kotlin_ui=False):
    """
    Start an in-the-loop testing session with agentic AI.
    
    Args:
        scenario_name (str, optional): The name of the scenario to run.
            If None, starts an exploratory testing session.
        duration_minutes (int, optional): The duration of the session in minutes.
            Defaults to 30 minutes.
        config_path (str, optional): Path to the agent configuration file.
            If None, uses the default configuration file.
        use_kotlin_ui (bool, optional): Whether to use the Kotlin UI instead of PyQt5.
            Defaults to False.
            
    Returns:
        bool: True if the session was started successfully, False otherwise.
    """
    try:
        print_message("Starting in-the-loop testing session with agentic AI...")
        
        # Define paths
        base_dir = Path("D:/Development/engine/CamProV5")
        results_dir = base_dir / "test_results" / "in_the_loop"
        scenarios_dir = results_dir / "scenarios"
        
        if config_path is None:
            config_path = results_dir / "agent_config.json"
            
        # Check if the configuration file exists
        if not os.path.exists(config_path):
            error(f"Configuration file not found: {config_path}", target="campro.testing.start_agent_session")
            return False
            
        # Initialize the agent controller with the configuration file
        print_message(f"Initializing agent controller with configuration: {config_path}")
        agent = AgentController(config_path=config_path)
        print_message("Agent controller initialized")
        
        # Launch the UI in testing mode
        print_message("Launching CamProV5 UI in testing mode")
        
        # Variable to track if we're using the Kotlin UI
        using_kotlin_ui = False
        kotlin_ui_bridge = None
        
        try:
            # Check if we should use the Kotlin UI
            if use_kotlin_ui:
                print_message("Checking for Kotlin UI availability...")
                if KotlinUIBridge.is_available():
                    print_message("Kotlin UI is available. Launching Kotlin UI in testing mode")
                    kotlin_ui_bridge = KotlinUIBridge(testing_mode=True)
                    if kotlin_ui_bridge.start():
                        using_kotlin_ui = True
                        print_message("Kotlin UI launched successfully")
                        
                        # Create a mock main_window object for the agent to connect to
                        class MockMainWindow:
                            def __init__(self):
                                self.testing_mode = True
                                self.enable_agent = True
                                self._object_name = "MainWindow"
                                self._children = []
                                self._layout = None
                                self._bridge = kotlin_ui_bridge
                                
                                # Create mock UI components that the agent is looking for
                                self.ResponsiveLayout = self._create_responsive_layout()
                                
                                # Create the main UI components
                                self.ParameterInputForm = self._create_parameter_input_form()
                                self.CycloidalAnimationWidget = self._create_cycloidal_animation_widget()
                                self.PlotCarouselWidget = self._create_plot_carousel_widget()
                                self.DataDisplayPanel = self._create_data_display_panel()
                                
                                # Add components to children list
                                self._children.extend([
                                    self.ResponsiveLayout,
                                    self.ParameterInputForm,
                                    self.CycloidalAnimationWidget,
                                    self.PlotCarouselWidget,
                                    self.DataDisplayPanel
                                ])
                            
                            def show(self):
                                pass
                                
                            def _create_responsive_layout(self):
                                """Create a mock responsive layout"""
                                class ResponsiveLayout:
                                    def __init__(self, parent):
                                        self.parent = parent
                                        self._object_name = "ResponsiveLayout"
                                        self._children = []
                                        self._containers = {}
                                        
                                    def objectName(self):
                                        return self._object_name
                                        
                                    def children(self):
                                        return self._children
                                        
                                    def getContainers(self):
                                        return self._containers
                                        
                                    def getState(self):
                                        return {
                                            "object_name": self._object_name,
                                            "containers": list(self._containers.keys())
                                        }
                                
                                return ResponsiveLayout(self)
                                
                            def _create_parameter_input_form(self):
                                """Create a mock parameter input form"""
                                class ParameterInputForm:
                                    def __init__(self, parent):
                                        self.parent = parent
                                        self._object_name = "ParameterInputForm"
                                        self._children = []
                                        self._values = {
                                            "base_circle_radius": "10",
                                            "rolling_circle_radius": "5",
                                            "tracing_point_distance": "3"
                                        }
                                        self._is_valid = True
                                        
                                    def objectName(self):
                                        return self._object_name
                                        
                                    def children(self):
                                        return self._children
                                        
                                    def isValid(self):
                                        return self._is_valid
                                        
                                    def getState(self):
                                        # Get the latest values from the bridge if available
                                        # This is a placeholder - in a real implementation, we would
                                        # query the bridge for the current values
                                        return {
                                            "object_name": self._object_name,
                                            "values": self._values,
                                            "is_valid": self._is_valid
                                        }
                                
                                return ParameterInputForm(self)
                                
                            def _create_cycloidal_animation_widget(self):
                                """Create a mock cycloidal animation widget"""
                                class CycloidalAnimationWidget:
                                    def __init__(self, parent):
                                        self.parent = parent
                                        self._object_name = "CycloidalAnimationWidget"
                                        self._children = []
                                        self._is_playing = False
                                        self._current_frame = 0
                                        self._total_frames = 100
                                        
                                    def objectName(self):
                                        return self._object_name
                                        
                                    def children(self):
                                        return self._children
                                        
                                    def isPlaying(self):
                                        return self._is_playing
                                        
                                    def currentFrame(self):
                                        return self._current_frame
                                        
                                    def totalFrames(self):
                                        return self._total_frames
                                        
                                    def getState(self):
                                        # Get the latest state from the bridge if available
                                        return {
                                            "object_name": self._object_name,
                                            "is_playing": self._is_playing,
                                            "current_frame": self._current_frame,
                                            "total_frames": self._total_frames
                                        }
                                
                                return CycloidalAnimationWidget(self)
                                
                            def _create_plot_carousel_widget(self):
                                """Create a mock plot carousel widget"""
                                class PlotCarouselWidget:
                                    def __init__(self, parent):
                                        self.parent = parent
                                        self._object_name = "PlotCarouselWidget"
                                        self._children = []
                                        self._current_plot = 0
                                        self._zoom_level = 1.0
                                        
                                    def objectName(self):
                                        return self._object_name
                                        
                                    def children(self):
                                        return self._children
                                        
                                    def currentPlot(self):
                                        return self._current_plot
                                        
                                    def zoomLevel(self):
                                        return self._zoom_level
                                        
                                    def getState(self):
                                        return {
                                            "object_name": self._object_name,
                                            "current_plot": self._current_plot,
                                            "zoom_level": self._zoom_level
                                        }
                                
                                return PlotCarouselWidget(self)
                                
                            def _create_data_display_panel(self):
                                """Create a mock data display panel"""
                                class DataDisplayPanel:
                                    def __init__(self, parent):
                                        self.parent = parent
                                        self._object_name = "DataDisplayPanel"
                                        self._children = []
                                        self._displayed_data = "simulation_results"
                                        self._filters = {}
                                        
                                    def objectName(self):
                                        return self._object_name
                                        
                                    def children(self):
                                        return self._children
                                        
                                    def displayedData(self):
                                        return self._displayed_data
                                        
                                    def filters(self):
                                        return self._filters
                                        
                                    def getState(self):
                                        return {
                                            "object_name": self._object_name,
                                            "displayed_data": self._displayed_data,
                                            "filters": self._filters
                                        }
                                
                                return DataDisplayPanel(self)
                                
                            def objectName(self):
                                return self._object_name
                                
                            def children(self):
                                return self._children
                                
                            def layout(self):
                                return self._layout
                                
                            def findChild(self, widget_type, name=None):
                                """Find a child widget by name"""
                                for child in self._children:
                                    if hasattr(child, "objectName") and child.objectName() == name:
                                        return child
                                return None
                                
                            def findChildren(self, widget_type, name=None):
                                """Find all child widgets of a given type"""
                                result = []
                                for child in self._children:
                                    if name and hasattr(child, "objectName") and child.objectName() == name:
                                        result.append(child)
                                    elif not name:
                                        result.append(child)
                                return result
                                
                            def getState(self):
                                """Get the state of this window for testing"""
                                return {
                                    "testing_mode": self.testing_mode,
                                    "enable_agent": self.enable_agent,
                                    "object_name": self._object_name,
                                    "components": [child.objectName() for child in self._children if hasattr(child, "objectName")]
                                }
                        
                        main_window = MockMainWindow()
                        main_module = None  # We don't need the main module for Kotlin UI
                    else:
                        print_message("Failed to start Kotlin UI, falling back to PyQt5")
                        kotlin_ui_bridge = None
                else:
                    print_message("Kotlin UI is not available, falling back to PyQt5")
            
            # If we're not using the Kotlin UI, use PyQt5
            if not using_kotlin_ui:
                # Import the main module dynamically
                main_module = importlib.import_module("campro.main")

                # Add these lines to create a QApplication instance before creating any QWidgets
                if hasattr(main_module, 'PYQT5_AVAILABLE') and main_module.PYQT5_AVAILABLE:
                    # Import QApplication from PyQt5 if available
                    from PyQt5.QtWidgets import QApplication
                    import sys
                    # Create the application instance if it doesn't exist
                    if QApplication.instance() is None:
                        app = QApplication(sys.argv)
                        print_message("Created QApplication instance for GUI")

                # Create the main window with testing mode enabled
                main_window = main_module.create_main_window(testing_mode=True, enable_agent=True)
                
                print_message("CamProV5 UI launched in testing mode")
            
            # Connect the agent to the UI
            print_message("Connecting agent to UI")
            agent.connect_to_ui(main_window)
            
            # Load scenario if specified
            if scenario_name:
                # Find the scenario file
                scenario_file = None
                
                # Check if the scenario name is a file path
                if os.path.exists(scenario_name):
                    scenario_file = scenario_name
                else:
                    # Look for the scenario in the scenarios directory
                    for file_name in os.listdir(scenarios_dir):
                        if file_name.endswith('.json'):
                            file_path = scenarios_dir / file_name
                            try:
                                with open(file_path, 'r') as f:
                                    scenario = json.load(f)
                                    if 'name' in scenario and scenario['name'] == scenario_name:
                                        scenario_file = file_path
                                        break
                            except Exception as e:
                                warn(f"Error loading scenario file {file_path}: {e}", target="campro.testing.start_agent_session")
                
                if scenario_file:
                    print_message(f"Running guided test with scenario: {scenario_name}")
                    print_message(f"Loading scenario from file: {scenario_file}")
                    
                    # Load the scenario
                    with open(scenario_file, 'r') as f:
                        scenario = json.load(f)
                        
                    # Present the scenario to the tester
                    agent.present_scenario(scenario)
                else:
                    error(f"Scenario not found: {scenario_name}", target="campro.testing.start_agent_session")
                    return False
            else:
                # Run exploratory testing
                print_message("Running exploratory testing session")
                print_message(f"Session will run for {duration_minutes} minutes")
                
                # Set exploration areas
                exploration_areas = [
                    "Parameter input edge cases",
                    "Visualization responsiveness",
                    "Error handling scenarios",
                    "Performance under load"
                ]
                
                print_message("Areas to explore:")
                for i, area in enumerate(exploration_areas, 1):
                    print_message(f"{i}. {area}")
                    
                # Set the agent to exploratory mode
                agent.set_mode("exploratory")
                agent.set_exploration_areas(exploration_areas)
                
                # Start a timed session
                agent.start_timed_session(duration_minutes * 60)
            
            # Start the session
            session_id = agent.start_session()
            
            print_message(f"\nTesting session started with ID: {session_id}")
            print_message("Follow the agent's guidance and provide feedback when prompted.")
            print_message("To end the session early, press Ctrl+C")
            
            # Start the main event loop
            try:
                if using_kotlin_ui:
                    # For Kotlin UI, we don't need to show the main window
                    # Instead, we monitor events from the Kotlin UI
                    print_message("Using Kotlin UI for testing")
                    
                    # Main testing loop
                    start_time = time.time()
                    end_time = start_time + (duration_minutes * 60)
                    
                    while time.time() < end_time and kotlin_ui_bridge.is_running():
                        # Process events from UI
                        events = kotlin_ui_bridge.get_events()
                        for event in events:
                            # Process event with agent
                            print_message(f"Received event from Kotlin UI: {event}")
                            
                        # Sleep to avoid high CPU usage
                        time.sleep(0.1)
                else:
                    # For PyQt5, show the main window and start the event loop
                    main_window.show()
                    
                    # Check if start_event_loop returns a value (for PyQt5)
                    # or just call it directly (for mock implementation)
                    event_loop_result = main_module.start_event_loop()
                    if hasattr(main_module, 'PYQT5_AVAILABLE') and main_module.PYQT5_AVAILABLE and event_loop_result is not None:
                        # If PyQt5 is available, the event loop will block until the application exits
                        # This code will only be reached when the application exits
                        pass
                    else:
                        # For mock implementation, simulate a short testing session
                        print_message("Using mock UI implementation, simulating a short testing session")
                        print_message("WARNING: No visible GUI will be displayed because PyQt5 is not installed")
                        print_message("For proper in-the-loop testing, please install PyQt5: pip install PyQt5")
                        time.sleep(1)  # Simulate a 1-second testing session
            except KeyboardInterrupt:
                print_message("Testing session interrupted by user")
            finally:
                # Stop the Kotlin UI if it was started
                if using_kotlin_ui and kotlin_ui_bridge is not None:
                    print_message("Stopping Kotlin UI")
                    kotlin_ui_bridge.stop()
                
                # Save the session data
                file_path = agent.save_session_data()
                if file_path:
                    print_message(f"Session data saved to: {file_path}")
                    
                    # Generate a report
                    session_data = agent.get_session_data()
                    report = agent.generate_report(session_data)
                    
                    # Save the report
                    report_path = results_dir / f"report_{session_id}.md"
                    with open(report_path, 'w') as f:
                        f.write(report)
                        
                    print_message(f"Session report saved to: {report_path}")
                
            return True
            
        except ImportError as e:
            error(f"Error importing main module: {e}", target="campro.testing.start_agent_session")
            return False
        except Exception as e:
            error(f"Error launching UI: {e}", target="campro.testing.start_agent_session")
            return False
            
    except Exception as e:
        error(f"Error starting agent session: {e}", target="campro.testing.start_agent_session")
        return False

def print_message(message):
    """
    Print a message to the console.
    
    Args:
        message (str): The message to print
    """
    # Use the logging system
    info(message, target="campro.testing.start_agent_session")

def main():
    """
    Main function to start an in-the-loop testing session.
    """
    parser = argparse.ArgumentParser(description="In-the-Loop Testing with Agentic AI")
    
    # Add arguments
    parser.add_argument("--scenario", type=str, help="Name of the scenario to run")
    parser.add_argument("--duration", type=int, default=30, help="Duration of the session in minutes (default: 30)")
    parser.add_argument("--config", type=str, help="Path to the agent configuration file")
    parser.add_argument("--use-kotlin-ui", action="store_true", help="Use the Kotlin UI instead of PyQt5")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Print header
    print_message("In-the-Loop Testing with Agentic AI")
    print_message("==================================")
    print_message("")
    
    # Start the agent session
    if args.scenario:
        print_message(f"Starting guided testing with scenario: {args.scenario}")
        success = start_agent_session(
            scenario_name=args.scenario,
            duration_minutes=args.duration,
            config_path=args.config,
            use_kotlin_ui=args.use_kotlin_ui
        )
    else:
        print_message(f"Starting exploratory testing session (duration: {args.duration} minutes)")
        success = start_agent_session(
            duration_minutes=args.duration,
            config_path=args.config,
            use_kotlin_ui=args.use_kotlin_ui
        )
        
    if success:
        print_message("Testing session completed successfully")
    else:
        error("Testing session failed", target="campro.testing.start_agent_session")
        return 1
        
    return 0

if __name__ == "__main__":
    main()