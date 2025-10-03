#!/usr/bin/env python3
"""
Debug with the actual motion law from the GUI.
"""

import json
import numpy as np
from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters

def debug_real_motion_law():
    """Debug with the actual motion law from the GUI."""
    
    print("=== Real Motion Law Debug ===")
    
    # Load the actual input parameters
    with open('/Users/maxholden/Documents/GitHub/CamProV5/desktop/output/input_parameters.json', 'r') as f:
        input_params = json.load(f)
    
    print(f"Input parameters: rMin={input_params['rMin']}, rMax={input_params['rMax']}")
    
    # Load the actual motion law from the results
    with open('/Users/maxholden/Documents/GitHub/CamProV5/desktop/output/optimization_results.json', 'r') as f:
        results = json.load(f)
    
    motion_law = results['motion_law']
    print(f"Motion law: {len(motion_law['grid'])} points")
    print(f"Displacement range: [{min(motion_law['displacement']):.3f}, {max(motion_law['displacement']):.3f}]")
    print(f"Velocity range: [{min(motion_law['velocity']):.3f}, {max(motion_law['velocity']):.3f}]")
    print(f"Acceleration range: [{min(motion_law['acceleration']):.3f}, {max(motion_law['acceleration']):.3f}]")
    
    # Try Phase 2 optimization with the real motion law
    gear_params = {
        'ringRotationDeg': input_params['ringRotationDeg'],
        'samplingStepDeg': input_params['samplingStepDeg'],
        'rMin': input_params['rMin'],
        'rMax': input_params['rMax'],
    }
    
    print(f"Gear params: {gear_params}")
    
    opt = Phase2GearOptimizer(Phase2Parameters(node_count=len(motion_law['grid'])))
    
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
    debug_real_motion_law()
