"""
Optimization module for CamProV5.

This module contains the enhanced optimization components implementing the unified
specification with real physics and advanced solvers.
"""

from .enhanced_motion_law_optimizer import (
    EnhancedMotionLawOptimizer, 
    EnhancedMotionLawParameters
)
from .enhanced_gear_optimizer import (
    EnhancedGearOptimizer, 
    EnhancedGearParameters
)
from .phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters, Phase2Solution
from .multi_objective import AugmentedTchebyshevScalarizer
from .bspline_motion_law import BSplineMotionLaw, BSplineMotionLawOptimizer
from .solver_improvements import SolverImprovements

__all__ = [
    'EnhancedMotionLawOptimizer', 
    'EnhancedMotionLawParameters',
    'EnhancedGearOptimizer', 
    'EnhancedGearParameters',
    'Phase2GearOptimizer', 
    'Phase2Parameters', 
    'Phase2Solution',
    'AugmentedTchebyshevScalarizer',
    'BSplineMotionLaw', 
    'BSplineMotionLawOptimizer',
    'SolverImprovements'
]
