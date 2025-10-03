"""
Tests for B-spline motion law parameterization.
"""

import pytest
import numpy as np
import casadi as ca
from campro.optimization.bspline_motion_law import (
    BSplineParameters,
    BSplineMotionLaw,
    BSplineMotionLawOptimizer
)


class TestBSplineParameters:
    """Test B-spline parameters."""
    
    def test_default_parameters(self):
        """Test default parameter initialization."""
        params = BSplineParameters()
        
        assert params.spline_order == 4
        assert params.num_control_points == 20
        assert params.cycle_time == 1.0
        assert params.stroke_length == 0.1
        assert params.initial_position == 0.0
        assert params.final_position == 0.1  # Set in __post_init__
        assert params.initial_velocity == 0.0
        assert params.final_velocity == 0.0
        assert params.max_jerk == 1000.0
        assert params.continuity_order == 2
    
    def test_custom_parameters(self):
        """Test custom parameter initialization."""
        params = BSplineParameters(
            spline_order=5,
            num_control_points=30,
            cycle_time=2.0,
            stroke_length=0.2,
            max_jerk=2000.0
        )
        
        assert params.spline_order == 5
        assert params.num_control_points == 30
        assert params.cycle_time == 2.0
        assert params.stroke_length == 0.2
        assert params.final_position == 0.2
        assert params.max_jerk == 2000.0


