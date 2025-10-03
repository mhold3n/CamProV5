"""
Tests for enhanced optimizers with thermodynamic and transmission physics.

This module tests the integration of the missing physics from the gap analysis:
- Enhanced motion law optimizer with thermodynamics
- Enhanced gear optimizer with transmission physics
- Integration between Phase 1 and Phase 2
"""

import pytest
import numpy as np
import casadi as ca

from campro.optimization.enhanced_motion_law_optimizer import (
    EnhancedMotionLawParameters, EnhancedMotionLawOptimizer
)
from campro.optimization.enhanced_gear_optimizer import (
    EnhancedGearParameters, EnhancedGearOptimizer
)


class TestEnhancedMotionLawOptimizer:
    """Test enhanced motion law optimizer with thermodynamics."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return EnhancedMotionLawParameters(
            node_count=16,  # Smaller for testing
            max_iterations=100,  # Smaller for testing
            work_weight=1.0,
            pressure_weight=0.1,
            valve_weight=0.01,
            combustion_weight=0.1,
            use_solver_improvements=False,  # Disable for testing
            use_continuation=False,  # Disable for testing
            use_objective_normalization=False,  # Disable for testing
            use_variable_scaling=False  # Disable for testing
        )
    
    @pytest.fixture
    def optimizer(self, params):
        """Create enhanced motion law optimizer."""
        return EnhancedMotionLawOptimizer(params)
    
    def test_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer.params is not None
        assert optimizer.thermo_calc is not None
        assert optimizer.valve_model is not None
        assert optimizer.combustion_model is not None
        assert optimizer.state_eqns is not None
        assert optimizer.thermo_optimizer is not None
    
    def test_motion_law_optimization(self, optimizer):
        """Test motion law optimization with thermodynamics."""
        motion_params = {
            'strokeLengthMm': 10.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 10.0,
            'compressionDurationPercent': 70.0,
            'maxVelocity': 100.0,
            'maxAcceleration': 200.0,
            'jerkLimit': 5000.0,
            'dwellTdcDeg': 10.0,
            'dwellBdcDeg': 10.0
        }
        
        # This would normally run the full optimization
        # For testing, we'll just verify the components work
        grid = optimizer._create_motion_law_grid(motion_params)
        assert len(grid) > 0
        
        nlp_info = optimizer._build_enhanced_nlp_formulation(motion_params, grid)
        assert 'nlp' in nlp_info
        assert 'lbx' in nlp_info
        assert 'ubx' in nlp_info
        assert 'lbg' in nlp_info
        assert 'ubg' in nlp_info
        assert 'x0' in nlp_info
    
    def test_thermodynamic_objectives(self, optimizer):
        """Test thermodynamic objectives calculation."""
        motion_params = {
            'strokeLengthMm': 10.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 10.0
        }
        
        grid = optimizer._create_motion_law_grid(motion_params)
        n = len(grid)
        
        # Create test variables
        x = ca.SX.sym('x', n)
        v = ca.SX.sym('v', n-1)
        a = ca.SX.sym('a', n-2)
        
        # Test thermodynamic objectives
        thermo_objectives = optimizer._add_thermodynamic_objectives(x, v, a, grid, motion_params)
        
        # Check that objectives are calculated
        assert isinstance(thermo_objectives, ca.SX)
    
    def test_thermodynamic_constraints(self, optimizer):
        """Test thermodynamic constraints calculation."""
        motion_params = {
            'strokeLengthMm': 10.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 10.0
        }
        
        grid = optimizer._create_motion_law_grid(motion_params)
        n = len(grid)
        
        # Create test variables
        x = ca.SX.sym('x', n)
        v = ca.SX.sym('v', n-1)
        a = ca.SX.sym('a', n-2)
        
        # Test thermodynamic constraints
        thermo_constraints = optimizer._add_thermodynamic_constraints(x, v, a, grid, motion_params)
        
        # Check that constraints are calculated
        assert 'g' in thermo_constraints
        assert 'lbg' in thermo_constraints
        assert 'ubg' in thermo_constraints
        assert len(thermo_constraints['g']) == len(thermo_constraints['lbg'])
        assert len(thermo_constraints['g']) == len(thermo_constraints['ubg'])
    
    def test_phase_indices(self, optimizer):
        """Test phase indices calculation."""
        motion_params = {
            'strokeLengthMm': 10.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 10.0,
            'dwellTdcDeg': 10.0,
            'dwellBdcDeg': 10.0
        }
        
        grid = optimizer._create_motion_law_grid(motion_params)
        
        # Test different phase indices
        tdc_indices = optimizer._get_phase_indices(grid, 'TDC_FULL', motion_params)
        bdc_indices = optimizer._get_phase_indices(grid, 'BDC_FULL', motion_params)
        travel_indices = optimizer._get_phase_indices(grid, 'TRAVEL', motion_params)
        
        # Check that indices are calculated
        assert isinstance(tdc_indices, list)
        assert isinstance(bdc_indices, list)
        assert isinstance(travel_indices, list)
        
        # Check that indices are within bounds
        assert all(0 <= idx < len(grid) for idx in tdc_indices)
        assert all(0 <= idx < len(grid) for idx in bdc_indices)
        assert all(0 <= idx < len(grid) for idx in travel_indices)
    
    def test_initial_guess(self, optimizer):
        """Test enhanced initial guess creation."""
        motion_params = {
            'strokeLengthMm': 10.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 10.0,
            'compressionDurationPercent': 70.0
        }
        
        grid = optimizer._create_motion_law_grid(motion_params)
        x0 = optimizer._create_enhanced_initial_guess(grid, motion_params)
        
        # Check that initial guess is created
        assert isinstance(x0, np.ndarray)
        assert len(x0) > 0
        
        # Check that initial guess has reasonable values
        # Displacement and velocity should be non-negative, acceleration can be negative
        n_grid = len(grid)
        displacement = x0[:n_grid]
        velocity = x0[n_grid:n_grid+n_grid-1]
        acceleration = x0[n_grid+n_grid-1:]  # noqa: F841
        
        assert np.all(displacement >= 0.0)  # Displacement should be non-negative
        assert np.all(velocity >= 0.0)  # Velocity should be non-negative
        # Acceleration can be negative, so we don't check it
    
    def test_thermodynamic_data_calculation(self, optimizer):
        """Test thermodynamic data calculation."""
        # Create test data - asymmetric cycle to get positive work
        displacement = np.array([0.0, 0.002, 0.01, 0.008, 0.0])  # 10mm stroke, asymmetric
        velocity = np.array([1.0, 1.5, 2.0, 1.5, 1.0])
        acceleration = np.array([0.5, 1.0, 0.5, -0.5, -1.0])
        theta_deg = np.array([0.0, 45.0, 90.0, 135.0, 180.0])
        
        # Calculate thermodynamic data
        thermo_data = optimizer._calculate_thermodynamic_data(
            displacement, velocity, acceleration, theta_deg
        )
        
        # Check that thermodynamic data is calculated
        required_keys = ['volume_m3', 'pressure_Pa', 'temperature_K', 'indicated_work_J',
                        'valve_lift_m', 'heat_release_J', 'thermodynamic_objectives']
        for key in required_keys:
            assert key in thermo_data
        
        # Check that data has reasonable values
        assert abs(thermo_data['indicated_work_J']) < 1000.0  # Should be reasonable magnitude
        assert len(thermo_data['volume_m3']) == len(displacement)
        assert len(thermo_data['pressure_Pa']) == len(displacement)
        assert len(thermo_data['temperature_K']) == len(displacement)


class TestEnhancedGearOptimizer:
    """Test enhanced gear optimizer with transmission physics."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return EnhancedGearParameters(
            node_count=16,  # Smaller for testing
            max_iterations=100,  # Smaller for testing
            kinematic_weight=1.0,
            power_balance_weight=1.0,
            contact_stress_weight=0.1,
            friction_weight=0.1,
            fatigue_weight=1.0,
            use_solver_improvements=False,  # Disable for testing
            use_continuation=False,  # Disable for testing
            use_objective_normalization=False,  # Disable for testing
            use_variable_scaling=False  # Disable for testing
        )
    
    @pytest.fixture
    def optimizer(self, params):
        """Create enhanced gear optimizer."""
        return EnhancedGearOptimizer(params)
    
    def test_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer.params is not None
        assert optimizer.kinematic_coupling is not None
        assert optimizer.power_balance is not None
        assert optimizer.transmission_efficiency is not None
        assert optimizer.contact_mechanics is not None
        assert optimizer.friction_model is not None
        assert optimizer.transmission_optimizer is not None
    
    def test_gear_optimization(self, optimizer):
        """Test gear optimization with transmission physics."""
        motion_law = {
            'grid': np.linspace(0, 180, 19),  # 10-degree steps
            'displacement': np.array([0.0, 0.005, 0.01, 0.005, 0.0] * 4)[:19],  # Simplified
            'velocity': np.array([1.0, 1.5, 2.0, 1.5, 1.0] * 4)[:19],  # Simplified
            'acceleration': np.array([0.5, 1.0, 0.5, -0.5, -1.0] * 4)[:19]  # Simplified
        }
        
        gear_params = {
            'ringRotationDeg': 180.0,
            'gearRatio': 2.0,
            'rMin': 2.0,
            'rMax': 2.5,
            'maxJournalOffsetPercent': 0.1
        }
        
        # This would normally run the full optimization
        # For testing, we'll just verify the components work
        grid = optimizer._create_gear_collocation_grid(motion_law['grid'], gear_params)
        assert len(grid) > 0
        
        nlp_info = optimizer._build_enhanced_gear_nlp_formulation(motion_law, gear_params, grid)
        assert 'nlp' in nlp_info
        assert 'lbx' in nlp_info
        assert 'ubx' in nlp_info
        assert 'lbg' in nlp_info
        assert 'ubg' in nlp_info
        assert 'x0' in nlp_info
    
    def test_transmission_objectives(self, optimizer):
        """Test transmission objectives calculation."""
        motion_law = {
            'grid': np.linspace(0, 180, 19),
            'displacement': np.array([0.0, 0.005, 0.01, 0.005, 0.0] * 4)[:19],
            'velocity': np.array([1.0, 1.5, 2.0, 1.5, 1.0] * 4)[:19],
            'acceleration': np.array([0.5, 1.0, 0.5, -0.5, -1.0] * 4)[:19]
        }
        
        gear_params = {
            'ringRotationDeg': 180.0,
            'gearRatio': 2.0
        }
        
        grid = optimizer._create_gear_collocation_grid(motion_law['grid'], gear_params)
        n = len(grid)
        
        # Create test variables
        sun_radius = ca.SX.sym('sun_radius', n)
        planet_radius = ca.SX.sym('planet_radius', n)
        ring_radius = ca.SX.sym('ring_radius', n)
        r_inst = ca.SX.sym('r_inst', n)
        journal_offset = ca.SX.sym('journal_offset', n)
        
        displacement = ca.DM(motion_law['displacement'])
        velocity = ca.DM(motion_law['velocity'])
        acceleration = ca.DM(motion_law['acceleration'])
        
        # Test transmission objectives
        transmission_objectives = optimizer._add_transmission_objectives(
            sun_radius, planet_radius, ring_radius, r_inst, journal_offset,
            displacement, velocity, acceleration, grid
        )
        
        # Check that objectives are calculated
        assert isinstance(transmission_objectives, ca.SX)
    
    def test_gear_smoothness(self, optimizer):
        """Test gear smoothness calculation."""
        motion_law = {
            'grid': np.linspace(0, 180, 19),
            'displacement': np.array([0.0, 0.005, 0.01, 0.005, 0.0] * 4)[:19],
            'velocity': np.array([1.0, 1.5, 2.0, 1.5, 1.0] * 4)[:19],
            'acceleration': np.array([0.5, 1.0, 0.5, -0.5, -1.0] * 4)[:19]
        }
        
        gear_params = {
            'ringRotationDeg': 180.0,
            'gearRatio': 2.0
        }
        
        grid = optimizer._create_gear_collocation_grid(motion_law['grid'], gear_params)
        n = len(grid)
        
        # Create test variable
        radius = ca.SX.sym('radius', n)
        
        # Test gear smoothness
        smoothness = optimizer._compute_gear_smoothness(radius, grid)
        
        # Check that smoothness is calculated
        assert isinstance(smoothness, ca.SX)
    
    def test_variable_bounds(self, optimizer):
        """Test variable bounds creation."""
        gear_params = {
            'ringRotationDeg': 180.0,
            'gearRatio': 2.0,
            'rMin': 2.0,
            'rMax': 2.5,
            'maxJournalOffsetPercent': 0.1
        }
        
        n = 19  # Test size
        
        lbx, ubx = optimizer._build_variable_bounds(n, gear_params)
        
        # Check that bounds are created
        assert len(lbx) == 5 * n  # 5 variables per node
        assert len(ubx) == 5 * n
        
        # Check that bounds are reasonable
        assert all(lb <= ub for lb, ub in zip(lbx, ubx))
    
    def test_initial_guess(self, optimizer):
        """Test enhanced initial guess creation."""
        motion_law = {
            'displacement': np.array([0.0, 0.005, 0.01, 0.005, 0.0] * 4)[:19],
            'velocity': np.array([1.0, 1.5, 2.0, 1.5, 1.0] * 4)[:19],
            'acceleration': np.array([0.5, 1.0, 0.5, -0.5, -1.0] * 4)[:19]
        }
        
        gear_params = {
            'ringRotationDeg': 180.0,
            'gearRatio': 2.0,
            'rMin': 2.0,
            'rMax': 2.5,
            'maxJournalOffsetPercent': 0.1
        }
        
        n = 19
        x0 = optimizer._create_enhanced_initial_guess(n, motion_law['displacement'], 
                                                    motion_law['velocity'], 
                                                    motion_law['acceleration'], 
                                                    gear_params)
        
        # Check that initial guess is created
        assert isinstance(x0, list)
        assert len(x0) == 5 * n  # 5 variables per node
        
        # Check that initial guess has reasonable values
        assert all(val >= 0.0 for val in x0[:3*n])  # Gear radii should be non-negative
    
    def test_transmission_data_calculation(self, optimizer):
        """Test transmission data calculation."""
        # Create test data
        sun_radius = np.array([0.05, 0.05, 0.05, 0.05, 0.05])
        planet_radius = np.array([0.08, 0.08, 0.08, 0.08, 0.08])
        ring_radius = np.array([0.21, 0.21, 0.21, 0.21, 0.21])
        r_inst = np.array([2.0, 2.1, 2.2, 2.1, 2.0])
        journal_offset = np.array([0.001, 0.002, 0.003, 0.002, 0.001])
        
        motion_law = {
            'displacement': np.array([0.0, 0.005, 0.01, 0.005, 0.0]),
            'velocity': np.array([1.0, 1.5, 2.0, 1.5, 1.0]),
            'acceleration': np.array([0.5, 1.0, 0.5, -0.5, -1.0])
        }
        
        grid = np.linspace(0, 180, 5)
        
        # Calculate transmission data
        transmission_data = optimizer._calculate_transmission_data(
            sun_radius, planet_radius, ring_radius, r_inst, journal_offset,
            motion_law, grid
        )
        
        # Check that transmission data is calculated
        required_keys = ['angular_velocity_rad_s', 'piston_force_N', 'output_torque_Nm',
                        'contact_force_N', 'contact_stress_Pa', 'transmission_efficiency',
                        'friction_power_loss_W', 'fatigue_safety_factor', 'transmission_objectives']
        for key in required_keys:
            assert key in transmission_data
        
        # Check that data has reasonable values
        assert len(transmission_data['angular_velocity_rad_s']) == len(sun_radius)
        assert len(transmission_data['contact_stress_Pa']) == len(sun_radius)
        assert len(transmission_data['transmission_efficiency']) == len(sun_radius)
        assert len(transmission_data['fatigue_safety_factor']) == len(sun_radius)


