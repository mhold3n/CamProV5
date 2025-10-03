"""
Multi-objective optimization implementation for CamPro V5.

This module implements the Augmented Tchebyshev scalarization method
as specified in the unified specification.
"""

import numpy as np
import casadi as ca
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from campro.utils.logging import get_logger


@dataclass
class MultiObjectiveParameters:
    """Parameters for multi-objective optimization."""
    
    # Augmented Tchebyshev parameters
    augmentation_factor: float = 0.01  # Augmentation term weight
    
    # Weight sets for different optimization cases
    work_efficiency_biased: Optional[Dict[str, float]] = None
    balanced: Optional[Dict[str, float]] = None
    durability_biased: Optional[Dict[str, float]] = None
    
    # Reference points for normalization
    reference_work_J: float = 1000.0
    reference_efficiency: float = 0.95
    reference_jerk_mps3: float = 1000.0
    reference_stress_Pa: float = 1e9
    reference_power_loss_W: float = 1000.0
    
    def __post_init__(self):
        """Initialize default weight sets if not provided."""
        if self.work_efficiency_biased is None:
            self.work_efficiency_biased = {
                'work': 0.4,
                'efficiency': 0.3,
                'jerk': 0.1,
                'stress': 0.1,
                'loss': 0.1
            }
        
        if self.balanced is None:
            self.balanced = {
                'work': 0.25,
                'efficiency': 0.25,
                'jerk': 0.25,
                'stress': 0.15,
                'loss': 0.1
            }
        
        if self.durability_biased is None:
            self.durability_biased = {
                'work': 0.15,
                'efficiency': 0.25,
                'jerk': 0.2,
                'stress': 0.25,
                'loss': 0.15
            }


