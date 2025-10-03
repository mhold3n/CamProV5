from __future__ import annotations

from typing import Dict, Any, Tuple, List

import numpy as np
import casadi as ca

from campro.logging import get_logger
from campro.models import smooth_friction_stribeck

log = get_logger(__name__)


def _collocation_coefficients(degree: int = 3) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
	"""
	Compute Radau collocation coefficients following CasADi examples.
	Returns (C, D, B) where:
	- C[a, j] is the coefficient for collocation equation
	- D[j] is the coefficient for continuity equation
	- B[j] is for quadrature
	"""
	# Radau collocation points
	from numpy.polynomial.legendre import leggauss
	# Use Radau by augmenting Legendre nodes with 0
	# degree indicates number of collocation points
	# Collocation points tau in (0,1]
	# We take Gauss-Legendre nodes on [-1,1] and map; then include tau=0 for basis construction
	tau_root, _ = leggauss(degree)
	tau_root = 0.5 * (tau_root + 1.0)  # map to [0,1]
	tau = np.concatenate(([0.0], tau_root))
	# Coefficients
	C = np.zeros((degree + 1, degree + 1))
	D = np.zeros(degree + 1)
	B = np.zeros(degree + 1)
	for j in range(degree + 1):
		# Lagrange polynomials
		p = np.poly1d([1.0])
		for r in range(degree + 1):
			if r != j:
				p *= np.poly1d([1.0, -tau[r]]) / (tau[j] - tau[r])
		D[j] = p(1.0)
		# derivative of p
		pder = np.polyder(p)
		for r in range(degree + 1):
			C[j, r] = pder(tau[r])
		# integral of p
		pint = np.polyint(p)
		B[j] = pint(1.0) - pint(0.0)
	return C, D, B


def _build_free_piston_radau(N: int, degree: int, smoothing: float) -> Tuple[Dict[str, Any], Dict[str, Any]]:
	"""
	Build a Radau collocation NLP with time-scaling h and periodicity on all states.
	Simple damped oscillator dynamics with smooth loss model for power balance residuals.
	"""
	nx = 2  # [pos, vel]
	nu = 1  # scalar control

	C, D, B = _collocation_coefficients(degree)

	# Decision variables
	h = ca.MX.sym("h")
	Xk = [ca.MX.sym(f"X_{k}", nx) for k in range(N + 1)]  # states at mesh points
	Uk = [ca.MX.sym(f"U_{k}", nu) for k in range(N)]      # control piecewise-constant per interval
	# Collocation states per interval
	Zkj: List[List[ca.MX]] = []
	for k in range(N):
		Zk = [ca.MX.sym(f"Z_{k}_{j}", nx) for j in range(1, degree + 1)]
		Zkj.append(Zk)

	# Dynamics parameters (dimensionless-friendly)
	m = 1.0
	k_spring = 50.0
	c_damp = 0.5

	def f(x: ca.MX, u: ca.MX) -> ca.MX:
		pos = x[0]
		vel = x[1]
		a = (u - k_spring * pos - c_damp * vel) / m
		return ca.vertcat(vel, a)

	w_list: List[ca.MX] = []
	lbx: List[float] = []
	ubx: List[float] = []
	x0: List[float] = []

	# Pack variables, bounds, initial guess
	for k in range(N + 1):
		w_list.append(Xk[k])
		lbx += [-2.0, -10.0]
		ubx += [2.0, 10.0]
		x0 += [0.1, 0.0]
	for k in range(N):
		w_list.append(Uk[k])
		lbx += [-10.0]
		ubx += [10.0]
		x0 += [0.0]
	for k in range(N):
		for j in range(1, degree + 1):
			w_list.append(Zkj[k][j - 1])
			lbx += [-2.0, -10.0]
			ubx += [2.0, 10.0]
			x0 += [0.1, 0.0]
	# h bounds
	w_list.append(h)
	lbx.append(1e-2)
	ubx.append(1e1)
	x0.append(1.0)

	w = ca.vertcat(*[ca.reshape(wi, -1, 1) for wi in w_list])

	g_list: List[ca.MX] = []
	# Collocation and continuity constraints
	for k in range(N):
		# State at start of interval
		xk = Xk[k]
		# Compute the state derivative approximation at collocation points
		for j in range(1, degree + 1):
			# State at collocation point j
			xkj = Zkj[k][j - 1]
			dxkj = 0
			for r in range(degree + 1):
				xr = xk if r == 0 else Zkj[k][r - 1]
				dxkj += C[r, j] * xr
			# Collocation equation: h * f(xkj, Uk[k]) - dx/dtau = 0
			g_list.append(h * f(xkj, Uk[k]) - dxkj)
		# Continuity equation: state at end equals combination of collocation states
		xkend = D[0] * xk
		for j in range(1, degree + 1):
			xkend += D[j] * Zkj[k][j - 1]
		# Enforce continuity
		g_list.append(Xk[k + 1] - xkend)

	# Periodicity for all states
	g_list.append(Xk[0] - Xk[-1])

	# Power-balance residuals at mesh nodes (simplified surrogate)
	for k in range(N + 1):
		pos = Xk[k][0]
		vel = Xk[k][1]
		F_p = -k_spring * pos
		P_loss = smooth_friction_stribeck(vel, fs=0.8, fc=0.5, vs=0.2, k_visc=0.01) * vel
		power_residual = F_p * vel - P_loss
		g_list.append(power_residual)

	# Objective: Radau quadrature over collocation states for v^2 and rectangle for u^2
	alpha_v = 1e-2
	beta_u = 1e-3
	J = 0
	for k in range(N):
		# v at collocation points
		quad_v = 0
		for j in range(1, degree + 1):
			vk_j = Zkj[k][j - 1][1]
			quad_v += B[j] * vk_j ** 2
		J += alpha_v * quad_v + beta_u * (Uk[k][0] ** 2) * (sum(B[1:]))
	J = h * J

	nlp = {"x": w, "f": J, "g": ca.vertcat(*g_list)}
	args = {
		"lbx": ca.DM(lbx),
		"ubx": ca.DM(ubx),
		"lbg": ca.DM.zeros((sum(gi.numel() for gi in g_list), 1)),
		"ubg": ca.DM.zeros((sum(gi.numel() for gi in g_list), 1)),
		"x0": ca.DM(x0),
	}
	return nlp, args


def run_problem_with_N(N: int, smoothing: float = 1.0, degree: int = 3) -> Dict[str, Any]:
	"""
	Solve the Radau free-piston NLP and return diagnostics for testing.
	"""
	nlp, args = _build_free_piston_radau(N=N, degree=degree, smoothing=smoothing)
	solver = ca.nlpsol("ipopt", "ipopt", nlp, {"print_time": False, "ipopt": {"print_level": 0}})
	res = solver(**args)
	J = float(res["f"]) if "f" in res else float("nan")
	g_eval = res["g"] if "g" in res else ca.DM()
	g_inf = float(ca.norm_inf(g_eval)) if g_eval.numel() > 0 else 0.0
	return {"J": J, "g_inf": g_inf, "x": res.get("x", ca.DM())}
