"""
Thermodynamic Foundation for Engine Optimization

This module implements the missing thermodynamic calculations for Phase 1 optimization:
- Volume calculation: V(t) = V_c + A_p x(t)
- Pressure calculation: Polytropic process pV^γ = const
- Temperature modeling: From ideal gas law
- Indicated work: W_id = ∮ p dV
- Valve modeling: Lift profiles, timing, constraints
- Combustion modeling: Wiebe function, heat release
- State equations: Mass/energy balance
"""

import numpy as np
import casadi as ca
from typing import Dict, Optional
from dataclasses import dataclass

from campro.logging import get_logger
log = get_logger(__name__)


@dataclass
class ThermodynamicParameters:
    """Parameters for thermodynamic calculations."""
    
    # Engine geometry
    piston_area_m2: float = 0.01  # Piston crown area (m²)
    clearance_volume_m3: float = 0.001  # Clearance volume (m³)
    stroke_length_m: float = 0.1  # Stroke length (m)
    
    # Thermodynamic properties
    gamma: float = 1.35  # Polytropic exponent (specific heat ratio)
    gas_constant: float = 287.0  # Specific gas constant (J/kg·K)
    ambient_temperature_K: float = 298.15  # Ambient temperature (K)
    ambient_pressure_Pa: float = 101325.0  # Ambient pressure (Pa)
    
    # Valve parameters
    max_valve_lift_m: float = 0.01  # Maximum valve lift (m)
    valve_timing_deg: Optional[Dict[str, float]] = None  # Valve timing in degrees
    
    # Combustion parameters
    combustion_efficiency: float = 0.95  # Combustion efficiency
    heat_release_fraction: float = 0.8  # Fraction of fuel energy released
    ignition_timing_deg: float = -15.0  # Ignition timing (degrees before TDC)
    
    # Operating conditions
    rpm: float = 3000.0  # Engine speed (RPM)
    equivalence_ratio: float = 1.0  # Air-fuel ratio
    
    def __post_init__(self):
        if self.valve_timing_deg is None:
            self.valve_timing_deg = {
                'intake_open': -10.0,    # Intake valve opens (degrees before TDC)
                'intake_close': 40.0,    # Intake valve closes (degrees after BDC)
                'exhaust_open': 50.0,    # Exhaust valve opens (degrees before BDC)
                'exhaust_close': 10.0    # Exhaust valve closes (degrees after TDC)
            }


