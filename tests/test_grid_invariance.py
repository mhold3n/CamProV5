import math
import pytest

from typing import Dict, Any

from campro.optimization.free_piston import run_problem_with_N


@pytest.mark.parametrize("N_values", [(30, 60, 120)])
def test_grid_invariance(N_values) -> None:
    sols = []
    Js = []
    for N in N_values:
        sol: Dict[str, Any] = run_problem_with_N(N=N, smoothing=1.0)
        sols.append((N, sol))
        J = float(sol["J"])
        Js.append(J)
        assert math.isfinite(J)
        assert sol["g_inf"] < 1e-6

    scale = max(1e-3, max(abs(j) for j in Js))
    for (N1, s1), (N2, s2) in zip(sols[:-1], sols[1:]):
        diff = abs(float(s1["J"]) - float(s2["J"])) / scale
        assert diff < 1e-3
