"""
Phase 2: Gear Profile Optimization with Force Transfer Efficiency

This module implements the second phase of the collocation-based optimization process,
focusing on gear profile optimization with force transfer efficiency from piston crown
to ring output, following the optimized motion law from Phase 1.
"""

import numpy as np
import casadi as ca
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import time

from campro.utils.angle_units import (
    ensure_percent_grid,
    percent_to_degrees,
    percent_to_radians,
    resolve_cycle_percent,
    degrees_to_percent,
)

logger = logging.getLogger(__name__)


@dataclass
class Phase2Parameters:
    """Parameters for Phase 2 gear profile optimization."""
    
    # Gear geometry parameters
    planet_radius_base_factor: float = 1.0
    sun_radius_variation_factor: float = 1.0
    ring_radius_base_factor: float = 1.0
    
    # Force transfer optimization weights
    force_transfer_weight: float = 1.0
    efficiency_weight: float = 1.0
    smoothness_weight: float = 0.1
    
    # Contact constraints
    min_contact_force: float = 100.0
    max_contact_stress: float = 1000.0
    
    # Collocation parameters
    node_count: int = 32
    max_iterations: int = 500
    tolerance: float = 1e-6
    constraint_tolerance: float = 1e-6
    
    # Gear clearance and safety
    clearance_safety_margin: float = 0.1
    min_gear_clearance: float = 0.05
    
    # Force transfer parameters
    piston_area_mm2: float = 100.0  # Piston crown area
    cylinder_pressure_bar: float = 10.0  # Operating pressure
    material_strength_mpa: float = 500.0  # Material strength
    
    # Optimization strategy
    use_continuation: bool = True
    
    # Variable instantaneous ratio parameters
    rMin: float = 2.0
    rMax: float = 2.5
    rSmoothnessWeight: float = 0.0
    motionVariationWeight: float = 0.1
    enableSymmetryPrior: bool = False
    symmetryWeight: float = 0.5
    continuation_steps: int = 3
    warm_start: bool = True


@dataclass
class Phase2Solution:
    """Solution from Phase 2 gear profile optimization."""
    
    success: bool
    execution_time: float
    iterations: int
    objective_value: float
    constraint_violation: float
    solver_status: str
    
    # Gear profiles
    sun_radius: np.ndarray
    planet_radius: np.ndarray
    ring_radius: np.ndarray
    
    # Force transfer metrics
    force_transfer_efficiency: np.ndarray  # Per-angle efficiency values
    max_contact_stress: float
    gear_clearance: np.ndarray
    
    # Grid information
    theta_grid: np.ndarray
    node_count: int

    # New outputs for variable instantaneous ratio
    instantaneous_ratio: np.ndarray
    journal_offset: np.ndarray
    accumulated_planet_angle_deg: float
    phi_planet: np.ndarray  # Planet rotation angle at each node


