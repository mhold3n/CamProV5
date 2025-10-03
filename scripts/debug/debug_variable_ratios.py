#!/usr/bin/env python3
"""
Debug why r(θ) is not varying and how to implement discrete variable ratios.
"""

import json
import numpy as np
from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters

def debug_variable_ratios():
    """Debug why r(θ) is not varying."""
    
    print("=== Variable Ratios Debug ===")
    
    # Load the actual motion law
    with open('/Users/maxholden/Documents/GitHub/CamProV5/desktop/output/optimization_results.json', 'r') as f:
        results = json.load(f)
    
    motion_law = results['motion_law']
    print(f"Motion law: {len(motion_law['grid'])} points")
    print(f"Displacement range: [{min(motion_law['displacement']):.3f}, {max(motion_law['displacement']):.3f}]")
    print(f"Velocity range: [{min(motion_law['velocity']):.3f}, {max(motion_law['velocity']):.3f}]")
    
    # Test different r bounds to see if we can get variation
    test_cases = [
        {'rMin': 2.0, 'rMax': 2.0, 'name': 'Fixed 2.0'},
        {'rMin': 2.0, 'rMax': 2.5, 'name': 'Current bounds'},
        {'rMin': 1.8, 'rMax': 2.2, 'name': 'Narrow variation'},
        {'rMin': 1.5, 'rMax': 2.5, 'name': 'Wide variation'},
    ]
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        gear_params = {
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 5.0,
            'rMin': case['rMin'],
            'rMax': case['rMax'],
        }
        
        opt = Phase2GearOptimizer(Phase2Parameters(node_count=len(motion_law['grid'])))
        
        try:
            sol = opt.optimize_gear_profiles(motion_law, gear_params)
            if sol.success:
                r_inst = sol.instantaneous_ratio
                print(f"Success: r_inst range = [{np.min(r_inst):.3f}, {np.max(r_inst):.3f}]")
                print(f"r_inst std dev: {np.std(r_inst):.6f}")
                print(f"r_inst unique values: {len(np.unique(np.round(r_inst, 3)))}")
            else:
                print(f"Failed: {sol.solver_status}")
        except Exception as e:
            print(f"Error: {e}")

def analyze_why_no_variation():
    """Analyze why r(θ) is not varying."""
    
    print("\n=== Why No Variation Analysis ===")
    
    print("Possible reasons why r(θ) is fixed at 2.0:")
    print("1. **Objective function**: The current objective only has smoothness terms")
    print("   - No incentive to vary r(θ) if smoothness weight is low")
    print("   - Need to add terms that encourage variation based on motion law")
    
    print("\n2. **Constraint system**: The constraints might be forcing r(θ) to be constant")
    print("   - Global constraint: sum(r_i) * step = 2 * total_rotation")
    print("   - If motion law is uniform, uniform r(θ) might be optimal")
    
    print("\n3. **Motion law characteristics**: The current motion law might not require variation")
    print("   - Constant velocity motion law")
    print("   - No acceleration changes that would benefit from variable ratios")
    
    print("\n4. **Initial guess**: Starting at r=2.0 might bias the solution")
    
    print("\n=== Solutions to Implement Variable Ratios ===")
    print("1. **Add motion-dependent objective terms**:")
    print("   - Penalty for r(θ) that doesn't match local motion requirements")
    print("   - Efficiency terms that vary with velocity/acceleration")
    
    print("\n2. **Use motion law to guide r(θ) variation**:")
    print("   - Higher r(θ) during high acceleration phases")
    print("   - Lower r(θ) during constant velocity phases")
    
    print("\n3. **Add discrete constraints**:")
    print("   - Force r(θ) to vary between different phases")
    print("   - Add phase-specific ratio requirements")
    
    print("\n4. **Modify initial guess**:")
    print("   - Start with varying r(θ) based on motion law")
    print("   - Use motion-dependent initial values")

if __name__ == "__main__":
    debug_variable_ratios()
    analyze_why_no_variation()
