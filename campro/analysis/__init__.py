"""
Analysis module for CamProV5.

This module provides analysis capabilities including FEA (Finite Element Analysis)
integration with the Rust engine.
"""

from .fea_analyzer import FEAAnalyzer
from .rust_engine_wrapper import RustEngineWrapper

__all__ = ['FEAAnalyzer', 'RustEngineWrapper']
