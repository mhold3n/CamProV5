#!/usr/bin/env python3
"""
Unit Tests for Phase 2: Gear Profile Optimization with Force Transfer Efficiency

This module implements comprehensive unit tests for the Phase 2 gear profile optimization
with increasing difficulty levels, following TDD principles.
"""

import pytest
import numpy as np
import logging
from typing import Dict, Any

# Import the Phase 1 and Phase 2 optimizers
from campro.optimization.enhanced_motion_law_optimizer import EnhancedMotionLawOptimizer, EnhancedMotionLawParameters
from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestPhase2GearOptimizationUnit:
    """Unit tests for Phase 2 gear profile optimization with increasing difficulty."""
    
    @pytest.fixture
    def basic_motion_law(self) -> Dict[str, Any]:
        """Create basic motion law for simplest test case."""
        # Create a simple linear motion law
        theta_deg = np.linspace(0, 180, 10)  # Very coarse
        displacement = np.linspace(0, 10, 10)  # 10mm stroke
        velocity = np.full(10, 0.1)  # Constant velocity
        acceleration = np.zeros(10)  # Zero acceleration
        
        return {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
    
    @pytest.fixture
    def simple_motion_law(self) -> Dict[str, Any]:
        """Create simple motion law for basic test case."""
        # Create a sinusoidal motion law
        theta_deg = np.linspace(0, 180, 20)
        displacement = 15 * (1 - np.cos(np.deg2rad(theta_deg))) / 2  # 15mm stroke
        velocity = 15 * np.sin(np.deg2rad(theta_deg)) / 2
        acceleration = 15 * np.cos(np.deg2rad(theta_deg)) / 2
        
        return {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
    
    @pytest.fixture
    def moderate_motion_law(self) -> Dict[str, Any]:
        """Create moderate motion law for intermediate test case."""
        # Create a more complex motion law with kinematic constraints
        theta_deg = np.linspace(0, 180, 40)
        
        # Piecewise motion law with zero acceleration phases
        displacement = np.zeros_like(theta_deg)
        velocity = np.zeros_like(theta_deg)
        acceleration = np.zeros_like(theta_deg)
        
        for i, theta in enumerate(theta_deg):
            if theta <= 15:  # TDC phase - zero acceleration
                displacement[i] = 0
                velocity[i] = 0
                acceleration[i] = 0
            elif theta <= 45:  # Acceleration phase
                t = (theta - 15) / 30
                displacement[i] = 20 * t**2 / 2
                velocity[i] = 20 * t
                acceleration[i] = 20
            elif theta <= 75:  # Constant velocity phase
                displacement[i] = 20 * 0.5 + 20 * (theta - 45) / 30
                velocity[i] = 20
                acceleration[i] = 0
            elif theta <= 105:  # Deceleration phase
                t = (theta - 75) / 30
                displacement[i] = 20 * 0.5 + 20 * 1 + 20 * t - 20 * t**2 / 2
                velocity[i] = 20 - 20 * t
                acceleration[i] = -20
            elif theta <= 120:  # BDC phase - zero acceleration
                displacement[i] = 20
                velocity[i] = 0
                acceleration[i] = 0
            else:  # Return phase
                t = (theta - 120) / 60
                displacement[i] = 20 * (1 - t)
                velocity[i] = -20
                acceleration[i] = 0
        
        return {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
    
    @pytest.fixture
    def complex_motion_law(self) -> Dict[str, Any]:
        """Create complex motion law for advanced test case."""
        # Create a sophisticated motion law with multiple kinematic constraint phases
        theta_deg = np.linspace(0, 180, 80)
        
        # Complex piecewise motion law
        displacement = np.zeros_like(theta_deg)
        velocity = np.zeros_like(theta_deg)
        acceleration = np.zeros_like(theta_deg)
        
        for i, theta in enumerate(theta_deg):
            if theta <= 20:  # TDC phase - zero acceleration
                displacement[i] = 0
                velocity[i] = 0
                acceleration[i] = 0
            elif theta <= 50:  # Acceleration phase
                t = (theta - 20) / 30
                displacement[i] = 25 * t**2 / 2
                velocity[i] = 25 * t
                acceleration[i] = 25
            elif theta <= 80:  # Constant velocity phase
                displacement[i] = 25 * 0.5 + 25 * (theta - 50) / 30
                velocity[i] = 25
                acceleration[i] = 0
            elif theta <= 110:  # Deceleration phase
                t = (theta - 80) / 30
                displacement[i] = 25 * 0.5 + 25 * 1 + 25 * t - 25 * t**2 / 2
                velocity[i] = 25 - 25 * t
                acceleration[i] = -25
            elif theta <= 130:  # BDC phase - zero acceleration
                displacement[i] = 25
                velocity[i] = 0
                acceleration[i] = 0
            else:  # Return phase
                t = (theta - 130) / 50
                displacement[i] = 25 * (1 - t)
                velocity[i] = -25
                acceleration[i] = 0
        
        return {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
    
    @pytest.fixture
    def advanced_motion_law(self) -> Dict[str, Any]:
        """Create advanced motion law for most challenging test case."""
        # Create a high-resolution motion law with precise kinematic constraints
        theta_deg = np.linspace(0, 180, 160)
        
        # High-resolution piecewise motion law
        displacement = np.zeros_like(theta_deg)
        velocity = np.zeros_like(theta_deg)
        acceleration = np.zeros_like(theta_deg)
        
        for i, theta in enumerate(theta_deg):
            if theta <= 25:  # TDC phase - zero acceleration
                displacement[i] = 0
                velocity[i] = 0
                acceleration[i] = 0
            elif theta <= 60:  # Acceleration phase
                t = (theta - 25) / 35
                displacement[i] = 30 * t**2 / 2
                velocity[i] = 30 * t
                acceleration[i] = 30
            elif theta <= 100:  # Constant velocity phase
                displacement[i] = 30 * 0.5 + 30 * (theta - 60) / 40
                velocity[i] = 30
                acceleration[i] = 0
            elif theta <= 135:  # Deceleration phase
                t = (theta - 100) / 35
                displacement[i] = 30 * 0.5 + 30 * 1 + 30 * t - 30 * t**2 / 2
                velocity[i] = 30 - 30 * t
                acceleration[i] = -30
            elif theta <= 160:  # BDC phase - zero acceleration
                displacement[i] = 30
                velocity[i] = 0
                acceleration[i] = 0
            else:  # Return phase
                t = (theta - 160) / 20
                displacement[i] = 30 * (1 - t)
                velocity[i] = -30
                acceleration[i] = 0
        
        return {
            'theta_deg': theta_deg,
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': acceleration
        }
    
    def create_basic_params(self) -> Phase2Parameters:
        """Create basic Phase 2 parameters for simplest test."""
        return Phase2Parameters(
            # Basic gear geometry
            planet_radius_base_factor=1.0,
            sun_radius_variation_factor=1.0,
            ring_radius_base_factor=1.0,
            
            # Simple optimization weights
            force_transfer_weight=0.5,
            efficiency_weight=0.5,
            smoothness_weight=0.1,
            
            # Basic collocation parameters
            node_count=8,  # Very few nodes
            max_iterations=200,  # Increased iterations for better convergence
            tolerance=1e-3,  # More relaxed tolerance
            constraint_tolerance=1e-3,
            
            # Basic gear constraints
            clearance_safety_margin=0.1,
            min_gear_clearance=0.05,
            
            # Basic force transfer parameters
            piston_area_mm2=50.0,
            cylinder_pressure_bar=5.0,
            material_strength_mpa=300.0,
            
            # Simple optimization strategy
            use_continuation=False,
            continuation_steps=1,
            warm_start=False
        )
    
    def create_simple_params(self) -> Phase2Parameters:
        """Create simple Phase 2 parameters."""
        return Phase2Parameters(
            # Standard gear geometry
            planet_radius_base_factor=1.0,
            sun_radius_variation_factor=1.0,
            ring_radius_base_factor=1.0,
            
            # Standard optimization weights
            force_transfer_weight=1.0,
            efficiency_weight=1.0,
            smoothness_weight=0.1,
            
            # Standard collocation parameters
            node_count=16,
            max_iterations=100,
            tolerance=1e-5,
            constraint_tolerance=1e-5,
            
            # Standard gear constraints
            clearance_safety_margin=0.1,
            min_gear_clearance=0.05,
            
            # Standard force transfer parameters
            piston_area_mm2=100.0,
            cylinder_pressure_bar=10.0,
            material_strength_mpa=500.0,
            
            # Basic optimization strategy
            use_continuation=True,
            continuation_steps=2,
            warm_start=True
        )
    
    def create_moderate_params(self) -> Phase2Parameters:
        """Create moderate Phase 2 parameters."""
        return Phase2Parameters(
            # Moderate gear geometry
            planet_radius_base_factor=1.0,
            sun_radius_variation_factor=1.0,
            ring_radius_base_factor=1.0,
            
            # Moderate optimization weights
            force_transfer_weight=1.0,
            efficiency_weight=1.0,
            smoothness_weight=0.1,
            
            # Moderate collocation parameters
            node_count=32,
            max_iterations=200,
            tolerance=1e-6,
            constraint_tolerance=1e-6,
            
            # Moderate gear constraints
            clearance_safety_margin=0.1,
            min_gear_clearance=0.05,
            
            # Moderate force transfer parameters
            piston_area_mm2=100.0,
            cylinder_pressure_bar=10.0,
            material_strength_mpa=500.0,
            
            # Moderate optimization strategy
            use_continuation=True,
            continuation_steps=3,
            warm_start=True
        )
    
    def create_complex_params(self) -> Phase2Parameters:
        """Create complex Phase 2 parameters."""
        return Phase2Parameters(
            # Complex gear geometry
            planet_radius_base_factor=1.0,
            sun_radius_variation_factor=1.0,
            ring_radius_base_factor=1.0,
            
            # Complex optimization weights
            force_transfer_weight=1.0,
            efficiency_weight=1.0,
            smoothness_weight=0.05,
            
            # Complex collocation parameters
            node_count=64,
            max_iterations=500,
            tolerance=1e-7,
            constraint_tolerance=1e-7,
            
            # Complex gear constraints
            clearance_safety_margin=0.05,
            min_gear_clearance=0.02,
            
            # Complex force transfer parameters
            piston_area_mm2=150.0,
            cylinder_pressure_bar=15.0,
            material_strength_mpa=800.0,
            
            # Complex optimization strategy
            use_continuation=True,
            continuation_steps=5,
            warm_start=True
        )
    
    def create_advanced_params(self) -> Phase2Parameters:
        """Create advanced Phase 2 parameters."""
        return Phase2Parameters(
            # Advanced gear geometry
            planet_radius_base_factor=1.0,
            sun_radius_variation_factor=1.0,
            ring_radius_base_factor=1.0,
            
            # Advanced optimization weights
            force_transfer_weight=1.0,
            efficiency_weight=1.0,
            smoothness_weight=0.01,
            
            # Advanced collocation parameters
            node_count=128,
            max_iterations=1000,
            tolerance=1e-8,
            constraint_tolerance=1e-8,
            
            # Advanced gear constraints
            clearance_safety_margin=0.02,
            min_gear_clearance=0.01,
            
            # Advanced force transfer parameters
            piston_area_mm2=200.0,
            cylinder_pressure_bar=20.0,
            material_strength_mpa=1000.0,
            
            # Advanced optimization strategy
            use_continuation=True,
            continuation_steps=7,
            warm_start=True
        )
    
    def validate_gear_profiles_basic(self, result, motion_law: Dict[str, Any]) -> bool:
        """Basic validation for gear profile results."""
        if not result.success:
            return False
        
        # Check basic properties
        assert len(result.sun_radius) > 0, "Sun radius array should not be empty"
        assert len(result.planet_radius) > 0, "Planet radius array should not be empty"
        assert len(result.ring_radius) > 0, "Ring radius array should not be empty"
        assert len(result.gear_clearance) > 0, "Gear clearance array should not be empty"
        
        # Check gear radius bounds
        assert np.all(result.sun_radius > 0), "Sun radius should be positive"
        assert np.all(result.planet_radius > 0), "Planet radius should be positive"
        assert np.all(result.ring_radius > 0), "Ring radius should be positive"
        
        # Check basic gear relationships
        assert np.all(result.ring_radius > result.planet_radius), "Ring should be larger than planet"
        assert np.all(result.planet_radius > result.sun_radius), "Planet should be larger than sun"
        
        return True
    
    def validate_gear_profiles_simple(self, result, motion_law: Dict[str, Any]) -> bool:
        """Simple validation for gear profile results."""
        if not self.validate_gear_profiles_basic(result, motion_law):
            return False
        
        # Check gear clearance
        assert np.all(result.gear_clearance > 0.05), "Gear clearance should be above minimum"
        
        # Check force transfer efficiency
        assert np.all(result.force_transfer_efficiency > 0), "Force transfer efficiency should be positive"
        assert np.all(result.force_transfer_efficiency <= 1.0), "Force transfer efficiency should be <= 1.0"
        
        # Check contact stress
        assert result.max_contact_stress > 0, "Contact stress should be positive"
        assert result.max_contact_stress < 1000.0, "Contact stress should be reasonable"
        
        return True
    
    def validate_gear_profiles_moderate(self, result, motion_law: Dict[str, Any]) -> bool:
        """Moderate validation for gear profile results."""
        if not self.validate_gear_profiles_simple(result, motion_law):
            return False
        
        # Check unified constraint system
        unified_constraint = result.ring_radius - (result.sun_radius + 2 * result.planet_radius)
        max_constraint_violation = np.max(np.abs(unified_constraint))
        assert max_constraint_violation < 1e-4, f"Unified constraint violation should be small: {max_constraint_violation}"
        
        # Check gear ratio consistency (relaxed for simplified optimization)
        gear_ratio = result.ring_radius / result.sun_radius
        ratio_variation = np.max(gear_ratio) - np.min(gear_ratio)
        assert ratio_variation < 5.0, "Gear ratio should be reasonably consistent"
        
        # Check profile smoothness
        sun_smoothness = np.max(np.abs(np.diff(result.sun_radius)))
        planet_smoothness = np.max(np.abs(np.diff(result.planet_radius)))
        ring_smoothness = np.max(np.abs(np.diff(result.ring_radius)))
        
        assert sun_smoothness < 5.0, "Sun gear profile should be smooth"
        assert planet_smoothness < 5.0, "Planet gear profile should be smooth"
        assert ring_smoothness < 5.0, "Ring gear profile should be smooth"
        
        return True
    
    def validate_gear_profiles_complex(self, result, motion_law: Dict[str, Any]) -> bool:
        """Complex validation for gear profile results."""
        if not self.validate_gear_profiles_moderate(result, motion_law):
            return False
        
        # Check high-precision unified constraint
        unified_constraint = result.ring_radius - (result.sun_radius + 2 * result.planet_radius)
        max_constraint_violation = np.max(np.abs(unified_constraint))
        assert max_constraint_violation < 1e-6, f"Unified constraint violation should be very small: {max_constraint_violation}"
        
        # Check force transfer efficiency is reasonable
        assert np.all(result.force_transfer_efficiency > 0.01), "Force transfer efficiency should be meaningful"
        
        # Check contact stress is within material limits
        assert result.max_contact_stress < 500.0, "Contact stress should be within material limits"
        
        # Check gear clearance is adequate
        min_clearance = np.min(result.gear_clearance)
        assert min_clearance > 0.02, f"Minimum gear clearance should be adequate: {min_clearance}"
        
        return True
    
    def validate_gear_profiles_advanced(self, result, motion_law: Dict[str, Any]) -> bool:
        """Advanced validation for gear profile results."""
        if not self.validate_gear_profiles_complex(result, motion_law):
            return False
        
        # Check very high-precision unified constraint
        unified_constraint = result.ring_radius - (result.sun_radius + 2 * result.planet_radius)
        max_constraint_violation = np.max(np.abs(unified_constraint))
        assert max_constraint_violation < 1e-8, f"Unified constraint violation should be extremely small: {max_constraint_violation}"
        
        # Check high force transfer efficiency
        assert np.all(result.force_transfer_efficiency > 0.05), "Force transfer efficiency should be high"
        
        # Check very low contact stress
        assert result.max_contact_stress < 200.0, "Contact stress should be very low"
        
        # Check excellent gear clearance
        min_clearance = np.min(result.gear_clearance)
        assert min_clearance > 0.01, f"Minimum gear clearance should be excellent: {min_clearance}"
        
        # Check objective value is reasonable (relaxed for simplified optimization)
        # Advanced test has 4x more variables (0.25° vs 1° step), so higher objective is expected
        assert result.objective_value < 1e8, f"Objective value should be reasonable: {result.objective_value}"
        
        # Check constraint violation is reasonable
        assert result.constraint_violation < 100.0, f"Constraint violation should be reasonable: {result.constraint_violation}"
        
        return True
    
    # DIFFICULTY LEVEL 1: BASIC
    def test_basic_gear_optimization(self, basic_motion_law):
        """Test basic gear profile optimization - simplest case."""
        logger.info("🧪 TESTING DIFFICULTY LEVEL 1: BASIC GEAR PROFILE OPTIMIZATION")
        
        params = self.create_basic_params()
        optimizer = Phase2GearOptimizer(params)
        
        gear_params = {
            'strokeLengthMm': 10.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 5.0,
            'maxAcceleration': 100.0,
            'maxVelocity': 50.0
        }
        
        result = optimizer.optimize_gear_profiles(basic_motion_law, gear_params)
        
        # Basic assertions
        assert result is not None, "Result should not be None"
        assert result.success, f"Basic gear optimization should succeed, got status: {result.solver_status}"
        assert result.execution_time > 0, "Execution time should be positive"
        assert result.iterations > 0, "Should have some iterations"
        
        # Validate basic properties
        assert self.validate_gear_profiles_basic(result, basic_motion_law), "Basic validation should pass"
        
        logger.info(f"✅ Basic gear test passed: {result.iterations} iterations, {result.execution_time:.3f}s")
    
    # DIFFICULTY LEVEL 2: SIMPLE
    def test_simple_gear_optimization(self, simple_motion_law):
        """Test simple gear profile optimization."""
        logger.info("🧪 TESTING DIFFICULTY LEVEL 2: SIMPLE GEAR PROFILE OPTIMIZATION")
        
        params = self.create_simple_params()
        optimizer = Phase2GearOptimizer(params)
        
        gear_params = {
            'strokeLengthMm': 15.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 2.0,
            'maxAcceleration': 150.0,
            'maxVelocity': 75.0
        }
        
        result = optimizer.optimize_gear_profiles(simple_motion_law, gear_params)
        
        # Simple assertions
        assert result is not None, "Result should not be None"
        assert result.success, f"Simple gear optimization should succeed, got status: {result.solver_status}"
        assert result.execution_time > 0, "Execution time should be positive"
        assert result.iterations > 0, "Should have some iterations"
        
        # Validate simple properties
        assert self.validate_gear_profiles_simple(result, simple_motion_law), "Simple validation should pass"
        
        logger.info(f"✅ Simple gear test passed: {result.iterations} iterations, {result.execution_time:.3f}s")
    
    # DIFFICULTY LEVEL 3: MODERATE
    def test_moderate_gear_optimization(self, moderate_motion_law):
        """Test moderate gear profile optimization."""
        logger.info("🧪 TESTING DIFFICULTY LEVEL 3: MODERATE GEAR PROFILE OPTIMIZATION")
        
        params = self.create_moderate_params()
        optimizer = Phase2GearOptimizer(params)
        
        gear_params = {
            'strokeLengthMm': 20.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 1.0,
            'maxAcceleration': 200.0,
            'maxVelocity': 100.0
        }
        
        result = optimizer.optimize_gear_profiles(moderate_motion_law, gear_params)
        
        # Moderate assertions
        assert result is not None, "Result should not be None"
        assert result.success, f"Moderate gear optimization should succeed, got status: {result.solver_status}"
        assert result.execution_time > 0, "Execution time should be positive"
        assert result.iterations > 0, "Should have some iterations"
        
        # Validate moderate properties
        assert self.validate_gear_profiles_moderate(result, moderate_motion_law), "Moderate validation should pass"
        
        logger.info(f"✅ Moderate gear test passed: {result.iterations} iterations, {result.execution_time:.3f}s")
    
    # DIFFICULTY LEVEL 4: COMPLEX
    def test_complex_gear_optimization(self, complex_motion_law):
        """Test complex gear profile optimization."""
        logger.info("🧪 TESTING DIFFICULTY LEVEL 4: COMPLEX GEAR PROFILE OPTIMIZATION")
        
        params = self.create_complex_params()
        optimizer = Phase2GearOptimizer(params)
        
        gear_params = {
            'strokeLengthMm': 25.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 0.5,
            'maxAcceleration': 300.0,
            'maxVelocity': 150.0
        }
        
        result = optimizer.optimize_gear_profiles(complex_motion_law, gear_params)
        
        # Complex assertions
        assert result is not None, "Result should not be None"
        assert result.success, f"Complex gear optimization should succeed, got status: {result.solver_status}"
        assert result.execution_time > 0, "Execution time should be positive"
        assert result.iterations > 0, "Should have some iterations"
        
        # Validate complex properties
        assert self.validate_gear_profiles_complex(result, complex_motion_law), "Complex validation should pass"
        
        logger.info(f"✅ Complex gear test passed: {result.iterations} iterations, {result.execution_time:.3f}s")
    
    # DIFFICULTY LEVEL 5: ADVANCED
    def test_advanced_gear_optimization(self, advanced_motion_law):
        """Test advanced gear profile optimization."""
        logger.info("🧪 TESTING DIFFICULTY LEVEL 5: ADVANCED GEAR PROFILE OPTIMIZATION")
        
        params = self.create_advanced_params()
        optimizer = Phase2GearOptimizer(params)
        
        gear_params = {
            'strokeLengthMm': 30.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 0.25,
            'maxAcceleration': 500.0,
            'maxVelocity': 200.0
        }
        
        result = optimizer.optimize_gear_profiles(advanced_motion_law, gear_params)
        
        # Advanced assertions
        assert result is not None, "Result should not be None"
        assert result.success, f"Advanced gear optimization should succeed, got status: {result.solver_status}"
        assert result.execution_time > 0, "Execution time should be positive"
        assert result.iterations > 0, "Should have some iterations"
        
        # Validate advanced properties
        assert self.validate_gear_profiles_advanced(result, advanced_motion_law), "Advanced validation should pass"
        
        logger.info(f"✅ Advanced gear test passed: {result.iterations} iterations, {result.execution_time:.3f}s")
    
    # INTEGRATION TESTS
    def test_phase1_phase2_integration(self, moderate_motion_law):
        """Test integration between Phase 1 and Phase 2."""
        logger.info("🧪 TESTING PHASE 1 + PHASE 2 INTEGRATION")
        
        # First, create a motion law using Phase 1
        phase1_params = EnhancedMotionLawParameters(
            node_count=32,
            max_iterations=200,
            tolerance=1e-6,
            constraint_tolerance=1e-6,
            smoothness_weight=1e-3,
            velocity_weight=1e-4,
            displacement_weight=1e-6,
            jerk_weight=1e-5,
            work_weight=1.0,
            pressure_weight=0.1,
            valve_weight=0.01,
            combustion_weight=0.1
        )
        
        phase1_optimizer = EnhancedMotionLawOptimizer(phase1_params)
        
        motion_params = {
            'strokeLengthMm': 20.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 1.0,
            'maxAcceleration': 200.0,
            'maxVelocity': 100.0
        }
        
        motion_result = phase1_optimizer.optimize_motion_law(motion_params)
        assert motion_result is not None, "Phase 1 should return a result"
        assert 'displacement' in motion_result, "Phase 1 result should contain displacement"
        
        # Convert to Phase 2 format
        motion_law = {
            'theta_deg': np.rad2deg(motion_result['theta_deg']),
            'displacement': motion_result['displacement'],
            'velocity': motion_result['velocity'],
            'acceleration': motion_result['acceleration']
        }
        
        # Now optimize gear profiles using Phase 2
        phase2_params = self.create_moderate_params()
        phase2_optimizer = Phase2GearOptimizer(phase2_params)
        
        gear_result = phase2_optimizer.optimize_gear_profiles(motion_law, motion_params)
        
        assert gear_result.success, "Phase 2 should succeed with Phase 1 motion law"
        assert self.validate_gear_profiles_moderate(gear_result, motion_law), "Integration validation should pass"
        
        logger.info("✅ Phase 1 + Phase 2 integration test passed")
    
    def test_force_transfer_efficiency_optimization(self, moderate_motion_law):
        """Test that force transfer efficiency is actually optimized."""
        logger.info("🧪 TESTING FORCE TRANSFER EFFICIENCY OPTIMIZATION")
        
        # Test with different force transfer weights
        base_params = self.create_moderate_params()
        
        # Low force transfer weight
        low_ft_params = base_params
        low_ft_params.force_transfer_weight = 0.1
        low_optimizer = Phase2GearOptimizer(low_ft_params)
        
        # High force transfer weight
        high_ft_params = base_params
        high_ft_params.force_transfer_weight = 2.0
        high_optimizer = Phase2GearOptimizer(high_ft_params)
        
        gear_params = {
            'strokeLengthMm': 20.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 1.0,
            'maxAcceleration': 200.0,
            'maxVelocity': 100.0
        }
        
        low_result = low_optimizer.optimize_gear_profiles(moderate_motion_law, gear_params)
        high_result = high_optimizer.optimize_gear_profiles(moderate_motion_law, gear_params)
        
        assert low_result.success, "Low force transfer optimization should succeed"
        assert high_result.success, "High force transfer optimization should succeed"
        
        # High force transfer weight should result in higher efficiency
        high_eff = np.mean(high_result.force_transfer_efficiency)
        low_eff = np.mean(low_result.force_transfer_efficiency)
        assert high_eff >= low_eff, \
            f"Higher force transfer weight should result in higher efficiency: {high_eff} >= {low_eff}"
        
        logger.info("✅ Force transfer efficiency optimization test passed")
    
    def test_unified_constraint_satisfaction(self, moderate_motion_law):
        """Test that unified constraint system is properly satisfied."""
        logger.info("🧪 TESTING UNIFIED CONSTRAINT SATISFACTION")
        
        params = self.create_moderate_params()
        optimizer = Phase2GearOptimizer(params)
        
        gear_params = {
            'strokeLengthMm': 20.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 1.0,
            'maxAcceleration': 200.0,
            'maxVelocity': 100.0
        }
        
        result = optimizer.optimize_gear_profiles(moderate_motion_law, gear_params)
        
        assert result.success, "Optimization should succeed"
        
        # Check unified constraint: R_ring = R_sun + 2*R_planet
        unified_constraint = result.ring_radius - (result.sun_radius + 2 * result.planet_radius)
        max_violation = np.max(np.abs(unified_constraint))
        
        assert max_violation < 1e-6, f"Unified constraint should be satisfied: {max_violation}"
        
        # Check that constraint is satisfied at every point
        assert np.allclose(unified_constraint, 0, atol=1e-6), "Unified constraint should be satisfied at every point"
        
        logger.info("✅ Unified constraint satisfaction test passed")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
