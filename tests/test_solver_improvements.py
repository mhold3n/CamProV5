"""
Tests for solver improvements implementation.

This module tests the global solver improvements including:
- Objective normalization: All objectives should be unitless
- Variable scaling: Variables need reference scaling
- Continuation strategy: 3-stage homotopy missing
- Convergence diagnostics: KKT error, constraint violations
"""

import pytest
import numpy as np
import casadi as ca

from campro.optimization.solver_improvements import (
    SolverParameters, ObjectiveNormalizer, VariableScaler, 
    ContinuationStrategy, ConvergenceDiagnostics, SolverImprovements
)


class TestSolverParameters:
    """Test solver parameters."""
    
    def test_default_parameters(self):
        """Test default parameter values."""
        params = SolverParameters()
        
        assert params.reference_work_J == 1000.0
        assert params.reference_pressure_Pa == 1000000.0
        assert params.reference_velocity_mps == 10.0
        assert params.reference_acceleration_mps2 == 100.0
        assert params.reference_force_N == 10000.0
        assert params.reference_torque_Nm == 1000.0
        assert params.reference_power_W == 10000.0
        assert params.reference_efficiency == 0.95
        assert params.variable_scaling_enabled
        assert params.objective_scaling_enabled
        assert params.constraint_scaling_enabled
        assert params.continuation_enabled
        assert params.continuation_steps == 3
        assert params.diagnostics_enabled
    
    def test_custom_parameters(self):
        """Test custom parameter values."""
        params = SolverParameters(
            reference_work_J=2000.0,
            reference_pressure_Pa=2000000.0,
            continuation_steps=5,
            variable_scaling_enabled=False
        )
        
        assert params.reference_work_J == 2000.0
        assert params.reference_pressure_Pa == 2000000.0
        assert params.continuation_steps == 5
        assert not params.variable_scaling_enabled


