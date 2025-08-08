"""
Bridge for launching and communicating with the Kotlin UI.

This module provides a bridge between the testing environment and the Kotlin UI,
allowing the testing environment to launch and interact with the actual production UI.
"""

import subprocess
import os
import time
import json
import threading

class KotlinUIBridge:
    """Bridge for launching and communicating with the Kotlin UI."""
    
    def __init__(self, testing_mode=True):
        """
        Initialize the Kotlin UI bridge.
        
        Args:
            testing_mode (bool): Whether to launch the UI in testing mode.
        """
        self.process = None
        self.testing_mode = testing_mode
        self.event_queue = []
        self.running = False
        
    def start(self):
        """
        Launch the Kotlin UI process.
        
        Returns:
            bool: True if the process was started successfully, False otherwise.
        """
        if self.process is not None:
            self.stop()
            
        # Path to the desktop launcher JAR
        # Use raw string with backslash after drive letter to ensure correct path format
        jar_path = r"D:\Development\engine\CamProV5\desktop\build\libs\CamProV5-desktop.jar"
        
        # Check if the JAR file exists
        if not os.path.exists(jar_path):
            print(f"Desktop launcher JAR not found: {jar_path}")
            return False
        
        # Launch with testing flag
        # Use the Java installation at D:\Java with raw string for correct path format
        java_path = r"D:\Java\bin\java"
        cmd = [java_path, "-jar", jar_path, "--testing-mode", "--enable-agent"]
        
        try:
            # Start the process
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Start monitoring thread
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_process)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            # Wait for UI to initialize
            time.sleep(2)
            return self.process.poll() is None
        except Exception as e:
            print(f"Error starting Kotlin UI: {e}")
            return False
        
    def stop(self):
        """
        Stop the Kotlin UI process.
        """
        if self.process is not None:
            self.running = False
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            
    def _monitor_process(self):
        """
        Monitor the process output for events.
        """
        while self.running and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line.startswith("EVENT:"):
                # Parse event from UI
                try:
                    event_data = json.loads(line[6:].strip())
                    self.event_queue.append(event_data)
                except json.JSONDecodeError as e:
                    print(f"Error parsing event: {e}")
                
    def send_command(self, command, params=None):
        """
        Send a command to the UI.
        
        Args:
            command (str): The command to send.
            params (dict, optional): Parameters for the command.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        if self.process is None or self.process.poll() is not None:
            return False
            
        cmd_obj = {"command": command}
        if params:
            cmd_obj["params"] = params
            
        cmd_str = f"COMMAND:{json.dumps(cmd_obj)}\n"
        try:
            self.process.stdin.write(cmd_str)
            self.process.stdin.flush()
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
        
    def get_events(self):
        """
        Get all pending events from the UI.
        
        Returns:
            list: A list of events from the UI.
        """
        events = self.event_queue.copy()
        self.event_queue.clear()
        return events
    
    def is_running(self):
        """
        Check if the Kotlin UI process is running.
        
        Returns:
            bool: True if the process is running, False otherwise.
        """
        return self.process is not None and self.process.poll() is None
    
    # ParameterInputForm component methods
    
    def set_parameter_value(self, parameter_name, value):
        """
        Set a parameter value in the ParameterInputForm.
        
        Args:
            parameter_name (str): The name of the parameter to set.
            value (str): The value to set.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("set_value", {
            "component": parameter_name,
            "value": value
        })
    
    def select_parameter_tab(self, tab_name):
        """
        Select a parameter category tab in the ParameterInputForm.
        
        Args:
            tab_name (str): The name of the tab to select.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("select_tab", {
            "component": "ParameterTab",
            "value": tab_name
        })
    
    def load_preset(self, preset_name=None):
        """
        Load a parameter preset.
        
        Args:
            preset_name (str, optional): The name of the preset to load.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        params = {"component": "LoadPresetButton"}
        if preset_name:
            params["preset"] = preset_name
        return self.send_command("click", params)
    
    def save_preset(self, preset_name=None):
        """
        Save current parameters as a preset.
        
        Args:
            preset_name (str, optional): The name to save the preset as.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        params = {"component": "SavePresetButton"}
        if preset_name:
            params["preset"] = preset_name
        return self.send_command("click", params)
    
    def import_parameters(self, file_path=None):
        """
        Import parameters from a file.
        
        Args:
            file_path (str, optional): The path to the file to import.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        params = {"component": "ImportButton"}
        if file_path:
            params["file_path"] = file_path
        return self.send_command("click", params)
    
    def export_parameters(self, file_path=None):
        """
        Export parameters to a file.
        
        Args:
            file_path (str, optional): The path to export the parameters to.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        params = {"component": "ExportButton"}
        if file_path:
            params["file_path"] = file_path
        return self.send_command("click", params)
    
    def generate_animation(self):
        """
        Generate the animation with the current parameters.
        
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("click", {
            "component": "GenerateAnimationButton"
        })
    
    # CycloidalAnimationWidget component methods
    
    def play_animation(self):
        """
        Play the cycloidal animation.
        
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("click", {
            "component": "PlayButton"
        })
    
    def pause_animation(self):
        """
        Pause the cycloidal animation.
        
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("click", {
            "component": "PauseButton"
        })
    
    def set_animation_speed(self, speed):
        """
        Set the speed of the cycloidal animation.
        
        Args:
            speed (float): The animation speed (0.1 to 3.0).
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("set_value", {
            "component": "SpeedSlider",
            "value": str(speed)
        })
    
    def zoom_in_animation(self):
        """
        Zoom in on the cycloidal animation.
        
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("click", {
            "component": "ZoomInButton"
        })
    
    def zoom_out_animation(self):
        """
        Zoom out on the cycloidal animation.
        
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("click", {
            "component": "ZoomOutButton"
        })
    
    def reset_animation_view(self):
        """
        Reset the view of the cycloidal animation.
        
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("click", {
            "component": "ResetViewButton"
        })
    
    def export_animation(self, file_path=None):
        """
        Export the cycloidal animation.
        
        Args:
            file_path (str, optional): The path to export the animation to.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        params = {"component": "ExportButton"}
        if file_path:
            params["file_path"] = file_path
        return self.send_command("click", params)
    
    def pan_zoom_animation(self, offset_x, offset_y, scale):
        """
        Pan and zoom the cycloidal animation.
        
        Args:
            offset_x (float): The x offset.
            offset_y (float): The y offset.
            scale (float): The zoom scale.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("gesture", {
            "component": "AnimationCanvas",
            "action": "pan_zoom",
            "offset_x": str(offset_x),
            "offset_y": str(offset_y),
            "scale": str(scale)
        })
    
    # PlotCarouselWidget component methods
    
    def select_plot_type(self, plot_type):
        """
        Select a plot type in the PlotCarouselWidget.
        
        Args:
            plot_type (str): The type of plot to select.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("select_tab", {
            "component": "PlotTypeTab",
            "value": plot_type
        })
    
    def zoom_in_plot(self):
        """
        Zoom in on the plot.
        
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("click", {
            "component": "PlotZoomInButton"
        })
    
    def zoom_out_plot(self):
        """
        Zoom out on the plot.
        
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("click", {
            "component": "PlotZoomOutButton"
        })
    
    def reset_plot_view(self):
        """
        Reset the view of the plot.
        
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("click", {
            "component": "PlotResetViewButton"
        })
    
    def export_plot(self, file_path=None):
        """
        Export the plot as an image.
        
        Args:
            file_path (str, optional): The path to export the plot to.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        params = {"component": "PlotExportButton"}
        if file_path:
            params["file_path"] = file_path
        return self.send_command("click", params)
    
    def export_plot_data(self, file_path=None):
        """
        Export the plot data.
        
        Args:
            file_path (str, optional): The path to export the data to.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        params = {"component": "DataExportButton"}
        if file_path:
            params["file_path"] = file_path
        return self.send_command("click", params)
    
    def pan_zoom_plot(self, offset_x, offset_y, scale):
        """
        Pan and zoom the plot.
        
        Args:
            offset_x (float): The x offset.
            offset_y (float): The y offset.
            scale (float): The zoom scale.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("gesture", {
            "component": "PlotCanvas",
            "action": "pan_zoom",
            "offset_x": str(offset_x),
            "offset_y": str(offset_y),
            "scale": str(scale)
        })
    
    # DataDisplayPanel component methods
    
    def select_data_tab(self, tab_name):
        """
        Select a data tab in the DataDisplayPanel.
        
        Args:
            tab_name (str): The name of the tab to select.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        return self.send_command("select_tab", {
            "component": "DataDisplayTab",
            "value": tab_name
        })
    
    def export_data_csv(self, file_path=None):
        """
        Export data as CSV.
        
        Args:
            file_path (str, optional): The path to export the data to.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        params = {"component": "ExportCSVButton"}
        if file_path:
            params["file_path"] = file_path
        return self.send_command("click", params)
    
    def generate_report(self, file_path=None):
        """
        Generate a report.
        
        Args:
            file_path (str, optional): The path to save the report to.
            
        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        params = {"component": "GenerateReportButton"}
        if file_path:
            params["file_path"] = file_path
        return self.send_command("click", params)
    
    @staticmethod
    def is_available():
        """
        Check if the Kotlin UI is available.
        
        Returns:
            bool: True if the Kotlin UI is available, False otherwise.
        """
        # Path to the desktop launcher JAR
        # Use raw string with backslash after drive letter to ensure correct path format
        jar_path = r"D:\Development\engine\CamProV5\desktop\build\libs\CamProV5-desktop.jar"
        
        # Check if the JAR file exists
        if not os.path.exists(jar_path):
            print(f"[DEBUG] JAR file not found: {jar_path}")
            return False
        else:
            print(f"[DEBUG] JAR file found: {jar_path}")
        
        # Check if Java is available
        try:
            # Use the Java installation at D:\Java with raw string for correct path format
            java_path = r"D:\Java\bin\java"
            print(f"[DEBUG] Checking Java at: {java_path}")
            result = subprocess.run([java_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"[DEBUG] Java check result: {result.returncode}")
            if result.stderr:
                print(f"[DEBUG] Java stderr: {result.stderr.decode('utf-8')}")
            return True
        except Exception as e:
            print(f"[DEBUG] Java check exception: {e}")
            return False