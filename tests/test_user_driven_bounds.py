#!/usr/bin/env python3
"""
Test user-driven bounds for gear ratio and journal offset.
"""

import numpy as np
from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters

def create_complex_motion_law():
    """Create a motion law with varying acceleration to drive variable ratios."""
    
    n = 37
    theta_deg = np.linspace(0.0, 180.0, n)
    theta_rad = np.deg2rad(theta_deg)
    
    # Create a motion law with varying acceleration
    displacement = 10.0 * (1 - np.cos(theta_rad))  # 0 to 20mm stroke
    velocity = np.gradient(displacement, theta_rad)
    acceleration = np.gradient(velocity, theta_rad)
    
    return {
        'grid': theta_rad,  # In radians for consistency
        'displacement': displacement,
        'velocity': velocity,
        'acceleration': acceleration,
    }

def test_user_driven_bounds():
    """Test that bounds are driven by user inputs."""
    
    print("=== Testing User-Driven Bounds ===")
    
    # Create complex motion law
    motion_law = create_complex_motion_law()
    print(f"Motion law: {len(motion_law['grid'])} points")
    print(f"Displacement range: [{np.min(motion_law['displacement']):.3f}, {np.max(motion_law['displacement']):.3f}]")
    
    # Test different user input scenarios
    test_cases = [
        {
            'gearRatio': 2.0,
            'maxGearRatioVariation': 0.2,
            'maxJournalOffsetPercent': 0.05,
            'name': 'Conservative bounds (small variation)'
        },
        {
            'gearRatio': 2.0,
            'maxGearRatioVariation': 0.5,
            'maxJournalOffsetPercent': 0.1,
            'name': 'Moderate bounds (medium variation)'
        },
        {
            'gearRatio': 2.0,
            'maxGearRatioVariation': 1.0,
            'maxJournalOffsetPercent': 0.2,
            'name': 'Aggressive bounds (large variation)'
        },
        {
            'gearRatio': 2.5,
            'maxGearRatioVariation': 0.3,
            'maxJournalOffsetPercent': 0.08,
            'name': 'Higher nominal ratio'
        }
    ]
    
    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        print(f"User inputs: gearRatio={case['gearRatio']}, maxGearRatioVariation={case['maxGearRatioVariation']}, maxJournalOffsetPercent={case['maxJournalOffsetPercent']}")
        
        # Calculate expected bounds
        expected_r_min = max(2.0, case['gearRatio'] - case['maxGearRatioVariation'])
        expected_r_max = case['gearRatio'] + case['maxGearRatioVariation']
        typical_planet_radius = max(5.0, np.mean(np.abs(motion_law['displacement'])) * 0.5)
        expected_journal_offset_max = typical_planet_radius * case['maxJournalOffsetPercent']
        
        print(f"Expected r bounds: [{expected_r_min:.3f}, {expected_r_max:.3f}]")
        print(f"Expected journal offset bounds: [{-expected_journal_offset_max:.3f}, {expected_journal_offset_max:.3f}]")
        
        gear_params = {
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 5.0,
            'gearRatio': case['gearRatio'],
            'rMin': expected_r_min,
            'rMax': expected_r_max,
            'maxGearRatioVariation': case['maxGearRatioVariation'],
            'maxJournalOffsetPercent': case['maxJournalOffsetPercent'],
            'motionVariationWeight': 0.5,
        }
        
        opt = Phase2GearOptimizer(Phase2Parameters(node_count=len(motion_law['grid'])))
        
        try:
            sol = opt.optimize_gear_profiles(motion_law, gear_params)
            if sol.success:
                r_inst = sol.instantaneous_ratio
                journal_offset = sol.journal_offset
                
                print(f"Actual r_inst range: [{np.min(r_inst):.3f}, {np.max(r_inst):.3f}]")
                print(f"Actual journal offset range: [{np.min(journal_offset):.3f}, {np.max(journal_offset):.3f}]")
                
                # Check if bounds are respected
                r_within_bounds = np.all(r_inst >= expected_r_min - 1e-6) and np.all(r_inst <= expected_r_max + 1e-6)
                offset_within_bounds = np.all(journal_offset >= -expected_journal_offset_max - 1e-6) and np.all(journal_offset <= expected_journal_offset_max + 1e-6)
                
                print(f"r(θ) within bounds: {'✓' if r_within_bounds else '✗'}")
                print(f"δ(θ) within bounds: {'✓' if offset_within_bounds else '✗'}")
                
                # Check variation
                r_variation = np.max(r_inst) - np.min(r_inst)
                offset_variation = np.max(journal_offset) - np.min(journal_offset)
                print(f"r(θ) variation: {r_variation:.3f}")
                print(f"δ(θ) variation: {offset_variation:.3f}")
                
            else:
                print(f"Failed: {sol.solver_status}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_user_driven_bounds()
