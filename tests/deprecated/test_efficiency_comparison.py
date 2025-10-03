"""
Test suite for efficiency comparison logic between Litvin and Collocation methods.

This test suite follows TDD principles to validate the efficiency comparison
and optimal solution selection logic.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add campro to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from campro.gears.profile_generator import GearProfileGenerator
from campro.physics.force_transfer import ForceTransferAnalyzer


class TestEfficiencyComparison:
    """Test suite for efficiency comparison logic."""
    
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
    
    def test_efficiency_comparison_initialization(self):
        """Test that efficiency comparison can be initialized."""
        from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
        
        optimizer = EfficiencyOptimizer()
        assert optimizer is not None
        assert hasattr(optimizer, 'compare_solutions')
        assert hasattr(optimizer, 'force_analyzer')
    
    def test_efficiency_comparison_basic_functionality(self):
        """Test basic efficiency comparison functionality."""
        from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
        
        optimizer = EfficiencyOptimizer()
        
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create mock solutions for comparison
        litvin_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        collocation_profiles = {
            'sun': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
            'planet': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
            'ring': np.array([[0, 0], [1, 1.1], [2, 2.1]])
        }
        
        # Compare solutions
        result = optimizer.compare_solutions(
            litvin_profiles, collocation_profiles, motion_law, self.test_params
        )
        
        # Validate results
        assert result is not None
        assert 'optimal_solution' in result
        assert 'efficiency_analysis' in result
        assert 'comparison_metrics' in result
        
        # Check that optimal solution is selected
        optimal_solution = result['optimal_solution']
        assert optimal_solution in ['litvin', 'collocation']
        
        # Check efficiency analysis
        efficiency_analysis = result['efficiency_analysis']
        assert 'litvin_efficiency' in efficiency_analysis
        assert 'collocation_efficiency' in efficiency_analysis
        assert 'efficiency_difference' in efficiency_analysis
    
    def test_efficiency_calculation_accuracy(self):
        """Test that efficiency calculations are accurate."""
        from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
        
        optimizer = EfficiencyOptimizer()
        
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test profiles
        litvin_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        collocation_profiles = {
            'sun': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
            'planet': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
            'ring': np.array([[0, 0], [1, 1.1], [2, 2.1]])
        }
        
        # Compare solutions
        result = optimizer.compare_solutions(
            litvin_profiles, collocation_profiles, motion_law, self.test_params
        )
        
        # Check efficiency analysis
        efficiency_analysis = result['efficiency_analysis']
        litvin_efficiency = efficiency_analysis['litvin_efficiency']
        collocation_efficiency = efficiency_analysis['collocation_efficiency']
        
        # Efficiencies should be between 0 and 1
        assert 0.0 <= litvin_efficiency <= 1.0
        assert 0.0 <= collocation_efficiency <= 1.0
        
        # Efficiency difference should be calculated correctly
        efficiency_difference = efficiency_analysis['efficiency_difference']
        expected_difference = abs(litvin_efficiency - collocation_efficiency)
        assert abs(efficiency_difference - expected_difference) < 1e-6
    
    def test_optimal_solution_selection_logic(self):
        """Test that optimal solution selection logic works correctly."""
        from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
        
        optimizer = EfficiencyOptimizer()
        
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create profiles where one is clearly more efficient
        high_efficiency_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        low_efficiency_profiles = {
            'sun': np.array([[0, 0], [1, 0.5], [2, 1]]),
            'planet': np.array([[0, 0], [1, 0.5], [2, 1]]),
            'ring': np.array([[0, 0], [1, 0.5], [2, 1]])
        }
        
        # Test with high efficiency as Litvin
        result1 = optimizer.compare_solutions(
            high_efficiency_profiles, low_efficiency_profiles, motion_law, self.test_params
        )
        assert result1['optimal_solution'] == 'litvin'
        
        # Test with high efficiency as Collocation
        result2 = optimizer.compare_solutions(
            low_efficiency_profiles, high_efficiency_profiles, motion_law, self.test_params
        )
        assert result2['optimal_solution'] == 'collocation'
    
    def test_efficiency_metrics_calculation(self):
        """Test that all efficiency metrics are calculated correctly."""
        from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
        
        optimizer = EfficiencyOptimizer()
        
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test profiles
        litvin_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        collocation_profiles = {
            'sun': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
            'planet': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
            'ring': np.array([[0, 0], [1, 1.1], [2, 2.1]])
        }
        
        # Compare solutions
        result = optimizer.compare_solutions(
            litvin_profiles, collocation_profiles, motion_law, self.test_params
        )
        
        # Check comparison metrics
        comparison_metrics = result['comparison_metrics']
        assert 'hertzian_losses' in comparison_metrics
        assert 'friction_losses' in comparison_metrics
        assert 'deformation_losses' in comparison_metrics
        assert 'windage_losses' in comparison_metrics
        assert 'total_losses' in comparison_metrics
        
        # Check that all metrics are calculated
        for metric in ['hertzian_losses', 'friction_losses', 'deformation_losses', 'windage_losses']:
            assert 'litvin' in comparison_metrics[metric]
            assert 'collocation' in comparison_metrics[metric]
            assert 'difference' in comparison_metrics[metric]
    
    def test_efficiency_comparison_with_different_parameters(self):
        """Test efficiency comparison with different parameter sets."""
        from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
        
        optimizer = EfficiencyOptimizer()
        
        # Test with different parameter sets
        param_sets = [
            self.get_baseline_gear_params(),
            # Add more parameter sets as needed
        ]
        
        for params in param_sets:
            motion_law = self.generator.generate_motion_law_piecewise(params)
            
            # Create test profiles
            litvin_profiles = {
                'sun': np.array([[0, 0], [1, 1], [2, 2]]),
                'planet': np.array([[0, 0], [1, 1], [2, 2]]),
                'ring': np.array([[0, 0], [1, 1], [2, 2]])
            }
            
            collocation_profiles = {
                'sun': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
                'planet': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
                'ring': np.array([[0, 0], [1, 1.1], [2, 2.1]])
            }
            
            # Compare solutions
            result = optimizer.compare_solutions(
                litvin_profiles, collocation_profiles, motion_law, params
            )
            
            # All results should be valid
            assert result is not None
            assert 'optimal_solution' in result
            assert 'efficiency_analysis' in result
            assert 'comparison_metrics' in result
    
    def test_efficiency_comparison_error_handling(self):
        """Test error handling in efficiency comparison."""
        from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
        
        optimizer = EfficiencyOptimizer()
        
        # Test with invalid profiles
        invalid_profiles = {
            'sun': np.array([]),  # Empty array
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        valid_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        motion_law = self.generator.generate_motion_law_piecewise(self.test_params)
        
        # Should handle errors gracefully
        with pytest.raises(ValueError):
            optimizer.compare_solutions(
                invalid_profiles, valid_profiles, motion_law, self.test_params
            )
    
    def test_efficiency_comparison_performance(self):
        """Test performance of efficiency comparison."""
        from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
        
        optimizer = EfficiencyOptimizer()
        
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test profiles
        litvin_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        collocation_profiles = {
            'sun': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
            'planet': np.array([[0, 0], [1, 1.1], [2, 2.1]]),
            'ring': np.array([[0, 0], [1, 1.1], [2, 2.1]])
        }
        
        # Time the comparison
        import time
        start_time = time.time()
        result = optimizer.compare_solutions(
            litvin_profiles, collocation_profiles, motion_law, self.test_params
        )
        end_time = time.time()
        
        # Should complete in reasonable time (less than 2 seconds)
        assert (end_time - start_time) < 2.0
        
        # Result should be valid
        assert result is not None
        assert 'optimal_solution' in result
