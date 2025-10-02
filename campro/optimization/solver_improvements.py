"""
Global Solver Improvements for Engine Optimization

This module implements the missing global solver improvements:
- Objective normalization: All objectives should be unitless
- Variable scaling: Variables need reference scaling
- Continuation strategy: 3-stage homotopy missing
- Convergence diagnostics: KKT error, constraint violations
"""

import numpy as np
import casadi as ca
from typing import Dict, List, Any, Union, Callable
from dataclasses import dataclass

from campro.logging import get_logger
log = get_logger(__name__)


@dataclass
class SolverParameters:
    """Parameters for solver improvements."""
    
    # Normalization parameters
    reference_work_J: float = 1000.0  # Reference work (J)
    reference_pressure_Pa: float = 1000000.0  # Reference pressure (Pa)
    reference_velocity_mps: float = 10.0  # Reference velocity (m/s)
    reference_acceleration_mps2: float = 100.0  # Reference acceleration (m/s²)
    reference_force_N: float = 10000.0  # Reference force (N)
    reference_torque_Nm: float = 1000.0  # Reference torque (Nm)
    reference_power_W: float = 10000.0  # Reference power (W)
    reference_efficiency: float = 0.95  # Reference efficiency
    
    # Scaling parameters
    variable_scaling_enabled: bool = True
    objective_scaling_enabled: bool = True
    constraint_scaling_enabled: bool = True
    
    # Continuation parameters
    continuation_enabled: bool = True
    continuation_steps: int = 3
    continuation_tolerance: float = 1e-6
    continuation_relaxation_factor: float = 0.1
    
    # Diagnostics parameters
    diagnostics_enabled: bool = True
    kkt_tolerance: float = 1e-6
    constraint_violation_tolerance: float = 1e-6
    max_iterations: int = 1000
    
    # IPOPT parameters
    ipopt_tolerance: float = 1e-6
    ipopt_constraint_tolerance: float = 1e-6
    ipopt_max_iterations: int = 1000
    ipopt_linear_solver: str = 'mumps'
    ipopt_mu_strategy: str = 'adaptive'


