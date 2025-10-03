#!/usr/bin/env python3
"""
Debug script for Phase 2 gear optimization infeasibility.
"""

import numpy as np
from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters

def debug_phase2_feasibility():
    """Debug why Phase 2 optimization is infeasible."""
    
    # Very simple motion law
    n = 5  # Small number of points
    theta_deg = np.linspace(0.0, 180.0, n)
    displacement = np.zeros(n)  # No displacement
    velocity = np.zeros(n)
    acceleration = np.zeros(n)
    
    motion_law = {
        'grid': theta_deg,
        'displacement': displacement,
        'velocity': velocity,
        'acceleration': acceleration,
    }
    
    gear_params = {
        'ringRotationDeg': 180.0,
        'samplingStepDeg': theta_deg[1] - theta_deg[0],
        'rMin': 2.0,  # Must be >= 2.0 for geometric consistency
        'rMax': 2.5,
    }
    
    print("=== Phase 2 Debug ===")
    print(f"Motion law: {len(motion_law['grid'])} points")
    print(f"Displacement range: [{np.min(displacement):.3f}, {np.max(displacement):.3f}]")
    print(f"Gear params: {gear_params}")
    
    opt = Phase2GearOptimizer(Phase2Parameters(node_count=n))
    
    # Try to build the NLP formulation
    try:
        nlp_info = opt._build_gear_nlp_formulation(motion_law, gear_params, theta_deg)
        print(f"NLP built successfully: {len(nlp_info['x0'])} variables, {len(nlp_info['lbg'])} constraints")
        
        # Check bounds
        print(f"Variable bounds: [{np.min(nlp_info['lbx']):.3f}, {np.max(nlp_info['ubx']):.3f}]")
        print(f"Constraint bounds: [{np.min(nlp_info['lbg']):.3f}, {np.max(nlp_info['ubg']):.3f}]")
        
        # Check initial guess
        print(f"Initial guess range: [{np.min(nlp_info['x0']):.3f}, {np.max(nlp_info['x0']):.3f}]")
        
    except Exception as e:
        print(f"Failed to build NLP: {e}")
        return
    
    # Try optimization
    try:
        sol = opt.optimize_gear_profiles(motion_law, gear_params)
        print(f"Optimization result: success={sol.success}, status={sol.solver_status}")
        if sol.success:
            print("Gear radii ranges:")
            print(f"  Sun: [{np.min(sol.sun_radius):.3f}, {np.max(sol.sun_radius):.3f}]")
            print(f"  Planet: [{np.min(sol.planet_radius):.3f}, {np.max(sol.planet_radius):.3f}]")
            print(f"  Ring: [{np.min(sol.ring_radius):.3f}, {np.max(sol.ring_radius):.3f}]")
            print(f"  r_inst: [{np.min(sol.instantaneous_ratio):.3f}, {np.max(sol.instantaneous_ratio):.3f}]")
        else:
            print(f"Objective value: {sol.objective_value}")
            print(f"Constraint violation: {sol.constraint_violation}")
    except Exception as e:
        print(f"Optimization failed: {e}")

if __name__ == "__main__":
    debug_phase2_feasibility()
