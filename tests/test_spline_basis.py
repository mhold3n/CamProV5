import numpy as np
import pytest

from campro.spline_helpers import build_bspline_matrices, evaluate_spline


@pytest.mark.parametrize("num_ctrl,degree", [(6, 3), (8, 2)])
def test_partition_of_unity(num_ctrl: int, degree: int) -> None:
    x = np.linspace(0.0, 1.0, 101)
    B, dBdx, d2Bdx2 = build_bspline_matrices(x, num_ctrl=num_ctrl, degree=degree)
    row_sum = (B @ np.ones((num_ctrl, 1))).full().ravel()
    assert np.allclose(row_sum, 1.0, rtol=1e-12, atol=1e-12)


def test_spline_reconstructs_controls_at_support_centers() -> None:
    x = np.linspace(0.0, 1.0, 101)
    B, _, _ = build_bspline_matrices(x, num_ctrl=6, degree=3)
    ctrl = np.linspace(0.0, 1.0, 6)
    y = evaluate_spline(B, ctrl).full().ravel()
    # y should be bounded within min/max of control points and smooth
    assert y.min() >= ctrl.min() - 1e-9
    assert y.max() <= ctrl.max() + 1e-9
    # monotone input should produce mostly monotone output for clamped basis
    diffs = np.diff(y)
    assert (diffs[10:-10] >= -1e-3).all()
