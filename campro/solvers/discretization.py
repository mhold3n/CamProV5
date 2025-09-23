"""
Collocation Discretization Components

This module provides the discretization infrastructure for collocation methods,
including node generation and differentiation matrices.
"""

import numpy as np
from typing import Tuple, Union
from scipy.special import legendre
from scipy.linalg import solve

import logging

logger = logging.getLogger(__name__)


# Global cache for collocation matrices
_MATRIX_CACHE = {}
_CACHE_HITS = 0
_CACHE_MISSES = 0


def get_cache_stats():
    """Get cache performance statistics."""
    total = _CACHE_HITS + _CACHE_MISSES
    hit_rate = _CACHE_HITS / total if total > 0 else 0.0
    return {
        'hits': _CACHE_HITS,
        'misses': _CACHE_MISSES,
        'hit_rate': hit_rate,
        'cached_entries': len(_MATRIX_CACHE)
    }


def clear_matrix_cache():
    """Clear the matrix cache."""
    global _MATRIX_CACHE, _CACHE_HITS, _CACHE_MISSES
    _MATRIX_CACHE.clear()
    _CACHE_HITS = 0
    _CACHE_MISSES = 0


class CollocationGrid:
    """
    Collocation grid with nodes and differentiation matrices.
    
    This class handles the discretization of the periodic domain [0, 2π]
    using various node distributions and provides differentiation matrices
    for computing derivatives at collocation points.
    """
    
    def __init__(self, node_count: int, node_type: str = "LGL"):
        """
        Initialize collocation grid.
        
        Args:
            node_count: Number of collocation nodes
            node_type: Type of nodes ("LGL", "Chebyshev", "Uniform")
        """
        self.node_count = node_count
        self.node_type = node_type
        
        # Generate nodes
        self.nodes = self._generate_nodes()
        
        # Compute differentiation matrices (with caching)
        self.differentiation_matrix = self._get_cached_differentiation_matrix()
        self.second_derivative_matrix = self._get_cached_second_derivative_matrix()
        
        logger.debug(f"Created {node_type} grid with {node_count} nodes")
    
    def _generate_nodes(self) -> np.ndarray:
        """Generate collocation nodes based on the specified type."""
        if self.node_type == "LGL":
            return self._generate_lgl_nodes()
        elif self.node_type == "Chebyshev":
            return self._generate_chebyshev_nodes()
        elif self.node_type == "Uniform":
            return self._generate_uniform_nodes()
        else:
            raise ValueError(f"Unknown node type: {self.node_type}")
    
    def _generate_lgl_nodes(self) -> np.ndarray:
        """Generate Legendre-Gauss-Lobatto nodes mapped to [0, 2π]."""
        if self.node_count < 3:
            raise ValueError("Need at least 3 nodes for LGL")
        
        # For periodic problems, use Fourier nodes for now
        # TODO: Implement proper periodic LGL nodes
        return self._generate_uniform_nodes()
    
    def _generate_chebyshev_nodes(self) -> np.ndarray:
        """Generate Chebyshev nodes mapped to [0, 2π]."""
        if self.node_count < 3:
            raise ValueError("Need at least 3 nodes for Chebyshev")
        
        # Chebyshev nodes on [-1, 1]
        k = np.arange(self.node_count)
        chebyshev_nodes = np.cos((2 * k + 1) * np.pi / (2 * self.node_count))
        
        # Map to [0, 2π] and sort
        nodes = np.pi * (chebyshev_nodes + 1.0)
        return np.sort(nodes)
    
    def _generate_uniform_nodes(self) -> np.ndarray:
        """Generate uniformly spaced nodes in [0, 2π)."""
        return np.linspace(0, 2 * np.pi, self.node_count, endpoint=False)
    
    def _compute_differentiation_matrix(self) -> np.ndarray:
        """Compute the differentiation matrix for the collocation nodes."""
        if self.node_type == "Uniform":
            return self._fourier_differentiation_matrix()
        else:
            return self._lagrange_differentiation_matrix()
    
    def _fourier_differentiation_matrix(self) -> np.ndarray:
        """Compute differentiation matrix using Fourier spectral method."""
        n = self.node_count
        D = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    D[i, j] = 0.5 * (-1)**(i-j) / np.tan(np.pi * (i - j) / n)
                # Diagonal elements are zero for periodic functions
        
        return D
    
    def _lagrange_differentiation_matrix(self) -> np.ndarray:
        """Compute differentiation matrix using Lagrange interpolation."""
        n = self.node_count
        D = np.zeros((n, n))
        nodes = self.nodes
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Off-diagonal elements
                    numerator = 1.0
                    denominator = 1.0
                    
                    for k in range(n):
                        if k != i and k != j:
                            numerator *= (nodes[i] - nodes[k])
                            denominator *= (nodes[j] - nodes[k])
                    
                    D[i, j] = (numerator / denominator) / (nodes[i] - nodes[j])
                else:
                    # Diagonal elements: negative sum of off-diagonal elements
                    D[i, i] = -np.sum([D[i, k] for k in range(n) if k != i])
        
        return D
    
    def interpolate_to_uniform_grid(self, values: np.ndarray, target_step_deg: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Interpolate values from collocation nodes to uniform grid.
        
        Args:
            values: Function values at collocation nodes
            target_step_deg: Step size in degrees for target grid
            
        Returns:
            Tuple of (uniform_nodes, interpolated_values)
        """
        # Create uniform target grid
        target_step_rad = target_step_deg * np.pi / 180.0
        num_target = int(2 * np.pi / target_step_rad)
        uniform_nodes = np.linspace(0, 2 * np.pi, num_target, endpoint=False)
        
        # Perform interpolation
        interpolated_values = np.interp(uniform_nodes, self.nodes, values, period=2*np.pi)
        
        return uniform_nodes, interpolated_values
    
    def validate_grid(self) -> bool:
        """Validate that the grid is properly constructed."""
        # Check node ordering
        if not np.all(np.diff(self.nodes) > 0):
            logger.warning("Nodes are not in ascending order")
            return False
        
        # Check bounds
        if self.nodes[0] < 0 or self.nodes[-1] >= 2 * np.pi:
            logger.warning(f"Nodes outside [0, 2π): range [{self.nodes[0]}, {self.nodes[-1]}]")
            return False
        
        # Check differentiation matrix
        if self.differentiation_matrix.shape != (self.node_count, self.node_count):
            logger.warning("Differentiation matrix has wrong shape")
            return False
        
        return True
    
    def get_grid_info(self) -> dict:
        """Get information about the grid."""
        spacing = np.diff(self.nodes)
        return {
            "node_count": self.node_count,
            "node_type": self.node_type,
            "min_spacing": np.min(spacing),
            "max_spacing": np.max(spacing),
            "mean_spacing": np.mean(spacing),
            "domain_span": self.nodes[-1] - self.nodes[0],
            "differentiation_matrix_norm": np.linalg.norm(self.differentiation_matrix, 'fro')
        }
    
    def _get_cache_key(self):
        """Generate cache key for this grid configuration."""
        # Create a hash of the nodes to ensure matrix compatibility
        nodes_hash = hash(tuple(np.round(self.nodes, 12)))  # Round to avoid floating point issues
        return (self.node_count, self.node_type, nodes_hash)
    
    def _get_cached_differentiation_matrix(self):
        """Get differentiation matrix from cache or compute if not cached."""
        global _MATRIX_CACHE, _CACHE_HITS, _CACHE_MISSES
        
        cache_key = (*self._get_cache_key(), 'D1')
        
        if cache_key in _MATRIX_CACHE:
            _CACHE_HITS += 1
            logger.debug(f"Cache hit for differentiation matrix: {self.node_type}({self.node_count})")
            return _MATRIX_CACHE[cache_key].copy()
        
        _CACHE_MISSES += 1
        logger.debug(f"Cache miss for differentiation matrix: {self.node_type}({self.node_count})")
        
        matrix = self._compute_differentiation_matrix()
        _MATRIX_CACHE[cache_key] = matrix.copy()
        
        return matrix
    
    def _get_cached_second_derivative_matrix(self):
        """Get second derivative matrix from cache or compute if not cached."""
        global _MATRIX_CACHE, _CACHE_HITS, _CACHE_MISSES
        
        cache_key = (*self._get_cache_key(), 'D2')
        
        if cache_key in _MATRIX_CACHE:
            _CACHE_HITS += 1
            logger.debug(f"Cache hit for second derivative matrix: {self.node_type}({self.node_count})")
            return _MATRIX_CACHE[cache_key].copy()
        
        _CACHE_MISSES += 1
        logger.debug(f"Cache miss for second derivative matrix: {self.node_type}({self.node_count})")
        
        # Compute as D @ D
        D = self.differentiation_matrix
        matrix = D @ D
        _MATRIX_CACHE[cache_key] = matrix.copy()
        
        return matrix
