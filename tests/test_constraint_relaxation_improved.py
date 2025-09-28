"""
Test suite for the improved constraint relaxation strategy in the collocation solver.

This test suite validates the sophisticated constraint relaxation implementation
that handles different constraint types (equality vs inequality) appropriately.
"""

import numpy as np
import pytest
from unittest.mock import Mock, patch


class FakeNLP:
    """Mock NLP for testing constraint relaxation."""
    
    def __init__(self, constraint_bounds):
        self.constraint_bounds = constraint_bounds


class TestConstraintRelaxationImproved:
    """Test the improved constraint relaxation strategy."""
    
    def test_equality_constraint_relaxation(self):
        """Test that equality constraints are relaxed symmetrically."""
        from campro.solvers.collocation_solver import CollocationSolver, CollocationParameters
        
        # Create NLP with equality constraints (lower == upper)
        constraint_bounds = {
            'lower': np.array([0.0, 5.0, -2.0]),  # Equality constraints
            'upper': np.array([0.0, 5.0, -2.0])   # Same as lower
        }
        nlp = FakeNLP(constraint_bounds)
        
        # Create solver
        params = CollocationParameters(use_continuation=True)
        solver = CollocationSolver(parameters=params)
        
        # Test relaxation with factor 0.5 (50% relaxed)
        relaxed_lower, relaxed_upper = solver._relax_constraints_sophisticated(nlp, 0.5)
        
        # For equality constraints, relaxation should be symmetric around target value
        expected_targets = np.array([0.0, 5.0, -2.0])
        expected_relaxation = 0.5 * np.maximum(1.0, np.abs(expected_targets))
        
        np.testing.assert_allclose(relaxed_lower, expected_targets - expected_relaxation, rtol=1e-10)
        np.testing.assert_allclose(relaxed_upper, expected_targets + expected_relaxation, rtol=1e-10)
    
    def test_inequality_constraint_relaxation(self):
        """Test that inequality constraints are relaxed appropriately."""
        from campro.solvers.collocation_solver import CollocationSolver, CollocationParameters
        
        # Create NLP with inequality constraints (lower != upper)
        constraint_bounds = {
            'lower': np.array([-10.0, 0.0, -5.0]),  # Inequality constraints
            'upper': np.array([10.0, 20.0, 5.0])    # Different from lower
        }
        nlp = FakeNLP(constraint_bounds)
        
        # Create solver
        params = CollocationParameters(use_continuation=True)
        solver = CollocationSolver(parameters=params)
        
        # Test relaxation with factor 0.3 (70% relaxed)
        relaxed_lower, relaxed_upper = solver._relax_constraints_sophisticated(nlp, 0.3)
        
        # For inequality constraints, relaxation should be based on constraint magnitude
        orig_l = constraint_bounds['lower']
        orig_u = constraint_bounds['upper']
        constraint_magnitudes = np.maximum(np.abs(orig_l), np.abs(orig_u))
        expected_relaxation = 0.7 * np.maximum(1.0, constraint_magnitudes)
        
        expected_lower = orig_l - expected_relaxation
        expected_upper = orig_u + expected_relaxation
        
        np.testing.assert_allclose(relaxed_lower, expected_lower, rtol=1e-10)
        np.testing.assert_allclose(relaxed_upper, expected_upper, rtol=1e-10)
    
    def test_mixed_constraint_types(self):
        """Test relaxation with both equality and inequality constraints."""
        from campro.solvers.collocation_solver import CollocationSolver, CollocationParameters
        
        # Create NLP with mixed constraint types
        constraint_bounds = {
            'lower': np.array([0.0, -5.0, 10.0, -1.0]),  # Mixed: equality, inequality, inequality, equality
            'upper': np.array([0.0, 5.0, 20.0, -1.0])    # Same as lower for equality constraints
        }
        nlp = FakeNLP(constraint_bounds)
        
        # Create solver
        params = CollocationParameters(use_continuation=True)
        solver = CollocationSolver(parameters=params)
        
        # Test relaxation
        relaxed_lower, relaxed_upper = solver._relax_constraints_sophisticated(nlp, 0.4)
        
        # Check equality constraints (indices 0 and 3)
        equality_indices = [0, 3]
        for idx in equality_indices:
            target_value = (constraint_bounds['lower'][idx] + constraint_bounds['upper'][idx]) / 2.0
            expected_relaxation = 0.6 * max(1.0, abs(target_value))
            assert abs(relaxed_lower[idx] - (target_value - expected_relaxation)) < 1e-10
            assert abs(relaxed_upper[idx] - (target_value + expected_relaxation)) < 1e-10
        
        # Check inequality constraints (indices 1 and 2)
        inequality_indices = [1, 2]
        for idx in inequality_indices:
            orig_l = constraint_bounds['lower'][idx]
            orig_u = constraint_bounds['upper'][idx]
            constraint_magnitude = max(abs(orig_l), abs(orig_u))
            expected_relaxation = 0.6 * max(1.0, constraint_magnitude)
            assert abs(relaxed_lower[idx] - (orig_l - expected_relaxation)) < 1e-10
            assert abs(relaxed_upper[idx] - (orig_u + expected_relaxation)) < 1e-10
    
    def test_no_relaxation_when_factor_is_one(self):
        """Test that no relaxation occurs when factor is 1.0."""
        from campro.solvers.collocation_solver import CollocationSolver, CollocationParameters
        
        constraint_bounds = {
            'lower': np.array([-5.0, 0.0, 10.0]),
            'upper': np.array([5.0, 10.0, 20.0])
        }
        nlp = FakeNLP(constraint_bounds)
        
        params = CollocationParameters(use_continuation=True)
        solver = CollocationSolver(parameters=params)
        
        # Test with factor 1.0 (no relaxation)
        relaxed_lower, relaxed_upper = solver._relax_constraints_sophisticated(nlp, 1.0)
        
        np.testing.assert_array_equal(relaxed_lower, constraint_bounds['lower'])
        np.testing.assert_array_equal(relaxed_upper, constraint_bounds['upper'])
    
    def test_bounds_remain_finite(self):
        """Test that relaxed bounds remain finite and reasonable."""
        from campro.solvers.collocation_solver import CollocationSolver, CollocationParameters
        
        # Create NLP with very large constraint bounds
        constraint_bounds = {
            'lower': np.array([-1e10, 0.0]),
            'upper': np.array([1e10, 1e10])
        }
        nlp = FakeNLP(constraint_bounds)
        
        params = CollocationParameters(use_continuation=True)
        solver = CollocationSolver(parameters=params)
        
        # Test with very small factor (maximum relaxation)
        relaxed_lower, relaxed_upper = solver._relax_constraints_sophisticated(nlp, 0.01)
        
        # Bounds should be clipped to reasonable values
        assert np.all(relaxed_lower >= -1e6)
        assert np.all(relaxed_upper <= 1e6)
    
    def test_continuation_integration(self):
        """Test that the improved relaxation integrates properly with continuation."""
        from campro.solvers.collocation_solver import CollocationSolver, CollocationParameters
        from campro.solvers.numerical_methods import NumericalGuards, NumericalParameters
        
        # Create solver with numerical guards
        params = CollocationParameters(use_continuation=True, continuation_steps=3)
        solver = CollocationSolver(parameters=params)
        
        # Mock numerical guards
        mock_guards = Mock()
        mock_continuation = Mock()
        mock_continuation.generate_continuation_sequence.return_value = [0.3, 0.7, 1.0]
        mock_continuation.adjust_regularization.return_value = 1e-3
        mock_guards.continuation = mock_continuation
        
        mock_warm_start = Mock()
        mock_warm_start.perturb_solution.return_value = np.array([1.0, 2.0, 3.0])
        mock_guards.warm_start = mock_warm_start
        
        solver.numerical_guards = mock_guards
        
        # Create mock NLP
        nlp = Mock()
        nlp.casadi_problem = {"dummy": True}
        nlp.constraint_bounds = {
            'lower': np.array([0.0, -5.0]),
            'upper': np.array([0.0, 5.0])
        }
        nlp.variable_bounds = {
            'lower': np.array([-10.0, -10.0]),
            'upper': np.array([10.0, 10.0])
        }
        
        # Mock CasADi
        with patch('campro.solvers.collocation_solver.ca') as mock_ca:
            mock_solver = Mock()
            mock_solver.stats.return_value = {"return_status": "Solve_Succeeded", "iter_count": 5}
            mock_solver.return_value = {
                'x': np.array([1.0, 2.0]),
                'f': np.array([0.5]),
                'g': np.array([0.1, 0.2])
            }
            mock_ca.nlpsol.return_value = mock_solver
            mock_ca.DM.return_value = np.array([1.0, 2.0])
            
            # Test continuation with improved relaxation
            result = solver._solve_with_continuation(nlp, {"strokeLengthMm": 10.0}, {"ipopt.tol": 1e-8})
            
            # Verify that the sophisticated relaxation was called
            assert result is not None
            assert 'x' in result
            assert 'f' in result
            assert 'g' in result


if __name__ == "__main__":
    pytest.main([__file__])
