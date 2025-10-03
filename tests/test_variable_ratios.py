#!/usr/bin/env python3
"""
Test the variable gear ratios implementation.
"""

import json
import numpy as np
from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters

def test_variable_ratios():
    """Test variable gear ratios with motion-dependent objective."""
    
    print("=== Testing Variable Gear Ratios ===")
    
    # Load the actual motion law
    with open('/Users/maxholden/Documents/GitHub/CamProV5/desktop/output/optimization_results.json', 'r') as f:
        results = json.load(f)
    
    motion_law = results['motion_law']
    print(f"Motion law: {len(motion_law['grid'])} points")
    print(f"Displacement range: [{min(motion_law['displacement']):.3f}, {max(motion_law['displacement']):.3f}]")
    print(f"Velocity range: [{min(motion_law['velocity']):.3f}, {max(motion_law['velocity']):.3f}]")
    print(f"Acceleration range: [{min(motion_law['acceleration']):.3f}, {max(motion_law['acceleration']):.3f}]")
    
    # Test with motion variation weight
    test_cases = [
        {'motionVariationWeight': 0.0, 'name': 'No motion variation'},
        {'motionVariationWeight': 0.1, 'name': 'Low motion variation'},
        {'motionVariationWeight': 0.5, 'name': 'Medium motion variation'},
        {'motionVariationWeight': 1.0, 'name': 'High motion variation'},
    ]
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        gear_params = {
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 5.0,
            'rMin': 2.0,
            'rMax': 2.5,
            'motionVariationWeight': case['motionVariationWeight'],
        }
        
        opt = Phase2GearOptimizer(Phase2Parameters(node_count=len(motion_law['grid'])))
        
        try:
            sol = opt.optimize_gear_profiles(motion_law, gear_params)
            if sol.success:
                r_inst = sol.instantaneous_ratio
                print(f"Success: r_inst range = [{np.min(r_inst):.3f}, {np.max(r_inst):.3f}]")
                print(f"r_inst std dev: {np.std(r_inst):.6f}")
                print(f"r_inst unique values: {len(np.unique(np.round(r_inst, 3)))}")
                
                # Show first few values
                print(f"First 10 r_inst values: {r_inst[:10]}")
                
                # Check if variation is meaningful
                if np.std(r_inst) > 0.01:
                    print("✓ Variable ratios achieved!")
                else:
                    print("✗ Still uniform ratios")
            else:
                print(f"Failed: {sol.solver_status}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_variable_ratios()
