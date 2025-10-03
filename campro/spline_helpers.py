from __future__ import annotations

from typing import Tuple

import numpy as np
import casadi as ca

from campro.logging import get_logger

log = get_logger(__name__)

try:
	from scipy.interpolate import BSpline  # type: ignore
	_SCIPY_OK = True
except Exception:
	_SCIPY_OK = False


def _open_uniform_knots(num_ctrl: int, degree: int) -> np.ndarray:
	m = num_ctrl + degree + 1
	knots = np.zeros(m)
	# Start clamped
	knots[: degree + 1] = 0.0
	# Internal uniform
	if num_ctrl - degree - 1 > 0:
		knots[degree + 1 : num_ctrl] = np.linspace(1.0 / (num_ctrl - degree),
																							 (num_ctrl - degree - 1) / (num_ctrl - degree),
																							 num_ctrl - degree - 1)
	# End clamped
	knots[num_ctrl:] = 1.0
	return knots


def _cox_de_boor_basis(x: np.ndarray, knots: np.ndarray, degree: int, i: int) -> np.ndarray:
	if degree == 0:
		left = knots[i]
		right = knots[i + 1]
		return ((x >= left) & (x < right)).astype(float) if right > left else np.zeros_like(x)
	B_i0_left = _cox_de_boor_basis(x, knots, degree - 1, i)
	B_i1_left = _cox_de_boor_basis(x, knots, degree - 1, i + 1)
	left_den = knots[i + degree] - knots[i]
	right_den = knots[i + degree + 1] - knots[i + 1]
	left_term = 0.0
	right_term = 0.0
	if left_den > 0:
		left_term = (x - knots[i]) / left_den * B_i0_left
	if right_den > 0:
		right_term = (knots[i + degree + 1] - x) / right_den * B_i1_left
	return left_term + right_term


def _basis_and_derivatives_numpy(x: np.ndarray, num_ctrl: int, degree: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
	knots = _open_uniform_knots(num_ctrl, degree)
	N = x.size
	B = np.zeros((N, num_ctrl))
	for i in range(num_ctrl):
		B[:, i] = _cox_de_boor_basis(x, knots, degree, i)
	# Derivatives via BSpline if SciPy available, else finite differences
	if _SCIPY_OK:
		ctrl = np.eye(num_ctrl)
		spl = BSpline(knots, ctrl, degree, extrapolate=False)
		B1 = spl(x, 1)
		B2 = spl(x, 2)
	else:
		dx = 1e-6
		xp = np.clip(x + dx, 0.0, 1.0)
		xm = np.clip(x - dx, 0.0, 1.0)
		Bp = np.zeros_like(B)
		Bm = np.zeros_like(B)
		for i in range(num_ctrl):
			Bp[:, i] = _cox_de_boor_basis(xp, knots, degree, i)
			Bm[:, i] = _cox_de_boor_basis(xm, knots, degree, i)
		B1 = (Bp - Bm) / (2 * dx)
		# Second derivative central diff
		xpp = np.clip(x + 2 * dx, 0.0, 1.0)
		xmm = np.clip(x - 2 * dx, 0.0, 1.0)
		Bpp = np.zeros_like(B)
		Bmm = np.zeros_like(B)
		for i in range(num_ctrl):
			Bpp[:, i] = _cox_de_boor_basis(xpp, knots, degree, i)
			Bmm[:, i] = _cox_de_boor_basis(xmm, knots, degree, i)
		B2 = (Bpp - 2 * B + Bmm) / (4 * dx * dx)
	# Enforce clamped endpoint: at x==1, last basis is 1, derivatives 0
	end_mask = np.isclose(x, 1.0)
	if np.any(end_mask):
		B[end_mask, :] = 0.0
		B[end_mask, -1] = 1.0
		B1[end_mask, :] = 0.0
		B2[end_mask, :] = 0.0
	# Normalize rows to ensure partition-of-unity numerically
	row_sum = B.sum(axis=1, keepdims=True)
	row_sum[row_sum == 0.0] = 1.0
	B /= row_sum
	return B, B1, B2


def build_bspline_matrices(
	x_grid: np.ndarray,
	num_ctrl: int,
	degree: int = 3,
	precompute_dm: bool = True,
) -> Tuple[ca.DM, ca.DM, ca.DM]:
	"""
	Build open-uniform clamped B-spline basis and first/second derivative matrices at x_grid.
	Returns CasADi DMs: (B, dB_dx, d2B_dx2) with shapes (N, num_ctrl).
	"""
	if not (num_ctrl >= degree + 1):
		raise ValueError("num_ctrl must be >= degree+1")
	x = np.asarray(x_grid, dtype=float)
	if x.ndim != 1:
		raise ValueError("x_grid must be 1D")
	if x.size < 2:
		raise ValueError("x_grid must have at least 2 points")
	if (x.min() < 0.0) or (x.max() > 1.0):
		raise ValueError("x_grid must be scaled to [0,1]")

	B, B1, B2 = _basis_and_derivatives_numpy(x, num_ctrl, degree)
	if precompute_dm:
		return ca.DM(B), ca.DM(B1), ca.DM(B2)
	else:
		return ca.DM(B), ca.DM(B1), ca.DM(B2)


def evaluate_spline(B: ca.DM, ctrl: ca.MX) -> ca.MX:
	return ca.mtimes(B, ctrl)


def evaluate_spline_with_derivatives(
	B: ca.DM, dB_dx: ca.DM, d2B_dx2: ca.DM, ctrl: ca.MX
) -> Tuple[ca.MX, ca.MX, ca.MX]:
	y = ca.mtimes(B, ctrl)
	dy = ca.mtimes(dB_dx, ctrl)
	d2y = ca.mtimes(d2B_dx2, ctrl)
	return y, dy, d2y
