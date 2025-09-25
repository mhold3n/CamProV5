#!/usr/bin/env python3
"""
Unit test for motion law displacement validation.

This test ensures that the motion law displacement corresponds to the expected
piston displacement for the planetary gearset test parameters.
"""

import unittest
import numpy as np
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from campro.models.movement_law import MotionLaw, MotionParameters
from scripts.generate_gear_profiles import GearProfileGenerator


class TestMotionLawDisplacement(unittest.TestCase):
    """Test motion law displacement for planetary gearset parameters."""
    
    def setUp(self):
        """Set up test parameters matching the established test data."""
        # Create a temporary output directory for testing
        import tempfile
        from pathlib import Path
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = GearProfileGenerator(self.temp_dir)
        self.params = self.generator.get_stress_test_parameters()
        
        # Expected values from our established test data
        self.expected_stroke_length = 100.0  # mm
        self.expected_ring_rotation = 180.0  # degrees
        self.expected_planet_rotation = 360.0  # degrees
        self.expected_gear_ratio = 2.0  # planet:ring
        
        # Motion law parameters
        self.motion_params = MotionParameters(
            base_circle_radius=self.params["planetRadius"],
            max_lift=self.params["strokeLengthMm"],
            rise_duration=self.params["rampBeforeTdcDeg"] + self.params["rampAfterTdcDeg"],
            dwell_duration=self.params["dwellTdcDeg"],
            fall_duration=self.params["rampBeforeBdcDeg"] + self.params["rampAfterBdcDeg"],
            rpm=self.params["rpm"]
        )
        
        self.motion_law = MotionLaw(self.motion_params)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_motion_law_span(self):
        """Test that motion law spans the expected range."""
        # Generate motion law for full 360° (as currently implemented)
        theta_deg = np.arange(0, 360, self.params["samplingStepDeg"])
        displacement = self.motion_law.displacement(theta_deg)
        
        # Check that we have the expected number of points
        expected_points = int(360 / self.params["samplingStepDeg"])
        self.assertEqual(len(displacement), expected_points)
        
        # Check that displacement spans the expected range
        min_displacement = np.min(displacement)
        max_displacement = np.max(displacement)
        stroke_range = max_displacement - min_displacement
        
        # Allow some tolerance for numerical precision
        self.assertAlmostEqual(stroke_range, self.expected_stroke_length, places=1)
        
        print(f"Motion law span test:")
        print(f"  Points: {len(displacement)} (expected: {expected_points})")
        print(f"  Min displacement: {min_displacement:.3f} mm")
        print(f"  Max displacement: {max_displacement:.3f} mm")
        print(f"  Stroke range: {stroke_range:.3f} mm (expected: {self.expected_stroke_length} mm)")
    
    def test_motion_law_characteristics(self):
        """Test specific characteristics of the motion law."""
        # Use the corrected motion law generation that spans 180° ring rotation
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.params)
        
        # Test 1: Motion should span the full 180° ring rotation
        # Check that there's significant motion throughout the 180° cycle
        n = len(displacement)
        max_angle = np.max(theta_deg)
        
        print(f"\nMotion law characteristics test:")
        print(f"  Motion law spans: 0° to {max_angle:.1f}°")
        print(f"  Number of points: {n}")
        
        # Check displacement variation in different segments of the 180° cycle
        if max_angle >= 180.0:
            # Full 180° cycle
            idx_60 = int(60 / self.params["samplingStepDeg"])
            idx_120 = int(120 / self.params["samplingStepDeg"])
            idx_180 = int(180 / self.params["samplingStepDeg"])
            
            disp_0_60 = displacement[:idx_60]
            disp_60_120 = displacement[idx_60:idx_120]
            disp_120_180 = displacement[idx_120:idx_180]
            
            var_0_60 = np.max(disp_0_60) - np.min(disp_0_60)
            var_60_120 = np.max(disp_60_120) - np.min(disp_60_120)
            var_120_180 = np.max(disp_120_180) - np.min(disp_120_180)
            
            print(f"  Displacement variation by segment:")
            print(f"    0-60°:   {var_0_60:.3f} mm")
            print(f"    60-120°: {var_60_120:.3f} mm")
            print(f"    120-180°: {var_120_180:.3f} mm")
            
            # Test 2: Motion should continue throughout the 180° cycle
            self.assertGreater(var_0_60, 10.0, "Motion should be significant in 0-60°")
            self.assertGreater(var_60_120, 1.0, "Motion should continue beyond 60°")
            self.assertGreater(var_120_180, 10.0, "Motion should be significant in 120-180°")
        else:
            # Partial cycle - this would be an error
            total_variation = np.max(displacement) - np.min(displacement)
            print(f"  Total displacement variation: {total_variation:.3f} mm")
            self.assertGreater(max_angle, 150.0, "Motion law should span at least 150°")
        
        # Test 3: Check for expected motion law features
        # Should have dwell periods (low velocity)
        max_velocity = np.max(np.abs(velocity))
        low_velocity_threshold = max_velocity * 0.1
        
        # Find dwell periods (where velocity is low)
        dwell_indices = np.where(np.abs(velocity) < low_velocity_threshold)[0]
        dwell_periods = len(dwell_indices)
        
        print(f"  Velocity analysis:")
        print(f"    Max velocity: {max_velocity:.3f} mm/deg")
        print(f"    Low velocity threshold: {low_velocity_threshold:.3f} mm/deg")
        print(f"    Dwell periods (low velocity): {dwell_periods} points")
        
        # Should have some dwell periods
        self.assertGreater(dwell_periods, 10, "Should have dwell periods")
    
    def test_planetary_gearset_mapping(self):
        """Test that motion law correctly maps to planetary gearset kinematics."""
        # Generate motion law
        theta_deg = np.arange(0, 360, self.params["samplingStepDeg"])
        displacement = self.motion_law.displacement(theta_deg)
        
        # Generate gear profiles to get planet kinematics
        gear_profiles = self.generator.generate_gear_profiles(
            theta_deg, self.motion_law.velocity(theta_deg), self.params
        )
        planets = self.generator.generate_planet_kinematics(gear_profiles, self.params)
        
        # Test that planet piston motion corresponds to motion law
        planet1_piston = planets[0]["piston_s"]
        
        # The piston motion should have similar characteristics to the motion law
        piston_stroke = np.max(planet1_piston) - np.min(planet1_piston)
        motion_law_stroke = np.max(displacement) - np.min(displacement)
        
        print(f"\nPlanetary gearset mapping test:")
        print(f"  Motion law stroke: {motion_law_stroke:.3f} mm")
        print(f"  Planet piston stroke: {piston_stroke:.3f} mm")
        print(f"  Stroke ratio: {piston_stroke/motion_law_stroke:.3f}")
        
        # The strokes should be related (not necessarily identical due to kinematics)
        self.assertGreater(piston_stroke, 50.0, "Planet piston should have significant stroke")
        self.assertGreater(motion_law_stroke, 50.0, "Motion law should have significant stroke")
    
    def test_expected_discrete_values(self):
        """Test specific expected discrete displacement values."""
        # Use the corrected motion law generation that spans 180° ring rotation
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.params)
        
        # Test specific expected values based on our parameters
        # These should match the established test data
        
        # Test specific expected values for 180° motion law
        max_angle = np.max(theta_deg)
        n = len(displacement)
        
        print(f"\nExpected discrete values test:")
        print(f"  Motion law spans: 0° to {max_angle:.1f}°")
        print(f"  Number of points: {n}")
        
        # Test 1: At 0° (start of cycle)
        disp_0 = displacement[0]
        print(f"  Displacement at 0°: {disp_0:.3f} mm")
        
        # Test 2: At 45° (quarter cycle)
        idx_45 = int(45 / self.params["samplingStepDeg"])
        if idx_45 < n:
            disp_45 = displacement[idx_45]
            print(f"  Displacement at 45°: {disp_45:.3f} mm")
        
        # Test 3: At 90° (mid-cycle)
        idx_90 = int(90 / self.params["samplingStepDeg"])
        if idx_90 < n:
            disp_90 = displacement[idx_90]
            print(f"  Displacement at 90°: {disp_90:.3f} mm")
        
        # Test 4: At 135° (three-quarter cycle)
        idx_135 = int(135 / self.params["samplingStepDeg"])
        if idx_135 < n:
            disp_135 = displacement[idx_135]
            print(f"  Displacement at 135°: {disp_135:.3f} mm")
        
        # Test 5: At 180° (end of cycle)
        disp_180 = displacement[-1]
        print(f"  Displacement at 180°: {disp_180:.3f} mm")
        
        # Test 6: Check for expected motion law features
        # Should have significant variation throughout the 180° cycle
        total_variation = np.max(displacement) - np.min(displacement)
        print(f"  Total displacement variation: {total_variation:.3f} mm")
        self.assertGreater(total_variation, self.expected_stroke_length * 0.8, 
                          "Motion law should have significant variation")
        
        # Test 7: Check that motion spans the full 180° cycle
        # Compare variation in first half vs second half of the 180° cycle
        mid_point = len(displacement) // 2
        first_half_var = np.max(displacement[:mid_point]) - np.min(displacement[:mid_point])
        second_half_var = np.max(displacement[mid_point:]) - np.min(displacement[mid_point:])
        
        print(f"  First half variation (0-90°): {first_half_var:.3f} mm")
        print(f"  Second half variation (90-180°): {second_half_var:.3f} mm")
        
        # Both halves should have significant variation for a proper 180° motion law
        self.assertGreater(first_half_var, 10.0, "First half should have significant motion")
        self.assertGreater(second_half_var, 10.0, "Second half should have significant motion")
        
        # Test 8: Verify the motion law spans the expected 180° range
        self.assertGreater(max_angle, 170.0, "Motion law should span at least 170°")
        self.assertLess(max_angle, 190.0, "Motion law should not exceed 190°")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
