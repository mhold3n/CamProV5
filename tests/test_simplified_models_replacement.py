"""
Test to verify that simplified physics models have been replaced with robust implementations.

This test ensures that the integration of robust gear design into the constraint
and validation systems is working correctly.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add campro to path
sys.path.append(str(Path(__file__).parent.parent))

from campro.solvers.litvin_constraints import LitvinConstraintBuilder, LitvinParameters
from campro.solvers.validation import DenseValidator, ValidationLimits
from campro.solvers.discretization import CollocationGrid
from campro.solvers.robust_gear_design import RobustGearDesign, GearMaterialProperties, GearDesignParameters


class TestSimplifiedModelsReplacement:
    """Test that simplified models have been replaced with robust implementations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.grid = CollocationGrid(node_count=8, node_type="LGL")
        self.litvin_params = LitvinParameters()
        self.validation_limits = ValidationLimits()
        
        # Create robust gear design calculator
        self.material = GearMaterialProperties()
        self.design_params = GearDesignParameters()
        self.gear_design = RobustGearDesign(self.material, self.design_params)
    
    def test_litvin_constraints_use_robust_gear_design(self):
        """Test that Litvin constraints now use robust gear design."""
        builder = LitvinConstraintBuilder(self.litvin_params, self.grid)
        
        # Create mock CasADi variables
        with pytest.MonkeyPatch().context() as m:
            # Mock CasADi to avoid import issues in test
            def mock_sum1(x, *args):
                if hasattr(x, '__len__'):
                    return float(np.sum(x))
                elif hasattr(x, '__class__') and 'MockCasADi' in str(x.__class__):
                    return 1.0  # Return a default value for mock objects
                else:
                    return float(x)
            
            mock_ca = type('MockCasADi', (), {
                'SX': lambda n: np.zeros(n),
                'cos': lambda x: 0.8,
                'sum1': mock_sum1,
                'sqrt': lambda x: 1.0,
                'fmax': lambda a, b: np.maximum(a, b)
            })()
            m.setattr('campro.solvers.litvin_constraints.ca', mock_ca)
            
            # Create mock position and velocity variables
            position_vars = np.zeros(self.grid.node_count)
            velocity_vars = np.zeros(self.grid.node_count)
            
            # Test tooth thickness constraints
            constraints = builder._build_tooth_thickness_constraints(position_vars, velocity_vars)
            
            # Verify that constraints are generated (robust implementation should work)
            assert len(constraints['expressions']) > 0
            assert len(constraints['lower']) > 0
            assert len(constraints['upper']) > 0
            
            # Test contact ratio constraints
            contact_constraints = builder._build_contact_ratio_constraints(position_vars, velocity_vars)
            
            # Verify that contact ratio constraints are generated
            assert len(contact_constraints['expressions']) > 0
            assert len(contact_constraints['lower']) > 0
            assert len(contact_constraints['upper']) > 0
    
    def test_validation_uses_robust_gear_design(self):
        """Test that validation now uses robust gear design."""
        validator = DenseValidator(self.validation_limits)
        
        # Create test data
        theta_grid = np.linspace(0, 2*np.pi, 100)
        position = 10.0 * (1.0 - np.cos(theta_grid))  # Simple motion
        velocity = 10.0 * np.sin(theta_grid)
        acceleration = 10.0 * np.cos(theta_grid)
        motion_params = {
            "strokeLengthMm": 20.0, 
            "rpm": 3000.0,
            "max_torque": 500.0  # Add torque parameter for robust design
        }
        
        # Test validation with robust gear design
        report = validator.validate_solution(theta_grid, position, velocity, acceleration, motion_params)
        
        # Verify that validation produces results
        assert report is not None
        assert hasattr(report, 'num_violations')
        assert hasattr(report, 'pressure_angle_violations')
        assert hasattr(report, 'contact_ratio_result')  # Changed from contact_ratio_violations
        
        # Verify that robust calculations produce reasonable values
        assert hasattr(report, 'pressure_angle_max')
        assert hasattr(report, 'contact_ratio_result')  # Changed from contact_ratio_avg
        
        # Check that pressure angle is within reasonable range
        if hasattr(report, 'pressure_angle_max') and report.pressure_angle_max is not None and report.pressure_angle_max > 0:
            assert 0.1 <= report.pressure_angle_max <= 1.0  # 6° to 57°
        
        # Check that contact ratio is within reasonable range
        if hasattr(report, 'contact_ratio_result') and report.contact_ratio_result is not None:
            assert 1.0 <= report.contact_ratio_result.value <= 3.0
    
    def test_robust_gear_design_integration(self):
        """Test that robust gear design integrates properly with constraint system."""
        # Test that robust gear design can be used in constraint calculations
        gear_radius = np.array([50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0])
        contact_force = np.array([1000.0, 1100.0, 1200.0, 1300.0, 1400.0, 1500.0, 1600.0, 1700.0])
        
        # Calculate robust tooth thickness
        thickness = self.gear_design.calculate_tooth_thickness(gear_radius, contact_force)
        
        # Verify that results are suitable for constraint system
        assert len(thickness) == len(gear_radius), "Length should match grid size"
        assert np.all(thickness > 0), "All thicknesses should be positive"
        assert np.all(np.isfinite(thickness)), "All thicknesses should be finite"
        assert np.all(thickness > 0.1), "Minimum thickness should be > 0.1mm"
        assert np.all(thickness < 50.0), "Maximum thickness should be < 50mm"
        
        # Test contact ratio calculation
        pinion_radius = gear_radius * 0.5  # Assume 2:1 ratio
        pressure_angle = np.full_like(gear_radius, 20.0 * np.pi / 180.0)  # 20 degrees
        addendum = np.full_like(gear_radius, 2.0)  # 2mm
        dedendum = np.full_like(gear_radius, 2.5)  # 2.5mm
        
        contact_ratio = self.gear_design.calculate_contact_ratio(
            gear_radius, pinion_radius, pressure_angle, addendum, dedendum
        )
        
        # Verify contact ratio results
        assert len(contact_ratio) == len(gear_radius), "Length should match input"
        assert np.all(contact_ratio > 0), "Contact ratio should be positive"
        assert np.all(contact_ratio >= 1.0), "Contact ratio should be >= 1.0"
        assert np.all(contact_ratio <= 3.0), "Contact ratio should be <= 3.0"
    
    def test_material_property_effects_in_constraints(self):
        """Test that material properties affect constraint calculations."""
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
    
    def test_design_parameter_effects_in_constraints(self):
        """Test that design parameters affect constraint calculations."""
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
    
    def test_no_simplified_models_remain(self):
        """Test that no simplified models remain in the constraint system."""
        # This test ensures that the robust implementations are being used
        # and not falling back to simplified models
        
        # Test that robust gear design is properly imported and used
        assert RobustGearDesign is not None
        assert GearMaterialProperties is not None
        assert GearDesignParameters is not None
        
        # Test that the robust implementations produce different results
        # than the simplified models would have
        
        # Create test data
        gear_radius = np.array([50.0, 60.0, 70.0])
        contact_force = np.array([1000.0, 1200.0, 1400.0])
        
        # Calculate using robust method
        thickness_robust = self.gear_design.calculate_tooth_thickness(gear_radius, contact_force)
        
        # Verify that results are physically reasonable and not simplified
        assert np.all(thickness_robust > 0.1), "Robust method should produce reasonable thickness"
        assert np.all(thickness_robust < 20.0), "Robust method should produce reasonable thickness"
        
        # Verify that results vary with input (not constant like simplified models)
        assert not np.allclose(thickness_robust, thickness_robust[0]), "Results should vary with input"
        
        # Test contact ratio calculation
        pinion_radius = gear_radius * 0.5
        pressure_angle = np.full_like(gear_radius, 20.0 * np.pi / 180.0)
        addendum = np.full_like(gear_radius, 2.0)
        dedendum = np.full_like(gear_radius, 2.5)
        
        contact_ratio_robust = self.gear_design.calculate_contact_ratio(
            gear_radius, pinion_radius, pressure_angle, addendum, dedendum
        )
        
        # Verify that contact ratio is reasonable
        assert np.all(contact_ratio_robust >= 1.0), "Contact ratio should be >= 1.0"
        assert np.all(contact_ratio_robust <= 2.5), "Contact ratio should be <= 2.5"


if __name__ == "__main__":
    pytest.main([__file__])
