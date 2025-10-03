#!/usr/bin/env python3
"""
Debug the global integral constraint.
"""

import numpy as np

def debug_global_constraint():
    """Debug the global 2:1 integral constraint."""
    
    print("=== Global Constraint Analysis ===")
    
    # Global constraint: sum_{i=0..n-2} r_i * Δθ = 2 * Θ
    # Where Θ is the total ring rotation
    
    n = 5
    theta_deg = np.linspace(0.0, 180.0, n)
    step_deg = theta_deg[1] - theta_deg[0]
    ring_rotation_deg = 180.0
    
    print(f"n = {n} points")
    print(f"step_deg = {step_deg}")
    print(f"ring_rotation_deg = {ring_rotation_deg}")
    print()
    
    # For a fixed ratio of 2.0
    r_fixed = 2.0
    r_inst = np.full(n, r_fixed)
    
    # Sum over intervals (n-1 intervals)
    r_sum_intervals = np.sum(r_inst[:-1])  # Sum over first n-1 elements
    global_constraint = r_sum_intervals * step_deg - 2.0 * ring_rotation_deg
    
    print(f"Fixed ratio r = {r_fixed}")
    print(f"r_inst = {r_inst}")
    print(f"Sum over intervals (first {n-1}): {r_sum_intervals}")
    print(f"Global constraint: {r_sum_intervals} * {step_deg} - 2 * {ring_rotation_deg} = {global_constraint}")
    print()
    
    # For variable ratios
    print("Variable ratios:")
    for r_avg in [2.0, 2.1, 2.2, 2.3, 2.4, 2.5]:
        r_inst = np.full(n, r_avg)
        r_sum_intervals = np.sum(r_inst[:-1])
        global_constraint = r_sum_intervals * step_deg - 2.0 * ring_rotation_deg
        print(f"r_avg = {r_avg}: constraint = {global_constraint:.6f}")
    
    print()
    print("The global constraint should be 0 for the 2:1 ratio to be satisfied.")
    print("For r_avg = 2.0, we get exactly 0, which is correct.")

if __name__ == "__main__":
    debug_global_constraint()
