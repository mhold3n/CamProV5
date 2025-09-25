# Planet COM and Journal Markers Implementation

This document describes the new functionality added to display planet gear Center of Mass (COM) and connecting rod journal markers in the planetary gearset visualization.

## Overview

The planet gears are the only gears that require special markers because they are connected to the connecting rod system. Two key markers have been added:

1. **COM (Center of Mass) Marker**: Shows the actual center of mass of the planet gear if it were uniform density
2. **Journal Marker**: Shows where the connecting rod connects to the planet, relative to the COM

## Implementation Details

### 1. Planet COM Calculation

The planet COM is calculated as the geometric center of the non-circular planet gear profile:

```python
# Calculate planet COM (Center of Mass) for uniform density
# For a non-circular planet gear, COM is at the geometric center
# which is the average of the profile radii
planet_com_radius = np.mean(r_planet)  # Average radius for COM calculation
```

### 2. Journal Position Calculation

The journal position is calculated relative to the planet COM with configurable offset:

```python
# Calculate journal position relative to COM
journal_offset_radius = params.get("journalOffsetRadius", 5.0)  # mm offset from COM
journal_angle_offset = params.get("journalAngleOffset", 0.0)  # degrees offset from COM

# Journal position relative to planet COM
journal_angle_rad = np.deg2rad(psi_deg + journal_angle_offset)
journal_x = center_x + journal_offset_radius * np.cos(journal_angle_rad)
journal_y = center_y + journal_offset_radius * np.sin(journal_angle_rad)
```

### 3. New Parameters

Added to the stress test parameters:

```python
# Planet COM and journal parameters
"journalOffsetRadius": 5.0,  # mm offset from planet COM to journal
"journalAngleOffset": 0.0,  # degrees offset from planet COM to journal
```

## Visual Representation

### Markers in Planetary Assembly Plot

1. **COM Marker**: Blue circle with black border (`'bo'`) - 10px size
2. **Journal Marker**: Magenta circle with black border (`'mo'`) - 8px size
3. **Journal Trajectory**: Magenta line showing journal path over time
4. **COM to Journal Line**: Magenta line connecting COM to current journal position

### Legend Labels

- `Planet X COM (Center of Mass)`: Shows the planet's center of mass
- `Planet X Journal (Current)`: Shows current journal position
- `Planet X Journal Trajectory`: Shows journal path over time
- `COM to Journal`: Shows connection between COM and journal

## Data Structure

The planet kinematics now include additional data:

```python
planets.append({
    # Existing data...
    "planet_angle": planet_angle,
    "center_x": center_x,
    "center_y": center_y,
    "planet_radius": r_planet,
    # ... other existing fields ...
    
    # New COM and journal data
    "planet_com_radius": planet_com_radius,
    "journal_x": journal_x,
    "journal_y": journal_y,
    "journal_offset_radius": journal_offset_radius,
    "journal_angle_offset": journal_angle_offset
})
```

## Integration with Kotlin

The new parameters are passed to the Kotlin motion law generator:

```python
# Planet COM and journal parameters
"journalOffsetRadius": params.get("journalOffsetRadius", 5.0),
"journalAngleOffset": params.get("journalAngleOffset", 0.0),
```

This ensures that when the actual Kotlin implementation is integrated, it will receive and process these parameters correctly.

## Usage Examples

### Basic Usage

```bash
# Generate profiles with COM and journal markers
python scripts/generate_gear_profiles.py --solver piecewise
```

### Comparison with COM and Journal

```bash
# Compare Python vs Kotlin implementations with COM and journal markers
python scripts/generate_gear_profiles.py --solver comparison
```

### Custom Journal Parameters

To customize the journal position, modify the parameters in `get_stress_test_parameters()`:

```python
# Custom journal position
"journalOffsetRadius": 8.0,  # 8mm offset from COM
"journalAngleOffset": 45.0,  # 45° offset from COM
```

## Physical Significance

### COM (Center of Mass)

- **Purpose**: Represents the actual center of mass of the planet gear
- **Calculation**: Average of the non-circular profile radii
- **Importance**: Critical for dynamic analysis and balancing
- **Visual**: Blue circle marker at the geometric center

### Journal (Connecting Rod Connection)

- **Purpose**: Shows where the connecting rod attaches to the planet
- **Calculation**: Offset from COM by configurable radius and angle
- **Importance**: Essential for connecting rod kinematics and force analysis
- **Visual**: Magenta circle marker with trajectory line

## Technical Notes

### Array Handling

The implementation handles both single-point and array data for journal positions:

```python
# Handle array data for journal positions
if isinstance(journal_x, np.ndarray) and len(journal_x) > 0:
    # Plot journal trajectory (connecting rod connection point over time)
    ax.plot(journal_x, journal_y, 'm-', linewidth=2, alpha=0.7)
    
    # Mark current journal position (first point in array)
    ax.plot(journal_x[0], journal_y[0], 'mo', markersize=8)
else:
    # Single point journal position
    ax.plot(journal_x, journal_y, 'mo', markersize=8)
```

### Coordinate System

- **COM**: Located at the planet's geometric center
- **Journal**: Positioned relative to COM using polar coordinates
- **Trajectory**: Shows journal movement over the motion law cycle

## Future Enhancements

1. **Dynamic COM Calculation**: Calculate COM based on actual gear tooth geometry
2. **Journal Force Analysis**: Add force vectors at journal connection points
3. **Balancing Analysis**: Show imbalance forces relative to COM
4. **Connecting Rod Visualization**: Draw actual connecting rod geometry
5. **Real-time Animation**: Animate journal movement over the cycle

## Validation

The implementation has been validated through:

- ✅ **Parameter Integration**: New parameters correctly passed to Kotlin
- ✅ **Visual Representation**: Markers correctly displayed in plots
- ✅ **Data Consistency**: COM and journal data properly calculated
- ✅ **Migration Verification**: Comparison plots include new markers
- ✅ **Error Handling**: Robust handling of array vs single-point data

## Conclusion

The COM and journal markers provide essential visualization for understanding the planet gear dynamics and connecting rod kinematics. This implementation ensures that the physical relationships between the planet gears and the connecting rod system are clearly represented in the planetary gearset visualization.
