#!/usr/bin/env python3
"""
Test script for the Kotlin UI.

This script tests the functionality of the Kotlin UI by using the KotlinUIBridge
to interact with the UI and verify that all components work as expected.
"""

import os
import sys
import time
import json
from bridge import KotlinUIBridge

def print_header(title):
    """Print a header for a test section."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def print_test(name, passed):
    """Print the result of a test."""
    result = "PASSED" if passed else "FAILED"
    color = "\033[92m" if passed else "\033[91m"  # Green for passed, red for failed
    reset = "\033[0m"
    print(f"{color}{result}{reset}: {name}")

def wait_for_event(bridge, event_type, timeout=5, component=None):
    """
    Wait for an event of the specified type.
    
    Args:
        bridge: The KotlinUIBridge instance
        event_type: The type of event to wait for
        timeout: The maximum time to wait in seconds
        component: The component to wait for (optional)
        
    Returns:
        The event if found, None otherwise
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        events = bridge.get_events()
        for event in events:
            if event.get("type") == event_type:
                if component is None or event.get("component") == component:
                    return event
        time.sleep(0.1)
    return None

def test_parameter_input_form(bridge):
    """Test the ParameterInputForm component."""
    print_header("Testing ParameterInputForm")
    
    # Test selecting a parameter tab
    print("Selecting 'Combustion' tab...")
    bridge.select_parameter_tab("Combustion")
    event = wait_for_event(bridge, "command_executed", component="ParameterTab")
    passed = event is not None and event.get("value") == "Combustion"
    print_test("Select parameter tab", passed)
    
    # Test setting a parameter value
    print("Setting 'Manifold Pressure' to '120000.0'...")
    bridge.set_parameter_value("Manifold Pressure", "120000.0")
    event = wait_for_event(bridge, "command_executed", component="Manifold Pressure")
    passed = event is not None and event.get("value") == "120000.0"
    print_test("Set parameter value", passed)
    
    # Test generating animation
    print("Generating animation...")
    bridge.generate_animation()
    event = wait_for_event(bridge, "command_executed", component="GenerateAnimationButton")
    passed = event is not None
    print_test("Generate animation", passed)
    
    # Wait for animation to start
    event = wait_for_event(bridge, "animation_started", timeout=10)
    passed = event is not None
    print_test("Animation started", passed)
    
    return passed

def test_cycloidal_animation_widget(bridge):
    """Test the CycloidalAnimationWidget component."""
    print_header("Testing CycloidalAnimationWidget")
    
    # Test pausing the animation
    print("Pausing animation...")
    bridge.pause_animation()
    event = wait_for_event(bridge, "command_executed", component="PauseButton")
    passed = event is not None
    print_test("Pause animation", passed)
    
    # Test playing the animation
    print("Playing animation...")
    bridge.play_animation()
    event = wait_for_event(bridge, "command_executed", component="PlayButton")
    passed = event is not None
    print_test("Play animation", passed)
    
    # Test setting animation speed
    print("Setting animation speed to 2.0...")
    bridge.set_animation_speed(2.0)
    event = wait_for_event(bridge, "command_executed", component="SpeedSlider")
    passed = event is not None and event.get("value") == "2.0"
    print_test("Set animation speed", passed)
    
    # Test zooming in
    print("Zooming in...")
    bridge.zoom_in_animation()
    event = wait_for_event(bridge, "command_executed", component="ZoomInButton")
    passed = event is not None
    print_test("Zoom in", passed)
    
    # Test zooming out
    print("Zooming out...")
    bridge.zoom_out_animation()
    event = wait_for_event(bridge, "command_executed", component="ZoomOutButton")
    passed = event is not None
    print_test("Zoom out", passed)
    
    # Test resetting view
    print("Resetting view...")
    bridge.reset_animation_view()
    event = wait_for_event(bridge, "command_executed", component="ResetViewButton")
    passed = event is not None
    print_test("Reset view", passed)
    
    return passed