class TestObjectiveNormalizer:
    """Test objective normalization."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return SolverParameters()
    
    @pytest.fixture
    def normalizer(self, params):
        """Create objective normalizer."""
        return ObjectiveNormalizer(params)
    
    def test_work_normalization(self, normalizer):
        """Test work objective normalization."""
        work_J = 1500.0
        normalized_work = normalizer.normalize_work_objective(work_J)
        
        expected_normalized = work_J / 1000.0  # reference_work_J
        assert abs(normalized_work - expected_normalized) < 1e-6
    
    def test_work_normalization_array(self, normalizer):
        """Test work objective normalization with array."""
        work_J = np.array([1000.0, 1500.0, 2000.0])
        normalized_work = normalizer.normalize_work_objective(work_J)
        
        expected_normalized = work_J / 1000.0
        np.testing.assert_array_almost_equal(normalized_work, expected_normalized, decimal=6)
    
    def test_work_normalization_casadi(self, normalizer):
        """Test work objective normalization with CasADi."""
        work_J = ca.SX.sym('W', 3)
        normalized_work = normalizer.normalize_work_objective(work_J)
        
        # Test with specific values
        work_val = np.array([1000.0, 1500.0, 2000.0])
        normalized_val = ca.Function('normalized_work', [work_J], [normalized_work])(work_val)
        
        # Convert CasADi DM to numpy array and flatten if needed
        if hasattr(normalized_val, 'full'):
            normalized_val = normalized_val.full().flatten()
        elif hasattr(normalized_val, 'toarray'):
            normalized_val = normalized_val.toarray().flatten()
        else:
            normalized_val = np.array(normalized_val).flatten()
        
        expected_normalized = work_val / 1000.0
        np.testing.assert_array_almost_equal(normalized_val, expected_normalized, decimal=6)
    
    def test_pressure_normalization(self, normalizer):
        """Test pressure objective normalization."""
        pressure_Pa = 1500000.0
        normalized_pressure = normalizer.normalize_pressure_objective(pressure_Pa)
        
        expected_normalized = pressure_Pa / 1000000.0  # reference_pressure_Pa
        assert abs(normalized_pressure - expected_normalized) < 1e-6
    
    def test_velocity_normalization(self, normalizer):
        """Test velocity objective normalization."""
        velocity_mps = 15.0
        normalized_velocity = normalizer.normalize_velocity_objective(velocity_mps)
        
        expected_normalized = velocity_mps / 10.0  # reference_velocity_mps
        assert abs(normalized_velocity - expected_normalized) < 1e-6
    
    def test_acceleration_normalization(self, normalizer):
        """Test acceleration objective normalization."""
        acceleration_mps2 = 150.0
        normalized_acceleration = normalizer.normalize_acceleration_objective(acceleration_mps2)
        
        expected_normalized = acceleration_mps2 / 100.0  # reference_acceleration_mps2
        assert abs(normalized_acceleration - expected_normalized) < 1e-6
    
    def test_force_normalization(self, normalizer):
        """Test force objective normalization."""
        force_N = 15000.0
        normalized_force = normalizer.normalize_force_objective(force_N)
        
        expected_normalized = force_N / 10000.0  # reference_force_N
        assert abs(normalized_force - expected_normalized) < 1e-6
    
    def test_torque_normalization(self, normalizer):
        """Test torque objective normalization."""
        torque_Nm = 1500.0
        normalized_torque = normalizer.normalize_torque_objective(torque_Nm)
        
        expected_normalized = torque_Nm / 1000.0  # reference_torque_Nm
        assert abs(normalized_torque - expected_normalized) < 1e-6
    
    def test_power_normalization(self, normalizer):
        """Test power objective normalization."""
        power_W = 15000.0
        normalized_power = normalizer.normalize_power_objective(power_W)
        
        expected_normalized = power_W / 10000.0  # reference_power_W
        assert abs(normalized_power - expected_normalized) < 1e-6
    
    def test_efficiency_normalization(self, normalizer):
        """Test efficiency objective normalization."""
        efficiency = 0.9
        normalized_efficiency = normalizer.normalize_efficiency_objective(efficiency)
        
        expected_normalized = efficiency / 0.95  # reference_efficiency
        assert abs(normalized_efficiency - expected_normalized) < 1e-6
    
    def test_normalize_objectives_dict(self, normalizer):
        """Test normalization of objectives dictionary."""
        objectives = {
            'work_J': 1500.0,
            'pressure_Pa': 1500000.0,
            'velocity_mps': 15.0,
            'efficiency': 0.9,
            'other_value': 100.0
        }
        
        normalized_objectives = normalizer.normalize_objectives(objectives)
        
        # Check that known objectives are normalized
        assert abs(normalized_objectives['work_J'] - 1.5) < 1e-6
        assert abs(normalized_objectives['pressure_Pa'] - 1.5) < 1e-6
        assert abs(normalized_objectives['velocity_mps'] - 1.5) < 1e-6
        assert abs(normalized_objectives['efficiency'] - 0.9/0.95) < 1e-6
        
        # Check that unknown objectives are unchanged
        assert normalized_objectives['other_value'] == 100.0


class TestVariableScaler:
    """Test variable scaling."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return SolverParameters()
    
    @pytest.fixture
    def scaler(self, params):
        """Create variable scaler."""
        return VariableScaler(params)
    
    def test_displacement_scaling(self, scaler):
        """Test displacement variable scaling."""
        displacement_m = 0.15
        scaled_displacement = scaler.scale_displacement(displacement_m)
        
        expected_scaled = displacement_m / 0.1  # reference_displacement
        assert abs(scaled_displacement - expected_scaled) < 1e-6
    
    def test_displacement_scaling_array(self, scaler):
        """Test displacement variable scaling with array."""
        displacement_m = np.array([0.05, 0.1, 0.15])
        scaled_displacement = scaler.scale_displacement(displacement_m)
        
        expected_scaled = displacement_m / 0.1
        np.testing.assert_array_almost_equal(scaled_displacement, expected_scaled, decimal=6)
    
    def test_displacement_scaling_casadi(self, scaler):
        """Test displacement variable scaling with CasADi."""
        displacement_m = ca.SX.sym('x', 3)
        scaled_displacement = scaler.scale_displacement(displacement_m)
        
        # Test with specific values
        displacement_val = np.array([0.05, 0.1, 0.15])
        scaled_val = ca.Function('scaled_displacement', [displacement_m], [scaled_displacement])(displacement_val)
        
        # Convert CasADi DM to numpy array and flatten if needed
        if hasattr(scaled_val, 'full'):
            scaled_val = scaled_val.full().flatten()
        elif hasattr(scaled_val, 'toarray'):
            scaled_val = scaled_val.toarray().flatten()
        else:
            scaled_val = np.array(scaled_val).flatten()
        
        expected_scaled = displacement_val / 0.1
        np.testing.assert_array_almost_equal(scaled_val, expected_scaled, decimal=6)
    
    def test_velocity_scaling(self, scaler):
        """Test velocity variable scaling."""
        velocity_mps = 15.0
        scaled_velocity = scaler.scale_velocity(velocity_mps)
        
        expected_scaled = velocity_mps / 10.0  # reference_velocity_mps
        assert abs(scaled_velocity - expected_scaled) < 1e-6
    
    def test_acceleration_scaling(self, scaler):
        """Test acceleration variable scaling."""
        acceleration_mps2 = 150.0
        scaled_acceleration = scaler.scale_acceleration(acceleration_mps2)
        
        expected_scaled = acceleration_mps2 / 100.0  # reference_acceleration_mps2
        assert abs(scaled_acceleration - expected_scaled) < 1e-6
    
    def test_pressure_scaling(self, scaler):
        """Test pressure variable scaling."""
        pressure_Pa = 1500000.0
        scaled_pressure = scaler.scale_pressure(pressure_Pa)
        
        expected_scaled = pressure_Pa / 1000000.0  # reference_pressure_Pa
        assert abs(scaled_pressure - expected_scaled) < 1e-6
    
    def test_gear_radius_scaling(self, scaler):
        """Test gear radius variable scaling."""
        radius_m = 0.15
        scaled_radius = scaler.scale_gear_radius(radius_m)
        
        expected_scaled = radius_m / 0.1  # reference_radius
        assert abs(scaled_radius - expected_scaled) < 1e-6
    
    def test_scale_variables_dict(self, scaler):
        """Test scaling of variables dictionary."""
        variables = {
            'displacement_m': 0.15,
            'velocity_mps': 15.0,
            'pressure_Pa': 1500000.0,
            'radius_m': 0.15,
            'other_value': 100.0
        }
        
        scaled_variables = scaler.scale_variables(variables)
        
        # Check that known variables are scaled
        assert abs(scaled_variables['displacement_m'] - 1.5) < 1e-6
        assert abs(scaled_variables['velocity_mps'] - 1.5) < 1e-6
        assert abs(scaled_variables['pressure_Pa'] - 1.5) < 1e-6
        assert abs(scaled_variables['radius_m'] - 1.5) < 1e-6
        
        # Check that unknown variables are unchanged
        assert scaled_variables['other_value'] == 100.0


