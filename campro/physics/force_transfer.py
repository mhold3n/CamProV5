"""
Force Transfer Analysis for Planetary Gearset Optimization

This module extracts the robust physics calculations from the test suite
and provides them as a modular component for the unified optimization pipeline.
"""

import numpy as np
from typing import Dict, List, Any
from campro.constants import DEFAULT_YOUNGS_MODULUS, DEFAULT_POISSON_RATIO
from campro.logging import get_logger

logger = get_logger(__name__)


class ForceTransferAnalyzer:
    """
    Force transfer analyzer for planetary gearset optimization.
    
    This class extracts the robust physics calculations from the test suite
    and provides them as modular methods for the unified optimization pipeline.
    """
    
    def __init__(self):
        """Initialize the force transfer analyzer."""
        self.logger = get_logger(__name__)
    
    def calculate_piston_forces(self, displacement: np.ndarray, velocity: np.ndarray, 
                              acceleration: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate piston forces from cylinder pressure, inertia, and friction.
        
        Extracted from TestPhysicsCalculations.calculate_piston_forces()
        
        Args:
            displacement: Piston displacement (mm)
            velocity: Piston velocity (mm/s)
            acceleration: Piston acceleration (mm/s²)
            params: Physics parameters dictionary
            
        Returns:
            Net piston force (N)
        """
        # Cylinder pressure force (combustion pressure)
        cylinder_pressure = params.get("cylinderPressure", 2.0e5)  # Pa
        piston_area = params.get("pistonArea", 0.01)  # m²
        pressure_force = np.full_like(displacement, cylinder_pressure * piston_area)  # N
        
        # Inertial forces (F = ma)
        piston_mass = params.get("pistonMass", 5.0)  # kg
        # Convert acceleration from mm/s² to m/s²
        acceleration_ms2 = acceleration * 1e-3  # mm/s² to m/s²
        # Ensure acceleration has the same length as pressure_force
        if len(acceleration_ms2) != len(pressure_force):
            # Interpolate acceleration to match pressure_force length
            acceleration_interp = np.interp(np.linspace(0, 1, len(pressure_force)), 
                                          np.linspace(0, 1, len(acceleration_ms2)), acceleration_ms2)
        else:
            acceleration_interp = acceleration_ms2
        inertial_force = piston_mass * acceleration_interp  # N
        
        # Friction forces (velocity-dependent)
        friction_coefficient = params.get("frictionCoefficient", 0.05)
        # Friction opposes motion and increases with velocity magnitude
        velocity_ms = velocity * 1e-3  # mm/s to m/s
        # Ensure velocity_ms has the same length as pressure_force
        if len(velocity_ms) != len(pressure_force):
            # Interpolate velocity to match pressure_force length
            velocity_interp = np.interp(np.linspace(0, 1, len(pressure_force)), 
                                      np.linspace(0, 1, len(velocity_ms)), velocity_ms)
        else:
            velocity_interp = velocity_ms
        friction_force = friction_coefficient * pressure_force * np.sign(velocity_interp) * (1 + np.abs(velocity_interp) / 10.0)
        
        # Net piston force
        net_force = pressure_force + inertial_force + friction_force
        
        return net_force
    
    def calculate_contact_forces(self, gear_profiles: Dict[str, np.ndarray], 
                               planets: List[Dict[str, np.ndarray]], 
                               params: Dict[str, Any], 
                               piston_forces: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate contact forces using Hertzian contact model.
        
        Extracted from TestPhysicsCalculations.calculate_contact_forces()
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            planets: List of planet kinematics data
            params: Physics parameters dictionary
            piston_forces: Piston forces (N)
            
        Returns:
            Dictionary containing contact forces
        """
        r_sun = gear_profiles["r_sun"]
        r_planet = gear_profiles["r_planet"]
        r_ring_inner = gear_profiles["r_ring_inner"]
        
        # Interpolate piston forces to match gear profile resolution (360 points)
        n_points = len(r_sun)
        if len(piston_forces) != n_points:
            # Interpolate piston forces to match gear profile resolution
            motion_law_theta = np.linspace(0, 180, len(piston_forces))
            gear_profile_theta = np.linspace(0, 180, n_points)
            piston_forces = np.interp(gear_profile_theta, motion_law_theta, piston_forces)
        
        # Hertzian contact model parameters
        youngs_modulus = params.get("feaYoungsModulus", DEFAULT_YOUNGS_MODULUS)  # Pa
        poissons_ratio = params.get("feaPoissonsRatio", DEFAULT_POISSON_RATIO)
        
        # Effective modulus for Hertzian contact
        E_star = youngs_modulus / (2 * (1 - poissons_ratio**2))
        
        # Contact stiffness calculation (Hertzian contact theory)
        # For gear contact: k = (4/3) * E_star * sqrt(R_eff)
        # where R_eff is the effective radius of curvature
        
        # Sun-planet contact
        R_eff_sun_planet = (r_sun * r_planet) / (r_sun + r_planet)  # mm
        k_sun_planet = (4/3) * E_star * np.sqrt(R_eff_sun_planet * 1e-3)  # Convert mm to m
        
        # Planet-ring contact (internal gear)
        R_eff_planet_ring = (r_planet * r_ring_inner) / (r_ring_inner - r_planet)  # mm
        k_planet_ring = (4/3) * E_star * np.sqrt(R_eff_planet_ring * 1e-3)  # Convert mm to m
        
        # Contact forces from piston forces
        # Force transmission through gear train
        # Sun-planet contact force (primary transmission)
        sun_planet_contact_force = piston_forces * (r_sun / r_planet) * 1e-3  # Convert mm to m
        
        # Planet-ring contact force (reaction force)
        planet_ring_contact_force = sun_planet_contact_force * (r_planet / r_ring_inner)
        
        # Apply Hertzian contact scaling
        # Higher contact stiffness = higher forces for same displacement
        contact_stiffness_factor = k_sun_planet / (1e6)  # Normalize to reasonable scale
        sun_planet_contact_force *= contact_stiffness_factor
        
        contact_stiffness_factor_ring = k_planet_ring / (1e6)
        planet_ring_contact_force *= contact_stiffness_factor_ring
        
        return {
            "sun_planet": sun_planet_contact_force,
            "planet_ring": planet_ring_contact_force,
            "total_contact": sun_planet_contact_force + planet_ring_contact_force
        }
    
    def calculate_mechanical_advantage(self, piston_forces: np.ndarray, 
                                     contact_forces: Dict[str, np.ndarray],
                                     gear_profiles: Dict[str, np.ndarray], 
                                     params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate mechanical advantage from forces and torques.
        
        Extracted from TestPhysicsCalculations.calculate_mechanical_advantage()
        
        Args:
            piston_forces: Piston forces (N)
            contact_forces: Dictionary containing contact forces
            gear_profiles: Dictionary containing gear profile data
            params: Physics parameters dictionary
            
        Returns:
            Mechanical advantage array
        """
        r_sun = gear_profiles["r_sun"]
        gear_profiles["r_planet"]
        r_ring_inner = gear_profiles["r_ring_inner"]
        
        # Interpolate piston forces to match gear profile resolution (360 points)
        n_points = len(r_sun)
        if len(piston_forces) != n_points:
            # Interpolate piston forces to match gear profile resolution
            motion_law_theta = np.linspace(0, 180, len(piston_forces))
            gear_profile_theta = np.linspace(0, 180, n_points)
            piston_forces = np.interp(gear_profile_theta, motion_law_theta, piston_forces)
        
        # Effective lever arms (convert mm to m)
        r_effective_sun = r_sun * 1e-3  # m
        r_effective_ring = r_ring_inner * 1e-3  # m
        r_effective_piston = params.get("pistonLeverArm", 0.1)  # m
        
        # Calculate torques from contact forces
        contact_forces["sun_planet"] * r_effective_sun  # N⋅m
        tau_ring = contact_forces["planet_ring"] * r_effective_ring  # N⋅m
        
        # Mechanical advantage = output torque / input force / effective radius
        # MA = τ_ring / (F_piston * r_effective_piston)
        ma = tau_ring / (piston_forces * r_effective_piston)
        
        return ma
    
    def calculate_efficiency_from_losses(self, gear_profiles: Dict[str, np.ndarray], 
                                       planets: List[Dict[str, np.ndarray]], 
                                       params: Dict[str, Any], 
                                       piston_forces: np.ndarray, 
                                       contact_forces: Dict[str, np.ndarray], 
                                       displacement: np.ndarray, 
                                       velocity: np.ndarray, 
                                       acceleration: np.ndarray) -> np.ndarray:
        """
        Calculate transfer efficiency from energy losses.
        
        Extracted from TestPhysicsCalculations.calculate_efficiency_from_losses()
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            planets: List of planet kinematics data
            params: Physics parameters dictionary
            piston_forces: Piston forces (N)
            contact_forces: Dictionary containing contact forces
            displacement: Piston displacement (mm)
            velocity: Piston velocity (mm/s)
            acceleration: Piston acceleration (mm/s²)
            
        Returns:
            Transfer efficiency array
        """
        # Interpolate motion law data to match gear profile resolution (360 points)
        n_points = len(gear_profiles["r_sun"])
        if len(piston_forces) != n_points:
            # Interpolate motion law data to match gear profile resolution
            motion_law_theta = np.linspace(0, 180, len(piston_forces))
            gear_profile_theta = np.linspace(0, 180, n_points)
            piston_forces = np.interp(gear_profile_theta, motion_law_theta, piston_forces)
            displacement = np.interp(gear_profile_theta, motion_law_theta, displacement)
            velocity = np.interp(gear_profile_theta, motion_law_theta, velocity)
            acceleration = np.interp(gear_profile_theta, motion_law_theta, acceleration)
        
        # Input power (piston force × velocity)
        velocity_ms = velocity * 1e-3  # Convert mm/s to m/s
        input_power = piston_forces * velocity_ms  # W
        
        # Calculate energy losses
        hertzian_losses = self.calculate_hertzian_losses(contact_forces, gear_profiles, params)
        friction_losses = self.calculate_friction_losses(contact_forces, gear_profiles, params)
        deformation_losses = self.calculate_deformation_losses(contact_forces, gear_profiles, params)
        windage_losses = self.calculate_windage_losses(gear_profiles, params)
        
        # Total losses
        total_losses = hertzian_losses + friction_losses + deformation_losses + windage_losses
        
        # Calculate efficiency safely without triggering divide-by-zero warnings
        # η = (P_input - P_losses) / P_input
        power_threshold = 1e-6  # Small threshold to avoid division by zero
        efficiency = np.zeros_like(input_power, dtype=float)
        valid_mask = input_power > power_threshold
        efficiency[valid_mask] = (
            (input_power[valid_mask] - total_losses[valid_mask]) / input_power[valid_mask]
        )
        
        # Ensure efficiency is between 0 and 1
        efficiency = np.clip(efficiency, 0.0, 1.0)
        
        return efficiency
    
    def calculate_hertzian_losses(self, contact_forces: Dict[str, np.ndarray], 
                                gear_profiles: Dict[str, np.ndarray], 
                                params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate energy losses from Hertzian contact deformation.
        
        Extracted from TestPhysicsCalculations.calculate_hertzian_losses()
        
        Args:
            contact_forces: Dictionary containing contact forces
            gear_profiles: Dictionary containing gear profile data
            params: Physics parameters dictionary
            
        Returns:
            Hertzian losses array
        """
        # Simplified Hertzian contact loss model
        # Losses proportional to contact force^1.5 and contact area
        contact_force = contact_forces["total_contact"]
        params.get("feaYoungsModulus", DEFAULT_YOUNGS_MODULUS)
        
        # Hertzian contact loss coefficient (simplified)
        loss_coefficient = 1e-6  # W/N^1.5
        hertzian_losses = loss_coefficient * (contact_force ** 1.5)
        
        return hertzian_losses
    
    def calculate_friction_losses(self, contact_forces: Dict[str, np.ndarray], 
                                gear_profiles: Dict[str, np.ndarray], 
                                params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate energy losses from friction.
        
        Extracted from TestPhysicsCalculations.calculate_friction_losses()
        
        Args:
            contact_forces: Dictionary containing contact forces
            gear_profiles: Dictionary containing gear profile data
            params: Physics parameters dictionary
            
        Returns:
            Friction losses array
        """
        # Simplified friction loss model
        friction_coefficient = params.get("frictionCoefficient", 0.1)
        contact_force = contact_forces["total_contact"]
        
        # Assume sliding velocity proportional to gear rotation
        # TODO: FUTURE ENHANCEMENT - This single RPM calculation will be part of RPM sweep
        # analysis where friction losses are calculated across multiple operating speeds
        # to identify optimal efficiency points and speed-dependent loss characteristics.
        rpm = params.get("rpm", 3000.0)
        sliding_velocity = rpm * 0.1  # Simplified sliding velocity (m/s)
        
        # Friction losses = μ × F × v
        friction_losses = friction_coefficient * contact_force * sliding_velocity
        
        return friction_losses
    
    def calculate_deformation_losses(self, contact_forces: Dict[str, np.ndarray], 
                                   gear_profiles: Dict[str, np.ndarray], 
                                   params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate energy losses from gear deformation.
        
        Extracted from TestPhysicsCalculations.calculate_deformation_losses()
        
        Args:
            contact_forces: Dictionary containing contact forces
            gear_profiles: Dictionary containing gear profile data
            params: Physics parameters dictionary
            
        Returns:
            Deformation losses array
        """
        # Simplified deformation loss model
        contact_force = contact_forces["total_contact"]
        params.get("feaYoungsModulus", DEFAULT_YOUNGS_MODULUS)
        
        # Deformation loss coefficient (simplified)
        deformation_coefficient = 1e-8  # W/N^2
        deformation_losses = deformation_coefficient * (contact_force ** 2)
        
        return deformation_losses
    
    def calculate_windage_losses(self, gear_profiles: Dict[str, np.ndarray], 
                               params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate energy losses from windage and churning.
        
        Extracted from TestPhysicsCalculations.calculate_windage_losses()
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            params: Physics parameters dictionary
            
        Returns:
            Windage losses array
        """
        # Simplified windage loss model
        # TODO: FUTURE ENHANCEMENT - This single RPM windage calculation will be part of RPM sweep
        # analysis where windage losses are calculated across multiple operating speeds to
        # identify speed-dependent aerodynamic losses and optimal operating ranges.
        r_ring = gear_profiles["r_ring_inner"]
        rpm = params.get("rpm", 3000.0)
        
        # Windage losses proportional to gear size and speed
        windage_coefficient = 1e-9  # W/(mm^2 × rpm^2)
        
        # Convert to numpy array if scalar
        if np.isscalar(r_ring):
            r_ring = np.array([r_ring])
        
        windage_losses = windage_coefficient * (r_ring ** 2) * (rpm ** 2)
        
        return windage_losses
    
    def calculate_fea_penalty(self, gear_profiles: Dict[str, np.ndarray], 
                            planets: List[Dict[str, np.ndarray]], 
                            params: Dict[str, Any], 
                            contact_forces: Dict[str, np.ndarray]) -> float:
        """
        Calculate FEA penalty from stress analysis.
        
        Extracted from TestPhysicsCalculations.calculate_fea_penalty()
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            planets: List of planet kinematics data
            params: Physics parameters dictionary
            contact_forces: Dictionary containing contact forces
            
        Returns:
            FEA penalty value
        """
        # Calculate Von Mises stress
        von_mises_stress = self.calculate_von_mises_stress(contact_forces, gear_profiles, params)
        
        # Calculate Hertzian contact stress
        hertzian_stress = self.calculate_hertzian_contact_stress(contact_forces, gear_profiles, params)
        
        # Get material properties
        yield_strength = params.get("feaYieldStrength", 400e6)  # Pa
        
        # Calculate safety factors
        safety_factor_von_mises = yield_strength / von_mises_stress
        safety_factor_hertzian = yield_strength / hertzian_stress
        
        # Minimum safety factor
        min_safety_factor = np.minimum(safety_factor_von_mises, safety_factor_hertzian)
        
        # Penalty for low safety factors (high stress)
        # Target safety factor = 2.0
        target_safety_factor = 2.0
        penalty = np.where(min_safety_factor < target_safety_factor,
                          (target_safety_factor - min_safety_factor) / target_safety_factor,
                          0.0)
        
        # Return maximum penalty across all points
        return np.max(penalty)
    
    def calculate_von_mises_stress(self, contact_forces: Dict[str, np.ndarray], 
                                 gear_profiles: Dict[str, np.ndarray], 
                                 params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate Von Mises stress from contact forces.
        
        Extracted from TestPhysicsCalculations.calculate_von_mises_stress()
        
        Args:
            contact_forces: Dictionary containing contact forces
            gear_profiles: Dictionary containing gear profile data
            params: Physics parameters dictionary
            
        Returns:
            Von Mises stress array
        """
        contact_force = contact_forces["total_contact"]
        
        # Simplified Von Mises stress calculation
        # Stress = Force / Area (simplified)
        # Assume contact area proportional to gear size
        r_planet = gear_profiles["r_planet"]
        contact_area = np.pi * (r_planet * 1e-3) ** 2  # Convert mm to m, area in m²
        
        # Von Mises stress (simplified)
        von_mises_stress = contact_force / contact_area  # Pa
        
        return von_mises_stress
    
    def calculate_hertzian_contact_stress(self, contact_forces: Dict[str, np.ndarray], 
                                        gear_profiles: Dict[str, np.ndarray], 
                                        params: Dict[str, Any]) -> np.ndarray:
        """
        Calculate Hertzian contact stress.
        
        Extracted from TestPhysicsCalculations.calculate_hertzian_contact_stress()
        
        Args:
            contact_forces: Dictionary containing contact forces
            gear_profiles: Dictionary containing gear profile data
            params: Physics parameters dictionary
            
        Returns:
            Hertzian contact stress array
        """
        contact_force = contact_forces["total_contact"]
        r_sun = gear_profiles["r_sun"]
        r_planet = gear_profiles["r_planet"]
        
        # Hertzian contact stress calculation
        # σ_h = (F * E_star / (π * R_eff))^0.5
        youngs_modulus = params.get("feaYoungsModulus", DEFAULT_YOUNGS_MODULUS)
        poissons_ratio = params.get("feaPoissonsRatio", DEFAULT_POISSON_RATIO)
        E_star = youngs_modulus / (2 * (1 - poissons_ratio**2))
        
        # Effective radius of curvature
        R_eff = (r_sun * r_planet) / (r_sun + r_planet) * 1e-3  # Convert mm to m
        
        # Hertzian contact stress
        hertzian_stress = np.sqrt(contact_force * E_star / (np.pi * R_eff))
        
        return hertzian_stress
