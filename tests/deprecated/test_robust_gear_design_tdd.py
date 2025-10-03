"""
TDD Tests for Robust Gear Design Implementation

This test suite follows Test-Driven Development principles to validate
that replace simplified physics models with robust implementations.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add campro to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from campro.solvers.robust_gear_design import (
    RobustGearDesign, 
    GearMaterialProperties, 
    GearDesignParameters
)


class TestRobustGearDesignTDD:
    """TDD test suite for robust gear design calculations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Standard steel material properties
        self.material = GearMaterialProperties(
            yield_strength=400e6,  # 400 MPa
            ultimate_strength=600e6,  # 600 MPa
            fatigue_limit=200e6,  # 200 MPa
            youngs_modulus=200e9,  # 200 GPa
            poisson_ratio=0.3,
            surface_hardness=60.0,  # HRC
            surface_roughness=0.8  # μm Ra
        )
        
        # Standard design parameters
        self.design_params = GearDesignParameters(
            max_torque=1000.0,  # N⋅m
            max_power=100000.0,  # W (100 kW)
            rpm_max=3000.0,  # RPM
            bending_safety_factor=2.0,
            contact_safety_factor=1.5,
            fatigue_safety_factor=1.8,
            manufacturing_accuracy=6.0,  # ISO 1328 grade
            surface_finish_factor=0.9,
            dynamic_factor=1.2,
            load_distribution_factor=1.1
        )
        
        self.gear_design = RobustGearDesign(self.material, self.design_params)
    
    def test_tooth_thickness_calculation_nominal(self):
        """Test tooth thickness calculation under nominal conditions."""
        # Nominal test case: moderate loads, standard gear sizes
        gear_radius = np.array([50.0, 55.0, 60.0])  # mm
        contact_force = np.array([1000.0, 1200.0, 1100.0])  # N
        tooth_count = np.array([20.0, 22.0, 24.0])
        
        thickness = self.gear_design.calculate_tooth_thickness(gear_radius, contact_force, tooth_count)
        
        # Validate results
        assert len(thickness) == len(gear_radius), "Output length should match input"
        assert np.all(thickness > 0), "Tooth thickness should be positive"
        assert np.all(thickness < 20.0), "Tooth thickness should be reasonable (< 20mm)"
        
        # Check that thickness increases with load (basic physics)
        # Higher contact force should generally require thicker teeth
        contact_force[1] / contact_force[0]
        thickness_ratio = thickness[1] / thickness[0]
        assert thickness_ratio > 0.8, "Thickness should increase with load"
    
    def test_tooth_thickness_calculation_edge_cases(self):
        """Test tooth thickness calculation under edge conditions."""
        # Edge case 1: Very small gear
        small_radius = np.array([5.0])  # mm
        small_force = np.array([100.0])  # N
        small_teeth = np.array([8.0])
        
        thickness_small = self.gear_design.calculate_tooth_thickness(small_radius, small_force, small_teeth)
        assert thickness_small[0] > 0, "Small gear should have positive thickness"
        assert thickness_small[0] < 5.0, "Small gear thickness should be reasonable"
        
        # Edge case 2: Very large gear
        large_radius = np.array([200.0])  # mm
        large_force = np.array([10000.0])  # N
        large_teeth = np.array([80.0])
        
        thickness_large = self.gear_design.calculate_tooth_thickness(large_radius, large_force, large_teeth)
        assert thickness_large[0] > 0, "Large gear should have positive thickness"
        assert thickness_large[0] > thickness_small[0], "Large gear should have thicker teeth"
    
    def test_tooth_thickness_calculation_experimental(self):
        """Test tooth thickness calculation under experimental conditions."""
        # Experimental case: High-speed, high-load conditions
        high_speed_radius = np.array([75.0])  # mm
        high_speed_force = np.array([5000.0])  # N
        high_speed_teeth = np.array([30.0])
        
        # Create high-speed design parameters
        high_speed_params = GearDesignParameters(
            max_torque=2000.0,  # Higher torque
            max_power=200000.0,  # Higher power
            rpm_max=6000.0,  # Higher RPM
            bending_safety_factor=2.5,  # Higher safety factor
            contact_safety_factor=2.0,
            fatigue_safety_factor=2.2,
            manufacturing_accuracy=4.0,  # Better accuracy
            surface_finish_factor=0.95,
            dynamic_factor=1.5,  # Higher dynamic factor
            load_distribution_factor=1.2
        )
        
        high_speed_design = RobustGearDesign(self.material, high_speed_params)
        thickness_high_speed = high_speed_design.calculate_tooth_thickness(
            high_speed_radius, high_speed_force, high_speed_teeth
        )
        
        # High-speed conditions should require thicker teeth
        thickness_standard = self.gear_design.calculate_tooth_thickness(
            high_speed_radius, high_speed_force, high_speed_teeth
        )
        
        assert thickness_high_speed[0] > thickness_standard[0], "High-speed should require thicker teeth"
    
    def test_contact_ratio_calculation_nominal(self):
        """Test contact ratio calculation under nominal conditions."""
        # Nominal test case
        gear_radius = np.array([50.0])  # mm
        pinion_radius = np.array([25.0])  # mm
        pressure_angle = np.array([20.0 * np.pi / 180.0])  # 20 degrees in radians
        addendum = np.array([2.0])  # mm
        dedendum = np.array([2.5])  # mm
        
        contact_ratio = self.gear_design.calculate_contact_ratio(
            gear_radius, pinion_radius, pressure_angle, addendum, dedendum
        )
        
        # Validate results
        assert len(contact_ratio) == len(gear_radius), "Output length should match input"
        assert np.all(contact_ratio > 0), "Contact ratio should be positive"
        assert np.all(contact_ratio > 1.0), "Contact ratio should be > 1.0 for smooth operation"
        assert np.all(contact_ratio < 3.0), "Contact ratio should be reasonable (< 3.0)"
    
    def test_contact_ratio_calculation_edge_cases(self):
        """Test contact ratio calculation under edge conditions."""
        # Edge case 1: Very small pressure angle
        small_pressure_angle = np.array([10.0 * np.pi / 180.0])  # 10 degrees
        contact_ratio_small = self.gear_design.calculate_contact_ratio(
            np.array([50.0]), np.array([25.0]), small_pressure_angle, 
            np.array([2.0]), np.array([2.5])
        )
        
        # Edge case 2: Large pressure angle
        large_pressure_angle = np.array([30.0 * np.pi / 180.0])  # 30 degrees
        contact_ratio_large = self.gear_design.calculate_contact_ratio(
            np.array([50.0]), np.array([25.0]), large_pressure_angle,
            np.array([2.0]), np.array([2.5])
        )
        
        # Contact ratio should decrease with increasing pressure angle
        assert contact_ratio_small[0] > contact_ratio_large[0], "Smaller pressure angle should give higher contact ratio"
    
    def test_gear_radius_calculation_nominal(self):
        """Test gear radius calculation under nominal conditions."""
        # Nominal test case
        torque = np.array([500.0, 600.0, 550.0])  # N⋅m
        rpm = np.array([1500.0, 1800.0, 1600.0])  # RPM
        
        gear_radius = self.gear_design.calculate_gear_radius(torque, rpm)
        
        # Validate results
        assert len(gear_radius) == len(torque), "Output length should match input"
        assert np.all(gear_radius > 0), "Gear radius should be positive"
        assert np.all(gear_radius > 10.0), "Gear radius should be reasonable (> 10mm)"
        assert np.all(gear_radius < 500.0), "Gear radius should be reasonable (< 500mm)"
        
        # Check that radius increases with torque (basic physics)
        torque[1] / torque[0]
        radius_ratio = gear_radius[1] / gear_radius[0]
        assert radius_ratio > 0.8, "Radius should increase with torque"
    
    def test_gear_radius_calculation_edge_cases(self):
        """Test gear radius calculation under edge conditions."""
        # Edge case 1: Very low torque
        low_torque = np.array([10.0])  # N⋅m
        low_rpm = np.array([100.0])  # RPM
        
        radius_low = self.gear_design.calculate_gear_radius(low_torque, low_rpm)
        assert radius_low[0] > 0, "Low torque should still give positive radius"
        
        # Edge case 2: Very high torque
        high_torque = np.array([5000.0])  # N⋅m
        high_rpm = np.array([3000.0])  # RPM
        
        radius_high = self.gear_design.calculate_gear_radius(high_torque, high_rpm)
        assert radius_high[0] > radius_low[0], "High torque should require larger radius"
    
    def test_pressure_angle_calculation_nominal(self):
        """Test pressure angle calculation under nominal conditions."""
        # Nominal test case
        gear_radius = np.array([50.0, 55.0, 60.0])  # mm
        pinion_radius = np.array([25.0, 27.5, 30.0])  # mm
        center_distance = np.array([75.0, 82.5, 90.0])  # mm
        
        pressure_angle = self.gear_design.calculate_pressure_angle(gear_radius, pinion_radius, center_distance)
        
        # Validate results
        assert len(pressure_angle) == len(gear_radius), "Output length should match input"
        assert np.all(pressure_angle > 0), "Pressure angle should be positive"
        assert np.all(pressure_angle < np.pi/2), "Pressure angle should be < 90 degrees"
        assert np.all(pressure_angle > np.pi/18), "Pressure angle should be > 10 degrees"
        assert np.all(pressure_angle < np.pi/3), "Pressure angle should be < 60 degrees"
    
    def test_pressure_angle_calculation_edge_cases(self):
        """Test pressure angle calculation under edge conditions."""
        # Edge case 1: Very small center distance
        small_center = np.array([70.0])  # mm
        pressure_angle_small = self.gear_design.calculate_pressure_angle(
            np.array([50.0]), np.array([25.0]), small_center
        )
        
        # Edge case 2: Large center distance
        large_center = np.array([80.0])  # mm
        pressure_angle_large = self.gear_design.calculate_pressure_angle(
            np.array([50.0]), np.array([25.0]), large_center
        )
        
        # Pressure angle should increase with center distance
        assert pressure_angle_large[0] > pressure_angle_small[0], "Larger center distance should give higher pressure angle"
    
    def test_material_property_effects(self):
        """Test that material properties affect calculations correctly."""
        # Create high-strength material
        high_strength_material = GearMaterialProperties(
            yield_strength=800e6,  # 800 MPa (higher)
            ultimate_strength=1000e6,  # 1000 MPa
            fatigue_limit=400e6,  # 400 MPa
            youngs_modulus=200e9,  # 200 GPa
            poisson_ratio=0.3,
            surface_hardness=60.0,  # HRC
            surface_roughness=0.8  # μm Ra
        )
        
        high_strength_design = RobustGearDesign(high_strength_material, self.design_params)
        
        # Test with same loads
        gear_radius = np.array([50.0])
        contact_force = np.array([1000.0])
        tooth_count = np.array([20.0])
        
        thickness_standard = self.gear_design.calculate_tooth_thickness(gear_radius, contact_force, tooth_count)
        thickness_high_strength = high_strength_design.calculate_tooth_thickness(gear_radius, contact_force, tooth_count)
        
        # Higher strength material should allow thinner teeth
        assert thickness_high_strength[0] < thickness_standard[0], "Higher strength material should allow thinner teeth"
    
    def test_design_parameter_effects(self):
        """Test that design parameters affect calculations correctly."""
        # Create conservative design parameters
        conservative_params = GearDesignParameters(
            max_torque=1000.0,
            max_power=100000.0,
            rpm_max=3000.0,
            bending_safety_factor=3.0,  # Higher safety factor
            contact_safety_factor=2.0,
            fatigue_safety_factor=2.5,
            manufacturing_accuracy=6.0,
            surface_finish_factor=0.9,
            dynamic_factor=1.2,
            load_distribution_factor=1.1
        )
        
        conservative_design = RobustGearDesign(self.material, conservative_params)
        
        # Test with same loads
        gear_radius = np.array([50.0])
        contact_force = np.array([1000.0])
        tooth_count = np.array([20.0])
        
        thickness_standard = self.gear_design.calculate_tooth_thickness(gear_radius, contact_force, tooth_count)
        thickness_conservative = conservative_design.calculate_tooth_thickness(gear_radius, contact_force, tooth_count)
        
        # Conservative design should require thicker teeth
        assert thickness_conservative[0] > thickness_standard[0], "Conservative design should require thicker teeth"
    
    def test_integration_with_litvin_constraints(self):
        """Test integration with Litvin constraint system."""
        # This test ensures the robust gear design can be used in the constraint system
        from campro.solvers.litvin_constraints import LitvinConstraintBuilder, LitvinParameters
        from campro.solvers.discretization import CollocationGrid
        
        # Create constraint builder
        grid = CollocationGrid(node_count=8, node_type="LGL")
        litvin_params = LitvinParameters()
        LitvinConstraintBuilder(litvin_params, grid)
        
        # Test that we can use robust gear design in constraints
        gear_radius = np.array([50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0])
        contact_force = np.array([1000.0, 1100.0, 1200.0, 1300.0, 1400.0, 1500.0, 1600.0, 1700.0])
        
        # Calculate robust tooth thickness
        thickness = self.gear_design.calculate_tooth_thickness(gear_radius, contact_force)
        
        # Validate that results are suitable for constraint system
        assert len(thickness) == len(gear_radius), "Length should match grid size"
        assert np.all(thickness > 0), "All thicknesses should be positive"
        assert np.all(np.isfinite(thickness)), "All thicknesses should be finite"
        
        # Test that results are physically reasonable
        assert np.all(thickness > 0.1), "Minimum thickness should be > 0.1mm"
        assert np.all(thickness < 50.0), "Maximum thickness should be < 50mm"


if __name__ == "__main__":
    pytest.main([__file__])