class TestContinuationStrategy:
    """Test continuation strategy."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return SolverParameters()
    
    @pytest.fixture
    def continuation_strategy(self, params):
        """Create continuation strategy."""
        return ContinuationStrategy(params)
    
    def test_create_continuation_sequence(self, continuation_strategy):
        """Test creation of continuation sequence."""
        base_problem = {
            'f': ca.SX.sym('f'),
            'g': ca.SX.sym('g', 3),
            'lbx': [0.0, 0.0, 0.0],
            'ubx': [1.0, 1.0, 1.0],
            'lbg': [0.0, 0.0, 0.0],
            'ubg': [1.0, 1.0, 1.0],
            'x0': [0.5, 0.5, 0.5]
        }
        
        problems = continuation_strategy.create_continuation_sequence(base_problem)
        
        # Check that 3 stages are created
        assert len(problems) == 3
        
        # Check that each stage has the required structure
        for i, problem in enumerate(problems):
            assert 'lbx' in problem
            assert 'ubx' in problem
            assert 'lbg' in problem
            assert 'ubg' in problem
            assert 'x0' in problem
            assert 'tolerance' in problem
    
    def test_continuation_sequence_creation(self, continuation_strategy):
        """Test continuation sequence creation with specification-compliant stages."""
        base_problem = {
            'lbx': [0.0, 0.0, 0.0],
            'ubx': [1.0, 1.0, 1.0],
            'lbg': [0.0, 0.0, 0.0],
            'ubg': [1.0, 1.0, 1.0],
            'epsilon_valve': 1e-2,
            'epsilon_friction': 1e-2,
            'stress_constraints': {
                'max_stress': 1e9,
                'contact_stress_limit': 1e8,
                'fatigue_limit': 5e8
            }
        }
        
        continuation_problems = continuation_strategy.create_continuation_sequence(base_problem)
        
        # Check that we have 3 stages
        assert len(continuation_problems) == 3
        
        # Check Stage 1 parameters
        stage1 = continuation_problems[0]
        assert stage1['stage_number'] == 1
        assert stage1['epsilon_valve'] == 1e-1
        assert stage1['epsilon_friction'] == 1e-1
        assert stage1['tolerance'] == 1e-4
        assert stage1['max_iter'] == 2000
        
        # Check Stage 2 parameters
        stage2 = continuation_problems[1]
        assert stage2['stage_number'] == 2
        assert stage2['epsilon_valve'] == 5e-2
        assert stage2['epsilon_friction'] == 5e-2
        assert stage2['tolerance'] == 1e-5
        assert stage2['max_iter'] == 3000
        
        # Check Stage 3 parameters
        stage3 = continuation_problems[2]
        assert stage3['stage_number'] == 3
        assert stage3['epsilon_valve'] == 1e-2
        assert stage3['epsilon_friction'] == 1e-2
        assert stage3['tolerance'] == 1e-6
        assert stage3['max_iter'] == 5000
    
    def test_stress_factor_application(self, continuation_strategy):
        """Test stress factor application in continuation stages."""
        base_problem = {
            'stress_constraints': {
                'max_stress': 1e9,
                'contact_stress_limit': 1e8,
                'fatigue_limit': 5e8
            }
        }
        
        continuation_problems = continuation_strategy.create_continuation_sequence(base_problem)
        
        # Check Stage 1 stress factors (0.7)
        stage1_stress = continuation_problems[0]['stress_constraints']
        assert stage1_stress['max_stress'] == 1e9 * 0.7
        assert stage1_stress['contact_stress_limit'] == 1e8 * 0.7
        assert stage1_stress['fatigue_limit'] == 5e8 * 0.7
        
        # Check Stage 2 stress factors (0.85)
        stage2_stress = continuation_problems[1]['stress_constraints']
        assert stage2_stress['max_stress'] == 1e9 * 0.85
        assert stage2_stress['contact_stress_limit'] == 1e8 * 0.85
        assert stage2_stress['fatigue_limit'] == 5e8 * 0.85
        
        # Check Stage 3 stress factors (1.0)
        stage3_stress = continuation_problems[2]['stress_constraints']
        assert stage3_stress['max_stress'] == 1e9 * 1.0
        assert stage3_stress['contact_stress_limit'] == 1e8 * 1.0
        assert stage3_stress['fatigue_limit'] == 5e8 * 1.0
    
    def test_grid_refinement(self, continuation_strategy):
        """Test grid refinement in continuation stages."""
        base_problem = {
            'collocation_points': 60,
            'time_grid': np.linspace(0, 1, 60)
        }
        
        continuation_problems = continuation_strategy.create_continuation_sequence(base_problem)
        
        # Check Stage 1 (no refinement)
        stage1 = continuation_problems[0]
        assert stage1['collocation_points'] == 60
        assert len(stage1['time_grid']) == 60
        
        # Check Stage 2 (1.5x refinement)
        stage2 = continuation_problems[1]
        assert stage2['collocation_points'] == 90  # 60 * 1.5
        assert len(stage2['time_grid']) == 90
        
        # Check Stage 3 (2x refinement)
        stage3 = continuation_problems[2]
        assert stage3['collocation_points'] == 120  # 60 * 2.0
        assert len(stage3['time_grid']) == 120


class TestConvergenceDiagnostics:
    """Test convergence diagnostics."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return SolverParameters()
    
    @pytest.fixture
    def diagnostics(self, params):
        """Create convergence diagnostics."""
        return ConvergenceDiagnostics(params)
    
    def test_calculate_kkt_error(self, diagnostics):
        """Test KKT error calculation."""
        # Create a simple problem
        x = ca.SX.sym('x', 2)
        f = x[0]**2 + x[1]**2
        g = x[0] + x[1] - 1
        
        problem = {
            'x': x,
            'f': f,
            'g': g,
            'lbx': [0.0, 0.0],
            'ubx': [1.0, 1.0],
            'lbg': [0.0],
            'ubg': [0.0]
        }
        
        # Create a mock solution
        solution = {
            'x': np.array([0.5, 0.5]),
            'lam_x': np.array([0.0, 0.0]),
            'lam_g': np.array([1.0])
        }
        
        kkt_error = diagnostics.calculate_kkt_error(solution, problem)
        
        # Check that KKT error is calculated
        assert isinstance(kkt_error, float)
        assert not np.isnan(kkt_error)
        assert not np.isinf(kkt_error)
        assert kkt_error >= 0.0
    
    def test_calculate_constraint_violations(self, diagnostics):
        """Test constraint violation calculation."""
        solution = {
            'x': np.array([0.5, 0.5]),
            'g': np.array([0.1, -0.1, 0.0])
        }
        
        problem = {
            'lbx': [0.0, 0.0],
            'ubx': [1.0, 1.0],
            'lbg': [0.0, 0.0, 0.0],
            'ubg': [1.0, 1.0, 1.0]
        }
        
        violations = diagnostics.calculate_constraint_violations(solution, problem)
        
        # Check that violations are calculated
        assert isinstance(violations, dict)
        assert 'variable_bound_violations' in violations
        assert 'constraint_violations' in violations
        assert 'total_violation' in violations
        
        # Check that violations are non-negative
        assert violations['variable_bound_violations'] >= 0.0
        assert violations['constraint_violations'] >= 0.0
        assert violations['total_violation'] >= 0.0
    
    def test_check_convergence(self, diagnostics):
        """Test convergence checking."""
        solution = {
            'x': np.array([0.5, 0.5]),
            'g': np.array([0.0, 0.0, 0.0]),
            'iterations': 10,
            'f': 0.5
        }
        
        problem = {
            'x': ca.SX.sym('x', 2),
            'f': ca.SX.sym('f'),
            'g': ca.SX.sym('g', 3),
            'lbx': [0.0, 0.0],
            'ubx': [1.0, 1.0],
            'lbg': [0.0, 0.0, 0.0],
            'ubg': [1.0, 1.0, 1.0]
        }
        
        convergence_status = diagnostics.check_convergence(solution, problem)
        
        # Check that convergence status is calculated
        assert isinstance(convergence_status, dict)
        assert 'converged' in convergence_status
        assert 'kkt_error' in convergence_status
        assert 'kkt_converged' in convergence_status
        assert 'constraint_violations' in convergence_status
        assert 'constraint_converged' in convergence_status
        assert 'iterations' in convergence_status
        assert 'objective_value' in convergence_status
        
        # Check that convergence status is boolean
        assert isinstance(convergence_status['converged'], bool)
        assert isinstance(convergence_status['kkt_converged'], bool)
        assert isinstance(convergence_status['constraint_converged'], bool)


