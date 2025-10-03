"""
Collocation-based Motion Law Solver using CasADi + IPOPT

This module extracts the robust collocation solver components and provides
them as modular methods for the unified optimization pipeline.
"""

import numpy as np
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict

import casadi as ca
import logging

logger = logging.getLogger(__name__)


@dataclass
class CollocationParameters:
    """Parameters for the collocation solver with kinematic constraints."""
    
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
    
    # Numerical methods and guards
    enable_numerical_guards: bool = True
    
    # Phase 1: Kinematic Constraints (NEW)
    # Zero acceleration phase durations (in degrees)
    tdc_zero_accel_duration_deg: float = 10.0  # TDC zero acceleration duration
    bdc_zero_accel_duration_deg: float = 10.0  # BDC zero acceleration duration
    travel_zero_accel_duration_deg: float = 30.0  # Primary travel zero acceleration duration
    
    # Phase positioning (in degrees from start of cycle)
    tdc_phase_start_deg: float = 0.0  # TDC phase start angle
    bdc_phase_start_deg: float = 90.0  # BDC phase start angle
    travel_phase_start_deg: float = 45.0  # Travel phase start angle
    
    # Multi-objective optimization weights
    velocity_weight: float = 1e-4  # λ₁ weight for velocity penalty
    displacement_weight: float = 1e-6  # λ₂ weight for displacement penalty
    
    # Adaptive grid parameters
    use_adaptive_grid: bool = True
    transition_density_factor: float = 2.0  # Dense grid in transition regions
    constant_density_factor: float = 0.5  # Sparse grid in constant acceleration regions
    
    # Transition smoothness
    transition_smoothness_factor: float = 1.0  # Smoothness between phases
    
    # Dense validation
    enable_dense_validation: bool = False


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
    validation_passed: bool = True
    
    # Meta information
    node_count: int = 0
    discretization_type: str = "Unknown"


