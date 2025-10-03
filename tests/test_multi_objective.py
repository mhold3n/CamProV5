"""
Tests for multi-objective optimization implementation.
"""

import pytest
import numpy as np
import casadi as ca
from campro.optimization.multi_objective import (
    MultiObjectiveParameters,
    AugmentedTchebyshevScalarizer,
    MultiObjectiveOptimizer,
    RobustOptimizer
)


class TestMultiObjectiveParameters:
    """Test multi-objective parameters."""
    
    def test_default_parameters(self):
        """Test default parameter initialization."""
        params = MultiObjectiveParameters()
        
        assert params.augmentation_factor == 0.01
        assert params.reference_work_J == 1000.0
        assert params.reference_efficiency == 0.95
        assert params.reference_jerk_mps3 == 1000.0
        assert params.reference_stress_Pa == 1e9
        assert params.reference_power_loss_W == 1000.0
        
        # Check weight sets
        assert 'work' in params.work_efficiency_biased
        assert 'efficiency' in params.work_efficiency_biased
        assert 'jerk' in params.work_efficiency_biased
        assert 'stress' in params.work_efficiency_biased
        assert 'loss' in params.work_efficiency_biased
        
        # Check weight sums
        assert abs(sum(params.work_efficiency_biased.values()) - 1.0) < 1e-6
        assert abs(sum(params.balanced.values()) - 1.0) < 1e-6
        assert abs(sum(params.durability_biased.values()) - 1.0) < 1e-6


