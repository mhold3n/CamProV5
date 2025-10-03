"""
Test suite for Litvin gear optimizer implementation.

This test suite follows TDD principles to validate the Litvin gear optimization
method using the extracted robust gear profile generation logic.
"""

import pytest
import sys
from pathlib import Path

# Add campro to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from campro.gears.profile_generator import GearProfileGenerator
from campro.physics.force_transfer import ForceTransferAnalyzer


class TestLitvinOptimizer:
    """Test suite for Litvin gear optimizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = GearProfileGenerator()
        self.force_analyzer = ForceTransferAnalyzer()
        
        # Test parameters for gear generation
        self.test_params = self.get_baseline_gear_params()
    
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
    
    def test_litvin_optimizer_initialization(self):
        """Test that Litvin optimizer can be initialized."""
        # This test will pass once we implement the LitvinOptimizer class
        from campro.optimization.litvin_optimizer import LitvinGearOptimizer
        
        optimizer = LitvinGearOptimizer()
        assert optimizer is not None
        assert hasattr(optimizer, 'optimize_profiles')
    
    def test_litvin_gear_optimization(self):
        """Test Litvin gear profile optimization."""
        from campro.optimization.litvin_optimizer import LitvinGearOptimizer
        
        optimizer = LitvinGearOptimizer()
        
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Optimize gear profiles using Litvin method
        result = optimizer.optimize_profiles(motion_law, self.test_params)
        
        # Validate results
        assert result is not None
        assert 'profiles' in result
        assert 'validation' in result
        assert 'mechanical_advantage' in result
        
        # Check that profiles are valid
        profiles = result['profiles']
        assert 'sun' in profiles
        assert 'planet' in profiles
        assert 'ring' in profiles
        
        # Check mechanical advantage
        mechanical_advantage = result['mechanical_advantage']
        assert mechanical_advantage > 1.0  # Must be greater than 1:1
    
    def test_litvin_conjugacy_constraints(self):
        """Test that Litvin method satisfies conjugacy constraints."""
        from campro.optimization.litvin_optimizer import LitvinGearOptimizer
        
        optimizer = LitvinGearOptimizer()
        motion_law = self.generator.generate_motion_law_piecewise(self.test_params)
        result = optimizer.optimize_profiles(motion_law, self.test_params)
        
        # Check that validation passes
        validation = result['validation']
        assert validation['passed'] is True
        assert validation['unified_constraint'] is True
        assert validation['contact_point_constraint'] is True
    
    def test_litvin_mechanical_advantage_calculation(self):
        """Test mechanical advantage calculation for Litvin method."""
        from campro.optimization.litvin_optimizer import LitvinGearOptimizer
        
        optimizer = LitvinGearOptimizer()
        motion_law = self.generator.generate_motion_law_piecewise(self.test_params)
        result = optimizer.optimize_profiles(motion_law, self.test_params)
        
        # Check mechanical advantage calculation
        mechanical_advantage = result['mechanical_advantage']
        assert isinstance(mechanical_advantage, (int, float))
        assert mechanical_advantage > 1.0
        assert mechanical_advantage < 10.0  # Reasonable upper bound
    
    def test_litvin_optimization_with_different_parameters(self):
        """Test Litvin optimization with different parameter sets."""
        from campro.optimization.litvin_optimizer import LitvinGearOptimizer
        
        optimizer = LitvinGearOptimizer()
        
        # Test with different parameter sets
        param_sets = [
            self.get_baseline_gear_params(),
            # Add more parameter sets as needed
        ]
        
        for params in param_sets:
            motion_law = self.generator.generate_motion_law_piecewise(params)
            result = optimizer.optimize_profiles(motion_law, params)
            
            # All results should be valid
            assert result is not None
            assert result['validation']['passed'] is True
            assert result['mechanical_advantage'] > 1.0
    
    def test_litvin_error_handling(self):
        """Test error handling in Litvin optimizer."""
        from campro.optimization.litvin_optimizer import LitvinGearOptimizer
        
        optimizer = LitvinGearOptimizer()
        
        # Test with invalid parameters
        invalid_params = self.test_params.copy()
        invalid_params['strokeLengthMm'] = -1.0  # Invalid stroke length
        
        motion_law = self.generator.generate_motion_law_piecewise(invalid_params)
        
        # Should handle errors gracefully
        with pytest.raises(ValueError):
            optimizer.optimize_profiles(motion_law, invalid_params)
    
    def test_litvin_performance_characteristics(self):
        """Test performance characteristics of Litvin method."""
        from campro.optimization.litvin_optimizer import LitvinGearOptimizer
        
        optimizer = LitvinGearOptimizer()
        motion_law = self.generator.generate_motion_law_piecewise(self.test_params)
        
        # Time the optimization
        import time
        start_time = time.time()
        result = optimizer.optimize_profiles(motion_law, self.test_params)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 5 seconds)
        assert (end_time - start_time) < 5.0
        
        # Result should be valid
        assert result is not None
        assert result['validation']['passed'] is True
