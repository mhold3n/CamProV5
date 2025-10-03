"""
Solver interface definitions for CamPro V5 optimization.

This module defines the canonical solver interface to ensure consistency
across all optimization components and eliminate interface compatibility issues.
"""

import numpy as np
from typing import Optional, Dict, Any, Protocol, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .nlp_types import NLPProblem


@dataclass
class SolverResult:
    """Standardized solver result format."""
    success: bool
    x: np.ndarray
    f: float
    lam_x: np.ndarray
    lam_g: np.ndarray
    iter_count: int
    status: str
    kkt_residuals: Dict[str, float]
    meta: Dict[str, Any]
    is_fallback: bool = False


@dataclass
class WarmStart:
    """Warm start data for optimization solvers."""
    x0: np.ndarray
    lam_x0: np.ndarray
    lam_g0: np.ndarray


class SolverInterface(Protocol):
    """
    Canonical solver interface for optimization problems.
    
    All solvers must implement this interface to ensure compatibility
    across the optimization pipeline.
    """
    
    def solve(self,
              nlp_problem: "NLPProblem",
              warm_start: Optional[WarmStart] = None,
              ipopt_opts: Optional[Dict[str, Any]] = None) -> SolverResult:
        """
        Solve an optimization problem.
        
        Args:
            nlp_problem: The NLP problem to solve
            warm_start: Optional warm start data
            ipopt_opts: Optional IPOPT options
            
        Returns:
            Standardized solver result
        """
        ...


class LegacyAdapter:
    """
    Temporary adapter for legacy 2-argument solvers.
    
    This adapter wraps legacy solvers to conform to the new interface
    until they can be properly upgraded.
    """
    
    def __init__(self, legacy_solver):
        self.legacy_solver = legacy_solver
    
    def solve(self, nlp_problem, warm_start=None, ipopt_opts=None) -> SolverResult:
        """
        Adapt legacy solver to new interface.
        
        Note: Legacy solvers ignore warm_start and ipopt_opts.
        """
        # Call legacy solver with 2 arguments
        legacy_result = self.legacy_solver.solve(nlp_problem)
        
        # Convert to standardized format
        return SolverResult(
            success=legacy_result.get('success', False),
            x=legacy_result.get('x', np.array([])),
            f=legacy_result.get('f', np.nan),
            lam_x=legacy_result.get('lam_x', np.array([])),
            lam_g=legacy_result.get('lam_g', np.array([])),
            iter_count=legacy_result.get('iter_count', 0),
            status=legacy_result.get('status', 'UNKNOWN'),
            kkt_residuals=legacy_result.get('kkt_residuals', {}),
            meta=legacy_result.get('meta', {}),
            is_fallback=legacy_result.get('is_fallback', False)
        )


def create_solver_adapter(solver_factory, problem: Dict[str, Any]) -> SolverInterface:
    """
    Create a solver adapter that ensures interface compatibility.
    
    Args:
        solver_factory: Function that creates a solver
        problem: Problem dictionary
        
    Returns:
        Solver that conforms to SolverInterface
    """
    solver = solver_factory(problem)
    
    # Check if solver already conforms to interface
    if hasattr(solver, 'solve'):
        import inspect
        sig = inspect.signature(solver.solve)
        if len(sig.parameters) >= 3:  # Includes self, nlp_problem, warm_start
            return solver
        else:
            # Legacy solver - wrap it
            return LegacyAdapter(solver)
    else:
        # Assume it's a CasADi solver that can be called directly
        return LegacyAdapter(solver)
