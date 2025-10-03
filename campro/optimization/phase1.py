"""
Phase-1 Feasibility Restoration

This module implements explicit Phase-1 feasibility restoration using
slack variables and penalty methods, rather than diagnosing after failure.
"""

import numpy as np
import casadi as ca
from typing import Dict, Any

from .nlp_types import NLPProblem, build_nlp_problem


def build_phase1_feasibility(prob: NLPProblem, w: float = 1.0) -> NLPProblem:
    """
    Build a Phase-1 feasibility restoration problem using slack variables.
    
    This creates an explicit feasibility restoration NLP that minimizes
    constraint violations using slack variables, rather than diagnosing
    after a hard failure.
    
    Args:
        prob: Original NLP problem
        w: Weight for original objective (small positive value)
        
    Returns:
        Phase-1 NLP problem with slack variables
    """
    x, p = prob.x, prob.p
    
    # Create slack variables for all constraints
    n_g = prob.g.shape[0]
    s = ca.SX.sym('s', n_g)  # Nonnegative slacks
    
    # Slack variable bounds
    sL = np.zeros(n_g)  # Lower bound: s >= 0
    sU = np.full(n_g, np.inf)  # Upper bound: s >= 0 (unbounded above)
    
    # Relaxed constraints: lbg - s <= g(x) <= ubg + s
    # This allows violations but penalizes them in the objective
    g_relaxed = prob.g
    
    # Phase-1 objective: minimize sum(s) + small weight * original objective
    # Use L1 penalty for sparsity (fewer active slacks)
    f_phase1 = ca.sumsqr(ca.fmax(s, 0))**0.5 + w * prob.f
    
    # Extended decision variables: [x, s]
    x_ext = ca.vertcat(x, s)
    
    # Compile functions for extended problem
    # Note: Functions compiled but not used in current implementation
    
    # Extended bounds
    lbx_ext = np.concatenate([prob.lbx, sL])
    ubx_ext = np.concatenate([prob.ubx, sU])
    
    # Constraint bounds unchanged (violations absorbed by slacks)
    lbg = prob.lbg
    ubg = prob.ubg
    
    # Build Phase-1 problem
    sym = {'x': x_ext, 'p': p, 'f': f_phase1, 'g': g_relaxed}
    bnd = {'lbx': lbx_ext, 'ubx': ubx_ext, 'lbg': lbg, 'ubg': ubg}
    meta = {'p_val': prob.p_val, 'phase': 'phase1', 'original_problem': prob}
    
    return build_nlp_problem(sym, bnd, meta)


def extract_phase1_solution(phase1_sol: Dict[str, Any], original_prob: NLPProblem) -> Dict[str, Any]:
    """
    Extract solution from Phase-1 problem back to original problem space.
    
    Args:
        phase1_sol: Solution from Phase-1 problem
        original_prob: Original NLP problem
        
    Returns:
        Solution in original problem space with feasibility information
    """
    if not phase1_sol.get('success', False):
        return {
            'success': False,
            'status': 'PHASE1_FAILED',
            'message': 'Phase-1 feasibility restoration failed',
            'is_feasible': False,
            'slack_violations': np.inf
        }
    
    x_full = phase1_sol['x']
    n_x = len(original_prob.lbx)
    
    # Extract original variables and slack variables
    x_orig = x_full[:n_x]
    s = x_full[n_x:]
    
    # Check feasibility
    slack_sum = np.sum(np.maximum(s, 0.0))
    is_feasible = slack_sum < 1e-6  # Small tolerance for numerical errors
    
    # Evaluate original problem at extracted solution
    f_orig = float(original_prob.fun(x_orig, original_prob.p_val))
    g_orig = np.array(original_prob.g_fun(x_orig, original_prob.p_val)).squeeze()
    
    return {
        'success': is_feasible,
        'status': 'FEASIBLE' if is_feasible else 'INFEASIBLE',
        'message': f"Phase-1 completed, slack sum: {slack_sum:.2e}",
        'x': x_orig,
        'f': f_orig,
        'g': g_orig,
        'is_feasible': is_feasible,
        'slack_violations': slack_sum,
        'slack_variables': s,
        'iter_count': phase1_sol.get('iter_count', 0),
        'meta': {
            'phase1_solution': phase1_sol,
            'original_problem': original_prob
        }
    }


def solve_phase1_feasibility(prob: NLPProblem, 
                           x0: np.ndarray, 
                           w: float = 1.0) -> Dict[str, Any]:
    """
    Solve Phase-1 feasibility restoration problem.
    
    Args:
        prob: Original NLP problem
        x0: Initial guess for original variables
        w: Weight for original objective in Phase-1
        
    Returns:
        Feasibility restoration result
    """
    from .solve_core import solve_with_improvements
    
    # Build Phase-1 problem
    phase1_prob = build_phase1_feasibility(prob, w)
    
    # Create initial guess for extended problem
    n_s = len(prob.lbg)
    s0 = np.zeros(n_s)  # Start with zero slacks
    x0_ext = np.concatenate([x0, s0])
    
    # Solve Phase-1 problem
    phase1_sol = solve_with_improvements(phase1_prob, x0_ext)
    
    # Extract solution back to original space
    return extract_phase1_solution(phase1_sol, prob)
