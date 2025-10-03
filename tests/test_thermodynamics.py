"""
Tests for thermodynamic foundation implementation.

This module tests the Phase 1 thermodynamic calculations including:
- Volume calculation: V(t) = V_c + A_p x(t)
- Pressure calculation: Polytropic process pV^γ = const
- Temperature modeling: From ideal gas law
- Indicated work: W_id = ∮ p dV
- Valve modeling: Lift profiles, timing, constraints
- Combustion modeling: Wiebe function, heat release
- State equations: Mass/energy balance
"""

import pytest
import numpy as np
import casadi as ca

from campro.physics.thermodynamics import (
    ThermodynamicParameters, ThermodynamicCalculator, ValveModel, 
    CombustionModel, StateEquations, ThermodynamicOptimizer
)


class TestThermodynamicParameters:
    """Test thermodynamic parameters."""
    
    def test_default_parameters(self):
        """Test default parameter values."""
        params = ThermodynamicParameters()
        
        assert params.piston_area_m2 == 0.01
        assert params.clearance_volume_m3 == 0.001
        assert params.stroke_length_m == 0.1
        assert params.gamma == 1.35
        assert params.gas_constant == 287.0
        assert params.ambient_temperature_K == 298.15
        assert params.ambient_pressure_Pa == 101325.0
    
    def test_custom_parameters(self):
        """Test custom parameter values."""
        params = ThermodynamicParameters(
            piston_area_m2=0.02,
            clearance_volume_m3=0.002,
            gamma=1.4
        )
        
        assert params.piston_area_m2 == 0.02
        assert params.clearance_volume_m3 == 0.002
        assert params.gamma == 1.4
    
    def test_valve_timing_defaults(self):
        """Test default valve timing values."""
        params = ThermodynamicParameters()
        
        assert 'intake_open' in params.valve_timing_deg
        assert 'intake_close' in params.valve_timing_deg
        assert 'exhaust_open' in params.valve_timing_deg
        assert 'exhaust_close' in params.valve_timing_deg