class TestBSplineMotionLaw:
    """Test B-spline motion law implementation."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return BSplineParameters(
            spline_order=4,
            num_control_points=10,
            cycle_time=1.0,
            stroke_length=0.1
        )
    
    @pytest.fixture
    def bspline(self, params):
        """Create test B-spline motion law."""
        return BSplineMotionLaw(params)
    
    def test_knot_vector_creation(self, bspline):
        """Test knot vector creation."""
        knot_vector = bspline.knot_vector
        
        # Check knot vector length
        expected_length = bspline.params.num_control_points + bspline.params.spline_order + 1
        assert len(knot_vector) == expected_length
        
        # Check clamped knots at ends
        p = bspline.params.spline_order
        assert np.allclose(knot_vector[:p+1], 0.0)
        assert np.allclose(knot_vector[-(p+1):], bspline.params.cycle_time)
        
        # Check knot vector is non-decreasing
        assert np.all(np.diff(knot_vector) >= 0)
    
    def test_basis_function_creation(self, bspline):
        """Test basis function creation."""
        # Check that basis functions are created
        assert len(bspline.basis_functions) == bspline.params.num_control_points
        
        # Check that evaluation functions are created
        assert bspline.basis_eval_func is not None
        assert bspline.velocity_eval_func is not None
        assert bspline.acceleration_eval_func is not None
        assert bspline.jerk_eval_func is not None
    
    def test_motion_law_creation(self, bspline):
        """Test motion law creation from control points."""
        # Create simple control points
        control_points = np.linspace(0, 0.1, bspline.params.num_control_points)
        
        motion_law = bspline.create_motion_law(control_points)

        # Check that motion law functions are created
        for key in ['position', 'velocity', 'acceleration', 'jerk']:
            assert key in motion_law
            assert isinstance(motion_law[key], ca.Function)

        assert motion_law['control_points_symbol'].size1() == bspline.params.num_control_points
    
    def test_boundary_constraints(self, bspline):
        """Test boundary constraint creation."""
        # Create symbolic control points
        control_points = ca.SX.sym('cp', bspline.params.num_control_points)
        
        constraints = bspline.create_boundary_constraints(control_points)
        
        # Check that constraints are created
        assert len(constraints) > 0
        
        # Check that constraints are CasADi expressions
        for constraint in constraints:
            assert isinstance(constraint, ca.SX)
    
    def test_initial_guess_creation(self, bspline):
        """Test initial guess creation."""
        initial_guess = bspline.create_initial_guess()

        # Check initial guess shape
        assert len(initial_guess) == bspline.params.num_control_points
        
        # Check boundary conditions
        assert initial_guess[0] == bspline.params.initial_position
        assert initial_guess[-1] == bspline.params.final_position
        
        # Check that it's a reasonable interpolation
        assert np.all(np.diff(initial_guess) >= 0)  # Non-decreasing

    def test_initial_guess_satisfies_boundary_constraints(self, bspline):
        """Initial guess should respect position/velocity boundary constraints."""
        initial_guess = bspline.create_initial_guess()
        control_points = ca.SX.sym('cp', bspline.params.num_control_points)
        constraints = bspline.create_boundary_constraints(control_points)
        constraint_func = ca.Function('boundary', [control_points], [ca.vertcat(*constraints)])
        residual = np.array(constraint_func(ca.DM(initial_guess).reshape((-1, 1))))
        assert np.allclose(residual, 0.0, atol=1e-10)

    def test_motion_law_responds_to_control_point_changes(self, bspline):
        """Perturbing a control point should change the motion law and derivatives."""
        control_points_symbol = ca.SX.sym('cp', bspline.params.num_control_points)
        motion_law = bspline.create_motion_law(control_points_symbol)

        baseline = bspline.create_initial_guess()
        perturbed = baseline.copy()
        perturbed[3] += 1e-3

        t_sample = 0.4 * bspline.params.cycle_time
        baseline_dm = ca.DM(baseline).reshape((-1, 1))
        perturbed_dm = ca.DM(perturbed).reshape((-1, 1))

        pos_base = float(motion_law['position'](t_sample, baseline_dm))
        pos_pert = float(motion_law['position'](t_sample, perturbed_dm))
        vel_base = float(motion_law['velocity'](t_sample, baseline_dm))
        vel_pert = float(motion_law['velocity'](t_sample, perturbed_dm))
        jerk_base = float(motion_law['jerk'](t_sample, baseline_dm))
        jerk_pert = float(motion_law['jerk'](t_sample, perturbed_dm))

        assert abs(pos_base - pos_pert) > 1e-8
        assert abs(vel_base - vel_pert) > 1e-8
        assert abs(jerk_base - jerk_pert) > 1e-8
    
    def test_motion_law_evaluation(self, bspline):
        """Test motion law evaluation."""
        # Create control points
        control_points = np.linspace(0, 0.1, bspline.params.num_control_points)
        
        # Create time grid
        time_grid = np.linspace(0, 1.0, 21)
        
        # Evaluate motion law
        results = bspline.evaluate_motion_law(control_points, time_grid)
        
        # Check results structure
        assert 'position' in results
        assert 'velocity' in results
        assert 'acceleration' in results
        assert 'jerk' in results
        
        # Check result shapes
        for key, values in results.items():
            assert len(values) == len(time_grid)
            assert isinstance(values, np.ndarray)
        
        # Check boundary conditions
        assert abs(results['position'][0] - bspline.params.initial_position) < 1e-6
        assert abs(results['position'][-1] - bspline.params.final_position) < 1e-6
        assert abs(results['velocity'][0] - bspline.params.initial_velocity) < 1e-6
        assert abs(results['velocity'][-1] - bspline.params.final_velocity) < 1e-6
    
    def test_optimization_problem_creation(self, bspline):
        """Test optimization problem creation."""
        time_grid = np.linspace(0, 1.0, 11)
        
        problem = bspline.create_optimization_problem(time_grid)
        
        # Check problem structure
        assert 'x' in problem
        assert 'f' in problem
        assert 'g' in problem
        assert 'lbx' in problem
        assert 'ubx' in problem
        assert 'lbg' in problem
        assert 'ubg' in problem
        assert 'x0' in problem
        assert 'motion_law' in problem
        assert 'time_grid' in problem
        
        # Check variable dimensions
        assert problem['x'].size1() == bspline.params.num_control_points
        assert len(problem['lbx']) == bspline.params.num_control_points
        assert len(problem['ubx']) == bspline.params.num_control_points
        assert len(problem['x0']) == bspline.params.num_control_points
        
        # Check constraint dimensions
        n_constraints = problem['g'].size1()
        assert len(problem['lbg']) == n_constraints
        assert len(problem['ubg']) == n_constraints


class TestBSplineMotionLawOptimizer:
    """Test B-spline motion law optimizer."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return BSplineParameters(
            spline_order=4,
            num_control_points=8,
            cycle_time=1.0,
            stroke_length=0.1
        )
    
    @pytest.fixture
    def optimizer(self, params):
        """Create test optimizer."""
        return BSplineMotionLawOptimizer(params)
    
    def test_velocity_flatness_objective(self, optimizer):
        """Test velocity flatness objective creation."""
        # Create simple motion law
        control_points = np.linspace(0, 0.1, optimizer.params.num_control_points)
        motion_law = optimizer.bspline.create_motion_law(control_points)
        
        # Create time grid
        time_grid = np.linspace(0, 1.0, 11)
        
        # Create velocity flatness objective
        target_velocity = 0.1
        objective = optimizer.create_velocity_flatness_objective(
            motion_law, time_grid, target_velocity
        )
        
        # Check that objective is a CasADi expression
        assert isinstance(objective, ca.SX)
        assert objective.size1() == 1
        assert objective.size2() == 1
    
    def test_jerk_regularization_objective(self, optimizer):
        """Test jerk regularization objective creation."""
        # Create simple motion law
        control_points = np.linspace(0, 0.1, optimizer.params.num_control_points)
        motion_law = optimizer.bspline.create_motion_law(control_points)
        
        # Create time grid
        time_grid = np.linspace(0, 1.0, 11)
        
        # Create jerk regularization objective
        objective = optimizer.create_jerk_regularization_objective(
            motion_law, time_grid
        )
        
        # Check that objective is a CasADi expression
        assert isinstance(objective, ca.SX)
        assert objective.size1() == 1
        assert objective.size2() == 1
    
    def test_optimization_problem_creation(self, optimizer):
        """Test optimization problem creation."""
        # Create time grid
        time_grid = np.linspace(0, 1.0, 11)
        
        # Create objective function
        def objective_function(motion_law, time_grid):
            return optimizer.create_velocity_flatness_objective(
                motion_law, time_grid, 0.1
            )
        
        # Create optimization problem
        problem = optimizer.optimize_motion_law(objective_function, time_grid)
        
        # Check problem structure
        assert 'x' in problem
        assert 'f' in problem
        assert 'g' in problem
        assert 'lbx' in problem
        assert 'ubx' in problem
        assert 'lbg' in problem
        assert 'ubg' in problem
        assert 'x0' in problem
        
        # Check that objective is properly set
        assert isinstance(problem['f'], ca.SX)
        assert problem['f'].size1() == 1
        assert problem['f'].size2() == 1
    
    def test_optimization_with_additional_constraints(self, optimizer):
        """Test optimization with additional constraints."""
        # Create time grid
        time_grid = np.linspace(0, 1.0, 11)
        
        # Create objective function
        def objective_function(motion_law, time_grid):
            return optimizer.create_velocity_flatness_objective(
                motion_law, time_grid, 0.1
            )
        
        # Create additional constraints
        control_points = ca.SX.sym('cp', optimizer.params.num_control_points)
        additional_constraints = [
            control_points[1] - control_points[0] - 0.01,  # Minimum step size
            control_points[-1] - control_points[-2] - 0.01  # Minimum step size
        ]
        
        # Create optimization problem
        problem = optimizer.optimize_motion_law(
            objective_function, time_grid, additional_constraints
        )
        
        # Check that additional constraints are included
        n_basic_constraints = len(optimizer.bspline.create_boundary_constraints(control_points))
        n_smoothness_constraints = len(time_grid) * 2  # Jerk bounds
        n_additional_constraints = len(additional_constraints)
        expected_total = n_basic_constraints + n_smoothness_constraints + n_additional_constraints
        
        assert problem['g'].size1() == expected_total
        assert len(problem['lbg']) == expected_total
        assert len(problem['ubg']) == expected_total