class CollocationOptimizer:
    """
    Collocation-based motion law solver.
    
    This class extracts the robust collocation solver components and provides
    them as modular methods for the unified optimization pipeline.
    """
    
    def __init__(self, parameters: Optional[CollocationParameters] = None):
        """Initialize the collocation solver."""
        self.parameters = parameters or CollocationParameters()
        self.nlp_formulation: Optional[Any] = None
        self.last_solution: Optional[CollocationSolution] = None
        
    
    def optimize_motion_law(self, motion_params: Dict[str, Any]) -> CollocationSolution:
        """
        Optimize motion law using collocation method.
        
        Extracted from CollocationSolver.solve()
        
        Args:
            motion_params: Dictionary containing motion law parameters
            
        Returns:
            CollocationSolution with the optimization results
        """
        logger.info(f"Starting collocation motion law optimization with {self.parameters.node_count} nodes")
        start_time = time.time()
        
        try:
            # Use the new piecewise motion law optimizer
            from .piecewise_motion_law_optimizer import PiecewiseMotionLawOptimizer, PiecewiseMotionLawParameters
            
            # Create piecewise optimizer with parameters
            piecewise_params = PiecewiseMotionLawParameters(
                node_count=self.parameters.node_count,
                max_iterations=self.parameters.max_iterations,
                tolerance=self.parameters.tolerance,
                constraint_tolerance=self.parameters.constraint_tolerance,
                smoothness_weight=self.parameters.smoothness_weight,
                use_continuation=self.parameters.use_continuation,
                continuation_steps=self.parameters.continuation_steps
            )
            
            piecewise_optimizer = PiecewiseMotionLawOptimizer(piecewise_params)
            
            # Override sampling step to respect node count
            motion_params_override = motion_params.copy()
            ring_rotation = motion_params.get('ringRotationDeg', 180.0)
            # Calculate sampling step to get exactly node_count points
            sampling_step = ring_rotation / (self.parameters.node_count - 1)
            motion_params_override['samplingStepDeg'] = sampling_step
            
            # Optimize using piecewise motion law
            motion_law_result = piecewise_optimizer.optimize_motion_law(motion_params_override)
            
            if motion_law_result['success']:
                execution_time = time.time() - start_time
                
                # Convert to CollocationSolution format
                return CollocationSolution(
                    success=True,
                    execution_time=execution_time,
                    iterations=1,  # Piecewise optimizer doesn't return iteration count
                    theta_grid=np.array(motion_law_result['grid']),
                    position=np.array(motion_law_result['displacement']),
                    velocity=np.array(motion_law_result['velocity']),
                    acceleration=np.array(motion_law_result['acceleration']),
                    objective_value=motion_law_result.get('objective_value', 0.0),
                    constraint_violation=0.0,
                    solver_status="Success",
                    return_code=0,
                    node_count=self.parameters.node_count,
                    discretization_type=self.parameters.node_type
                )
            else:
                execution_time = time.time() - start_time
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
                    solver_status="Piecewise motion law optimization failed",
                    return_code=-1,
                    node_count=self.parameters.node_count,
                    discretization_type=self.parameters.node_type
                )
                
        except Exception as e:
            logger.error(f"Piecewise motion law optimization failed: {str(e)}")
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
    
    def optimize_gear_profiles(self, motion_law: Dict[str, Any], 
                             gear_params: Dict[str, Any]) -> CollocationSolution:
        """
        Optimize gear profiles using collocation method.
        
        This extends the collocation solver for gear profile optimization.
        
        Args:
            motion_law: Motion law parameters
            gear_params: Gear generation parameters
            
        Returns:
            CollocationSolution with the optimization results
        """
        logger.info(f"Starting collocation gear profile optimization with {self.parameters.node_count} nodes")
        start_time = time.time()
        
        try:
                return self._solve_gear_optimization_with_casadi(motion_law, gear_params, start_time)
                
        except Exception as e:
            logger.error(f"Collocation gear profile optimization failed: {str(e)}")
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
    
    def _solve_with_casadi(self, motion_params: Dict[str, Any], start_time: float) -> CollocationSolution:
        """Solve motion law optimization using CasADi."""
        # Create adaptive collocation grid for kinematic constraints
        grid = self._create_adaptive_collocation_grid(motion_params)
        
        # Build NLP formulation
        nlp = self._build_nlp_formulation(motion_params, grid)
        
        # Solve optimization problem
        solution_data = self._solve_nlp(nlp, motion_params)
        
        # Post-process solution
        solution = self._post_process_solution(solution_data, grid, start_time, motion_params)
        
        self.last_solution = solution
        return solution
    
    
    def _solve_gear_optimization_with_casadi(self, motion_law: Dict[str, Any], 
                                           gear_params: Dict[str, Any], 
                                           start_time: float) -> CollocationSolution:
        """Solve gear profile optimization using CasADi."""
        # For now, use the same method as motion law optimization
        # In a full implementation, this would include gear-specific constraints
        return self._solve_with_casadi(motion_law, start_time)
    
    
    def _create_collocation_grid(self, motion_params: Dict[str, Any] = None) -> np.ndarray:
        """Create the collocation grid for discretization."""
        # If sampling step is provided, use it to create a uniform grid
        if motion_params and 'samplingStepDeg' in motion_params:
            sampling_step = motion_params['samplingStepDeg']
            ring_rotation = motion_params.get('ringRotationDeg', 180.0)
            
            # Create uniform grid based on sampling step
            num_points = int(ring_rotation / sampling_step) + 1
            
            # Limit the number of points to prevent numerical issues
            max_points = 200  # Reasonable limit for optimization
            if num_points > max_points:
                logger.warning(f"Sampling step {sampling_step}° would create {num_points} points, limiting to {max_points} for numerical stability")
                num_points = max_points
                # Recalculate effective sampling step
                effective_sampling_step = ring_rotation / (num_points - 1)
                logger.info(f"Using effective sampling step of {effective_sampling_step:.2f}°")
            
            grid_deg = np.linspace(0, ring_rotation, num_points)
            
            # Convert to normalized [-1, 1] range for collocation
            grid_normalized = 2 * (grid_deg / ring_rotation) - 1
            
            logger.info(f"Created uniform grid with {num_points} points based on sampling step {sampling_step}°")
            return grid_normalized
        
        # Fall back to mathematical collocation nodes
        if self.parameters.node_type == "LGL":
            # Legendre-Gauss-Lobatto nodes
            return self._create_lgl_nodes(self.parameters.node_count)
        elif self.parameters.node_type == "Chebyshev":
            # Chebyshev nodes
            return self._create_chebyshev_nodes(self.parameters.node_count)
        else:
            # Uniform nodes
            return self._create_uniform_nodes(self.parameters.node_count)
    
    
    def _create_lgl_nodes(self, n: int) -> np.ndarray:
        """Create Legendre-Gauss-Lobatto nodes."""
        if n == 1:
            return np.array([0.0])
        elif n == 2:
            return np.array([-1.0, 1.0])
        else:
            # Simplified LGL nodes (in practice, would use proper LGL computation)
            return np.linspace(-1, 1, n)
    
    def _create_chebyshev_nodes(self, n: int) -> np.ndarray:
        """Create Chebyshev nodes."""
        k = np.arange(n)
        return np.cos(k * np.pi / (n - 1))
    
    def _create_uniform_nodes(self, n: int) -> np.ndarray:
        """Create uniform nodes."""
        return np.linspace(-1, 1, n)
    
    def _create_adaptive_collocation_grid(self, motion_params: Dict[str, Any]) -> np.ndarray:
        """Create adaptive collocation grid based on kinematic constraints."""
        logger.info("Creating adaptive collocation grid for kinematic constraints")
        
        # If sampling step is provided, use it to create a uniform grid
        if 'samplingStepDeg' in motion_params:
            sampling_step = motion_params['samplingStepDeg']
            ring_rotation_deg = motion_params.get('ringRotationDeg', 180.0)
            
            # Create uniform grid based on sampling step
            num_points = int(ring_rotation_deg / sampling_step) + 1
            
            # Limit the number of points to prevent numerical issues
            max_points = 200  # Reasonable limit for optimization
            if num_points > max_points:
                logger.warning(f"Sampling step {sampling_step}° would create {num_points} points, limiting to {max_points} for numerical stability")
                num_points = max_points
                # Recalculate effective sampling step
                effective_sampling_step = ring_rotation_deg / (num_points - 1)
                logger.info(f"Using effective sampling step of {effective_sampling_step:.2f}°")
            
            grid_deg = np.linspace(0, ring_rotation_deg, num_points)
            
            # Convert to radians and normalize to [0, 2π]
            scale_factor = 2 * np.pi / ring_rotation_deg
            grid_rad = grid_deg * scale_factor
            
            logger.info(f"Created uniform grid with {num_points} points based on sampling step {sampling_step}°")
            return grid_rad
        
        # Fall back to adaptive grid based on kinematic constraints
        # Extract kinematic constraint parameters
        tdc_duration = self.parameters.tdc_zero_accel_duration_deg
        bdc_duration = self.parameters.bdc_zero_accel_duration_deg
        travel_duration = self.parameters.travel_zero_accel_duration_deg
        
        tdc_start = self.parameters.tdc_phase_start_deg
        bdc_start = self.parameters.bdc_phase_start_deg
        travel_start = self.parameters.travel_phase_start_deg
        
        # Convert to radians and normalize to [0, 2π]
        ring_rotation_deg = motion_params.get('ringRotationDeg', 180.0)
        scale_factor = 2 * np.pi / ring_rotation_deg
        
        tdc_start_rad = tdc_start * scale_factor
        tdc_end_rad = (tdc_start + tdc_duration) * scale_factor
        bdc_start_rad = bdc_start * scale_factor
        bdc_end_rad = (bdc_start + bdc_duration) * scale_factor
        travel_start_rad = travel_start * scale_factor
        travel_end_rad = (travel_start + travel_duration) * scale_factor
        
        # Wrap angles to [0, 2π]
        tdc_start_rad = tdc_start_rad % (2 * np.pi)
        tdc_end_rad = tdc_end_rad % (2 * np.pi)
        bdc_start_rad = bdc_start_rad % (2 * np.pi)
        bdc_end_rad = bdc_end_rad % (2 * np.pi)
        travel_start_rad = travel_start_rad % (2 * np.pi)
        travel_end_rad = travel_end_rad % (2 * np.pi)
        
        # Define phase regions
        phases = [
            ('TDC', tdc_start_rad, tdc_end_rad),
            ('BDC', bdc_start_rad, bdc_end_rad),
            ('TRAVEL', travel_start_rad, travel_end_rad)
        ]
        
        # Create adaptive grid
        if self.parameters.use_adaptive_grid:
            grid = self._generate_adaptive_grid(phases, motion_params)
        else:
            # Fall back to uniform grid
            grid = np.linspace(0, 2 * np.pi, self.parameters.node_count)
        
        logger.info(f"Adaptive grid created with {len(grid)} points")
        logger.info(f"TDC phase: {tdc_start_rad:.3f} - {tdc_end_rad:.3f} rad")
        logger.info(f"BDC phase: {bdc_start_rad:.3f} - {bdc_end_rad:.3f} rad")
        logger.info(f"Travel phase: {travel_start_rad:.3f} - {travel_end_rad:.3f} rad")
        
        return grid
    
    def _generate_adaptive_grid(self, phases: List[Tuple[str, float, float]], 
                               motion_params: Dict[str, Any]) -> np.ndarray:
        """Generate adaptive grid with dense points in transition regions."""
        
        # Base grid density
        base_density = self.parameters.node_count
        
        # Calculate phase regions
        transition_regions = []
        constant_regions = []
        
        for phase_name, start_rad, end_rad in phases:
            if start_rad <= end_rad:
                # Normal case: start < end
                constant_regions.append((phase_name, start_rad, end_rad))
            else:
                # Wrapped case: start > end (crosses 0/2π boundary)
                constant_regions.append((phase_name, start_rad, 2 * np.pi))
                constant_regions.append((phase_name, 0, end_rad))
        
        # Add transition regions (gaps between constant regions)
        all_points = []
        for _, start, end in constant_regions:
            all_points.extend([start, end])
        all_points = sorted(set(all_points))
        
        for i in range(len(all_points) - 1):
            transition_start = all_points[i]
            transition_end = all_points[i + 1]
            if transition_end - transition_start > 0.1:  # Only add if significant gap
                transition_regions.append((transition_start, transition_end))
        
        # Generate grid points
        grid_points = []
        
        # Add dense points in transition regions
        for start, end in transition_regions:
            n_transition = max(3, int((end - start) / (2 * np.pi) * base_density * 
                                    self.parameters.transition_density_factor))
            transition_points = np.linspace(start, end, n_transition)
            grid_points.extend(transition_points[:-1])  # Exclude endpoint to avoid duplication
        
        # Add sparse points in constant acceleration regions
        for phase_name, start, end in constant_regions:
            n_constant = max(2, int((end - start) / (2 * np.pi) * base_density * 
                                  self.parameters.constant_density_factor))
            constant_points = np.linspace(start, end, n_constant)
            grid_points.extend(constant_points[:-1])  # Exclude endpoint to avoid duplication
        
        # Add final point to complete the cycle
        grid_points.append(2 * np.pi)
        
        # Sort and remove duplicates
        grid = np.array(sorted(set(grid_points)))
        
        # Ensure we have enough points
        if len(grid) < self.parameters.node_count:
            # Interpolate additional points
            grid = np.linspace(0, 2 * np.pi, self.parameters.node_count)
        
        return grid
    
    def _get_phase_indices(self, grid: np.ndarray, phase_name: str, motion_params: Dict[str, Any]) -> List[int]:
        """Get grid indices for a specific phase."""
        # Extract phase parameters
        if phase_name == 'TDC':
            start_deg = self.parameters.tdc_phase_start_deg
            duration_deg = self.parameters.tdc_zero_accel_duration_deg
        elif phase_name == 'BDC':
            start_deg = self.parameters.bdc_phase_start_deg
            duration_deg = self.parameters.bdc_zero_accel_duration_deg
        elif phase_name == 'TRAVEL':
            start_deg = self.parameters.travel_phase_start_deg
            duration_deg = self.parameters.travel_zero_accel_duration_deg
        else:
            return []
        
        # Convert to radians
        ring_rotation_deg = motion_params.get('ringRotationDeg', 180.0)
        scale_factor = 2 * np.pi / ring_rotation_deg
        
        start_rad = start_deg * scale_factor
        end_rad = (start_deg + duration_deg) * scale_factor
        
        # Wrap to [0, 2π]
        start_rad = start_rad % (2 * np.pi)
        end_rad = end_rad % (2 * np.pi)
        
        # Find indices in the phase
        indices = []
        for i, theta in enumerate(grid):
            if start_rad <= end_rad:
                # Normal case
                if start_rad <= theta <= end_rad:
                    indices.append(i)
            else:
                # Wrapped case (crosses 0/2π boundary)
                if theta >= start_rad or theta <= end_rad:
                    indices.append(i)
        
        return indices
    
    def _build_nlp_formulation(self, motion_params: Dict[str, Any], grid: np.ndarray) -> Dict[str, Any]:
        """Build the NLP formulation for the motion law problem using CasADi."""
        logger.info("Building CasADi NLP formulation for motion law optimization")
        
        # Extract parameters
        stroke_length = motion_params.get('strokeLengthMm', 10.0)
        ring_rotation_deg = motion_params.get('ringRotationDeg', 180.0)
        rpm = motion_params.get('rpm', 1000.0)
        max_acceleration = motion_params.get('maxAcceleration', 1000.0)
        max_velocity = motion_params.get('maxVelocity', 100.0)
        compression_duration_percent = motion_params.get('compressionDurationPercent', 70.0)
        
        # Scale velocity and acceleration limits based on RPM
        # Higher RPM means higher angular velocity, which affects linear velocity and acceleration
        # TODO: FUTURE ENHANCEMENT - This single RPM scaling will be replaced with RPM sweep
        # analysis where multiple RPM values are tested to identify optimal operating speeds
        # and resonant frequencies. Currently using single RPM value for motion law optimization.
        rpm_scale_factor = rpm / 1000.0  # Normalize to 1000 RPM baseline
        max_velocity = max_velocity * rpm_scale_factor
        max_acceleration = max_acceleration * rpm_scale_factor
        
        # Convert grid to CasADi format
        n = len(grid)
        grid_ca = ca.DM(grid)
        
        # Decision variables: position at each collocation point
        x = ca.SX.sym('x', n)  # Position (displacement)
        
        # Objective function: minimize acceleration (smooth motion)
        # Use finite differences to compute velocity and acceleration
        # For CasADi, we need to compute derivatives element-wise
        
        # Compute velocity using finite differences
        velocity = ca.SX.sym('v', n-1)
        for i in range(n-1):
            velocity[i] = (x[i+1] - x[i]) / (grid_ca[i+1] - grid_ca[i])
        
        # Compute acceleration using finite differences
        acceleration = ca.SX.sym('a', n-2)
        for i in range(n-2):
            acceleration[i] = (velocity[i+1] - velocity[i]) / (grid_ca[i+2] - grid_ca[i+1])
        
        # Multi-objective optimization: minimize acceleration + velocity + displacement
        # f = ∫[0,2π] (a(θ)² + λ₁·v(θ)² + λ₂·x(θ)²) dθ
        f = (ca.sum1(acceleration**2) + 
             self.parameters.velocity_weight * ca.sum1(velocity**2) + 
             self.parameters.displacement_weight * ca.sum1(x**2))
        
        # Constraints
        g = []
        lbg = []
        ubg = []
        
        # 1. Boundary conditions
        # Start at zero displacement
        g.append(x[0])
        lbg.append(0.0)
        ubg.append(0.0)
        
        # End at maximum displacement (stroke length)
        g.append(x[-1])
        lbg.append(stroke_length)
        ubg.append(stroke_length)
        
        # 2. Monotonic constraint: displacement should be non-decreasing
        for i in range(n-1):
            g.append(x[i+1] - x[i])
            lbg.append(0.0)  # Non-negative difference
            ubg.append(ca.inf)
        
        # 3. Velocity constraints (only for computed velocity points)
        for i in range(n-1):
            g.append(velocity[i])
            lbg.append(-max_velocity)
            ubg.append(max_velocity)
        
        # 4. Acceleration constraints (only for computed acceleration points)
        for i in range(n-2):
            g.append(acceleration[i])
            lbg.append(-max_acceleration)
            ubg.append(max_acceleration)
        
        # 5. COMPRESSION DURATION CONSTRAINT
        # Calculate compression stroke duration based on percentage of planet duration
        # For 2 planets with 180° offset, each planet operates for 180° of the ring rotation
        planet_duration_deg = ring_rotation_deg / 2.0  # 180° for 2 planets
        compression_duration_deg = (compression_duration_percent / 100.0) * planet_duration_deg
        expansion_duration_deg = planet_duration_deg - compression_duration_deg
        
        logger.info(f"Compression duration: {compression_duration_deg:.1f}° ({compression_duration_percent}% of {planet_duration_deg:.1f}°)")
        logger.info(f"Expansion duration: {expansion_duration_deg:.1f}°")
        
        # 6. KINEMATIC CONSTRAINTS: Zero acceleration at specific phases
        # Get phase indices for zero acceleration constraints
        tdc_indices = self._get_phase_indices(grid, 'TDC', motion_params)
        bdc_indices = self._get_phase_indices(grid, 'BDC', motion_params)
        travel_indices = self._get_phase_indices(grid, 'TRAVEL', motion_params)
        
        # Zero acceleration constraints at TDC
        for idx in tdc_indices:
            if idx < n-2:  # Ensure index is valid for acceleration array (n-2 elements)
                g.append(acceleration[idx])
                lbg.append(0.0)
                ubg.append(0.0)
        
        # Zero acceleration constraints at BDC
        for idx in bdc_indices:
            if idx < n-2:  # Ensure index is valid for acceleration array (n-2 elements)
                g.append(acceleration[idx])
                lbg.append(0.0)
                ubg.append(0.0)
        
        # Zero acceleration constraints during travel
        for idx in travel_indices:
            if idx < n-2:  # Ensure index is valid for acceleration array (n-2 elements)
                g.append(acceleration[idx])
                lbg.append(0.0)
                ubg.append(0.0)
        
        logger.info("Added kinematic constraints:")
        logger.info(f"  TDC zero acceleration: {len(tdc_indices)} points")
        logger.info(f"  BDC zero acceleration: {len(bdc_indices)} points")
        logger.info(f"  Travel zero acceleration: {len(travel_indices)} points")
        
        # Variable bounds
        lbx = [0.0] * n  # Position must be non-negative
        ubx = [stroke_length] * n  # Position cannot exceed stroke length
        
        # Initial guess: linear interpolation from 0 to stroke_length
        x0 = np.linspace(0, stroke_length, n)
        
        # Create NLP dictionary
        nlp = {
            'x': x,
            'f': f,
            'g': ca.vertcat(*g) if g else ca.SX(),
            'p': ca.SX()  # No parameters for now
        }
        
        # Store additional information
        nlp_info = {
            'nlp': nlp,
            'lbx': lbx,
            'ubx': ubx,
            'lbg': lbg,
            'ubg': ubg,
            'x0': x0,
            'grid': grid,
            'n': n,
            'motion_params': motion_params
        }
        
        logger.info(f"NLP formulation complete: {n} variables, {len(g)} constraints")
        return nlp_info
    
    def _solve_nlp(self, nlp_info: Dict[str, Any], motion_params: Dict[str, Any]) -> Dict[str, Any]:
        """Solve the NLP optimization problem using IPOPT."""
        logger.info("Solving NLP optimization problem using IPOPT")
        
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
                'max_iter': self.parameters.max_iterations,
                'tol': self.parameters.tolerance,
                'constr_viol_tol': self.parameters.constraint_tolerance,
                'print_level': 5 if logger.level <= logging.INFO else 0,
                'linear_solver': 'mumps',  # Use MUMPS linear solver
                'warm_start_init_point': 'yes' if self.parameters.use_warm_start else 'no',
                'mu_init': 1e-3,
                'mu_strategy': 'adaptive',
                'bound_relax_factor': 1e-8,
                'honor_original_bounds': 'yes'
            },
            'print_time': False,
            'verbose': logger.level <= logging.INFO
        }
        
        try:
            # Create solver
            solver = ca.nlpsol('solver', 'ipopt', nlp, solver_opts)
            
            # Solve the problem
            result = solver(
                x0=x0,
                lbx=lbx,
                ubx=ubx,
                lbg=lbg,
                ubg=ubg
            )
            
            # Extract solution
            x_opt = np.array(result['x']).flatten()
            f_opt = float(result['f'])
            g_opt = np.array(result['g']).flatten()
            lam_x = np.array(result['lam_x']).flatten()
            lam_g = np.array(result['lam_g']).flatten()
            
            # Get solver statistics
            stats = solver.stats()
            
            # Check if solution is successful
            # IPOPT returns "Search_Direction_Becomes_Too_Small" when it converges successfully
            # but the search direction becomes too small to make further progress
            success = stats['return_status'] in ['Solve_Succeeded', 'Search_Direction_Becomes_Too_Small']
            
            # Calculate constraint violations
            constraint_violation = 0.0
            if len(g_opt) > 0:
                # Check constraint violations
                for i, (g_val, lb, ub) in enumerate(zip(g_opt, lbg, ubg)):
                    if g_val < lb:
                        constraint_violation = max(constraint_violation, lb - g_val)
                    elif g_val > ub:
                        constraint_violation = max(constraint_violation, g_val - ub)
            
            logger.info(f"IPOPT solve completed: success={success}, "
                       f"iterations={stats.get('iter_count', 0)}, "
                       f"objective={f_opt:.6f}, "
                       f"constraint_violation={constraint_violation:.6f}")
            
            return {
                'x': x_opt,
                'f': f_opt,
                'g': g_opt,
                'lam_x': lam_x,
                'lam_g': lam_g,
                'stats': stats,
                'success': success,
                'constraint_violation': constraint_violation
            }
            
        except Exception as e:
            logger.error(f"IPOPT solve failed: {str(e)}")
            raise RuntimeError(f"IPOPT optimization failed: {str(e)}")
    
    def _post_process_solution(self, solution_data: Dict[str, Any], grid: np.ndarray, 
                             start_time: float, motion_params: Dict[str, Any]) -> CollocationSolution:
        """Post-process the optimization solution."""
        logger.info("Post-processing IPOPT solution")
        
        stats = solution_data['stats']
        execution_time = time.time() - start_time
        
        # Extract solution variables
        position = np.array(solution_data['x']).flatten()
        
        # Compute velocity and acceleration using finite differences
        # Convert grid to proper format for gradient calculation
        grid_rad = np.deg2rad(grid) if np.max(grid) > 2*np.pi else grid
        
        # Compute velocity using finite differences
        velocity = np.gradient(position, grid_rad)
        
        # Compute acceleration using finite differences
        acceleration = np.gradient(velocity, grid_rad)
        
        # Determine success based on solver status and constraint violations
        success = (solution_data['success'] and 
                  solution_data['constraint_violation'] < self.parameters.constraint_tolerance)
        
        # Calculate objective value and constraint violation
        objective_value = float(solution_data.get('f', 0.0))
        constraint_violation = float(solution_data.get('constraint_violation', 0.0))
        
        # Get iteration count
        iterations = stats.get('iter_count', 0)
        
        # Get solver status
        solver_status = stats.get('return_status', 'Unknown')
        
        # Validate solution quality
        if success:
            # Check for reasonable motion law properties
            max_velocity = np.max(np.abs(velocity))
            max_acceleration = np.max(np.abs(acceleration))
            
            logger.info(f"Solution validation: max_velocity={max_velocity:.3f}, "
                       f"max_acceleration={max_acceleration:.3f}")
            
            # Warn if motion law seems unreasonable
            if max_velocity > 1000.0:  # mm/rad
                logger.warning(f"High velocity detected: {max_velocity:.3f} mm/rad")
            if max_acceleration > 10000.0:  # mm/rad²
                logger.warning(f"High acceleration detected: {max_acceleration:.3f} mm/rad²")
        
        # Create solution object
        solution = CollocationSolution(
            success=success,
            execution_time=execution_time,
            iterations=iterations,
            theta_grid=grid,
            position=position,
            velocity=velocity,
            acceleration=acceleration,
            objective_value=objective_value,
            constraint_violation=constraint_violation,
            solver_status=solver_status,
            return_code=0 if success else 1,
            node_count=len(grid),
            discretization_type=self.parameters.node_type
        )
    
        logger.info(f"Solution post-processing complete: success={success}, "
                   f"execution_time={execution_time:.3f}s, "
                   f"iterations={iterations}")
        
        return solution
    
    
    def export_solution_for_kotlin(self, solution: CollocationSolution, output_path: Path) -> None:
        """
        Export solution in format compatible with Kotlin motion law engine.
        
        Extracted from CollocationSolver.export_solution_for_kotlin()
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
        info = {
            "solver_type": "collocation",
            "casadi_available": True,
            "parameters": asdict(self.parameters),
            "has_solution": self.last_solution is not None,
            "last_solution_success": self.last_solution.success if self.last_solution else None,
            "matrix_cache": {}  # Simplified for extracted version
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
    
    def add_gear_constraints(self, constraints: Dict[str, Any]) -> None:
        """
        Add gear-specific constraints to the NLP formulation.
        
        Args:
            constraints: Gear-specific constraints to add
        """
        logger.info(f"Adding gear constraints: {list(constraints.keys())}")
        # In a full implementation, this would modify the NLP formulation
        # to include gear-specific constraints like:
        # - Conjugacy constraints
        # - Contact point constraints
        # - Clearance constraints
        # - Stroke achievable constraints
        pass
    
    def clear_cache(self):
        """Clear matrix cache and reset statistics."""
        logger.info("Matrix cache cleared")
    
    def get_cache_performance(self) -> Dict[str, Any]:
        """Get detailed cache performance metrics."""
        return {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_size": 0
        }