class TestThermodynamicCalculator:
    """Test thermodynamic calculator."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return ThermodynamicParameters(
            piston_area_m2=0.01,
            clearance_volume_m3=0.001,
            gamma=1.35
        )
    
    @pytest.fixture
    def calculator(self, params):
        """Create thermodynamic calculator."""
        return ThermodynamicCalculator(params)
    
    def test_volume_calculation(self, calculator):
        """Test volume calculation."""
        displacement = np.array([0.0, 0.05, 0.1])
        volume = calculator.calculate_volume(displacement)
        
        expected_volume = np.array([0.001, 0.0015, 0.002])
        np.testing.assert_array_almost_equal(volume, expected_volume, decimal=6)
    
    def test_volume_calculation_casadi(self, calculator):
        """Test volume calculation with CasADi."""
        displacement = ca.SX.sym('x', 3)
        volume = calculator.calculate_volume_casadi(displacement)
        
        # Test with specific values
        displacement_val = np.array([0.0, 0.05, 0.1])
        volume_val = ca.Function('volume', [displacement], [volume])(displacement_val)
        
        expected_volume = np.array([0.001, 0.0015, 0.002])
        # Handle CasADi DM array shape differences
        volume_val_flat = np.array(volume_val).flatten()
        np.testing.assert_array_almost_equal(volume_val_flat, expected_volume, decimal=6)
    
    def test_pressure_calculation(self, calculator):
        """Test pressure calculation using polytropic process."""
        volume = np.array([0.001, 0.0015, 0.002])
        pressure = calculator.calculate_pressure_polytropic(volume)
        
        # Check that pressure decreases as volume increases
        assert pressure[0] > pressure[1] > pressure[2]
        
        # Check that pressure is positive
        assert np.all(pressure > 0)
    
    def test_pressure_calculation_casadi(self, calculator):
        """Test pressure calculation with CasADi."""
        volume = ca.SX.sym('V', 3)
        pressure = calculator.calculate_pressure_polytropic_casadi(volume)
        
        # Test with specific values
        volume_val = np.array([0.001, 0.0015, 0.002])
        pressure_val = ca.Function('pressure', [volume], [pressure])(volume_val)
        
        # Check that pressure decreases as volume increases
        assert pressure_val[0] > pressure_val[1] > pressure_val[2]
        
        # Check that pressure is positive
        assert np.all(pressure_val > 0)
    
    def test_temperature_calculation(self, calculator):
        """Test temperature calculation."""
        pressure = np.array([101325.0, 80000.0, 60000.0])
        volume = np.array([0.001, 0.0015, 0.002])
        temperature = calculator.calculate_temperature(pressure, volume)
        
        # Check that temperature is positive
        assert np.all(temperature > 0)
        
        # Check that temperature is reasonable (not too high or too low)
        assert np.all(temperature > 100.0)  # Above 100K
        assert np.all(temperature < 5000.0)  # Below 5000K
    
    def test_indicated_work_calculation(self, calculator):
        """Test indicated work calculation."""
        pressure = np.array([101325.0, 80000.0, 60000.0])
        volume = np.array([0.001, 0.0015, 0.002])
        work = calculator.calculate_indicated_work(pressure, volume)
        
        # Check that work is calculated
        assert isinstance(work, float)
        assert not np.isnan(work)
        assert not np.isinf(work)
    
    def test_indicated_work_calculation_casadi(self, calculator):
        """Test indicated work calculation with CasADi."""
        pressure = ca.SX.sym('p', 3)
        volume = ca.SX.sym('V', 3)
        work = calculator.calculate_indicated_work_casadi(pressure, volume)
        
        # Test with specific values
        pressure_val = np.array([101325.0, 80000.0, 60000.0])
        volume_val = np.array([0.001, 0.0015, 0.002])
        work_val = ca.Function('work', [pressure, volume], [work])(pressure_val, volume_val)
        
        # Check that work is calculated (CasADi returns DM, not float)
        assert hasattr(work_val, '__float__') or isinstance(work_val, (float, int))
        assert not np.isnan(work_val)
        assert not np.isinf(work_val)
    
    def test_thermodynamic_cycle(self, calculator):
        """Test complete thermodynamic cycle calculation."""
        displacement = np.array([0.0, 0.05, 0.1, 0.05, 0.0])
        theta_deg = np.array([0.0, 45.0, 90.0, 135.0, 180.0])
        
        cycle = calculator.calculate_thermodynamic_cycle(displacement, theta_deg)
        
        # Check that all required keys are present
        required_keys = ['volume_m3', 'pressure_Pa', 'temperature_K', 
                        'indicated_work_J', 'valve_lift_m', 'heat_release_J']
        for key in required_keys:
            assert key in cycle
        
        # Check that all values are arrays
        for key, value in cycle.items():
            if key == 'indicated_work_J':  # This is a scalar
                assert isinstance(value, (int, float, np.number))
            elif key in ['valve_lift_m']:  # This is a dictionary
                assert isinstance(value, dict)
                for valve_key, valve_value in value.items():
                    assert isinstance(valve_value, np.ndarray)
                    assert len(valve_value) == len(displacement)
            else:  # Regular arrays
                assert isinstance(value, np.ndarray)
                assert len(value) == len(displacement)


class TestValveModel:
    """Test valve modeling."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return ThermodynamicParameters(
            max_valve_lift_m=0.01,
            valve_timing_deg={
                'intake_open': -10.0,
                'intake_close': 40.0,
                'exhaust_open': 50.0,
                'exhaust_close': 10.0
            }
        )
    
    @pytest.fixture
    def valve_model(self, params):
        """Create valve model."""
        return ValveModel(params)
    
    def test_valve_lift_profiles(self, valve_model):
        """Test valve lift profile calculation."""
        theta_deg = np.linspace(0, 360, 37)  # 10-degree steps
        valve_lift = valve_model.calculate_valve_lift_profiles(theta_deg)
        
        # Check that both intake and exhaust profiles are calculated
        assert 'intake_lift_m' in valve_lift
        assert 'exhaust_lift_m' in valve_lift
        
        # Check that lift values are within bounds
        assert np.all(valve_lift['intake_lift_m'] >= 0.0)
        assert np.all(valve_lift['intake_lift_m'] <= 0.01)
        assert np.all(valve_lift['exhaust_lift_m'] >= 0.0)
        assert np.all(valve_lift['exhaust_lift_m'] <= 0.01)
    
    def test_valve_constraints(self, valve_model):
        """Test valve constraint calculation."""
        theta_deg = np.linspace(0, 360, 37)
        constraints = valve_model.calculate_valve_constraints(theta_deg)
        
        # Check that all required keys are present
        required_keys = ['intake_bounds', 'exhaust_bounds', 'intake_lift', 'exhaust_lift']
        for key in required_keys:
            assert key in constraints
        
        # Check that bounds are correct
        assert np.all(constraints['intake_bounds']['lower'] == 0.0)
        assert np.all(constraints['intake_bounds']['upper'] == 0.01)
        assert np.all(constraints['exhaust_bounds']['lower'] == 0.0)
        assert np.all(constraints['exhaust_bounds']['upper'] == 0.01)


