"""
Transmission Physics for Engine Optimization

This module implements the missing transmission physics for Phase 2 optimization:
- Kinematic coupling: θ̇ = i(x)·ẋ
- Power balance: τ_out·θ̇ = F_p·ẋ − P_loss
- Transmission efficiency: η̂ = η/η̄
- Contact stress: Hertzian contact calculation
- Friction modeling: Stribeck friction model
- Fatigue constraints: SF = σ_lim/σ_max ≥ 1
"""

import numpy as np
import casadi as ca
from typing import Dict, Optional
from dataclasses import dataclass

from campro.logging import get_logger
log = get_logger(__name__)


@dataclass
class TransmissionParameters:
    """Parameters for transmission physics calculations."""
    
    # Gear geometry
    sun_radius_base_m: float = 0.05  # Base sun gear radius (m)
    planet_radius_base_m: float = 0.08  # Base planet gear radius (m)
    ring_radius_base_m: float = 0.21  # Base ring gear radius (m)
    
    # Material properties
    youngs_modulus_Pa: float = 200e9  # Young's modulus (Pa)
    poisson_ratio: float = 0.3  # Poisson's ratio
    material_strength_Pa: float = 500e6  # Material strength (Pa)
    
    # Friction parameters
    static_friction_coeff: float = 0.1  # Static friction coefficient
    dynamic_friction_coeff: float = 0.08  # Dynamic friction coefficient
    stribeck_velocity_mps: float = 0.01  # Stribeck velocity (m/s)
    
    # Contact parameters
    contact_stiffness_N_m: float = 1e8  # Contact stiffness (N/m)
    contact_damping_Ns_m: float = 1e3  # Contact damping (Ns/m)
    
    # Efficiency parameters
    base_efficiency: float = 0.95  # Base transmission efficiency
    efficiency_degradation_factor: float = 0.1  # Efficiency degradation factor
    
    # Operating conditions
    rpm: float = 3000.0  # Operating speed (RPM)
    load_torque_Nm: float = 100.0  # Load torque (Nm)


