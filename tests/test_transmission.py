"""
Tests for transmission physics implementation.

This module tests the Phase 2 transmission physics including:
- Kinematic coupling: θ̇ = i(x)·ẋ
- Power balance: τ_out·θ̇ = F_p·ẋ − P_loss
- Transmission efficiency: η̂ = η/η̄
- Contact stress: Hertzian contact calculation
- Friction modeling: Stribeck friction model
- Fatigue constraints: SF = σ_lim/σ_max ≥ 1
"""

import pytest
import numpy as np
import casadi as ca

from campro.physics.transmission import (
    TransmissionParameters, KinematicCoupling, PowerBalance, 
    TransmissionEfficiency, ContactMechanics, FrictionModel, TransmissionOptimizer
)


class TestTransmissionParameters:
    """Test transmission parameters."""
    
    def test_default_parameters(self):
        """Test default parameter values."""
        params = TransmissionParameters()
        
        assert params.sun_radius_base_m == 0.05
        assert params.planet_radius_base_m == 0.08
        assert params.ring_radius_base_m == 0.21
        assert params.youngs_modulus_Pa == 200e9
        assert params.poisson_ratio == 0.3
        assert params.material_strength_Pa == 500e6
        assert params.static_friction_coeff == 0.1
        assert params.dynamic_friction_coeff == 0.08
        assert params.base_efficiency == 0.95
    
    def test_custom_parameters(self):
        """Test custom parameter values."""
        params = TransmissionParameters(
            sun_radius_base_m=0.06,
            planet_radius_base_m=0.09,
            youngs_modulus_Pa=210e9,
            static_friction_coeff=0.12
        )
        
        assert params.sun_radius_base_m == 0.06
        assert params.planet_radius_base_m == 0.09
        assert params.youngs_modulus_Pa == 210e9
        assert params.static_friction_coeff == 0.12