def test_plot_carousel_widget(bridge):
    """Test the PlotCarouselWidget component."""
    print_header("Testing PlotCarouselWidget")
    
    # Test selecting a plot type
    print("Selecting 'Velocity' plot...")
    bridge.select_plot_type("Velocity")
    event = wait_for_event(bridge, "command_executed", component="PlotTypeTab")
    passed = event is not None and event.get("value") == "Velocity"
    print_test("Select plot type", passed)
    
    # Test zooming in
    print("Zooming in...")
    bridge.zoom_in_plot()
    event = wait_for_event(bridge, "command_executed", component="PlotZoomInButton")
    passed = event is not None
    print_test("Zoom in", passed)
    
    # Test zooming out
    print("Zooming out...")
    bridge.zoom_out_plot()
    event = wait_for_event(bridge, "command_executed", component="PlotZoomOutButton")
    passed = event is not None
    print_test("Zoom out", passed)
    
    # Test resetting view
    print("Resetting view...")
    bridge.reset_plot_view()
    event = wait_for_event(bridge, "command_executed", component="PlotResetViewButton")
    passed = event is not None
    print_test("Reset view", passed)
    
    return passed

def test_data_display_panel(bridge):
    """Test the DataDisplayPanel component."""
    print_header("Testing DataDisplayPanel")
    
    # Test selecting a data tab
    print("Selecting 'Kinematics' tab...")
    bridge.select_data_tab("Kinematics")
    event = wait_for_event(bridge, "command_executed", component="DataDisplayTab")
    passed = event is not None and event.get("value") == "Kinematics"
    print_test("Select data tab", passed)
    
    # Test exporting data as CSV
    print("Exporting data as CSV...")
    bridge.export_data_csv()
    event = wait_for_event(bridge, "command_executed", component="ExportCSVButton")
    passed = event is not None
    print_test("Export data as CSV", passed)
    
    # Test generating a report
    print("Generating report...")
    bridge.generate_report()
    event = wait_for_event(bridge, "command_executed", component="GenerateReportButton")
    passed = event is not None
    print_test("Generate report", passed)
    
    return passed

def main():
    """Main function."""
    print_header("Kotlin UI Test Script")
    
    # Create a bridge to the Kotlin UI
    bridge = KotlinUIBridge(testing_mode=True)
    
    # Check if the Kotlin UI is available
    if not bridge.is_available():
        print("ERROR: Kotlin UI is not available.")
        return 1
    
    # Start the Kotlin UI
    print("Starting Kotlin UI...")
    if not bridge.start():
        print("ERROR: Failed to start Kotlin UI.")
        return 1
    
    print("Kotlin UI started successfully.")
    
    try:
        # Wait for UI to initialize
        print("Waiting for UI to initialize...")
        event = wait_for_event(bridge, "ui_initialized", timeout=10)
        if event is None:
            print("ERROR: UI initialization timeout.")
            return 1
        
        print("UI initialized successfully.")
        
        # Run tests
        tests_passed = 0
        tests_total = 4
        
        # Test ParameterInputForm
        if test_parameter_input_form(bridge):
            tests_passed += 1
        
        # Test CycloidalAnimationWidget
        if test_cycloidal_animation_widget(bridge):
            tests_passed += 1
        
        # Test PlotCarouselWidget
        if test_plot_carousel_widget(bridge):
            tests_passed += 1
        
        # Test DataDisplayPanel
        if test_data_display_panel(bridge):
            tests_passed += 1
        
        # Print summary
        print_header("Test Summary")
        print(f"Tests passed: {tests_passed}/{tests_total}")
        
        if tests_passed == tests_total:
            print("\nAll tests passed!")
            return 0
        else:
            print("\nSome tests failed.")
            return 1
    
    finally:
        # Stop the Kotlin UI
        print("\nStopping Kotlin UI...")
        bridge.stop()
        print("Kotlin UI stopped.")

if __name__ == "__main__":
    sys.exit(main())