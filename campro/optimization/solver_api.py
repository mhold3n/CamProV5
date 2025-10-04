"""
Standardized solver interface and result access for CamPro V5 optimization.

This module provides a unified interface for all optimization solvers to eliminate
interface compatibility issues and ensure consistent result handling.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Protocol, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from .nlp_types import NLPProblem

from .solver_utils import extract_kkt, ensure_kkt_aliases

@dataclass
class SolverResult:
    """Standardized solver result format."""
    success: bool
    status: str
    iter_count: int
    x: Optional[np.ndarray] = None
    lam_x: Optional[np.ndarray] = None
    lam_g: Optional[np.ndarray] = None
    kkt: Optional[Dict[str, float]] = None
    is_fallback: bool = False
    message: str = ""
    meta: Optional[Dict[str, Any]] = None

    # Change: compatibility helpers
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        data = asdict(self)
        ensure_kkt_aliases(data)
        return data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style access for backward compatibility."""
        return getattr(self, key, default)
    
    def __contains__(self, key: str) -> bool:
        """Dictionary-style membership test for backward compatibility."""
        return hasattr(self, key)


@dataclass
class WarmStart:
    """Warm start data for optimization solvers."""
    x0: np.ndarray
    lam_x0: Optional[np.ndarray] = None
    lam_g0: Optional[np.ndarray] = None


class SolverInterface(Protocol):
    """Standardized solver interface protocol."""
    
    def solve(self, 
              nlp_problem: "NLPProblem",
              warm_start: Optional[WarmStart] = None,
              ipopt_opts: Optional[Dict[str, Any]] = None) -> SolverResult:
        """
        Solve an NLP problem using the standardized interface.
        
        Args:
            nlp_problem: NLP problem to solve
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
        legacy_kkt = extract_kkt(legacy_result)
        return SolverResult(
            success=legacy_result.get('success', False),
            x=legacy_result.get('x', np.array([])),
            lam_x=legacy_result.get('lam_x', np.array([])),
            lam_g=legacy_result.get('lam_g', np.array([])),
            iter_count=legacy_result.get('iter_count', 0),
            status=legacy_result.get('status', 'UNKNOWN'),
            kkt=legacy_kkt,
            meta=legacy_result.get('meta', {}),
            is_fallback=legacy_result.get('is_fallback', False),
            message=legacy_result.get('message', '')
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
