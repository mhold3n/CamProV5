#!/usr/bin/env python3
"""
Debug the step size calculation in the global constraint.
"""

import json
import numpy as np

def debug_step_size():
    """Debug the step size calculation."""
    
    print("=== Step Size Debug ===")
    
    # Load the actual motion law
    with open('/Users/maxholden/Documents/GitHub/CamProV5/desktop/output/optimization_results.json', 'r') as f:
        results = json.load(f)
    
    motion_law = results['motion_law']
    grid = motion_law['grid']
    
    print(f"Grid: {grid[:5]}... (first 5 points)")
    print(f"Grid range: [{grid[0]:.6f}, {grid[-1]:.6f}]")
    
    # Check if grid is in radians or degrees
    if abs(grid[-1] - 2 * np.pi) < 0.1:
        print("Grid is in RADIANS")
        step_rad = grid[1] - grid[0]
        step_deg = np.degrees(step_rad)
        total_rad = grid[-1] - grid[0]
        total_deg = np.degrees(total_rad)
    else:
        print("Grid is in DEGREES")
        step_deg = grid[1] - grid[0]
        total_deg = grid[-1] - grid[0]
    
    print(f"Step size: {step_deg:.3f} degrees")
    print(f"Total range: {total_deg:.3f} degrees")
    
    # Load input parameters
    with open('/Users/maxholden/Documents/GitHub/CamProV5/desktop/output/input_parameters.json', 'r') as f:
        input_params = json.load(f)
    
    ring_rotation_deg = input_params['ringRotationDeg']
    print(f"Expected ring rotation: {ring_rotation_deg} degrees")
    
    # Test global constraint
    n = len(grid)
    r_avg = 2.0
    r_inst = np.full(n, r_avg)
    r_sum_intervals = np.sum(r_inst[:-1])  # Sum over first n-1 elements
    
    print(f"Number of intervals: {n-1}")
    print(f"Sum of r values: {r_sum_intervals}")
    print(f"Global constraint: {r_sum_intervals} * {step_deg:.3f} - 2 * {ring_rotation_deg} = {r_sum_intervals * step_deg - 2 * ring_rotation_deg:.6f}")
    
    # Check if the total range matches expected rotation
    if abs(total_deg - ring_rotation_deg) > 1.0:
        print(f"WARNING: Total range ({total_deg:.1f}°) doesn't match expected rotation ({ring_rotation_deg}°)")
        print("This suggests a units mismatch in the motion law generation")

if __name__ == "__main__":
    debug_step_size()