class TestCombustionModel:
    """Test combustion modeling."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return ThermodynamicParameters(
            combustion_efficiency=0.95,
            heat_release_fraction=0.8,
            ignition_timing_deg=-15.0
        )
    
    @pytest.fixture
    def combustion_model(self, params):
        """Create combustion model."""
        return CombustionModel(params)
    
    def test_combustion_heat_release(self, combustion_model):
        """Test combustion heat release calculation."""
        theta_deg = np.linspace(0, 360, 37)
        heat_release = combustion_model.calculate_combustion_heat_release(theta_deg)
        
        # Check that heat release is calculated
        assert isinstance(heat_release, np.ndarray)
        assert len(heat_release) == len(theta_deg)
        
        # Check that heat release is non-negative
        assert np.all(heat_release >= 0.0)
    
    def test_combustion_constraints(self, combustion_model):
        """Test combustion constraint calculation."""
        theta_deg = np.linspace(0, 360, 37)
        constraints = combustion_model.calculate_combustion_constraints(theta_deg)
        
        # Check that all required keys are present
        required_keys = ['heat_release_J', 'max_heat_release_J', 'min_heat_release_J']
        for key in required_keys:
            assert key in constraints
        
        # Check that constraints are reasonable
        assert constraints['min_heat_release_J'] == 0.0
        assert constraints['max_heat_release_J'] > 0.0


class TestStateEquations:
    """Test state equations."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return ThermodynamicParameters()
    
    @pytest.fixture
    def state_eqns(self, params):
        """Create state equations."""
        return StateEquations(params)
    
    def test_mass_balance(self, state_eqns):
        """Test mass balance calculation."""
        volume = np.array([0.001, 0.0015, 0.002])
        pressure = np.array([101325.0, 80000.0, 60000.0])
        temperature = np.array([298.15, 300.0, 302.0])
        valve_lift = {'intake_lift_m': np.array([0.0, 0.01, 0.0]),
                     'exhaust_lift_m': np.array([0.0, 0.0, 0.01])}
        
        mass_flow = state_eqns.calculate_mass_balance(volume, pressure, temperature, valve_lift)
        
        # Check that mass flow is calculated
        assert isinstance(mass_flow, np.ndarray)
        assert len(mass_flow) == len(volume)
    
    def test_energy_balance(self, state_eqns):
        """Test energy balance calculation."""
        volume = np.array([0.001, 0.0015, 0.002])
        pressure = np.array([101325.0, 80000.0, 60000.0])
        temperature = np.array([298.15, 300.0, 302.0])
        heat_release = np.array([0.0, 1000.0, 0.0])
        
        energy_balance = state_eqns.calculate_energy_balance(volume, pressure, temperature, heat_release)
        
        # Check that energy balance is calculated
        assert isinstance(energy_balance, np.ndarray)
        assert len(energy_balance) == len(volume)
    
    def test_collocation_defects(self, state_eqns):
        """Test collocation defects calculation."""
        state_variables = {
            'pressure': np.array([101325.0, 80000.0, 60000.0]),
            'temperature': np.array([298.15, 300.0, 302.0])
        }
        grid = np.array([0.0, 0.5, 1.0])
        
        defects = state_eqns.calculate_collocation_defects(state_variables, grid)
        
        # Check that defects are calculated
        assert isinstance(defects, dict)
        assert len(defects) > 0


