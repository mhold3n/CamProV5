# RPM Sweep Analysis - Future Enhancement

## Overview

This document outlines the planned enhancement to implement RPM sweep analysis for comprehensive FEA testing across multiple operating speeds and resonant frequencies.

## Current State

Currently, the optimization pipeline uses a single RPM value (typically 3000 RPM) for:
- Motion law optimization (velocity/acceleration scaling)
- FEA analysis (stress, vibration, fatigue)
- Force transfer analysis (friction and windage losses)
- Gear design calculations (dynamic factors)

## Proposed Enhancement

### 1. Parameter Structure

**Current:**
```python
"rpm": 3000.0  # Static RPM value from GUI
```

**Future:**
```python
"rpm_sweep": {
    "enabled": True,
    "start_rpm": 500.0,      # Fixed starting RPM
    "end_rpm": 10000.0,      # Fixed ending RPM  
    "step_rpm": 500.0,       # User-defined step interval from GUI
    "critical_ranges": [     # Optional: focus on critical ranges
        {"start": 2000, "end": 3000, "step": 100},  # Fine resolution around critical range
        {"start": 5000, "end": 6000, "step": 200}   # Another critical range
    ]
}
```

### 1.1 GUI Input Change Required

**Current GUI Input:**
- User inputs a static RPM value (e.g., 3000 RPM)
- Single analysis performed at that RPM

**Future GUI Input:**
- User inputs an RPM step interval (e.g., 500 RPM)
- System automatically sweeps from 500 to 10000 RPM in 500 RPM steps
- Comprehensive analysis across 20 different RPM values

### 2. New Methods to Add

#### FEAAnalyzer
- `analyze_assembly_rpm_sweep()` - Main RPM sweep analysis method
- `_generate_rpm_sweep_points()` - Generate RPM points for sweep
- `_analyze_single_rpm()` - Run FEA at single RPM value
- `_compile_rpm_sweep_results()` - Compile results from multiple analyses

#### UnifiedOptimizer
- Integration point in `run_pipeline()` to choose between single RPM and RPM sweep

### 3. Benefits

1. **Resonant Frequency Detection**: Automatically identifies critical speeds
2. **Comprehensive Analysis**: Tests across entire operating range
3. **Safety Margins**: Identifies safe operating ranges
4. **Performance Optimization**: Finds optimal operating speeds
5. **Design Validation**: Ensures design works across all intended speeds

### 4. Output Structure

```python
{
    "rpm_sweep_results": {
        "sweep_config": {...},
        "individual_results": [...],  # Results for each RPM
        "summary": {
            "critical_rpms": [...],           # Identified resonant frequencies
            "max_stress_rpm": 3000.0,         # RPM with highest stress
            "max_vibration_rpm": 2500.0,      # RPM with highest vibration
            "safe_operating_range": {...},    # Safe operating range
            "resonance_avoidance_ranges": [...] # Ranges to avoid
        }
    }
}
```

### 5. Performance Considerations

- **Parallel Processing**: Each RPM analysis is independent and can be parallelized
- **Progressive Analysis**: Start with coarse sweep, then fine-tune critical ranges
- **Caching**: Cache results for repeated analyses

### 6. Implementation Priority

1. **Phase 1**: Basic RPM sweep with fixed step size
2. **Phase 2**: Critical range detection and fine-resolution analysis
3. **Phase 3**: Parallel processing for performance
4. **Phase 4**: Advanced analysis (modal analysis, Campbell diagrams)

## Files Modified with TODO Notes

The following files have been updated with TODO notes indicating this future enhancement:

- `campro/analysis/fea_analyzer.py` - Main FEA analysis method
- `campro/pipeline/unified_optimizer.py` - Pipeline integration point
- `campro/optimization/collocation_optimizer.py` - Motion law RPM scaling
- `campro/physics/force_transfer.py` - Friction and windage loss calculations
- `campro/solvers/robust_gear_design.py` - Gear radius calculations
- `desktop/src/main/kotlin/com/campro/v5/models/OptimizationParameters.kt` - **GUI INPUT CHANGE REQUIRED**

## GUI Changes Required

### Current GUI Behavior:
- User inputs a single RPM value (e.g., 3000 RPM)
- System performs analysis at that single RPM

### Future GUI Behavior:
- User inputs an RPM step interval (e.g., 500 RPM)
- System automatically performs analysis at: 500, 1000, 1500, 2000, ..., 10000 RPM
- Results show comprehensive analysis across all tested speeds
- GUI displays resonant frequencies, critical speeds, and safe operating ranges

## Status

**Priority**: Not currently a priority - focusing on core optimization functionality first.

**Timeline**: To be implemented after core optimization pipeline is stable and well-tested.

**Dependencies**: Requires stable FEA analyzer and robust single-RPM analysis before extending to sweep functionality.
