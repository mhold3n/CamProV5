"""
Standardized NLP Problem Schema

This module provides a canonical container for NLP problems that unifies
the interface between solver, diagnostics, and tests.
"""

from dataclasses import dataclass
import casadi as ca
import numpy as np
from typing import Dict, Any, Tuple
from campro.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StageParams:
    """Parameters for a continuation stage."""
    epsilon_valve: float
    epsilon_friction: float
    stress_factor: float
    grid_nodes: int
    colloc_degree: int
    enable_constraints: Dict[str, bool]  # e.g., {"stress": True, "jerk": True}
    tolerance: float
    max_iter: int
    description: str


@dataclass
class NLPProblem:
    """
    Canonical NLP problem container with both symbolic and compiled functions.
    
    This eliminates the "nlp vs. nlp['nlp']" mismatches by providing
    a single source of truth for problem structure.
    """
    # Symbolic variables and functions
    x: ca.SX                    # Decision variables
    p: ca.SX                    # Parameters
    f: ca.SX                    # Objective function
    g: ca.SX                    # Constraint functions
    
    # Compiled numeric functions (evaluated at runtime)
    fun: ca.Function            # f(x,p) -> scalar
    grad_f: ca.Function         # ∇f(x,p) -> vector
    g_fun: ca.Function          # g(x,p) -> vector
    jac_g: ca.Function          # J_g(x,p) -> matrix
    
    # Bounds and parameters
    lbx: np.ndarray             # Variable lower bounds
    ubx: np.ndarray             # Variable upper bounds
    lbg: np.ndarray             # Constraint lower bounds
    ubg: np.ndarray             # Constraint upper bounds
    p_val: np.ndarray           # Numeric parameter values
    
    # Structural signature for rebuild decisions
    structure_sig: Tuple[int, int, int, Tuple[int, int]]  # (nx, ng, deg, jac_sig)
    
    # Metadata
    meta: Dict[str, Any]        # Additional problem metadata


def build_nlp_problem(sym: Dict[str, ca.SX], 
                     bnd: Dict[str, np.ndarray], 
                     meta: Dict[str, Any]) -> NLPProblem:
    """
    Build a standardized NLP problem from symbolic components.
    
    Args:
        sym: Dictionary with 'x', 'p', 'f', 'g' CasADi SX objects
        bnd: Dictionary with 'lbx', 'ubx', 'lbg', 'ubg' bounds
        meta: Additional metadata including 'p_val' parameter values
        
    Returns:
        NLPProblem with compiled functions
    """
    x, p, f, g = sym['x'], sym['p'], sym['f'], sym['g']
    
    logger.debug(f"Building NLP problem: x.shape={x.shape}, f.shape={f.shape}, g.shape={g.shape}")
    
    # Compile functions once for use everywhere
    logger.debug("Compiling objective function...")
    fun = ca.Function('f', [x, p], [f])
    logger.debug("Compiling gradient function...")
    grad_f = ca.Function('grad_f', [x, p], [ca.gradient(f, x)])
    logger.debug("Compiling constraint function...")
    g_fun = ca.Function('g', [x, p], [g])
    logger.debug("Compiling Jacobian function...")
    try:
        jac_g = ca.Function('jac_g', [x, p], [ca.jacobian(g, x)])
        logger.debug("Jacobian compilation successful")
    except Exception as e:
        logger.debug(f"Jacobian compilation failed: {e}")
        raise
    
    # Compute structural signature for rebuild decisions
    nx = int(x.shape[0])
    ng = int(g.shape[0])
    deg = meta.get('colloc_degree', 1)  # Default degree
    spars = ca.jacobian(g, x).sparsity()
    jac_sig = (int(spars.nnz()), int(spars.shape[0]*spars.shape[1]))  # coarse but cheap
    structure_sig = (nx, ng, deg, jac_sig)
    
    return NLPProblem(
        x=x, p=p, f=f, g=g,
        fun=fun, grad_f=grad_f, g_fun=g_fun, jac_g=jac_g,
        lbx=bnd['lbx'], ubx=bnd['ubx'], 
        lbg=bnd['lbg'], ubg=bnd['ubg'],
        p_val=meta.get('p_val', np.array([])),
        structure_sig=structure_sig,
        meta=meta
    )


def validate_nlp_problem(prob: NLPProblem) -> bool:
    """
    Validate that an NLP problem is well-formed.
    
    Args:
        prob: NLP problem to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check that all required fields are present
        required_fields = ['x', 'p', 'f', 'g', 'fun', 'grad_f', 'g_fun', 'jac_g']
        for field in required_fields:
            if not hasattr(prob, field):
                return False
        
        # Check that bounds have consistent dimensions
        if len(prob.lbx) != len(prob.ubx):
            return False
        if len(prob.lbg) != len(prob.ubg):
            return False
        
        # Check that bounds are valid (lb <= ub)
        if not np.all(prob.lbx <= prob.ubx):
            return False
        if not np.all(prob.lbg <= prob.ubg):
            return False
            
        return True
        
    except Exception:
        return False
