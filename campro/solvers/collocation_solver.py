"""
Collocation-based Motion Law Solver using CasADi + IPOPT

This module implements the collocation approach described in the 
collocation solution method documentation, treating profile generation
as a global algebraic system with NLP optimization.
"""

import numpy as np
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict

try:
    import casadi as ca
    CASADI_AVAILABLE = True
except ImportError:
    CASADI_AVAILABLE = False

import logging
from .nlp_formulation import MotionNLP, ConstraintBuilder
from .discretization import CollocationGrid, get_cache_stats, clear_matrix_cache
from .litvin_constraints import LitvinParameters
from .numerical_methods import NumericalGuards, NumericalParameters
from .validation import DenseValidator, ValidationLimits

logger = logging.getLogger(__name__)


@dataclass
class CollocationParameters:
    """Parameters for the collocation solver."""
    
    # Discretization parameters
    node_count: int = 16
    node_type: str = "LGL"  # LGL, Chebyshev, Uniform
    
    # Solver parameters
    max_iterations: int = 1000
    tolerance: float = 1e-8
    constraint_tolerance: float = 1e-6
    
    # Regularization parameters
    smoothness_weight: float = 1e-3
    acceleration_limit: float = 1000.0
    jerk_limit: float = 5000.0
    
    # Continuation strategy
    use_continuation: bool = True
    continuation_steps: int = 3
    
    # Warm start
    use_warm_start: bool = True
    initial_guess_type: str = "sinusoidal"  # sinusoidal, piecewise, custom
    
    # Litvin conjugacy constraints
    enable_litvin_constraints: bool = False
    litvin_parameters: Optional[LitvinParameters] = None
    
    # Numerical methods and guards
    enable_numerical_guards: bool = True
    numerical_parameters: Optional[NumericalParameters] = None
    
    # Dense validation
    enable_dense_validation: bool = False
    validation_limits: Optional[ValidationLimits] = None


@dataclass
class CollocationSolution:
    """Solution from the collocation solver."""
    
    success: bool
    execution_time: float
    iterations: int
    
    # Solution data
    theta_grid: np.ndarray
    position: np.ndarray
    velocity: np.ndarray
    acceleration: np.ndarray
    
    # Objective and constraint information
    objective_value: float
    constraint_violation: float
    
    # Solver status
    solver_status: str
    return_code: int
    
    # Validation information
    validation_report: Optional[Any] = None  # DenseValidationReport
    validation_passed: bool = True
    
    # Meta information
    node_count: int = 0
    discretization_type: str = "Unknown"