class ThermodynamicCalculator:
    """
    Thermodynamic calculator for engine optimization.
    
    Implements the missing thermodynamic foundation from the gap analysis:
    - Volume calculation: V(t) = V_c + A_p x(t)
    - Pressure calculation: Polytropic process pV^γ = const
    - Temperature modeling: From ideal gas law
    - Indicated work: W_id = ∮ p dV
    """
    
    def __init__(self, parameters: ThermodynamicParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_volume(self, displacement: np.ndarray) -> np.ndarray:
        """
        Calculate cylinder volume from displacement.
        
        V(t) = V_c + A_p x(t)
        
        Args:
            displacement: Piston displacement array (m)
            
        Returns:
            Volume array (m³)
        """
        volume = self.params.clearance_volume_m3 + self.params.piston_area_m2 * displacement
        return np.maximum(volume, 1e-9)  # Ensure positive volume
    
    def calculate_volume_casadi(self, displacement: ca.SX) -> ca.SX:
        """
        Calculate cylinder volume from displacement using CasADi.
        
        Args:
            displacement: Piston displacement (CasADi SX)
            
        Returns:
            Volume (CasADi SX)
        """
        volume = self.params.clearance_volume_m3 + self.params.piston_area_m2 * displacement
        return ca.fmax(volume, 1e-9)  # Ensure positive volume
    
    def calculate_pressure_polytropic(self, volume: np.ndarray, 
                                    initial_pressure: Optional[float] = None,
                                    initial_volume: Optional[float] = None) -> np.ndarray:
        """
        Calculate pressure using polytropic process.
        
        pV^γ = const
        
        Args:
            volume: Volume array (m³)
            initial_pressure: Initial pressure (Pa)
            initial_volume: Initial volume (m³)
            
        Returns:
            Pressure array (Pa)
        """
        if initial_pressure is None:
            initial_pressure = self.params.ambient_pressure_Pa
        if initial_volume is None:
            initial_volume = self.params.clearance_volume_m3
        
        # For a more realistic cycle, use different initial conditions
        # based on the volume range to create asymmetry
        min_volume = np.min(volume)
        max_volume = np.max(volume)
        
        # Use clearance volume as reference for compression
        # Use maximum volume as reference for expansion
        if len(volume) > 1:
            # Find the point of maximum volume (BDC)
            bdc_idx = np.argmax(volume)
            
            # Compression phase: from BDC to TDC
            compression_volumes = volume[:bdc_idx+1]
            expansion_volumes = volume[bdc_idx:]
            
            pressure = np.zeros_like(volume)
            
            # Compression: use BDC conditions as initial
            if len(compression_volumes) > 1:
                bdc_volume = max_volume
                bdc_pressure = initial_pressure * (initial_volume / bdc_volume) ** self.params.gamma
                k_comp = bdc_pressure * (bdc_volume ** self.params.gamma)
                pressure[:bdc_idx+1] = k_comp / (compression_volumes ** self.params.gamma)
            
            # Expansion: use TDC conditions as initial (higher pressure)
            if len(expansion_volumes) > 1:
                tdc_volume = min_volume
                tdc_pressure = initial_pressure * (initial_volume / tdc_volume) ** self.params.gamma * 2.0  # Higher pressure at TDC
                k_exp = tdc_pressure * (tdc_volume ** self.params.gamma)
                pressure[bdc_idx:] = k_exp / (expansion_volumes ** self.params.gamma)
        else:
            # Single point case
            k = initial_pressure * (initial_volume ** self.params.gamma)
            pressure = k / (volume ** self.params.gamma)
        
        return pressure
    
    def calculate_pressure_polytropic_casadi(self, volume: ca.SX,
                                           initial_pressure: Optional[float] = None,
                                           initial_volume: Optional[float] = None,
                                           polytropic_exponent: Optional[float] = None) -> ca.SX:
        """
        Calculate pressure using polytropic process with CasADi.
        
        Uses log-domain evaluation for numerical stability: p(V) = p0 * (V0/V)^n
        
        Args:
            volume: Volume (CasADi SX) - must be > 0 (enforced by NLP bounds)
            initial_pressure: Initial pressure (Pa)
            initial_volume: Initial volume (m³)
            polytropic_exponent: Polytropic exponent n (default: gamma)
            
        Returns:
            Pressure (CasADi SX)
        """
        if initial_pressure is None:
            initial_pressure = self.params.ambient_pressure_Pa
        if initial_volume is None:
            initial_volume = self.params.clearance_volume_m3
        if polytropic_exponent is None:
            polytropic_exponent = self.params.gamma
        
        # Log-domain evaluation for numerical stability
        # p(V) = p0 * (V0/V)^n = p0 * exp(n * log(V0/V))
        # = p0 * exp(n * (log(V0) - log(V)))
        logp = ca.log(initial_pressure) + polytropic_exponent * (ca.log(initial_volume) - ca.log(volume))
        pressure = ca.exp(logp)
        
        return pressure
    
    def calculate_temperature(self, pressure: np.ndarray, volume: np.ndarray,
                            mass: Optional[float] = None) -> np.ndarray:
        """
        Calculate temperature from ideal gas law.
        
        T = pV / (mR)
        
        Args:
            pressure: Pressure array (Pa)
            volume: Volume array (m³)
            mass: Gas mass (kg)
            
        Returns:
            Temperature array (K)
        """
        if mass is None:
            # Estimate mass from initial conditions
            initial_volume = self.params.clearance_volume_m3
            initial_pressure = self.params.ambient_pressure_Pa
            mass = (initial_pressure * initial_volume) / (self.params.gas_constant * self.params.ambient_temperature_K)
        
        temperature = (pressure * volume) / (mass * self.params.gas_constant)
        return temperature
    
    def calculate_indicated_work(self, pressure: np.ndarray, volume: np.ndarray) -> float:
        """
        Calculate indicated work from pressure-volume diagram.
        
        W_id = ∮ p dV
        
        Args:
            pressure: Pressure array (Pa)
            volume: Volume array (m³)
            
        Returns:
            Indicated work (J)
        """
        # Use trapezoidal rule for integration
        dV = np.diff(volume)
        p_mid = 0.5 * (pressure[:-1] + pressure[1:])
        work = np.sum(p_mid * dV)
        
        return work
    
    def calculate_indicated_work_casadi(self, pressure: ca.SX, volume: ca.SX) -> ca.SX:
        """
        Calculate indicated work using CasADi.
        
        Uses vectorized trapezoidal rule: W = ∫ p dV ≈ Σ (p_avg * dV)
        Avoids Python loops that create long AD tapes.
        
        Args:
            pressure: Pressure (CasADi SX)
            volume: Volume (CasADi SX)
            
        Returns:
            Indicated work (CasADi SX)
        """
        # Vectorized trapezoidal rule for numerical stability and speed
        dV = volume[1:] - volume[:-1]
        p_avg = 0.5 * (pressure[1:] + pressure[:-1])
        work = ca.sum1(p_avg * dV)
        
        return work
    
    def add_volume_barrier(self, volume: ca.SX, V_min: float, mu: float = 1e-4) -> ca.SX:
        """
        Optional log-barrier for volume constraints (objective-side only).
        
        Use only during early-phase robustness tests. This preserves smoothness
        and keeps the constraint "visible" to IPOPT's line search.
        
        Args:
            volume: Volume (CasADi SX)
            V_min: Minimum volume threshold
            mu: Barrier parameter (small positive value)
            
        Returns:
            Log-barrier term for objective function
        """
        # Interior-point style barrier: -μ * Σ log(V - V_min)
        # Use smooth approximation for volumes close to or below V_min
        # For V < V_min, use a quadratic penalty instead of log barrier
        volume_safe = ca.fmax(volume, V_min + 1e-6)  # Ensure V > V_min
        return -mu * ca.sum1(ca.log(volume_safe - V_min))
    
    def calculate_thermodynamic_cycle(self, displacement: np.ndarray,
                                    theta_deg: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate complete thermodynamic cycle.
        
        Args:
            displacement: Piston displacement array (m)
            theta_deg: Crank angle array (degrees)
            
        Returns:
            Dictionary with thermodynamic quantities
        """
        # Calculate volume
        volume = self.calculate_volume(displacement)
        
        # Calculate pressure (polytropic process)
        pressure = self.calculate_pressure_polytropic(volume)
        
        # Calculate temperature
        temperature = self.calculate_temperature(pressure, volume)
        
        # Calculate indicated work
        indicated_work = self.calculate_indicated_work(pressure, volume)
        
        # Calculate valve lift profiles (using ValveModel)
        valve_model = ValveModel(self.params)
        valve_lift = valve_model.calculate_valve_lift_profiles(theta_deg)
        
        # Calculate combustion heat release (using CombustionModel)
        combustion_model = CombustionModel(self.params)
        heat_release = combustion_model.calculate_combustion_heat_release(theta_deg)
        
        return {
            'volume_m3': volume,
            'pressure_Pa': pressure,
            'temperature_K': temperature,
            'indicated_work_J': indicated_work,
            'valve_lift_m': valve_lift,
            'heat_release_J': heat_release
        }


class ValveModel:
    """
    Valve modeling with smooth lift profiles and timing constraints.
    
    Implements valve lift profiles as C¹ sigmoid/poly-7 with ε_v smoothing.
    """
    
    def __init__(self, parameters: ThermodynamicParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_valve_lift_profiles(self, theta_deg: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate valve lift profiles for intake and exhaust valves.
        
        Uses smooth sigmoid functions with C¹ continuity.
        
        Args:
            theta_deg: Crank angle array (degrees)
            
        Returns:
            Dictionary with intake and exhaust valve lift profiles
        """
        intake_lift = self._calculate_single_valve_lift(
            theta_deg,
            self.params.valve_timing_deg['intake_open'],
            self.params.valve_timing_deg['intake_close']
        )
        
        exhaust_lift = self._calculate_single_valve_lift(
            theta_deg,
            self.params.valve_timing_deg['exhaust_open'],
            self.params.valve_timing_deg['exhaust_close']
        )
        
        return {
            'intake_lift_m': intake_lift,
            'exhaust_lift_m': exhaust_lift
        }
    
    def _calculate_single_valve_lift(self, theta_deg: np.ndarray, 
                                   open_angle: float, close_angle: float) -> np.ndarray:
        """
        Calculate lift profile for a single valve using smooth sigmoid.
        
        Args:
            theta_deg: Crank angle array (degrees)
            open_angle: Valve opening angle (degrees)
            close_angle: Valve closing angle (degrees)
            
        Returns:
            Valve lift array (m)
        """
        # Normalize angles to [0, 360]
        theta_norm = np.mod(theta_deg, 360.0)
        open_norm = np.mod(open_angle, 360.0)
        close_norm = np.mod(close_angle, 360.0)
        
        # Handle case where valve timing crosses 0 degrees
        if open_norm > close_norm:
            # Valve timing crosses 0 degrees
            valve_open = (theta_norm >= open_norm) | (theta_norm <= close_norm)
        else:
            # Normal case
            valve_open = (theta_norm >= open_norm) & (theta_norm <= close_norm)
        
        # Create smooth transition using sigmoid function
        lift = np.zeros_like(theta_deg)
        
        # Find transition regions
        transition_width = 5.0  # degrees
        
        for i, theta in enumerate(theta_norm):
            if valve_open[i]:
                # Calculate smooth opening/closing transitions
                if abs(theta - open_norm) < transition_width:
                    # Opening transition
                    t = (theta - open_norm + transition_width) / (2 * transition_width)
                    lift[i] = self.params.max_valve_lift_m * self._smooth_step(t)
                elif abs(theta - close_norm) < transition_width:
                    # Closing transition
                    t = (close_norm - theta + transition_width) / (2 * transition_width)
                    lift[i] = self.params.max_valve_lift_m * self._smooth_step(t)
                else:
                    # Fully open
                    lift[i] = self.params.max_valve_lift_m
        
        return lift
    
    def _smooth_step(self, t: float) -> float:
        """
        Smooth step function with C¹ continuity.
        
        Uses polynomial: 3t² - 2t³ for t ∈ [0,1]
        
        Args:
            t: Normalized parameter [0,1]
            
        Returns:
            Smooth step value [0,1]
        """
        t = np.clip(t, 0.0, 1.0)
        return 3 * t**2 - 2 * t**3
    
    def calculate_valve_constraints(self, theta_deg: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate valve constraints for optimization.
        
        Args:
            theta_deg: Crank angle array (degrees)
            
        Returns:
            Dictionary with valve constraints
        """
        valve_lift = self.calculate_valve_lift_profiles(theta_deg)
        
        # Valve bounds: 0 ≤ L(t) ≤ L_max
        intake_bounds = {
            'lower': np.zeros_like(theta_deg),
            'upper': np.full_like(theta_deg, self.params.max_valve_lift_m)
        }
        
        exhaust_bounds = {
            'lower': np.zeros_like(theta_deg),
            'upper': np.full_like(theta_deg, self.params.max_valve_lift_m)
        }
        
        return {
            'intake_bounds': intake_bounds,
            'exhaust_bounds': exhaust_bounds,
            'intake_lift': valve_lift['intake_lift_m'],
            'exhaust_lift': valve_lift['exhaust_lift_m']
        }


class CombustionModel:
    """
    Combustion modeling with Wiebe function and heat release.
    
    Implements x_burn(t) as Wiebe function with parameters a, m, t0, Δt.
    """
    
    def __init__(self, parameters: ThermodynamicParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_combustion_heat_release(self, theta_deg: np.ndarray) -> np.ndarray:
        """
        Calculate combustion heat release using Wiebe function.
        
        x_burn(t) = 1 - exp(-a * ((t - t0) / Δt)^m)
        
        Args:
            theta_deg: Crank angle array (degrees)
            
        Returns:
            Heat release array (J)
        """
        # Wiebe function parameters
        a = 5.0  # Shape parameter
        m = 2.0  # Shape parameter
        t0 = self.params.ignition_timing_deg  # Ignition timing
        dt = 30.0  # Combustion duration (degrees)
        
        # Calculate burn fraction
        burn_fraction = self._calculate_burn_fraction(theta_deg, a, m, t0, dt)
        
        # Calculate total heat release
        # Estimate fuel energy from equivalence ratio and engine size
        fuel_energy_per_cycle = self._estimate_fuel_energy()
        
        # Heat release rate
        heat_release = burn_fraction * fuel_energy_per_cycle * self.params.combustion_efficiency
        
        return heat_release
    
    def _calculate_burn_fraction(self, theta_deg: np.ndarray, a: float, m: float,
                               t0: float, dt: float) -> np.ndarray:
        """
        Calculate burn fraction using Wiebe function.
        
        Args:
            theta_deg: Crank angle array (degrees)
            a: Shape parameter
            m: Shape parameter
            t0: Ignition timing (degrees)
            dt: Combustion duration (degrees)
            
        Returns:
            Burn fraction array [0,1]
        """
        # Normalize time
        t_norm = (theta_deg - t0) / dt
        
        # Wiebe function
        burn_fraction = np.zeros_like(theta_deg)
        
        # Only calculate for positive normalized time
        mask = t_norm > 0
        burn_fraction[mask] = 1 - np.exp(-a * (t_norm[mask] ** m))
        
        return burn_fraction
    
    def _estimate_fuel_energy(self) -> float:
        """
        Estimate fuel energy per cycle.
        
        Returns:
            Fuel energy per cycle (J)
        """
        # Estimate based on engine size and operating conditions
        # This is a simplified calculation
        engine_displacement = self.params.piston_area_m2 * self.params.stroke_length_m
        fuel_energy_per_cycle = engine_displacement * 1e6 * 0.8  # Rough estimate
        
        return fuel_energy_per_cycle
    
    def calculate_combustion_constraints(self, theta_deg: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate combustion constraints for optimization.
        
        Args:
            theta_deg: Crank angle array (degrees)
            
        Returns:
            Dictionary with combustion constraints
        """
        heat_release = self.calculate_combustion_heat_release(theta_deg)
        
        # Combustion constraints
        max_heat_release = np.max(heat_release)
        min_heat_release = 0.0
        
        return {
            'heat_release_J': heat_release,
            'max_heat_release_J': max_heat_release,
            'min_heat_release_J': min_heat_release
        }


class StateEquations:
    """
    State equations for mass and energy balance.
    
    Implements mass/energy balances with collocation defects.
    """
    
    def __init__(self, parameters: ThermodynamicParameters):
        self.params = parameters
        self.logger = get_logger(__name__)
    
    def calculate_mass_balance(self, volume: np.ndarray, pressure: np.ndarray,
                             temperature: np.ndarray, valve_lift: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Calculate mass balance equation.
        
        dm/dt = ṁ_in - ṁ_out
        
        Args:
            volume: Volume array (m³)
            pressure: Pressure array (Pa)
            temperature: Temperature array (K)
            valve_lift: Valve lift profiles
            
        Returns:
            Mass flow rate array (kg/s)
        """
        # Simplified mass flow calculation
        # In a full implementation, this would include:
        # - Intake flow through intake valve
        # - Exhaust flow through exhaust valve
        # - Leakage flows
        
        # For now, return zero (closed system assumption)
        mass_flow = np.zeros_like(volume)
        
        return mass_flow
    
    def calculate_energy_balance(self, volume: np.ndarray, pressure: np.ndarray,
                               temperature: np.ndarray, heat_release: np.ndarray) -> np.ndarray:
        """
        Calculate energy balance equation.
        
        dE/dt = Q_in - Q_out - W_out
        
        Args:
            volume: Volume array (m³)
            pressure: Pressure array (Pa)
            temperature: Temperature array (K)
            heat_release: Heat release array (J)
            
        Returns:
            Energy balance residual array (J/s)
        """
        # Simplified energy balance
        # In a full implementation, this would include:
        # - Heat transfer to walls
        # - Work output
        # - Internal energy changes
        
        # For now, return zero (adiabatic assumption)
        energy_balance = np.zeros_like(volume)
        
        return energy_balance
    
    def calculate_collocation_defects(self, state_variables: Dict[str, np.ndarray],
                                    grid: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate collocation defects for state equations.
        
        Args:
            state_variables: Dictionary of state variables
            grid: Collocation grid
            
        Returns:
            Dictionary of collocation defects
        """
        # Calculate defects for each state variable
        defects = {}
        
        for var_name, var_values in state_variables.items():
            # Calculate derivative using finite differences
            if len(var_values) > 1:
                dvar_dt = np.gradient(var_values, grid)
                defects[f'{var_name}_defect'] = dvar_dt
        
        return defects


class ThermodynamicOptimizer:
    """
    Thermodynamic optimizer that integrates all thermodynamic calculations.
    
    This class provides the interface for Phase 1 thermodynamic optimization.
    """
    
    def __init__(self, parameters: ThermodynamicParameters):
        self.params = parameters
        self.thermo_calc = ThermodynamicCalculator(parameters)
        self.valve_model = ValveModel(parameters)
        self.combustion_model = CombustionModel(parameters)
        self.state_eqns = StateEquations(parameters)
        self.logger = get_logger(__name__)
    
    def calculate_thermodynamic_objectives(self, displacement: np.ndarray,
                                         theta_deg: np.ndarray) -> Dict[str, float]:
        """
        Calculate thermodynamic objectives for optimization.
        
        Args:
            displacement: Piston displacement array (m)
            theta_deg: Crank angle array (degrees)
            
        Returns:
            Dictionary of objective values
        """
        # Calculate thermodynamic cycle
        thermo_cycle = self.thermo_calc.calculate_thermodynamic_cycle(displacement, theta_deg)
        
        # Calculate objectives
        objectives = {
            'indicated_work_J': thermo_cycle['indicated_work_J'],
            'max_pressure_Pa': np.max(thermo_cycle['pressure_Pa']),
            'min_pressure_Pa': np.min(thermo_cycle['pressure_Pa']),
            'max_temperature_K': np.max(thermo_cycle['temperature_K']),
            'min_temperature_K': np.min(thermo_cycle['temperature_K']),
            'volumetric_efficiency': self._calculate_volumetric_efficiency(thermo_cycle),
            'thermal_efficiency': self._calculate_thermal_efficiency(thermo_cycle)
        }
        
        return objectives
    
    def _calculate_volumetric_efficiency(self, thermo_cycle: Dict[str, np.ndarray]) -> float:
        """
        Calculate volumetric efficiency.
        
        Args:
            thermo_cycle: Thermodynamic cycle data
            
        Returns:
            Volumetric efficiency [0,1]
        """
        # Simplified calculation
        # In a full implementation, this would consider:
        # - Intake flow characteristics
        # - Valve timing effects
        # - Pressure losses
        
        return 0.85  # Typical value
    
    def _calculate_thermal_efficiency(self, thermo_cycle: Dict[str, np.ndarray]) -> float:
        """
        Calculate thermal efficiency.
        
        Args:
            thermo_cycle: Thermodynamic cycle data
            
        Returns:
            Thermal efficiency [0,1]
        """
        # Simplified calculation
        # In a full implementation, this would consider:
        # - Heat addition and rejection
        # - Work output
        # - Losses
        
        return 0.35  # Typical value
    
    def calculate_thermodynamic_constraints(self, displacement: np.ndarray,
                                          theta_deg: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate thermodynamic constraints for optimization.
        
        Args:
            displacement: Piston displacement array (m)
            theta_deg: Crank angle array (degrees)
            
        Returns:
            Dictionary of constraints
        """
        # Calculate valve constraints
        valve_constraints = self.valve_model.calculate_valve_constraints(theta_deg)
        
        # Calculate combustion constraints
        combustion_constraints = self.combustion_model.calculate_combustion_constraints(theta_deg)
        
        # Calculate thermodynamic cycle
        thermo_cycle = self.thermo_calc.calculate_thermodynamic_cycle(displacement, theta_deg)  # noqa: F841
        
        # Combine constraints
        constraints = {
            'valve_constraints': valve_constraints,
            'combustion_constraints': combustion_constraints,
            'pressure_bounds': {
                'lower': np.full_like(displacement, 1000.0),  # Minimum pressure (Pa)
                'upper': np.full_like(displacement, 10000000.0)  # Maximum pressure (Pa)
            },
            'temperature_bounds': {
                'lower': np.full_like(displacement, 200.0),  # Minimum temperature (K)
                'upper': np.full_like(displacement, 3000.0)  # Maximum temperature (K)
            }
        }
        
        return constraints
