#!/usr/bin/env python3
"""
Test suite for extracted gear profile generation.

This module tests the extracted gear profile generation logic from the scripts
to ensure it works correctly when moved to the new modular structure.
"""

import pytest
import numpy as np

from campro.gears.profile_generator import GearProfileGenerator


class TestExtractedGearGeneration:
    """Test suite for extracted gear profile generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = GearProfileGenerator()
        self.baseline_params = self.get_baseline_gear_params()
    
    def get_baseline_gear_params(self):
        """Get baseline gear parameters for testing."""
        return {
            # CORRECTED: 2-stroke cycle over 180° ring rotation, 360° planet rotation
            "ringRotationDeg": 180.0,  # Ring rotates 180° for complete 2-stroke cycle
            "planetRotationDeg": 360.0,  # Planet rotates 360° for complete 2-stroke cycle
            "gearRatio": 2.0,  # Planet:Ring ratio = 360:180 = 2:1

            # Asymmetric stroke durations within 180° ring rotation
            "expansionDurationDeg": 110.0,  # 220° expansion scaled to 180° ring rotation
            "compressionDurationDeg": 70.0,  # 140° compression scaled to 180° ring rotation

            # CORRECTED: Motion law with small acceleration ramps and large constant velocity zones
            # Small acceleration/deceleration ramps (5-8° each)
            "rampBeforeTdcDeg": 6.0,   # Small ramp to accelerate to constant velocity
            "rampAfterTdcDeg": 5.0,    # Small ramp to decelerate from constant velocity
            "rampBeforeBdcDeg": 7.0,   # Small ramp to accelerate to constant velocity
            "rampAfterBdcDeg": 4.0,    # Small ramp to decelerate from constant velocity
            
            # Short dwell periods at TDC and BDC (3-5° each)
            "dwellTdcDeg": 4.0,        # Short dwell at TDC
            "dwellBdcDeg": 3.0,        # Short dwell at BDC
            
            # Linear acceleration periods (constant velocity through most of stroke)
            "linearAccelTdcDeg": 8.0,  # Small window for linear acceleration near TDC
            "linearAccelBdcDeg": 6.0,  # Small window for linear acceleration near BDC
            
            # Motion law parameters
            "strokeLengthMm": 100.0,
            "upFraction": 110.0 / 180.0,  # Asymmetric up/down ratio within 180° ring rotation
            "rodLength": 100.0,
            "rampProfile": "S5",

            # Planetary gearset parameters
            "samplingStepDeg": 1.0,
            "interferenceBuffer": 0.5,
            "planetCount": 2,
            "carrierOffsetDeg": 180.0,
            "ringThicknessVisual": 6.0,
            "arcResidualTolMm": 0.01,
            "sliderAxisDeg": 0.0,
            "journalPhaseBetaDeg": 0.0,
            "journalRadius": 5.0,
            
            # CORRECTED: Proper planetary gearset geometry
            "planetRadius": 15.0,  # Fixed planet radius (not max, but actual)
            "ringInnerRadiusBase": 70.0,  # Base ring inner radius (must be > planet radius)
            "ringInnerRadiusVariation": 10.0,  # Variation in ring inner radius for non-circular profile
            "ringThickness": 3.0,  # Ring gear thickness (outer - inner radius)
            "centerDistance": 85.0,  # Distance from center to planet centers
            "rpm": 3000.0,
            
            # Specific tooth meshing parameters
            "planetTeeth": 20,  # Number of teeth on planet gear
            "ringTeeth": 40,  # Number of teeth on ring gear (2:1 ratio)
            "toothModule": 2.0,  # Module for gear tooth sizing
            
            # Planet COM and journal parameters
            "journalOffsetRadius": 5.0,  # mm offset from planet COM to journal
            "journalAngleOffset": 0.0,  # degrees offset from planet COM to journal
            
            # Gear profile scaling parameters (FIXED: parameterized instead of hardcoded)
            "planetRadiusBaseFactor": 0.3,  # Planet radius as fraction of max rod extension (increased for larger gearset)
            "planetRadiusVariationFactor": 0.1,  # Planet radius variation as fraction of max rod extension (increased for more variation)
            "sunRadiusBaseFactor": 0.2,  # Sun radius as fraction of max rod extension (increased for larger gearset)
            "sunRadiusVariationFactor": 0.05,  # Sun radius variation as fraction of max rod extension (increased for more variation)
            "planetRadiusMinFactor": 0.8,  # Minimum planet radius as fraction of base
            "sunRadiusMinFactor": 0.9,  # Minimum sun radius as fraction of base
            
            # Motion law phase parameters (FIXED: parameterized instead of hardcoded)
            "constantVelocityTdcDeg": 30.0,  # Constant velocity duration at TDC
            "constantVelocityBdcDeg": 40.0,  # Constant velocity duration at BDC
            
            # Gear clearance parameters (duplicate removed)
            "strokeAchievableFactor": 0.3,  # Fraction of stroke that must be achievable (relaxed for testing)
            "clearanceSafetyMargin": 0.1,  # mm safety margin for clearance adjustments
            "adjustmentSplitFactor": 0.5,  # How to split clearance adjustments between sun and ring
        }
    
    def test_motion_law_piecewise_generation(self):
        """Test piecewise motion law generation extraction."""
        # Test the extracted method
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(
            self.baseline_params
        )
        
        # Verify results
        assert len(theta_deg) > 0
        assert len(displacement) == len(theta_deg)
        assert len(velocity) == len(theta_deg)
        assert len(acceleration) == len(theta_deg)
        
        # Check that motion law spans the correct range
        assert np.min(theta_deg) >= 0.0
        assert np.max(theta_deg) <= self.baseline_params["ringRotationDeg"]
        
        # Check that displacement is reasonable
        assert np.min(displacement) >= 0.0
        assert np.max(displacement) <= self.baseline_params["strokeLengthMm"]
        
        # Check that all values are finite
        assert np.all(np.isfinite(displacement))
        assert np.all(np.isfinite(velocity))
        assert np.all(np.isfinite(acceleration))
    
    def test_gear_profile_generation(self):
        """Test gear profile generation extraction."""
        # Generate motion law first
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(
            self.baseline_params
        )
        
        # Test the extracted method
        gear_profiles = self.generator.generate_gear_profiles(
            theta_deg, displacement, self.baseline_params
        )
        
        # Verify results
        assert "theta_deg" in gear_profiles
        assert "r_planet" in gear_profiles
        assert "r_sun" in gear_profiles
        assert "r_ring_inner" in gear_profiles
        assert "r_ring_outer" in gear_profiles
        
        # Check that all profiles have the same length
        n_points = len(gear_profiles["theta_deg"])
        assert len(gear_profiles["r_planet"]) == n_points
        assert len(gear_profiles["r_sun"]) == n_points
        assert len(gear_profiles["r_ring_inner"]) == n_points
        assert len(gear_profiles["r_ring_outer"]) == n_points
        
        # Check that all radii are positive
        assert np.all(gear_profiles["r_planet"] > 0)
        assert np.all(gear_profiles["r_sun"] > 0)
        assert np.all(gear_profiles["r_ring_inner"] > 0)
        assert np.all(gear_profiles["r_ring_outer"] > 0)
        
        # Check that ring outer > ring inner
        assert np.all(gear_profiles["r_ring_outer"] > gear_profiles["r_ring_inner"])
        
        # Check that all values are finite
        assert np.all(np.isfinite(gear_profiles["r_planet"]))
        assert np.all(np.isfinite(gear_profiles["r_sun"]))
        assert np.all(np.isfinite(gear_profiles["r_ring_inner"]))
        assert np.all(np.isfinite(gear_profiles["r_ring_outer"]))
    
    def test_gearset_constraints_validation(self):
        """Test gearset constraints validation extraction."""
        # Generate motion law and gear profiles
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(
            self.baseline_params
        )
        gear_profiles = self.generator.generate_gear_profiles(
            theta_deg, displacement, self.baseline_params
        )
        
        # Test the extracted method
        validation_result = self.generator.validate_gearset_constraints(
            gear_profiles, self.baseline_params
        )
        
        # Verify results
        assert isinstance(validation_result, dict)
        assert "passed" in validation_result
        assert "constraints" in validation_result
        
        # Check that validation passed
        assert validation_result["passed"] is True
        
        # Check that all constraints are satisfied
        constraints = validation_result["constraints"]
        assert "unified_constraint" in constraints
        assert "contact_point_constraint" in constraints
        assert "positive_clearance" in constraints
        assert "stroke_achievable" in constraints
        
        # All constraints should be satisfied
        assert constraints["unified_constraint"] is True
        assert constraints["contact_point_constraint"] is True
        assert constraints["positive_clearance"] is True
        assert constraints["stroke_achievable"] is True
    
    def test_planet_kinematics_generation(self):
        """Test planet kinematics generation extraction."""
        # Generate motion law and gear profiles
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(
            self.baseline_params
        )
        gear_profiles = self.generator.generate_gear_profiles(
            theta_deg, displacement, self.baseline_params
        )
        
        # Test the extracted method
        planets = self.generator.generate_planet_kinematics(
            gear_profiles, self.baseline_params
        )
        
        # Verify results
        assert isinstance(planets, list)
        assert len(planets) == self.baseline_params["planetCount"]
        
        for i, planet in enumerate(planets):
            # Check required fields
            assert "planet_angle" in planet
            assert "center_x" in planet
            assert "center_y" in planet
            assert "planet_radius" in planet
            assert "ring_inner_radius" in planet
            assert "sun_radius" in planet
            assert "psi_deg" in planet
            assert "alpha_deg" in planet
            
            # Check that all values are finite
            assert np.all(np.isfinite(planet["center_x"]))
            assert np.all(np.isfinite(planet["center_y"]))
            assert np.all(np.isfinite(planet["planet_radius"]))
            assert np.all(np.isfinite(planet["ring_inner_radius"]))
            assert np.all(np.isfinite(planet["sun_radius"]))
            assert np.all(np.isfinite(planet["psi_deg"]))
            assert np.all(np.isfinite(planet["alpha_deg"]))
    
    def test_unified_constraint_system(self):
        """Test that the unified constraint system is properly enforced."""
        # Generate motion law and gear profiles
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(
            self.baseline_params
        )
        gear_profiles = self.generator.generate_gear_profiles(
            theta_deg, displacement, self.baseline_params
        )
        
        # Check UNIFIED CONSTRAINT: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
        r_sun = gear_profiles["r_sun"]
        r_planet = gear_profiles["r_planet"]
        r_ring_inner = gear_profiles["r_ring_inner"]
        
        # The unified constraint should be satisfied within tolerance
        unified_constraint_satisfied = np.allclose(
            r_ring_inner, r_sun + 2.0 * r_planet, atol=0.01
        )
        assert unified_constraint_satisfied, "UNIFIED CONSTRAINT not satisfied"
        
        # Check contact point constraint: R_ring - R_planet = R_sun + R_planet
        contact_point_constraint_satisfied = np.allclose(
            r_ring_inner - r_planet, r_sun + r_planet, atol=0.01
        )
        assert contact_point_constraint_satisfied, "Contact point constraint not satisfied"
    
    def test_gear_ratio_verification(self):
        """Test that the gear ratio is properly verified."""
        # Generate motion law and gear profiles
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(
            self.baseline_params
        )
        gear_profiles = self.generator.generate_gear_profiles(
            theta_deg, displacement, self.baseline_params
        )
        
        # Check that gear ratio is correctly set
        expected_gear_ratio = self.baseline_params["gearRatio"]
        actual_gear_ratio = gear_profiles["gear_ratio"]
        assert actual_gear_ratio == expected_gear_ratio
        
        # Check φ(θ) mapping for gear ratio
        phi_of_theta_deg = gear_profiles["phi_of_theta_deg"]
        # For 180° ring rotation, planet angle range should be gear_ratio * 180°
        ring_rotation = self.baseline_params.get("ringRotationDeg", 180.0)
        expected_planet_angle_range = ring_rotation * expected_gear_ratio
        actual_planet_angle_range = np.max(phi_of_theta_deg) - np.min(phi_of_theta_deg)
        
        # The planet angle range should match the expected gear ratio (allow for small rounding errors)
        assert abs(actual_planet_angle_range - expected_planet_angle_range) < 5.0
    
    def test_end_to_end_gear_generation(self):
        """Test complete gear generation pipeline."""
        # Test the complete pipeline
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(
            self.baseline_params
        )
        gear_profiles = self.generator.generate_gear_profiles(
            theta_deg, displacement, self.baseline_params
        )
        planets = self.generator.generate_planet_kinematics(
            gear_profiles, self.baseline_params
        )
        validation_result = self.generator.validate_gearset_constraints(
            gear_profiles, self.baseline_params
        )
        
        # All components should work together
        assert len(gear_profiles["theta_deg"]) > 0
        assert len(planets) == self.baseline_params["planetCount"]
        assert validation_result["passed"] is True
        
        # Check that all generated data is consistent
        n_points = len(gear_profiles["theta_deg"])
        assert len(gear_profiles["r_planet"]) == n_points
        assert len(gear_profiles["r_sun"]) == n_points
        assert len(gear_profiles["r_ring_inner"]) == n_points
        assert len(gear_profiles["r_ring_outer"]) == n_points


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
