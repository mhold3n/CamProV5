"""
Optimization module for CamProV5.

This module contains extracted optimization components including collocation
solvers and gear optimization methods.
"""

from .collocation_optimizer import CollocationOptimizer, CollocationParameters, CollocationSolution

__all__ = ['CollocationOptimizer', 'CollocationParameters', 'CollocationSolution']