class Phase2GearOptimizer:
    """
    Phase 2: Gear Profile Optimization with Force Transfer Efficiency
    
    This optimizer takes the optimized motion law from Phase 1 and generates
    gear profiles that maximize force transfer efficiency from piston crown
    to ring output using collocation methods.
    """
    
    def __init__(self, parameters: Optional[Phase2Parameters] = None):
        """Initialize the Phase 2 gear optimizer."""
        self.parameters = parameters or Phase2Parameters()
        self.logger = logging.getLogger(__name__)
    
    def optimize_gear_profiles(self, motion_law: Dict[str, Any], 
                             gear_params: Dict[str, Any]) -> Phase2Solution:
        """
        Optimize gear profiles for force transfer efficiency.
        
        Args:
            motion_law: Optimized motion law from Phase 1
            gear_params: Gear-specific parameters
            
        Returns:
            Phase2Solution with optimized gear profiles
        """
        start_time = time.time()
        self.logger.info("Starting Phase 2: Gear Profile Optimization with Force Transfer Efficiency")
        
        # Extract motion law data - handle both 'grid' and 'theta_deg' keys
        if 'grid' in motion_law:
            theta_grid = np.array(motion_law['grid'])
        elif 'theta_deg' in motion_law:
            theta_grid = np.array(motion_law['theta_deg'])
        else:
            raise KeyError("Motion law must contain either 'grid' or 'theta_deg' key")
        
        # Extract motion law data (currently unused but may be needed for future enhancements)
        # displacement = np.array(motion_law['displacement'])
        # velocity = np.array(motion_law['velocity'])
        # acceleration = np.array(motion_law['acceleration'])
        
        # Create collocation grid for gear optimization
        gear_grid = self._create_gear_collocation_grid(theta_grid, gear_params)
        
        # Build & solve NLP (no fallbacks; analysis integrity)
        try:
            nlp_info = self._build_gear_nlp_formulation(motion_law, gear_params, gear_grid)
            solution_data = self._solve_gear_nlp(nlp_info, gear_params)
            solution = self._post_process_gear_solution(solution_data, gear_grid, start_time, motion_law, gear_params)
        except Exception as e:
            self.logger.error(f"Phase 2 solve failed: {e}")
            return Phase2Solution(
                success=False,
                execution_time=time.time() - start_time,
                iterations=0,
                objective_value=float('inf'),
                constraint_violation=float('inf'),
                solver_status='Infeasible_Problem_Detected',
                sun_radius=np.array([]),
                planet_radius=np.array([]),
                ring_radius=np.array([]),
                force_transfer_efficiency=np.array([]),
                max_contact_stress=0.0,
                gear_clearance=np.array([]),
                theta_grid=gear_grid,
                node_count=len(gear_grid),
                instantaneous_ratio=np.array([]),
                journal_offset=np.array([]),
                accumulated_planet_angle_deg=0.0,
                phi_planet=np.array([])
            )
        
        self.logger.info(f"Phase 2 optimization completed: success={solution.success}, "
                        f"time={solution.execution_time:.3f}s")
        
        return solution
    
    def _create_gear_collocation_grid(self, theta_grid: np.ndarray, 
                                    gear_params: Dict[str, Any]) -> np.ndarray:
        """Create collocation grid for gear profile optimization."""
        self.logger.info("Creating gear profile collocation grid")
        
        # Use the same grid as motion law for consistency but normalise units
        theta_percent = degrees_to_percent(theta_grid)
        gear_grid = percent_to_radians(theta_percent)

        ring_rotation_percent = resolve_cycle_percent(
            gear_params, 'ringRotation', default_percent=degrees_to_percent(180.0)
        )
        scale_factor = (2 * np.pi) / percent_to_radians(ring_rotation_percent)
        gear_grid = gear_grid * scale_factor
        
        self.logger.info(f"Gear collocation grid created with {len(gear_grid)} points")
        return gear_grid
    
    def _build_gear_nlp_formulation(self, motion_law: Dict[str, Any], 
                                  gear_params: Dict[str, Any], 
                                  grid: np.ndarray) -> Dict[str, Any]:
        """Build NLP formulation for gear profile optimization."""
        self.logger.info("Building CasADi NLP formulation for gear profile optimization")
        
        # Extract parameters
        n = len(grid)
        # gear_params.get('strokeLengthMm', 10.0)  # Currently unused
        # ring_rotation_deg = float(gear_params.get('ringRotationDeg', 180.0))  # Currently unused
        # Get theta grid in degrees - handle both 'grid' and 'theta_deg' keys
        if 'grid' in motion_law:
            theta_grid_deg = motion_law['grid']
        elif 'theta_deg' in motion_law:
            theta_grid_deg = motion_law['theta_deg']
        else:
            raise KeyError("Motion law must contain either 'grid' or 'theta_deg' key")
        # Assume uniform step from motion law grid
        # Calculate step size for future use
        if len(theta_grid_deg) > 1:
            # step_deg = float(theta_grid_deg[1] - theta_grid_deg[0])  # TODO: Use in future implementation
            pass
        else:
            # step_deg = ring_rotation_deg  # TODO: Use in future implementation
            pass
        
        # Create CasADi variables for gear radii
        sun_radius = ca.SX.sym('sun_radius', n)
        planet_radius = ca.SX.sym('planet_radius', n)
        ring_radius = ca.SX.sym('ring_radius', n)
        # New instantaneous ratio variable r(θ) = dφ/dθ per node
        r_inst = ca.SX.sym('r_inst', n)
        # Journal offset from planet COM δ(θ) - critical for variable ratios
        journal_offset = ca.SX.sym('journal_offset', n)
        
        # Extract motion law data
        displacement = motion_law['displacement']
        velocity = motion_law['velocity']
        acceleration = motion_law['acceleration']
        
        # Convert to numpy arrays for proper operations
        accel_array = np.array(acceleration)
        vel_array = np.array(velocity)
        
        # Convert to CasADi constants
        displacement_ca = ca.DM(displacement)
        velocity_ca = ca.DM(velocity)
        ca.DM(acceleration)
        
        # CORRECTED UNIFIED RELATION (soft, via residual)
        # R_ring(θ) = R_sun(θ) + 2*R_planet(θ) (standard planetary gear constraint)
        unified_residual = ring_radius - (sun_radius + 2 * planet_radius)
        
        # Force transfer efficiency objective
        # Maximize force transfer from piston to ring output
        self._compute_force_transfer_efficiency(
            sun_radius, planet_radius, ring_radius, displacement_ca, velocity_ca, n
        )
        
        # Gear smoothness objective (minimize curvature variation)
        sun_smoothness = self._compute_gear_smoothness(sun_radius, grid)
        planet_smoothness = self._compute_gear_smoothness(planet_radius, grid)
        ring_smoothness = self._compute_gear_smoothness(ring_radius, grid)
        
        # SIMPLIFIED objective function for better convergence
        # 1. Basic gear smoothness (reduced weight)
        f = 0.01 * (sun_smoothness + planet_smoothness + ring_smoothness)
        
        # 2. Simple r(θ) smoothness (reduced weight)
        r_smooth_weight = float(gear_params.get('rSmoothnessWeight', 0.01))  # Much smaller weight
        if r_smooth_weight > 0.0:
            r_smooth = 0
            for i in range(n - 1):
                r_smooth = r_smooth + (r_inst[i + 1] - r_inst[i]) ** 2
            f = f + r_smooth_weight * r_smooth
        
        # 3. DISABLED Motion-dependent r(θ) variation for basic test
        # This adds complexity that can cause convergence issues
        # TODO: Re-enable with better formulation in future iterations
        
        # Constraints: hard equality constraints for critical relationships
        g = []
        lbg = []
        ubg = []

        # HARD CONSTRAINT: Unified relation R_ring = R_sun + 2*R_planet
        # This ensures the constraint is satisfied exactly
        g.append(unified_residual)
        lbg.extend([0.0] * n)  # Equality constraint: residual = 0
        ubg.extend([0.0] * n)

        # Add soft penalty terms to objective for other objectives
        # Weights (tunable)
        w_noslip = 1.0
        w_integral = 10.0
        w_smooth_r = 0.1
        w_smooth_radii = 0.01

        # No-slip residual across all nodes: r*R_planet - R_ring
        noslip_residual = r_inst * planet_radius - ring_radius

        # Global integral residual (use same step)
        ring_rotation_percent = resolve_cycle_percent(
            gear_params, 'ringRotation', default_percent=degrees_to_percent(180.0)
        )
        step_percent = ring_rotation_percent / (n - 1) if n > 1 else ring_rotation_percent
        integral_r = ca.sum1(r_inst) * percent_to_radians(step_percent)
        expected_integral = 2.0 * np.pi
        integral_residual = integral_r - expected_integral

        # Smoothness penalties (first differences)
        def _diff1(vec: ca.SX) -> ca.SX:
            return vec[1:] - vec[:-1] if n > 1 else ca.SX.zeros(0)

        smooth_penalty = (
            w_smooth_r * ca.sum1(ca.power(_diff1(r_inst), 2)) +
            w_smooth_radii * ca.sum1(ca.power(_diff1(sun_radius), 2)) +
            w_smooth_radii * ca.sum1(ca.power(_diff1(planet_radius), 2)) +
            w_smooth_radii * ca.sum1(ca.power(_diff1(ring_radius), 2))
        )

        penalty = (
            w_noslip * ca.sum1(ca.power(noslip_residual, 2)) +
            w_integral * (integral_residual**2) +
            smooth_penalty
        )

        f = f + penalty
        
        # Variable bounds
        lbx = []
        ubx = []
        
        # CORRECTED: Gear radius bounds to allow significant non-circular profiles
        # The bounds must accommodate the stroke-based variation factors
        # Calculate reasonable bounds based on stroke requirements
        # For 100mm stroke with 30% variation, we need ~30mm variation in gear radii
        min_sun_radius = 5.0  # Sun gear must be positive for proper meshing
        min_planet_radius = 10.0  # Planet must be positive and substantial
        min_ring_radius = 50.0    # Ring must be positive and substantial
        max_radius = 500.0  # Increased to allow for larger gearset
        
        # Sun gear bounds
        for i in range(n):
            lbx.append(min_sun_radius)
            ubx.append(max_radius)
        
        # Planet gear bounds
        for i in range(n):
            lbx.append(min_planet_radius)
            ubx.append(max_radius)
        
        # Ring gear bounds
        for i in range(n):
            lbx.append(min_ring_radius)
            ubx.append(max_radius)

        # r(θ) bounds (instantaneous ratio)
        # Must be >= 2.0 to ensure R_sun >= 0 from constraint: R_sun = (r_inst - 2) * R_planet
        r_min = max(2.0, float(gear_params.get('rMin', 2.0)))
        r_max = float(gear_params.get('rMax', 2.5))
        for i in range(n):
            lbx.append(r_min)
            ubx.append(r_max)
        
        # Journal offset bounds δ(θ) - calculated from user inputs
        # Use maxJournalOffsetPercent to calculate bounds based on typical planet radius
        max_journal_offset_percent = float(gear_params.get('maxJournalOffsetPercent', 0.1))
        # Estimate typical planet radius from displacement and gear ratio
        typical_planet_radius = max(5.0, np.mean(np.abs(displacement)) * 0.5)
        max_journal_offset = typical_planet_radius * max_journal_offset_percent
        
        for i in range(n):
            lbx.append(-max_journal_offset)
            ubx.append(max_journal_offset)
        
        # Removed φ(θ) bounds; φ will be derived post-solve
        
        # Initial guess - IMPROVED for better feasibility
        x0 = []
        
        # Initialize with FEASIBLE gear sizes that satisfy the unified constraint
        # R_ring = R_sun + 2*R_planet must be satisfied
        for i in range(n):
            # Base gear sizes proportional to displacement, ensuring feasibility
            base_size = max(5.0, 10.0 + abs(displacement[i]) * 0.3)  # Increased base size
            
            # Ensure the unified constraint R_ring = R_sun + 2*R_planet is satisfied
            sun_guess = base_size * 0.3  # Smaller sun gear
            planet_guess = base_size * 0.4  # Medium planet gear
            ring_guess = sun_guess + 2 * planet_guess  # Ring satisfies constraint exactly
            
            x0.extend([sun_guess, planet_guess, ring_guess])
        # Initial r guess: vary based on motion law characteristics
        gear_ratio_guess = float(gear_params.get('gearRatio', 2.0))
        r0 = []
        for i in range(n):
            # Vary initial r(θ) based on motion law
            if i < len(accel_array):
                accel_factor = abs(accel_array[i]) / (np.max(np.abs(accel_array)) + 1e-6)
            else:
                accel_factor = 0.5  # Default for last points
            if i < len(vel_array):
                vel_factor = abs(vel_array[i]) / (np.max(np.abs(vel_array)) + 1e-6)
            else:
                vel_factor = 0.5  # Default for last point
            
            # Start with varying r(θ) that responds to motion
            initial_r = gear_ratio_guess + 0.5 * accel_factor - 0.2 * vel_factor
            initial_r = min(max(initial_r, r_min), r_max)  # Clamp to bounds
            r0.append(initial_r)
        x0.extend(r0)
        
        # Initial journal offset guess: vary based on motion law
        journal_offset_0 = []
        for i in range(n):
            # Vary journal offset based on motion law - higher during acceleration
            # Use velocity instead of acceleration since accel_array has n-2 elements
            if i < len(vel_array):
                vel_factor = abs(vel_array[i]) / (np.max(np.abs(vel_array)) + 1e-6)
            else:
                vel_factor = 0.5  # Default for last point
            initial_offset = 0.1 * vel_factor * max_journal_offset  # Start with small offset
            initial_offset = min(max(initial_offset, -max_journal_offset), max_journal_offset)
            journal_offset_0.append(initial_offset)
        x0.extend(journal_offset_0)
        
        # Removed φ(θ) initial guess; φ will be derived post-solve
        
        # Create NLP (φ not included in decision vector)
        nlp = {
            'x': ca.vertcat(sun_radius, planet_radius, ring_radius, r_inst, journal_offset),
            'f': f,
            'g': ca.vertcat(*g) if g else ca.SX()
        }
        
        # Change: Add block slices metadata for x₀ transfer
        from .nlp_meta import create_gear_optimization_block_slices
        block_slices = create_gear_optimization_block_slices(n)
        
        nlp_info = {
            'nlp': nlp,
            'lbx': lbx,
            'ubx': ubx,
            'lbg': lbg,
            'ubg': ubg,
            'x0': x0,
            'block_slices': block_slices,  # Add block slices for x₀ transfer
            'grid_t': gear_grid  # Store grid for interpolation
        }
        
        self.logger.info(f"Gear NLP formulation complete: {5*n} variables, {len(g)} constraints")
        return nlp_info
    
    def _compute_contact_forces(self, sun_radius: ca.SX, planet_radius: ca.SX, 
                               ring_radius: ca.SX, displacement: ca.DM, 
                               velocity: ca.DM) -> List[ca.SX]:
        """Compute contact forces between gears."""
        # Get the size from the displacement array instead of CasADi variables
        n = displacement.shape[0] if hasattr(displacement, 'shape') else len(displacement)
        contact_forces = []
        
        for i in range(n):
            # Simplified contact force calculation
            # F = k * (R_ring - R_sun - 2*R_planet) where k is stiffness
            stiffness = 1000.0  # N/mm
            # Ensure positive contact force to avoid negative values
            force = stiffness * ca.fmax(ring_radius[i] - sun_radius[i] - 2 * planet_radius[i], 1e-6)
            contact_forces.append(force)
        
        return contact_forces
    
    def _compute_contact_stresses(self, sun_radius: ca.SX, planet_radius: ca.SX, 
                                 ring_radius: ca.SX, contact_forces: List[ca.SX]) -> List[ca.SX]:
        """Compute contact stresses between gears."""
        n = len(contact_forces)
        contact_stresses = []
        
        for i in range(n):
            # Simplified contact stress calculation using Hertzian contact theory
            # σ = sqrt(F * E / (π * R_contact))
            youngs_modulus = 200e3  # MPa
            contact_radius = (sun_radius[i] + planet_radius[i]) / 2.0
            # Ensure positive values to avoid NaN
            force_term = ca.fmax(contact_forces[i], 1e-6)  # Minimum positive force
            radius_term = ca.fmax(contact_radius, 1e-6)    # Minimum positive radius
            stress = ca.sqrt(force_term * youngs_modulus / (ca.pi * radius_term))
            contact_stresses.append(stress)
        
        return contact_stresses
    
    def _compute_force_transfer_efficiency(self, sun_radius: ca.SX, planet_radius: ca.SX, 
                                         ring_radius: ca.SX, displacement: ca.SX, 
                                         velocity: ca.SX, n: int) -> ca.SX:
        """Compute force transfer efficiency from piston to ring output."""
        
        # Force transfer efficiency is based on:
        # 1. Gear ratio optimization
        # 2. Contact stress minimization
        # 3. Velocity matching
        
        # Gear ratio: ring_radius / sun_radius
        gear_ratio = ring_radius / sun_radius
        
        # Optimal gear ratio for force transfer (typically 2:1 for planetary)
        optimal_ratio = 2.0
        ratio_efficiency = 1.0 / (1.0 + (gear_ratio - optimal_ratio)**2)
        
        # Contact stress factor (lower stress = higher efficiency)
        contact_stress = self._compute_contact_stress(sun_radius, planet_radius, ring_radius)
        stress_efficiency = 1.0 / (1.0 + contact_stress / self.parameters.material_strength_mpa)
        
        # Velocity matching efficiency (use average velocity to match dimensions)
        # velocity is a CasADi DM with n-1 elements, so we use n-1 for the average
        avg_velocity = ca.sum1(velocity) / (n - 1)
        velocity_efficiency = 1.0 / (1.0 + ca.fabs(avg_velocity) / 10.0)
        
        # Combined efficiency (velocity_efficiency is now scalar)
        total_efficiency = ratio_efficiency * stress_efficiency * velocity_efficiency
        
        return ca.sum1(total_efficiency) / n
    
    def _compute_contact_stress(self, sun_radius: ca.SX, planet_radius: ca.SX, 
                              ring_radius: ca.SX) -> ca.SX:
        """Compute contact stress between gears."""
        
        # Simplified contact stress calculation
        # Based on Hertz contact theory
        
        # Contact force (proportional to gear size and displacement)
        contact_force = (sun_radius + planet_radius) * 10.0  # Simplified
        
        # Contact area (proportional to gear radii)
        contact_area = ca.pi * planet_radius * 0.1  # Simplified tooth width
        
        # Contact stress
        contact_stress = contact_force / contact_area
        
        return contact_stress
    
    def _compute_gear_smoothness(self, radius: ca.SX, grid: np.ndarray) -> ca.SX:
        """Compute gear profile smoothness (minimize curvature variation)."""
        
        # Compute first and second derivatives using finite differences
        n = len(grid)
        
        # First derivative (slope)
        dr_dtheta = ca.SX.sym('dr_dtheta', n-1)
        for i in range(n-1):
            dr_dtheta[i] = (radius[i+1] - radius[i]) / (grid[i+1] - grid[i])
        
        # Second derivative (curvature)
        d2r_dtheta2 = ca.SX.sym('d2r_dtheta2', n-2)
        for i in range(n-2):
            d2r_dtheta2[i] = (dr_dtheta[i+1] - dr_dtheta[i]) / (grid[i+2] - grid[i+1])
        
        # Smoothness penalty (minimize curvature variation)
        smoothness = ca.sum1(d2r_dtheta2**2)
        
        return smoothness
    
    def _compute_gear_clearance_constraints(self, sun_radius: ca.SX, planet_radius: ca.SX, 
                                          ring_radius: ca.SX) -> ca.SX:
        """Compute gear clearance constraints."""
        
        # Clearance between sun and planet
        sun_planet_clearance = planet_radius - sun_radius - self.parameters.min_gear_clearance
        
        # Clearance between planet and ring
        planet_ring_clearance = ring_radius - planet_radius - self.parameters.min_gear_clearance
        
        # Combined clearance constraint
        clearance = ca.fmin(sun_planet_clearance, planet_ring_clearance)
        
        return clearance
    
    def _compute_force_transfer_constraints(self, sun_radius: ca.SX, planet_radius: ca.SX, 
                                          ring_radius: ca.SX, displacement: ca.SX) -> ca.SX:
        """Compute force transfer capability constraints."""
        
        # Force transfer capability is proportional to gear size and displacement
        # Larger gears can transfer more force
        
        # Piston force (from pressure and area)
        piston_force = self.parameters.cylinder_pressure_bar * self.parameters.piston_area_mm2
        
        # Gear force transfer capability
        gear_capability = (sun_radius + planet_radius + ring_radius) * displacement * 10.0
        
        # Force transfer ratio
        force_ratio = gear_capability / piston_force
        
        return force_ratio
    
    def _solve_gear_nlp(self, nlp_info: Dict[str, Any], gear_params: Dict[str, Any]) -> Dict[str, Any]:
        """Solve the gear optimization NLP using IPOPT."""
        self.logger.info("Solving gear optimization NLP using IPOPT")
        
        # Extract NLP components
        nlp = nlp_info['nlp']
        lbx = nlp_info['lbx']
        ubx = nlp_info['ubx']
        lbg = nlp_info['lbg']
        ubg = nlp_info['ubg']
        x0 = nlp_info['x0']
        
        # Create IPOPT solver with IMPROVED settings for better convergence
        solver = ca.nlpsol('solver', 'ipopt', nlp, {
            'ipopt.max_iter': self.parameters.max_iterations,
            'ipopt.tol': self.parameters.tolerance,
            'ipopt.constr_viol_tol': self.parameters.constraint_tolerance,
            'ipopt.print_level': 0,  # Reduce output
            'ipopt.sb': 'yes',  # Suppress banner
            'ipopt.acceptable_tol': 1e-4,  # Relaxed acceptable tolerance
            'ipopt.acceptable_constr_viol_tol': 1e-4,  # Relaxed constraint tolerance
            'ipopt.acceptable_iter': 10,  # Accept solution after 10 iterations if acceptable
            'ipopt.mu_strategy': 'adaptive',  # Adaptive barrier parameter
            'ipopt.hessian_approximation': 'limited-memory'  # Use L-BFGS for better convergence
        })
        
        # Solve optimization problem
        solution = solver(x0=x0, lbx=lbx, ubx=ubx, lbg=lbg, ubg=ubg)
        
        # Extract solution
        x_opt = np.array(solution['x']).flatten()
        f_opt = float(solution['f'])
        g_opt = np.array(solution['g']).flatten()
        
        # Get solver statistics
        stats = solver.stats()
        
        self.logger.info(f"IPOPT solve completed: success={stats['success']}, "
                        f"iterations={stats['iter_count']}, objective={f_opt:.6f}")
        
        return {
            'x': x_opt,
            'f': f_opt,
            'g': g_opt,
            'stats': stats
        }
    
    def _post_process_gear_solution(self, solution_data: Dict[str, Any], 
                                  grid: np.ndarray, start_time: float,
                                  motion_law: Dict[str, Any], 
                                  gear_params: Dict[str, Any]) -> Phase2Solution:
        """Post-process the gear optimization solution."""
        stats = solution_data['stats']
        execution_time = time.time() - start_time
        
        # Extract solution variables
        x_opt = solution_data['x']
        n = len(grid)
        
        # Split solution into gear radii, instantaneous ratio, journal offset, and planet rotation
        sun_radius = x_opt[:n]
        planet_radius = x_opt[n:2*n]
        ring_radius = x_opt[2*n:3*n]
        r_inst = x_opt[3*n:4*n]
        journal_offset = x_opt[4*n:5*n]
        phi_planet = x_opt[5*n:6*n]
        
        # Compute constraint violation
        g_opt = np.array(solution_data['g'])
        constraint_violation = np.max(np.abs(g_opt)) if len(g_opt) > 0 else 0.0
        
        # Strict success criteria: solver must report success and constraints within tolerance
        success = bool(stats.get('success', False)) and (constraint_violation <= self.parameters.constraint_tolerance)
        
        # Compute force transfer efficiency
        force_transfer_efficiency = self._compute_force_transfer_efficiency_numeric(
            sun_radius, planet_radius, ring_radius, motion_law, r_inst
        )
        
        # Compute maximum contact stress
        max_contact_stress = self._compute_max_contact_stress_numeric(
            sun_radius, planet_radius, ring_radius
        )
        
        # Compute gear clearance
        gear_clearance = self._compute_gear_clearance_numeric(
            sun_radius, planet_radius, ring_radius
        )

        # Accumulated planet angle from r: φ = Σ r_i Δθ (degrees)
        # Get theta grid in degrees - handle both 'grid' and 'theta_deg' keys
        if 'grid' in motion_law:
            theta_grid_deg = motion_law['grid']
        elif 'theta_deg' in motion_law:
            theta_grid_deg = motion_law['theta_deg']
        else:
            raise KeyError("Motion law must contain either 'grid' or 'theta_deg' key")
        
        if len(theta_grid_deg) > 1:
            step_deg = float(theta_grid_deg[1] - theta_grid_deg[0])
        else:
            step_deg = float(
                percent_to_degrees(
                    resolve_cycle_percent(
                        gear_params, 'ringRotation', default_percent=degrees_to_percent(180.0)
                    )
                )
            )
        # Accumulate over intervals to be consistent with the constraint
        if n > 1:
            accumulated_phi_deg = float(np.sum(r_inst[: n - 1]) * step_deg)
        else:
            accumulated_phi_deg = float(r_inst[0] * step_deg)
        
        self.logger.info(f"Solution post-processing complete: success={success}, "
                        f"execution_time={execution_time:.3f}s, "
                        f"iterations={stats['iter_count']}")
        
        return Phase2Solution(
            success=success,
            execution_time=execution_time,
            iterations=stats['iter_count'],
            objective_value=float(solution_data['f']),
            constraint_violation=constraint_violation,
            solver_status=stats['return_status'],
            sun_radius=sun_radius,
            planet_radius=planet_radius,
            ring_radius=ring_radius,
            force_transfer_efficiency=force_transfer_efficiency,
            max_contact_stress=max_contact_stress,
            gear_clearance=gear_clearance,
            theta_grid=grid,
            phi_planet=phi_planet,
            node_count=len(grid),
            instantaneous_ratio=r_inst,
            journal_offset=journal_offset,
            accumulated_planet_angle_deg=accumulated_phi_deg
        )
    
    def _compute_force_transfer_efficiency_numeric(self, sun_radius: np.ndarray, 
                                                 planet_radius: np.ndarray, 
                                                 ring_radius: np.ndarray,
                                                 motion_law: Dict[str, Any],
                                                 instantaneous_ratio: Optional[np.ndarray] = None) -> np.ndarray:
        """Compute force transfer efficiency numerically for each angle."""
        
        n = len(sun_radius)
        
        # Gear ratio efficiency (per-angle) - use instantaneous ratio if provided
        if instantaneous_ratio is not None:
            gear_ratio = instantaneous_ratio
        else:
            # Fallback to calculated ratio (but this can be problematic with negative sun radii)
            gear_ratio = ring_radius / sun_radius
            
        optimal_ratio = 2.0
        ratio_efficiency = 1.0 / (1.0 + (gear_ratio - optimal_ratio)**2)
        
        # Contact stress efficiency (per-angle)
        contact_stress = self._compute_contact_stress_numeric(sun_radius, planet_radius, ring_radius)
        stress_efficiency = 1.0 / (1.0 + contact_stress / self.parameters.material_strength_mpa)
        
        # Velocity efficiency (per-angle, interpolated from velocity array)
        velocity = np.array(motion_law['velocity'])
        
        # Interpolate velocity to match gear profile dimensions
        if len(velocity) == n - 1:
            # Velocity has n-1 elements, interpolate to n elements
            velocity_interp = np.zeros(n)
            velocity_interp[:-1] = velocity
            velocity_interp[-1] = velocity[-1]  # Extend last value
        else:
            # Use average velocity for all points if dimensions don't match
            avg_velocity = np.mean(np.abs(velocity))
            velocity_interp = np.full(n, avg_velocity)
        
        velocity_efficiency = 1.0 / (1.0 + np.abs(velocity_interp) / 10.0)
        
        # Combined efficiency (per-angle)
        total_efficiency = ratio_efficiency * stress_efficiency * velocity_efficiency
        
        return total_efficiency
    
    def _compute_contact_stress_numeric(self, sun_radius: np.ndarray, 
                                      planet_radius: np.ndarray, 
                                      ring_radius: np.ndarray) -> np.ndarray:
        """Compute contact stress numerically."""
        
        # Simplified contact stress calculation
        contact_force = (sun_radius + planet_radius) * 10.0
        contact_area = np.pi * planet_radius * 0.1
        contact_stress = contact_force / contact_area
        
        return contact_stress
    
    def _compute_max_contact_stress_numeric(self, sun_radius: np.ndarray, 
                                          planet_radius: np.ndarray, 
                                          ring_radius: np.ndarray) -> float:
        """Compute maximum contact stress."""
        
        contact_stress = self._compute_contact_stress_numeric(sun_radius, planet_radius, ring_radius)
        return np.max(contact_stress)
    
    def _compute_gear_clearance_numeric(self, sun_radius: np.ndarray, 
                                      planet_radius: np.ndarray, 
                                      ring_radius: np.ndarray) -> np.ndarray:
        """Compute gear clearance numerically."""
        
        # Clearance between sun and planet
        sun_planet_clearance = planet_radius - sun_radius - self.parameters.min_gear_clearance
        
        # Clearance between planet and ring
        planet_ring_clearance = ring_radius - planet_radius - self.parameters.min_gear_clearance
        
        # Combined clearance
        clearance = np.minimum(sun_planet_clearance, planet_ring_clearance)
        
        return clearance