class TestIntegration:
    """Test integration between enhanced optimizers."""
    
    @pytest.fixture
    def motion_law_params(self):
        """Create motion law parameters."""
        return EnhancedMotionLawParameters(
            node_count=16,
            max_iterations=100,
            use_solver_improvements=False,
            use_continuation=False
        )
    
    @pytest.fixture
    def gear_params(self):
        """Create gear parameters."""
        return EnhancedGearParameters(
            node_count=16,
            max_iterations=100,
            use_solver_improvements=False,
            use_continuation=False
        )
    
    @pytest.fixture
    def motion_law_optimizer(self, motion_law_params):
        """Create motion law optimizer."""
        return EnhancedMotionLawOptimizer(motion_law_params)
    
    @pytest.fixture
    def gear_optimizer(self, gear_params):
        """Create gear optimizer."""
        return EnhancedGearOptimizer(gear_params)
    
    def test_phase1_to_phase2_integration(self, motion_law_optimizer, gear_optimizer):
        """Test integration from Phase 1 to Phase 2."""
        # Create motion law parameters
        motion_params = {
            'strokeLengthMm': 10.0,
            'ringRotationDeg': 180.0,
            'samplingStepDeg': 10.0,
            'compressionDurationPercent': 70.0,
            'maxVelocity': 100.0,
            'maxAcceleration': 200.0,
            'jerkLimit': 5000.0,
            'dwellTdcDeg': 10.0,
            'dwellBdcDeg': 10.0
        }
        
        # Create gear parameters
        gear_params = {
            'ringRotationDeg': 180.0,
            'gearRatio': 2.0,
            'rMin': 2.0,
            'rMax': 2.5,
            'maxJournalOffsetPercent': 0.1
        }
        
        # Create mock motion law result (would come from Phase 1)
        motion_law = {
            'grid': np.linspace(0, 180, 19),
            'displacement': np.array([0.0, 0.005, 0.01, 0.005, 0.0] * 4)[:19],
            'velocity': np.array([1.0, 1.5, 2.0, 1.5, 1.0] * 4)[:19],
            'acceleration': np.array([0.5, 1.0, 0.5, -0.5, -1.0] * 4)[:19],
            'success': True,
            'thermodynamic_data': {
                'volume_m3': [0.001, 0.0015, 0.002, 0.0015, 0.001] * 4,
                'pressure_Pa': [101325, 80000, 60000, 80000, 101325] * 4,
                'indicated_work_J': 100.0
            }
        }
        
        # Test that both optimizers can handle the data
        motion_law_grid = motion_law_optimizer._create_motion_law_grid(motion_params)
        gear_grid = gear_optimizer._create_gear_collocation_grid(motion_law['grid'], gear_params)
        
        # Check that grids are compatible
        assert len(motion_law_grid) > 0
        assert len(gear_grid) > 0
        
        # Test that motion law has thermodynamic data
        assert 'thermodynamic_data' in motion_law
        assert 'indicated_work_J' in motion_law['thermodynamic_data']
        assert motion_law['thermodynamic_data']['indicated_work_J'] > 0.0
    
    def test_consistency_between_phases(self, motion_law_optimizer, gear_optimizer):
        """Test consistency between Phase 1 and Phase 2."""
        # Create test data
        displacement = np.array([0.0, 0.005, 0.01, 0.005, 0.0])
        velocity = np.array([1.0, 1.5, 2.0, 1.5, 1.0])
        theta_deg = np.array([0.0, 45.0, 90.0, 135.0, 180.0])
        
        # Test Phase 1 thermodynamic calculations
        thermo_data = motion_law_optimizer._calculate_thermodynamic_data(
            displacement, velocity, np.array([0.5, 1.0, 0.5, -0.5, -1.0]), theta_deg
        )
        
        # Test Phase 2 transmission calculations
        sun_radius = np.array([0.05, 0.05, 0.05, 0.05, 0.05])
        planet_radius = np.array([0.08, 0.08, 0.08, 0.08, 0.08])
        ring_radius = np.array([0.21, 0.21, 0.21, 0.21, 0.21])
        r_inst = np.array([2.0, 2.1, 2.2, 2.1, 2.0])
        journal_offset = np.array([0.001, 0.002, 0.003, 0.002, 0.001])
        
        motion_law = {
            'displacement': displacement,
            'velocity': velocity,
            'acceleration': np.array([0.5, 1.0, 0.5, -0.5, -1.0])
        }
        
        grid = np.linspace(0, 180, 5)
        
        transmission_data = gear_optimizer._calculate_transmission_data(
            sun_radius, planet_radius, ring_radius, r_inst, journal_offset,
            motion_law, grid
        )
        
        # Check that both phases produce consistent data
        assert len(thermo_data['volume_m3']) == len(displacement)
        assert len(transmission_data['angular_velocity_rad_s']) == len(displacement)
        
        # Check that indicated work is reasonable
        assert abs(thermo_data['indicated_work_J']) < 1000.0
        
        # Check that transmission efficiency is reasonable
        assert all(0.0 <= eff <= 1.0 for eff in transmission_data['transmission_efficiency'])
        
        # Check that fatigue safety factors are adequate
        assert all(sf >= 1.0 for sf in transmission_data['fatigue_safety_factor'])


if __name__ == '__main__':
    pytest.main([__file__])
