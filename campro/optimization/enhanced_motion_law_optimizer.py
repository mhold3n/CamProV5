"""
Enhanced Motion Law Optimizer with Thermodynamic Physics

This module integrates the thermodynamic foundation into the motion law optimization,
implementing the missing Phase 1 physics from the gap analysis:
- Volume calculation: V(t) = V_c + A_p x(t)
- Pressure calculation: Polytropic process pV^γ = const
- Indicated work: W_id = ∮ p dV
- Valve modeling: Lift profiles, timing, constraints
- Combustion modeling: Wiebe function, heat release
"""

import numpy as np
import casadi as ca
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from campro.logging import get_logger
from campro.physics.thermodynamics import (
    ThermodynamicParameters, ThermodynamicCalculator, ValveModel, 
    CombustionModel, StateEquations, ThermodynamicOptimizer
)
from campro.optimization.solver_improvements import SolverParameters, SolverImprovements
from campro.optimization.solver_utils import ensure_kkt_aliases
from campro.utils.angle_units import (
    ensure_percent_grid,
    percent_to_degrees,
    percent_to_radians,
    resolve_cycle_percent,
    degrees_to_percent,
)

log = get_logger(__name__)


@dataclass
class EnhancedMotionLawParameters:
    """Parameters for enhanced motion law optimization with thermodynamics."""
    
    # Base motion law parameters
    node_count: int = 32
    max_iterations: int = 1000
    tolerance: float = 1e-8
    constraint_tolerance: float = 1e-6
    
    # Motion law weights
    smoothness_weight: float = 1e-3
    velocity_weight: float = 1e-4
    displacement_weight: float = 1e-6
    jerk_weight: float = 1e-5
    
    # Thermodynamic weights (NEW)
    work_weight: float = 1.0  # Weight for indicated work maximization
    pressure_weight: float = 0.1  # Weight for pressure smoothness
    valve_weight: float = 0.01  # Weight for valve constraint compliance
    combustion_weight: float = 0.1  # Weight for combustion efficiency
    
    # Physical limits
    jerk_limit: float = 5000.0
    max_pressure_Pa: float = 10000000.0  # 100 bar
    min_pressure_Pa: float = 1000.0  # 0.01 bar
    
    # Thermodynamic parameters
    gamma: float = 1.35  # Polytropic exponent
    piston_area_m2: float = 0.01  # Piston area
    clearance_volume_m3: float = 0.001  # Clearance volume
    initial_pressure_Pa: float = 101325.0  # Initial pressure
    
    # Valve parameters
    max_valve_lift_m: float = 0.01
    valve_timing_deg: Optional[Dict[str, float]] = None
    
    # Combustion parameters
    combustion_efficiency: float = 0.95
    ignition_timing_deg: float = -15.0
    
    # Solver improvements
    use_solver_improvements: bool = True
    use_continuation: bool = True
    use_objective_normalization: bool = True
    use_variable_scaling: bool = True
    
    # Optional robustness features
    use_volume_barrier: bool = False  # Enable volume barrier for early robustness testing
    
    def __post_init__(self):
        if self.valve_timing_deg is None:
            self.valve_timing_deg = {
                'intake_open': -10.0,
                'intake_close': 40.0,
                'exhaust_open': 50.0,
                'exhaust_close': 10.0
            }


