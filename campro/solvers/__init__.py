"""
CamProV5 Optimization Solvers

This module provides advanced optimization solvers for cam profile generation,
including collocation-based methods using CasADi + IPOPT.
"""

from .collocation_solver import CollocationSolver, CollocationParameters, CollocationSolution
from .nlp_formulation import MotionNLP, ConstraintBuilder
from .litvin_constraints import LitvinConstraintBuilder, LitvinParameters
from .numerical_methods import NumericalGuards, NumericalParameters
from .discretization import CollocationGrid

__all__ = [
    'CollocationSolver', 'CollocationParameters', 'CollocationSolution',
    'MotionNLP', 'ConstraintBuilder',
    'LitvinConstraintBuilder', 'LitvinParameters',
    'NumericalGuards', 'NumericalParameters',
    'CollocationGrid'
]