class CollocationSolver:
    """
    Collocation-based motion law solver.
    
    This solver implements the collocation method for cam profile generation
    using CasADi for symbolic differentiation and IPOPT for NLP optimization.
    """
    
    def __init__(self, parameters: Optional[CollocationParameters] = None):
        """Initialize the collocation solver."""
        self.parameters = parameters or CollocationParameters()
        self.nlp_formulation: Optional[MotionNLP] = None
        self.last_solution: Optional[CollocationSolution] = None
        
        # Initialize numerical guards if enabled
        self.numerical_guards = None
        if self.parameters.enable_numerical_guards:
            numerical_params = self.parameters.numerical_parameters or NumericalParameters()
            self.numerical_guards = NumericalGuards(numerical_params)
        
        if not CASADI_AVAILABLE:
            raise ImportError(
                "CasADi is required for the collocation solver. "
                "Install with: pip install casadi"
            )
    
    def solve(self, motion_params: Dict[str, Any]) -> CollocationSolution:
        """
        Solve the motion law generation problem using collocation.
        
        Args:
            motion_params: Dictionary containing motion law parameters
            
        Returns:
            CollocationSolution with the optimization results
        """
        logger.info(f"Starting collocation solver with {self.parameters.node_count} nodes")
        start_time = time.time()
        
        try:
            # Phase 1: Set up discretization
            grid = self._create_collocation_grid()
            
            # Phase 2: Build NLP formulation
            nlp = self._build_nlp_formulation(motion_params, grid)
            
            # Phase 3: Solve optimization problem
            solution_data = self._solve_nlp(nlp, motion_params)
            
            # Phase 4: Post-process solution
            solution = self._post_process_solution(solution_data, grid, start_time, motion_params)
            
            self.last_solution = solution
            return solution
            
        except Exception as e:
            logger.error(f"Collocation solver failed: {str(e)}")
            execution_time = time.time() - start_time
            
            # Return failed solution
            return CollocationSolution(
                success=False,
                execution_time=execution_time,
                iterations=0,
                theta_grid=np.array([]),
                position=np.array([]),
                velocity=np.array([]),
                acceleration=np.array([]),
                objective_value=float('inf'),
                constraint_violation=float('inf'),
                solver_status=f"Error: {str(e)}",
                return_code=-1,
                node_count=self.parameters.node_count,
                discretization_type=self.parameters.node_type
            )
    
    def _create_collocation_grid(self) -> CollocationGrid:
        """Create the collocation grid for discretization."""
        return CollocationGrid(
            node_count=self.parameters.node_count,
            node_type=self.parameters.node_type
        )
    
    def _build_nlp_formulation(self, motion_params: Dict[str, Any], grid: CollocationGrid) -> MotionNLP:
        """Build the NLP formulation for the motion law problem."""
        constraint_builder = ConstraintBuilder(motion_params, grid)
        
        nlp = MotionNLP(
            grid=grid,
            constraint_builder=constraint_builder,
            regularization_weight=self.parameters.smoothness_weight,
            enable_litvin_constraints=self.parameters.enable_litvin_constraints,
            litvin_params=self.parameters.litvin_parameters
        )
        
        self.nlp_formulation = nlp
        return nlp
    
    def _solve_nlp(self, nlp: MotionNLP, motion_params: Dict[str, Any]) -> Dict[str, Any]:
        """Solve the NLP optimization problem with numerical guards."""
        logger.info("Setting up IPOPT solver...")
        
        # Base solver options
        solver_options = {
            'ipopt.max_iter': self.parameters.max_iterations,
            'ipopt.tol': self.parameters.tolerance,
            'ipopt.constr_viol_tol': self.parameters.constraint_tolerance,
            'ipopt.print_level': 5,
            'print_time': True,
            'ipopt.linear_solver': 'mumps'
        }
        
        # Apply numerical guards to solver options
        if self.numerical_guards:
            solver_options = self.numerical_guards.setup_robust_solver_options(solver_options)
            logger.info("Applied numerical guards to solver options")
        
        # Use continuation strategy if enabled
        if self.parameters.use_continuation and self.numerical_guards:
            return self._solve_with_continuation(nlp, motion_params, solver_options)
        else:
            return self._solve_single_step(nlp, motion_params, solver_options)
    
    def _solve_single_step(self, nlp: MotionNLP, motion_params: Dict[str, Any], 
                          solver_options: Dict[str, Any]) -> Dict[str, Any]:
        """Solve NLP in a single step."""
        solver = ca.nlpsol('solver', 'ipopt', nlp.casadi_problem, solver_options)
        
        # Generate initial guess
        initial_guess = self._generate_initial_guess(nlp, motion_params)
        
        # Solve the problem
        logger.info("Starting single-step optimization...")
        solution = solver(
            x0=initial_guess,
            lbx=nlp.variable_bounds['lower'],
            ubx=nlp.variable_bounds['upper'],
            lbg=nlp.constraint_bounds['lower'],
            ubg=nlp.constraint_bounds['upper']
        )
        
        return {
            'x': solution['x'],
            'f': solution['f'],
            'g': solution['g'],
            'stats': solver.stats()
        }
    
    def _solve_with_continuation(self, nlp: MotionNLP, motion_params: Dict[str, Any],
                               base_solver_options: Dict[str, Any]) -> Dict[str, Any]:
        """Solve NLP using continuation strategy."""
        logger.info("Starting continuation optimization...")
        
        continuation_factors = self.numerical_guards.continuation.generate_continuation_sequence()
        logger.info(f"Continuation sequence: {continuation_factors}")
        
        current_solution = None
        
        for i, factor in enumerate(continuation_factors):
            logger.info(f"Continuation step {i+1}/{len(continuation_factors)}, factor={factor:.3f}")
            
            # Adjust solver options for current step
            step_options = base_solver_options.copy()
            if i == 0:
                # First step: more relaxed tolerance
                step_options['ipopt.tol'] = self.parameters.tolerance * 10
                step_options['ipopt.constr_viol_tol'] = self.parameters.constraint_tolerance * 10
            elif i == len(continuation_factors) - 1:
                # Final step: full precision
                step_options['ipopt.tol'] = self.parameters.tolerance
                step_options['ipopt.constr_viol_tol'] = self.parameters.constraint_tolerance
            
            # Adjust regularization
            adjusted_weight = self.numerical_guards.continuation.adjust_regularization(
                self.parameters.smoothness_weight, factor
            )
            
            # Create solver for this step
            solver = ca.nlpsol(f'solver_step_{i}', 'ipopt', nlp.casadi_problem, step_options)
            
            # Generate initial guess (warm start from previous step)
            if current_solution is None:
                initial_guess = self._generate_initial_guess(nlp, motion_params)
            else:
                # Perturb previous solution slightly
                prev_x = np.array(current_solution['x']).flatten()
                if self.numerical_guards:
                    initial_guess = ca.DM(self.numerical_guards.warm_start.perturb_solution(prev_x, 0.01))
                else:
                    initial_guess = current_solution['x']
            
            # Relax constraints for early steps
            if factor < 1.0:
                # TODO: Implement constraint relaxation
                # For now, use original bounds
                lower_bounds = nlp.constraint_bounds['lower']
                upper_bounds = nlp.constraint_bounds['upper']
            else:
                lower_bounds = nlp.constraint_bounds['lower']
                upper_bounds = nlp.constraint_bounds['upper']
            
            # Solve current step
            try:
                solution = solver(
                    x0=initial_guess,
                    lbx=nlp.variable_bounds['lower'],
                    ubx=nlp.variable_bounds['upper'],
                    lbg=lower_bounds,
                    ubg=upper_bounds
                )
                current_solution = {
                    'x': solution['x'],
                    'f': solution['f'],
                    'g': solution['g'],
                    'stats': solver.stats()
                }
                
                logger.info(f"Step {i+1} completed: obj={float(solution['f']):.6f}")
                
            except Exception as e:
                logger.warning(f"Continuation step {i+1} failed: {e}")
                if current_solution is None:
                    raise RuntimeError(f"First continuation step failed: {e}")
                # Continue with last successful solution
                logger.info("Using last successful solution")
                break
        
        return current_solution
    
    def _generate_initial_guess(self, nlp: MotionNLP, motion_params: Dict[str, Any]) -> ca.DM:
        """Generate initial guess for the optimization variables."""
        if self.parameters.initial_guess_type == "sinusoidal":
            return self._sinusoidal_initial_guess(nlp, motion_params)
        elif self.parameters.initial_guess_type == "piecewise":
            return self._piecewise_initial_guess(nlp, motion_params)
        else:
            # Default fallback
            return ca.DM.zeros(nlp.num_variables)
    
    def _sinusoidal_initial_guess(self, nlp: MotionNLP, motion_params: Dict[str, Any]) -> ca.DM:
        """Generate sinusoidal initial guess using numerical guards."""
        stroke_length = motion_params.get('strokeLengthMm', 10.0)
        grid = nlp.grid
        
        # Use warm-start generator if available
        if self.numerical_guards:
            position_guess = self.numerical_guards.warm_start.generate_sinusoidal_start(
                grid.nodes, stroke_length, motion_params
            )
        else:
            # Simple sinusoidal motion as fallback
            position_guess = stroke_length / 2.0 * (1.0 - np.cos(grid.nodes))
        
        # Pack into CasADi format
        initial_guess = ca.DM.zeros(nlp.num_variables)
        initial_guess[:grid.node_count] = position_guess
        
        return initial_guess
    
    def _piecewise_initial_guess(self, nlp: MotionNLP, motion_params: Dict[str, Any]) -> ca.DM:
        """Generate piecewise initial guess based on traditional segments."""
        # TODO: Implement piecewise initial guess using traditional motion law
        # For now, fall back to sinusoidal
        return self._sinusoidal_initial_guess(nlp, motion_params)
    
    def _post_process_solution(self, solution_data: Dict[str, Any], grid: CollocationGrid, start_time: float, motion_params: Dict[str, Any]) -> CollocationSolution:
        """Post-process the optimization solution."""
        stats = solution_data['stats']
        execution_time = time.time() - start_time
        
        # Extract solution variables
        x_opt = np.array(solution_data['x']).flatten()
        position = x_opt[:grid.node_count]
        
        # Compute derivatives using differentiation matrices
        velocity = grid.differentiation_matrix @ position
        acceleration = grid.second_derivative_matrix @ position
        
        # Check success criteria
        success = (
            stats['return_status'] == 'Solve_Succeeded' and
            float(solution_data['f']) < float('inf')
        )
        
        # Compute constraint violation
        g_opt = np.array(solution_data['g']).flatten()
        constraint_violation = np.max(np.abs(g_opt)) if len(g_opt) > 0 else 0.0
        
        # Dense validation (if enabled)
        validation_report = None
        validation_passed = True
        
        if self.parameters.enable_dense_validation:
            logger.info("Running dense post-solve validation")
            try:
                validator = DenseValidator(self.parameters.validation_limits)
                validation_report = validator.validate_solution(
                    theta_grid=grid.nodes,
                    position=position,
                    velocity=velocity,
                    acceleration=acceleration,
                    motion_params=motion_params
                )
                validation_passed = validation_report.passed
                
                if validation_passed:
                    logger.info("✓ Dense validation passed")
                else:
                    logger.warning(f"✗ Dense validation failed with {validation_report.num_violations} violations")
                    
            except Exception as e:
                logger.error(f"Dense validation failed: {e}")
                validation_passed = False
        
        return CollocationSolution(
            success=success,
            execution_time=execution_time,
            iterations=stats.get('iter_count', 0),
            theta_grid=grid.nodes.copy(),
            position=position,
            velocity=velocity,
            acceleration=acceleration,
            objective_value=float(solution_data['f']),
            constraint_violation=constraint_violation,
            validation_report=validation_report,
            validation_passed=validation_passed,
            solver_status=stats['return_status'],
            return_code=0 if success else 1,
            node_count=grid.node_count,
            discretization_type=grid.node_type
        )
    
    def export_solution_for_kotlin(self, solution: CollocationSolution, output_path: Path) -> None:
        """
        Export solution in format compatible with Kotlin motion law engine.
        
        This creates a JSON file that can be consumed by the Kotlin CollocationMotionSolver.
        """
        if not solution.success:
            raise ValueError("Cannot export failed solution")
        
        # Resample to uniform grid for compatibility
        uniform_step_deg = 1.0  # Default step size
        uniform_theta = np.arange(0, 360, uniform_step_deg) * np.pi / 180.0
        
        # Interpolate solution to uniform grid
        uniform_position = np.interp(uniform_theta, solution.theta_grid, solution.position)
        uniform_velocity = np.interp(uniform_theta, solution.theta_grid, solution.velocity)
        uniform_acceleration = np.interp(uniform_theta, solution.theta_grid, solution.acceleration)
        
        # Create motion law samples format
        samples = []
        for i, theta in enumerate(uniform_theta):
            samples.append({
                "thetaDeg": float(theta * 180.0 / np.pi),
                "xMm": float(uniform_position[i]),
                "vMmPerOmega": float(uniform_velocity[i]),
                "aMmPerOmega2": float(uniform_acceleration[i])
            })
        
        motion_law_data = {
            "stepDeg": uniform_step_deg,
            "samples": samples,
            "solver_metadata": {
                "method": "collocation",
                "node_count": solution.node_count,
                "discretization_type": solution.discretization_type,
                "execution_time": solution.execution_time,
                "iterations": solution.iterations,
                "objective_value": solution.objective_value,
                "constraint_violation": solution.constraint_violation,
                "solver_status": solution.solver_status
            }
        }
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(motion_law_data, f, indent=2)
        
        logger.info(f"Exported collocation solution to {output_path}")
    
    def get_solver_info(self) -> Dict[str, Any]:
        """Get information about the current solver state."""
        cache_stats = get_cache_stats()
        
        info = {
            "solver_type": "collocation",
            "casadi_available": CASADI_AVAILABLE,
            "parameters": asdict(self.parameters),
            "has_solution": self.last_solution is not None,
            "last_solution_success": self.last_solution.success if self.last_solution else None,
            "matrix_cache": cache_stats
        }
        
        if self.last_solution:
            info["last_solution"] = {
                "execution_time": self.last_solution.execution_time,
                "iterations": self.last_solution.iterations,
                "objective_value": self.last_solution.objective_value,
                "constraint_violation": self.last_solution.constraint_violation,
                "validation_passed": self.last_solution.validation_passed
            }
        
        return info
    
    def clear_cache(self):
        """Clear matrix cache and reset statistics."""
        clear_matrix_cache()
        logger.info("Matrix cache cleared")
    
    def get_cache_performance(self) -> Dict[str, Any]:
        """Get detailed cache performance metrics."""
        return get_cache_stats()
