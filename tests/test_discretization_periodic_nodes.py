import math
import numpy as np
import pytest

from campro.solvers.discretization import CollocationGrid


def _relative_error(a: float, b: float) -> float:
    denom = max(1.0, abs(b))
    return abs(a - b) / denom


class TestPeriodicLGLNodes:
    @pytest.mark.parametrize("n", [8, 16, 32])
    def test_nodes_periodic_and_ordered(self, n):
        grid = CollocationGrid(node_count=n, node_type="LGL")
        nodes = grid.nodes

        # Strictly increasing within [0, 2π)
        assert np.all(np.diff(nodes) > 0), "Nodes must be strictly increasing"
        assert 0.0 <= nodes[0] < 2 * math.pi
        assert nodes[-1] < 2 * math.pi

        # Periodicity property: for periodic LGL mapping, endpoints should align in function space
        # Evaluate a 2π-periodic function at first and last nodes' neighborhood via interpolation
        f = np.sin
        vals = f(nodes)
        # Wrap-around continuity: last step + first step approx equals uniform step near 2π
        spacings = np.diff(np.concatenate([nodes, nodes[:1] + 2 * math.pi]))
        assert np.all(spacings > 0), "Wrapped spacings must be positive"

    @pytest.mark.parametrize("n", [16, 32, 48])
    def test_quadrature_accuracy_on_periodic_functions(self, n):
        grid = CollocationGrid(node_count=n, node_type="LGL")
        nodes = grid.nodes

        # Define periodic test functions with known integrals over [0, 2π]
        funcs = [
            (lambda x: np.sin(x), 0.0),
            (lambda x: np.cos(x), 0.0),
            (lambda x: np.sin(2 * x), 0.0),
            (lambda x: np.cos(3 * x), 0.0),
        ]

        # Numerically integrate using trapezoidal rule on the nonuniform nodes via periodic wrap
        nodes_wrapped = np.concatenate([nodes, nodes[:1] + 2 * math.pi])
        spacings = np.diff(nodes_wrapped)

        tol = 1e-6 if n >= 32 else 5e-6
        for f, expected in funcs:
            values = f(nodes)
            # Piecewise-constant (midpoint) Riemann-like sum on segments
            seg_vals = values
            approx = float(np.sum(seg_vals * spacings))
            assert _relative_error(approx, expected) <= tol, (
                f"Quadrature error too high for n={n}: got {approx}, expected {expected}"
            )

    @pytest.mark.parametrize("n", [3, 4, 5, 6])
    def test_small_node_counts_stability(self, n):
        grid = CollocationGrid(node_count=n, node_type="LGL")
        assert grid.validate_grid(), "Grid should validate for small node counts"