class TestKinematicCoupling:
    """Test kinematic coupling."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return TransmissionParameters()
    
    @pytest.fixture
    def kinematic_coupling(self, params):
        """Create kinematic coupling."""
        return KinematicCoupling(params)
    
    def test_instantaneous_ratio_calculation(self, kinematic_coupling):
        """Test instantaneous ratio calculation."""
        displacement = np.array([0.0, 0.05, 0.1])
        gear_radii = {
            'sun_radius': np.array([0.05, 0.05, 0.05]),
            'planet_radius': np.array([0.08, 0.08, 0.08]),
            'ring_radius': np.array([0.21, 0.21, 0.21])
        }
        
        instantaneous_ratio = kinematic_coupling.calculate_instantaneous_ratio(displacement, gear_radii)
        
        # Check that ratio is calculated correctly
        expected_ratio = gear_radii['ring_radius'] / gear_radii['sun_radius']
        np.testing.assert_array_almost_equal(instantaneous_ratio, expected_ratio, decimal=6)
    
    def test_instantaneous_ratio_calculation_casadi(self, kinematic_coupling):
        """Test instantaneous ratio calculation with CasADi."""
        displacement = ca.SX.sym('x', 3)
        gear_radii = {
            'sun_radius': ca.SX.sym('R_sun', 3),
            'planet_radius': ca.SX.sym('R_planet', 3),
            'ring_radius': ca.SX.sym('R_ring', 3)
        }
        
        instantaneous_ratio = kinematic_coupling.calculate_instantaneous_ratio_casadi(displacement, gear_radii)
        
        # Test with specific values
        displacement_val = np.array([0.0, 0.05, 0.1])
        gear_radii_val = {
            'sun_radius': np.array([0.05, 0.05, 0.05]),
            'planet_radius': np.array([0.08, 0.08, 0.08]),
            'ring_radius': np.array([0.21, 0.21, 0.21])
        }
        
        ratio_val = ca.Function('ratio', [displacement, gear_radii['sun_radius'], gear_radii['planet_radius'], gear_radii['ring_radius']], 
                               [instantaneous_ratio])(displacement_val, gear_radii_val['sun_radius'], 
                                                     gear_radii_val['planet_radius'], gear_radii_val['ring_radius'])
        
        # Convert CasADi DM to numpy array and flatten if needed
        if hasattr(ratio_val, 'full'):
            ratio_val = ratio_val.full().flatten()
        elif hasattr(ratio_val, 'toarray'):
            ratio_val = ratio_val.toarray().flatten()
        else:
            ratio_val = np.array(ratio_val).flatten()
        
        expected_ratio = gear_radii_val['ring_radius'] / gear_radii_val['sun_radius']
        np.testing.assert_array_almost_equal(ratio_val, expected_ratio, decimal=6)
    
    def test_angular_velocity_calculation(self, kinematic_coupling):
        """Test angular velocity calculation."""
        linear_velocity = np.array([1.0, 2.0, 3.0])
        instantaneous_ratio = np.array([2.0, 2.5, 3.0])
        
        angular_velocity = kinematic_coupling.calculate_angular_velocity(linear_velocity, instantaneous_ratio)
        
        # Check that angular velocity is calculated correctly
        expected_angular_velocity = instantaneous_ratio * linear_velocity
        np.testing.assert_array_almost_equal(angular_velocity, expected_angular_velocity, decimal=6)
    
    def test_angular_velocity_calculation_casadi(self, kinematic_coupling):
        """Test angular velocity calculation with CasADi."""
        linear_velocity = ca.SX.sym('v', 3)
        instantaneous_ratio = ca.SX.sym('i', 3)
        
        angular_velocity = kinematic_coupling.calculate_angular_velocity_casadi(linear_velocity, instantaneous_ratio)
        
        # Test with specific values
        linear_velocity_val = np.array([1.0, 2.0, 3.0])
        instantaneous_ratio_val = np.array([2.0, 2.5, 3.0])
        
        angular_velocity_val = ca.Function('angular_velocity', [linear_velocity, instantaneous_ratio], 
                                          [angular_velocity])(linear_velocity_val, instantaneous_ratio_val)
        
        # Convert CasADi DM to numpy array and flatten if needed
        if hasattr(angular_velocity_val, 'full'):
            angular_velocity_val = angular_velocity_val.full().flatten()
        elif hasattr(angular_velocity_val, 'toarray'):
            angular_velocity_val = angular_velocity_val.toarray().flatten()
        else:
            angular_velocity_val = np.array(angular_velocity_val).flatten()
        
        expected_angular_velocity = instantaneous_ratio_val * linear_velocity_val
        np.testing.assert_array_almost_equal(angular_velocity_val, expected_angular_velocity, decimal=6)
    
    def test_kinematic_constraints(self, kinematic_coupling):
        """Test kinematic constraints calculation."""
        displacement = np.array([0.0, 0.05, 0.1])
        velocity = np.array([1.0, 2.0, 3.0])
        gear_radii = {
            'sun_radius': np.array([0.05, 0.05, 0.05]),
            'planet_radius': np.array([0.08, 0.08, 0.08]),
            'ring_radius': np.array([0.21, 0.21, 0.21])
        }
        
        constraints = kinematic_coupling.calculate_kinematic_constraints(displacement, velocity, gear_radii)
        
        # Check that all required keys are present
        required_keys = ['instantaneous_ratio', 'angular_velocity_rad_s', 'ratio_bounds', 'angular_velocity_bounds']
        for key in required_keys:
            assert key in constraints
        
        # Check that bounds are reasonable
        assert np.all(constraints['ratio_bounds']['lower'] > 0.0)
        assert np.all(constraints['ratio_bounds']['upper'] > constraints['ratio_bounds']['lower'])


class TestPowerBalance:
    """Test power balance."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return TransmissionParameters()
    
    @pytest.fixture
    def power_balance(self, params):
        """Create power balance."""
        return PowerBalance(params)
    
    def test_piston_force_calculation(self, power_balance):
        """Test piston force calculation."""
        pressure = np.array([100000.0, 200000.0, 300000.0])
        piston_area = 0.01
        
        piston_force = power_balance.calculate_piston_force(pressure, piston_area)
        
        # Check that force is calculated correctly
        expected_force = pressure * piston_area
        np.testing.assert_array_almost_equal(piston_force, expected_force, decimal=6)
    
    def test_piston_force_calculation_casadi(self, power_balance):
        """Test piston force calculation with CasADi."""
        pressure = ca.SX.sym('p', 3)
        piston_area = 0.01
        
        piston_force = power_balance.calculate_piston_force_casadi(pressure, piston_area)
        
        # Test with specific values
        pressure_val = np.array([100000.0, 200000.0, 300000.0])
        force_val = ca.Function('force', [pressure], [piston_force])(pressure_val)
        
        # Convert CasADi DM to numpy array and flatten if needed
        if hasattr(force_val, 'full'):
            force_val = force_val.full().flatten()
        elif hasattr(force_val, 'toarray'):
            force_val = force_val.toarray().flatten()
        else:
            force_val = np.array(force_val).flatten()
        
        expected_force = pressure_val * piston_area
        np.testing.assert_array_almost_equal(force_val, expected_force, decimal=6)
    
    def test_output_torque_calculation(self, power_balance):
        """Test output torque calculation."""
        piston_force = np.array([1000.0, 2000.0, 3000.0])
        displacement = np.array([0.0, 0.05, 0.1])
        instantaneous_ratio = np.array([2.0, 2.5, 3.0])
        efficiency = np.array([0.95, 0.96, 0.97])
        
        output_torque = power_balance.calculate_output_torque(
            piston_force, displacement, instantaneous_ratio, efficiency)
        
        # Check that torque is calculated correctly
        expected_torque = piston_force * displacement * instantaneous_ratio * efficiency
        np.testing.assert_array_almost_equal(output_torque, expected_torque, decimal=6)
    
    def test_power_loss_calculation(self, power_balance):
        """Test power loss calculation."""
        velocity = np.array([1.0, 2.0, 3.0])
        angular_velocity = np.array([2.0, 5.0, 9.0])
        contact_force = np.array([100.0, 200.0, 300.0])
        
        power_loss = power_balance.calculate_power_loss(velocity, angular_velocity, contact_force)
        
        # Check that power loss is calculated
        assert isinstance(power_loss, np.ndarray)
        assert len(power_loss) == len(velocity)
        assert np.all(power_loss >= 0.0)  # Power loss should be non-negative
    
    def test_power_balance_constraints(self, power_balance):
        """Test power balance constraints calculation."""
        piston_force = np.array([1000.0, 2000.0, 3000.0])
        velocity = np.array([1.0, 2.0, 3.0])
        angular_velocity = np.array([2.0, 5.0, 9.0])
        output_torque = np.array([100.0, 200.0, 300.0])
        power_loss = np.array([10.0, 20.0, 30.0])
        
        constraints = power_balance.calculate_power_balance_constraints(
            piston_force, velocity, angular_velocity, output_torque, power_loss)
        
        # Check that all required keys are present
        required_keys = ['input_power_W', 'output_power_W', 'power_loss_W', 
                        'power_balance_residual_W', 'power_balance_tolerance_W']
        for key in required_keys:
            assert key in constraints
        
        # Check that power balance residual is calculated
        expected_input_power = piston_force * velocity
        expected_output_power = output_torque * angular_velocity
        expected_residual = expected_input_power - expected_output_power - power_loss
        
        np.testing.assert_array_almost_equal(constraints['input_power_W'], expected_input_power, decimal=6)
        np.testing.assert_array_almost_equal(constraints['output_power_W'], expected_output_power, decimal=6)
        np.testing.assert_array_almost_equal(constraints['power_balance_residual_W'], expected_residual, decimal=6)