class TestIntegration:
    """Integration tests for B-spline motion law."""
    
    def test_full_motion_law_workflow(self):
        """Test complete motion law workflow."""
        # Create parameters
        params = BSplineParameters(
            spline_order=4,
            num_control_points=10,
            cycle_time=1.0,
            stroke_length=0.1
        )
        
        # Create B-spline motion law
        bspline = BSplineMotionLaw(params)
        
        # Create control points
        control_points = np.linspace(0, 0.1, params.num_control_points)
        
        # Create time grid
        time_grid = np.linspace(0, 1.0, 21)
        
        # Evaluate motion law
        results = bspline.evaluate_motion_law(control_points, time_grid)
        
        # Check that results are reasonable
        assert np.all(results['position'] >= 0)
        assert np.all(results['position'] <= params.stroke_length)
        
        # Check boundary conditions
        assert abs(results['position'][0] - 0.0) < 1e-6
        assert abs(results['position'][-1] - params.stroke_length) < 1e-6
        assert abs(results['velocity'][0] - 0.0) < 1e-6
        assert abs(results['velocity'][-1] - 0.0) < 1e-6
    
    def test_optimization_workflow(self):
        """Test optimization workflow."""
        # Create parameters
        params = BSplineParameters(
            spline_order=4,
            num_control_points=8,
            cycle_time=1.0,
            stroke_length=0.1
        )
        
        # Create optimizer
        optimizer = BSplineMotionLawOptimizer(params)
        
        # Create time grid
        time_grid = np.linspace(0, 1.0, 11)
        
        # Create objective function (minimize jerk)
        def objective_function(motion_law, time_grid):
            return optimizer.create_jerk_regularization_objective(
                motion_law, time_grid
            )
        
        # Create optimization problem
        problem = optimizer.optimize_motion_law(objective_function, time_grid)
        
        # Check that problem is well-formed
        assert problem['x'].size1() == params.num_control_points
        assert problem['f'].size1() == 1
        assert problem['g'].size1() > 0  # Should have constraints
        
        # Check that initial guess is reasonable
        assert len(problem['x0']) == params.num_control_points
        assert problem['x0'][0] == params.initial_position
        assert problem['x0'][-1] == params.final_position
