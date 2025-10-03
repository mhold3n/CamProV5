#!/usr/bin/env python3
"""
Debug the global constraint with real motion law data.
"""

import json
import numpy as np

def debug_global_constraint_real():
    """Debug the global constraint with real data."""
    
    print("=== Global Constraint Debug (Real Data) ===")
    
    # Load the actual motion law
    with open('/Users/maxholden/Documents/GitHub/CamProV5/desktop/output/optimization_results.json', 'r') as f:
        results = json.load(f)
    
    motion_law = results['motion_law']
    grid = motion_law['grid']
    n = len(grid)
    
    print(f"n = {n} points")
    print(f"Grid range: [{grid[0]:.3f}, {grid[-1]:.3f}]")
    
    # Calculate step size
    step_deg = grid[1] - grid[0] if n > 1 else 0
    ring_rotation_deg = 180.0
    
    print(f"step_deg = {step_deg}")
    print(f"ring_rotation_deg = {ring_rotation_deg}")
    print()
    
    # Test different r values
    r_values = [2.0, 2.1, 2.2, 2.3, 2.4, 2.5]
    
    for r_avg in r_values:
        r_inst = np.full(n, r_avg)
        r_sum_intervals = np.sum(r_inst[:-1])  # Sum over first n-1 elements
        global_constraint = r_sum_intervals * step_deg - 2.0 * ring_rotation_deg
        
        print(f"r_avg = {r_avg}:")
        print(f"  Sum over intervals: {r_sum_intervals}")
        print(f"  Global constraint: {r_sum_intervals} * {step_deg} - 2 * {ring_rotation_deg} = {global_constraint:.6f}")
        
        # Check if this would be feasible
        if abs(global_constraint) < 1e-6:
            print("  ✓ Feasible (constraint ≈ 0)")
        else:
            print("  ✗ Infeasible (constraint ≠ 0)")
        print()
    
    # Test with variable r values that average to 2.0
    print("Variable r values averaging to 2.0:")
    r_variable = np.array([1.8, 2.0, 2.2, 2.0, 1.8] + [2.0] * (n-5))  # Ensure average is 2.0
    r_sum_intervals = np.sum(r_variable[:-1])
    global_constraint = r_sum_intervals * step_deg - 2.0 * ring_rotation_deg
    
    print(f"Variable r: {r_variable[:10]}... (showing first 10)")
    print(f"Average: {np.mean(r_variable):.3f}")
    print(f"Sum over intervals: {r_sum_intervals}")
    print(f"Global constraint: {global_constraint:.6f}")

if __name__ == "__main__":
    debug_global_constraint_real()