class TestSolverImprovements:
    """Test solver improvements integration."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return SolverParameters()
    
    @pytest.fixture
    def solver_improvements(self, params):
        """Create solver improvements."""
        return SolverImprovements(params)
    
    def test_enhance_optimization_problem(self, solver_improvements):
        """Test optimization problem enhancement."""
        problem = {
            'f': ca.SX.sym('f'),
            'g': ca.SX.sym('g', 3),
            'lbx': [0.0, 0.0, 0.0],
            'ubx': [1.0, 1.0, 1.0],
            'lbg': [0.0, 0.0, 0.0],
            'ubg': [1.0, 1.0, 1.0],
            'x0': [0.5, 0.5, 0.5]
        }
        
        enhanced_problem = solver_improvements.enhance_optimization_problem(problem)
        
        # Check that enhanced problem has the same structure
        assert 'f' in enhanced_problem
        assert 'g' in enhanced_problem
        assert 'lbx' in enhanced_problem
        assert 'ubx' in enhanced_problem
        assert 'lbg' in enhanced_problem
        assert 'ubg' in enhanced_problem
        assert 'x0' in enhanced_problem
    
    def test_apply_variable_scaling(self, solver_improvements):
        """Test variable scaling application."""
        problem = {
            'x0': [0.15, 0.15, 0.15],
            'lbx': [0.0, 0.0, 0.0],
            'ubx': [0.2, 0.2, 0.2]
        }
        
        scaled_problem = solver_improvements._apply_variable_scaling(problem)
        
        # Check that variables are scaled
        assert 'x0' in scaled_problem
        assert 'lbx' in scaled_problem
        assert 'ubx' in scaled_problem
    
    def test_apply_objective_normalization(self, solver_improvements):
        """Test objective normalization application."""
        problem = {
            'f': ca.SX.sym('f')
        }
        
        normalized_problem = solver_improvements._apply_objective_normalization(problem)
        
        # Check that problem structure is preserved
        assert 'f' in normalized_problem
    
    def test_apply_constraint_scaling(self, solver_improvements):
        """Test constraint scaling application."""
        problem = {
            'lbg': [1000.0, 2000.0, 3000.0],
            'ubg': [4000.0, 5000.0, 6000.0]
        }
        
        scaled_problem = solver_improvements._apply_constraint_scaling(problem)
        
        # Check that constraints are scaled
        assert 'lbg' in scaled_problem
        assert 'ubg' in scaled_problem
        
        # Check that scaling is applied
        expected_lbg = [lb / 10000.0 for lb in problem['lbg']]  # reference_force_N
        expected_ubg = [ub / 10000.0 for ub in problem['ubg']]
        
        assert scaled_problem['lbg'] == expected_lbg
        assert scaled_problem['ubg'] == expected_ubg


class TestIntegration:
    """Test integration between components."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return SolverParameters()
    
    @pytest.fixture
    def solver_improvements(self, params):
        """Create solver improvements."""
        return SolverImprovements(params)
    
    def test_full_solver_improvements_workflow(self, solver_improvements):
        """Test complete solver improvements workflow."""
        # Create a simple optimization problem
        x = ca.SX.sym('x', 2)
        f = x[0]**2 + x[1]**2
        g = x[0] + x[1] - 1
        
        problem = {
            'x': x,
            'f': f,
            'g': g,
            'lbx': [0.0, 0.0],
            'ubx': [1.0, 1.0],
            'lbg': [0.0],
            'ubg': [0.0],
            'x0': [0.5, 0.5]
        }
        
        # Mock solver factory
        def mock_solver_factory(problem):
            class MockSolver:
                def solve(self, problem):
                    return {
                        'x': np.array([0.5, 0.5]),
                        'f': 0.5,
                        'g': np.array([0.0]),
                        'lam_x': np.array([0.0, 0.0]),
                        'lam_g': np.array([1.0]),
                        'iterations': 10
                    }
            return MockSolver()
        
        # Test with improvements
        solution = solver_improvements.solve_with_improvements(problem, mock_solver_factory)
        
        # Check that solution is returned
        assert isinstance(solution, dict)
        assert 'x' in solution
        assert 'f' in solution
        assert 'g' in solution
        
        # Check that convergence diagnostics are added
        if solver_improvements.params.diagnostics_enabled:
            assert 'convergence_status' in solution
    
    def test_consistency_between_components(self, solver_improvements):
        """Test consistency between different components."""
        # Test that normalization and scaling work together
        objectives = {
            'work_J': 1500.0,
            'pressure_Pa': 1500000.0,
            'velocity_mps': 15.0
        }
        
        variables = {
            'displacement_m': 0.15,
            'velocity_mps': 15.0,
            'pressure_Pa': 1500000.0
        }
        
        # Normalize objectives
        normalized_objectives = solver_improvements.objective_normalizer.normalize_objectives(objectives)
        
        # Scale variables
        scaled_variables = solver_improvements.variable_scaler.scale_variables(variables)
        
        # Check that both operations work
        assert len(normalized_objectives) == len(objectives)
        assert len(scaled_variables) == len(variables)
        
        # Check that known values are processed correctly
        assert abs(normalized_objectives['work_J'] - 1.5) < 1e-6
        assert abs(scaled_variables['displacement_m'] - 1.5) < 1e-6


if __name__ == '__main__':
    pytest.main([__file__])