class TestTransmissionEfficiency:
    """Test transmission efficiency."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return TransmissionParameters()
    
    @pytest.fixture
    def transmission_efficiency(self, params):
        """Create transmission efficiency."""
        return TransmissionEfficiency(params)
    
    def test_transmission_efficiency_calculation(self, transmission_efficiency):
        """Test transmission efficiency calculation."""
        contact_stress = np.array([100e6, 200e6, 300e6])
        velocity = np.array([1.0, 2.0, 3.0])
        angular_velocity = np.array([2.0, 5.0, 9.0])
        
        efficiency = transmission_efficiency.calculate_transmission_efficiency(
            contact_stress, velocity, angular_velocity)
        
        # Check that efficiency is calculated
        assert isinstance(efficiency, np.ndarray)
        assert len(efficiency) == len(contact_stress)
        assert np.all(efficiency >= 0.0)  # Efficiency should be non-negative
        assert np.all(efficiency <= 1.0)  # Efficiency should not exceed 1.0
    
    def test_transmission_efficiency_calculation_casadi(self, transmission_efficiency):
        """Test transmission efficiency calculation with CasADi."""
        contact_stress = ca.SX.sym('sigma', 3)
        velocity = ca.SX.sym('v', 3)
        angular_velocity = ca.SX.sym('omega', 3)
        
        efficiency = transmission_efficiency.calculate_transmission_efficiency_casadi(
            contact_stress, velocity, angular_velocity)
        
        # Test with specific values
        contact_stress_val = np.array([100e6, 200e6, 300e6])
        velocity_val = np.array([1.0, 2.0, 3.0])
        angular_velocity_val = np.array([2.0, 5.0, 9.0])
        
        efficiency_val = ca.Function('efficiency', [contact_stress, velocity, angular_velocity], 
                                   [efficiency])(contact_stress_val, velocity_val, angular_velocity_val)
        
        # Convert CasADi DM to numpy array and flatten if needed
        if hasattr(efficiency_val, 'full'):
            efficiency_val = efficiency_val.full().flatten()
        elif hasattr(efficiency_val, 'toarray'):
            efficiency_val = efficiency_val.toarray().flatten()
        else:
            efficiency_val = np.array(efficiency_val).flatten()
        
        # Check that efficiency is calculated
        assert isinstance(efficiency_val, np.ndarray)
        assert len(efficiency_val) == len(contact_stress_val)
        assert np.all(efficiency_val >= 0.0)
        assert np.all(efficiency_val <= 1.0)
    
    def test_efficiency_objectives(self, transmission_efficiency):
        """Test efficiency objectives calculation."""
        efficiency = np.array([0.95, 0.96, 0.97, 0.98, 0.99])
        
        objectives = transmission_efficiency.calculate_efficiency_objectives(efficiency)
        
        # Check that all required objectives are present
        required_objectives = ['mean_efficiency', 'min_efficiency', 'max_efficiency', 
                              'efficiency_variance', 'efficiency_std']
        for obj in required_objectives:
            assert obj in objectives
        
        # Check that objectives are reasonable
        assert objectives['mean_efficiency'] == np.mean(efficiency)
        assert objectives['min_efficiency'] == np.min(efficiency)
        assert objectives['max_efficiency'] == np.max(efficiency)
        assert objectives['efficiency_variance'] == np.var(efficiency)
        assert objectives['efficiency_std'] == np.std(efficiency)


class TestContactMechanics:
    """Test contact mechanics."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return TransmissionParameters()
    
    @pytest.fixture
    def contact_mechanics(self, params):
        """Create contact mechanics."""
        return ContactMechanics(params)
    
    def test_contact_stress_hertzian_calculation(self, contact_mechanics):
        """Test Hertzian contact stress calculation."""
        contact_force = np.array([1000.0, 2000.0, 3000.0])
        contact_radius = np.array([0.01, 0.01, 0.01])  # Same radius to isolate force effect
        
        contact_stress = contact_mechanics.calculate_contact_stress_hertzian(
            contact_force, contact_radius)
        
        # Check that stress is calculated
        assert isinstance(contact_stress, np.ndarray)
        assert len(contact_stress) == len(contact_force)
        assert np.all(contact_stress > 0.0)  # Stress should be positive
        
        # Check that stress increases with force (for same radius)
        # Note: stress should increase with force, but the relationship with radius is more complex
        assert contact_stress[0] < contact_stress[1] < contact_stress[2]
    
    def test_contact_stress_hertzian_calculation_casadi(self, contact_mechanics):
        """Test Hertzian contact stress calculation with CasADi."""
        contact_force = ca.SX.sym('F', 3)
        contact_radius = ca.SX.sym('R', 3)
        
        contact_stress = contact_mechanics.calculate_contact_stress_hertzian_casadi(
            contact_force, contact_radius)
        
        # Test with specific values
        contact_force_val = np.array([1000.0, 2000.0, 3000.0])
        contact_radius_val = np.array([0.01, 0.02, 0.03])
        
        stress_val = ca.Function('stress', [contact_force, contact_radius], 
                               [contact_stress])(contact_force_val, contact_radius_val)
        
        # Convert CasADi DM to numpy array and flatten if needed
        if hasattr(stress_val, 'full'):
            stress_val = stress_val.full().flatten()
        elif hasattr(stress_val, 'toarray'):
            stress_val = stress_val.toarray().flatten()
        else:
            stress_val = np.array(stress_val).flatten()
        
        # Check that stress is calculated
        assert isinstance(stress_val, np.ndarray)
        assert len(stress_val) == len(contact_force_val)
        assert np.all(stress_val > 0.0)
    
    def test_contact_force_calculation(self, contact_mechanics):
        """Test contact force calculation."""
        gear_radii = {
            'sun_radius': np.array([0.05, 0.05, 0.05]),
            'planet_radius': np.array([0.08, 0.08, 0.08]),
            'ring_radius': np.array([0.21, 0.21, 0.21])
        }
        displacement = np.array([0.0, 0.05, 0.1])
        
        contact_force = contact_mechanics.calculate_contact_force(gear_radii, displacement)
        
        # Check that force is calculated
        assert isinstance(contact_force, np.ndarray)
        assert len(contact_force) == len(displacement)
        assert np.all(contact_force >= 0.0)  # Force should be non-negative
    
    def test_fatigue_safety_factor_calculation(self, contact_mechanics):
        """Test fatigue safety factor calculation."""
        contact_stress = np.array([100e6, 200e6, 300e6])
        
        safety_factor = contact_mechanics.calculate_fatigue_safety_factor(contact_stress)
        
        # Check that safety factor is calculated
        assert isinstance(safety_factor, np.ndarray)
        assert len(safety_factor) == len(contact_stress)
        assert np.all(safety_factor > 0.0)  # Safety factor should be positive
        
        # Check that safety factor decreases with stress
        assert safety_factor[0] > safety_factor[1] > safety_factor[2]


