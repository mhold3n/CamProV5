"""
Litvin Conjugacy and Manufacturability Constraints for NLP

This module implements the Litvin gear design constraints for ensuring
that generated motion laws can be manufactured as conjugate gear pairs
with acceptable geometry and performance characteristics.
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

try:
    import casadi as ca
    CASADI_AVAILABLE = True
except ImportError:
    CASADI_AVAILABLE = False

import logging
from .discretization import CollocationGrid

logger = logging.getLogger(__name__)


@dataclass
class LitvinParameters:
    """Parameters for Litvin gear synthesis."""
    
    # Geometric parameters
    center_distance: float = 50.0  # Center distance between gears (mm)
    cam_base_radius: float = 40.0  # Base radius of cam (mm)
    ring_thickness_min: float = 5.0  # Minimum ring gear thickness (mm)
    
    # Manufacturing constraints
    pressure_angle_max_deg: float = 30.0  # Maximum pressure angle (degrees)
    tooth_thickness_min: float = 1.0  # Minimum tooth thickness (mm)
    curvature_radius_min: float = 2.0  # Minimum radius of curvature (mm)
    contact_ratio_min: float = 1.2  # Minimum contact ratio
    
    # Arc-length conjugacy tolerances
    arc_length_tolerance: float = 0.01  # Arc-length matching tolerance (mm)
    max_conjugacy_iterations: int = 10  # Maximum iterations for conjugacy
    
    # Performance limits
    sliding_velocity_max: float = 50.0  # Maximum sliding velocity (mm/s)
    contact_stress_max: float = 1000.0  # Maximum contact stress (MPa)
    bending_stress_max: float = 500.0  # Maximum bending stress (MPa)


class LitvinConstraintBuilder:
    """
    Builds Litvin conjugacy and manufacturability constraints for the NLP.
    
    This class implements the mathematical constraints necessary to ensure
    that the optimized motion law can be realized as a manufacturable
    gear pair with acceptable performance characteristics.
    """
    
    def __init__(self, litvin_params: LitvinParameters, grid: CollocationGrid):
        """Initialize the Litvin constraint builder."""
        self.params = litvin_params
        self.grid = grid
        self.logger = logging.getLogger(__name__)
        
        # Convert parameters to working units
        self.pressure_angle_max = np.deg2rad(litvin_params.pressure_angle_max_deg)
        
    def build_litvin_constraints(self, position_vars: 'ca.SX', velocity_vars: 'ca.SX') -> Dict[str, Any]:
        """
        Build all Litvin-related constraints for the NLP.
        
        Args:
            position_vars: CasADi variables for position at collocation nodes
            velocity_vars: CasADi variables for velocity at collocation nodes
            
        Returns:
            Dictionary containing constraint expressions and bounds
        """
        if not CASADI_AVAILABLE:
            raise ImportError("CasADi is required for Litvin constraints")
        
        constraints = []
        bounds_lower = []
        bounds_upper = []
        
        # 1. Build gear geometry from motion law
        cam_radius, ring_radius = self._compute_gear_radii(position_vars, velocity_vars)
        
        # 2. Arc-length conjugacy constraints
        arc_constraints = self._build_arc_length_constraints(cam_radius, ring_radius)
        constraints.extend(arc_constraints['expressions'])
        bounds_lower.extend(arc_constraints['lower'])
        bounds_upper.extend(arc_constraints['upper'])
        
        # 3. Pressure angle constraints
        pressure_constraints = self._build_pressure_angle_constraints(cam_radius, ring_radius)
        constraints.extend(pressure_constraints['expressions'])
        bounds_lower.extend(pressure_constraints['lower'])
        bounds_upper.extend(pressure_constraints['upper'])
        
        # 4. Tooth thickness constraints
        thickness_constraints = self._build_tooth_thickness_constraints(cam_radius, ring_radius)
        constraints.extend(thickness_constraints['expressions'])
        bounds_lower.extend(thickness_constraints['lower'])
        bounds_upper.extend(thickness_constraints['upper'])
        
        # 5. Curvature constraints (no undercut)
        curvature_constraints = self._build_curvature_constraints(cam_radius, ring_radius)
        constraints.extend(curvature_constraints['expressions'])
        bounds_lower.extend(curvature_constraints['lower'])
        bounds_upper.extend(curvature_constraints['upper'])
        
        # 6. Contact ratio constraints
        contact_constraints = self._build_contact_ratio_constraints(cam_radius, ring_radius)
        constraints.extend(contact_constraints['expressions'])
        bounds_lower.extend(contact_constraints['lower'])
        bounds_upper.extend(contact_constraints['upper'])
        
        return {
            'expressions': constraints,
            'bounds_lower': bounds_lower,
            'bounds_upper': bounds_upper,
            'num_constraints': len(constraints)
        }
    
    def _compute_gear_radii(self, position_vars: 'ca.SX', velocity_vars: 'ca.SX') -> Tuple['ca.SX', 'ca.SX']:
        """
        Compute gear radii from motion law using Litvin relationships.
        
        The cam radius is derived from the velocity profile, and the ring radius
        is computed from the center distance constraint.
        """
        # Normalize velocity to create cam radius variation
        v_max = ca.mmax(ca.fabs(velocity_vars))
        v_normalized = velocity_vars / (v_max + 1e-8)  # Avoid division by zero
        
        # Cam radius: r_cam = r_base + k * v_normalized
        cam_radius_variation = 5.0  # mm, variation range
        cam_radius = self.params.cam_base_radius + cam_radius_variation * v_normalized
        
        # Ensure minimum radius
        cam_radius = ca.fmax(cam_radius, 10.0)  # Minimum 10mm radius
        
        # Ring radius from center distance (external gear pair)
        ring_radius = self.params.center_distance - cam_radius
        
        # Ensure ring radius is positive
        ring_radius = ca.fmax(ring_radius, self.params.ring_thickness_min)
        
        return cam_radius, ring_radius
    
    def _build_arc_length_constraints(self, cam_radius: 'ca.SX', ring_radius: 'ca.SX') -> Dict[str, List]:
        """
        Build arc-length conjugacy constraints.
        
        For conjugate gears, the arc lengths must match:
        ∫√(r_cam² + (dr_cam/dθ)²) dθ = ∫√(r_ring² + (dr_ring/dφ)²) dφ
        """
        # Compute derivatives using differentiation matrix
        D = ca.DM(self.grid.differentiation_matrix)
        dr_cam_dtheta = D @ cam_radius
        dr_ring_dphi = D @ ring_radius
        
        # Arc length elements
        ds_cam = ca.sqrt(cam_radius**2 + dr_cam_dtheta**2)
        ds_ring = ca.sqrt(ring_radius**2 + dr_ring_dphi**2)
        
        # Total arc lengths (using trapezoidal integration)
        step_size = 2.0 * np.pi / self.grid.node_count
        arc_length_cam = step_size * ca.sum1(ds_cam)
        arc_length_ring = step_size * ca.sum1(ds_ring)
        
        # Arc length matching constraint
        arc_length_error = arc_length_cam - arc_length_ring
        
        return {
            'expressions': [arc_length_error],
            'lower': [-self.params.arc_length_tolerance],
            'upper': [self.params.arc_length_tolerance]
        }
    
    def _build_pressure_angle_constraints(self, cam_radius: 'ca.SX', ring_radius: 'ca.SX') -> Dict[str, List]:
        """
        Build pressure angle constraints for gear tooth geometry.
        
        The pressure angle must be within acceptable limits for manufacturability.
        """
        # Compute derivatives
        D = ca.DM(self.grid.differentiation_matrix)
        dr_cam_dtheta = D @ cam_radius
        
        # Pressure angle: α = arctan(dr/dθ / r)
        pressure_angle = ca.atan2(ca.fabs(dr_cam_dtheta), cam_radius)
        
        # Constraints: 0 ≤ α ≤ α_max
        expressions = []
        lower_bounds = []
        upper_bounds = []
        
        for i in range(self.grid.node_count):
            expressions.append(pressure_angle[i])
            lower_bounds.append(0.0)
            upper_bounds.append(self.pressure_angle_max)
        
        return {
            'expressions': expressions,
            'lower': lower_bounds,
            'upper': upper_bounds
        }
    
    def _build_tooth_thickness_constraints(self, cam_radius: 'ca.SX', ring_radius: 'ca.SX') -> Dict[str, List]:
        """
        Build tooth thickness constraints to prevent weak teeth.
        
        Tooth thickness is approximately related to the gear radius and
        the number of teeth (which depends on the circumference).
        """
        # Estimate number of teeth from circumference
        # This is a simplified model - real tooth count would be discrete
        circumference_cam = 2.0 * np.pi * cam_radius
        circumference_ring = 2.0 * np.pi * ring_radius
        
        # Assume minimum tooth count of 12 for reasonable gear strength
        min_teeth = 12.0
        tooth_pitch_cam = circumference_cam / min_teeth
        tooth_pitch_ring = circumference_ring / min_teeth
        
        # Tooth thickness should be at least 40% of tooth pitch
        min_thickness_fraction = 0.4
        thickness_cam = min_thickness_fraction * tooth_pitch_cam
        thickness_ring = min_thickness_fraction * tooth_pitch_ring
        
        expressions = []
        lower_bounds = []
        upper_bounds = []
        
        # Constraints for cam and ring tooth thickness
        for i in range(self.grid.node_count):
            expressions.append(thickness_cam[i])
            lower_bounds.append(self.params.tooth_thickness_min)
            upper_bounds.append(float('inf'))
            
            expressions.append(thickness_ring[i])
            lower_bounds.append(self.params.tooth_thickness_min)
            upper_bounds.append(float('inf'))
        
        return {
            'expressions': expressions,
            'lower': lower_bounds,
            'upper': upper_bounds
        }
    
    def _build_curvature_constraints(self, cam_radius: 'ca.SX', ring_radius: 'ca.SX') -> Dict[str, List]:
        """
        Build curvature constraints to prevent undercut and ensure manufacturability.
        
        The radius of curvature must be above a minimum value to avoid
        undercutting during gear manufacturing.
        """
        # Compute second derivatives
        D = ca.DM(self.grid.differentiation_matrix)
        D2 = ca.DM(self.grid.second_derivative_matrix)
        
        dr_cam = D @ cam_radius
        d2r_cam = D2 @ cam_radius
        
        # Radius of curvature: ρ = (r² + (dr/dθ)²)^(3/2) / |r² + 2(dr/dθ)² - r·d²r/dθ²|
        numerator = (cam_radius**2 + dr_cam**2)**(1.5)
        denominator = ca.fabs(cam_radius**2 + 2*dr_cam**2 - cam_radius*d2r_cam) + 1e-8
        curvature_radius = numerator / denominator
        
        expressions = []
        lower_bounds = []
        upper_bounds = []
        
        # Curvature radius must be above minimum
        for i in range(self.grid.node_count):
            expressions.append(curvature_radius[i])
            lower_bounds.append(self.params.curvature_radius_min)
            upper_bounds.append(float('inf'))
        
        return {
            'expressions': expressions,
            'lower': lower_bounds,
            'upper': upper_bounds
        }
    
    def _build_contact_ratio_constraints(self, cam_radius: 'ca.SX', ring_radius: 'ca.SX') -> Dict[str, List]:
        """
        Build contact ratio constraints for smooth power transmission.
        
        The contact ratio should be above a minimum value to ensure
        continuous tooth contact during gear meshing.
        """
        # Simplified contact ratio estimation
        # Real contact ratio depends on addendum, dedendum, and pressure angle
        
        # Base radii (simplified)
        base_radius_cam = cam_radius * ca.cos(self.pressure_angle_max)
        base_radius_ring = ring_radius * ca.cos(self.pressure_angle_max)
        
        # Contact length approximation
        contact_length = ca.sqrt((cam_radius + ring_radius)**2 - 
                                (base_radius_cam + base_radius_ring)**2)
        
        # Circular pitch
        circular_pitch = 2.0 * np.pi * cam_radius / 20.0  # Assume 20 teeth
        
        # Contact ratio
        contact_ratio = contact_length / circular_pitch
        
        # Average contact ratio over all nodes
        avg_contact_ratio = ca.sum1(contact_ratio) / self.grid.node_count
        
        return {
            'expressions': [avg_contact_ratio],
            'lower': [self.params.contact_ratio_min],
            'upper': [float('inf')]
        }
    
    def get_constraint_info(self) -> Dict[str, Any]:
        """Get information about the Litvin constraints."""
        return {
            "constraint_type": "litvin_conjugacy_manufacturability",
            "parameters": {
                "center_distance": self.params.center_distance,
                "cam_base_radius": self.params.cam_base_radius,
                "pressure_angle_max_deg": np.rad2deg(self.pressure_angle_max),
                "tooth_thickness_min": self.params.tooth_thickness_min,
                "curvature_radius_min": self.params.curvature_radius_min,
                "contact_ratio_min": self.params.contact_ratio_min
            },
            "grid_info": self.grid.get_grid_info()
        }