class TestAugmentedTchebyshevScalarizer:
    """Test augmented Tchebyshev scalarization."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return MultiObjectiveParameters()
    
    @pytest.fixture
    def scalarizer(self, params):
        """Create test scalarizer."""
        return AugmentedTchebyshevScalarizer(params)
    
    @pytest.fixture
    def test_objectives(self):
        """Create test objectives."""
        x = ca.SX.sym('x', 2)
        return {
            'work': x[0]**2 + x[1]**2,
            'efficiency': x[0] * x[1],
            'jerk': (x[0] - 1)**2 + (x[1] - 1)**2,
            'stress': x[0]**2 + x[1]**2,
            'loss': (x[0] + x[1])**2
        }
    
    def test_scalarize_basic(self, scalarizer, test_objectives):
        """Test basic scalarization."""
        weights = {
            'work': 0.4,
            'efficiency': 0.3,
            'jerk': 0.1,
            'stress': 0.1,
            'loss': 0.1
        }
        
        scalarized = scalarizer.scalarize(test_objectives, weights)
        
        # Check that scalarized is a CasADi expression
        assert isinstance(scalarized, ca.SX)
        
        # Check that it has the right number of variables
        assert scalarized.size1() == 1
        assert scalarized.size2() == 1
    
    def test_scalarize_with_reference_point(self, scalarizer, test_objectives):
        """Test scalarization with custom reference point."""
        weights = {
            'work': 0.4,
            'efficiency': 0.3,
            'jerk': 0.1,
            'stress': 0.1,
            'loss': 0.1
        }
        
        reference_point = {
            'work': 500.0,
            'efficiency': 0.8,
            'jerk': 500.0,
            'stress': 5e8,
            'loss': 500.0
        }
        
        scalarized = scalarizer.scalarize(test_objectives, weights, reference_point)
        
        assert isinstance(scalarized, ca.SX)
        assert scalarized.size1() == 1
        assert scalarized.size2() == 1
    
    def test_get_weight_set(self, scalarizer):
        """Test getting predefined weight sets."""
        # Test work efficiency biased
        weights = scalarizer.get_weight_set('work_efficiency_biased')
        assert weights['work'] == 0.4
        assert weights['efficiency'] == 0.3
        
        # Test balanced
        weights = scalarizer.get_weight_set('balanced')
        assert weights['work'] == 0.25
        assert weights['efficiency'] == 0.25
        
        # Test durability biased
        weights = scalarizer.get_weight_set('durability_biased')
        assert weights['stress'] == 0.25
        assert weights['loss'] == 0.15
        
        # Test invalid case
        with pytest.raises(ValueError):
            scalarizer.get_weight_set('invalid_case')


class TestMultiObjectiveOptimizer:
    """Test multi-objective optimizer."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return MultiObjectiveParameters()
    
    @pytest.fixture
    def optimizer(self, params):
        """Create test optimizer."""
        return MultiObjectiveOptimizer(params)
    
    @pytest.fixture
    def test_objectives(self):
        """Create test objectives."""
        x = ca.SX.sym('x', 2)
        return {
            'work': x[0]**2 + x[1]**2,
            'efficiency': x[0] * x[1],
            'jerk': (x[0] - 1)**2 + (x[1] - 1)**2,
            'stress': x[0]**2 + x[1]**2,
            'loss': (x[0] + x[1])**2
        }
    
    def test_create_scalarized_objective_balanced(self, optimizer, test_objectives):
        """Test creating scalarized objective with balanced weights."""
        scalarized = optimizer.create_scalarized_objective(test_objectives, 'balanced')
        
        assert isinstance(scalarized, ca.SX)
        assert scalarized.size1() == 1
        assert scalarized.size2() == 1
    
    def test_create_scalarized_objective_custom(self, optimizer, test_objectives):
        """Test creating scalarized objective with custom weights."""
        custom_weights = {
            'work': 0.5,
            'efficiency': 0.3,
            'jerk': 0.1,
            'stress': 0.05,
            'loss': 0.05
        }
        
        scalarized = optimizer.create_scalarized_objective(test_objectives, 'custom', custom_weights)
        
        assert isinstance(scalarized, ca.SX)
        assert scalarized.size1() == 1
        assert scalarized.size2() == 1
    
    def test_optimize_with_weight_sweep(self, optimizer, test_objectives):
        """Test optimization with weight sweep."""
        scalarized_objectives = optimizer.optimize_with_weight_sweep(test_objectives)
        
        # Check that all cases are included
        assert 'work_efficiency_biased' in scalarized_objectives
        assert 'balanced' in scalarized_objectives
        assert 'durability_biased' in scalarized_objectives
        
        # Check that all are CasADi expressions
        for case, obj in scalarized_objectives.items():
            assert isinstance(obj, ca.SX)
            assert obj.size1() == 1
            assert obj.size2() == 1
    
    def test_calculate_pareto_frontier(self, optimizer):
        """Test Pareto frontier calculation."""
        solutions = {
            'solution_1': {'work': 1000.0, 'efficiency': 0.9, 'jerk': 100.0, 'stress': 1e8, 'loss': 200.0},
            'solution_2': {'work': 1200.0, 'efficiency': 0.85, 'jerk': 150.0, 'stress': 1.2e8, 'loss': 250.0},
            'solution_3': {'work': 800.0, 'efficiency': 0.95, 'jerk': 80.0, 'stress': 8e7, 'loss': 150.0},
            'solution_4': {'work': 1100.0, 'efficiency': 0.88, 'jerk': 120.0, 'stress': 1.1e8, 'loss': 180.0}
        }
        
        pareto_analysis = optimizer.calculate_pareto_frontier(solutions)
        
        # Check that analysis contains expected keys
        assert 'pareto_solutions' in pareto_analysis
        assert 'pareto_indices' in pareto_analysis
        assert 'objective_matrix' in pareto_analysis
        assert 'objective_names' in pareto_analysis
        
        # Check objective matrix shape
        assert pareto_analysis['objective_matrix'].shape == (4, 5)
        
        # Check that Pareto solutions exist
        assert len(pareto_analysis['pareto_solutions']) > 0
        assert len(pareto_analysis['pareto_indices']) > 0
    
    def test_dominates(self, optimizer):
        """Test dominance checking."""
        # Solution A dominates B (better in all objectives)
        solution_a = np.array([1000.0, 0.9, 100.0, 1e8, 200.0])  # work, efficiency, jerk, stress, loss
        solution_b = np.array([800.0, 0.8, 150.0, 1.2e8, 250.0])
        
        assert optimizer._dominates(solution_a, solution_b)
        assert not optimizer._dominates(solution_b, solution_a)
        
        # Solutions that don't dominate each other
        solution_c = np.array([1000.0, 0.8, 100.0, 1e8, 200.0])
        solution_d = np.array([800.0, 0.9, 150.0, 1.2e8, 250.0])
        
        assert not optimizer._dominates(solution_c, solution_d)
        assert not optimizer._dominates(solution_d, solution_c)


