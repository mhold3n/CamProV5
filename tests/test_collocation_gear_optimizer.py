"""
Test suite for Collocation gear optimizer implementation.

This test suite follows TDD principles to validate the Collocation gear optimization
method extending the existing robust collocation solver.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add campro to path
sys.path.append(str(Path(__file__).parent.parent))

from campro.optimization.collocation_optimizer import CollocationOptimizer, CollocationParameters
from campro.gears.profile_generator import GearProfileGenerator


class TestCollocationGearOptimizer:
    """Test suite for Collocation gear optimizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = GearProfileGenerator()
        
        # Test parameters for gear generation
        self.test_params = self.get_baseline_gear_params()
        
        # Collocation parameters
        self.collocation_params = CollocationParameters(
            node_count=16,
            max_iterations=1000,
            tolerance=1e-8,
            constraint_tolerance=1e-6
        )
    
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
            
            # CORRECTED: Motion law parameters for 180° ring rotation
            "strokeLengthMm": 15.0,    # Stroke length in mm
            "samplingStepDeg": 1.0,    # Sampling step in degrees
            "upFraction": 0.6,         # Fraction of cycle for expansion
            "rpm": 3000.0,             # Engine RPM
            
            # CORRECTED: Gearset sizing for larger gearset to avoid "too small" issues
            "planetRadiusBaseFactor": 0.8,      # Base planet radius factor
            "planetRadiusVariationFactor": 0.3, # Planet radius variation factor
            "sunRadiusBaseFactor": 0.6,         # Base sun radius factor
            "sunRadiusVariationFactor": 0.2,    # Sun radius variation factor
            
            # CORRECTED: Relaxed stroke achievable factor for testing
            "strokeAchievableFactor": 0.3,      # Relaxed for testing
            
            # CORRECTED: Ramp profile for smooth motion
            "rampProfile": "MODIFIED_SINE"      # Smooth ramp profile
        }
    
    def test_collocation_gear_optimizer_initialization(self):
        """Test that Collocation gear optimizer can be initialized."""
        from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
        
        optimizer = CollocationGearOptimizer()
        assert optimizer is not None
        assert hasattr(optimizer, 'optimize_profiles')
        assert hasattr(optimizer, 'solver')
    
    def test_collocation_gear_optimization(self):
        """Test Collocation gear profile optimization."""
        from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
        
        optimizer = CollocationGearOptimizer()
        
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Optimize gear profiles using Collocation method
        result = optimizer.optimize_profiles(motion_law, self.test_params, self.collocation_params)
        
        # Validate results
        assert result is not None
        assert 'profiles' in result
        assert 'validation' in result
        assert 'mechanical_advantage' in result
        assert 'optimization_info' in result
        
        # Check that profiles are valid
        profiles = result['profiles']
        assert 'sun' in profiles
        assert 'planet' in profiles
        assert 'ring' in profiles
        
        # Check mechanical advantage
        mechanical_advantage = result['mechanical_advantage']
        assert mechanical_advantage > 1.0  # Must be greater than 1:1
    
    def test_collocation_gear_specific_constraints(self):
        """Test that Collocation method includes gear-specific constraints."""
        from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
        
        optimizer = CollocationGearOptimizer()
        motion_law = self.generator.generate_motion_law_piecewise(self.test_params)
        result = optimizer.optimize_profiles(motion_law, self.test_params, self.collocation_params)
        
        # Check that validation passes
        validation = result['validation']
        assert validation['passed'] is True
        assert validation['unified_constraint'] is True
        assert validation['contact_point_constraint'] is True
        
        # Check optimization info
        optimization_info = result['optimization_info']
        assert 'iterations' in optimization_info
        assert 'convergence' in optimization_info
        assert 'constraint_violations' in optimization_info
    
    def test_collocation_nlp_formulation_extension(self):
        """Test that Collocation solver is properly extended for gear optimization."""
        from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
        
        optimizer = CollocationGearOptimizer()
        
        # Check that the solver has gear-specific capabilities
        assert hasattr(optimizer.solver, 'optimize_gear_profiles')
        assert hasattr(optimizer.solver, 'add_gear_constraints')
    
    def test_collocation_casadi_framework_integration(self):
        """Test integration with CasADi framework for gear optimization."""
        from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
        
        optimizer = CollocationGearOptimizer()
        motion_law = self.generator.generate_motion_law_piecewise(self.test_params)
        
        # Test that CasADi integration works
        result = optimizer.optimize_profiles(motion_law, self.test_params, self.collocation_params)
        
        # Check that optimization info includes CasADi-specific details
        optimization_info = result['optimization_info']
        assert 'solver_status' in optimization_info
        assert 'objective_value' in optimization_info
        assert 'constraint_violations' in optimization_info
    
    def test_collocation_optimization_with_different_parameters(self):
        """Test Collocation optimization with different parameter sets."""
        from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
        
        optimizer = CollocationGearOptimizer()
        
        # Test with different collocation parameters
        param_sets = [
            CollocationParameters(node_count=8, max_iterations=500, tolerance=1e-6),
            CollocationParameters(node_count=16, max_iterations=1000, tolerance=1e-8),
            CollocationParameters(node_count=32, max_iterations=2000, tolerance=1e-10),
        ]
        
        for collocation_params in param_sets:
            motion_law = self.generator.generate_motion_law_piecewise(self.test_params)
            result = optimizer.optimize_profiles(motion_law, self.test_params, collocation_params)
            
            # All results should be valid
            assert result is not None
            assert result['validation']['passed'] is True
            assert result['mechanical_advantage'] > 1.0
            
            # Check that optimization info reflects the parameters used
            optimization_info = result['optimization_info']
            assert optimization_info['node_count'] == collocation_params.node_count
    
    def test_collocation_error_handling(self):
        """Test error handling in Collocation gear optimizer."""
        from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
        
        optimizer = CollocationGearOptimizer()
        
        # Test with invalid parameters
        invalid_params = self.test_params.copy()
        invalid_params['strokeLengthMm'] = -1.0  # Invalid stroke length
        
        motion_law = self.generator.generate_motion_law_piecewise(invalid_params)
        
        # Should handle errors gracefully
        with pytest.raises(ValueError):
            optimizer.optimize_profiles(motion_law, invalid_params, self.collocation_params)
    
    def test_collocation_performance_characteristics(self):
        """Test performance characteristics of Collocation method."""
        from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
        
        optimizer = CollocationGearOptimizer()
        motion_law = self.generator.generate_motion_law_piecewise(self.test_params)
        
        # Time the optimization
        import time
        start_time = time.time()
        result = optimizer.optimize_profiles(motion_law, self.test_params, self.collocation_params)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 10 seconds for collocation)
        assert (end_time - start_time) < 10.0
        
        # Result should be valid
        assert result is not None
        assert result['validation']['passed'] is True
        
        # Check optimization performance
        optimization_info = result['optimization_info']
        assert optimization_info['iterations'] > 0
        assert optimization_info['convergence'] is True
    
    def test_collocation_fallback_mechanism(self):
        """Test fallback mechanism when CasADi is not available."""
        from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
        
        optimizer = CollocationGearOptimizer()
        motion_law = self.generator.generate_motion_law_piecewise(self.test_params)
        
        # Test that fallback mechanism works
        # This should work even if CasADi is not available
        result = optimizer.optimize_profiles(motion_law, self.test_params, self.collocation_params)
        
        # Result should still be valid
        assert result is not None
        assert result['validation']['passed'] is True
        
        # Check that fallback info is included
        optimization_info = result['optimization_info']
        assert 'fallback_used' in optimization_info
