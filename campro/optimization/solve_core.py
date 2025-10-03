"""
Core Solver Implementation

This module provides the core solver functionality with robust error handling,
preflight checks, and standardized result formats.
"""

import numpy as np
import casadi as ca
from typing import Dict, Any, Optional

from .nlp_types import NLPProblem
from .ipopt_options import default_ipopt_options
from .solver_interface import WarmStart
from campro.logging import get_logger

logger = get_logger(__name__)


def _inf_norm(v: np.ndarray) -> float:
    """Helper function to compute infinity norm."""
    if v.size == 0:
        return 0.0
    else:
        result = float(np.max(np.abs(v)))
        return result


def _fallback_result(reason: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a standardized fallback result for failed solves.
    
    Args:
        reason: Reason for failure
        meta: Additional metadata
        
    Returns:
        Standardized fallback result dictionary
    """
    return {
        'success': False,
        'status': 'FALLBACK',
        'message': reason,
        'iter_count': 0,
        'x': None,
        'f': np.nan,
        'lam_g': None,
        'z_L': None,
        'z_U': None,
        'is_fallback': True,
        'meta': meta,
        'kkt': {
            'stationarity': np.inf,
            'primal': np.inf,
            'dual': np.inf,
            'complementarity': np.inf
        }
    }


def _preflight(prob: NLPProblem, x0: np.ndarray) -> None:
    """
    Perform preflight checks on the NLP problem and initial guess.
    
    This catches modeling mistakes early (units, sign, domain) before
    IPOPT starts iterating.
    
    Args:
        prob: NLP problem
        x0: Initial guess
        
    Raises:
        ValueError: If preflight checks fail
    """
    try:
        # Check initial guess dimensions
        if len(x0) != len(prob.lbx):
            raise ValueError(f"Initial guess dimension {len(x0)} != variable dimension {len(prob.lbx)}")
        
        # Check that initial guess satisfies bounds (with tolerance for floating point precision)
        tolerance = 1e-12
        if not np.all(prob.lbx - tolerance <= x0) or not np.all(x0 <= prob.ubx + tolerance):
            # Debug: Find which variables violate bounds
            lower_violations = np.where(x0 < prob.lbx - tolerance)[0]
            upper_violations = np.where(x0 > prob.ubx + tolerance)[0]
            if len(lower_violations) > 0:
                logger.error(f"Lower bound violations at indices {lower_violations[:5]}: x0={x0[lower_violations[:5]]}, lbx={prob.lbx[lower_violations[:5]]}")
            if len(upper_violations) > 0:
                logger.error(f"Upper bound violations at indices {upper_violations[:5]}: x0={x0[upper_violations[:5]]}, ubx={prob.ubx[upper_violations[:5]]}")
            raise ValueError("Initial guess violates variable bounds")
        
        # Variable scaling diagnostics
        x0_scale = np.max(np.abs(x0))
        lbx_scale = np.max(np.abs(prob.lbx[np.isfinite(prob.lbx)]))
        ubx_scale = np.max(np.abs(prob.ubx[np.isfinite(prob.ubx)]))
        logger.info(f"Variable scaling: x0_max={x0_scale:.2e}, lbx_max={lbx_scale:.2e}, ubx_max={ubx_scale:.2e}")
        
        # Check for potential scaling issues
        if x0_scale > 1e6 or x0_scale < 1e-6:
            logger.warning(f"Initial guess has extreme scaling: x0_max={x0_scale:.2e}")
        if lbx_scale > 1e6 or lbx_scale < 1e-6:
            logger.warning(f"Lower bounds have extreme scaling: lbx_max={lbx_scale:.2e}")
        if ubx_scale > 1e6 or ubx_scale < 1e-6:
            logger.warning(f"Upper bounds have extreme scaling: ubx_max={ubx_scale:.2e}")
        
        # Evaluate objective at initial guess
        f0 = float(prob.fun(x0, prob.p_val))
        if not np.isfinite(f0):
            raise ValueError(f"Non-finite objective at initial guess: f0={f0}")
        
        # Evaluate constraints at initial guess (handle empty constraints)
        if len(prob.lbg) > 0:
            g0_raw = np.array(prob.g_fun(x0, prob.p_val))
            # Handle both scalar and vector constraints
            if g0_raw.ndim == 0:  # Scalar constraint
                g0 = np.array([g0_raw])
            else:  # Vector constraint
                g0 = g0_raw.squeeze()
                if g0.ndim == 0:  # Still scalar after squeeze
                    g0 = np.array([g0])
            
            if not np.all(np.isfinite(g0)):
                raise ValueError("Non-finite constraints at initial guess")
            
            # Check constraint dimensions
            if len(g0) != len(prob.lbg):
                raise ValueError(f"Constraint dimension {len(g0)} != bound dimension {len(prob.lbg)}")
            
            # Check constraint feasibility
            tolerance = 1e-12
            g_violations = np.where((g0 < prob.lbg - tolerance) | (g0 > prob.ubg + tolerance))[0]
            if len(g_violations) > 0:
                logger.error(f"Constraint violations at indices {g_violations[:5]}: g0={g0[g_violations[:5]]}, lbg={prob.lbg[g_violations[:5]]}, ubg={prob.ubg[g_violations[:5]]}")
                raise ValueError(f"Initial guess violates constraints at {len(g_violations)} indices")
            
            # Enhanced constraint diagnostics
            g_max_violation = np.max(np.maximum(0, prob.lbg - g0)) + np.max(np.maximum(0, g0 - prob.ubg))
            logger.info(f"Constraint characteristics: {len(prob.lbg)} constraints, "
                       f"lbg_range=[{np.min(prob.lbg):.2e}, {np.max(prob.lbg):.2e}], "
                       f"ubg_range=[{np.min(prob.ubg):.2e}, {np.max(prob.ubg):.2e}], "
                       f"max_violation={g_max_violation:.6e}")
        else:
            g0 = np.array([])
        
        logger.info(f"Preflight checks passed: f0={f0:.6e}, g0_norm={_inf_norm(g0):.6e}")
        
    except Exception as e:
        logger.error(f"Preflight check failed: {e}")
        raise ValueError(f"Preflight failed: {e}")


def compute_kkt_residuals(prob: NLPProblem, sol: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute KKT residuals with correct mathematical formulation.
    
    This function implements the correct KKT conditions:
    - Stationarity: ∇f + Jg^T λ - lam_x = 0 (where lam_x = z_U - z_L)
    - Primal feasibility: constraint and bound violations
    - Complementarity: with proper infinite bound masking
    
    Args:
        prob: NLP problem
        sol: Solution dictionary
        
    Returns:
        Dictionary of KKT residuals
    """
    if not sol.get('success', False) or sol.get('is_fallback', False):
        return {
            'stationarity': np.inf,
            'primal': np.inf,
            'dual': np.inf,
            'complementarity': np.inf
        }
    
    try:
        # Robust array handling
        x = np.asarray(sol['x']).flatten()
        lam_g = np.atleast_1d(sol.get('lam_g', np.array([]))).astype(float).flatten()
        lam_x = np.atleast_1d(sol.get('lam_x', np.zeros_like(x))).astype(float).flatten()
        
        # Evaluate functions
        grad_f = np.asarray(prob.grad_f(x, prob.p_val)).flatten()
        g_val_raw = prob.g_fun(x, prob.p_val)
        g_val = np.atleast_1d(np.asarray(g_val_raw)).flatten()
        Jg = np.asarray(prob.jac_g(x, prob.p_val))
        
        # CRITICAL FIX: Correct shape check
        if lam_g.size and Jg.shape[0] != lam_g.size:
            raise ValueError(f"Jg shape {Jg.shape} incompatible with lam_g length {lam_g.size}")
        
        # CRITICAL FIX: Correct stationarity with signed lam_x
        # Stationarity: ∇f + Jg^T λ - lam_x = 0 (where lam_x = z_U - z_L)
        if lam_g.size:
            stationarity_term = grad_f + Jg.T @ lam_g - lam_x
        else:
            stationarity_term = grad_f - lam_x
        stationarity = np.linalg.norm(stationarity_term, ord=np.inf)
        
        # Primal feasibility: constraints and variable bounds
        if lam_g.size or len(g_val):
            g_viol = np.maximum(prob.lbg - g_val, 0.0) + np.maximum(g_val - prob.ubg, 0.0)
        else:
            g_viol = 0.0
        
        x_viol = np.maximum(prob.lbx - x, 0.0) + np.maximum(x - prob.ubx, 0.0)
        primal = max(
            np.max(np.abs(g_viol)) if np.size(g_viol) else 0.0,
            np.max(np.abs(x_viol))
        )
        
        # CRITICAL FIX: Correct complementarity with infinite bound masking
        z_U = np.clip(lam_x, 0.0, np.inf)  # Upper bound multipliers
        z_L = np.clip(-lam_x, 0.0, np.inf)  # Lower bound multipliers
        
        maskL = np.isfinite(prob.lbx)
        maskU = np.isfinite(prob.ubx)
        
        comp = 0.0
        if maskL.any():
            comp += np.max(np.abs((x[maskL] - prob.lbx[maskL]) * z_L[maskL]))
        if maskU.any():
            comp += np.max(np.abs((prob.ubx[maskU] - x[maskU]) * z_U[maskU]))
        
        return {
            'stationarity': float(stationarity),
            'primal': float(primal),
            'dual': float(np.linalg.norm(lam_g, ord=np.inf)),
            'complementarity': float(comp)
        }
        
    except Exception as e:
        logger.error(f"KKT residual computation failed: {e}")
        return {
            'stationarity': np.inf,
            'primal': np.inf,
            'dual': np.inf,
            'complementarity': np.inf
        }


def solve_with_improvements(prob: NLPProblem, 
                          x0: np.ndarray, 
                          ipopt_opts: Optional[Dict[str, Any]] = None,
                          warm_start: Optional["WarmStart"] = None) -> Dict[str, Any]:
    """
    Solve NLP problem with robust error handling and diagnostics.
    
    Args:
        prob: Standardized NLP problem
        x0: Initial guess
        ipopt_opts: Optional IPOPT options (uses defaults if None)
        warm_start: Optional warm-start data with 'lam_x' and 'lam_g' keys
        
    Returns:
        Standardized solution dictionary
    """
    logger.debug(f"solve_with_improvements called with x0.shape={x0.shape}")
    logger.debug(f"prob.x.shape={prob.x.shape}, prob.f.shape={prob.f.shape}, prob.g.shape={prob.g.shape}")
    # Preflight checks
    try:
        logger.debug("Starting preflight checks...")
        _preflight(prob, x0)
        logger.debug("Preflight checks passed")
    except Exception as e:
        logger.debug(f"Preflight checks failed: {e}")
        return _fallback_result(f"Preflight failed: {e}", {'stage': 'preflight'})
    
    # Create solver with warm-start options
    opts = ipopt_opts or default_ipopt_options()
    if warm_start:
        # Enable warm start for dual variables
        opts['ipopt']['warm_start_init_point'] = 'yes'
        opts['ipopt']['warm_start_bound_push'] = 1e-6
        opts['ipopt']['warm_start_mult_bound_push'] = 1e-6
        opts['ipopt']['warm_start_slack_bound_push'] = 1e-6
    
    try:
        logger.debug(f"Creating solver with opts: {opts}")
        solver = ca.nlpsol('S', 'ipopt',
                          {'x': prob.x, 'p': prob.p, 'f': prob.f, 'g': prob.g},
                          opts)
        logger.debug("Solver creation successful")
    except Exception as e:
        logger.debug(f"Solver creation failed: {e}")
        return _fallback_result(f"Solver creation failed: {e}", {'stage': 'create'})
    
    # Solve with optional warm-start
    try:
        solve_args = {
            'x0': x0, 
            'p': prob.p_val, 
            'lbx': prob.lbx, 
            'ubx': prob.ubx, 
            'lbg': prob.lbg, 
            'ubg': prob.ubg
        }
        
        # CRITICAL: Add all three warm-start components
        if warm_start:
            solve_args['lam_x0'] = warm_start.lam_x0
            solve_args['lam_g0'] = warm_start.lam_g0
        
        r = solver(**solve_args)
    except Exception as e:
        return _fallback_result(f"Numeric failure: {e}", {'stage': 'solve'})
    
    # Extract results
    stats = solver.stats()
    ok = stats.get('success', False)
    status = stats.get('return_status', 'UNKNOWN')
    
    # Enhanced error logging and diagnostics
    logger.info(f"Solver completed: success={ok}, status={status}")
    logger.info(f"Solver stats: {stats}")
    
    # Check constraint feasibility at solution
    x = np.array(r['x']).squeeze()
    if len(x) > 0:
        # Variable bounds feasibility
        lbx_violations = np.where(x < prob.lbx - 1e-8)[0]
        ubx_violations = np.where(x > prob.ubx + 1e-8)[0]
        
        if len(lbx_violations) > 0:
            logger.error(f"Lower bound violations at indices {lbx_violations[:5]}: x={x[lbx_violations[:5]]}, lbx={prob.lbx[lbx_violations[:5]]}")
        if len(ubx_violations) > 0:
            logger.error(f"Upper bound violations at indices {ubx_violations[:5]}: x={x[ubx_violations[:5]]}, ubx={prob.ubx[ubx_violations[:5]]}")
        
        # Constraint feasibility
        if len(prob.lbg) > 0:
            try:
                g_sol = np.array(prob.g_fun(x, prob.p_val)).squeeze()
                g_violations = np.where((g_sol < prob.lbg - 1e-8) | (g_sol > prob.ubg + 1e-8))[0]
                if len(g_violations) > 0:
                    logger.error(f"Constraint violations at indices {g_violations[:5]}: g={g_sol[g_violations[:5]]}, lbg={prob.lbg[g_violations[:5]]}, ubg={prob.ubg[g_violations[:5]]}")
                else:
                    logger.info(f"All {len(prob.lbg)} constraints satisfied within tolerance")
            except Exception as e:
                logger.error(f"Could not evaluate constraints at solution: {e}")
        
        # Variable scaling diagnostics
        x_scale = np.max(np.abs(x))
        lbx_scale = np.max(np.abs(prob.lbx[np.isfinite(prob.lbx)]))
        ubx_scale = np.max(np.abs(prob.ubx[np.isfinite(prob.ubx)]))
        logger.info(f"Variable scaling: x_max={x_scale:.2e}, lbx_max={lbx_scale:.2e}, ubx_max={ubx_scale:.2e}")
        
        # Check for numerical issues
        if np.any(np.isnan(x)) or np.any(np.isinf(x)):
            logger.error(f"Solution contains NaN or Inf values: nan_count={np.sum(np.isnan(x))}, inf_count={np.sum(np.isinf(x))}")
    
    if not ok:
        logger.error(f"Solver failed with status: {status}")
        logger.error(f"Full solver stats: {stats}")
        # Log IPOPT-specific error information if available
        if 'return_status' in stats:
            logger.error(f"IPOPT return status: {stats['return_status']}")
        if 't_wall_total' in stats:
            logger.error(f"Total wall time: {stats['t_wall_total']:.2f}s")
        if 'iter_count' in stats:
            logger.error(f"Iteration count: {stats['iter_count']}")
    
    # Extract multipliers as returned by CasADi/IPOPT
    if ok:
        lam_x = np.array(r.get('lam_x', [])).squeeze()
        lam_g = np.array(r.get('lam_g', [])).squeeze()
        
        # Reconstruct separate nonnegative bound multipliers
        # CasADi convention: lam_x > 0 => upper bound active, lam_x < 0 => lower bound active
        # IPOPT KKT: ∇f + J_g^T λ + z_L - z_U = 0, where lam_x = z_U - z_L
        z_U = np.clip(lam_x, 0.0, np.inf)   # upper bound multipliers (nonnegative)
        z_L = np.clip(-lam_x, 0.0, np.inf)  # lower bound multipliers (nonnegative)
    else:
        lam_x = np.array([])
        lam_g = np.array([])
        z_L = np.array([])
        z_U = np.array([])
    
    out = {
        'success': ok,
        'status': status,
        'message': stats.get('return_status', ''),
        'iter_count': int(stats.get('iter_count', 0)),
        'x': x,
        'f': float(np.array(r['f']).squeeze()) if ok else np.nan,
        'lam_x': lam_x,  # signed (z_U - z_L)
        'lam_g': lam_g,
        'z_L': z_L,      # lower bound multipliers (nonnegative)
        'z_U': z_U,      # upper bound multipliers (nonnegative)
        'is_fallback': False,
        'meta': {'ipopt': stats}
    }
    
    # Change: Only compute KKT diagnostics for real successes
    logger.debug(f"Solver result: ok={ok}, status={status}")
    if ok and not out.get('is_fallback', False):
        logger.debug("Computing KKT residuals for successful solve")
        out['kkt'] = compute_kkt_residuals(prob, out)
    else:
        logger.debug("Not computing KKT residuals for failed or fallback solve")
        out['kkt'] = None
        out['diagnostics_status'] = 'not_computed'
    
    return out