class TestRobustOptimizer:
    """Test robust optimization."""
    
    @pytest.fixture
    def params(self):
        """Create test parameters."""
        return MultiObjectiveParameters()
    
    @pytest.fixture
    def robust_optimizer(self, params):
        """Create test robust optimizer."""
        return RobustOptimizer(params)
    
    def test_add_chance_constraints(self, robust_optimizer):
        """Test adding chance constraints."""
        problem = {
            'x': ca.SX.sym('x', 2),
            'f': ca.SX.sym('f', 1),
            'g': [],
            'lbg': [],
            'ubg': []
        }
        
        uncertain_params = {
            'friction_coeff': {'mean': 0.08, 'std': 0.02, 'stress_limit': 1e9},
            'heat_release': {'eta_min': 0.8},
            'clearance': {'pressure_limit': 1e7}
        }
        
        robust_problem = robust_optimizer.add_chance_constraints(problem, uncertain_params)
        
        # Check that constraints were added
        assert len(robust_problem['g']) > 0
        assert len(robust_problem['lbg']) > 0
        assert len(robust_problem['ubg']) > 0
        
        # Check that all constraint arrays have the same length
        assert len(robust_problem['g']) == len(robust_problem['lbg'])
        assert len(robust_problem['g']) == len(robust_problem['ubg'])
    
    def test_add_friction_chance_constraint(self, robust_optimizer):
        """Test adding friction chance constraint."""
        problem = {
            'x': ca.SX.sym('x', 2),
            'f': ca.SX.sym('f', 1),
            'g': [],
            'lbg': [],
            'ubg': [],
            'stress_max': 5e8
        }
        
        param_info = {'mean': 0.08, 'std': 0.02, 'stress_limit': 1e9}
        
        robust_problem = robust_optimizer._add_friction_chance_constraint(problem, param_info)
        
        # Check that constraint was added
        assert len(robust_problem['g']) == 1
        assert len(robust_problem['lbg']) == 1
        assert len(robust_problem['ubg']) == 1
        
        # Check constraint bounds
        assert robust_problem['lbg'][0] == -np.inf
        assert robust_problem['ubg'][0] == 1e9
    
    def test_add_heat_release_chance_constraint(self, robust_optimizer):
        """Test adding heat release chance constraint."""
        problem = {
            'x': ca.SX.sym('x', 2),
            'f': ca.SX.sym('f', 1),
            'g': [],
            'lbg': [],
            'ubg': [],
            'efficiency': 0.85
        }
        
        param_info = {'eta_min': 0.8}
        
        robust_problem = robust_optimizer._add_heat_release_chance_constraint(problem, param_info)
        
        # Check that constraint was added
        assert len(robust_problem['g']) == 1
        assert len(robust_problem['lbg']) == 1
        assert len(robust_problem['ubg']) == 1
        
        # Check constraint bounds
        assert robust_problem['lbg'][0] == 0.8
        assert robust_problem['ubg'][0] == np.inf
    
    def test_add_clearance_chance_constraint(self, robust_optimizer):
        """Test adding clearance chance constraint."""
        problem = {
            'x': ca.SX.sym('x', 2),
            'f': ca.SX.sym('f', 1),
            'g': [],
            'lbg': [],
            'ubg': [],
            'pressure_max': 5e6
        }
        
        param_info = {'pressure_limit': 1e7}
        
        robust_problem = robust_optimizer._add_clearance_chance_constraint(problem, param_info)
        
        # Check that constraint was added
        assert len(robust_problem['g']) == 1
        assert len(robust_problem['lbg']) == 1
        assert len(robust_problem['ubg']) == 1
        
        # Check constraint bounds
        assert robust_problem['lbg'][0] == -np.inf
        assert robust_problem['ubg'][0] == 1e7


class TestIntegration:
    """Integration tests for multi-objective optimization."""
    
    def test_full_multi_objective_workflow(self):
        """Test complete multi-objective optimization workflow."""
        # Create parameters
        params = MultiObjectiveParameters()
        
        # Create optimizer
        optimizer = MultiObjectiveOptimizer(params)
        
        # Create test objectives
        x = ca.SX.sym('x', 2)
        objectives = {
            'work': x[0]**2 + x[1]**2,
            'efficiency': x[0] * x[1],
            'jerk': (x[0] - 1)**2 + (x[1] - 1)**2,
            'stress': x[0]**2 + x[1]**2,
            'loss': (x[0] + x[1])**2
        }
        
        # Create scalarized objectives for different cases
        scalarized_objectives = optimizer.optimize_with_weight_sweep(objectives)
        
        # Check that all cases are present
        assert len(scalarized_objectives) == 3
        assert 'work_efficiency_biased' in scalarized_objectives
        assert 'balanced' in scalarized_objectives
        assert 'durability_biased' in scalarized_objectives
        
        # Check that all objectives are valid CasADi expressions
        for case, obj in scalarized_objectives.items():
            assert isinstance(obj, ca.SX)
            assert obj.size1() == 1
            assert obj.size2() == 1
    
    def test_robust_optimization_workflow(self):
        """Test robust optimization workflow."""
        # Create parameters
        params = MultiObjectiveParameters()
        
        # Create robust optimizer
        robust_optimizer = RobustOptimizer(params)
        
        # Create test problem
        problem = {
            'x': ca.SX.sym('x', 2),
            'f': ca.SX.sym('f', 1),
            'g': [],
            'lbg': [],
            'ubg': [],
            'stress_max': 5e8,
            'efficiency': 0.85,
            'pressure_max': 5e6
        }
        
        # Add chance constraints
        uncertain_params = {
            'friction_coeff': {'mean': 0.08, 'std': 0.02, 'stress_limit': 1e9},
            'heat_release': {'eta_min': 0.8},
            'clearance': {'pressure_limit': 1e7}
        }
        
        robust_problem = robust_optimizer.add_chance_constraints(problem, uncertain_params)
        
        # Check that problem was modified correctly
        assert len(robust_problem['g']) == 3  # Three chance constraints
        assert len(robust_problem['lbg']) == 3
        assert len(robust_problem['ubg']) == 3
        
        # Check that original problem structure is preserved
        assert 'x' in robust_problem
        assert 'f' in robust_problem
