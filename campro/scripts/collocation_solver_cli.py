#!/usr/bin/env python3
"""
Collocation Solver CLI Interface

This script provides a command-line interface to the CasADi + IPOPT
collocation solver for integration with the Kotlin motion law engine.
"""

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, Any

# Add the campro module to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from campro.solvers import CollocationSolver, CollocationParameters
    from campro.solvers.litvin_constraints import LitvinParameters
    from campro.solvers.numerical_methods import NumericalParameters
    import logging
    
    DEPENDENCIES_AVAILABLE = True
    
except ImportError as e:
    print(f"Warning: Required dependencies not available: {e}", file=sys.stderr)
    DEPENDENCIES_AVAILABLE = False


def setup_logging(log_file: Path) -> None:
    """Set up logging to file."""
    logging.basicConfig(
        filename=str(log_file),
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_input_parameters(input_file: Path) -> Dict[str, Any]:
    """Load input parameters from JSON file."""
    with open(input_file, 'r') as f:
        params = json.load(f)
    return params


def convert_parameters_to_solver_format(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Kotlin parameters to Python solver format."""
    motion_params = {
        # Basic motion parameters
        'strokeLengthMm': params.get('strokeLengthMm', 10.0),
        'samplingStepDeg': params.get('samplingStepDeg', 1.0),
        'dwellTdcDeg': params.get('dwellTdcDeg', 0.0),
        'dwellBdcDeg': params.get('dwellBdcDeg', 0.0),
        'rampAfterTdcDeg': params.get('rampAfterTdcDeg', 0.0),
        'rampBeforeBdcDeg': params.get('rampBeforeBdcDeg', 0.0),
        'rampAfterBdcDeg': params.get('rampAfterBdcDeg', 0.0),
        'rampBeforeTdcDeg': params.get('rampBeforeTdcDeg', 0.0),
        'upFraction': params.get('upFraction', 0.5),
        'rpm': params.get('rpm', 3000.0),
        'rampProfile': params.get('rampProfile', 'Cycloidal'),
    }
    
    return motion_params


def create_solver_parameters(params: Dict[str, Any]) -> CollocationParameters:
    """Create CollocationParameters from input parameters."""
    collocation_params = params.get('collocation_params', {})
    
    # Create Litvin parameters if conjugacy constraints are enabled
    litvin_params = None
    enable_litvin = collocation_params.get('enable_litvin_constraints', False)
    if enable_litvin:
        litvin_config = collocation_params.get('litvin_parameters', {})
        litvin_params = LitvinParameters(
            center_distance=litvin_config.get('center_distance', 50.0),
            cam_base_radius=litvin_config.get('cam_base_radius', 40.0),
            pressure_angle_max_deg=litvin_config.get('pressure_angle_max_deg', 30.0),
            tooth_thickness_min=litvin_config.get('tooth_thickness_min', 1.0),
            curvature_radius_min=litvin_config.get('curvature_radius_min', 2.0),
            contact_ratio_min=litvin_config.get('contact_ratio_min', 1.2),
            arc_length_tolerance=litvin_config.get('arc_length_tolerance', 0.01)
        )
    
    # Create numerical parameters if enabled
    numerical_params = None
    enable_numerical = collocation_params.get('enable_numerical_guards', True)
    if enable_numerical:
        numerical_config = collocation_params.get('numerical_parameters', {})
        numerical_params = NumericalParameters(
            ks_rho=numerical_config.get('ks_rho', 10.0),
            ks_smooth_factor=numerical_config.get('ks_smooth_factor', 1e-3),
            bound_margin=numerical_config.get('bound_margin', 1e-6),
            bound_smoothness=numerical_config.get('bound_smoothness', 1e-2),
            continuation_steps=numerical_config.get('continuation_steps', 3),
            continuation_factor=numerical_config.get('continuation_factor', 0.1),
            warm_start_noise=numerical_config.get('warm_start_noise', 1e-3),
            warm_start_damping=numerical_config.get('warm_start_damping', 0.8)
        )
    
    return CollocationParameters(
        node_count=collocation_params.get('node_count', 16),
        node_type=collocation_params.get('node_type', 'LGL'),
        max_iterations=collocation_params.get('max_iterations', 1000),
        tolerance=collocation_params.get('tolerance', 1e-8),
        constraint_tolerance=collocation_params.get('constraint_tolerance', 1e-6),
        smoothness_weight=collocation_params.get('smoothness_weight', 1e-3),
        acceleration_limit=collocation_params.get('acceleration_limit', 1000.0),
        jerk_limit=collocation_params.get('jerk_limit', 5000.0),
        use_continuation=collocation_params.get('use_continuation', True),
        use_warm_start=collocation_params.get('use_warm_start', True),
        initial_guess_type=collocation_params.get('initial_guess_type', 'sinusoidal'),
        enable_litvin_constraints=enable_litvin,
        litvin_parameters=litvin_params,
        enable_numerical_guards=enable_numerical,
        numerical_parameters=numerical_params
    )


def solve_collocation_problem(motion_params: Dict[str, Any], solver_params: CollocationParameters) -> Dict[str, Any]:
    """Solve the collocation problem and return results."""
    logger = logging.getLogger(__name__)
    logger.info("Starting collocation solver")
    
    # Create and configure solver
    solver = CollocationSolver(solver_params)
    
    # Solve the problem
    solution = solver.solve(motion_params)
    
    # Convert solution to JSON-serializable format
    result = {
        'success': solution.success,
        'execution_time': solution.execution_time,
        'iterations': solution.iterations,
        'theta_grid': solution.theta_grid.tolist(),
        'position': solution.position.tolist(),
        'velocity': solution.velocity.tolist(),
        'acceleration': solution.acceleration.tolist(),
        'objective_value': solution.objective_value,
        'constraint_violation': solution.constraint_violation,
        'solver_status': solution.solver_status,
        'return_code': solution.return_code,
        'node_count': solution.node_count,
        'discretization_type': solution.discretization_type,
        'solver_info': solver.get_solver_info()
    }
    
    logger.info(f"Collocation solver completed: success={solution.success}, "
                f"time={solution.execution_time:.3f}s, iterations={solution.iterations}")
    
    return result


def save_solution(solution: Dict[str, Any], output_file: Path) -> None:
    """Save solution to JSON file."""
    with open(output_file, 'w') as f:
        json.dump(solution, f, indent=2)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='CasADi + IPOPT Collocation Solver')
    parser.add_argument('--input', required=True, type=Path,
                       help='Input JSON file with motion parameters')
    parser.add_argument('--output', required=True, type=Path,
                       help='Output JSON file for solution')
    parser.add_argument('--log', required=True, type=Path,
                       help='Log file for solver output')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log)
    logger = logging.getLogger(__name__)
    
    try:
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies (CasADi, NumPy, SciPy) not available")
        
        logger.info("Collocation solver CLI started")
        logger.info(f"Input: {args.input}")
        logger.info(f"Output: {args.output}")
        logger.info(f"Log: {args.log}")
        
        # Load input parameters
        logger.debug("Loading input parameters")
        input_params = load_input_parameters(args.input)
        
        # Convert parameters
        motion_params = convert_parameters_to_solver_format(input_params)
        solver_params = create_solver_parameters(input_params)
        
        logger.debug(f"Motion parameters: {motion_params}")
        logger.debug(f"Solver parameters: {solver_params}")
        
        # Solve the problem
        logger.info("Starting optimization")
        solution = solve_collocation_problem(motion_params, solver_params)
        
        # Save solution
        logger.debug("Saving solution")
        save_solution(solution, args.output)
        
        if solution['success']:
            logger.info("Collocation solver completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Collocation solver failed: {solution['solver_status']}")
            sys.exit(1)
            
    except Exception as e:
        error_msg = f"Collocation solver error: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Try to save error information
        try:
            error_solution = {
                'success': False,
                'execution_time': 0.0,
                'iterations': 0,
                'theta_grid': [],
                'position': [],
                'velocity': [],
                'acceleration': [],
                'objective_value': float('inf'),
                'constraint_violation': float('inf'),
                'solver_status': f'Error: {str(e)}',
                'return_code': -1,
                'node_count': 0,
                'discretization_type': 'unknown',
                'error_traceback': traceback.format_exc()
            }
            save_solution(error_solution, args.output)
        except Exception:
            pass  # If we can't save the error, just exit
        
        print(error_msg, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