class KinematicCoupling:
    """
    Kinematic coupling between linear and rotational motion.
    
    Implements θ̇ = i(x)·ẋ where i(x) is the instantaneous gear ratio.
    """
    
    def __init__(self, parameters: TransmissionParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_instantaneous_ratio(self, displacement: np.ndarray,
                                    gear_radii: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Calculate instantaneous gear ratio i(x).
        
        i(x) = R_ring(x) / R_sun(x)
        
        Args:
            displacement: Piston displacement array (m)
            gear_radii: Dictionary with sun, planet, ring radii
            
        Returns:
            Instantaneous ratio array
        """
        sun_radius = gear_radii['sun_radius']
        ring_radius = gear_radii['ring_radius']
        
        # Avoid division by zero
        sun_radius_safe = np.maximum(sun_radius, 1e-6)
        
        instantaneous_ratio = ring_radius / sun_radius_safe
        
        return instantaneous_ratio
    
    def calculate_instantaneous_ratio_casadi(self, displacement: ca.SX,
                                           gear_radii: Dict[str, ca.SX]) -> ca.SX:
        """
        Calculate instantaneous gear ratio using CasADi.
        
        Args:
            displacement: Piston displacement (CasADi SX)
            gear_radii: Dictionary with gear radii (CasADi SX)
            
        Returns:
            Instantaneous ratio (CasADi SX)
        """
        sun_radius = gear_radii['sun_radius']
        ring_radius = gear_radii['ring_radius']
        
        # Ensure proper array shapes
        if sun_radius.shape[1] == 1:
            sun_radius = ca.reshape(sun_radius, -1, 1)
        if ring_radius.shape[1] == 1:
            ring_radius = ca.reshape(ring_radius, -1, 1)
        
        # Avoid division by zero
        sun_radius_safe = ca.fmax(sun_radius, 1e-6)
        
        instantaneous_ratio = ring_radius / sun_radius_safe
        
        return instantaneous_ratio
    
    def calculate_angular_velocity(self, linear_velocity: np.ndarray,
                                 instantaneous_ratio: np.ndarray) -> np.ndarray:
        """
        Calculate angular velocity from linear velocity.
        
        θ̇ = i(x)·ẋ
        
        Args:
            linear_velocity: Linear velocity array (m/s)
            instantaneous_ratio: Instantaneous ratio array
            
        Returns:
            Angular velocity array (rad/s)
        """
        angular_velocity = instantaneous_ratio * linear_velocity
        
        return angular_velocity
    
    def calculate_angular_velocity_casadi(self, linear_velocity: ca.SX,
                                        instantaneous_ratio: ca.SX) -> ca.SX:
        """
        Calculate angular velocity using CasADi.
        
        Args:
            linear_velocity: Linear velocity (CasADi SX)
            instantaneous_ratio: Instantaneous ratio (CasADi SX)
            
        Returns:
            Angular velocity (CasADi SX)
        """
        angular_velocity = instantaneous_ratio * linear_velocity
        
        return angular_velocity
    
    def calculate_kinematic_constraints(self, displacement: np.ndarray,
                                      velocity: np.ndarray,
                                      gear_radii: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Calculate kinematic constraints for optimization.
        
        Args:
            displacement: Piston displacement array (m)
            velocity: Linear velocity array (m/s)
            gear_radii: Dictionary with gear radii
            
        Returns:
            Dictionary of kinematic constraints
        """
        # Calculate instantaneous ratio
        instantaneous_ratio = self.calculate_instantaneous_ratio(displacement, gear_radii)
        
        # Calculate angular velocity
        angular_velocity = self.calculate_angular_velocity(velocity, instantaneous_ratio)
        
        # Calculate constraints
        constraints = {
            'instantaneous_ratio': instantaneous_ratio,
            'angular_velocity_rad_s': angular_velocity,
            'ratio_bounds': {
                'lower': np.full_like(displacement, 1.5),  # Minimum ratio
                'upper': np.full_like(displacement, 5.0)   # Maximum ratio
            },
            'angular_velocity_bounds': {
                'lower': np.full_like(displacement, -1000.0),  # Minimum angular velocity (rad/s)
                'upper': np.full_like(displacement, 1000.0)    # Maximum angular velocity (rad/s)
            }
        }
        
        return constraints


class PowerBalance:
    """
    Power balance between input and output.
    
    Implements τ_out·θ̇ = F_p·ẋ − P_loss
    """
    
    def __init__(self, parameters: TransmissionParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_piston_force(self, pressure: np.ndarray,
                             piston_area: float) -> np.ndarray:
        """
        Calculate piston force from pressure.
        
        F_p = p * A_p
        
        Args:
            pressure: Pressure array (Pa)
            piston_area: Piston area (m²)
            
        Returns:
            Piston force array (N)
        """
        piston_force = pressure * piston_area
        
        return piston_force
    
    def calculate_piston_force_casadi(self, pressure: ca.SX,
                                    piston_area: float) -> ca.SX:
        """
        Calculate piston force using CasADi.
        
        Args:
            pressure: Pressure (CasADi SX)
            piston_area: Piston area (m²)
            
        Returns:
            Piston force (CasADi SX)
        """
        piston_force = pressure * piston_area
        
        return piston_force
    
    def calculate_output_torque(self, piston_force: np.ndarray,
                              displacement: np.ndarray,
                              instantaneous_ratio: np.ndarray,
                              efficiency: np.ndarray) -> np.ndarray:
        """
        Calculate output torque.
        
        τ_out = F_p * x * i(x) * η(x)
        
        Args:
            piston_force: Piston force array (N)
            displacement: Piston displacement array (m)
            instantaneous_ratio: Instantaneous ratio array
            efficiency: Transmission efficiency array
            
        Returns:
            Output torque array (Nm)
        """
        output_torque = piston_force * displacement * instantaneous_ratio * efficiency
        
        return output_torque
    
    def calculate_output_torque_casadi(self, piston_force: ca.SX,
                                     displacement: ca.SX,
                                     instantaneous_ratio: ca.SX,
                                     efficiency: ca.SX) -> ca.SX:
        """
        Calculate output torque using CasADi.
        
        Args:
            piston_force: Piston force (CasADi SX)
            displacement: Piston displacement (CasADi SX)
            instantaneous_ratio: Instantaneous ratio (CasADi SX)
            efficiency: Transmission efficiency (CasADi SX)
            
        Returns:
            Output torque (CasADi SX)
        """
        output_torque = piston_force * displacement * instantaneous_ratio * efficiency
        
        return output_torque
    
    def calculate_power_loss(self, velocity: np.ndarray,
                           angular_velocity: np.ndarray,
                           contact_force: np.ndarray) -> np.ndarray:
        """
        Calculate power loss due to friction.
        
        P_loss = F_friction * v
        
        Args:
            velocity: Linear velocity array (m/s)
            angular_velocity: Angular velocity array (rad/s)
            contact_force: Contact force array (N)
            
        Returns:
            Power loss array (W)
        """
        # Simplified power loss calculation
        # In a full implementation, this would include:
        # - Rolling friction
        # - Sliding friction
        # - Bearing losses
        # - Windage losses
        
        friction_force = contact_force * self.params.dynamic_friction_coeff
        power_loss = friction_force * np.abs(velocity)
        
        return power_loss
    
    def calculate_power_balance_constraints(self, piston_force: np.ndarray,
                                          velocity: np.ndarray,
                                          angular_velocity: np.ndarray,
                                          output_torque: np.ndarray,
                                          power_loss: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate power balance constraints.
        
        Args:
            piston_force: Piston force array (N)
            velocity: Linear velocity array (m/s)
            angular_velocity: Angular velocity array (rad/s)
            output_torque: Output torque array (Nm)
            power_loss: Power loss array (W)
            
        Returns:
            Dictionary of power balance constraints
        """
        # Calculate input power
        input_power = piston_force * velocity
        
        # Calculate output power
        output_power = output_torque * angular_velocity
        
        # Calculate power balance residual
        power_balance_residual = input_power - output_power - power_loss
        
        constraints = {
            'input_power_W': input_power,
            'output_power_W': output_power,
            'power_loss_W': power_loss,
            'power_balance_residual_W': power_balance_residual,
            'power_balance_tolerance_W': np.full_like(velocity, 1.0)  # 1W tolerance
        }
        
        return constraints


class TransmissionEfficiency:
    """
    Transmission efficiency calculation.
    
    Implements η̂ = η/η̄ where η is the actual efficiency and η̄ is the reference efficiency.
    """
    
    def __init__(self, parameters: TransmissionParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_transmission_efficiency(self, contact_stress: np.ndarray,
                                        velocity: np.ndarray,
                                        angular_velocity: np.ndarray) -> np.ndarray:
        """
        Calculate transmission efficiency.
        
        η = η_base * (1 - degradation_factor * stress_factor * velocity_factor)
        
        Args:
            contact_stress: Contact stress array (Pa)
            velocity: Linear velocity array (m/s)
            angular_velocity: Angular velocity array (rad/s)
            
        Returns:
            Transmission efficiency array [0,1]
        """
        # Calculate stress factor
        stress_factor = contact_stress / self.params.material_strength_Pa
        
        # Calculate velocity factor
        velocity_magnitude = np.sqrt(velocity**2 + angular_velocity**2)
        velocity_factor = velocity_magnitude / 10.0  # Normalize to 10 m/s
        
        # Calculate efficiency degradation
        degradation = self.params.efficiency_degradation_factor * stress_factor * velocity_factor
        
        # Calculate efficiency
        efficiency = self.params.base_efficiency * (1.0 - degradation)
        
        # Ensure efficiency is within bounds
        efficiency = np.clip(efficiency, 0.1, 1.0)
        
        return efficiency
    
    def calculate_transmission_efficiency_casadi(self, contact_stress: ca.SX,
                                               velocity: ca.SX,
                                               angular_velocity: ca.SX) -> ca.SX:
        """
        Calculate transmission efficiency using CasADi.
        
        Args:
            contact_stress: Contact stress (CasADi SX)
            velocity: Linear velocity (CasADi SX)
            angular_velocity: Angular velocity (CasADi SX)
            
        Returns:
            Transmission efficiency (CasADi SX)
        """
        # Calculate stress factor
        stress_factor = contact_stress / self.params.material_strength_Pa
        
        # Calculate velocity factor
        velocity_magnitude = ca.sqrt(velocity**2 + angular_velocity**2)
        velocity_factor = velocity_magnitude / 10.0  # Normalize to 10 m/s
        
        # Calculate efficiency degradation
        degradation = self.params.efficiency_degradation_factor * stress_factor * velocity_factor
        
        # Calculate efficiency
        efficiency = self.params.base_efficiency * (1.0 - degradation)
        
        # Ensure efficiency is within bounds
        efficiency = ca.fmax(ca.fmin(efficiency, 1.0), 0.1)
        
        return efficiency
    
    def calculate_efficiency_objectives(self, efficiency: np.ndarray) -> Dict[str, float]:
        """
        Calculate efficiency objectives for optimization.
        
        Args:
            efficiency: Transmission efficiency array
            
        Returns:
            Dictionary of efficiency objectives
        """
        objectives = {
            'mean_efficiency': np.mean(efficiency),
            'min_efficiency': np.min(efficiency),
            'max_efficiency': np.max(efficiency),
            'efficiency_variance': np.var(efficiency),
            'efficiency_std': np.std(efficiency)
        }
        
        return objectives


class ContactMechanics:
    """
    Contact mechanics for gear interactions.
    
    Implements Hertzian contact calculation and contact stress analysis.
    """
    
    def __init__(self, parameters: TransmissionParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_contact_stress_hertzian(self, contact_force: np.ndarray,
                                        contact_radius: np.ndarray,
                                        material_properties: Optional[Dict[str, float]] = None) -> np.ndarray:
        """
        Calculate contact stress using Hertzian contact theory.
        
        σ = sqrt(F * E / (π * R_contact))
        
        Args:
            contact_force: Contact force array (N)
            contact_radius: Contact radius array (m)
            material_properties: Material properties dictionary
            
        Returns:
            Contact stress array (Pa)
        """
        if material_properties is None:
            E = self.params.youngs_modulus_Pa
            nu = self.params.poisson_ratio
        else:
            E = material_properties.get('youngs_modulus_Pa', self.params.youngs_modulus_Pa)
            nu = material_properties.get('poisson_ratio', self.params.poisson_ratio)
        
        # Calculate effective modulus
        E_eff = E / (1 - nu**2)
        
        # Calculate contact stress
        # Avoid division by zero
        contact_radius_safe = np.maximum(contact_radius, 1e-6)
        contact_force_safe = np.maximum(contact_force, 1e-6)
        
        contact_stress = np.sqrt(contact_force_safe * E_eff / (np.pi * contact_radius_safe))
        
        return contact_stress
    
    def calculate_contact_stress_hertzian_casadi(self, contact_force: ca.SX,
                                               contact_radius: ca.SX,
                                               material_properties: Optional[Dict[str, float]] = None) -> ca.SX:
        """
        Calculate contact stress using CasADi.
        
        Args:
            contact_force: Contact force (CasADi SX)
            contact_radius: Contact radius (CasADi SX)
            material_properties: Material properties dictionary
            
        Returns:
            Contact stress (CasADi SX)
        """
        if material_properties is None:
            E = self.params.youngs_modulus_Pa
            nu = self.params.poisson_ratio
        else:
            E = material_properties.get('youngs_modulus_Pa', self.params.youngs_modulus_Pa)
            nu = material_properties.get('poisson_ratio', self.params.poisson_ratio)
        
        # Calculate effective modulus
        E_eff = E / (1 - nu**2)
        
        # Calculate contact stress
        contact_radius_safe = ca.fmax(contact_radius, 1e-6)
        contact_force_safe = ca.fmax(contact_force, 1e-6)
        
        contact_stress = ca.sqrt(contact_force_safe * E_eff / (ca.pi * contact_radius_safe))
        
        return contact_stress
    
    def calculate_contact_force(self, gear_radii: Dict[str, np.ndarray],
                              displacement: np.ndarray,
                              stiffness: Optional[float] = None) -> np.ndarray:
        """
        Calculate contact force between gears.
        
        F_contact = k * (R_ring - R_sun - 2*R_planet)
        
        Args:
            gear_radii: Dictionary with gear radii
            displacement: Piston displacement array (m)
            stiffness: Contact stiffness (N/m)
            
        Returns:
            Contact force array (N)
        """
        if stiffness is None:
            stiffness = self.params.contact_stiffness_N_m
        
        sun_radius = gear_radii['sun_radius']
        planet_radius = gear_radii['planet_radius']
        ring_radius = gear_radii['ring_radius']
        
        # Calculate contact force
        contact_force = stiffness * (ring_radius - sun_radius - 2 * planet_radius)
        
        # Ensure positive contact force
        contact_force = np.maximum(contact_force, 0.0)
        
        return contact_force
    
    def calculate_contact_force_casadi(self, gear_radii: Dict[str, ca.SX],
                                     displacement: ca.SX,
                                     stiffness: Optional[float] = None) -> ca.SX:
        """
        Calculate contact force using CasADi.
        
        Args:
            gear_radii: Dictionary with gear radii (CasADi SX)
            displacement: Piston displacement (CasADi SX)
            stiffness: Contact stiffness (N/m)
            
        Returns:
            Contact force (CasADi SX)
        """
        if stiffness is None:
            stiffness = self.params.contact_stiffness_N_m
        
        sun_radius = gear_radii['sun_radius']
        planet_radius = gear_radii['planet_radius']
        ring_radius = gear_radii['ring_radius']
        
        # Calculate contact force
        contact_force = stiffness * (ring_radius - sun_radius - 2 * planet_radius)
        
        # Ensure positive contact force
        contact_force = ca.fmax(contact_force, 0.0)
        
        return contact_force
    
    def calculate_fatigue_safety_factor(self, contact_stress: np.ndarray,
                                      material_strength: Optional[float] = None) -> np.ndarray:
        """
        Calculate fatigue safety factor.
        
        SF = σ_lim / σ_max
        
        Args:
            contact_stress: Contact stress array (Pa)
            material_strength: Material strength (Pa)
            
        Returns:
            Safety factor array
        """
        if material_strength is None:
            material_strength = self.params.material_strength_Pa
        
        # Calculate safety factor
        safety_factor = material_strength / np.maximum(contact_stress, 1e-6)
        
        return safety_factor
    
    def calculate_fatigue_safety_factor_casadi(self, contact_stress: ca.SX,
                                             material_strength: Optional[float] = None) -> ca.SX:
        """
        Calculate fatigue safety factor using CasADi.
        
        Args:
            contact_stress: Contact stress (CasADi SX)
            material_strength: Material strength (Pa)
            
        Returns:
            Safety factor (CasADi SX)
        """
        if material_strength is None:
            material_strength = self.params.material_strength_Pa
        
        # Calculate safety factor
        safety_factor = material_strength / ca.fmax(contact_stress, 1e-6)
        
        return safety_factor


class FrictionModel:
    """
    Friction modeling using Stribeck friction model.
    
    Implements smooth Stribeck (C¹) friction model.
    """
    
    def __init__(self, parameters: TransmissionParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_stribeck_friction(self, velocity: np.ndarray,
                                  normal_force: np.ndarray) -> np.ndarray:
        """
        Calculate friction force using Stribeck model.
        
        F_friction = μ(v) * F_normal
        
        where μ(v) = μ_d + (μ_s - μ_d) * exp(-|v|/v_s)
        
        Args:
            velocity: Relative velocity array (m/s)
            normal_force: Normal force array (N)
            
        Returns:
            Friction force array (N)
        """
        # Calculate friction coefficient
        velocity_magnitude = np.abs(velocity)
        friction_coeff = (self.params.dynamic_friction_coeff + 
                         (self.params.static_friction_coeff - self.params.dynamic_friction_coeff) * 
                         np.exp(-velocity_magnitude / self.params.stribeck_velocity_mps))
        
        # Calculate friction force
        friction_force = friction_coeff * normal_force
        
        return friction_force
    
    def calculate_stribeck_friction_casadi(self, velocity: ca.SX,
                                         normal_force: ca.SX) -> ca.SX:
        """
        Calculate friction force using CasADi.
        
        Args:
            velocity: Relative velocity (CasADi SX)
            normal_force: Normal force (CasADi SX)
            
        Returns:
            Friction force (CasADi SX)
        """
        # Calculate friction coefficient
        velocity_magnitude = ca.fabs(velocity)
        friction_coeff = (self.params.dynamic_friction_coeff + 
                         (self.params.static_friction_coeff - self.params.dynamic_friction_coeff) * 
                         ca.exp(-velocity_magnitude / self.params.stribeck_velocity_mps))
        
        # Calculate friction force
        friction_force = friction_coeff * normal_force
        
        return friction_force
    
    def calculate_friction_power_loss(self, friction_force: np.ndarray,
                                    velocity: np.ndarray) -> np.ndarray:
        """
        Calculate power loss due to friction.
        
        P_friction = F_friction * |v|
        
        Args:
            friction_force: Friction force array (N)
            velocity: Relative velocity array (m/s)
            
        Returns:
            Friction power loss array (W)
        """
        power_loss = friction_force * np.abs(velocity)
        
        return power_loss
    
    def calculate_friction_power_loss_casadi(self, friction_force: ca.SX,
                                           velocity: ca.SX) -> ca.SX:
        """
        Calculate friction power loss using CasADi.
        
        Args:
            friction_force: Friction force (CasADi SX)
            velocity: Relative velocity (CasADi SX)
            
        Returns:
            Friction power loss (CasADi SX)
        """
        power_loss = friction_force * ca.fabs(velocity)
        
        return power_loss


class TransmissionOptimizer:
    """
    Transmission optimizer that integrates all transmission physics.
    
    This class provides the interface for Phase 2 transmission optimization.
    """
    
    def __init__(self, parameters: TransmissionParameters):
        self.params = parameters
        self.kinematic_coupling = KinematicCoupling(parameters)
        self.power_balance = PowerBalance(parameters)
        self.transmission_efficiency = TransmissionEfficiency(parameters)
        self.contact_mechanics = ContactMechanics(parameters)
        self.friction_model = FrictionModel(parameters)
        self.logger = get_logger(__name__)
    
    def calculate_transmission_objectives(self, displacement: np.ndarray,
                                        velocity: np.ndarray,
                                        pressure: np.ndarray,
                                        gear_radii: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Calculate transmission objectives for optimization.
        
        Args:
            displacement: Piston displacement array (m)
            velocity: Linear velocity array (m/s)
            pressure: Pressure array (Pa)
            gear_radii: Dictionary with gear radii
            
        Returns:
            Dictionary of transmission objectives
        """
        # Calculate instantaneous ratio
        instantaneous_ratio = self.kinematic_coupling.calculate_instantaneous_ratio(
            displacement, gear_radii)
        
        # Calculate angular velocity
        angular_velocity = self.kinematic_coupling.calculate_angular_velocity(
            velocity, instantaneous_ratio)
        
        # Calculate piston force
        piston_force = self.power_balance.calculate_piston_force(
            pressure, 0.01)  # Assume 0.01 m² piston area
        
        # Calculate contact force
        contact_force = self.contact_mechanics.calculate_contact_force(
            gear_radii, displacement)
        
        # Calculate contact stress
        contact_radius = (gear_radii['sun_radius'] + gear_radii['planet_radius']) / 2.0
        contact_stress = self.contact_mechanics.calculate_contact_stress_hertzian(
            contact_force, contact_radius)
        
        # Calculate transmission efficiency
        efficiency = self.transmission_efficiency.calculate_transmission_efficiency(
            contact_stress, velocity, angular_velocity)
        
        # Calculate output torque
        output_torque = self.power_balance.calculate_output_torque(
            piston_force, displacement, instantaneous_ratio, efficiency)
        
        # Calculate friction power loss
        friction_force = self.friction_model.calculate_stribeck_friction(
            velocity, contact_force)
        friction_power_loss = self.friction_model.calculate_friction_power_loss(
            friction_force, velocity)
        
        # Calculate objectives
        objectives = {
            'mean_efficiency': np.mean(efficiency),
            'min_efficiency': np.min(efficiency),
            'max_contact_stress_Pa': np.max(contact_stress),
            'mean_contact_stress_Pa': np.mean(contact_stress),
            'max_output_torque_Nm': np.max(output_torque),
            'mean_output_torque_Nm': np.mean(output_torque),
            'total_friction_power_loss_W': np.sum(friction_power_loss),
            'mean_friction_power_loss_W': np.mean(friction_power_loss)
        }
        
        return objectives
    
    def calculate_transmission_constraints(self, displacement: np.ndarray,
                                         velocity: np.ndarray,
                                         pressure: np.ndarray,
                                         gear_radii: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Calculate transmission constraints for optimization.
        
        Args:
            displacement: Piston displacement array (m)
            velocity: Linear velocity array (m/s)
            pressure: Pressure array (Pa)
            gear_radii: Dictionary with gear radii
            
        Returns:
            Dictionary of transmission constraints
        """
        # Calculate kinematic constraints
        kinematic_constraints = self.kinematic_coupling.calculate_kinematic_constraints(
            displacement, velocity, gear_radii)
        
        # Calculate contact force and stress
        contact_force = self.contact_mechanics.calculate_contact_force(
            gear_radii, displacement)
        contact_radius = (gear_radii['sun_radius'] + gear_radii['planet_radius']) / 2.0
        contact_stress = self.contact_mechanics.calculate_contact_stress_hertzian(
            contact_force, contact_radius)
        
        # Calculate fatigue safety factor
        safety_factor = self.contact_mechanics.calculate_fatigue_safety_factor(
            contact_stress)
        
        # Calculate power balance constraints
        piston_force = self.power_balance.calculate_piston_force(
            pressure, 0.01)  # Assume 0.01 m² piston area
        angular_velocity = kinematic_constraints['angular_velocity_rad_s']
        output_torque = self.power_balance.calculate_output_torque(
            piston_force, displacement, 
            kinematic_constraints['instantaneous_ratio'], 
            np.ones_like(displacement) * 0.95)  # Assume 95% efficiency
        
        power_loss = self.power_balance.calculate_power_loss(
            velocity, angular_velocity, contact_force)
        
        power_balance_constraints = self.power_balance.calculate_power_balance_constraints(
            piston_force, velocity, angular_velocity, output_torque, power_loss)
        
        # Combine constraints
        constraints = {
            'kinematic_constraints': kinematic_constraints,
            'contact_stress_Pa': contact_stress,
            'fatigue_safety_factor': safety_factor,
            'power_balance_constraints': power_balance_constraints,
            'contact_force_N': contact_force,
            'safety_factor_bounds': {
                'lower': np.ones_like(displacement),  # SF ≥ 1
                'upper': np.full_like(displacement, 10.0)  # SF ≤ 10
            }
        }
        
        return constraints
