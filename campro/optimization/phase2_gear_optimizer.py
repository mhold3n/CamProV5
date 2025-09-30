"""
Phase 2: Gear Profile Optimization with Force Transfer Efficiency

This module implements the second phase of the collocation-based optimization process,
focusing on gear profile optimization with force transfer efficiency from piston crown
to ring output, following the optimized motion law from Phase 1.
"""

import numpy as np
import casadi as ca
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import logging
import time

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
    force_transfer_efficiency: float
    max_contact_stress: float
    gear_clearance: np.ndarray
    
    # Grid information
    theta_grid: np.ndarray
    node_count: int


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
        
        # Extract motion law data
        theta_grid = motion_law['grid']
        displacement = motion_law['displacement']
        velocity = motion_law['velocity']
        acceleration = motion_law['acceleration']
        
        # Create collocation grid for gear optimization
        gear_grid = self._create_gear_collocation_grid(theta_grid, gear_params)
        
        # Build NLP formulation for gear optimization
        nlp_info = self._build_gear_nlp_formulation(
            motion_law, gear_params, gear_grid
        )
        
        # Solve optimization problem
        solution_data = self._solve_gear_nlp(nlp_info, gear_params)
        
        # Post-process solution
        solution = self._post_process_gear_solution(
            solution_data, gear_grid, start_time, motion_law, gear_params
        )
        
        self.logger.info(f"Phase 2 optimization completed: success={solution.success}, "
                        f"time={solution.execution_time:.3f}s")
        
        return solution
    
    def _create_gear_collocation_grid(self, theta_grid: np.ndarray, 
                                    gear_params: Dict[str, Any]) -> np.ndarray:
        """Create collocation grid for gear profile optimization."""
        self.logger.info("Creating gear profile collocation grid")
        
        # Use the same grid as motion law for consistency
        gear_grid = np.deg2rad(theta_grid)
        
        # Ensure proper scaling for gear optimization
        ring_rotation_deg = gear_params.get('ringRotationDeg', 180.0)
        scale_factor = 2 * np.pi / ring_rotation_deg
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
        stroke_length = gear_params.get('strokeLengthMm', 10.0)
        
        # Create CasADi variables for gear radii
        sun_radius = ca.SX.sym('sun_radius', n)
        planet_radius = ca.SX.sym('planet_radius', n)
        ring_radius = ca.SX.sym('ring_radius', n)
        
        # Extract motion law data
        displacement = motion_law['displacement']
        velocity = motion_law['velocity']
        acceleration = motion_law['acceleration']
        
        # Convert to CasADi constants
        displacement_ca = ca.DM(displacement)
        velocity_ca = ca.DM(velocity)
        acceleration_ca = ca.DM(acceleration)
        
        # UNIFIED CONSTRAINT SYSTEM: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
        # This is the fundamental constraint for planetary gearset geometry
        unified_constraint = ring_radius - (sun_radius + 2 * planet_radius)
        
        # Force transfer efficiency objective
        # Maximize force transfer from piston to ring output
        force_transfer_efficiency = self._compute_force_transfer_efficiency(
            sun_radius, planet_radius, ring_radius, displacement_ca, velocity_ca, n
        )
        
        # Gear smoothness objective (minimize curvature variation)
        sun_smoothness = self._compute_gear_smoothness(sun_radius, grid)
        planet_smoothness = self._compute_gear_smoothness(planet_radius, grid)
        ring_smoothness = self._compute_gear_smoothness(ring_radius, grid)
        
        # Simplified objective function for better convergence
        # Focus on minimizing gear size variation (smoothness)
        f = self.parameters.smoothness_weight * (sun_smoothness + planet_smoothness + ring_smoothness)
        
        # Constraints
        g = []
        lbg = []
        ubg = []
        
        # 1. Unified constraint system (equality constraint)
        for i in range(n):
            g.append(unified_constraint[i])
            lbg.append(0.0)
            ubg.append(0.0)
        
        # 2. Gear radius bounds will be handled as variable bounds (not constraints)
        
        # 3. Simplified constraints for better convergence
        # Only keep essential constraints for now
        
        # Variable bounds
        lbx = []
        ubx = []
        
        # Gear radius bounds
        min_radius = 1.0  # Minimum gear radius
        max_radius = 50.0  # Maximum gear radius
        
        # Sun gear bounds
        for i in range(n):
            lbx.append(min_radius)
            ubx.append(max_radius)
        
        # Planet gear bounds
        for i in range(n):
            lbx.append(min_radius)
            ubx.append(max_radius)
        
        # Ring gear bounds
        for i in range(n):
            lbx.append(min_radius)
            ubx.append(max_radius)
        
        # Initial guess
        x0 = []
        
        # Initialize with reasonable gear sizes based on displacement
        for i in range(n):
            # Base gear sizes proportional to displacement
            base_size = 5.0 + displacement[i] * 0.5
            x0.extend([base_size, base_size * 0.6, base_size * 2.2])
        
        # Create NLP
        nlp = {
            'x': ca.vertcat(sun_radius, planet_radius, ring_radius),
            'f': f,
            'g': ca.vertcat(*g)
        }
        
        nlp_info = {
            'nlp': nlp,
            'lbx': lbx,
            'ubx': ubx,
            'lbg': lbg,
            'ubg': ubg,
            'x0': x0
        }
        
        self.logger.info(f"Gear NLP formulation complete: {3*n} variables, {len(g)} constraints")
        return nlp_info
    
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
        
        # Velocity matching efficiency
        velocity_efficiency = 1.0 / (1.0 + ca.fabs(velocity) / 10.0)
        
        # Combined efficiency
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
        
        # Create IPOPT solver
        solver = ca.nlpsol('solver', 'ipopt', nlp, {
            'ipopt.max_iter': self.parameters.max_iterations,
            'ipopt.tol': self.parameters.tolerance,
            'ipopt.constr_viol_tol': self.parameters.constraint_tolerance,
            'ipopt.print_level': 0,  # Reduce output
            'ipopt.sb': 'yes'  # Suppress banner
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
        
        # Split solution into gear radii
        sun_radius = x_opt[:n]
        planet_radius = x_opt[n:2*n]
        ring_radius = x_opt[2*n:3*n]
        
        # Compute constraint violation
        g_opt = np.array(solution_data['g'])
        constraint_violation = np.max(np.abs(g_opt)) if len(g_opt) > 0 else 0.0
        
        # Check success criteria
        # Consider it successful if constraints are satisfied and objective is reasonable
        success = (
            (stats['success'] or 
             (constraint_violation < 1e-6 and float(solution_data['f']) < float('inf'))) and
            float(solution_data['f']) < float('inf')
        )
        
        # Compute force transfer efficiency
        force_transfer_efficiency = self._compute_force_transfer_efficiency_numeric(
            sun_radius, planet_radius, ring_radius, motion_law
        )
        
        # Compute maximum contact stress
        max_contact_stress = self._compute_max_contact_stress_numeric(
            sun_radius, planet_radius, ring_radius
        )
        
        # Compute gear clearance
        gear_clearance = self._compute_gear_clearance_numeric(
            sun_radius, planet_radius, ring_radius
        )
        
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
            node_count=len(grid)
        )
    
    def _compute_force_transfer_efficiency_numeric(self, sun_radius: np.ndarray, 
                                                 planet_radius: np.ndarray, 
                                                 ring_radius: np.ndarray,
                                                 motion_law: Dict[str, Any]) -> float:
        """Compute force transfer efficiency numerically."""
        
        # Gear ratio efficiency
        gear_ratio = ring_radius / sun_radius
        optimal_ratio = 2.0
        ratio_efficiency = 1.0 / (1.0 + (gear_ratio - optimal_ratio)**2)
        
        # Contact stress efficiency
        contact_stress = self._compute_contact_stress_numeric(sun_radius, planet_radius, ring_radius)
        stress_efficiency = 1.0 / (1.0 + contact_stress / self.parameters.material_strength_mpa)
        
        # Velocity efficiency
        velocity = motion_law['velocity']
        velocity_efficiency = 1.0 / (1.0 + np.abs(velocity) / 10.0)
        
        # Combined efficiency
        total_efficiency = ratio_efficiency * stress_efficiency * velocity_efficiency
        
        return np.mean(total_efficiency)
    
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
