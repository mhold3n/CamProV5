"""
Numerical Methods and Guards for Robust NLP Optimization

This module provides advanced numerical techniques for robust and efficient
solution of the collocation NLP, including KS aggregation, smooth bound maps,
continuation strategies, and warm-start generation.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    import casadi as ca
    CASADI_AVAILABLE = True
except ImportError:
    CASADI_AVAILABLE = False

import logging

logger = logging.getLogger(__name__)


@dataclass
class NumericalParameters:
    """Parameters for numerical methods and guards."""
    
    # KS aggregation parameters
    ks_rho: float = 10.0  # KS aggregation parameter (higher = tighter)
    ks_smooth_factor: float = 1e-3  # Smoothing factor for KS
    
    # Bound mapping parameters
    bound_margin: float = 1e-6  # Margin for bound enforcement
    bound_smoothness: float = 1e-2  # Smoothness parameter for bound maps
    
    # Continuation parameters
    continuation_steps: int = 3  # Number of continuation steps
    continuation_factor: float = 0.1  # Relaxation factor for first step
    
    # Warm-start parameters
    warm_start_noise: float = 1e-3  # Noise level for warm-start perturbation
    warm_start_damping: float = 0.8  # Damping factor for warm-start


class KSAggregator:
    """
    Kreisselmeier-Steinhauser (KS) aggregation for smooth constraint handling.
    
    The KS function provides a smooth approximation to max/min functions,
    allowing gradient-based optimizers to handle inequality constraints
    more robustly than exact max/min formulations.
    """
    
    def __init__(self, rho: float = 10.0):
        """Initialize KS aggregator."""
        self.rho = rho
        
    def ks_max(self, expressions: List['ca.SX']) -> 'ca.SX':
        """
        Compute smooth maximum using KS aggregation.
        
        KS_max(x) ≈ max(x) = (1/ρ) * log(Σ exp(ρ * x_i))
        
        Args:
            expressions: List of CasADi expressions
            
        Returns:
            CasADi expression for smooth maximum
        """
        if not CASADI_AVAILABLE:
            raise ImportError("CasADi is required for KS aggregation")
        
        if not expressions:
            return ca.DM(0.0)
        
        if len(expressions) == 1:
            return expressions[0]
        
        # Stack expressions and apply KS formula
        x_stack = ca.vertcat(*expressions)
        return (1.0 / self.rho) * ca.log(ca.sum1(ca.exp(self.rho * x_stack)))
    
    def ks_min(self, expressions: List['ca.SX']) -> 'ca.SX':
        """
        Compute smooth minimum using KS aggregation.
        
        KS_min(x) ≈ min(x) = -(1/ρ) * log(Σ exp(-ρ * x_i))
        """
        if not expressions:
            return ca.DM(0.0)
        
        # Convert to negative and use ks_max
        neg_expressions = [-expr for expr in expressions]
        return -self.ks_max(neg_expressions)
    
    def constraint_violation(self, constraints: List['ca.SX'], bounds_upper: List[float]) -> 'ca.SX':
        """
        Compute aggregate constraint violation using KS.
        
        This provides a single scalar measure of constraint violation
        that can be used in penalty methods or for monitoring convergence.
        
        Args:
            constraints: List of constraint expressions
            bounds_upper: Upper bounds for constraints
            
        Returns:
            Smooth aggregate constraint violation
        """
        if not constraints:
            return ca.DM(0.0)
        
        # Compute violations: max(0, g_i - b_i)
        violations = []
        for g, b in zip(constraints, bounds_upper):
            violation = ca.fmax(0.0, g - b)
            violations.append(violation)
        
        return self.ks_max(violations)


class SmoothBoundMap:
    """
    Smooth bound mapping for converting bounded variables to unbounded.
    
    This allows the optimizer to work with unbounded variables while
    ensuring the original variables stay within their bounds.
    """
    
    def __init__(self, smoothness: float = 1e-2):
        """Initialize smooth bound mapper."""
        self.smoothness = smoothness
    
    def map_to_unbounded(self, x: 'ca.SX', lower: float, upper: float) -> 'ca.SX':
        """
        Map bounded variable to unbounded using smooth transformation.
        
        Uses a smooth sigmoid-like transformation:
        y = atanh(2*(x - lower)/(upper - lower) - 1)
        
        Args:
            x: Bounded variable in [lower, upper]
            lower: Lower bound
            upper: Upper bound
            
        Returns:
            Unbounded variable y
        """
        if not CASADI_AVAILABLE:
            raise ImportError("CasADi is required for bound mapping")
        
        if abs(upper - lower) < 1e-12:
            # Degenerate case: bounds are equal
            return ca.DM(0.0)
        
        # Normalize to [0, 1]
        x_norm = (x - lower) / (upper - lower)
        
        # Map to [-1 + ε, 1 - ε] to avoid atanh singularities
        eps = self.smoothness
        x_scaled = (1.0 - 2*eps) * x_norm + eps
        
        # Apply inverse hyperbolic tangent
        return ca.atanh(2.0 * x_scaled - 1.0)
    
    def map_from_unbounded(self, y: 'ca.SX', lower: float, upper: float) -> 'ca.SX':
        """
        Map unbounded variable back to bounded domain.
        
        Inverse of map_to_unbounded:
        x = lower + (upper - lower) * (tanh(y) + 1) / 2
        
        Args:
            y: Unbounded variable
            lower: Lower bound for x
            upper: Upper bound for x
            
        Returns:
            Bounded variable x in [lower, upper]
        """
        if abs(upper - lower) < 1e-12:
            return ca.DM((lower + upper) / 2.0)
        
        # Apply hyperbolic tangent and scale back
        x_scaled = (ca.tanh(y) + 1.0) / 2.0
        
        # Remove smoothness margin and scale to [lower, upper]
        eps = self.smoothness
        x_norm = (x_scaled - eps) / (1.0 - 2*eps)
        
        return lower + (upper - lower) * x_norm


class ContinuationStrategy:
    """
    Continuation method for robust NLP solution.
    
    Gradually increases constraint strictness and problem difficulty
    to guide the optimizer to a good solution.
    """
    
    def __init__(self, steps: int = 3, initial_factor: float = 0.1):
        """Initialize continuation strategy."""
        self.steps = steps
        self.initial_factor = initial_factor
        
    def generate_continuation_sequence(self) -> List[float]:
        """
        Generate sequence of continuation parameters.
        
        Returns:
            List of factors from initial_factor to 1.0
        """
        if self.steps <= 1:
            return [1.0]
        
        factors = []
        for i in range(self.steps):
            # Exponential interpolation from initial_factor to 1.0
            t = i / (self.steps - 1)
            factor = self.initial_factor * (1.0 / self.initial_factor) ** t
            factors.append(factor)
        
        return factors
    
    def relax_constraints(self, constraints: List['ca.SX'], bounds_upper: List[float], 
                         factor: float) -> List[float]:
        """
        Relax constraint bounds by continuation factor.
        
        Args:
            constraints: List of constraint expressions
            bounds_upper: Original upper bounds
            factor: Relaxation factor (0 = fully relaxed, 1 = original)
            
        Returns:
            Relaxed upper bounds
        """
        relaxed_bounds = []
        for bound in bounds_upper:
            if bound < float('inf'):
                # Relax finite bounds
                relaxed_bound = bound + (1.0 - factor) * abs(bound)
                relaxed_bounds.append(relaxed_bound)
            else:
                # Keep infinite bounds unchanged
                relaxed_bounds.append(bound)
        
        return relaxed_bounds
    
    def adjust_regularization(self, base_weight: float, factor: float) -> float:
        """
        Adjust regularization weight based on continuation factor.
        
        Early continuation steps use higher regularization for stability.
        """
        # Increase regularization for early steps
        regularization_boost = 1.0 + 10.0 * (1.0 - factor)
        return base_weight * regularization_boost


class WarmStartGenerator:
    """
    Generates good initial guesses for NLP optimization.
    
    Combines analytical estimates with noise to provide diverse
    starting points for the optimizer.
    """
    
    def __init__(self, noise_level: float = 1e-3, damping: float = 0.8):
        """Initialize warm-start generator."""
        self.noise_level = noise_level
        self.damping = damping
    
    def generate_sinusoidal_start(self, grid_nodes: np.ndarray, stroke_length: float,
                                motion_params: Dict[str, Any]) -> np.ndarray:
        """
        Generate sinusoidal warm start with motion-specific adjustments.
        
        Args:
            grid_nodes: Collocation nodes in [0, 2π]
            stroke_length: Stroke length in mm
            motion_params: Motion parameters for adjustments
            
        Returns:
            Initial guess for position variables
        """
        # Base sinusoidal motion
        base_motion = stroke_length / 2.0 * (1.0 - np.cos(grid_nodes))
        
        # Add dwell adjustments
        dwell_tdc_rad = motion_params.get('dwellTdcDeg', 0.0) * np.pi / 180.0
        dwell_bdc_rad = motion_params.get('dwellBdcDeg', 0.0) * np.pi / 180.0
        
        adjusted_motion = base_motion.copy()
        
        # Flatten motion during dwells
        if dwell_tdc_rad > 0:
            tdc_mask = grid_nodes <= dwell_tdc_rad
            adjusted_motion[tdc_mask] = 0.0
        
        if dwell_bdc_rad > 0:
            bdc_start = np.pi - dwell_bdc_rad / 2.0
            bdc_end = np.pi + dwell_bdc_rad / 2.0
            bdc_mask = (grid_nodes >= bdc_start) & (grid_nodes <= bdc_end)
            adjusted_motion[bdc_mask] = stroke_length
        
        # Add controlled noise for robustness
        noise = np.random.normal(0, self.noise_level * stroke_length, len(grid_nodes))
        noisy_motion = adjusted_motion + noise
        
        # Apply damping to reduce extreme values
        return self.damping * noisy_motion + (1.0 - self.damping) * base_motion
    
    def generate_piecewise_start(self, grid_nodes: np.ndarray, stroke_length: float,
                               motion_params: Dict[str, Any]) -> np.ndarray:
        """
        Generate warm start based on piecewise motion law.
        
        This uses the existing piecewise motion law as a starting point,
        which should be close to the desired solution.
        """
        # For now, fall back to sinusoidal with better parameters
        return self.generate_sinusoidal_start(grid_nodes, stroke_length, motion_params)
    
    def perturb_solution(self, solution: np.ndarray, perturbation_factor: float = 0.05) -> np.ndarray:
        """
        Perturb an existing solution for multiple optimization attempts.
        
        Args:
            solution: Previous solution
            perturbation_factor: Relative perturbation strength
            
        Returns:
            Perturbed solution
        """
        noise = np.random.normal(0, perturbation_factor, len(solution))
        return solution + noise * np.std(solution)


class NumericalGuards:
    """
    Collection of numerical methods for robust NLP optimization.
    
    This class combines KS aggregation, bound mapping, continuation,
    and warm-start generation into a unified interface.
    """
    
    def __init__(self, params: Optional[NumericalParameters] = None):
        """Initialize numerical guards."""
        self.params = params or NumericalParameters()
        
        self.ks_aggregator = KSAggregator(rho=self.params.ks_rho)
        self.bound_mapper = SmoothBoundMap(smoothness=self.params.bound_smoothness)
        self.continuation = ContinuationStrategy(
            steps=self.params.continuation_steps,
            initial_factor=self.params.continuation_factor
        )
        self.warm_start = WarmStartGenerator(
            noise_level=self.params.warm_start_noise,
            damping=self.params.warm_start_damping
        )
    
    def setup_robust_solver_options(self, base_options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance solver options with numerical guards.
        
        Args:
            base_options: Base IPOPT options
            
        Returns:
            Enhanced solver options
        """
        robust_options = base_options.copy()
        
        # IPOPT-specific robustness settings
        robust_options.update({
            # Barrier parameter strategy
            'ipopt.mu_strategy': 'adaptive',
            'ipopt.mu_init': 1e-1,
            'ipopt.mu_min': 1e-12,
            
            # Line search robustness
            'ipopt.alpha_for_y': 'primal',
            'ipopt.recalc_y': 'yes',
            'ipopt.recalc_y_feas_tol': 1e-6,
            
            # Hessian regularization
            'ipopt.jacobian_regularization_value': 1e-8,
            'ipopt.jacobian_regularization_exponent': 0.25,
            
            # Watchdog for robustness
            'ipopt.watchdog_shortened_iter_trigger': 10,
            'ipopt.watchdog_trial_iter_max': 3,
            
            # Adaptive bounds
            'ipopt.bound_relax_factor': 1e-8,
            'ipopt.honor_original_bounds': 'yes'
        })
        
        return robust_options
    
    def get_methods_info(self) -> Dict[str, Any]:
        """Get information about active numerical methods."""
        return {
            "ks_aggregation": {
                "rho": self.params.ks_rho,
                "smooth_factor": self.params.ks_smooth_factor
            },
            "bound_mapping": {
                "margin": self.params.bound_margin,
                "smoothness": self.params.bound_smoothness
            },
            "continuation": {
                "steps": self.params.continuation_steps,
                "initial_factor": self.params.continuation_factor,
                "sequence": self.continuation.generate_continuation_sequence()
            },
            "warm_start": {
                "noise_level": self.params.warm_start_noise,
                "damping": self.params.warm_start_damping
            }
        }