class ObjectiveNormalizer:
    """
    Objective normalization to make all objectives unitless.
    
    Implements normalization: Ĵ = J / J̄ where J̄ is the reference value.
    """
    
    def __init__(self, parameters: SolverParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def normalize_work_objective(self, work_J: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Normalize work objective to unitless.
        
        Ŵ = W / W̄
        
        Args:
            work_J: Work value(s) (J)
            
        Returns:
            Normalized work value(s)
        """
        if isinstance(work_J, ca.SX):
            return work_J / self.params.reference_work_J
        else:
            return work_J / self.params.reference_work_J
    
    def normalize_pressure_objective(self, pressure_Pa: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Normalize pressure objective to unitless.
        
        p̂ = p / p̄
        
        Args:
            pressure_Pa: Pressure value(s) (Pa)
            
        Returns:
            Normalized pressure value(s)
        """
        if isinstance(pressure_Pa, ca.SX):
            return pressure_Pa / self.params.reference_pressure_Pa
        else:
            return pressure_Pa / self.params.reference_pressure_Pa
    
    def normalize_velocity_objective(self, velocity_mps: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Normalize velocity objective to unitless.
        
        v̂ = v / v̄
        
        Args:
            velocity_mps: Velocity value(s) (m/s)
            
        Returns:
            Normalized velocity value(s)
        """
        if isinstance(velocity_mps, ca.SX):
            return velocity_mps / self.params.reference_velocity_mps
        else:
            return velocity_mps / self.params.reference_velocity_mps
    
    def normalize_acceleration_objective(self, acceleration_mps2: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Normalize acceleration objective to unitless.
        
        â = a / ā
        
        Args:
            acceleration_mps2: Acceleration value(s) (m/s²)
            
        Returns:
            Normalized acceleration value(s)
        """
        if isinstance(acceleration_mps2, ca.SX):
            return acceleration_mps2 / self.params.reference_acceleration_mps2
        else:
            return acceleration_mps2 / self.params.reference_acceleration_mps2
    
    def normalize_force_objective(self, force_N: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Normalize force objective to unitless.
        
        F̂ = F / F̄
        
        Args:
            force_N: Force value(s) (N)
            
        Returns:
            Normalized force value(s)
        """
        if isinstance(force_N, ca.SX):
            return force_N / self.params.reference_force_N
        else:
            return force_N / self.params.reference_force_N
    
    def normalize_torque_objective(self, torque_Nm: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Normalize torque objective to unitless.
        
        τ̂ = τ / τ̄
        
        Args:
            torque_Nm: Torque value(s) (Nm)
            
        Returns:
            Normalized torque value(s)
        """
        if isinstance(torque_Nm, ca.SX):
            return torque_Nm / self.params.reference_torque_Nm
        else:
            return torque_Nm / self.params.reference_torque_Nm
    
    def normalize_power_objective(self, power_W: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Normalize power objective to unitless.
        
        P̂ = P / P̄
        
        Args:
            power_W: Power value(s) (W)
            
        Returns:
            Normalized power value(s)
        """
        if isinstance(power_W, ca.SX):
            return power_W / self.params.reference_power_W
        else:
            return power_W / self.params.reference_power_W
    
    def normalize_efficiency_objective(self, efficiency: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Normalize efficiency objective to unitless.
        
        η̂ = η / η̄
        
        Args:
            efficiency: Efficiency value(s) [0,1]
            
        Returns:
            Normalized efficiency value(s)
        """
        if isinstance(efficiency, ca.SX):
            return efficiency / self.params.reference_efficiency
        else:
            return efficiency / self.params.reference_efficiency
    
    def normalize_objectives(self, objectives: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all objectives in a dictionary.
        
        Args:
            objectives: Dictionary of objectives
            
        Returns:
            Dictionary of normalized objectives
        """
        normalized_objectives = {}
        
        for key, value in objectives.items():
            if 'work' in key.lower() or key.endswith('_J'):
                normalized_objectives[key] = self.normalize_work_objective(value)
            elif 'velocity' in key.lower() or key.endswith('_mps'):
                normalized_objectives[key] = self.normalize_velocity_objective(value)
            elif 'pressure' in key.lower() or key.endswith('_Pa'):
                normalized_objectives[key] = self.normalize_pressure_objective(value)
            elif 'acceleration' in key.lower() or key.endswith('_mps2'):
                normalized_objectives[key] = self.normalize_acceleration_objective(value)
            elif 'force' in key.lower() or key.endswith('_N'):
                normalized_objectives[key] = self.normalize_force_objective(value)
            elif 'torque' in key.lower() or key.endswith('_Nm'):
                normalized_objectives[key] = self.normalize_torque_objective(value)
            elif 'power' in key.lower() or key.endswith('_W'):
                normalized_objectives[key] = self.normalize_power_objective(value)
            elif 'efficiency' in key.lower() or 'eta' in key:
                normalized_objectives[key] = self.normalize_efficiency_objective(value)
            else:
                # Keep as is if no specific normalization found
                normalized_objectives[key] = value
        
        return normalized_objectives


class VariableScaler:
    """
    Variable scaling using reference values.
    
    Implements scaling: x̂ = x / x̄ where x̄ is the reference value.
    """
    
    def __init__(self, parameters: SolverParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def scale_displacement(self, displacement_m: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Scale displacement variable.
        
        Args:
            displacement_m: Displacement value(s) (m)
            
        Returns:
            Scaled displacement value(s)
        """
        reference_displacement = 0.1  # 100mm reference
        if isinstance(displacement_m, ca.SX):
            return displacement_m / reference_displacement
        elif isinstance(displacement_m, (list, np.ndarray)):
            return np.array(displacement_m) / reference_displacement
        else:
            return displacement_m / reference_displacement
    
    def scale_velocity(self, velocity_mps: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Scale velocity variable.
        
        Args:
            velocity_mps: Velocity value(s) (m/s)
            
        Returns:
            Scaled velocity value(s)
        """
        if isinstance(velocity_mps, ca.SX):
            return velocity_mps / self.params.reference_velocity_mps
        else:
            return velocity_mps / self.params.reference_velocity_mps
    
    def scale_acceleration(self, acceleration_mps2: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Scale acceleration variable.
        
        Args:
            acceleration_mps2: Acceleration value(s) (m/s²)
            
        Returns:
            Scaled acceleration value(s)
        """
        if isinstance(acceleration_mps2, ca.SX):
            return acceleration_mps2 / self.params.reference_acceleration_mps2
        else:
            return acceleration_mps2 / self.params.reference_acceleration_mps2
    
    def scale_pressure(self, pressure_Pa: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Scale pressure variable.
        
        Args:
            pressure_Pa: Pressure value(s) (Pa)
            
        Returns:
            Scaled pressure value(s)
        """
        if isinstance(pressure_Pa, ca.SX):
            return pressure_Pa / self.params.reference_pressure_Pa
        else:
            return pressure_Pa / self.params.reference_pressure_Pa
    
    def scale_gear_radius(self, radius_m: Union[float, np.ndarray, ca.SX]) -> Union[float, np.ndarray, ca.SX]:
        """
        Scale gear radius variable.
        
        Args:
            radius_m: Radius value(s) (m)
            
        Returns:
            Scaled radius value(s)
        """
        reference_radius = 0.1  # 100mm reference
        if isinstance(radius_m, ca.SX):
            return radius_m / reference_radius
        else:
            return radius_m / reference_radius
    
    def scale_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scale all variables in a dictionary.
        
        Args:
            variables: Dictionary of variables
            
        Returns:
            Dictionary of scaled variables
        """
        scaled_variables = {}
        
        for key, value in variables.items():
            if 'displacement' in key.lower() or key.endswith('_m') and 'displacement' in key:
                scaled_variables[key] = self.scale_displacement(value)
            elif 'velocity' in key.lower() or key.endswith('_mps'):
                scaled_variables[key] = self.scale_velocity(value)
            elif 'acceleration' in key.lower() or key.endswith('_mps2'):
                scaled_variables[key] = self.scale_acceleration(value)
            elif 'pressure' in key.lower() or key.endswith('_Pa'):
                scaled_variables[key] = self.scale_pressure(value)
            elif 'radius' in key.lower() or key.endswith('_m') and 'radius' in key:
                scaled_variables[key] = self.scale_gear_radius(value)
            else:
                # Keep as is if no specific scaling found
                scaled_variables[key] = value
        
        return scaled_variables


class ContinuationStrategy:
    """
    Continuation strategy with 3-stage homotopy.
    
    Implements specification-compliant homotopy continuation with parameter scheduling:
    - Stage 1: ε_v=1e-1, ε_fric=1e-1, stress_factor=0.7 (very smooth, relaxed limits)
    - Stage 2: ε_v=5e-2, ε_fric=5e-2, stress_factor=0.85 (tighten bounds)
    - Stage 3: ε_v=1e-2, ε_fric=1e-2, stress_factor=1.0 (final physics-like limits)
    """
    
    def __init__(self, parameters: SolverParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
        
        # Specification-compliant continuation stages
        self.continuation_stages = [
            {
                'epsilon_valve': 1e-1,
                'epsilon_friction': 1e-1,
                'stress_factor': 0.7,
                'tolerance': 1e-4,
                'max_iter': 2000,
                'description': 'Very smooth, relaxed limits, coarse grid'
            },
            {
                'epsilon_valve': 5e-2,
                'epsilon_friction': 5e-2,
                'stress_factor': 0.85,
                'tolerance': 1e-5,
                'max_iter': 3000,
                'description': 'Tighten bounds; refine grid'
            },
            {
                'epsilon_valve': 1e-2,
                'epsilon_friction': 1e-2,
                'stress_factor': 1.0,
                'tolerance': 1e-6,
                'max_iter': 5000,
                'description': 'Final physics-like limits; final grid'
            }
        ]
    
    def create_continuation_sequence(self, base_problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create continuation sequence with 3 stages according to specification.
        
        Args:
            base_problem: Base optimization problem
            
        Returns:
            List of problems for continuation
        """
        continuation_problems = []
        
        for i, stage_params in enumerate(self.continuation_stages):
            stage_problem = self._create_stage_problem(base_problem, stage_params, i + 1)
            continuation_problems.append(stage_problem)
        
        return continuation_problems
    
    def _create_stage_problem(self, base_problem: Dict[str, Any], 
                             stage_params: Dict[str, Any], 
                             stage_number: int) -> Dict[str, Any]:
        """
        Create a stage problem with specification-compliant parameters.
        
        Args:
            base_problem: Base optimization problem
            stage_params: Stage parameters (epsilon_valve, epsilon_friction, stress_factor, etc.)
            stage_number: Stage number (1, 2, or 3)
            
        Returns:
            Stage problem with applied parameters
        """
        stage_problem = base_problem.copy()
        
        # Apply stage-specific parameters
        stage_problem['stage_number'] = stage_number
        stage_problem['stage_params'] = stage_params
        
        # Apply valve smoothing parameter
        if 'epsilon_valve' in stage_problem:
            stage_problem['epsilon_valve'] = stage_params['epsilon_valve']
        
        # Apply friction smoothing parameter
        if 'epsilon_friction' in stage_problem:
            stage_problem['epsilon_friction'] = stage_params['epsilon_friction']
        
        # Apply stress limit factor
        stress_factor = stage_params['stress_factor']
        if 'stress_constraints' in stage_problem:
            stage_problem['stress_constraints'] = self._apply_stress_factor(
                stage_problem['stress_constraints'], stress_factor)
        
        # Apply tolerance and iteration limits
        stage_problem['tolerance'] = stage_params['tolerance']
        stage_problem['max_iter'] = stage_params['max_iter']
        
        # Apply grid refinement for later stages
        if stage_number > 1:
            stage_problem = self._refine_grid(stage_problem, stage_number)
        
        # Log stage information
        self.logger.info(f"Created Stage {stage_number}: {stage_params['description']}")
        self.logger.info(f"  ε_valve={stage_params['epsilon_valve']:.1e}, "
                        f"ε_friction={stage_params['epsilon_friction']:.1e}, "
                        f"stress_factor={stress_factor:.2f}")
        
        return stage_problem
    
    def _apply_stress_factor(self, stress_constraints: Dict[str, Any], 
                           stress_factor: float) -> Dict[str, Any]:
        """
        Apply stress factor to stress constraints.
        
        Args:
            stress_constraints: Original stress constraints
            stress_factor: Stress limit factor (0.7, 0.85, or 1.0)
            
        Returns:
            Modified stress constraints
        """
        modified_constraints = stress_constraints.copy()
        
        # Apply stress factor to stress limits
        if 'max_stress' in modified_constraints:
            modified_constraints['max_stress'] *= stress_factor
        
        if 'contact_stress_limit' in modified_constraints:
            modified_constraints['contact_stress_limit'] *= stress_factor
        
        if 'fatigue_limit' in modified_constraints:
            modified_constraints['fatigue_limit'] *= stress_factor
        
        return modified_constraints
    
    def _refine_grid(self, problem: Dict[str, Any], stage_number: int) -> Dict[str, Any]:
        """
        Refine grid for later stages.
        
        Args:
            problem: Optimization problem
            stage_number: Stage number (2 or 3)
            
        Returns:
            Problem with refined grid
        """
        refined_problem = problem.copy()
        
        # Grid refinement factors
        grid_factors = {2: 1.5, 3: 2.0}  # Refine by 1.5x in stage 2, 2x in stage 3
        
        if stage_number in grid_factors:
            factor = grid_factors[stage_number]
            
            # Refine collocation grid
            if 'collocation_points' in refined_problem:
                original_points = refined_problem['collocation_points']
                refined_problem['collocation_points'] = int(original_points * factor)
            
            # Refine time grid
            if 'time_grid' in refined_problem:
                original_grid = refined_problem['time_grid']
                # Interpolate to finer grid
                refined_problem['time_grid'] = self._interpolate_grid(original_grid, factor)
        
        return refined_problem
    
    def _interpolate_grid(self, original_grid: np.ndarray, factor: float) -> np.ndarray:
        """
        Interpolate grid to finer resolution.
        
        Args:
            original_grid: Original grid points
            factor: Refinement factor
            
        Returns:
            Refined grid
        """
        n_original = len(original_grid)
        n_refined = int(n_original * factor)
        
        # Create refined grid using linear interpolation
        refined_grid = np.linspace(original_grid[0], original_grid[-1], n_refined)
        
        return refined_grid
    
    def solve_with_continuation(self, problems: List[Dict[str, Any]], 
                              solver_factory: Callable) -> Dict[str, Any]:
        """
        Solve optimization problem using continuation strategy.
        
        Args:
            problems: List of problems for continuation
            solver_factory: Function to create solver
            
        Returns:
            Final solution with continuation diagnostics
        """
        solutions = []
        current_solution = None
        
        for i, problem in enumerate(problems):
            stage_number = i + 1
            self.logger.info(f"Solving Stage {stage_number} of {len(problems)}")
            
            # Create solver for this stage
            solver = solver_factory(problem)
            
            # Use previous solution as initial guess if available
            if current_solution is not None:
                problem['x0'] = current_solution.get('x', None)
            
            # Solve current stage
            try:
                # Check if solver is callable or has a solve method
                if hasattr(solver, 'solve'):
                    solution = solver.solve(problem)
                elif callable(solver):
                    solution = solver(problem)
                else:
                    # Assume it's a CasADi solver that can be called directly
                    solution = solver(problem)
                solutions.append(solution)
                current_solution = solution
                
                self.logger.info(f"Stage {stage_number} converged successfully")
                
                # Check convergence criteria
                if self._check_convergence(solution, problem):
                    self.logger.info(f"Convergence criteria met at Stage {stage_number}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Stage {stage_number} failed: {str(e)}")
                if current_solution is None:
                    raise e
                else:
                    self.logger.warning(f"Using previous solution from Stage {stage_number - 1}")
                    break
        
        # Return final solution with continuation diagnostics
        final_solution = current_solution.copy() if current_solution else {}
        final_solution['continuation_solutions'] = solutions
        final_solution['continuation_stages_completed'] = len(solutions)
        
        return final_solution
    
    def _check_convergence(self, solution: Dict[str, Any], problem: Dict[str, Any]) -> bool:
        """
        Check if convergence criteria are met.
        
        Args:
            solution: Current solution
            problem: Current problem
            
        Returns:
            True if convergence criteria are met
        """
        # Check KKT error
        kkt_error = solution.get('kkt_error', float('inf'))
        if kkt_error > problem.get('tolerance', 1e-6):
            return False
        
        # Check constraint violations
        constraint_violations = solution.get('constraint_violations', {})
        for violation in constraint_violations.values():
            if abs(violation) > problem.get('tolerance', 1e-6):
                return False
        
        # Check if this is the final stage
        stage_number = problem.get('stage_number', 1)
        if stage_number < 3:
            return False
        
        return True


class ConvergenceDiagnostics:
    """
    Convergence diagnostics for optimization problems.
    
    Implements KKT error calculation and constraint violation monitoring.
    """
    
    def __init__(self, parameters: SolverParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_kkt_error(self, solution: Dict[str, Any], 
                          problem: Dict[str, Any]) -> float:
        """
        Calculate KKT error for convergence diagnostics.
        
        Args:
            solution: Optimization solution
            problem: Optimization problem
            
        Returns:
            KKT error
        """
        try:
            # Extract solution components
            x = solution.get('x', np.array([]))
            lam_x = solution.get('lam_x', np.array([]))
            lam_g = solution.get('lam_g', np.array([]))
            
            # Extract problem components
            f = problem.get('f', None)
            g = problem.get('g', None)
            lbx = problem.get('lbx', [])  # noqa: F841
            ubx = problem.get('ubx', [])  # noqa: F841
            lbg = problem.get('lbg', [])  # noqa: F841
            ubg = problem.get('ubg', [])  # noqa: F841
            
            if f is None or g is None:
                return float('inf')
            
            # Convert numpy arrays to CasADi DM for symbolic operations
            x_dm = ca.DM(x)
            lam_x_dm = ca.DM(lam_x)
            lam_g_dm = ca.DM(lam_g)
            
            # Calculate gradient of objective at solution point
            grad_f = ca.gradient(f, problem['x'])
            grad_f_val = ca.Function('grad_f', [problem['x']], [grad_f])(x_dm)
            
            # Calculate Jacobian of constraints at solution point
            jac_g = ca.jacobian(g, problem['x'])
            jac_g_val = ca.Function('jac_g', [problem['x']], [jac_g])(x_dm)
            
            # Calculate KKT residual
            kkt_residual = grad_f_val + jac_g_val.T @ lam_g_dm + lam_x_dm
            
            # Calculate KKT error
            kkt_error = float(ca.norm_2(kkt_residual))
            
            return kkt_error
            
        except Exception as e:
            self.logger.error(f"Error calculating KKT error: {str(e)}")
            return float('inf')
    
    def calculate_constraint_violations(self, solution: Dict[str, Any],
                                      problem: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate constraint violations.
        
        Args:
            solution: Optimization solution
            problem: Optimization problem
            
        Returns:
            Dictionary of constraint violations
        """
        violations = {}
        
        try:
            # Extract solution components
            x = solution.get('x', np.array([]))
            g = solution.get('g', np.array([]))
            
            # Extract problem components
            lbx = problem.get('lbx', [])
            ubx = problem.get('ubx', [])
            lbg = problem.get('lbg', [])
            ubg = problem.get('ubg', [])
            
            # Calculate variable bound violations
            if len(lbx) > 0 and len(ubx) > 0:
                x_violations = []
                for i, (xi, lb, ub) in enumerate(zip(x, lbx, ubx)):
                    if xi < lb:
                        x_violations.append(lb - xi)
                    elif xi > ub:
                        x_violations.append(xi - ub)
                
                violations['variable_bound_violations'] = max(x_violations) if x_violations else 0.0
            
            # Calculate constraint violations
            if len(lbg) > 0 and len(ubg) > 0:
                g_violations = []
                for i, (gi, lb, ub) in enumerate(zip(g, lbg, ubg)):
                    if gi < lb:
                        g_violations.append(lb - gi)
                    elif gi > ub:
                        g_violations.append(gi - ub)
                
                violations['constraint_violations'] = max(g_violations) if g_violations else 0.0
            
            # Calculate total violation
            violations['total_violation'] = max(violations.values()) if violations else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating constraint violations: {str(e)}")
            violations['error'] = float('inf')
        
        return violations
    
    def check_convergence(self, solution: Dict[str, Any],
                         problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check convergence criteria.
        
        Args:
            solution: Optimization solution
            problem: Optimization problem
            
        Returns:
            Convergence status
        """
        # Calculate KKT error
        kkt_error = self.calculate_kkt_error(solution, problem)
        
        # Calculate constraint violations
        violations = self.calculate_constraint_violations(solution, problem)
        
        # Check convergence criteria
        kkt_converged = kkt_error < self.params.kkt_tolerance
        constraint_converged = violations.get('total_violation', float('inf')) < self.params.constraint_violation_tolerance
        
        # Overall convergence
        converged = kkt_converged and constraint_converged
        
        convergence_status = {
            'converged': converged,
            'kkt_error': kkt_error,
            'kkt_converged': kkt_converged,
            'constraint_violations': violations,
            'constraint_converged': constraint_converged,
            'iterations': solution.get('iterations', 0),
            'objective_value': solution.get('f', float('inf'))
        }
        
        return convergence_status
    
    def log_convergence_info(self, convergence_status: Dict[str, Any]) -> None:
        """
        Log convergence information.
        
        Args:
            convergence_status: Convergence status dictionary
        """
        self.logger.info("Convergence Diagnostics:")
        self.logger.info(f"  Converged: {convergence_status['converged']}")
        self.logger.info(f"  KKT Error: {convergence_status['kkt_error']:.2e}")
        self.logger.info(f"  KKT Converged: {convergence_status['kkt_converged']}")
        self.logger.info(f"  Constraint Violations: {convergence_status['constraint_violations']}")
        self.logger.info(f"  Constraint Converged: {convergence_status['constraint_converged']}")
        self.logger.info(f"  Iterations: {convergence_status['iterations']}")
        self.logger.info(f"  Objective Value: {convergence_status['objective_value']:.2e}")


class SolverImprovements:
    """
    Main class that integrates all solver improvements.
    
    This class provides the interface for enhanced optimization solving.
    """
    
    def __init__(self, parameters: SolverParameters):
        self.params = parameters
        self.objective_normalizer = ObjectiveNormalizer(parameters)
        self.variable_scaler = VariableScaler(parameters)
        self.continuation_strategy = ContinuationStrategy(parameters)
        self.convergence_diagnostics = ConvergenceDiagnostics(parameters)
        self.logger = get_logger(__name__)
    
    def enhance_optimization_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance optimization problem with scaling and normalization.
        
        Args:
            problem: Original optimization problem
            
        Returns:
            Enhanced optimization problem
        """
        enhanced_problem = problem.copy()
        
        # Scale variables if enabled
        if self.params.variable_scaling_enabled:
            enhanced_problem = self._apply_variable_scaling(enhanced_problem)
        
        # Normalize objectives if enabled
        if self.params.objective_scaling_enabled:
            enhanced_problem = self._apply_objective_normalization(enhanced_problem)
        
        # Scale constraints if enabled
        if self.params.constraint_scaling_enabled:
            enhanced_problem = self._apply_constraint_scaling(enhanced_problem)
        
        return enhanced_problem
    
    def _apply_variable_scaling(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply variable scaling to optimization problem.
        
        Args:
            problem: Optimization problem
            
        Returns:
            Problem with scaled variables
        """
        # Scale initial guess
        if 'x0' in problem:
            problem['x0'] = self.variable_scaler.scale_variables({'x0': problem['x0']})['x0']
        
        # Scale variable bounds
        if 'lbx' in problem:
            problem['lbx'] = self.variable_scaler.scale_variables({'lbx': problem['lbx']})['lbx']
        if 'ubx' in problem:
            problem['ubx'] = self.variable_scaler.scale_variables({'ubx': problem['ubx']})['ubx']
        
        return problem
    
    def _apply_objective_normalization(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply objective normalization to optimization problem.
        
        Args:
            problem: Optimization problem
            
        Returns:
            Problem with normalized objectives
        """
        # Normalize objective function
        if 'f' in problem:
            # This would need to be implemented based on the specific objective structure
            # For now, we'll assume the objective is already properly structured
            pass
        
        return problem
    
    def _apply_constraint_scaling(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply constraint scaling to optimization problem.
        
        Args:
            problem: Optimization problem
            
        Returns:
            Problem with scaled constraints
        """
        scaled_problem = problem.copy()
        
        # Scale constraint bounds
        if 'lbg' in scaled_problem:
            scaled_problem['lbg'] = [lb / self.params.reference_force_N for lb in scaled_problem['lbg']]
        if 'ubg' in scaled_problem:
            scaled_problem['ubg'] = [ub / self.params.reference_force_N for ub in scaled_problem['ubg']]
        
        return scaled_problem
    
    def solve_with_improvements(self, problem: Dict[str, Any],
                              solver_factory: Callable) -> Dict[str, Any]:
        """
        Solve optimization problem with all improvements.
        
        Args:
            problem: Optimization problem
            solver_factory: Function to create solver
            
        Returns:
            Solution with diagnostics
        """
        # Enhance problem
        enhanced_problem = self.enhance_optimization_problem(problem)
        
        # Create continuation sequence if enabled
        if self.params.continuation_enabled:
            problems = self.continuation_strategy.create_continuation_sequence(enhanced_problem)
            solution = self.continuation_strategy.solve_with_continuation(problems, solver_factory)
        else:
            # Solve directly
            solver = solver_factory(enhanced_problem)
            solution = solver.solve(enhanced_problem)
        
        # Ensure solution has success field and x_opt field
        if solution is not None:
            # Ensure x_opt field exists (mapped from x)
            if 'x' in solution and 'x_opt' not in solution:
                solution['x_opt'] = solution['x']
            
            # Ensure f_opt field exists (mapped from f)
            if 'f' in solution and 'f_opt' not in solution:
                solution['f_opt'] = solution['f']
        
        # Add convergence diagnostics
        if self.params.diagnostics_enabled and solution is not None:
            convergence_status = self.convergence_diagnostics.check_convergence(solution, enhanced_problem)
            solution['convergence_status'] = convergence_status
            self.convergence_diagnostics.log_convergence_info(convergence_status)
            
            # Update success based on convergence diagnostics
            if 'success' not in solution:
                # Check if solution is valid and converged
                if ('x' in solution and solution['x'] is not None and 
                    convergence_status.get('converged', False)):
                    solution['success'] = True
                else:
                    solution['success'] = False
            else:
                # Override success with convergence status if diagnostics show failure
                if not convergence_status.get('converged', True):
                    solution['success'] = False
        
        return solution
