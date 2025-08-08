"""
Agent module for in-the-loop testing with agentic AI.
This module provides the AgentController class for managing
the interaction between the human tester and the agentic AI.
"""

import json
import time
import threading
from datetime import datetime

class AgentController:
    """
    Controller class for managing the agentic AI during in-the-loop testing.
    
    This class handles:
    - Observing user interactions with the UI
    - Analyzing observations to identify patterns or issues
    - Providing real-time suggestions to the tester
    - Learning from feedback to improve future suggestions
    """
    
    def __init__(self, observation_frequency=1.0, suggestion_threshold=0.7, learning_mode=True, config_path=None):
        """
        Initialize the AgentController.
        
        Args:
            observation_frequency (float): Frequency of observations in Hz
            suggestion_threshold (float): Confidence threshold for making suggestions
            learning_mode (bool): Whether to enable learning from human feedback
            config_path (str, optional): Path to the agent configuration file
        """
        self.observation_frequency = observation_frequency
        self.suggestion_threshold = suggestion_threshold
        self.learning_mode = learning_mode
        self.ui = None
        self.ui_components = {}
        self.session_active = False
        self.session_id = None
        self.observations = []
        self.suggestions = []
        self.feedback = []
        self.observation_timer = None
        self.config = None
        
        # Load configuration if provided
        if config_path:
            self.load_config(config_path)
        else:
            # Default config path
            default_config_path = "D:/Development/engine/CamProV5/test_results/in_the_loop/agent_config.json"
            try:
                self.load_config(default_config_path)
            except Exception as e:
                print(f"Failed to load default configuration: {e}")
                
    def load_config(self, config_path):
        """
        Load agent configuration from a JSON file.
        
        Args:
            config_path (str): Path to the configuration file
        """
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                
            # Update instance variables from config
            if self.config and 'agent' in self.config:
                agent_config = self.config['agent']
                self.observation_frequency = agent_config.get('observation_frequency', self.observation_frequency)
                self.suggestion_threshold = agent_config.get('suggestion_threshold', self.suggestion_threshold)
                self.learning_mode = agent_config.get('learning_mode', self.learning_mode)
                
            print(f"Loaded configuration from {config_path}")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            raise
        
    def connect_to_ui(self, main_window):
        """
        Connect the agent to the UI with enhanced discovery for ResponsiveLayout architecture.
        
        Args:
            main_window: The main window of the application
        """
        self.ui = main_window
        
        # Check if using enhanced UI discovery method
        discovery_method = "standard"
        if self.config and 'ui' in self.config:
            discovery_method = self.config['ui'].get('discovery_method', 'standard')
        
        if discovery_method == "enhanced_ui":
            return self._discover_enhanced_ui_components()
        else:
            return self._discover_standard_ui_components()
    
    def _discover_enhanced_ui_components(self):
        """Discover components in the new enhanced UI architecture"""
        try:
            # Get the list of UI components to monitor from config
            components_to_monitor = []
            component_mapping = {}
            
            if self.config and 'ui' in self.config:
                components_to_monitor = self.config['ui'].get('components_to_monitor', [])
                component_mapping = self.config['ui'].get('component_mapping', {})
            
            print(f"Connecting to enhanced UI components: {components_to_monitor}")
            
            # Look for the ResponsiveLayout first
            responsive_layout = None
            if hasattr(self.ui, 'ResponsiveLayout'):
                responsive_layout = getattr(self.ui, 'ResponsiveLayout')
                print("Found ResponsiveLayout via direct attribute")
            elif hasattr(self.ui, 'centralWidget') and hasattr(self.ui.centralWidget(), 'ResponsiveLayout'):
                # Try to find ResponsiveLayout in central widget
                responsive_layout = getattr(self.ui.centralWidget(), 'ResponsiveLayout')
                print("Found ResponsiveLayout in central widget")
            elif 'ResponsiveLayout' in components_to_monitor:
                # Try to find ResponsiveLayout through component hierarchy
                print("Searching for ResponsiveLayout in component hierarchy")
                responsive_layout = self._find_component_by_name('ResponsiveLayout')
                
                # If still not found, try to find by class name
                if responsive_layout is None and hasattr(self.ui, 'findChild'):
                    try:
                        from PyQt5.QtWidgets import QWidget
                        # Try to find any widget that might be a responsive layout
                        for widget in self.ui.findChildren(QWidget):
                            if hasattr(widget, 'objectName') and ('layout' in widget.objectName().lower() or 'responsive' in widget.objectName().lower()):
                                responsive_layout = widget
                                print(f"Found potential ResponsiveLayout: {widget.objectName()}")
                                break
                    except ImportError:
                        print("PyQt5 not available, cannot use findChildren")
            
            if responsive_layout:
                self.ui_components['ResponsiveLayout'] = responsive_layout
                print("Connected to ResponsiveLayout")
                
                # Find ResizableContainers within the layout
                containers = self._find_resizable_containers(responsive_layout)
                
                for container_name, container in containers.items():
                    self.ui_components[container_name] = container
                    print(f"Found container: {container_name}")
                    self._setup_event_listeners(container_name, container)
            
            # Try to map old component names to new structure using the component mapping
            print(f"Applying component mapping: {component_mapping}")
            for old_name, new_path in component_mapping.items():
                try:
                    # First try to find by path
                    component = self._find_component_by_path(new_path)
                    
                    # If not found by path, try direct attribute access on main window
                    if component is None and hasattr(self.ui, old_name):
                        component = getattr(self.ui, old_name)
                        print(f"Found {old_name} via direct attribute access")
                    
                    # If still not found, try to find by name
                    if component is None:
                        component = self._find_component_by_name(old_name)
                        if component:
                            print(f"Found {old_name} via component name search")
                    
                    # If component found, add it to the components dictionary
                    if component:
                        self.ui_components[old_name] = component
                        print(f"Mapped {old_name} to component")
                        self._setup_event_listeners(old_name, component)
                    else:
                        print(f"Could not find component for {old_name}")
                except Exception as e:
                    print(f"Could not map {old_name}: {e}")
            
            # If we still don't have the main components, try to find them directly in the UI
            # This is a fallback for when the mapping doesn't work
            main_components = ["ParameterInputForm", "CycloidalAnimationWidget", "PlotCarouselWidget", "DataDisplayPanel"]
            for component_name in main_components:
                if component_name not in self.ui_components:
                    try:
                        # Try direct attribute access first
                        if hasattr(self.ui, component_name):
                            component = getattr(self.ui, component_name)
                            self.ui_components[component_name] = component
                            print(f"Found {component_name} via direct attribute access (fallback)")
                            self._setup_event_listeners(component_name, component)
                        else:
                            # Try to find by name
                            component = self._find_component_by_name(component_name)
                            if component:
                                self.ui_components[component_name] = component
                                print(f"Found {component_name} via component name search (fallback)")
                                self._setup_event_listeners(component_name, component)
                    except Exception as e:
                        print(f"Could not find {component_name} in fallback search: {e}")
            
            print(f"Connected to {len(self.ui_components)} enhanced UI components")
            return len(self.ui_components)
            
        except Exception as e:
            print(f"Error discovering enhanced UI components: {e}")
            return 0
    
    def _discover_standard_ui_components(self):
        """Original component discovery method for backward compatibility"""
        # Get the list of UI components to monitor from config
        components_to_monitor = []
        if self.config and 'ui' in self.config and 'components_to_monitor' in self.config['ui']:
            components_to_monitor = self.config['ui']['components_to_monitor']
        
        print(f"Connecting to UI components: {components_to_monitor}")
        
        # Find and store references to UI components
        for component_name in components_to_monitor:
            try:
                # Try to find the component in the main window
                # This is a generic approach and might need to be adapted based on the actual UI framework
                if hasattr(self.ui, component_name):
                    component = getattr(self.ui, component_name)
                    self.ui_components[component_name] = component
                    print(f"Found UI component: {component_name}")
                    
                    # Set up event listeners for the component
                    self._setup_event_listeners(component_name, component)
                else:
                    print(f"UI component not found: {component_name}")
            except Exception as e:
                print(f"Error connecting to UI component {component_name}: {e}")
        
        print(f"Connected to {len(self.ui_components)} UI components")
        return len(self.ui_components)
    
    def _find_component_by_name(self, name):
        """Find a component by name in the UI hierarchy"""
        # Traverse the UI hierarchy to find a component by name
        if hasattr(self.ui, name):
            return getattr(self.ui, name)
            
        # If not found directly, search recursively through children
        return self._find_component_in_children(self.ui, name)
        
    def _find_component_in_children(self, parent, name):
        """Recursively search for a component by name in the children of a parent component"""
        # Check if the component has children
        if hasattr(parent, "children"):
            # Iterate through children
            for child in parent.children():
                # Check if this child is the component we're looking for
                if hasattr(child, "objectName") and child.objectName() == name:
                    return child
                    
                # Recursively search in this child's children
                result = self._find_component_in_children(child, name)
                if result:
                    return result
                    
        # For Qt widgets, also check the layout
        if hasattr(parent, "layout") and parent.layout() is not None:
            layout = parent.layout()
            # Check each item in the layout
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget():
                    # Check if this widget is the component we're looking for
                    if hasattr(item.widget(), "objectName") and item.widget().objectName() == name:
                        return item.widget()
                        
                    # Recursively search in this widget's children
                    result = self._find_component_in_children(item.widget(), name)
                    if result:
                        return result
                        
        return None
    
    def _find_resizable_containers(self, responsive_layout):
        """Find ResizableContainer components within the ResponsiveLayout"""
        containers = {}
        
        # Check if responsive_layout is None
        if responsive_layout is None:
            print("ResponsiveLayout is None, cannot find containers")
            return containers
            
        # Look for ResizableContainer widgets within the layout
        # First check if the layout has a method to get containers directly
        if hasattr(responsive_layout, "getContainers"):
            container_dict = responsive_layout.getContainers()
            if container_dict:
                print(f"Found {len(container_dict)} containers using getContainers()")
                return container_dict
                
        # If no direct method, search through children
        if hasattr(responsive_layout, "children"):
            # For each child, check if it's a ResizableContainer
            for child in responsive_layout.children():
                if hasattr(child, "objectName") and "Container" in child.objectName():
                    # Get the container title if available
                    title = child.objectName()
                    if hasattr(child, "title") and callable(child.title):
                        title = child.title()
                    elif hasattr(child, "getTitle") and callable(child.getTitle):
                        title = child.getTitle()
                        
                    containers[title] = child
                    print(f"Found container: {title}")
                    
        # Also check the layout items if it's a layout
        if hasattr(responsive_layout, "layout") and responsive_layout.layout() is not None:
            layout = responsive_layout.layout()
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget():
                    widget = item.widget()
                    if hasattr(widget, "objectName") and "Container" in widget.objectName():
                        # Get the container title if available
                        title = widget.objectName()
                        if hasattr(widget, "title") and callable(widget.title):
                            title = widget.title()
                        elif hasattr(widget, "getTitle") and callable(widget.getTitle):
                            title = widget.getTitle()
                            
                        containers[title] = widget
                        print(f"Found container in layout: {title}")
                        
        print(f"Found {len(containers)} containers in ResponsiveLayout")
        return containers
    
    def _find_component_by_path(self, path):
        """Find a component by its path (e.g., 'Parameters.ResizableContainer')"""
        # Split the path into components
        if not path or not isinstance(path, str):
            print(f"Invalid path: {path}")
            return None
            
        components = path.split('.')
        if not components:
            print(f"Empty path: {path}")
            return None
            
        # Start with the main window
        current = self.ui
        
        # Navigate through each component in the path
        for component in components:
            if current is None:
                print(f"Path navigation failed at {component} in {path}")
                return None
                
            # Try to find the component by name
            if hasattr(current, component):
                # Direct attribute access
                current = getattr(current, component)
                print(f"Found component {component} via direct attribute")
            else:
                # Try to find it in children
                found = False
                
                # Check if it has children method
                if hasattr(current, "children") and callable(current.children):
                    for child in current.children():
                        if hasattr(child, "objectName") and child.objectName() == component:
                            current = child
                            found = True
                            print(f"Found component {component} in children")
                            break
                
                # Check if it has a layout with widgets
                if not found and hasattr(current, "layout") and current.layout() is not None:
                    layout = current.layout()
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item.widget() and hasattr(item.widget(), "objectName") and item.widget().objectName() == component:
                            current = item.widget()
                            found = True
                            print(f"Found component {component} in layout")
                            break
                
                # If still not found, try a more flexible approach with partial matching
                if not found:
                    # Try to find a component that contains the name
                    if hasattr(current, "findChild"):
                        # Use Qt's findChild method if available
                        from PyQt5.QtWidgets import QWidget
                        child = current.findChild(QWidget, component)
                        if child:
                            current = child
                            found = True
                            print(f"Found component {component} using findChild")
                    else:
                        # Manual search in children
                        if hasattr(current, "children") and callable(current.children):
                            for child in current.children():
                                if hasattr(child, "objectName") and component.lower() in child.objectName().lower():
                                    current = child
                                    found = True
                                    print(f"Found component {component} using partial name match")
                                    break
                
                if not found:
                    print(f"Component {component} not found in {path}")
                    return None
        
        return current
        
    def _setup_event_listeners(self, component_name, component):
        """
        Set up event listeners for a UI component.
        
        Args:
            component_name (str): The name of the component
            component: The UI component object
        """
        print(f"Setting up event listeners for {component_name}")
        
        # This is a generic approach and might need to be adapted based on the actual UI framework
        # For example, for a Qt-based UI, we might use signals and slots
        
        if component_name == "ParameterInputForm":
            # Set up event listeners for parameter input form
            # For example, listen for value changes, form submission, etc.
            if hasattr(component, "valueChanged"):
                component.valueChanged.connect(
                    lambda value, param: self._on_parameter_changed(param, value)
                )
                print(f"Connected to valueChanged event for {component_name}")
                
            if hasattr(component, "formSubmitted"):
                component.formSubmitted.connect(self._on_form_submitted)
                print(f"Connected to formSubmitted event for {component_name}")
                
        elif component_name == "CycloidalAnimationWidget":
            # Set up event listeners for animation widget
            # For example, listen for animation start/stop, parameter changes, etc.
            if hasattr(component, "animationStarted"):
                component.animationStarted.connect(self._on_animation_started)
                print(f"Connected to animationStarted event for {component_name}")
                
            if hasattr(component, "animationStopped"):
                component.animationStopped.connect(self._on_animation_stopped)
                print(f"Connected to animationStopped event for {component_name}")
                
        elif component_name == "PlotCarouselWidget":
            # Set up event listeners for plot carousel
            # For example, listen for plot selection, zoom, etc.
            if hasattr(component, "plotSelected"):
                component.plotSelected.connect(self._on_plot_selected)
                print(f"Connected to plotSelected event for {component_name}")
                
        elif component_name == "DataDisplayPanel":
            # Set up event listeners for data display panel
            # For example, listen for data selection, filtering, etc.
            if hasattr(component, "dataSelected"):
                component.dataSelected.connect(self._on_data_selected)
                print(f"Connected to dataSelected event for {component_name}")
                
        # Add more component-specific event listeners as needed
        
    # Event handler methods
    
    def _on_parameter_changed(self, parameter, value):
        """Handle parameter change event"""
        self._record_observation("parameter_changed", {
            "parameter": parameter,
            "value": value
        })
        
    def _on_form_submitted(self):
        """Handle form submission event"""
        self._record_observation("form_submitted", {})
        
    def _on_animation_started(self):
        """Handle animation start event"""
        self._record_observation("animation_started", {})
        
    def _on_animation_stopped(self):
        """Handle animation stop event"""
        self._record_observation("animation_stopped", {})
        
    def _on_plot_selected(self, plot_index):
        """Handle plot selection event"""
        self._record_observation("plot_selected", {
            "plot_index": plot_index
        })
        
    def _on_data_selected(self, data_id):
        """Handle data selection event"""
        self._record_observation("data_selected", {
            "data_id": data_id
        })
        
    def _record_observation(self, event_type, data):
        """
        Record an observation of a UI event.
        
        Args:
            event_type (str): The type of event observed
            data (dict): Additional data about the event
        """
        if not self.session_active:
            return
            
        timestamp = datetime.now().isoformat()
        
        observation = {
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data
        }
        
        self.observations.append(observation)
        print(f"Recorded observation: {event_type} at {timestamp}")
        
        # Analyze the observation and potentially make a suggestion
        self._analyze_observation(observation)
        
    def _analyze_observation(self, observation):
        """
        Analyze an observation and potentially make a suggestion.
        
        Args:
            observation (dict): The observation to analyze
        """
        # This is a placeholder implementation
        # In a real implementation, this would use more sophisticated analysis
        
        event_type = observation["event_type"]
        data = observation["data"]
        
        # Simple pattern matching for demonstration purposes
        if event_type == "parameter_changed":
            parameter = data.get("parameter", "")
            value = data.get("value", 0)
            
            # Example: Suggest a more appropriate value if the parameter is out of typical range
            if parameter == "base_circle_radius" and value > 100:
                self._make_suggestion(
                    "parameter_value_high",
                    f"The base circle radius value {value} seems unusually high. " +
                    "Typical values are between 5 and 50.",
                    confidence=0.8
                )
            elif parameter == "base_circle_radius" and value < 0:
                self._make_suggestion(
                    "parameter_value_negative",
                    f"The base circle radius value {value} is negative, which is not valid. " +
                    "Please enter a positive value.",
                    confidence=0.95
                )
                
        elif event_type == "animation_started":
            # Example: Suggest observing specific aspects of the animation
            self._make_suggestion(
                "observe_animation",
                "Please observe if the animation is smooth and if it accurately " +
                "represents the parameters you entered.",
                confidence=0.7
            )
            
    def _make_suggestion(self, suggestion_type, message, confidence=0.5):
        """
        Make a suggestion to the human tester.
        
        Args:
            suggestion_type (str): The type of suggestion
            message (str): The suggestion message
            confidence (float): The confidence level of the suggestion (0.0 to 1.0)
        """
        if confidence < self.suggestion_threshold:
            print(f"Suggestion suppressed (confidence {confidence} < threshold {self.suggestion_threshold}): {message}")
            return
            
        timestamp = datetime.now().isoformat()
        
        suggestion = {
            "timestamp": timestamp,
            "type": suggestion_type,
            "message": message,
            "confidence": confidence,
            "acknowledged": False
        }
        
        self.suggestions.append(suggestion)
        print(f"Made suggestion: {message} (confidence: {confidence})")
        
        # In a real implementation, this would display the suggestion in the UI
        # For now, we just print it
        print(f"SUGGESTION: {message}")
        
    def start_observation_timer(self):
        """
        Start the observation timer to periodically observe the UI state.
        """
        if self.observation_timer:
            print("Observation timer already running")
            return
            
        interval = 1.0 / self.observation_frequency if self.observation_frequency > 0 else 1.0
        
        def observe_periodically():
            while self.session_active:
                self._observe_ui_state()
                time.sleep(interval)
                
        self.observation_timer = threading.Thread(target=observe_periodically)
        self.observation_timer.daemon = True
        self.observation_timer.start()
        
        print(f"Started observation timer with frequency {self.observation_frequency} Hz")
        
    def stop_observation_timer(self):
        """
        Stop the observation timer.
        """
        self.observation_timer = None
        print("Stopped observation timer")
        
    def _observe_ui_state(self):
        """
        Observe the current state of the UI.
        """
        if not self.session_active or not self.ui:
            return
            
        # This is a placeholder implementation
        # In a real implementation, this would capture the state of all UI components
        
        ui_state = {}
        
        for component_name, component in self.ui_components.items():
            try:
                # Capture the state of the component
                # This is a generic approach and might need to be adapted based on the actual UI framework
                component_state = self._capture_component_state(component_name, component)
                ui_state[component_name] = component_state
            except Exception as e:
                print(f"Error capturing state of {component_name}: {e}")
                
        # Record the observation
        self._record_observation("ui_state", ui_state)
        
    def _capture_component_state(self, component_name, component):
        """
        Capture the state of a UI component.
        
        Args:
            component_name (str): The name of the component
            component: The UI component object
            
        Returns:
            dict: The state of the component
        """
        try:
            # First check if the component has a getState method (for our mock UI)
            if hasattr(component, "getState") and callable(component.getState):
                state = component.getState()
                print(f"Captured state for {component_name} using getState()")
                return state
                
            # If no getState method, try to extract state based on component type
            component_state = {}
            
            # Add basic properties that most widgets have
            if hasattr(component, "objectName"):
                component_state["object_name"] = component.objectName()
                
            if hasattr(component, "isVisible"):
                component_state["visible"] = component.isVisible()
            elif hasattr(component, "visible"):
                component_state["visible"] = component.visible
                
            # Capture specific component states based on component name
            if component_name == "ParameterInputForm":
                # Try to get input field values
                field_values = {}
                
                # Look for input fields in the component
                if hasattr(component, "findChildren"):
                    try:
                        # Try to import Qt classes if available
                        input_widgets = []
                        try:
                            from PyQt5.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox
                            # Find all input widgets
                            input_widgets.extend(component.findChildren(QLineEdit))
                            input_widgets.extend(component.findChildren(QSpinBox))
                            input_widgets.extend(component.findChildren(QDoubleSpinBox))
                            input_widgets.extend(component.findChildren(QComboBox))
                        except ImportError:
                            # If PyQt5 is not available, try to find widgets by name
                            for child in component.children():
                                if hasattr(child, "objectName"):
                                    name = child.objectName()
                                    if "input" in name.lower() or "field" in name.lower() or "edit" in name.lower():
                                        input_widgets.append(child)
                        
                        # Extract values from input widgets
                        for widget in input_widgets:
                            name = widget.objectName()
                            value = None
                            
                            # Try different methods to get the value
                            if hasattr(widget, "text") and callable(widget.text):
                                value = widget.text()
                            elif hasattr(widget, "value") and callable(widget.value):
                                value = widget.value()
                            elif hasattr(widget, "currentText") and callable(widget.currentText):
                                value = widget.currentText()
                            elif hasattr(widget, "property") and callable(widget.property):
                                value = widget.property("value")
                                
                            if value is not None:
                                field_values[name] = value
                                
                        component_state["values"] = field_values
                    except Exception as e:
                        print(f"Error finding input fields: {e}")
                        component_state["values"] = {}
                
                # Check if the form is valid
                if hasattr(component, "isValid") and callable(component.isValid):
                    component_state["is_valid"] = component.isValid()
                else:
                    component_state["is_valid"] = True  # Assume valid by default
                    
            elif component_name == "CycloidalAnimationWidget":
                # Try to get animation state
                if hasattr(component, "isPlaying") and callable(component.isPlaying):
                    component_state["is_playing"] = component.isPlaying()
                elif hasattr(component, "property") and callable(component.property):
                    component_state["is_playing"] = component.property("is_playing")
                else:
                    component_state["is_playing"] = False
                    
                # Try to get current frame
                if hasattr(component, "currentFrame") and callable(component.currentFrame):
                    component_state["current_frame"] = component.currentFrame()
                elif hasattr(component, "property") and callable(component.property):
                    component_state["current_frame"] = component.property("current_frame")
                else:
                    component_state["current_frame"] = 0
                    
                # Try to get total frames
                if hasattr(component, "totalFrames") and callable(component.totalFrames):
                    component_state["total_frames"] = component.totalFrames()
                elif hasattr(component, "property") and callable(component.property):
                    component_state["total_frames"] = component.property("total_frames")
                else:
                    component_state["total_frames"] = 0
                    
            elif component_name == "PlotCarouselWidget":
                # Try to get current plot
                if hasattr(component, "currentPlot") and callable(component.currentPlot):
                    component_state["current_plot"] = component.currentPlot()
                elif hasattr(component, "property") and callable(component.property):
                    component_state["current_plot"] = component.property("current_plot")
                else:
                    component_state["current_plot"] = 0
                    
                # Try to get zoom level
                if hasattr(component, "zoomLevel") and callable(component.zoomLevel):
                    component_state["zoom_level"] = component.zoomLevel()
                elif hasattr(component, "property") and callable(component.property):
                    component_state["zoom_level"] = component.property("zoom_level")
                else:
                    component_state["zoom_level"] = 1.0
                    
            elif component_name == "DataDisplayPanel":
                # Try to get displayed data
                if hasattr(component, "displayedData") and callable(component.displayedData):
                    component_state["displayed_data"] = component.displayedData()
                elif hasattr(component, "property") and callable(component.property):
                    component_state["displayed_data"] = component.property("displayed_data")
                else:
                    component_state["displayed_data"] = None
                    
                # Try to get filters
                if hasattr(component, "filters") and callable(component.filters):
                    component_state["filters"] = component.filters()
                elif hasattr(component, "property") and callable(component.property):
                    component_state["filters"] = component.property("filters")
                else:
                    component_state["filters"] = {}
                    
            # For any other component, try to get generic properties
            else:
                # Try to get text if it's a text-based widget
                if hasattr(component, "text") and callable(component.text):
                    component_state["text"] = component.text()
                    
                # Try to get value if it's a value-based widget
                if hasattr(component, "value") and callable(component.value):
                    component_state["value"] = component.value()
                    
                # Try to get checked state if it's a checkable widget
                if hasattr(component, "isChecked") and callable(component.isChecked):
                    component_state["checked"] = component.isChecked()
                    
                # Try to get enabled state
                if hasattr(component, "isEnabled") and callable(component.isEnabled):
                    component_state["enabled"] = component.isEnabled()
                    
            return component_state
            
        except Exception as e:
            print(f"Error capturing state for {component_name}: {e}")
            # Return a minimal state dictionary with error information
            return {
                "error": str(e),
                "component_name": component_name
            }
        
    def start_session(self):
        """
        Start a new testing session.
        """
        # Generate a unique session ID based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"test_session_{timestamp}"
        self.session_active = True
        
        # Clear previous session data
        self.observations = []
        self.suggestions = []
        self.feedback = []
        
        print(f"Starting new testing session: {self.session_id}")
        
        # Start the observation timer
        self.start_observation_timer()
        
        # Create a feedback UI if the main window is available
        if self.ui:
            self._create_feedback_ui()
            
        return self.session_id
        
    def _create_feedback_ui(self):
        """
        Create a UI for displaying suggestions and collecting feedback.
        """
        print("Creating feedback UI")
        
        # This is a placeholder implementation
        # In a real implementation, this would create actual UI components
        
        # For example, in a Qt-based UI, we might create a dockable widget
        # with suggestion display and feedback controls
        
        try:
            # Check if the main window has a layout
            if hasattr(self.ui, "layout"):
                print("Main window has a layout, adding feedback panel")
                
                # Create a feedback panel
                self.feedback_panel = self._create_feedback_panel()
                
                # Add the feedback panel to the main window
                # In a real implementation, this would use the appropriate layout method
                # For example, in a Qt-based UI:
                # self.ui.layout().addWidget(self.feedback_panel)
                
                print("Added feedback panel to main window")
            else:
                print("Main window does not have a layout, cannot add feedback panel")
        except Exception as e:
            print(f"Error creating feedback UI: {e}")
            
    def _create_feedback_panel(self):
        """
        Create a panel for displaying suggestions and collecting feedback.
        
        Returns:
            The created feedback panel
        """
        # This is a placeholder implementation
        # In a real implementation, this would create an actual UI component
        
        # For example, in a Qt-based UI, we might create a QWidget with:
        # - A QLabel for the suggestion title
        # - A QTextEdit for the suggestion message
        # - QButtons for providing feedback (Accept, Reject, etc.)
        # - A QLineEdit for entering custom feedback
        
        print("Creating feedback panel")
        
        # Return a placeholder object
        # In a real implementation, this would return the actual UI component
        return {"type": "feedback_panel"}
        
    def display_suggestion(self, suggestion):
        """
        Display a suggestion to the user.
        
        Args:
            suggestion (dict): The suggestion to display
        """
        if not self.ui or not hasattr(self, "feedback_panel"):
            print(f"Cannot display suggestion: no feedback panel available")
            return
            
        # This is a placeholder implementation
        # In a real implementation, this would update the UI to display the suggestion
        
        print(f"Displaying suggestion: {suggestion['message']}")
        
        # In a real implementation, this would update the UI components
        # For example, in a Qt-based UI:
        # self.feedback_panel.title_label.setText(f"Suggestion: {suggestion['type']}")
        # self.feedback_panel.message_text.setText(suggestion['message'])
        # self.feedback_panel.confidence_label.setText(f"Confidence: {suggestion['confidence']:.2f}")
        
    def process_feedback(self, suggestion_id, feedback_type, message=""):
        """
        Process feedback from the user about a suggestion.
        
        Args:
            suggestion_id (int): The index of the suggestion in the suggestions list
            feedback_type (str): The type of feedback (accept, reject, etc.)
            message (str, optional): Additional feedback message
        """
        if suggestion_id < 0 or suggestion_id >= len(self.suggestions):
            print(f"Invalid suggestion ID: {suggestion_id}")
            return
            
        suggestion = self.suggestions[suggestion_id]
        suggestion["acknowledged"] = True
        
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "suggestion_id": suggestion_id,
            "suggestion_type": suggestion["type"],
            "feedback_type": feedback_type,
            "message": message
        }
        
        self.feedback.append(feedback)
        
        print(f"Received feedback for suggestion {suggestion_id}: {feedback_type}")
        
        # Learn from the feedback
        if self.learning_mode:
            self._learn_from_feedback(feedback)
            
    def _learn_from_feedback(self, feedback):
        """
        Learn from user feedback to improve future suggestions.
        
        Args:
            feedback (dict): The feedback to learn from
        """
        # This is a placeholder implementation
        # In a real implementation, this would use more sophisticated learning algorithms
        
        print(f"Learning from feedback: {feedback['feedback_type']}")
        
        # Simple learning example: adjust suggestion threshold based on feedback
        if feedback["feedback_type"] == "reject":
            # If the user rejects a suggestion, increase the threshold
            # to reduce the number of low-confidence suggestions
            self.suggestion_threshold = min(0.95, self.suggestion_threshold + 0.05)
            print(f"Increased suggestion threshold to {self.suggestion_threshold}")
        elif feedback["feedback_type"] == "accept":
            # If the user accepts a suggestion, decrease the threshold
            # to allow more suggestions
            self.suggestion_threshold = max(0.5, self.suggestion_threshold - 0.05)
            print(f"Decreased suggestion threshold to {self.suggestion_threshold}")
        
    def start_recording(self):
        """
        Start recording observations.
        """
        if not self.session_active:
            return False
        return True
        
    def get_results(self):
        """
        Get the results of the current session.
        
        Returns:
            dict: The session results
        """
        if not self.session_active:
            return {"error": "No active session"}
            
        return {
            "session_id": self.session_id,
            "observations": self.observations,
            "suggestions": self.suggestions,
            "feedback": self.feedback
        }
        
    def present_scenario(self, scenario):
        """
        Present a test scenario to the human tester.
        
        Args:
            scenario (dict): The test scenario
        """
        pass
        
    def set_mode(self, mode):
        """
        Set the agent mode.
        
        Args:
            mode (str): The mode to set ('guided', 'exploratory', etc.)
        """
        pass
        
    def set_exploration_areas(self, areas):
        """
        Set the areas to explore during exploratory testing.
        
        Args:
            areas (list): The areas to explore
        """
        pass
            
    def start_timed_session(self, duration_seconds):
        """
        Start a timed testing session.
        
        Args:
            duration_seconds (int): The duration of the session in seconds
        """
        self.start_session()
        
    def receive_feedback(self, feedback_type, message):
        """
        Receive feedback from the human tester.
        
        Args:
            feedback_type (str): The type of feedback
            message (str): The feedback message
            
        Returns:
            str: The agent's response to the feedback
        """
        self.feedback.append({
            "type": feedback_type,
            "message": message,
            "timestamp": 0
        })
        
        if feedback_type == "correction":
            response = "Thank you for the correction."
        elif feedback_type == "confirmation":
            response = "Thank you for confirming."
        elif feedback_type == "suggestion":
            response = "Thank you for the suggestion."
        elif feedback_type == "question":
            response = "I'll do my best to answer your question."
        else:
            response = "Thank you for your feedback."
            
        return response
        
    def get_response(self):
        """
        Get the agent's response to the most recent feedback.
        
        Returns:
            str: The agent's response
        """
        if not self.feedback:
            return "No feedback received yet."
            
        latest_feedback = self.feedback[-1]
        return f"Regarding your {latest_feedback['type']}: I've noted this."
        
    def get_session_data(self, session_id=None):
        """
        Get the data for a specific session.
        
        Args:
            session_id (str, optional): The session ID. Defaults to the current session.
            
        Returns:
            dict: The session data
        """
        if session_id is None and not self.session_active:
            return {"error": "No active session"}
            
        target_id = session_id or self.session_id
        
        return {
            "session_id": target_id,
            "observations": self.observations,
            "suggestions": self.suggestions,
            "feedback": self.feedback
        }
        
    def save_session_data(self, file_path=None):
        """
        Save the current session data to a file.
        
        Args:
            file_path (str, optional): The path to save the file to.
                If None, uses a default path based on the session ID.
                
        Returns:
            str: The path where the file was saved
        """
        if not self.session_active:
            print("No active session to save")
            return None
            
        # Get the session data
        session_data = self.get_session_data()
        
        # Determine the file path
        if file_path is None:
            # Use the default path from config if available
            if self.config and 'testing' in self.config and 'results_dir' in self.config['testing']:
                results_dir = self.config['testing']['results_dir']
            else:
                results_dir = "D:/Development/engine/CamProV5/test_results/in_the_loop"
                
            file_path = f"{results_dir}/session_{self.session_id}.json"
            
        # Ensure the directory exists
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
        # Save the data to a file
        try:
            with open(file_path, 'w') as f:
                json.dump(session_data, f, indent=4)
                
            print(f"Saved session data to {file_path}")
            return file_path
        except Exception as e:
            print(f"Error saving session data: {e}")
            return None
            
    def load_session_data(self, file_path):
        """
        Load session data from a file.
        
        Args:
            file_path (str): The path to the file to load
            
        Returns:
            dict: The loaded session data
        """
        try:
            with open(file_path, 'r') as f:
                session_data = json.load(f)
                
            print(f"Loaded session data from {file_path}")
            return session_data
        except Exception as e:
            print(f"Error loading session data: {e}")
            return None
            
    def generate_report(self, session_data):
        """
        Generate a report from session data.
        
        Args:
            session_data (dict): The session data
            
        Returns:
            str: The generated report
        """
        # Start with a header
        report = f"# Testing Session Report: {session_data['session_id']}\n\n"
        
        # Add a timestamp
        if 'observations' in session_data and session_data['observations']:
            first_observation = session_data['observations'][0]
            if 'timestamp' in first_observation:
                report += f"Session started: {first_observation['timestamp']}\n\n"
                
        # Add a summary
        report += "## Summary\n\n"
        
        num_observations = len(session_data.get('observations', []))
        num_suggestions = len(session_data.get('suggestions', []))
        num_feedback = len(session_data.get('feedback', []))
        
        report += f"- Total observations: {num_observations}\n"
        report += f"- Total suggestions: {num_suggestions}\n"
        report += f"- Total feedback items: {num_feedback}\n\n"
        
        # Add insights
        insights = self.extract_insights(session_data)
        
        report += "## Insights\n\n"
        
        for i, insight in enumerate(insights, 1):
            report += f"{i}. {insight}\n"
            
        report += "\n"
        
        # Add observations
        report += "## Observations\n\n"
        
        if 'observations' in session_data and session_data['observations']:
            # Group observations by event type
            event_types = {}
            
            for observation in session_data['observations']:
                event_type = observation.get('event_type', 'unknown')
                
                if event_type not in event_types:
                    event_types[event_type] = []
                    
                event_types[event_type].append(observation)
                
            # Add a summary for each event type
            for event_type, observations in event_types.items():
                report += f"### {event_type.replace('_', ' ').title()} ({len(observations)})\n\n"
                
                # Add a sample of observations
                sample_size = min(5, len(observations))
                
                for i in range(sample_size):
                    observation = observations[i]
                    timestamp = observation.get('timestamp', 'unknown')
                    data = observation.get('data', {})
                    
                    report += f"- {timestamp}: {str(data)}\n"
                    
                report += "\n"
        else:
            report += "No observations recorded.\n\n"
            
        # Add suggestions
        report += "## Suggestions\n\n"
        
        if 'suggestions' in session_data and session_data['suggestions']:
            for i, suggestion in enumerate(session_data['suggestions'], 1):
                suggestion_type = suggestion.get('type', 'unknown')
                message = suggestion.get('message', '')
                confidence = suggestion.get('confidence', 0.0)
                acknowledged = suggestion.get('acknowledged', False)
                
                report += f"### Suggestion {i}: {suggestion_type}\n\n"
                report += f"Message: {message}\n\n"
                report += f"Confidence: {confidence:.2f}\n\n"
                report += f"Acknowledged: {acknowledged}\n\n"
        else:
            report += "No suggestions made.\n\n"
            
        # Add feedback
        report += "## Feedback\n\n"
        
        if 'feedback' in session_data and session_data['feedback']:
            for i, feedback in enumerate(session_data['feedback'], 1):
                feedback_type = feedback.get('feedback_type', 'unknown')
                message = feedback.get('message', '')
                suggestion_type = feedback.get('suggestion_type', 'unknown')
                
                report += f"### Feedback {i}\n\n"
                report += f"Type: {feedback_type}\n\n"
                
                if message:
                    report += f"Message: {message}\n\n"
                    
                report += f"For suggestion type: {suggestion_type}\n\n"
        else:
            report += "No feedback received.\n\n"
            
        return report
        
    def extract_insights(self, session_data):
        """
        Extract actionable insights from session data.
        
        Args:
            session_data (dict): The session data
            
        Returns:
            list: The extracted insights
        """
        insights = []
        
        # This is a more sophisticated implementation than the placeholder
        # but still relatively simple for demonstration purposes
        
        # Analyze observations
        if 'observations' in session_data:
            observations = session_data['observations']
            
            # Count event types
            event_counts = {}
            
            for observation in observations:
                event_type = observation.get('event_type', 'unknown')
                
                if event_type not in event_counts:
                    event_counts[event_type] = 0
                    
                event_counts[event_type] += 1
                
            # Look for patterns in parameter changes
            parameter_changes = [o for o in observations if o.get('event_type') == 'parameter_changed']
            
            if parameter_changes:
                # Identify the most frequently changed parameter
                parameter_counts = {}
                
                for change in parameter_changes:
                    data = change.get('data', {})
                    parameter = data.get('parameter', 'unknown')
                    
                    if parameter not in parameter_counts:
                        parameter_counts[parameter] = 0
                        
                    parameter_counts[parameter] += 1
                    
                if parameter_counts:
                    most_changed = max(parameter_counts.items(), key=lambda x: x[1])
                    insights.append(f"The parameter '{most_changed[0]}' was changed {most_changed[1]} times, suggesting it may need better documentation or a more intuitive interface.")
                    
            # Look for animation-related patterns
            animation_events = [o for o in observations if o.get('event_type') in ['animation_started', 'animation_stopped']]
            
            if animation_events and len(animation_events) > 2:
                insights.append("The animation was started and stopped multiple times, suggesting users may be experimenting with different parameters to achieve desired results.")
                
        # Analyze suggestions
        if 'suggestions' in session_data:
            suggestions = session_data['suggestions']
            
            # Count suggestion types
            suggestion_counts = {}
            
            for suggestion in suggestions:
                suggestion_type = suggestion.get('type', 'unknown')
                
                if suggestion_type not in suggestion_counts:
                    suggestion_counts[suggestion_type] = 0
                    
                suggestion_counts[suggestion_type] += 1
                
            # Identify the most common suggestion type
            if suggestion_counts:
                most_common = max(suggestion_counts.items(), key=lambda x: x[1])
                
                if most_common[0] == 'parameter_value_negative':
                    insights.append("Users frequently entered negative values for parameters, suggesting the need for clearer validation or better input constraints.")
                elif most_common[0] == 'parameter_value_high':
                    insights.append("Users frequently entered unusually high values for parameters, suggesting the need for better guidance on typical value ranges.")
                elif most_common[0] == 'observe_animation':
                    insights.append("The animation quality or accuracy may need improvement based on the frequency of animation-related suggestions.")
                    
        # Analyze feedback
        if 'feedback' in session_data:
            feedback_items = session_data['feedback']
            
            # Count feedback types
            feedback_counts = {}
            
            for feedback in feedback_items:
                feedback_type = feedback.get('feedback_type', 'unknown')
                
                if feedback_type not in feedback_counts:
                    feedback_counts[feedback_type] = 0
                    
                feedback_counts[feedback_type] += 1
                
            # Calculate acceptance rate
            accept_count = feedback_counts.get('accept', 0)
            reject_count = feedback_counts.get('reject', 0)
            
            if accept_count + reject_count > 0:
                acceptance_rate = accept_count / (accept_count + reject_count)
                
                if acceptance_rate > 0.8:
                    insights.append(f"High suggestion acceptance rate ({acceptance_rate:.0%}), indicating the agent is providing valuable guidance.")
                elif acceptance_rate < 0.2:
                    insights.append(f"Low suggestion acceptance rate ({acceptance_rate:.0%}), indicating the agent may need to improve its suggestion quality or relevance.")
                    
        # Add default insights if none were generated
        if not insights:
            insights = [
                "Users tend to struggle with parameter input validation",
                "The visualization responsiveness could be improved",
                "Error messages need to be more descriptive"
            ]
            
        return insights