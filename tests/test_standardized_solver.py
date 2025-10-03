"""
Test the new standardized solver approach.

This test verifies that the new NLP problem schema and solver
implementation work correctly and eliminate the NaN/∞-KKT issues.
"""

import pytest
import numpy as np
import casadi as ca

from campro.optimization.nlp_types import build_nlp_problem, validate_nlp_problem
from campro.optimization.solve_core import solve_with_improvements, _preflight
from campro.optimization.ipopt_options import default_ipopt_options
from campro.optimization.phase1 import solve_phase1_feasibility


class TestStandardizedSolver:
    """Test the standardized solver implementation."""
    
    def test_simple_quadratic_problem(self):
        """Test solving a simple quadratic problem."""
        # Create a simple quadratic problem: minimize x^2 + y^2 subject to x + y = 1
        x = ca.SX.sym('x', 2)
        p = ca.SX.sym('p', 0)  # No parameters
        
        # Objective: x^2 + y^2
        f = x[0]**2 + x[1]**2
        
        # Constraint: x + y = 1
        g = x[0] + x[1] - 1
        
        # Bounds: x >= 0, y >= 0
        lbx = np.array([0.0, 0.0])
        ubx = np.array([10.0, 10.0])
        lbg = np.array([0.0])  # g >= 0
        ubg = np.array([0.0])  # g <= 0
        
        # Build standardized NLP problem
        sym = {'x': x, 'p': p, 'f': f, 'g': g}
        bnd = {'lbx': lbx, 'ubx': ubx, 'lbg': lbg, 'ubg': ubg}
        meta = {'p_val': np.array([])}
        
        nlp_problem = build_nlp_problem(sym, bnd, meta)
        
        # Validate problem
        assert validate_nlp_problem(nlp_problem)
        
        # Initial guess
        x0 = np.array([0.5, 0.5])
        
        # Solve
        result = solve_with_improvements(nlp_problem, x0, default_ipopt_options())
        
        # Check results
        assert result['success'], f"Solver failed: {result.get('message', 'Unknown error')}"
        assert result['iter_count'] > 0, "Solver should have performed iterations"
        assert np.isfinite(result['f']), "Objective should be finite"
        assert not result['is_fallback'], "Should not be a fallback solution"
        
        # Check KKT residuals
        kkt = result['kkt']
        assert kkt['stationarity'] < 1e-4, f"Stationarity residual too large: {kkt['stationarity']}"
        assert kkt['primal'] < 1e-6, f"Primal feasibility residual too large: {kkt['primal']}"
        
        # Check solution quality (should be x = [0.5, 0.5])
        x_opt = result['x']
        assert np.allclose(x_opt, [0.5, 0.5], atol=1e-4), f"Solution incorrect: {x_opt}"
        
        # Check objective value (should be 0.5)
        assert np.isclose(result['f'], 0.5, atol=1e-4), f"Objective incorrect: {result['f']}"
    
    def test_preflight_checks(self):
        """Test that preflight checks catch invalid problems."""
        # Create a problem with non-finite objective
        x = ca.SX.sym('x', 1)
        p = ca.SX.sym('p', 0)
        
        # Objective that becomes infinite at x=0
        f = 1.0 / x[0]
        
        g = ca.SX()  # No constraints
        
        lbx = np.array([0.0])
        ubx = np.array([1.0])
        lbg = np.array([])
        ubg = np.array([])
        
        sym = {'x': x, 'p': p, 'f': f, 'g': g}
        bnd = {'lbx': lbx, 'ubx': ubx, 'lbg': lbg, 'ubg': ubg}
        meta = {'p_val': np.array([])}
        
        nlp_problem = build_nlp_problem(sym, bnd, meta)
        
        # Initial guess at x=0 (should cause non-finite objective)
        x0 = np.array([0.0])
        
        # Preflight should fail
        with pytest.raises(ValueError, match="Preflight failed"):
            _preflight(nlp_problem, x0)
    
    def test_phase1_feasibility(self):
        """Test Phase-1 feasibility restoration."""
        # Create an infeasible problem: minimize x^2 subject to x = 1 and x = 2
        x = ca.SX.sym('x', 1)
        p = ca.SX.sym('p', 0)
        
        f = x[0]**2
        
        # Infeasible constraints: x = 1 and x = 2
        g = ca.vertcat(x[0] - 1, x[0] - 2)
        
        lbx = np.array([-10.0])
        ubx = np.array([10.0])
        lbg = np.array([0.0, 0.0])  # g >= 0
        ubg = np.array([0.0, 0.0])  # g <= 0
        
        sym = {'x': x, 'p': p, 'f': f, 'g': g}
        bnd = {'lbx': lbx, 'ubx': ubx, 'lbg': lbg, 'ubg': ubg}
        meta = {'p_val': np.array([])}
        
        nlp_problem = build_nlp_problem(sym, bnd, meta)
        
        # Initial guess
        x0 = np.array([1.5])
        
        # Solve Phase-1 feasibility restoration
        result = solve_phase1_feasibility(nlp_problem, x0)
        
        # Should detect infeasibility (either through Phase-1 failure or explicit detection)
        assert not result['is_feasible'], "Should detect infeasibility"
        assert result['status'] in ['INFEASIBLE', 'PHASE1_FAILED'], f"Status should indicate infeasibility, got {result['status']}"
        
        # If Phase-1 succeeded, check slack violations
        if result['status'] == 'INFEASIBLE':
            assert result['slack_violations'] > 0, "Should have slack violations"
    
    def test_fallback_handling(self):
        """Test that fallback solutions are handled correctly."""
        # Create a problem that will fail (invalid bounds)
        x = ca.SX.sym('x', 1)
        p = ca.SX.sym('p', 0)
        
        f = x[0]**2
        g = ca.SX()  # No constraints
        
        # Invalid bounds: lbx > ubx
        lbx = np.array([2.0])
        ubx = np.array([1.0])
        lbg = np.array([])
        ubg = np.array([])
        
        sym = {'x': x, 'p': p, 'f': f, 'g': g}
        bnd = {'lbx': lbx, 'ubx': ubx, 'lbg': lbg, 'ubg': ubg}
        meta = {'p_val': np.array([])}
        
        nlp_problem = build_nlp_problem(sym, bnd, meta)
        
        # Initial guess that violates bounds (should trigger preflight failure)
        x0 = np.array([1.5])  # This violates lbx > ubx
        
        # Solve should return fallback due to preflight failure
        result = solve_with_improvements(nlp_problem, x0, default_ipopt_options())
        
        # Should be a fallback solution
        assert result['is_fallback'], "Should be a fallback solution"
        assert not result['success'], "Fallback should not be successful"
        assert result['iter_count'] == 0, "Fallback should have 0 iterations"
        assert np.isnan(result['f']), "Fallback should have NaN objective"
        
        # KKT residuals should be infinite
        kkt = result['kkt']
        assert kkt['stationarity'] == np.inf, "Fallback should have infinite KKT residuals"
        assert kkt['primal'] == np.inf, "Fallback should have infinite KKT residuals"
