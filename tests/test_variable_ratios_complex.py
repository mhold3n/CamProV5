#!/usr/bin/env python3
"""
Test variable gear ratios with a complex motion law that has varying acceleration.
"""

import numpy as np
from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters

def create_complex_motion_law():
    """Create a motion law with varying acceleration to drive variable ratios."""
    
    n = 37
    theta_deg = np.linspace(0.0, 180.0, n)
    theta_rad = np.deg2rad(theta_deg)
    
    # Create a motion law with varying acceleration
    # This simulates a piston with acceleration/deceleration phases
    displacement = 10.0 * (1 - np.cos(theta_rad))  # 0 to 20mm stroke
    velocity = np.gradient(displacement, theta_rad)
    acceleration = np.gradient(velocity, theta_rad)
    
    return {
        'grid': theta_rad,  # In radians for consistency
        'displacement': displacement,
        'velocity': velocity,
        'acceleration': acceleration,
    }

def test_variable_ratios_complex():
    """Test variable gear ratios with complex motion law."""
    
    print("=== Testing Variable Ratios with Complex Motion Law ===")
    
    # Create complex motion law
    motion_law = create_complex_motion_law()
    print(f"Motion law: {len(motion_law['grid'])} points")
    print(f"Displacement range: [{np.min(motion_law['displacement']):.3f}, {np.max(motion_law['displacement']):.3f}]")
    print(f"Velocity range: [{np.min(motion_law['velocity']):.3f}, {np.max(motion_law['velocity']):.3f}]")
    print(f"Acceleration range: [{np.min(motion_law['acceleration']):.3f}, {np.max(motion_law['acceleration']):.3f}]")
    
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
                    
                    # Show correlation with acceleration
                    accel_norm = np.abs(motion_law['acceleration']) / np.max(np.abs(motion_law['acceleration']))
                    correlation = np.corrcoef(accel_norm, r_inst)[0, 1]
                    print(f"Correlation with acceleration: {correlation:.3f}")
                else:
                    print("✗ Still uniform ratios")
            else:
                print(f"Failed: {sol.solver_status}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_variable_ratios_complex()
