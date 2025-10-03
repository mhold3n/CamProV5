#!/usr/bin/env python3
"""
Debug the motion law units issue.
"""

import json
import numpy as np

def debug_motion_law_units():
    """Debug the motion law units."""
    
    print("=== Motion Law Units Debug ===")
    
    # Load the actual motion law
    with open('/Users/maxholden/Documents/GitHub/CamProV5/desktop/output/optimization_results.json', 'r') as f:
        results = json.load(f)
    
    motion_law = results['motion_law']
    grid = motion_law['grid']
    
    print(f"Grid range: [{grid[0]:.6f}, {grid[-1]:.6f}]")
    print(f"Grid range in degrees: [{np.degrees(grid[0]):.1f}, {np.degrees(grid[-1]):.1f}]")
    
    # Check if grid is in radians or degrees
    if abs(grid[-1] - 2 * np.pi) < 0.1:
        print("Grid appears to be in RADIANS (0 to 2π)")
        step_rad = grid[1] - grid[0]
        step_deg = np.degrees(step_rad)
        print(f"Step size: {step_rad:.6f} rad = {step_deg:.1f} deg")
    elif abs(grid[-1] - 180.0) < 0.1:
        print("Grid appears to be in DEGREES (0 to 180°)")
        step_deg = grid[1] - grid[0]
        print(f"Step size: {step_deg:.1f} deg")
    else:
        print(f"Grid range unclear: {grid[-1]:.3f}")
    
    # Load input parameters
    with open('/Users/maxholden/Documents/GitHub/CamProV5/desktop/output/input_parameters.json', 'r') as f:
        input_params = json.load(f)
    
    print(f"Input samplingStepDeg: {input_params['samplingStepDeg']}")
    print(f"Input ringRotationDeg: {input_params['ringRotationDeg']}")
    
    # Check the global constraint calculation
    n = len(grid)
    if abs(grid[-1] - 2 * np.pi) < 0.1:
        # Grid is in radians, need to convert to degrees for constraint
        step_deg = np.degrees(grid[1] - grid[0])
        ring_rotation_deg = np.degrees(grid[-1] - grid[0])
    else:
        # Grid is in degrees
        step_deg = grid[1] - grid[0]
        ring_rotation_deg = grid[-1] - grid[0]
    
    print(f"Calculated step_deg: {step_deg:.1f}")
    print(f"Calculated ring_rotation_deg: {ring_rotation_deg:.1f}")
    
    # Test global constraint with correct units
    r_avg = 2.0
    r_inst = np.full(n, r_avg)
    r_sum_intervals = np.sum(r_inst[:-1])
    global_constraint = r_sum_intervals * step_deg - 2.0 * ring_rotation_deg
    
    print("Global constraint with r_avg=2.0:")
    print(f"  Sum over intervals: {r_sum_intervals}")
    print(f"  Constraint: {r_sum_intervals} * {step_deg:.1f} - 2 * {ring_rotation_deg:.1f} = {global_constraint:.6f}")

if __name__ == "__main__":
    debug_motion_law_units()
