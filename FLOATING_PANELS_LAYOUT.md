# Floating Panels Layout

## Overview

The Floating Panels Layout is a new UI layout for CamProV5 that allows panels to be freely positioned, resized, and stacked. This layout provides a more flexible user experience compared to the previous fixed layout.

## Features

- **Freely Draggable Panels**: Panels can be positioned anywhere within the application window
- **Resizable from All Directions**: Panels can be resized from any edge or corner
- **Stackable Panels**: Panels can overlap and be stacked on top of each other
- **Automatic Z-Index Management**: Moving panels are automatically brought to front
- **Manual Z-Index Controls**: Up/down buttons to manually control panel stacking order
- **State Persistence**: Panel positions and sizes are preserved during the session

## Implementation Details

### Components

1. **DraggableResizablePanel**: A composable that combines dragging and resizing capabilities
   - Supports position (x, y) and size (width, height) state
   - Provides z-index support for stacking
   - Includes visual feedback for active/dragging states
   - Implements resize handles in all directions

2. **FloatingPanelsLayout**: A composable that uses DraggableResizablePanel for each panel
   - Replaces the previous Row-based layout with a Box layout
   - Manages panel states (position, size, z-index)
   - Ensures panels can be brought to front when moved

3. **FloatingPanelState**: A data class that represents the state of a floating panel
   - Stores position (x, y), size (width, height), and z-index
   - Used for state persistence

### State Management

Panel states are managed using a `mutableStateMapOf` that maps panel IDs to `FloatingPanelState` objects. When a panel is moved or resized, its state is updated in this map. The states are initialized with default values when the application starts.

## Usage Instructions

### Moving Panels

1. Hover over the panel's title bar
2. Click and drag to move the panel
3. Release to place the panel at the new position
4. The panel will automatically be brought to front when moved

### Resizing Panels

1. Hover over any edge or corner of the panel to see the resize handle
2. Click and drag the handle to resize the panel
3. Release to set the new size

### Stacking Panels

Panels can be stacked on top of each other in several ways:

1. **Automatic**: Moving a panel automatically brings it to the front
2. **Manual**: Use the up/down arrow buttons in the panel's title bar
   - Up arrow: Bring panel to front
   - Down arrow: Send panel to back

## Customization

The initial positions and sizes of panels can be customized by modifying the default panel states in the `FloatingPanelsLayout` composable:

```kotlin
val defaultPanelStates = mapOf(
    "parameters" to FloatingPanelState(
        id = "parameters",
        x = 20.dp,
        y = 60.dp,
        width = 400.dp,
        height = 300.dp,
        zIndex = 0f
    ),
    // Other panel states...
)
```

## Responsive Behavior

The Floating Panels Layout is used for larger screens, while smaller screens continue to use the SingleColumnSimpleLayout. This ensures a good user experience across different device sizes.

## Future Enhancements

Potential future enhancements for the Floating Panels Layout:

1. **Persistent Storage**: Save panel states to disk for persistence between application restarts
2. **Snap-to-Grid**: Add option for panels to snap to a grid for easier alignment
3. **Panel Minimization**: Allow panels to be minimized to a taskbar
4. **Layout Presets**: Provide predefined layout configurations that users can select
5. **Panel Grouping**: Allow panels to be grouped together and moved/resized as a unit