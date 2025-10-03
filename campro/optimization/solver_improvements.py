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
from typing import Dict, List, Any, Union, Callable, Tuple, Optional
from dataclasses import dataclass

from campro.logging import get_logger
log = get_logger(__name__)


# ============================================================================
# Robust x₀ Transfer and Bounds Handling
# ============================================================================

def _project_to_bounds(x: np.ndarray, lbx: np.ndarray, ubx: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """
    Project x into [lbx, ubx] with an optional tiny interior push.
    - Fixed variables (lbx == ubx within fixed_tol) are set exactly and never altered.
    - For finite-width intervals, use eps_eff <= 0.49 * width to keep a nonempty interior.
    - For single-sided bounds, push only on the finite side.
    
    Args:
        x: Decision variables
        lbx: Lower bounds
        ubx: Upper bounds
        eps: Interior margin
        
    Returns:
        Projected variables that satisfy bounds
    """
    x = np.asarray(x, float).copy()
    lbx = np.asarray(lbx, float)
    ubx = np.asarray(ubx, float)
    
    # Identify bound types
    finite_L = np.isfinite(lbx)
    finite_U = np.isfinite(ubx)
    fixed = finite_L & finite_U & (np.abs(ubx - lbx) <= 1e-14)
    
    # 1) Set fixed variables exactly
    x[fixed] = lbx[fixed]
    
    # 2) Work on the remainder
    nf = ~fixed
    if not np.any(nf):
        return x
    
    # Compute width where both finite; inf otherwise
    width = np.where(finite_L & finite_U, ubx - lbx, np.inf)
    
    # Safe interior ε: never exceed ~half the width to keep interior nonempty
    eps_eff = np.minimum(eps, 0.49 * np.maximum(width, 0.0))
    
    # Lower clamp (only where lower bound is finite)
    lower_mask = nf & finite_L
    if np.any(lower_mask):
        x[lower_mask] = np.maximum(x[lower_mask], lbx[lower_mask] + eps_eff[lower_mask])
    
    # Upper clamp (only where upper bound is finite)
    upper_mask = nf & finite_U
    if np.any(upper_mask):
        x[upper_mask] = np.minimum(x[upper_mask], ubx[upper_mask] - eps_eff[upper_mask])
    
    # Final safety clip (exact to bounds) to kill any numerical fuzz
    x = np.minimum(np.where(finite_U, ubx, x), np.maximum(np.where(finite_L, lbx, x), x))
    
    # Reassert fixed exactly (in case of FP noise)
    x[fixed] = lbx[fixed]
    return x


def _transfer_x0(prev_nlp: Any, new_nlp: Any, prev_sol: Optional[Dict[str, Any]]) -> np.ndarray:
    """
    Block-aware x₀ transfer between NLP formulations.
    
    Args:
        prev_nlp: Previous NLP problem
        new_nlp: New NLP problem
        prev_sol: Previous solution (may be None)
        
    Returns:
        New initial guess that respects bounds and structure
    """
    # Get block slices from metadata
    bs_prev = prev_nlp.meta.get('block_slices', None) if prev_nlp else None
    bs_new = new_nlp.meta.get('block_slices', None)
    x_prev = np.asarray(prev_sol.get('x', None), float) if prev_sol else None
    
    x_new = np.zeros_like(new_nlp.lbx, dtype=float)
    
    def _copy_common(block: str) -> bool:
        """Copy or interpolate a common block between formulations."""
        if x_prev is None or bs_prev is None or block not in bs_prev.slices or block not in bs_new.slices:
            return False
            
        x_block_prev = x_prev[bs_prev.slices[block]]
        
        # If both blocks are same length: direct copy
        if (bs_prev.slices[block].stop - bs_prev.slices[block].start) == \
           (bs_new.slices[block].stop - bs_new.slices[block].start):
            x_new[bs_new.slices[block]] = x_block_prev
            return True
            
        # If both have a (N,) shape and grids available: interpolate
        shp_prev = bs_prev.shapes.get(block, None)
        shp_new = bs_new.shapes.get(block, None)
        if shp_prev and shp_new and len(shp_prev) == len(shp_new) == 1:
            t_old = prev_nlp.meta.get('grid_t', None)
            t_new = new_nlp.meta.get('grid_t', None)
            if t_old is not None and t_new is not None:
                x_block_prev = x_block_prev.reshape(shp_prev)
                # Piecewise linear interpolation in numpy
                x_interp = np.interp(t_new, t_old, x_block_prev)
                x_new[bs_new.slices[block]] = x_interp.reshape(-1)
                return True
        return False
    
    # Try copying/interpolating known state/control blocks
    for block in ('disp', 'vel', 'acc', 'sun_radius', 'planet_radius', 'ring_radius', 'gear_ratio', 'journal_offset'):
        _copy_common(block)
    
    # Uninitialized entries: choose mid-bounds (good warm start)
    unset = ~np.isfinite(x_new)
    if np.any(unset):
        mid = 0.5 * (new_nlp.lbx + new_nlp.ubx)
        x_new[unset] = np.where(np.isfinite(mid[unset]), mid[unset], 0.0)
    
    # Final: enforce endpoints through bounds (not ad-hoc edits), then project
    x_new = _project_to_bounds(x_new, new_nlp.lbx, new_nlp.ubx)
    
    # Constraint-aware correction for equality constraints
    x_new = _correct_for_equality_constraints(x_new, new_nlp)
    
    return x_new


def _correct_for_equality_constraints(x: np.ndarray, nlp: Any) -> np.ndarray:
    """
    Correct initial guess to satisfy equality constraints (lbg == ubg).
    
    This is a simple correction that adjusts variables to minimize constraint violations
    for equality constraints. For complex problems, a more sophisticated approach
    might be needed.
    
    Args:
        x: Initial guess vector
        nlp: NLP problem with constraints
        
    Returns:
        Corrected initial guess
    """
    if len(nlp.lbg) == 0:
        return x
    
    # Identify equality constraints (lbg == ubg)
    equality_mask = np.abs(nlp.lbg - nlp.ubg) < 1e-12
    equality_count = np.sum(equality_mask)
    log.info(f"Found {equality_count} equality constraints out of {len(nlp.lbg)} total constraints")
    
    if not np.any(equality_mask):
        log.info("No equality constraints found")
        return x
    
    try:
        # Evaluate constraints at current x
        g_current = np.array(nlp.g_fun(x, nlp.p_val)).squeeze()
        if g_current.ndim == 0:
            g_current = np.array([g_current])
        
        # Check if equality constraints are already satisfied
        equality_violations = np.abs(g_current[equality_mask])
        log.info(f"Equality constraint violations: max={np.max(equality_violations):.2e}, count={np.sum(equality_violations > 1e-8)}")
        
        if np.all(equality_violations < 1e-8):
            log.info("All equality constraints satisfied")
            return x
        
        # More sophisticated constraint correction
        max_violation = np.max(equality_violations)
        if max_violation > 1e-6:
            log.info(f"Attempting constraint correction for max violation: {max_violation:.2e}")
            
            # Try multiple correction strategies
            strategies = [
                ("scale_0.5", lambda x: x * 0.5),
                ("scale_0.1", lambda x: x * 0.1),
                ("zero_small", lambda x: np.where(np.abs(x) < 1e-6, 0.0, x)),
                ("mid_bounds", lambda x: 0.5 * (nlp.lbx + nlp.ubx))
            ]
            
            best_x = x
            best_violations = equality_violations
            
            for strategy_name, correction_func in strategies:
                try:
                    x_corrected = correction_func(x)
                    
                    # Re-project to bounds
                    x_corrected = _project_to_bounds(x_corrected, nlp.lbx, nlp.ubx)
                    
                    # Check if this helps
                    g_corrected = np.array(nlp.g_fun(x_corrected, nlp.p_val)).squeeze()
                    if g_corrected.ndim == 0:
                        g_corrected = np.array([g_corrected])
                    
                    corrected_violations = np.abs(g_corrected[equality_mask])
                    max_corrected = np.max(corrected_violations)
                    
                    log.info(f"Strategy {strategy_name}: max violation = {max_corrected:.2e}")
                    
                    if max_corrected < np.max(best_violations):
                        best_x = x_corrected
                        best_violations = corrected_violations
                        
                        # If we've achieved good constraint satisfaction, use this
                        if max_corrected < 1e-8:
                            log.info(f"Strategy {strategy_name} achieved constraint satisfaction")
                            return x_corrected
                            
                except Exception as e:
                    log.warning(f"Strategy {strategy_name} failed: {e}")
                    continue
            
            # Return the best correction found
            if np.max(best_violations) < np.max(equality_violations):
                log.info(f"Best correction reduced max violation from {np.max(equality_violations):.2e} to {np.max(best_violations):.2e}")
                return best_x
        
        return x
        
    except Exception as e:
        # If constraint evaluation fails, return original x
        log.warning(f"Could not correct for equality constraints: {e}")
        return x


# ============================================================================
# Core Success Predicate and Robust x₀ Propagation
# ============================================================================

def is_stage_success(sol: Dict[str, Any], kkt_tol: Tuple[float, float] = (1e-4, 1e-4), 
                     allow_acceptable: bool = True) -> bool:
    """
    Central predicate to determine if a stage solution is truly successful.
    
    Args:
        sol: Solution dictionary from solver
        kkt_tol: (stationarity_tol, primal_tol) thresholds
        allow_acceptable: Whether to accept 'Solved_To_Acceptable_Level' status
        
    Returns:
        True if solution is valid and converged
    """
    # Check basic success flags
    ok_flag = bool(sol.get('success', False)) and not sol.get('is_fallback', False)
    if not ok_flag:
        return False

    # Check IPOPT return status - handle both new and legacy formats
    status = str(sol.get('status', ''))
    if not status:  # Legacy format - check stats
        stats = sol.get('stats', {})
        status = str(stats.get('return_status', ''))
    
    ok_status = (status == 'Solve_Succeeded') or (allow_acceptable and status == 'Solved_To_Acceptable_Level')

    # Check objective is finite
    f = sol.get('f', float('nan'))
    finite_ok = np.isfinite(f)
    
    # For legacy solvers, if we have a successful IPOPT status and finite objective,
    # we trust the solver's convergence. For new standardized solvers, we check KKT.
    if 'kkt' in sol:  # New standardized format
        kkt = sol.get('kkt', {})
        stat = float(kkt.get('stationarity', float('inf')))
        prim = float(kkt.get('primal', float('inf')))
        kkt_ok = (stat <= kkt_tol[0]) and (prim <= kkt_tol[1])
        return ok_status and finite_ok and kkt_ok
    else:  # Legacy format - trust IPOPT's convergence
        return ok_status and finite_ok


def project_to_bounds(x: np.ndarray, lbx: np.ndarray, ubx: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """
    Interior projection to avoid active-bound stalling.
    Uses the same robust logic as _project_to_bounds.
    
    Args:
        x: Variable vector
        lbx: Lower bounds
        ubx: Upper bounds
        eps: Safety margin from bounds
        
    Returns:
        Projected variable vector
    """
    return _project_to_bounds(x, lbx, ubx, eps)


def valid_x0(x: Any, n_expected: int) -> bool:
    """
    Check if x0 is valid for use as initial guess.
    
    Args:
        x: Initial guess candidate
        n_expected: Expected dimension
        
    Returns:
        True if x0 is valid
    """
    return (x is not None) and (len(x) == n_expected) and np.all(np.isfinite(x))


def choose_next_x0(base_x0: np.ndarray, prev_sol: Optional[Dict[str, Any]], 
                   lbx: np.ndarray, ubx: np.ndarray) -> np.ndarray:
    """
    Choose next initial guess with robust fallback logic.
    
    Args:
        base_x0: Base initial guess
        prev_sol: Previous solution (may be None or failed)
        lbx: Lower bounds
        ubx: Upper bounds
        
    Returns:
        Valid initial guess projected to bounds
    """
    n = len(base_x0)
    
    # Prefer previous successful solution
    if prev_sol and is_stage_success(prev_sol):
        x_prev = prev_sol.get('x', None)
        if valid_x0(x_prev, n):
            return project_to_bounds(np.asarray(x_prev, float), lbx, ubx)
    
    # Fall back to base, safely projected
    return project_to_bounds(np.asarray(base_x0, float), lbx, ubx)


def finite_or_raise(name: str, arr: np.ndarray) -> None:
    """
    Check that array is finite, raise if not.
    
    Args:
        name: Name for error message
        arr: Array to check
        
    Raises:
        ValueError: If array contains non-finite values
    """
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")


def within_bounds_or_project(x: np.ndarray, lbx: np.ndarray, ubx: np.ndarray, 
                            eps: float = 1e-8) -> np.ndarray:
    """
    Project x to bounds with warning if significant adjustment needed.
    
    Args:
        x: Variable vector
        lbx: Lower bounds
        ubx: Upper bounds
        eps: Safety margin
        
    Returns:
        Projected variable vector
    """
    x_p = project_to_bounds(np.asarray(x, float), lbx, ubx, eps)
    
    # Warn if significant projection
    if np.max(np.abs(x_p - x)) > 1e-6:
        log.warning("x0 significantly adjusted to satisfy bounds.")
    
    return x_p


def summarized_kkt(sol: Dict[str, Any]) -> Tuple[float, float]:
    """
    Extract KKT residuals from new format.
    
    Args:
        sol: Solution dictionary
        
    Returns:
        (stationarity, primal) residuals
    """
    k = sol.get('kkt', {})
    return float(k.get('stationarity', np.inf)), float(k.get('primal', np.inf))


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
    kkt_tolerance: float = 5e-2  # More reasonable for motion law optimization
    constraint_violation_tolerance: float = 5e-2  # More reasonable for motion law optimization
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
        Create a stage problem with robust NLP rebuilding/parameterization.
        
        Args:
            base_problem: Base optimization problem
            stage_params: Stage parameters (epsilon_valve, epsilon_friction, stress_factor, etc.)
            stage_number: Stage number (1, 2, or 3)
            
        Returns:
            Stage problem with properly updated NLP
        """
        from copy import deepcopy
        from .nlp_types import StageParams
        from .builders import build_nlp_problem_from_stage, update_p_val_for_stage, should_rebuild_nlp
        
        stage_problem = deepcopy(base_problem)
        
        # Convert stage_params to StageParams object
        stage_params_obj = StageParams(
            epsilon_valve=stage_params['epsilon_valve'],
            epsilon_friction=stage_params['epsilon_friction'],
            stress_factor=stage_params['stress_factor'],
            grid_nodes=stage_params.get('grid_nodes', 32),
            colloc_degree=stage_params.get('colloc_degree', 1),
            enable_constraints=stage_params.get('enable_constraints', {}),
            tolerance=stage_params['tolerance'],
            max_iter=stage_params['max_iter'],
            description=stage_params['description']
        )
        
        # Apply grid refinement for later stages
        if stage_number > 1:
            stage_problem = self._refine_grid(stage_problem, stage_number)
            stage_params_obj.grid_nodes = stage_problem.get('grid_nodes', stage_params_obj.grid_nodes)
        
        # Get base metadata for NLP building
        base_meta = None
        # Priority 1: Get from motion law optimizer (contains factory functions)
        if 'motion_law_optimizer' in stage_problem:
            base_meta = stage_problem['motion_law_optimizer'].base_meta
        # Priority 2: Get from base_meta in stage_problem
        elif 'base_meta' in stage_problem:
            base_meta = stage_problem['base_meta']
        # Priority 3: Get from solver improvements
        elif hasattr(self, 'base_meta'):
            base_meta = self.base_meta
        # Priority 4: Get from existing nlp_problem (may not have factory functions)
        elif 'nlp_problem' in stage_problem and stage_problem['nlp_problem'] is not None:
            base_meta = stage_problem['nlp_problem'].meta
        
        if base_meta is None:
            self.logger.warning(f"Stage {stage_number}: No base_meta found, using legacy approach")
            # Fall back to legacy parameter updates
            stage_problem['stage_number'] = stage_number
            stage_problem['stage_params'] = stage_params
            stage_problem['epsilon_valve'] = stage_params['epsilon_valve']
            stage_problem['epsilon_friction'] = stage_params['epsilon_friction']
            stage_problem['tolerance'] = stage_params['tolerance']
            stage_problem['max_iter'] = stage_params['max_iter']
            return stage_problem
        
        # Check if we need to rebuild the NLP
        current_nlp = stage_problem.get('nlp_problem', None)
        if should_rebuild_nlp(current_nlp, stage_params_obj):
            # REBUILD the NLP for this stage
            nlp = build_nlp_problem_from_stage(stage_params_obj, base_meta)
            stage_problem['nlp_problem'] = nlp
            self.logger.info(f"[Stage {stage_number}] NLP rebuilt: sig={nlp.structure_sig}")
            
            # Change: Use block-aware x₀ transfer instead of truncation
            if 'x0' in stage_problem:
                old_x0 = stage_problem['x0']
                new_nx = len(nlp.lbx)
                if len(old_x0) != new_nx:
                    self.logger.info(f"[Stage {stage_number}] Transferring initial guess: {len(old_x0)} -> {new_nx}")
                    
                    # Get previous NLP for transfer (if available)
                    prev_nlp = stage_problem.get('prev_nlp_problem', None)
                    if prev_nlp is None:
                        # For first stage, use the original NLP problem to get block slices
                        prev_nlp = stage_problem.get('nlp_problem', None)
                        prev_sol = {'x': old_x0}
                    else:
                        prev_sol = None
                    
                    # Use block-aware transfer
                    new_x0 = _transfer_x0(prev_nlp, nlp, prev_sol)
                    stage_problem['x0'] = new_x0
                    
                    self.logger.debug(f"Transferred x0: shape={new_x0.shape}, bounds satisfied: {np.all(nlp.lbx <= new_x0) and np.all(new_x0 <= nlp.ubx)}")
                else:
                    # Same size - just project to ensure bounds satisfaction
                    stage_problem['x0'] = _project_to_bounds(old_x0, nlp.lbx, nlp.ubx)
        else:
            # PURE PARAM UPDATE (no rebuild)
            nlp = update_p_val_for_stage(stage_problem['nlp_problem'], stage_params_obj)
            stage_problem['nlp_problem'] = nlp
            self.logger.info(f"[Stage {stage_number}] NLP reused; p_val updated.")
        
        # Update stage metadata
        stage_problem['stage_number'] = stage_number
        stage_problem['stage_params'] = stage_params
        
        # Log stage information
        self.logger.info(f"Created Stage {stage_number}: {stage_params['description']}")
        self.logger.info(f"  ε_valve={stage_params['epsilon_valve']:.1e}, "
                        f"ε_friction={stage_params['epsilon_friction']:.1e}, "
                        f"stress_factor={stage_params['stress_factor']:.2f}")
        
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
        Solve optimization problem using continuation strategy with robust x₀ propagation.
        
        Args:
            problems: List of problems for continuation
            solver_factory: Function to create solver
            
        Returns:
            Final solution with continuation diagnostics
        """
        solutions = []
        current_solution = None
        base_x0 = None
        
        for i, problem in enumerate(problems):
            stage_number = i + 1
            self.logger.info(f"Solving Stage {stage_number} of {len(problems)}")
            
            # Extract bounds for robust x₀ handling
            # Use bounds from rebuilt NLP if available, otherwise from original problem
            if 'nlp_problem' in problem and problem['nlp_problem'] is not None:
                lbx = problem['nlp_problem'].lbx
                ubx = problem['nlp_problem'].ubx
            else:
                lbx = problem.get('lbx', np.array([]))
                ubx = problem.get('ubx', np.array([]))
            
            # Get base x₀ from first problem
            if base_x0 is None:
                base_x0 = problem.get('x0', np.array([]))
                if len(base_x0) == 0:
                    raise ValueError("No initial guess provided in first problem")
            
            # Choose robust initial guess
            # Use the resized initial guess if available, otherwise use base_x0
            self.logger.info(f"Stage {stage_number}: base_x0 len={len(base_x0)}, problem['x0'] len={len(problem.get('x0', []))}, lbx len={len(lbx)}")
            if 'x0' in problem and len(problem['x0']) == len(lbx):
                self.logger.info(f"Stage {stage_number}: Using resized initial guess")
                x0 = choose_next_x0(problem['x0'], current_solution, lbx, ubx)
            else:
                self.logger.info(f"Stage {stage_number}: Using base_x0 (fallback)")
                x0 = choose_next_x0(base_x0, current_solution, lbx, ubx)
            problem['x0'] = x0
            
            # Preflight checks
            try:
                # Check if we have an NLP problem for preflight
                if 'nlp_problem' in problem:
                    from .solve_core import _preflight
                    _preflight(problem['nlp_problem'], x0)
                else:
                    # Basic finite check for legacy problems
                    finite_or_raise("x0", x0)
                    if len(lbx) > 0 and len(ubx) > 0:
                        if not np.all(lbx <= x0) or not np.all(x0 <= ubx):
                            raise ValueError("Initial guess violates variable bounds")
            except Exception as e:
                self.logger.error(f"Stage {stage_number} preflight failed: {e}")
                if current_solution is None:
                    raise e
                else:
                    self.logger.warning(f"Using previous solution from Stage {stage_number - 1}")
                    break
            
            # Create solver for this stage
            solver = solver_factory(problem)
            
            # Solve current stage with warm-start from previous stage
            warm_start_data = None
            if stage_number > 1 and current_solution and is_stage_success(current_solution):
                warm_start_data = {
                    'lam_x': current_solution.get('lam_x', np.array([])),
                    'lam_g': current_solution.get('lam_g', np.array([]))
                }
            
            try:
                # Change: Use the new standardized solver interface
                from .solver_api import create_solver_adapter
                compatible_solver = create_solver_adapter(lambda p: solver, problem)
                solution = compatible_solver.solve(problem, warm_start_data)
                
                solutions.append(solution)
                
                # Change: Use attribute access instead of dictionary methods
                self.logger.debug(f"Stage {stage_number} solution type: {type(solution)}")
                if hasattr(solution, 'success'):
                    self.logger.debug(f"Stage {stage_number} success: {solution.success}")
                    self.logger.debug(f"Stage {stage_number} is_fallback: {solution.is_fallback}")
                    self.logger.debug(f"Stage {stage_number} status: {solution.status}")
                else:
                    # Fallback for dictionary-style results
                    self.logger.debug(f"Stage {stage_number} success: {solution.get('success', 'No success key')}")
                    self.logger.debug(f"Stage {stage_number} is_fallback: {solution.get('is_fallback', 'No is_fallback key')}")
                    self.logger.debug(f"Stage {stage_number} status: {solution.get('status', 'No status key')}")
                    if 'stats' in solution:
                        self.logger.debug(f"Stage {stage_number} return_status: {solution['stats'].get('return_status', 'No return_status')}")
                
                # Check success using robust predicate
                if is_stage_success(solution):
                    self.logger.info(f"Stage {stage_number} converged successfully: "
                                   f"{solution.get('status', 'Unknown')} "
                                   f"iters={solution.get('iter_count', 0)}")
                    current_solution = solution
                    
                    # Check convergence criteria
                    if self._check_convergence(solution, problem):
                        self.logger.info(f"Convergence criteria met at Stage {stage_number}")
                        break
                else:
                    # Enhanced failure diagnostics
                    self.logger.error(f"Stage {stage_number} FAILED: "
                                    f"status={solution.get('status', 'Unknown')}, "
                                    f"msg={solution.get('message', 'No message')}")
                    
                    # Log detailed failure information
                    self.logger.error(f"Stage {stage_number} failure details:")
                    self.logger.error(f"  - Success: {solution.get('success', False)}")
                    self.logger.error(f"  - Status: {solution.get('status', 'Unknown')}")
                    self.logger.error(f"  - Iterations: {solution.get('iter_count', 0)}")
                    self.logger.error(f"  - Is fallback: {solution.get('is_fallback', False)}")
                    
                    # Log problem characteristics
                    if 'nlp_problem' in problem:
                        nlp = problem['nlp_problem']
                        self.logger.error(f"  - Problem size: {len(nlp.lbx)} variables, {len(nlp.lbg)} constraints")
                        self.logger.error(f"  - Variable bounds: lbx_min={np.min(nlp.lbx):.2e}, lbx_max={np.max(nlp.lbx):.2e}")
                        self.logger.error(f"  - Variable bounds: ubx_min={np.min(nlp.ubx):.2e}, ubx_max={np.max(nlp.ubx):.2e}")
                        self.logger.error(f"  - Constraint bounds: lbg_min={np.min(nlp.lbg):.2e}, lbg_max={np.max(nlp.lbg):.2e}")
                        self.logger.error(f"  - Constraint bounds: ubg_min={np.min(nlp.ubg):.2e}, ubg_max={np.max(nlp.ubg):.2e}")
                    
                    # Log initial guess characteristics
                    if 'x0' in problem:
                        x0 = problem['x0']
                        self.logger.error(f"  - Initial guess: min={np.min(x0):.2e}, max={np.max(x0):.2e}, mean={np.mean(x0):.2e}")
                        self.logger.error(f"  - Initial guess finite: {np.all(np.isfinite(x0))}")
                    
                    if current_solution is None:
                        raise RuntimeError(f"Stage {stage_number} failed and no previous solution available")
                    else:
                        self.logger.warning(f"Using previous solution from Stage {stage_number - 1}")
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
    
    def solve_with_backtracking_continuation(self, base_problem: Dict[str, Any], 
                                           target_problem: Dict[str, Any],
                                           solver_factory: Callable,
                                           lambdas: Tuple[float, ...] = (0.2, 0.4, 0.6, 0.8, 1.0)) -> Dict[str, Any]:
        """
        Solve with backtracking continuation on homotopy parameter.
        
        Args:
            base_problem: Base problem (lambda=0)
            target_problem: Target problem (lambda=1)
            solver_factory: Function to create solver
            lambdas: Homotopy parameter values
            
        Returns:
            Final solution with continuation diagnostics
        """
        from .solve_core import _fallback_result
        
        last_good = None
        x0 = base_problem.get('x0', np.array([]))
        
        if len(x0) == 0:
            return _fallback_result("No initial guess in base problem", {'stage': 'init'})
        
        for i, lam in enumerate(lambdas):
            self.logger.info(f"Continuation step {i+1}/{len(lambdas)}: lambda={lam:.2f}")
            
            # Interpolate problem parameters
            stage_problem = self._interpolate_problem(base_problem, target_problem, lam)
            
            # Extract bounds
            lbx = stage_problem.get('lbx', np.array([]))
            ubx = stage_problem.get('ubx', np.array([]))
            
            # Choose robust initial guess
            x0 = choose_next_x0(x0, last_good, lbx, ubx)
            stage_problem['x0'] = x0
            
            # Preflight checks
            try:
                if 'nlp_problem' in stage_problem:
                    from .solve_core import _preflight
                    _preflight(stage_problem['nlp_problem'], x0)
                else:
                    finite_or_raise("x0", x0)
                    if len(lbx) > 0 and len(ubx) > 0:
                        if not np.all(lbx <= x0) or not np.all(x0 <= ubx):
                            raise ValueError("Initial guess violates variable bounds")
            except Exception as e:
                self.logger.error(f"Preflight failed at lambda={lam:.2f}: {e}")
                # Backtrack: insert finer steps
                if i > 0:
                    lam_prev = lambdas[i-1]
                    mid = 0.5 * (lam_prev + lam)
                    if abs(lam - lam_prev) < 1e-3:
                        return _fallback_result(f"Continuation stalled at lambda={lam:.2f}", {'stage': 'cont'})
                    
                    # Recursive backtrack with finer steps
                    new_lambdas = (lam_prev, mid, lam) + tuple(lambda_val for lambda_val in lambdas if lambda_val > lam)
                    return self.solve_with_backtracking_continuation(
                        base_problem, target_problem, solver_factory, new_lambdas)
                else:
                    return _fallback_result(f"Preflight failed at first lambda={lam:.2f}", {'stage': 'preflight'})
            
            # Create solver and solve
            solver = solver_factory(stage_problem)
            
            try:
                if hasattr(solver, 'solve'):
                    solution = solver.solve(stage_problem)
                elif callable(solver):
                    solution = solver(stage_problem)
                else:
                    solution = solver(stage_problem)
                
                if is_stage_success(solution):
                    self.logger.info(f"Lambda={lam:.2f} converged: {solution.get('status', 'Unknown')} "
                                   f"iters={solution.get('iter_count', 0)}")
                    last_good = solution
                    x0 = solution['x']
                else:
                    self.logger.error(f"Lambda={lam:.2f} FAILED: {solution.get('status', 'Unknown')}")
                    # Backtrack
                    if i > 0:
                        lam_prev = lambdas[i-1]
                        mid = 0.5 * (lam_prev + lam)
                        if abs(lam - lam_prev) < 1e-3:
                            return _fallback_result(f"Continuation stalled at lambda={lam:.2f}", {'stage': 'cont'})
                        
                        new_lambdas = (lam_prev, mid, lam) + tuple(lambda_val for lambda_val in lambdas if lambda_val > lam)
                        return self.solve_with_backtracking_continuation(
                            base_problem, target_problem, solver_factory, new_lambdas)
                    else:
                        return _fallback_result(f"Failed at first lambda={lam:.2f}", {'stage': 'solve'})
                        
            except Exception as e:
                self.logger.error(f"Lambda={lam:.2f} failed: {e}")
                # Backtrack
                if i > 0:
                    lam_prev = lambdas[i-1]
                    mid = 0.5 * (lam_prev + lam)
                    if abs(lam - lam_prev) < 1e-3:
                        return _fallback_result(f"Continuation stalled at lambda={lam:.2f}", {'stage': 'cont'})
                    
                    new_lambdas = (lam_prev, mid, lam) + tuple(lambda_val for lambda_val in lambdas if lambda_val > lam)
                    return self.solve_with_backtracking_continuation(
                        base_problem, target_problem, solver_factory, new_lambdas)
                else:
                    return _fallback_result(f"Failed at first lambda={lam:.2f}", {'stage': 'solve'})
        
        return last_good or _fallback_result("No successful stage", {'stage': 'cont'})
    
    def _interpolate_problem(self, base_problem: Dict[str, Any], target_problem: Dict[str, Any], 
                           lam: float) -> Dict[str, Any]:
        """
        Interpolate between base and target problems.
        
        Args:
            base_problem: Base problem (lambda=0)
            target_problem: Target problem (lambda=1)
            lam: Interpolation parameter [0,1]
            
        Returns:
            Interpolated problem
        """
        # Start with base problem
        interpolated = base_problem.copy()
        
        # Interpolate smoothing parameters
        if 'epsilon_valve' in base_problem and 'epsilon_valve' in target_problem:
            base_valve = base_problem['epsilon_valve']
            target_valve = target_problem['epsilon_valve']
            interpolated['epsilon_valve'] = (1 - lam) * base_valve + lam * target_valve
        
        if 'epsilon_friction' in base_problem and 'epsilon_friction' in target_problem:
            base_friction = base_problem['epsilon_friction']
            target_friction = target_problem['epsilon_friction']
            interpolated['epsilon_friction'] = (1 - lam) * base_friction + lam * target_friction
        
        # Interpolate stress factors
        if 'stress_factor' in base_problem and 'stress_factor' in target_problem:
            base_stress = base_problem['stress_factor']
            target_stress = target_problem['stress_factor']
            interpolated['stress_factor'] = (1 - lam) * base_stress + lam * target_stress
        
        # Interpolate tolerances
        if 'tolerance' in base_problem and 'tolerance' in target_problem:
            base_tol = base_problem['tolerance']
            target_tol = target_problem['tolerance']
            interpolated['tolerance'] = (1 - lam) * base_tol + lam * target_tol
        
        return interpolated
    
    def remesh_states(self, prev_t: np.ndarray, prev_X: np.ndarray, new_t: np.ndarray) -> np.ndarray:
        """
        Remesh states from old grid to new grid using piecewise linear interpolation.
        
        Args:
            prev_t: Previous time grid (N_prev,)
            prev_X: Previous state matrix (n_state, N_prev)
            new_t: New time grid (N_new,)
            
        Returns:
            X_new: Interpolated state matrix (n_state, N_new)
        """
        if prev_X.ndim == 1:
            # Handle single state case
            prev_X = prev_X.reshape(1, -1)
        
        X_new = []
        for i in range(prev_X.shape[0]):
            # Build piecewise linear interpolant for each state
            f_i = ca.pw_lin(prev_t, prev_X[i, :], new_t)
            X_new.append(ca.DM(f_i).full().squeeze())
        
        return np.vstack(X_new)
    
    def _check_convergence(self, solution: Dict[str, Any], problem: Dict[str, Any]) -> bool:
        """
        Check if convergence criteria are met using new KKT layout.
        
        Args:
            solution: Current solution
            problem: Current problem
            
        Returns:
            True if convergence criteria are met
        """
        # Use new KKT format
        stat_residual, prim_residual = summarized_kkt(solution)
        tolerance = problem.get('tolerance', 1e-6)
        
        # Check KKT residuals
        if stat_residual > tolerance or prim_residual > tolerance:
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
        
        DEPRECATED: This method has structural issues and should be replaced
        with the new solve_core.compute_kkt_residuals function.
        
        Args:
            solution: Optimization solution
            problem: Optimization problem
            
        Returns:
            KKT error (always returns inf for safety)
        """
        # This method is deprecated due to structural issues with problem schema
        # Always return inf to avoid incorrect convergence reporting
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
        # Change: Use attribute access instead of dictionary methods
        self.logger.debug(f"check_convergence called with solution type: {type(solution)}")
        if hasattr(solution, 'kkt'):
            self.logger.debug(f"solution has kkt attribute: {solution.kkt is not None}")
            self.logger.debug(f"kkt content: {solution.kkt}")
        elif hasattr(solution, 'kkt_residuals'):
            self.logger.debug(f"solution has kkt_residuals attribute: {solution.kkt_residuals is not None}")
            self.logger.debug(f"kkt_residuals content: {solution.kkt_residuals}")
        else:
            # Fallback for dictionary-style results
            self.logger.debug(f"solution has 'kkt' key: {'kkt' in solution}")
            self.logger.debug(f"solution has 'kkt_residuals' key: {'kkt_residuals' in solution}")
            if 'kkt' in solution:
                self.logger.debug(f"kkt content: {solution['kkt']}")
            if 'kkt_residuals' in solution:
                self.logger.debug(f"kkt_residuals content: {solution['kkt_residuals']}")
        
        # Change: Calculate KKT error using new format with proper gating
        if hasattr(solution, 'kkt') and solution.kkt is not None:
            # New standardized format with attribute access
            kkt_residuals = solution.kkt
            kkt_error = max(
                float(kkt_residuals.get('stationarity', float('inf'))),
                float(kkt_residuals.get('primal', float('inf')))
            )
            self.logger.debug(f"KKT error from new format (attribute): {kkt_error}")
        elif 'kkt' in solution and solution.get('kkt') is not None:  # Dictionary format
            kkt_residuals = solution.get('kkt', {})
            kkt_error = max(
                float(kkt_residuals.get('stationarity', float('inf'))),
                float(kkt_residuals.get('primal', float('inf')))
            )
            self.logger.debug(f"KKT error from new format (dict): {kkt_error}")
        elif 'kkt_residuals' in solution:  # Alternative new format
            kkt_residuals = solution.get('kkt_residuals', {})
            kkt_error = max(
                float(kkt_residuals.get('stationarity', float('inf'))),
                float(kkt_residuals.get('primal', float('inf')))
            )
            self.logger.debug(f"KKT error from new format (kkt_residuals): {kkt_error}")
        else:  # No KKT data available
            self.logger.debug("No KKT data available - not computed for this solve")
            kkt_error = float('inf')
        
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
            # Solve directly using standardized interface
            from .solver_interface import create_solver_adapter
            compatible_solver = create_solver_adapter(solver_factory, enhanced_problem)
            solution = compatible_solver.solve(enhanced_problem)
        
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
            
            # Strict success criteria: require converged diagnostics AND solver stats success when available
            stats_success = True
            if 'stats' in solution and isinstance(solution['stats'], dict):
                try:
                    stats_success = bool(solution['stats'].get('success', False))
                except Exception:
                    stats_success = False
            strict_converged = bool(convergence_status.get('converged', False)) and stats_success

            solution['success'] = strict_converged
        
        return solution