class TestThermodynamicOptimizer:
    """Test thermodynamic optimizer."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return ThermodynamicParameters(
            piston_area_m2=0.01,
            clearance_volume_m3=0.001,
            gamma=1.35
        )
    
    @pytest.fixture
    def optimizer(self, params):
        """Create thermodynamic optimizer."""
        return ThermodynamicOptimizer(params)
    
    def test_thermodynamic_objectives(self, optimizer):
        """Test thermodynamic objectives calculation."""
        displacement = np.array([0.0, 0.05, 0.1, 0.05, 0.0])
        theta_deg = np.array([0.0, 45.0, 90.0, 135.0, 180.0])
        
        objectives = optimizer.calculate_thermodynamic_objectives(displacement, theta_deg)
        
        # Check that all required objectives are present
        required_objectives = ['indicated_work_J', 'max_pressure_Pa', 'min_pressure_Pa',
                              'max_temperature_K', 'min_temperature_K', 'volumetric_efficiency',
                              'thermal_efficiency']
        for obj in required_objectives:
            assert obj in objectives
        
        # Check that objectives are reasonable
        assert abs(objectives['indicated_work_J']) < 1000.0  # Should be reasonable magnitude
        assert objectives['max_pressure_Pa'] > objectives['min_pressure_Pa']
        assert objectives['max_temperature_K'] > objectives['min_temperature_K']
        assert 0.0 <= objectives['volumetric_efficiency'] <= 1.0
        assert 0.0 <= objectives['thermal_efficiency'] <= 1.0
    
    def test_thermodynamic_constraints(self, optimizer):
        """Test thermodynamic constraints calculation."""
        displacement = np.array([0.0, 0.05, 0.1, 0.05, 0.0])
        theta_deg = np.array([0.0, 45.0, 90.0, 135.0, 180.0])
        
        constraints = optimizer.calculate_thermodynamic_constraints(displacement, theta_deg)
        
        # Check that all required constraints are present
        required_constraints = ['valve_constraints', 'combustion_constraints', 
                               'pressure_bounds', 'temperature_bounds']
        for constraint in required_constraints:
            assert constraint in constraints
        
        # Check that bounds are reasonable
        assert np.all(constraints['pressure_bounds']['lower'] > 0.0)
        assert np.all(constraints['pressure_bounds']['upper'] > constraints['pressure_bounds']['lower'])
        assert np.all(constraints['temperature_bounds']['lower'] > 0.0)
        assert np.all(constraints['temperature_bounds']['upper'] > constraints['temperature_bounds']['lower'])


class TestIntegration:
    """Test integration between components."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return ThermodynamicParameters(
            piston_area_m2=0.01,
            clearance_volume_m3=0.001,
            gamma=1.35,
            max_valve_lift_m=0.01,
            combustion_efficiency=0.95
        )
    
    @pytest.fixture
    def optimizer(self, params):
        """Create thermodynamic optimizer."""
        return ThermodynamicOptimizer(params)
    
    def test_full_thermodynamic_cycle(self, optimizer):
        """Test complete thermodynamic cycle calculation."""
        # Create a simple compression-expansion cycle
        displacement = np.array([0.0, 0.025, 0.05, 0.075, 0.1, 0.075, 0.05, 0.025, 0.0])
        theta_deg = np.array([0.0, 22.5, 45.0, 67.5, 90.0, 112.5, 135.0, 157.5, 180.0])
        
        # Calculate objectives
        objectives = optimizer.calculate_thermodynamic_objectives(displacement, theta_deg)
        
        # Calculate constraints
        constraints = optimizer.calculate_thermodynamic_constraints(displacement, theta_deg)
        
        # Check that both calculations work together
        assert len(objectives) > 0
        assert len(constraints) > 0
        
        # Check that indicated work is reasonable (net work output)
        assert abs(objectives['indicated_work_J']) < 1000.0  # Should be reasonable magnitude
    
    def test_consistency_between_components(self, optimizer):
        """Test consistency between different components."""
        displacement = np.array([0.0, 0.05, 0.1])
        theta_deg = np.array([0.0, 45.0, 90.0])
        
        # Calculate using different methods
        cycle = optimizer.thermo_calc.calculate_thermodynamic_cycle(displacement, theta_deg)
        objectives = optimizer.calculate_thermodynamic_objectives(displacement, theta_deg)
        
        # Check that indicated work is consistent
        assert abs(cycle['indicated_work_J'] - objectives['indicated_work_J']) < 1e-6
        
        # Check that pressure values are consistent
        assert abs(np.max(cycle['pressure_Pa']) - objectives['max_pressure_Pa']) < 1e-6
        assert abs(np.min(cycle['pressure_Pa']) - objectives['min_pressure_Pa']) < 1e-6


if __name__ == '__main__':
    pytest.main([__file__])
