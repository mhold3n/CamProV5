"""
IPOPT Options and Configuration

This module provides robust default IPOPT options and configuration
to ensure consistent solver behavior across tests and production.
"""

from typing import Dict, Any


def default_ipopt_options() -> Dict[str, Any]:
    """
    Return robust default IPOPT options.
    
    These options are designed for stability and reliability:
    - Conservative tolerances for robust convergence
    - Adaptive barrier strategy for handling difficult problems
    - Limited-memory Hessian approximation for efficiency
    - Gradient-based scaling for automatic conditioning
    
    Returns:
        Dictionary of IPOPT options
    """
    return {
        'ipopt': {
            'print_level': 0,  # Minimal output
            'max_iter': 2000,
            'tol': 1e-6,
            'constr_viol_tol': 1e-6,
            'compl_inf_tol': 1e-6,
            'acceptable_tol': 1e-4,
            'acceptable_constr_viol_tol': 1e-4,
            'mu_strategy': 'adaptive',
            'hessian_approximation': 'exact',
            'linear_solver': 'mumps',
            'bound_relax_factor': 1e-8,
            'honor_original_bounds': 'yes'
        },
        'print_time': False,
        'verbose': False
    }


def continuation_ipopt_options(stage: int, total_stages: int = 3) -> Dict[str, Any]:
    """
    Return IPOPT options for continuation/homotopy stages.
    
    Args:
        stage: Current stage (1-based)
        total_stages: Total number of stages
        
    Returns:
        Dictionary of IPOPT options for the given stage
    """
    base_opts = default_ipopt_options()
    
    if stage == 1:
        # Stage 1: Very relaxed for initial feasibility
        base_opts.update({
            'tol': 1e-4,
            'acceptable_tol': 1e-3,
            'constr_viol_tol': 1e-4,
            'max_iter': 1000,
            'mu_strategy': 'monotone',
            'hessian_approximation': 'limited-memory'
        })
    elif stage == 2:
        # Stage 2: Moderate tightening
        base_opts.update({
            'tol': 1e-5,
            'acceptable_tol': 1e-4,
            'constr_viol_tol': 1e-5,
            'max_iter': 1500,
            'mu_strategy': 'adaptive'
        })
    else:
        # Stage 3+: Final tight tolerances
        base_opts.update({
            'tol': 1e-6,
            'acceptable_tol': 1e-5,
            'constr_viol_tol': 1e-6,
            'max_iter': 2000,
            'mu_strategy': 'adaptive',
            'hessian_approximation': 'exact'  # Use exact Hessian for final stage
        })
    
    return base_opts


def user_scaling_ipopt_options() -> Dict[str, Any]:
    """
    Return IPOPT options for user-provided scaling.
    
    Use this when you provide explicit variable/constraint scaling.
    
    Returns:
        Dictionary of IPOPT options with user scaling enabled
    """
    opts = default_ipopt_options()
    opts.update({
        'nlp_scaling_method': 'user-scaling',
        'obj_scaling_factor': 1.0,
        'nlp_scaling_max_gradient': 100.0
    })
    return opts


def debug_ipopt_options() -> Dict[str, Any]:
    """
    Return IPOPT options for debugging and development.
    
    These options provide verbose output for troubleshooting.
    
    Returns:
        Dictionary of IPOPT options with debug settings
    """
    opts = default_ipopt_options()
    opts.update({
        'print_level': 12,  # Maximum verbosity
        'print_user_options': 'yes',
        'print_options_documentation': 'yes',
        'print_timing_statistics': 'yes',
        'print_frequency_iter': 1,
        'print_frequency_time': 1.0
    })
    return opts