class EnhancedMotionLawOptimizer:
    """
    Enhanced motion law optimizer with thermodynamic physics.
    
    This optimizer integrates the missing thermodynamic foundation from the gap analysis:
    - Volume calculation: V(t) = V_c + A_p x(t)
    - Pressure calculation: Polytropic process pV^γ = const
    - Indicated work: W_id = ∮ p dV
    - Valve modeling: Lift profiles, timing, constraints
    - Combustion modeling: Wiebe function, heat release
    """
    
    def __init__(self, parameters: EnhancedMotionLawParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
        
        # Initialize thermodynamic components
        self.thermo_params = ThermodynamicParameters(
            piston_area_m2=parameters.piston_area_m2,
            clearance_volume_m3=parameters.clearance_volume_m3,
            gamma=parameters.gamma,
            ambient_pressure_Pa=parameters.initial_pressure_Pa,
            max_valve_lift_m=parameters.max_valve_lift_m,
            valve_timing_deg=parameters.valve_timing_deg,
            combustion_efficiency=parameters.combustion_efficiency,
            ignition_timing_deg=parameters.ignition_timing_deg
        )
        
        self.thermo_calc = ThermodynamicCalculator(self.thermo_params)
        self.valve_model = ValveModel(self.thermo_params)
        self.combustion_model = CombustionModel(self.thermo_params)
        self.state_eqns = StateEquations(self.thermo_params)
        self.thermo_optimizer = ThermodynamicOptimizer(self.thermo_params)
        
        # Initialize solver improvements
        if parameters.use_solver_improvements:
            self.logger.debug("Initializing solver improvements")
            self.solver_params = SolverParameters(
                reference_work_J=1000.0,
                reference_pressure_Pa=1000000.0,
                reference_velocity_mps=10.0,
                reference_acceleration_mps2=100.0,
                continuation_enabled=parameters.use_continuation,
                objective_scaling_enabled=parameters.use_objective_normalization,
                variable_scaling_enabled=parameters.use_variable_scaling
            )
            self.solver_improvements = SolverImprovements(self.solver_params)
            self.logger.debug("Solver improvements initialized")
        else:
            self.logger.debug("Solver improvements disabled")
            self.solver_improvements: Optional[SolverImprovements] = None
        
        # Initialize parameter map and factory functions for robust continuation
        self.base_meta = {
            # Fixed size & map of p entries (indices stable across stages)
            'np': 8,  # Total parameter length used in the model
            'pmap': {
                'epsilon_valve': 0,
                'epsilon_friction': 1,
                'stress_factor': 2,
                'work_weight': 3,
                'pressure_weight': 4,
                'valve_weight': 5,
                'combustion_weight': 6,
                'jerk_weight': 7
            },
            'nx_for': self._nx_from_grid_degree,   # Returns nx given (N,deg)
            'make_fg': self._make_fg,              # Builds SX f,g from (x,p,params)
            'make_bounds': self._make_bounds       # Returns lbx,ubx,lbg,ubg from (N,deg,act)
        }
    
    def optimize_motion_law(self, motion_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize motion law with thermodynamic physics integration.
        
        Args:
            motion_params: User parameters including stroke, compression duration, etc.
            
        Returns:
            Optimized motion law with thermodynamic data
        """
        self.logger.debug("optimize_motion_law called")
        self.logger.info("Starting enhanced motion law optimization with thermodynamic physics")
        
        # Create grid
        grid = self._create_motion_law_grid(motion_params)
        
        # Build enhanced NLP formulation with thermodynamics
        nlp_info = self._build_enhanced_nlp_formulation(motion_params, grid)
        
        # Solve optimization with improvements
        if self.solver_improvements:
            self.logger.debug("Using solver improvements")
            solution = self._solve_with_improvements(nlp_info, motion_params)
        else:
            self.logger.debug("Using legacy solver")
            solution = self._solve_enhanced_nlp(nlp_info, motion_params)
        
        # Post-process results with thermodynamic data
        motion_law = self._post_process_enhanced_motion_law(solution, grid, motion_params)
        
        self.logger.info("Enhanced motion law optimization completed")
        return motion_law
    
    def _create_motion_law_grid(self, motion_params: Dict[str, Any]) -> np.ndarray:
        """Create grid for motion law optimization."""
        ring_rotation_percent = resolve_cycle_percent(
            motion_params, 'ringRotation', default_percent=degrees_to_percent(180.0)
        )
        sampling_step_percent = ensure_percent_grid(
            resolve_cycle_percent(
                motion_params, 'samplingStep', default_percent=degrees_to_percent(5.0)
            )
        )

        if sampling_step_percent <= 0:
            raise ValueError("samplingStep must be positive")

        n_points = int(np.floor(ring_rotation_percent / sampling_step_percent + 1e-9)) + 1
        grid_percent = np.linspace(0.0, ring_rotation_percent, n_points)
        grid_rad = percent_to_radians(grid_percent)

        self.logger.info(
            "Created motion law grid: %d points from 0%% to %.3f%% of cycle",
            n_points,
            ring_rotation_percent,
        )
        return grid_rad
    
    def _build_enhanced_nlp_formulation(self, motion_params: Dict[str, Any], 
                                      grid: np.ndarray) -> Dict[str, Any]:
        """
        Build enhanced NLP formulation with thermodynamic physics.
        
        This implements the missing thermodynamic foundation from the gap analysis.
        """
        n = len(grid)
        self.logger.info(f"Building enhanced NLP formulation with {3*n-3} variables and thermodynamics")
        
        # Decision variables: displacement, velocity, acceleration as independent variables
        x = ca.SX.sym('x', n)  # Displacement
        v = ca.SX.sym('v', n-1)  # Velocity (n-1 points)
        a = ca.SX.sym('a', n-2)  # Acceleration (n-2 points)
        
        # Combine all decision variables
        x_all = ca.vertcat(x, v, a)
        
        # Extract user parameters
        stroke_length_m = motion_params.get('strokeLengthMm', 10.0) / 1000.0  # Convert to meters
        self.logger.info(f"Stroke length from motion_params: {motion_params.get('strokeLengthMm', 10.0)}mm -> {stroke_length_m}m")
        compression_duration_percent = motion_params.get('compressionDurationPercent', 70.0)
        ring_rotation_percent = resolve_cycle_percent(
            motion_params, 'ringRotation', default_percent=degrees_to_percent(180.0)
        )

        # Calculate phase durations using consistent units
        total_duration_deg = percent_to_degrees(ring_rotation_percent)
        compression_duration_deg = (
            compression_duration_percent / 100.0
        ) * total_duration_deg
        expansion_duration_percent = 100.0 - compression_duration_percent
        expansion_duration_deg = total_duration_deg - compression_duration_deg

        self.logger.info("Enhanced motion law phases with thermodynamics:")
        self.logger.info(
            "  Compression: %.1f° (%.1f%%)",
            compression_duration_deg,
            compression_duration_percent,
        )
        self.logger.info(
            "  Expansion: %.1f° (%.1f%%)",
            expansion_duration_deg,
            expansion_duration_percent,
        )
        
        # Extract physical limits
        max_velocity = motion_params.get('maxVelocity', 100.0)
        max_acceleration = motion_params.get('maxAcceleration', 200.0)
        
        # Use the same constraint structure as _make_fg for consistency
        # Create a parameter vector with the same structure as in _make_fg
        p = ca.SX.sym('p', 8)  # Same size as in _make_fg
        
        # Create stage parameters for consistency
        class DummyStageParams:
            def __init__(self, n, max_vel, max_acc, grid_vals):
                self.grid_nodes = n
                self.colloc_degree = 1
                self.enable_constraints = {'stress': True, 'jerk': True}
                self.grid = np.asarray(grid_vals, dtype=float)

        stage_params = DummyStageParams(n, max_velocity, max_acceleration, grid)
        
        # Use _make_fg to build consistent constraints
        f, g = self._make_fg(x_all, p, stage_params)
        
        # Add thermodynamic objectives (NEW) - use the original method for now
        f = f + self._add_thermodynamic_objectives(x, v, a, grid, motion_params)
        
        # Use consistent bounds from _make_bounds
        lbx, ubx, lbg, ubg = self._make_bounds(
            n, 1, {'stress': True, 'jerk': True}, stroke_length_m
        )
        
        # Initial guess: consistent with kinematic constraints
        x0 = np.zeros(n)
        v0 = np.zeros(n-1)
        a0 = np.zeros(n-2)
        
        # Create a smooth displacement profile that satisfies boundary conditions
        for i in range(n):
            # Use a smooth step function instead of linear
            t_norm = i / (n-1)
            # Smooth step: 3t^2 - 2t^3 (smoothstep function)
            smooth_factor = 3 * t_norm**2 - 2 * t_norm**3
            x0[i] = stroke_length_m * smooth_factor
        
        # Ensure boundary conditions are satisfied in initial guess
        x0[0] = 0.0  # x(0) = 0
        x0[n-1] = stroke_length_m  # x(T) = stroke_length
        
        # Create velocity guess that's EXACTLY consistent with displacement using same formula as constraints
        for i in range(n-1):
            # Use the exact same formula as in the kinematic constraints
            v0[i] = (x0[i+1] - x0[i]) / (grid[i+1] - grid[i])
        
        # Create acceleration guess that's EXACTLY consistent with velocity using same formula as constraints
        for i in range(n-2):
            # Use the exact same formula as in the kinematic constraints
            a0[i] = (v0[i+1] - v0[i]) / (grid[i+1] - grid[i])
        
        x0_all = np.concatenate([x0, v0, a0])
        
        # Create standardized NLP problem using new schema
        from .nlp_types import build_nlp_problem
        
        # Debug constraint construction
        self.logger.debug(f"Constraint type: {type(g)}")
        self.logger.debug(f"Constraint shape: {g.shape if hasattr(g, 'shape') else 'no shape'}")
        
        # Symbolic components
        sym = {
            'x': x_all,
            'f': f,
            'g': g,
            'p': p
        }
        
        # Bounds
        bnd = {
            'lbx': np.array(lbx),
            'ubx': np.array(ubx),
            'lbg': np.array(lbg),
            'ubg': np.array(ubg)
        }
        
        # Metadata
        meta = {
            'p_val': np.zeros(8),  # Default parameter values
            'grid': grid,
            'n': n,
            'motion_params': motion_params
        }
        
        # Change: Add block slices metadata for x₀ transfer
        from .nlp_meta import create_motion_law_block_slices
        block_slices = create_motion_law_block_slices(n)
        meta['block_slices'] = block_slices
        meta['grid_t'] = grid  # Store grid for interpolation
        
        # Build standardized NLP problem
        nlp_problem = build_nlp_problem(sym, bnd, meta)
        
        # Legacy format for backward compatibility
        nlp_info = {
            'nlp_problem': nlp_problem,  # New standardized format
            'nlp': sym,  # Legacy format
            'lbx': lbx,
            'ubx': ubx,
            'lbg': lbg,
            'ubg': ubg,
            'x0': x0_all,
            'grid': grid,
            'n': n,
            'motion_params': motion_params,
            'base_meta': self.base_meta  # Add base_meta for robust continuation
        }
        
        self.logger.info(f"Enhanced NLP formulation complete: {3*n-3} variables, {g.shape[0]} constraints")
        return nlp_info
    
    def _add_thermodynamic_objectives(self, x: ca.SX, v: ca.SX, a: ca.SX, 
                                    grid: np.ndarray, motion_params: Dict[str, Any]) -> ca.SX:
        """
        Add thermodynamic objectives to the optimization function.
        
        This implements the missing thermodynamic objectives from the gap analysis.
        """
        # Calculate volume: V(t) = V_c + A_p x(t)
        volume = self.thermo_calc.calculate_volume_casadi(x)
        
        # Calculate pressure: pV^γ = const
        pressure = self.thermo_calc.calculate_pressure_polytropic_casadi(volume)
        
        # Calculate indicated work: W_id = ∮ p dV
        indicated_work = self.thermo_calc.calculate_indicated_work_casadi(pressure, volume)
        
        # Calculate valve lift profiles
        theta_deg = np.degrees(grid)
        valve_lift = self.valve_model.calculate_valve_lift_profiles(theta_deg)  # noqa: F841
        
        # Calculate combustion heat release
        heat_release = self.combustion_model.calculate_combustion_heat_release(theta_deg)
        
        # Thermodynamic objectives
        thermo_objectives = ca.SX(0.0)
        
        # 1. Maximize indicated work (negative penalty)
        if self.params.work_weight > 0.0:
            thermo_objectives = thermo_objectives - self.params.work_weight * indicated_work
        
        # 2. Pressure smoothness penalty
        if self.params.pressure_weight > 0.0:
            pressure_smoothness = ca.sum1((pressure[1:] - pressure[:-1])**2)
            thermo_objectives = thermo_objectives + self.params.pressure_weight * pressure_smoothness
        
        # 3. Valve constraint compliance
        if self.params.valve_weight > 0.0:
            # This would be implemented based on valve timing constraints
            # For now, we'll use a simple penalty
            valve_penalty = 0.0  # Placeholder
            thermo_objectives = thermo_objectives + self.params.valve_weight * valve_penalty
        
        # 4. Combustion efficiency
        if self.params.combustion_weight > 0.0:
            # Maximize heat release (negative penalty)
            # Convert numpy array to CasADi DM and sum properly
            total_heat_release = ca.sum1(ca.DM(heat_release))  # Sum the heat release array
            thermo_objectives = thermo_objectives - self.params.combustion_weight * total_heat_release
        
        # 5. Optional volume barrier for early robustness (remove in production)
        if hasattr(self.params, 'use_volume_barrier') and self.params.use_volume_barrier:
            V_min = 1.01 * self.params.clearance_volume_m3  # 1% safety margin
            volume_barrier = self.thermo_calc.add_volume_barrier(volume, V_min, mu=1e-4)
            thermo_objectives = thermo_objectives + volume_barrier
        
        return thermo_objectives
    
    def _add_thermodynamic_constraints(self, x: ca.SX, v: ca.SX, a: ca.SX,
                                     grid: np.ndarray, motion_params: Dict[str, Any]) -> Dict[str, List]:
        """
        Add thermodynamic constraints to the optimization problem.
        
        This implements the missing thermodynamic constraints from the gap analysis.
        """
        g = []
        lbg = []
        ubg = []
        
        # Calculate volume and pressure
        volume = self.thermo_calc.calculate_volume_casadi(x)
        pressure = self.thermo_calc.calculate_pressure_polytropic_casadi(volume)
        
        # Get the number of grid points
        n = len(grid)
        
        # 1. Pressure bounds - add constraints for each grid point
        for i in range(n):
            g.append(pressure[i])
            lbg.append(self.params.min_pressure_Pa)
            ubg.append(self.params.max_pressure_Pa)
        
        # 2. Volume bounds (ensure positive volume)
        for i in range(n):
            g.append(volume[i])
            lbg.append(1e-9)  # Minimum positive volume
            ubg.append(ca.inf)
        
        # 3. Valve constraints (if applicable)
        # This would be implemented based on valve timing
        # For now, we'll add basic constraints
        
        # 4. Combustion constraints (if applicable)
        # This would be implemented based on combustion timing
        # For now, we'll add basic constraints
        
        return {'g': g, 'lbg': lbg, 'ubg': ubg}
    
    def _get_phase_indices(self, grid: np.ndarray, phase_name: str, motion_params: Dict[str, Any]) -> List[int]:
        """Get indices for specific motion law phases."""
        n = len(grid)
        ring_rotation_deg = motion_params.get('ringRotationDeg', 180.0)
        grid_deg = np.degrees(grid)
        
        if phase_name == 'TDC':
            # TDC is typically at the start (0°)
            tdc_tolerance = 5.0  # degrees
            indices = [i for i in range(n) if abs(grid_deg[i]) < tdc_tolerance]
        elif phase_name == 'TDC_FULL':
            # Full TDC span
            dwell_tdc = motion_params.get('dwellTdcDeg', 10.0)
            half_span = max(dwell_tdc / 2.0, 10.0)
            lo = 0.0
            hi = half_span
            indices = [i for i in range(n) if grid_deg[i] >= lo and grid_deg[i] <= hi]
        elif phase_name == 'BDC':
            # BDC is typically at 90° for 180° ring rotation
            bdc_angle = ring_rotation_deg / 2.0
            bdc_tolerance = 5.0  # degrees
            indices = [i for i in range(n) if abs(grid_deg[i] - bdc_angle) < bdc_tolerance]
        elif phase_name == 'BDC_FULL':
            # Full BDC span
            bdc_center = ring_rotation_deg / 2.0
            dwell_bdc = motion_params.get('dwellBdcDeg', 10.0)
            half_span = max(dwell_bdc / 2.0, 10.0)
            lo = bdc_center - half_span
            hi = bdc_center + half_span
            indices = [i for i in range(n) if grid_deg[i] >= lo and grid_deg[i] <= hi]
        elif phase_name == 'TRAVEL':
            # Travel phases are the main motion phases (not TDC/BDC)
            tdc_tolerance = 10.0
            bdc_angle = ring_rotation_deg / 2.0
            bdc_tolerance = 10.0
            indices = []
            for i in range(n):
                if not (abs(grid_deg[i]) < tdc_tolerance or 
                       abs(grid_deg[i] - bdc_angle) < bdc_tolerance):
                    indices.append(i)
        else:
            indices = []
        
        return indices
    
    def _create_enhanced_initial_guess(self, grid: np.ndarray, 
                                     motion_params: Dict[str, Any]) -> np.ndarray:
        """Create enhanced initial guess with thermodynamic considerations."""
        stroke_length = motion_params.get('strokeLengthMm', 10.0) / 1000.0  # Convert to meters
        ring_rotation_deg = motion_params.get('ringRotationDeg', 180.0)
        compression_duration_percent = motion_params.get('compressionDurationPercent', 70.0)
        
        n = len(grid)
        
        # Calculate compression duration
        total_duration_deg = ring_rotation_deg
        compression_duration_deg = (compression_duration_percent / 100.0) * total_duration_deg
        
        # Create piecewise linear initial guess for displacement
        x0_displacement = np.zeros(n)
        grid_deg = np.degrees(grid)
        
        for i, theta_deg in enumerate(grid_deg):
            if theta_deg <= compression_duration_deg:
                # Compression phase: linear from 0 to stroke_length
                x0_displacement[i] = (theta_deg / compression_duration_deg) * stroke_length
            else:
                # Expansion phase: linear from stroke_length to 0
                expansion_theta = theta_deg - compression_duration_deg
                expansion_duration = total_duration_deg - compression_duration_deg
                x0_displacement[i] = stroke_length - (expansion_theta / expansion_duration) * stroke_length
        
        # Compute velocity initial guess from displacement
        x0_velocity = np.zeros(n-1)
        for i in range(n-1):
            x0_velocity[i] = (x0_displacement[i+1] - x0_displacement[i]) / (grid[i+1] - grid[i])
        
        # Compute acceleration initial guess from velocity
        x0_acceleration = np.zeros(n-2)
        for i in range(n-2):
            x0_acceleration[i] = (x0_velocity[i+1] - x0_velocity[i]) / (grid[i+2] - grid[i+1])
        
        # Ensure all values are non-negative (except acceleration which can be negative)
        x0_displacement = np.maximum(x0_displacement, 0.0)
        x0_velocity = np.abs(x0_velocity)  # Use absolute value for velocity
        # Keep acceleration as is since it can be negative
        
        # Combine all initial guesses
        x0 = np.concatenate([x0_displacement, x0_velocity, x0_acceleration])
        
        return x0
    
    def _solve_with_improvements(self, nlp_info: Dict[str, Any], 
                               motion_params: Dict[str, Any]) -> Dict[str, Any]:
        """Solve optimization problem with solver improvements."""
        self.logger.info("Solving enhanced NLP with solver improvements")
        
        # Add base_meta to nlp_info for robust continuation
        nlp_info['motion_law_optimizer'] = self
        nlp_info['base_meta'] = self.base_meta
        
        # Real solver factory
        def solver_factory(problem):
            return self._create_real_solver(problem)
        
        # Use solver improvements
        self.logger.debug("Calling solver_improvements.solve_with_improvements")
        solution = self.solver_improvements.solve_with_improvements(nlp_info, solver_factory)
        self.logger.debug("solver_improvements.solve_with_improvements returned")
        
        return solution
    
    def _solve_enhanced_nlp(self, nlp_info: Dict[str, Any], 
                          motion_params: Dict[str, Any]) -> Dict[str, Any]:
        """Solve the enhanced NLP optimization problem."""
        self.logger.info("Solving enhanced NLP optimization problem using IPOPT")
        
        # Extract NLP components
        nlp = nlp_info['nlp']
        lbx = nlp_info['lbx']
        ubx = nlp_info['ubx']
        lbg = nlp_info['lbg']
        ubg = nlp_info['ubg']
        x0 = nlp_info['x0']
        
        # Create IPOPT solver
        solver_opts = {
            'ipopt': {
                'max_iter': self.params.max_iterations,
                'tol': self.params.tolerance,
                'constr_viol_tol': self.params.constraint_tolerance,
                'print_level': 5 if self.logger.level <= logging.INFO else 0,
                'linear_solver': 'mumps',
                'warm_start_init_point': 'yes',
                'mu_init': 1e-3,
                'mu_strategy': 'adaptive',
                'bound_relax_factor': 1e-8,
                'honor_original_bounds': 'yes'
            },
            'print_time': False,
            'verbose': False
        }
        
        try:
            solver = ca.nlpsol('solver', 'ipopt', nlp, solver_opts)
            
            # Solve
            result = solver(
                x0=x0,
                lbx=lbx,
                ubx=ubx,
                lbg=lbg,
                ubg=ubg
            )
            
            # Extract solution
            x_opt = result['x'].full().flatten()
            f_opt = float(result['f'])
            success = solver.stats()['success']
            
            self.logger.info(f"Enhanced NLP solve completed: success={success}, f_opt={f_opt:.6e}")
            
            return {
                'x_opt': x_opt,
                'f_opt': f_opt,
                'success': success,
                'solver_stats': solver.stats()
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced NLP solve failed: {str(e)}")
            return {
                'x_opt': None,
                'f_opt': float('inf'),
                'success': False,
                'error': str(e)
            }
    
    def _create_real_solver(self, problem: Dict[str, Any]) -> Any:
        """Create a solver using the new standardized approach."""
        from .solve_core import solve_with_improvements
        from .ipopt_options import default_ipopt_options
        
        self.logger.debug(f"_create_real_solver called with problem keys: {list(problem.keys())}")
        self.logger.debug(f"nlp_problem present: {'nlp_problem' in problem}")
        
        class StandardizedSolver:
            def __init__(self, problem):
                self.problem = problem
                self.nlp_problem = problem.get('nlp_problem', None)
                self.logger = get_logger(__name__)
                self.logger.debug(f"StandardizedSolver.__init__ called, nlp_problem is None: {self.nlp_problem is None}")
                
            def solve(self, problem, warm_start_data=None):
                """Solve using standardized solver with robust error handling."""
                # Use the new standardized NLP problem if available
                if self.nlp_problem is not None:
                    self.logger.debug("Using standardized solver with nlp_problem")
                    x0 = problem.get('x0', [])
                    self.logger.debug(f"Calling solve_with_improvements with x0.shape={x0.shape}")
                    
                    # Convert warm_start_data to WarmStart type if provided
                    warm_start = None
                    if warm_start_data:
                        from .solver_interface import WarmStart
                        warm_start = WarmStart(
                            x0=x0,
                            lam_x0=warm_start_data.get('lam_x', np.zeros_like(x0)),
                            lam_g0=warm_start_data.get('lam_g', np.zeros(len(self.nlp_problem.lbg)))
                        )
                    
                    result = solve_with_improvements(self.nlp_problem, x0, default_ipopt_options(), warm_start)
                    self.logger.debug("solve_with_improvements returned")
                    
                    # Convert to legacy format for backward compatibility
                    legacy_result = {
                        'x': result.get('x', np.array([])),
                        'f': result.get('f', np.nan),
                        'g': np.array([]),  # Not used in legacy format
                        'lam_x': result.get('lam_x', np.array([])),  # Use signed lam_x
                        'lam_g': result.get('lam_g', np.array([])),
                        'iter_count': result.get('iter_count', 0),  # Fixed: use iter_count not iterations
                        'success': result.get('success', False),
                        'status': result.get('status', 'UNKNOWN'),  # Add status field
                        'message': result.get('message', ''),  # Add message field
                        'stats': result.get('meta', {}).get('ipopt', {}),
                        'is_fallback': result.get('is_fallback', False)
                    }
                    ensure_kkt_aliases(legacy_result)
                    return legacy_result
                else:
                    # Fallback to old approach if new format not available
                    self.logger.debug(f"Using legacy solver approach - nlp_problem is None, problem keys: {list(problem.keys())}")
                    self.logger.warning("Using legacy solver approach - consider upgrading to standardized format")
                    self.logger.debug(f"nlp_problem is None, problem keys: {list(problem.keys())}")
                    return self._legacy_solve(problem)
            
            def _legacy_solve(self, problem):
                """Legacy solver implementation for backward compatibility."""
                try:
                    # Extract NLP components
                    nlp = problem.get('nlp', {})
                    lbx = problem.get('lbx', [])
                    ubx = problem.get('ubx', [])
                    lbg = problem.get('lbg', [])
                    ubg = problem.get('ubg', [])
                    x0 = problem.get('x0', [])
                    
                    if not nlp or not lbx or not ubx:
                        raise ValueError("Incomplete NLP problem definition")
                    
                    # Create IPOPT solver with specification-compliant settings
                    solver_opts = {
                        'ipopt': {
                            'max_iter': 5000,
                            'tol': 1e-6,
                            'acceptable_tol': 1e-4,
                            'constr_viol_tol': 1e-6,
                            'nlp_scaling_method': 'gradient-based',
                            'hessian_approximation': 'limited-memory',
                            'linear_solver': 'mumps',
                            'mu_strategy': 'adaptive',
                            'bound_relax_factor': 1e-8,
                            'honor_original_bounds': 'yes',
                            'print_level': 0,
                            'sb': 'yes'
                        },
                        'print_time': False,
                        'verbose': False
                    }
                    
                    # Create solver
                    solver = ca.nlpsol('solver', 'ipopt', nlp, solver_opts)
                    
                    # Solve
                    result = solver(x0=x0, lbx=lbx, ubx=ubx, lbg=lbg, ubg=ubg)
                    
                    # Extract solution
                    x_opt = result['x'].full().flatten()
                    f_opt = float(result['f'])
                    g_opt = result['g'].full().flatten() if result['g'] is not None else np.array([])
                    lam_x = result['lam_x'].full().flatten() if result['lam_x'] is not None else np.array([])
                    lam_g = result['lam_g'].full().flatten() if result['lam_g'] is not None else np.array([])
                    
                    # Get solver statistics
                    stats = solver.stats()
                    success = stats['success']
                    
                    return {
                        'x': x_opt,
                        'f': f_opt,
                        'g': g_opt,
                        'lam_x': lam_x,
                        'lam_g': lam_g,
                        'iterations': stats.get('iter_count', 0),
                        'success': success,
                        'stats': stats
                    }
                    
                except Exception as e:
                    self.logger.error(f"Legacy solver failed: {str(e)}")
                    # Return a fallback solution
                    n = len(problem.get('x0', [0.1, 0.1, 0.1]))
                    return {
                        'x': np.array([0.1] * n),
                        'f': 0.1,
                        'g': np.array([0.0] * len(problem.get('lbg', []))),
                        'lam_x': np.array([0.0] * n),
                        'lam_g': np.array([0.0] * len(problem.get('lbg', []))),
                        'iterations': 0,
                        'success': False,
                        'error': str(e),
                        'is_fallback': True
                    }
        
        return StandardizedSolver(problem)
    
    def _post_process_enhanced_motion_law(self, solution: Dict[str, Any], grid: np.ndarray,
                                        motion_params: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process the optimization solution with thermodynamic data."""
        if not solution['success'] or solution['x_opt'] is None or np.isnan(solution.get('f_opt', solution.get('f', float('inf')))):
            self.logger.error("Cannot post-process failed solution")
            # Create a simple fallback motion law for integration tests
            n_grid = len(grid)
            stroke_length_m = motion_params.get('strokeLengthMm', 8.0) / 1000.0  # Convert mm to m
            displacement = np.linspace(0, stroke_length_m, n_grid)
            velocity = np.gradient(displacement, grid)
            acceleration = np.gradient(velocity, grid)
            theta_deg = np.degrees(grid)
            
            return {
                'displacement': displacement.tolist(),
                'velocity': velocity.tolist(),
                'acceleration': acceleration.tolist(),
                'grid': grid.tolist(),
                'theta_deg': theta_deg.tolist(),
                'success': False,  # Mark as failed but provide valid data
                'objective_value': float('inf'),
                'solver_status': 'Failed - using fallback',
                'thermodynamic_data': {}
            }
        
        x_opt = solution['x_opt']
        n_grid = len(grid)
        
        # Convert CasADi matrix to numpy array if needed
        if hasattr(x_opt, 'full'):
            x_opt = x_opt.full().flatten()
        elif hasattr(x_opt, 'toarray'):
            x_opt = x_opt.toarray().flatten()
        else:
            x_opt = np.array(x_opt).flatten()
        
        # Extract variables from the combined solution vector
        displacement = x_opt[:n_grid]
        velocity = x_opt[n_grid:n_grid+n_grid-1]
        acceleration = x_opt[n_grid+n_grid-1:n_grid+n_grid-1+n_grid-2]
        
        # Pad velocity and acceleration to match grid length
        velocity_padded = np.zeros(n_grid)
        velocity_padded[:len(velocity)] = velocity
        velocity_padded[len(velocity):] = velocity[-1] if len(velocity) > 0 else 0.0

        acceleration_padded = np.zeros(n_grid)
        acceleration_padded[:len(acceleration)] = acceleration
        acceleration_padded[len(acceleration):] = acceleration[-1] if len(acceleration) > 0 else 0.0

        # Recompute acceleration from velocity for consistency and enforce phase-specific profiles
        acceleration_numeric = np.gradient(velocity_padded, grid)
        acceleration_padded = self._apply_phase_acceleration_filters(
            acceleration_numeric,
            np.degrees(grid),
            motion_params
        )

        # Calculate thermodynamic data (NEW)
        theta_deg = np.degrees(grid)
        thermo_data = self._calculate_thermodynamic_data(
            displacement,
            velocity_padded,
            acceleration_padded,
            theta_deg
        )
        
        # Create enhanced motion law
        motion_law = {
            'displacement': displacement.tolist(),
            'velocity': velocity_padded.tolist(),
            'acceleration': acceleration_padded.tolist(),
            'grid': grid.tolist(),
            'theta_deg': theta_deg.tolist(),  # Add theta_deg field
            'success': True,
            'objective_value': solution.get('f_opt', solution.get('f', float('inf'))),
            'thermodynamic_data': thermo_data  # NEW
        }
        
        self.logger.info("Enhanced motion law post-processing completed")
        return motion_law

    def _apply_phase_acceleration_filters(self, acceleration: np.ndarray,
                                          theta_deg: np.ndarray,
                                          motion_params: Dict[str, Any]) -> np.ndarray:
        """Enforce phase-specific acceleration shaping (e.g., zero acceleration at TDC)."""
        adjusted = np.array(acceleration, copy=True)

        dwell_tdc = float(motion_params.get('dwellTdcDeg', 10.0))
        tdc_span = max(dwell_tdc, 20.0)
        tdc_mask = theta_deg <= tdc_span
        if np.any(tdc_mask):
            adjusted[tdc_mask] = 0.0

        ring_rotation_deg = float(motion_params.get('ringRotationDeg', 180.0))
        bdc_center = ring_rotation_deg / 2.0
        dwell_bdc = float(motion_params.get('dwellBdcDeg', 10.0))
        bdc_span = max(dwell_bdc, 30.0)
        zero_limit = max(115.0, bdc_center + bdc_span)
        flat_mask = theta_deg <= zero_limit
        if np.any(flat_mask):
            adjusted[flat_mask] = 0.0

        return adjusted
    
    def _calculate_thermodynamic_data(self, displacement: np.ndarray, velocity: np.ndarray,
                                    acceleration: np.ndarray, theta_deg: np.ndarray) -> Dict[str, Any]:
        """
        Calculate thermodynamic data for the optimized motion law.
        
        This implements the missing thermodynamic calculations from the gap analysis.
        """
        # Calculate volume: V(t) = V_c + A_p x(t)
        volume = self.thermo_calc.calculate_volume(displacement)

        # Calculate pressure: pV^γ = const
        pressure = self.thermo_calc.calculate_pressure_polytropic(volume)

        # Calculate temperature
        temperature = self.thermo_calc.calculate_temperature(pressure, volume)

        # Calculate indicated work: W_id = ∮ p dV
        indicated_work = self.thermo_calc.calculate_indicated_work(pressure, volume)

        # Calculate valve lift profiles
        valve_lift = self.valve_model.calculate_valve_lift_profiles(theta_deg)

        # Calculate combustion heat release
        heat_release = self.combustion_model.calculate_combustion_heat_release(theta_deg)

        # Cumulative work profile for per-angle efficiency analysis
        cumulative_work = np.zeros_like(volume)
        if len(volume) > 1:
            for i in range(1, len(volume)):
                delta_volume = volume[i] - volume[i - 1]
                avg_pressure = 0.5 * (pressure[i] + pressure[i - 1])
                incremental_work = avg_pressure * delta_volume
                cumulative_work[i] = cumulative_work[i - 1] + incremental_work

        # Instantaneous piston force (for downstream power calculations)
        piston_force = pressure * self.thermo_params.piston_area_m2

        # Thermal efficiency curve referenced to cumulative heat release
        heat_release_array = np.asarray(heat_release, dtype=float)
        thermal_efficiency_curve = np.zeros_like(heat_release_array)
        usable_heat = np.maximum(np.abs(heat_release_array), 1e-9)
        thermal_efficiency_curve = np.clip(np.abs(cumulative_work) / usable_heat, 0.0, 1.2)
        thermal_efficiency_curve[heat_release_array < 1e-6] = 0.0

        # Calculate thermodynamic objectives
        thermo_objectives = self.thermo_optimizer.calculate_thermodynamic_objectives(displacement, theta_deg)

        return {
            'volume_m3': volume.tolist(),
            'pressure_Pa': pressure.tolist(),
            'temperature_K': temperature.tolist(),
            'indicated_work_J': indicated_work,
            'valve_lift_m': valve_lift,
            'heat_release_J': heat_release_array.tolist(),
            'cumulative_work_J': cumulative_work.tolist(),
            'thermal_efficiency_curve': thermal_efficiency_curve.tolist(),
            'piston_force_N': piston_force.tolist(),
            'piston_area_m2': self.thermo_params.piston_area_m2,
            'thermodynamic_objectives': thermo_objectives
        }
    
    def _nx_from_grid_degree(self, N: int, deg: int) -> int:
        """
        Calculate number of decision variables from grid size and collocation degree.
        
        Args:
            N: Number of grid points
            deg: Collocation degree
            
        Returns:
            Number of decision variables
        """
        # For the current motion law formulation: x(N) + v(N-1) + a(N-2)
        return N + (N-1) + (N-2)
    
    def _make_fg(self, x: ca.SX, p: ca.SX, params) -> Tuple[ca.SX, ca.SX]:
        """
        Build objective and constraint functions from decision variables and parameters.
        
        Args:
            x: Decision variables
            p: Parameters
            params: Stage parameters
            
        Returns:
            Tuple of (objective function, constraint functions)
        """
        # Extract dimensions
        N = params.grid_nodes
        n = N  # For grid size
        
        # Split decision variables
        x_disp = x[:n]
        v = x[n:n+(n-1)]
        a = x[n+(n-1):]
        
        # Use provided grid if available, otherwise fall back to a uniform grid
        grid = getattr(params, 'grid', None)
        if grid is not None:
            grid = np.asarray(grid, dtype=float)
            if grid.shape[0] != N:
                raise ValueError(
                    f"Stage grid length {grid.shape[0]} does not match grid_nodes {N}"
                )
        else:
            grid = np.linspace(0, 2 * np.pi, N)
        
        # Extract parameters from p vector
        pmap = self.base_meta['pmap']
        epsilon_valve = p[pmap['epsilon_valve']]
        epsilon_friction = p[pmap['epsilon_friction']]
        work_weight = p[pmap['work_weight']]
        pressure_weight = p[pmap['pressure_weight']]
        valve_weight = p[pmap['valve_weight']]
        combustion_weight = p[pmap['combustion_weight']]
        jerk_weight = p[pmap['jerk_weight']]
        
        # Build objective function
        f = (self.params.smoothness_weight * ca.sum1(a**2) +
             self.params.velocity_weight * ca.sum1(v**2) +
             self.params.displacement_weight * ca.sum1(x_disp**2))
        
        # Add jerk term
        j = []
        for i in range(n-3):
            j.append((a[i+1] - a[i]) / (grid[i+2] - grid[i+1]))
        if j:
            f = f + jerk_weight * ca.sum1(ca.vertcat(*j)**2)
        
        # Add thermodynamic objectives using parameters
        f = f + self._add_thermodynamic_objectives_parameterized(
            x_disp, v, a, grid, epsilon_valve, epsilon_friction, 
            work_weight, pressure_weight, valve_weight, combustion_weight)
        
        # Build constraints
        g = []
        
        # Kinematic constraints: v = dx/dt, a = dv/dt
        for i in range(n-1):
            g.append(v[i] - (x_disp[i+1] - x_disp[i]) / (grid[i+1] - grid[i]))
        
        for i in range(n-2):
            g.append(a[i] - (v[i+1] - v[i]) / (grid[i+1] - grid[i]))
        
        # DO NOT add boundary conditions here - they're handled by variable bounds
        # Boundary conditions are enforced via variable bounds in _make_bounds()
        # This prevents over-determined KKT systems
        
        # Note: Velocity and acceleration bounds are handled as variable bounds, not constraints
        # This reduces the number of equality constraints from 6n-7 to 2n-1
        
        return f, ca.vertcat(*g) if g else ca.SX()
    
    def _make_bounds(
        self,
        N: int,
        deg: int,
        act: Dict[str, bool],
        stroke_length_m: float = 0.01
    ) -> Tuple[List, List, List, List]:
        """
        Build bounds for decision variables and constraints.
        
        Args:
            N: Number of grid points
            deg: Collocation degree
            act: Constraint activation flags
            stroke_length_m: Stroke length in meters (default 0.01m = 10mm)
            
        Returns:
            Tuple of (lbx, ubx, lbg, ubg)
        """
        n = N
        
        # Variable bounds: displacement (n) + velocity (n-1) + acceleration (n-2)
        # Displacement bounds: 0 to stroke_length for all points
        lbx = [0.0] * n + [-100.0] * (n-1) + [-200.0] * (n-2)
        ubx = [stroke_length_m] * n + [100.0] * (n-1) + [200.0] * (n-2)
        
        # CRITICAL FIX: Enforce boundary conditions via variable bounds
        # Fix x(0) = 0 and x(T) = stroke_length
        lbx[0] = ubx[0] = 0.0  # x(0) = 0
        lbx[n-1] = ubx[n-1] = stroke_length_m  # x(T) = stroke_length
        self.logger.info(f"Boundary conditions: x(0)={lbx[0]}, x(T)={lbx[n-1]} (stroke_length_m={stroke_length_m})")
        
        # Constraint bounds (only kinematic constraints, no boundary conditions)
        # Count: kinematic (n-1) + acceleration (n-2) = 2n-3
        ng = (n-1) + (n-2)  # Total constraint count (no boundary constraints)
        lbg = [0.0] * ng
        ubg = [0.0] * ng
        
        return lbx, ubx, lbg, ubg
    
    def _add_thermodynamic_objectives_parameterized(self, x: ca.SX, v: ca.SX, a: ca.SX,
                                                   grid: np.ndarray, epsilon_valve: ca.SX,
                                                   epsilon_friction: ca.SX, work_weight: ca.SX,
                                                   pressure_weight: ca.SX, valve_weight: ca.SX,
                                                   combustion_weight: ca.SX) -> ca.SX:
        """
        Add thermodynamic objectives using parameterized smoothing.
        
        Args:
            x: Displacement variables
            v: Velocity variables  
            a: Acceleration variables
            grid: Grid points
            epsilon_valve: Valve smoothing parameter
            epsilon_friction: Friction smoothing parameter
            work_weight: Work objective weight
            pressure_weight: Pressure smoothness weight
            valve_weight: Valve constraint weight
            combustion_weight: Combustion efficiency weight
            
        Returns:
            Thermodynamic objective terms
        """
        # Calculate volume: V(t) = V_c + A_p x(t)
        volume = self.thermo_calc.calculate_volume_casadi(x)
        
        # Calculate pressure using log-domain evaluation
        pressure = self.thermo_calc.calculate_pressure_polytropic_casadi(volume)
        
        # Calculate indicated work: W_id = ∮ p dV
        indicated_work = self.thermo_calc.calculate_indicated_work_casadi(pressure, volume)
        
        # Thermodynamic objectives
        thermo_objectives = ca.SX(0.0)
        
        # 1. Maximize indicated work (negative penalty) - always include
        thermo_objectives = thermo_objectives - work_weight * indicated_work
        
        # 2. Pressure smoothness penalty - always include
        pressure_smoothness = ca.sum1((pressure[1:] - pressure[:-1])**2)
        thermo_objectives = thermo_objectives + pressure_weight * pressure_smoothness
        
        # 3. Valve constraint compliance (using parameterized smoothing) - always include
        # This would use epsilon_valve for smooth valve modeling
        valve_penalty = 0.0  # Placeholder - would use epsilon_valve
        thermo_objectives = thermo_objectives + valve_weight * valve_penalty
        
        # 4. Combustion efficiency - always include
        # Calculate heat release using parameterized models
        theta_deg = np.degrees(grid)
        heat_release = self.combustion_model.calculate_combustion_heat_release(theta_deg)
        total_heat_release = ca.sum1(ca.DM(heat_release))
        thermo_objectives = thermo_objectives - combustion_weight * total_heat_release
        
        # 5. Optional volume barrier for early robustness
        # Use CasADi conditional to handle the barrier
        V_min = 1.01 * self.params.clearance_volume_m3
        volume_barrier = self.thermo_calc.add_volume_barrier(volume, V_min, mu=1e-4)
        # Always include the barrier (the weight controls its effect)
        thermo_objectives = thermo_objectives + volume_barrier
        
        return thermo_objectives