class AugmentedTchebyshevScalarizer:
    """
    Implement augmented Tchebyshev scalarization for multi-objective optimization.
    
    This class implements the specification-compliant multi-objective optimization
    using the Augmented Tchebyshev method as defined in the unified specification.
    """
    
    def __init__(self, parameters: MultiObjectiveParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def scalarize(self, objectives: Dict[str, ca.SX], 
                  weights: Dict[str, float],
                  reference_point: Optional[Dict[str, float]] = None) -> ca.SX:
        """
        Scalarize multiple objectives using augmented Tchebyshev method.
        
        Args:
            objectives: Dictionary of objective functions (CasADi SX)
            weights: Weight dictionary for each objective
            reference_point: Reference point for normalization (optional)
            
        Returns:
            Scalarized objective function
        """
        if reference_point is None:
            reference_point = self._get_default_reference_point()
        
        # Normalize objectives
        normalized = {}
        for name, obj in objectives.items():
            if name in reference_point:
                normalized[name] = obj / reference_point[name]
            else:
                normalized[name] = obj
                self.logger.warning(f"No reference point for objective '{name}', using unnormalized")
        
        # Calculate Tchebyshev distance (max weighted distance)
        max_distance = 0
        for name, obj in normalized.items():
            if name in weights:
                # For maximization objectives, use negative sign
                if name in ['work', 'efficiency']:
                    distance = weights[name] * (reference_point[name] - obj)
                else:
                    distance = weights[name] * (obj - reference_point[name])
                max_distance = ca.fmax(max_distance, distance)
        
        # Add augmentation term (sum of weighted distances)
        augmentation = 0
        for name, obj in normalized.items():
            if name in weights:
                # For maximization objectives, use negative sign
                if name in ['work', 'efficiency']:
                    augmentation += self.params.augmentation_factor * weights[name] * (reference_point[name] - obj)
                else:
                    augmentation += self.params.augmentation_factor * weights[name] * (obj - reference_point[name])
        
        return max_distance + augmentation
    
    def _get_default_reference_point(self) -> Dict[str, float]:
        """Get default reference point for normalization."""
        return {
            'work': self.params.reference_work_J,
            'efficiency': self.params.reference_efficiency,
            'jerk': self.params.reference_jerk_mps3,
            'stress': self.params.reference_stress_Pa,
            'loss': self.params.reference_power_loss_W
        }
    
    def get_weight_set(self, case: str) -> Dict[str, float]:
        """
        Get predefined weight set for different optimization cases.
        
        Args:
            case: Case name ('work_efficiency_biased', 'balanced', 'durability_biased')
            
        Returns:
            Weight dictionary
        """
        weight_sets = {
            'work_efficiency_biased': self.params.work_efficiency_biased,
            'balanced': self.params.balanced,
            'durability_biased': self.params.durability_biased
        }
        
        if case not in weight_sets:
            raise ValueError(f"Unknown case '{case}'. Available: {list(weight_sets.keys())}")
        
        return weight_sets[case]


class MultiObjectiveOptimizer:
    """
    Main multi-objective optimization class that integrates all components.
    
    This class provides the interface for multi-objective optimization
    using the Augmented Tchebyshev scalarization method.
    """
    
    def __init__(self, parameters: MultiObjectiveParameters):
        self.params = parameters
        self.scalarizer = AugmentedTchebyshevScalarizer(parameters)
        self.logger = get_logger(__name__)
    
    def create_scalarized_objective(self, objectives: Dict[str, ca.SX],
                                   case: str = 'balanced',
                                   custom_weights: Optional[Dict[str, float]] = None) -> ca.SX:
        """
        Create scalarized objective function for optimization.
        
        Args:
            objectives: Dictionary of objective functions
            case: Predefined case name or 'custom'
            custom_weights: Custom weights (required if case='custom')
            
        Returns:
            Scalarized objective function
        """
        if case == 'custom':
            if custom_weights is None:
                raise ValueError("custom_weights required when case='custom'")
            weights = custom_weights
        else:
            weights = self.scalarizer.get_weight_set(case)
        
        return self.scalarizer.scalarize(objectives, weights)
    
    def optimize_with_weight_sweep(self, objectives: Dict[str, ca.SX],
                                  cases: Optional[List[str]] = None) -> Dict[str, ca.SX]:
        """
        Create scalarized objectives for multiple weight sets.
        
        Args:
            objectives: Dictionary of objective functions
            cases: List of cases to optimize (default: all cases)
            
        Returns:
            Dictionary of scalarized objectives for each case
        """
        if cases is None:
            cases = ['work_efficiency_biased', 'balanced', 'durability_biased']
        
        scalarized_objectives = {}
        for case in cases:
            scalarized_objectives[case] = self.create_scalarized_objective(objectives, case)
        
        return scalarized_objectives
    
    def calculate_pareto_frontier(self, solutions: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Calculate Pareto frontier from multiple solutions.
        
        Args:
            solutions: Dictionary of solutions with objective values
            
        Returns:
            Pareto frontier analysis
        """
        # Convert to numpy arrays for analysis
        objective_names = list(next(iter(solutions.values())).keys())
        n_objectives = len(objective_names)
        n_solutions = len(solutions)
        
        objective_matrix = np.zeros((n_solutions, n_objectives))
        solution_names = list(solutions.keys())
        
        for i, solution_name in enumerate(solution_names):
            for j, obj_name in enumerate(objective_names):
                objective_matrix[i, j] = solutions[solution_name][obj_name]
        
        # Find Pareto optimal solutions
        pareto_indices = self._find_pareto_optimal(objective_matrix)
        pareto_solutions = {solution_names[i]: solutions[solution_names[i]] 
                           for i in pareto_indices}
        
        return {
            'pareto_solutions': pareto_solutions,
            'pareto_indices': pareto_indices,
            'objective_matrix': objective_matrix,
            'objective_names': objective_names
        }
    
    def _find_pareto_optimal(self, objective_matrix: np.ndarray) -> List[int]:
        """
        Find Pareto optimal solutions.
        
        Args:
            objective_matrix: Matrix of objective values (n_solutions x n_objectives)
            
        Returns:
            List of indices of Pareto optimal solutions
        """
        n_solutions, n_objectives = objective_matrix.shape
        pareto_indices = []
        
        for i in range(n_solutions):
            is_pareto = True
            for j in range(n_solutions):
                if i != j:
                    # Check if solution j dominates solution i
                    if self._dominates(objective_matrix[j], objective_matrix[i]):
                        is_pareto = False
                        break
            
            if is_pareto:
                pareto_indices.append(i)
        
        return pareto_indices
    
    def _dominates(self, solution_a: np.ndarray, solution_b: np.ndarray) -> bool:
        """
        Check if solution A dominates solution B.
        
        Args:
            solution_a: Objective values for solution A
            solution_b: Objective values for solution B
            
        Returns:
            True if A dominates B
        """
        # For maximization objectives (work, efficiency), higher is better
        # For minimization objectives (jerk, stress, loss), lower is better
        
        # Assume first two objectives are maximization (work, efficiency)
        # and the rest are minimization
        better_in_at_least_one = False
        
        for i, (a, b) in enumerate(zip(solution_a, solution_b)):
            if i < 2:  # Maximization objectives
                if a > b:
                    better_in_at_least_one = True
                elif a < b:
                    return False  # A is worse in this objective
            else:  # Minimization objectives
                if a < b:
                    better_in_at_least_one = True
                elif a > b:
                    return False  # A is worse in this objective
        
        return better_in_at_least_one


class RobustOptimizer:
    """
    Robust optimization with chance constraints.
    
    This class implements robust optimization as specified in the unified
    specification, including chance constraints for uncertain parameters.
    """
    
    def __init__(self, parameters: MultiObjectiveParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def add_chance_constraints(self, problem: Dict[str, Any],
                              uncertain_params: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Add chance constraints for uncertain parameters.
        
        Args:
            problem: Optimization problem dictionary
            uncertain_params: Dictionary of uncertain parameters with distributions
            
        Returns:
            Problem with chance constraints added
        """
        robust_problem = problem.copy()
        
        # Add chance constraints for each uncertain parameter
        for param_name, param_info in uncertain_params.items():
            if param_name == 'friction_coeff':
                # P(σ_max ≤ σ_lim) ≥ 0.95
                robust_problem = self._add_friction_chance_constraint(robust_problem, param_info)
            elif param_name == 'heat_release':
                # P(η ≥ η_min) ≥ 0.95
                robust_problem = self._add_heat_release_chance_constraint(robust_problem, param_info)
            elif param_name == 'clearance':
                # P(Peak p ≤ p_lim) ≥ 0.95
                robust_problem = self._add_clearance_chance_constraint(robust_problem, param_info)
        
        return robust_problem
    
    def _add_friction_chance_constraint(self, problem: Dict[str, Any], 
                                       param_info: Dict[str, float]) -> Dict[str, Any]:
        """Add chance constraint for friction coefficient."""
        # This is a simplified implementation
        # In practice, this would involve more sophisticated uncertainty propagation
        mean_mu = param_info.get('mean', 0.08)  # noqa: F841
        std_mu = param_info.get('std', 0.02)
        
        # Add constraint: σ_max + 1.96 * std_mu * sensitivity ≤ σ_lim
        # This is a conservative approximation
        if 'g' not in problem:
            problem['g'] = []
        if 'lbg' not in problem:
            problem['lbg'] = []
        if 'ubg' not in problem:
            problem['ubg'] = []
        
        # Add chance constraint (simplified)
        # In practice, this would be more sophisticated
        problem['g'].append(problem.get('stress_max', 0) + 1.96 * std_mu)
        problem['lbg'].append(-np.inf)
        problem['ubg'].append(param_info.get('stress_limit', 1e9))
        
        return problem
    
    def _add_heat_release_chance_constraint(self, problem: Dict[str, Any],
                                           param_info: Dict[str, float]) -> Dict[str, Any]:
        """Add chance constraint for heat release parameters."""
        # Similar to friction constraint but for efficiency
        if 'g' not in problem:
            problem['g'] = []
        if 'lbg' not in problem:
            problem['lbg'] = []
        if 'ubg' not in problem:
            problem['ubg'] = []
        
        # Add efficiency chance constraint
        problem['g'].append(problem.get('efficiency', 0))
        problem['lbg'].append(param_info.get('eta_min', 0.8))
        problem['ubg'].append(np.inf)
        
        return problem
    
    def _add_clearance_chance_constraint(self, problem: Dict[str, Any],
                                        param_info: Dict[str, float]) -> Dict[str, Any]:
        """Add chance constraint for clearance volume."""
        # Similar to other constraints but for pressure
        if 'g' not in problem:
            problem['g'] = []
        if 'lbg' not in problem:
            problem['lbg'] = []
        if 'ubg' not in problem:
            problem['ubg'] = []
        
        # Add pressure chance constraint
        problem['g'].append(problem.get('pressure_max', 0))
        problem['lbg'].append(-np.inf)
        problem['ubg'].append(param_info.get('pressure_limit', 1e7))
        
        return problem