class TestFrictionModel:
    """Test friction model."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return TransmissionParameters()
    
    @pytest.fixture
    def friction_model(self, params):
        """Create friction model."""
        return FrictionModel(params)
    
    def test_stribeck_friction_calculation(self, friction_model):
        """Test Stribeck friction calculation."""
        velocity = np.array([0.0, 0.01, 0.1, 1.0])
        normal_force = np.array([100.0, 200.0, 300.0, 400.0])
        
        friction_force = friction_model.calculate_stribeck_friction(velocity, normal_force)
        
        # Check that friction force is calculated
        assert isinstance(friction_force, np.ndarray)
        assert len(friction_force) == len(velocity)
        assert np.all(friction_force >= 0.0)  # Friction force should be non-negative
        
        # Check that friction force increases with normal force
        assert friction_force[0] < friction_force[1] < friction_force[2] < friction_force[3]
    
    def test_stribeck_friction_calculation_casadi(self, friction_model):
        """Test Stribeck friction calculation with CasADi."""
        velocity = ca.SX.sym('v', 4)
        normal_force = ca.SX.sym('F', 4)
        
        friction_force = friction_model.calculate_stribeck_friction_casadi(velocity, normal_force)
        
        # Test with specific values
        velocity_val = np.array([0.0, 0.01, 0.1, 1.0])
        normal_force_val = np.array([100.0, 200.0, 300.0, 400.0])
        
        friction_val = ca.Function('friction', [velocity, normal_force], 
                                  [friction_force])(velocity_val, normal_force_val)
        
        # Convert CasADi DM to numpy array and flatten if needed
        if hasattr(friction_val, 'full'):
            friction_val = friction_val.full().flatten()
        elif hasattr(friction_val, 'toarray'):
            friction_val = friction_val.toarray().flatten()
        else:
            friction_val = np.array(friction_val).flatten()
        
        # Check that friction force is calculated
        assert isinstance(friction_val, np.ndarray)
        assert len(friction_val) == len(velocity_val)
        assert np.all(friction_val >= 0.0)
    
    def test_friction_power_loss_calculation(self, friction_model):
        """Test friction power loss calculation."""
        friction_force = np.array([10.0, 20.0, 30.0])
        velocity = np.array([1.0, 2.0, 3.0])
        
        power_loss = friction_model.calculate_friction_power_loss(friction_force, velocity)
        
        # Check that power loss is calculated
        assert isinstance(power_loss, np.ndarray)
        assert len(power_loss) == len(friction_force)
        assert np.all(power_loss >= 0.0)  # Power loss should be non-negative
        
        # Check that power loss increases with force and velocity
        expected_power_loss = friction_force * np.abs(velocity)
        np.testing.assert_array_almost_equal(power_loss, expected_power_loss, decimal=6)


class TestTransmissionOptimizer:
    """Test transmission optimizer."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return TransmissionParameters()
    
    @pytest.fixture
    def optimizer(self, params):
        """Create transmission optimizer."""
        return TransmissionOptimizer(params)
    
    def test_transmission_objectives(self, optimizer):
        """Test transmission objectives calculation."""
        displacement = np.array([0.0, 0.05, 0.1])
        velocity = np.array([1.0, 2.0, 3.0])
        pressure = np.array([100000.0, 200000.0, 300000.0])
        gear_radii = {
            'sun_radius': np.array([0.05, 0.05, 0.05]),
            'planet_radius': np.array([0.08, 0.08, 0.08]),
            'ring_radius': np.array([0.21, 0.21, 0.21])
        }
        
        objectives = optimizer.calculate_transmission_objectives(
            displacement, velocity, pressure, gear_radii)
        
        # Check that all required objectives are present
        required_objectives = ['mean_efficiency', 'min_efficiency', 'max_contact_stress_Pa',
                              'mean_contact_stress_Pa', 'max_output_torque_Nm', 'mean_output_torque_Nm',
                              'total_friction_power_loss_W', 'mean_friction_power_loss_W']
        for obj in required_objectives:
            assert obj in objectives
        
        # Check that objectives are reasonable
        assert 0.0 <= objectives['mean_efficiency'] <= 1.0
        assert 0.0 <= objectives['min_efficiency'] <= 1.0
        assert objectives['max_contact_stress_Pa'] > 0.0
        assert objectives['mean_contact_stress_Pa'] > 0.0
        assert objectives['max_output_torque_Nm'] > 0.0
        assert objectives['mean_output_torque_Nm'] > 0.0
        assert objectives['total_friction_power_loss_W'] >= 0.0
        assert objectives['mean_friction_power_loss_W'] >= 0.0
    
    def test_transmission_constraints(self, optimizer):
        """Test transmission constraints calculation."""
        displacement = np.array([0.0, 0.05, 0.1])
        velocity = np.array([1.0, 2.0, 3.0])
        pressure = np.array([100000.0, 200000.0, 300000.0])
        gear_radii = {
            'sun_radius': np.array([0.05, 0.05, 0.05]),
            'planet_radius': np.array([0.08, 0.08, 0.08]),
            'ring_radius': np.array([0.21, 0.21, 0.21])
        }
        
        constraints = optimizer.calculate_transmission_constraints(
            displacement, velocity, pressure, gear_radii)
        
        # Check that all required constraints are present
        required_constraints = ['kinematic_constraints', 'contact_stress_Pa', 'fatigue_safety_factor',
                               'power_balance_constraints', 'contact_force_N', 'safety_factor_bounds']
        for constraint in required_constraints:
            assert constraint in constraints
        
        # Check that constraints are reasonable
        assert np.all(constraints['contact_stress_Pa'] > 0.0)
        assert np.all(constraints['fatigue_safety_factor'] > 0.0)
        assert np.all(constraints['contact_force_N'] >= 0.0)
        assert np.all(constraints['safety_factor_bounds']['lower'] >= 1.0)  # SF ≥ 1


