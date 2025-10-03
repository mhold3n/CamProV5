"""
Test suite for efficiency optimizer implementation.

This test suite follows TDD principles to validate the efficiency optimization
logic for comparing and selecting optimal gear solutions.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add campro to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
from campro.physics.force_transfer import ForceTransferAnalyzer
from campro.gears.profile_generator import GearProfileGenerator


class TestEfficiencyOptimizer:
    """Test suite for efficiency optimizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = EfficiencyOptimizer()
        self.force_analyzer = ForceTransferAnalyzer()
        self.generator = GearProfileGenerator()
        
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
    
    def test_efficiency_optimizer_initialization(self):
        """Test that efficiency optimizer can be initialized."""
        assert self.optimizer is not None
        assert hasattr(self.optimizer, 'compare_solutions')
        assert hasattr(self.optimizer, 'force_analyzer')
        assert hasattr(self.optimizer, '_calculate_solution_efficiency')
        assert hasattr(self.optimizer, '_select_optimal_solution')
    
    def test_efficiency_optimizer_compare_solutions(self):
        """Test the main compare_solutions method."""
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
        result = self.optimizer.compare_solutions(
            litvin_profiles, collocation_profiles, motion_law, self.test_params
        )
        
        # Validate results
        assert result is not None
        assert 'optimal_solution' in result
        assert 'efficiency_analysis' in result
        assert 'comparison_metrics' in result
        assert 'recommendation' in result
        
        # Check optimal solution
        optimal_solution = result['optimal_solution']
        assert optimal_solution in ['litvin', 'collocation']
        
        # Check efficiency analysis
        efficiency_analysis = result['efficiency_analysis']
        assert 'litvin_efficiency' in efficiency_analysis
        assert 'collocation_efficiency' in efficiency_analysis
        assert 'efficiency_difference' in efficiency_analysis
        assert 'optimal_method' in efficiency_analysis
        assert 'efficiency_improvement' in efficiency_analysis
    
    def test_efficiency_optimizer_select_optimal_solution(self):
        """Test optimal solution selection logic."""
        # Test with Litvin more efficient
        litvin_efficiency = 0.85
        collocation_efficiency = 0.80
        optimal = self.optimizer._select_optimal_solution(litvin_efficiency, collocation_efficiency)
        assert optimal == 'litvin'
        
        # Test with Collocation more efficient
        litvin_efficiency = 0.80
        collocation_efficiency = 0.85
        optimal = self.optimizer._select_optimal_solution(litvin_efficiency, collocation_efficiency)
        assert optimal == 'collocation'
        
        # Test with equal efficiency (should prefer Litvin)
        litvin_efficiency = 0.85
        collocation_efficiency = 0.85
        optimal = self.optimizer._select_optimal_solution(litvin_efficiency, collocation_efficiency)
        assert optimal == 'litvin'
    
    def test_efficiency_optimizer_calculate_solution_efficiency(self):
        """Test solution efficiency calculation."""
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test profiles
        profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        # Calculate efficiency
        efficiency = self.optimizer._calculate_solution_efficiency(
            profiles, motion_law, self.test_params, 'test_method'
        )
        
        # Validate efficiency
        assert isinstance(efficiency, (int, float))
        assert 0.0 <= efficiency <= 1.0
    
    def test_efficiency_optimizer_calculate_comparison_metrics(self):
        """Test comparison metrics calculation."""
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
        
        # Calculate comparison metrics
        metrics = self.optimizer._calculate_comparison_metrics(
            litvin_profiles, collocation_profiles, motion_law, self.test_params
        )
        
        # Validate metrics
        assert isinstance(metrics, dict)
        assert 'total_losses' in metrics
        
        # Check total losses structure
        total_losses = metrics['total_losses']
        assert 'litvin' in total_losses
        assert 'collocation' in total_losses
        assert 'difference' in total_losses
    
    def test_efficiency_optimizer_generate_recommendation(self):
        """Test recommendation generation."""
        # Test with small efficiency difference
        efficiency_analysis = {
            'optimal_method': 'litvin',
            'efficiency_difference': 0.005,  # 0.5% difference
            'efficiency_improvement': 0.5
        }
        recommendation = self.optimizer._generate_recommendation(efficiency_analysis)
        assert 'similar' in recommendation.lower() or 'both' in recommendation.lower()
        
        # Test with large efficiency difference
        efficiency_analysis = {
            'optimal_method': 'collocation',
            'efficiency_difference': 0.08,  # 8% difference
            'efficiency_improvement': 8.0
        }
        recommendation = self.optimizer._generate_recommendation(efficiency_analysis)
        assert 'significant' in recommendation.lower() or 'strongly' in recommendation.lower()
    
    def test_efficiency_optimizer_error_handling(self):
        """Test error handling in efficiency optimizer."""
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
        
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Should handle errors gracefully
        with pytest.raises(ValueError):
            self.optimizer.compare_solutions(
                invalid_profiles, valid_profiles, motion_law, self.test_params
            )
    
    def test_efficiency_optimizer_performance(self):
        """Test performance of efficiency optimizer."""
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
        result = self.optimizer.compare_solutions(
            litvin_profiles, collocation_profiles, motion_law, self.test_params
        )
        end_time = time.time()
        
        # Should complete in reasonable time (less than 2 seconds)
        assert (end_time - start_time) < 2.0
        
        # Result should be valid
        assert result is not None
        assert 'optimal_solution' in result
    
    def test_efficiency_optimizer_get_optimizer_info(self):
        """Test optimizer info retrieval."""
        info = self.optimizer.get_optimizer_info()
        
        assert isinstance(info, dict)
        assert 'optimizer_type' in info
        assert 'description' in info
        assert 'features' in info
        assert 'dependencies' in info
        
        assert info['optimizer_type'] == 'efficiency'
        assert 'efficiency' in info['description'].lower()
        assert 'ForceTransferAnalyzer' in info['dependencies']
