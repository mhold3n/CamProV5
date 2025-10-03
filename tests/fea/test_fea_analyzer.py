"""
Test suite for FEA analyzer implementation.

This test suite follows TDD principles to validate the FEA engine integration
for stress, vibration, and fatigue analysis.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add campro to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from campro.analysis.fea_analyzer import FEAAnalyzer
from campro.gears.profile_generator import GearProfileGenerator


class TestFEAAnalyzer:
    """Test suite for FEA analyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = FEAAnalyzer()
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
    
    def test_fea_analyzer_initialization(self):
        """Test that FEA analyzer can be initialized."""
        assert self.analyzer is not None
        assert hasattr(self.analyzer, 'analyze_assembly')
        assert hasattr(self.analyzer, 'run_stress_analysis')
        assert hasattr(self.analyzer, 'run_vibration_analysis')
        assert hasattr(self.analyzer, 'run_fatigue_analysis')
        assert hasattr(self.analyzer, 'is_available')
        assert hasattr(self.analyzer, 'get_version')
    
    def test_fea_analyzer_availability(self):
        """Test FEA engine availability check."""
        # Test availability check
        is_available = self.analyzer.is_available()
        assert isinstance(is_available, bool)
        
        # Test version retrieval
        version = self.analyzer.get_version()
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_fea_analyzer_analyze_assembly(self):
        """Test complete assembly analysis."""
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test gear profiles
        gear_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Create test tooth profiles
        tooth_profiles = {
            'sun_teeth': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet_teeth': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring_teeth': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        # Analyze assembly
        result = self.analyzer.analyze_assembly(gear_profiles, tooth_profiles, motion_law, self.test_params)
        
        # Validate results
        assert result is not None
        assert 'stress_analysis' in result
        assert 'vibration_analysis' in result
        assert 'fatigue_analysis' in result
        assert 'analysis_summary' in result
        
        # Check stress analysis
        stress_analysis = result['stress_analysis']
        assert 'max_stress' in stress_analysis
        assert 'stress_distribution' in stress_analysis
        assert 'safety_factor' in stress_analysis
        
        # Check vibration analysis
        vibration_analysis = result['vibration_analysis']
        assert 'natural_frequencies' in vibration_analysis
        assert 'mode_shapes' in vibration_analysis
        assert 'damping_ratios' in vibration_analysis
        
        # Check fatigue analysis
        fatigue_analysis = result['fatigue_analysis']
        assert 'fatigue_life' in fatigue_analysis
        assert 'damage_accumulation' in fatigue_analysis
        assert 'safety_margin' in fatigue_analysis
    
    def test_fea_analyzer_run_stress_analysis(self):
        """Test stress analysis execution."""
        # Create test gear profiles
        gear_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Create test tooth profiles
        tooth_profiles = {
            'sun_teeth': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet_teeth': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring_teeth': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        # Run stress analysis
        result = self.analyzer.run_stress_analysis(gear_profiles, tooth_profiles, self.test_params)
        
        # Validate results
        assert result is not None
        assert 'max_stress' in result
        assert 'stress_distribution' in result
        assert 'safety_factor' in result
        assert 'von_mises_stress' in result
        assert 'principal_stresses' in result
        
        # Check stress values are reasonable
        assert result['max_stress'] > 0
        assert result['safety_factor'] > 0
        assert isinstance(result['stress_distribution'], dict)
    
    def test_fea_analyzer_run_vibration_analysis(self):
        """Test vibration analysis execution."""
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test gear profiles
        gear_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Run vibration analysis
        result = self.analyzer.run_vibration_analysis(gear_profiles, motion_law, self.test_params)
        
        # Validate results
        assert result is not None
        assert 'natural_frequencies' in result
        assert 'mode_shapes' in result
        assert 'damping_ratios' in result
        assert 'frequency_response' in result
        
        # Check natural frequencies
        natural_frequencies = result['natural_frequencies']
        assert isinstance(natural_frequencies, list)
        assert len(natural_frequencies) > 0
        assert all(freq > 0 for freq in natural_frequencies)
        
        # Check mode shapes
        mode_shapes = result['mode_shapes']
        assert isinstance(mode_shapes, list)
        assert len(mode_shapes) == len(natural_frequencies)
    
    def test_fea_analyzer_run_fatigue_analysis(self):
        """Test fatigue analysis execution."""
        # Create test gear profiles
        gear_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Create test tooth profiles
        tooth_profiles = {
            'sun_teeth': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet_teeth': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring_teeth': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        # Run fatigue analysis
        result = self.analyzer.run_fatigue_analysis(gear_profiles, tooth_profiles, self.test_params)
        
        # Validate results
        assert result is not None
        assert 'fatigue_life' in result
        assert 'damage_accumulation' in result
        assert 'safety_margin' in result
        assert 'stress_cycles' in result
        assert 'endurance_limit' in result
        
        # Check fatigue life
        fatigue_life = result['fatigue_life']
        assert isinstance(fatigue_life, (int, float))
        assert fatigue_life > 0
        
        # Check safety margin
        safety_margin = result['safety_margin']
        assert isinstance(safety_margin, (int, float))
        assert safety_margin > 0
    
    def test_fea_analyzer_data_conversion(self):
        """Test data conversion between Python and Rust formats."""
        # Create test gear profiles
        gear_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Test Python to Rust conversion
        rust_data = self.analyzer._convert_python_to_rust(gear_profiles, self.test_params)
        assert isinstance(rust_data, dict)
        assert 'sun' in rust_data
        assert 'planet' in rust_data
        assert 'ring' in rust_data
        
        # Test Rust to Python conversion
        python_data = self.analyzer._convert_rust_to_python(rust_data)
        assert isinstance(python_data, dict)
        assert 'sun' in python_data
        assert 'planet' in python_data
        assert 'ring' in python_data
    
    def test_fea_analyzer_error_handling(self):
        """Test error handling in FEA analyzer."""
        # Test with invalid gear profiles
        invalid_profiles = {
            'sun': np.array([]),  # Empty array
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        # Should handle errors gracefully
        with pytest.raises(ValueError):
            self.analyzer.run_stress_analysis(invalid_profiles, {}, self.test_params)
    
    def test_fea_analyzer_performance(self):
        """Test performance of FEA analyzer."""
        # Create test gear profiles
        gear_profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Create test tooth profiles
        tooth_profiles = {
            'sun_teeth': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet_teeth': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring_teeth': np.array([[0, 0], [1, 1], [2, 2]])
        }
        
        # Time the analysis
        import time
        start_time = time.time()
        
        # Run stress analysis
        result = self.analyzer.run_stress_analysis(gear_profiles, tooth_profiles, self.test_params)
        
        end_time = time.time()
        
        # Should complete in reasonable time (less than 5 seconds)
        assert (end_time - start_time) < 5.0
        
        # Result should be valid
        assert result is not None
        assert 'max_stress' in result
    
    def test_fea_analyzer_get_analyzer_info(self):
        """Test analyzer info retrieval."""
        info = self.analyzer.get_analyzer_info()
        
        assert isinstance(info, dict)
        assert 'analyzer_type' in info
        assert 'description' in info
        assert 'features' in info
        assert 'dependencies' in info
        
        assert info['analyzer_type'] == 'fea'
        assert 'fea' in info['description'].lower()
        assert 'rust' in str(info['dependencies']).lower()