class TestIntegration:
    """Test integration between components."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return TransmissionParameters()
    
    @pytest.fixture
    def optimizer(self, params):
        """Create transmission optimizer."""
        return TransmissionOptimizer(params)
    
    def test_full_transmission_analysis(self, optimizer):
        """Test complete transmission analysis."""
        displacement = np.array([0.0, 0.025, 0.05, 0.075, 0.1])
        velocity = np.array([1.0, 1.5, 2.0, 1.5, 1.0])
        pressure = np.array([100000.0, 150000.0, 200000.0, 150000.0, 100000.0])
        gear_radii = {
            'sun_radius': np.array([0.05, 0.05, 0.05, 0.05, 0.05]),
            'planet_radius': np.array([0.08, 0.08, 0.08, 0.08, 0.08]),
            'ring_radius': np.array([0.21, 0.21, 0.21, 0.21, 0.21])
        }
        
        # Calculate objectives
        objectives = optimizer.calculate_transmission_objectives(
            displacement, velocity, pressure, gear_radii)
        
        # Calculate constraints
        constraints = optimizer.calculate_transmission_constraints(
            displacement, velocity, pressure, gear_radii)
        
        # Check that both calculations work together
        assert len(objectives) > 0
        assert len(constraints) > 0
        
        # Check that efficiency is reasonable
        assert 0.0 <= objectives['mean_efficiency'] <= 1.0
        
        # Check that safety factors are adequate
        assert np.all(constraints['fatigue_safety_factor'] >= 1.0)
    
    def test_consistency_between_components(self, optimizer):
        """Test consistency between different components."""
        displacement = np.array([0.0, 0.05, 0.1])
        velocity = np.array([1.0, 2.0, 3.0])
        pressure = np.array([100000.0, 200000.0, 300000.0])
        gear_radii = {
            'sun_radius': np.array([0.05, 0.05, 0.05]),
            'planet_radius': np.array([0.08, 0.08, 0.08]),
            'ring_radius': np.array([0.21, 0.21, 0.21])
        }
        
        # Calculate using different methods
        kinematic_constraints = optimizer.kinematic_coupling.calculate_kinematic_constraints(
            displacement, velocity, gear_radii)
        objectives = optimizer.calculate_transmission_objectives(
            displacement, velocity, pressure, gear_radii)
        
        # Check that instantaneous ratio is consistent
        assert 'instantaneous_ratio' in kinematic_constraints
        assert len(kinematic_constraints['instantaneous_ratio']) == len(displacement)
        
        # Check that efficiency is calculated
        assert 'mean_efficiency' in objectives
        assert 0.0 <= objectives['mean_efficiency'] <= 1.0


if __name__ == '__main__':
    pytest.main([__file__])
