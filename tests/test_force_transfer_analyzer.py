"""
Test suite for force transfer analyzer implementation.

This test suite follows TDD principles to validate the force transfer calculations
used in efficiency optimization.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add campro to path
sys.path.append(str(Path(__file__).parent.parent))

from campro.physics.force_transfer import ForceTransferAnalyzer
from campro.gears.profile_generator import GearProfileGenerator


class TestForceTransferAnalyzer:
    """Test suite for force transfer analyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ForceTransferAnalyzer()
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
    
    def test_force_transfer_analyzer_initialization(self):
        """Test that force transfer analyzer can be initialized."""
        assert self.analyzer is not None
        assert hasattr(self.analyzer, 'calculate_piston_forces')
        assert hasattr(self.analyzer, 'calculate_contact_forces')
        assert hasattr(self.analyzer, 'calculate_mechanical_advantage')
        assert hasattr(self.analyzer, 'calculate_efficiency_from_losses')
        assert hasattr(self.analyzer, 'calculate_hertzian_losses')
        assert hasattr(self.analyzer, 'calculate_friction_losses')
        assert hasattr(self.analyzer, 'calculate_deformation_losses')
        assert hasattr(self.analyzer, 'calculate_windage_losses')
    
    def test_calculate_piston_forces(self):
        """Test piston force calculation."""
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Calculate piston forces
        piston_forces = self.analyzer.calculate_piston_forces(
            displacement, velocity, acceleration, self.test_params
        )
        
        # Validate results
        assert isinstance(piston_forces, np.ndarray)
        assert len(piston_forces) == len(theta_deg)
        assert np.all(piston_forces >= 0)  # Forces should be non-negative
    
    def test_calculate_contact_forces(self):
        """Test contact force calculation."""
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test gear profiles
        profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Calculate piston forces first
        piston_forces = self.analyzer.calculate_piston_forces(
            displacement, velocity, acceleration, self.test_params
        )
        
        # Calculate contact forces
        contact_forces = self.analyzer.calculate_contact_forces(profiles, piston_forces, self.test_params)
        
        # Validate results
        assert isinstance(contact_forces, dict)
        assert 'sun_planet_force' in contact_forces
        assert 'planet_ring_force' in contact_forces
        assert 'total_contact_force' in contact_forces
        
        # Check force arrays
        for force_key in ['sun_planet_force', 'planet_ring_force', 'total_contact_force']:
            force_array = contact_forces[force_key]
            assert isinstance(force_array, np.ndarray)
            assert len(force_array) == len(theta_deg)
            assert np.all(force_array >= 0)  # Forces should be non-negative
    
    def test_calculate_mechanical_advantage(self):
        """Test mechanical advantage calculation."""
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test gear profiles
        profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Calculate piston forces first
        piston_forces = self.analyzer.calculate_piston_forces(
            displacement, velocity, acceleration, self.test_params
        )
        
        # Calculate contact forces
        contact_forces = self.analyzer.calculate_contact_forces(profiles, piston_forces, self.test_params)
        
        # Calculate mechanical advantage
        mechanical_advantage = self.analyzer.calculate_mechanical_advantage(
            profiles, piston_forces, contact_forces, displacement, velocity, acceleration, self.test_params
        )
        
        # Validate results
        assert isinstance(mechanical_advantage, (int, float))
        assert mechanical_advantage > 1.0  # Should be greater than 1:1
        assert mechanical_advantage < 10.0  # Should be reasonable upper bound
    
    def test_calculate_hertzian_losses(self):
        """Test Hertzian contact losses calculation."""
        # Create test contact forces
        contact_forces = {
            'sun_planet_force': np.array([100, 150, 200]),
            'planet_ring_force': np.array([120, 160, 180]),
            'total_contact': np.array([220, 310, 380])
        }
        
        # Create test gear profiles
        profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Calculate Hertzian losses
        hertzian_losses = self.analyzer.calculate_hertzian_losses(contact_forces, profiles, self.test_params)
        
        # Validate results
        assert isinstance(hertzian_losses, np.ndarray)
        assert len(hertzian_losses) == len(contact_forces['total_contact_force'])
        assert np.all(hertzian_losses >= 0)  # Losses should be non-negative
    
    def test_calculate_friction_losses(self):
        """Test friction losses calculation."""
        # Create test contact forces
        contact_forces = {
            'sun_planet_force': np.array([100, 150, 200]),
            'planet_ring_force': np.array([120, 160, 180]),
            'total_contact': np.array([220, 310, 380])
        }
        
        # Create test gear profiles
        profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Calculate friction losses
        friction_losses = self.analyzer.calculate_friction_losses(contact_forces, profiles, self.test_params)
        
        # Validate results
        assert isinstance(friction_losses, np.ndarray)
        assert len(friction_losses) == len(contact_forces['total_contact_force'])
        assert np.all(friction_losses >= 0)  # Losses should be non-negative
    
    def test_calculate_deformation_losses(self):
        """Test deformation losses calculation."""
        # Create test contact forces
        contact_forces = {
            'sun_planet_force': np.array([100, 150, 200]),
            'planet_ring_force': np.array([120, 160, 180]),
            'total_contact': np.array([220, 310, 380])
        }
        
        # Create test gear profiles
        profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Calculate deformation losses
        deformation_losses = self.analyzer.calculate_deformation_losses(contact_forces, profiles, self.test_params)
        
        # Validate results
        assert isinstance(deformation_losses, np.ndarray)
        assert len(deformation_losses) == len(contact_forces['total_contact_force'])
        assert np.all(deformation_losses >= 0)  # Losses should be non-negative
    
    def test_calculate_windage_losses(self):
        """Test windage losses calculation."""
        # Create test gear profiles
        profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Calculate windage losses
        windage_losses = self.analyzer.calculate_windage_losses(profiles, self.test_params)
        
        # Validate results
        assert isinstance(windage_losses, np.ndarray)
        assert len(windage_losses) > 0
        assert np.all(windage_losses >= 0)  # Losses should be non-negative
    
    def test_calculate_efficiency_from_losses(self):
        """Test efficiency calculation from losses."""
        # Create test gear profiles
        profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test total losses
        total_losses = np.array([0.1, 0.15, 0.2])
        
        # Calculate piston forces and contact forces first
        piston_forces = self.analyzer.calculate_piston_forces(
            displacement, velocity, acceleration, self.test_params
        )
        contact_forces = self.analyzer.calculate_contact_forces(profiles, piston_forces, self.test_params)
        
        # Calculate efficiency
        efficiency = self.analyzer.calculate_efficiency_from_losses(
            profiles, piston_forces, contact_forces, displacement, velocity, acceleration
        )
        
        # Validate results
        assert isinstance(efficiency, (int, float))
        assert 0.0 <= efficiency <= 1.0  # Efficiency should be between 0 and 1
    
    def test_force_transfer_analyzer_error_handling(self):
        """Test error handling in force transfer analyzer."""
        # Test with invalid profiles
        invalid_profiles = {
            'sun': np.array([]),  # Empty array
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
        
        # Calculate piston forces first
        piston_forces = self.analyzer.calculate_piston_forces(
            displacement, velocity, acceleration, self.test_params
        )
        
        # Should handle errors gracefully
        with pytest.raises(ValueError):
            self.analyzer.calculate_contact_forces(invalid_profiles, piston_forces, self.test_params)
    
    def test_force_transfer_analyzer_performance(self):
        """Test performance of force transfer analyzer."""
        # Generate motion law for testing
        theta_deg, displacement, velocity, acceleration = self.generator.generate_motion_law_piecewise(self.test_params)
        motion_law = {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
        
        # Create test gear profiles
        profiles = {
            'sun': np.array([[0, 0], [1, 1], [2, 2]]),
            'planet': np.array([[0, 0], [1, 1], [2, 2]]),
            'ring': np.array([[0, 0], [1, 1], [2, 2]]),
            'r_sun': 10.0,
            'r_planet': 15.0,
            'r_ring_inner': 25.0
        }
        
        # Time the calculations
        import time
        start_time = time.time()
        
        # Calculate all force transfer components
        piston_forces = self.analyzer.calculate_piston_forces(
            displacement, velocity, acceleration, self.test_params
        )
        contact_forces = self.analyzer.calculate_contact_forces(profiles, piston_forces, self.test_params)
        mechanical_advantage = self.analyzer.calculate_mechanical_advantage(
            profiles, piston_forces, contact_forces, displacement, velocity, acceleration, self.test_params
        )
        
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        assert (end_time - start_time) < 1.0
        
        # Results should be valid
        assert piston_forces is not None
        assert contact_forces is not None
        assert mechanical_advantage is not None
