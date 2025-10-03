"""
CamProV5 Optimization Solvers

This module provides advanced optimization solvers for cam profile generation,
including enhanced methods with real physics and proper constraint handling.
"""

from .nlp_formulation import MotionNLP, ConstraintBuilder
from .numerical_methods import NumericalGuards, NumericalParameters
from .discretization import CollocationGrid
from .validation import DenseValidator, ValidationLimits, ValidationResult
from .robust_gear_design import RobustGearDesign

__all__ = [
    'MotionNLP', 'ConstraintBuilder',
    'NumericalGuards', 'NumericalParameters',
    'CollocationGrid',
    'DenseValidator', 'ValidationLimits', 'ValidationResult',
    'RobustGearDesign'
]
