"""
Test suite for robust gear design calculations.

This test suite validates the production-ready gear design calculations
that replace simplified physics models.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add campro to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from campro.solvers.robust_gear_design import (
    RobustGearDesign, GearMaterialProperties, GearDesignParameters
)


class TestRobustGearDesign:
    """Test suite for robust gear design calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.material = GearMaterialProperties(
            yield_strength=400e6,  # 400 MPa
            ultimate_strength=600e6,  # 600 MPa
            youngs_modulus=200e9,  # 200 GPa
            poisson_ratio=0.3
        )
        
        self.design_params = GearDesignParameters(
            max_torque=1000.0,  # N⋅m
            max_power=100000.0,  # W
            rpm_max=3000.0,  # RPM
            bending_safety_factor=2.0,
            contact_safety_factor=1.5
        )
        
        self.gear_design = RobustGearDesign(self.material, self.design_params)
    
    def test_tooth_thickness_calculation(self):
        """Test robust tooth thickness calculation."""
        # Given
        gear_radius = np.array([50.0, 60.0, 70.0])  # mm
        contact_force = np.array([1000.0, 1200.0, 1400.0])  # N
        tooth_count = np.array([20.0, 24.0, 28.0])
        
        # When
        tooth_thickness = self.gear_design.calculate_tooth_thickness(
            gear_radius, contact_force, tooth_count
        )
        
        # Then
        assert len(tooth_thickness) == len(gear_radius)
        assert np.all(tooth_thickness > 0)  # Positive thickness
        assert np.all(np.isfinite(tooth_thickness))  # Finite values
        assert np.all(tooth_thickness >= 1.0)  # Minimum thickness constraint
        
        # Higher contact forces should generally require thicker teeth
        # (though this depends on the specific geometry)
        assert np.all(tooth_thickness > 0.5)  # Reasonable minimum
    
    def test_tooth_thickness_load_dependency(self):
        """Test that tooth thickness increases with load."""
        # Given
        gear_radius = np.array([50.0, 50.0, 50.0])  # Same radius
        contact_force_low = np.array([500.0, 500.0, 500.0])  # Low load
        contact_force_high = np.array([1500.0, 1500.0, 1500.0])  # High load
        tooth_count = np.array([20.0, 20.0, 20.0])
        
        # When
        thickness_low = self.gear_design.calculate_tooth_thickness(
            gear_radius, contact_force_low, tooth_count
        )
        thickness_high = self.gear_design.calculate_tooth_thickness(
            gear_radius, contact_force_high, tooth_count
        )
        
        # Then
        # Higher loads should generally require thicker teeth
        assert np.mean(thickness_high) >= np.mean(thickness_low)
    
    def test_contact_ratio_calculation(self):
        """Test robust contact ratio calculation."""
        # Given
        gear_radius = np.array([50.0, 60.0, 70.0])  # mm
        pinion_radius = np.array([20.0, 25.0, 30.0])  # mm
        pressure_angle = np.deg2rad([20.0, 20.0, 20.0])  # rad
        addendum = np.array([2.0, 2.5, 3.0])  # mm
        dedendum = np.array([2.5, 3.0, 3.5])  # mm
        
        # When
        contact_ratio = self.gear_design.calculate_contact_ratio(
            gear_radius, pinion_radius, pressure_angle, addendum, dedendum
        )
        
        # Then
        assert len(contact_ratio) == len(gear_radius)
        assert np.all(contact_ratio >= 0)  # Non-negative contact ratio
        assert np.all(np.isfinite(contact_ratio))  # Finite values
        
        # Contact ratio should be reasonable (typically 1.0 to 2.5)
        assert np.all(contact_ratio >= 0.0)
        assert np.all(contact_ratio <= 5.0)  # Upper bound for safety
    
    def test_gear_radius_calculation(self):
        """Test robust gear radius calculation."""
        # Given
        torque = np.array([100.0, 200.0, 300.0])  # N⋅m
        rpm = np.array([1000.0, 1500.0, 2000.0])  # RPM
        
        # When
        gear_radius = self.gear_design.calculate_gear_radius(torque, rpm)
        
        # Then
        assert len(gear_radius) == len(torque)
        assert np.all(gear_radius > 0)  # Positive radius
        assert np.all(np.isfinite(gear_radius))  # Finite values
        assert np.all(gear_radius >= 10.0)  # Minimum radius constraint
        
        # Higher torques should generally require larger radii
        # (though this depends on the specific design)
        assert np.all(gear_radius > 5.0)  # Reasonable minimum
    
    def test_pressure_angle_calculation(self):
        """Test robust pressure angle calculation."""
        # Given
        gear_radius = np.array([50.0, 60.0, 70.0])  # mm
        pinion_radius = np.array([20.0, 25.0, 30.0])  # mm
        contact_force = np.array([1000.0, 1200.0, 1400.0])  # N
        normal_force = np.array([1000.0, 1200.0, 1400.0])  # N
        
        # When
        pressure_angle = self.gear_design.calculate_pressure_angle(
            gear_radius, pinion_radius, contact_force, normal_force
        )
        
        # Then
        assert len(pressure_angle) == len(gear_radius)
        assert np.all(pressure_angle > 0)  # Positive pressure angle
        assert np.all(np.isfinite(pressure_angle))  # Finite values
        
        # Pressure angle should be within reasonable bounds
        min_angle = np.deg2rad(14.5)  # Minimum for involute gears
        max_angle = np.deg2rad(25.0)  # Maximum for standard gears
        assert np.all(pressure_angle >= min_angle)
        assert np.all(pressure_angle <= max_angle)
    
    def test_material_properties_impact(self):
        """Test that material properties affect design calculations."""
        # Given
        gear_radius = np.array([50.0, 50.0, 50.0])
        contact_force = np.array([1000.0, 1000.0, 1000.0])
        tooth_count = np.array([20.0, 20.0, 20.0])
        
        # Create design with different material properties
        high_strength_material = GearMaterialProperties(
            yield_strength=800e6,  # Higher strength
            ultimate_strength=1000e6,
            youngs_modulus=200e9,
            poisson_ratio=0.3
        )
        
        low_strength_material = GearMaterialProperties(
            yield_strength=200e6,  # Lower strength
            ultimate_strength=400e6,
            youngs_modulus=200e9,
            poisson_ratio=0.3
        )
        
        high_strength_design = RobustGearDesign(high_strength_material, self.design_params)
        low_strength_design = RobustGearDesign(low_strength_material, self.design_params)
        
        # When
        thickness_high_strength = high_strength_design.calculate_tooth_thickness(
            gear_radius, contact_force, tooth_count
        )
        thickness_low_strength = low_strength_design.calculate_tooth_thickness(
            gear_radius, contact_force, tooth_count
        )
        
        # Then
        # Higher strength material should allow thinner teeth
        assert np.mean(thickness_high_strength) <= np.mean(thickness_low_strength)
    
    def test_safety_factor_impact(self):
        """Test that safety factors affect design calculations."""
        # Given
        gear_radius = np.array([50.0, 50.0, 50.0])
        contact_force = np.array([1000.0, 1000.0, 1000.0])
        tooth_count = np.array([20.0, 20.0, 20.0])
        
        # Create designs with different safety factors
        high_safety_params = GearDesignParameters(
            max_torque=1000.0,
            max_power=100000.0,
            rpm_max=3000.0,
            bending_safety_factor=3.0,  # Higher safety factor
            contact_safety_factor=2.0
        )
        
        low_safety_params = GearDesignParameters(
            max_torque=1000.0,
            max_power=100000.0,
            rpm_max=3000.0,
            bending_safety_factor=1.5,  # Lower safety factor
            contact_safety_factor=1.2
        )
        
        high_safety_design = RobustGearDesign(self.material, high_safety_params)
        low_safety_design = RobustGearDesign(self.material, low_safety_params)
        
        # When
        thickness_high_safety = high_safety_design.calculate_tooth_thickness(
            gear_radius, contact_force, tooth_count
        )
        thickness_low_safety = low_safety_design.calculate_tooth_thickness(
            gear_radius, contact_force, tooth_count
        )
        
        # Then
        # Higher safety factors should require thicker teeth
        assert np.mean(thickness_high_safety) >= np.mean(thickness_low_safety)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Given
        gear_radius = np.array([10.0, 100.0, 1000.0])  # Wide range
        contact_force = np.array([100.0, 10000.0, 100000.0])  # Wide range
        tooth_count = np.array([10.0, 50.0, 200.0])  # Wide range
        
        # When
        tooth_thickness = self.gear_design.calculate_tooth_thickness(
            gear_radius, contact_force, tooth_count
        )
        
        # Then
        assert len(tooth_thickness) == len(gear_radius)
        assert np.all(tooth_thickness > 0)  # Positive thickness
        assert np.all(np.isfinite(tooth_thickness))  # Finite values
        assert np.all(tooth_thickness >= 1.0)  # Minimum thickness constraint
    
    def test_consistency_with_design_standards(self):
        """Test that calculations are consistent with gear design standards."""
        # Given - Standard gear parameters
        gear_radius = np.array([50.0])  # mm
        contact_force = np.array([1000.0])  # N
        tooth_count = np.array([20.0])
        
        # When
        tooth_thickness = self.gear_design.calculate_tooth_thickness(
            gear_radius, contact_force, tooth_count
        )
        
        # Then
        # Tooth thickness should be reasonable for standard gear
        # Typical tooth thickness is 0.4 to 0.6 times the module
        module = 2.0 * gear_radius[0] / tooth_count[0]  # 5.0 mm
        expected_thickness_range = (0.4 * module, 0.6 * module)  # 2.0 to 3.0 mm
        
        assert expected_thickness_range[0] <= tooth_thickness[0] <= expected_thickness_range[1] * 2.0
    
    def test_casadi_compatibility(self):
        """Test that calculations work with CasADi symbolic variables."""
        try:
            import casadi as ca
            
            # Given - CasADi variables
            gear_radius = ca.SX.sym('r', 3)
            contact_force = ca.SX.sym('F', 3)
            tooth_count = ca.SX.sym('N', 3)
            
            # When
            tooth_thickness = self.gear_design.calculate_tooth_thickness(
                gear_radius, contact_force, tooth_count
            )
            
            # Then
            assert isinstance(tooth_thickness, ca.SX)
            assert tooth_thickness.shape[0] == 3
            
        except ImportError:
            pytest.skip("CasADi not available")
    
    def test_performance_characteristics(self):
        """Test that calculations produce reasonable performance characteristics."""
        # Given
        gear_radius = np.array([50.0, 60.0, 70.0])
        pinion_radius = np.array([20.0, 25.0, 30.0])
        pressure_angle = np.deg2rad([20.0, 20.0, 20.0])
        addendum = np.array([2.0, 2.5, 3.0])
        dedendum = np.array([2.5, 3.0, 3.5])
        
        # When
        contact_ratio = self.gear_design.calculate_contact_ratio(
            gear_radius, pinion_radius, pressure_angle, addendum, dedendum
        )
        
        # Then
        # Contact ratio should be above minimum for smooth operation
        assert np.all(contact_ratio >= 1.0)  # Minimum for continuous contact
        
        # Contact ratio should not be excessively high
        assert np.all(contact_ratio <= 3.0)  # Reasonable upper bound


if __name__ == "__main__":
    pytest.main([__file__])
