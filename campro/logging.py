"""
Standardized logging for CamProV5.

This module provides a standardized logging interface for all CamProV5 modules.
It ensures consistent logging configuration and follows the project's logging standards.
"""

from campro.utils.logging import get_logger

# Re-export the get_logger function for easy access
__all__ = ['get_logger']
