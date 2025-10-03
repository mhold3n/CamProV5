"""
Centralized NLP Problem Builder

This module provides a single builder that constructs NLP problems from stage parameters,
handling both parameterization and structural changes correctly.
"""

import casadi as ca
import numpy as np
from typing import Dict, Any, Optional
from .nlp_types import NLPProblem, StageParams


def build_nlp_problem_from_stage(params: StageParams, base_meta: Dict[str, Any], original_meta: Optional[Dict[str, Any]] = None) -> NLPProblem:
    """
    Build the symbolic NLP (x,p,f,g) for the given stage parameters,
    compile numeric functions, and attach bounds/params/meta.
    
    Args:
        params: Stage parameters including grid, degree, and smoothing parameters
        base_meta: Base metadata including parameter map and factory functions
        
    Returns:
        Complete NLPProblem with compiled functions and structure signature
    """
    # Extract structural parameters
    grid = getattr(params, 'grid', None)
    if grid is not None:
        grid = np.asarray(grid, dtype=float)
        N = grid.shape[0]
        if params.grid_nodes != N:
            params.grid_nodes = N
        params.grid = grid
    else:
        N = params.grid_nodes
    deg = params.colloc_degree
    act = params.enable_constraints
    
    # Build decision vector and parameter vector using factory functions
    nx = base_meta['nx_for'](N, deg)
    np_total = base_meta['np']
    
    x = ca.SX.sym('x', nx)
    p = ca.SX.sym('p', np_total)
    
    # Map stage scalars into p slots
    p_val = np.zeros((np_total,), dtype=float)
    pmap = base_meta['pmap']
    p_val[pmap['epsilon_valve']] = params.epsilon_valve
    p_val[pmap['epsilon_friction']] = params.epsilon_friction
    p_val[pmap['stress_factor']] = params.stress_factor
    
    # Construct f(x,p), g(x,p) using current grid/degree/activations
    f, g = base_meta['make_fg'](x, p, params)
    
    # Get stroke length from motion_params if available
    stroke_length_m = 0.01  # Default value
    if original_meta is not None and 'motion_params' in original_meta:
        motion_params = original_meta['motion_params']
        stroke_length_m = motion_params.get('strokeLengthMm', 10.0) / 1000.0  # Convert mm to meters
    
    lbx, ubx, lbg, ubg = base_meta['make_bounds'](N, deg, act, stroke_length_m)
    
    # Compile numeric functions once
    fun = ca.Function('f', [x, p], [f])
    grad_f = ca.Function('grad_f', [x, p], [ca.gradient(f, x)])
    g_fun = ca.Function('g', [x, p], [g])
    jac_g = ca.Function('jac_g', [x, p], [ca.jacobian(g, x)])
    
    # Compute structural signature for rebuild decisions
    nx_actual = int(x.shape[0])
    ng = int(g.shape[0])
    spars = ca.jacobian(g, x).sparsity()
    jac_sig = (int(spars.nnz()), int(spars.shape[0]*spars.shape[1]))
    structure_sig = (nx_actual, ng, deg, jac_sig)
    
    # Create metadata
    meta = {
        'stage_params': params,
        'pmap': pmap,
        'np': np_total,
        'grid': grid,
        **base_meta
    }
    
    # Preserve motion_params from original metadata if available
    if original_meta is not None and 'motion_params' in original_meta:
        meta['motion_params'] = original_meta['motion_params']
    
    return NLPProblem(
        x=x, p=p, f=f, g=g,
        fun=fun, grad_f=grad_f, g_fun=g_fun, jac_g=jac_g,
        lbx=np.asarray(lbx, dtype=float), 
        ubx=np.asarray(ubx, dtype=float),
        lbg=np.asarray(lbg, dtype=float), 
        ubg=np.asarray(ubg, dtype=float),
        p_val=p_val,
        structure_sig=structure_sig,
        meta=meta
    )


def update_p_val_for_stage(nlp: NLPProblem, params: StageParams) -> NLPProblem:
    """
    Update parameter vector without rebuild for pure numeric changes.
    
    Args:
        nlp: Existing NLP problem
        params: New stage parameters
        
    Returns:
        Updated NLP problem with new parameter values
    """
    # Update parameter vector without rebuild
    p_val = np.array(nlp.p_val, copy=True)
    pmap = nlp.meta['pmap']
    p_val[pmap['epsilon_valve']] = params.epsilon_valve
    p_val[pmap['epsilon_friction']] = params.epsilon_friction
    p_val[pmap['stress_factor']] = params.stress_factor
    
    # Update the NLP problem
    nlp.p_val = p_val
    nlp.meta['stage_params'] = params
    
    return nlp


def should_rebuild_nlp(current_nlp: NLPProblem, new_params: StageParams) -> bool:
    """
    Determine if NLP needs to be rebuilt based on structural changes.
    
    Args:
        current_nlp: Current NLP problem
        new_params: New stage parameters
        
    Returns:
        True if rebuild is needed, False if parameter update is sufficient
    """
    if current_nlp is None:
        return True
    
    # Check if structure changes
    current_params = current_nlp.meta.get('stage_params', None)
    
    if current_params is None:
        return True
    
    # Structure changes if:
    # 1. Grid size changes
    # 2. Collocation degree changes  
    # 3. Constraint activation changes
    structure_changes = (
        new_params.grid_nodes != current_params.grid_nodes or
        new_params.colloc_degree != current_params.colloc_degree or
        new_params.enable_constraints != current_params.enable_constraints
    )
    
    return structure_changes
