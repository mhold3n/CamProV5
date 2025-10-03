"""
NLP metadata and block layout definitions for CamPro V5 optimization.

This module defines explicit block layouts and slices for each stage to enable
robust x₀ transfer between different NLP formulations.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
import numpy as np


@dataclass
class BlockSlices:
    """Block layout and slice information for NLP decision variables."""
    
    # mapping: block_name -> slice indices in the flat decision vector
    slices: Dict[str, slice]
    
    # (optional) per-block shape info for remeshing/interpolation
    shapes: Dict[str, Tuple[int, ...]]  # e.g., ("disp": (N,), "vel": (N,), "u": (N-1,))
    
    def get_block_data(self, x: np.ndarray, block_name: str) -> np.ndarray:
        """Extract block data from flat decision vector."""
        if block_name not in self.slices:
            raise KeyError(f"Block '{block_name}' not found in slices")
        return x[self.slices[block_name]]
    
    def set_block_data(self, x: np.ndarray, block_name: str, data: np.ndarray) -> None:
        """Set block data in flat decision vector."""
        if block_name not in self.slices:
            raise KeyError(f"Block '{block_name}' not found in slices")
        x[self.slices[block_name]] = data


def create_motion_law_block_slices(n: int) -> BlockSlices:
    """Create block slices for motion law optimization.
    
    Variable ordering: displacement (n) + velocity (n-1) + acceleration (n-2)
    """
    slices = {}
    shapes = {}
    
    # Displacement block: indices 0 to n-1
    slices['disp'] = slice(0, n)
    shapes['disp'] = (n,)
    
    # Velocity block: indices n to 2n-2
    slices['vel'] = slice(n, 2*n-1)
    shapes['vel'] = (n-1,)
    
    # Acceleration block: indices 2n-1 to 3n-3
    slices['acc'] = slice(2*n-1, 3*n-2)
    shapes['acc'] = (n-2,)
    
    return BlockSlices(slices=slices, shapes=shapes)


def create_gear_optimization_block_slices(n: int) -> BlockSlices:
    """Create block slices for gear optimization.
    
    Variable ordering: sun_radius (n) + planet_radius (n) + ring_radius (n) + 
                      gear_ratio (n) + journal_offset (n)
    """
    slices = {}
    shapes = {}
    
    # Each block has n variables
    slices['sun_radius'] = slice(0, n)
    shapes['sun_radius'] = (n,)
    
    slices['planet_radius'] = slice(n, 2*n)
    shapes['planet_radius'] = (n,)
    
    slices['ring_radius'] = slice(2*n, 3*n)
    shapes['ring_radius'] = (n,)
    
    slices['gear_ratio'] = slice(3*n, 4*n)
    shapes['gear_ratio'] = (n,)
    
    slices['journal_offset'] = slice(4*n, 5*n)
    shapes['journal_offset'] = (n,)
    
    return BlockSlices(slices=slices, shapes=shapes)


def create_enhanced_gear_block_slices(n: int) -> BlockSlices:
    """Create block slices for enhanced gear optimization.
    
    Variable ordering: sun_radius (n) + planet_radius (n) + ring_radius (n) + 
                      gear_ratio (n) + journal_offset (n)
    """
    # Same structure as basic gear optimization
    return create_gear_optimization_block_slices(n)
