from __future__ import annotations

from typing import Union

import casadi as ca

from campro.logging import get_logger

log = get_logger(__name__)

CasType = Union[ca.MX, ca.SX, float]


def _require(cond: bool, msg: str) -> None:
	if not cond:
		raise ValueError(msg)


def _smooth_step(x: CasType, eps: float) -> ca.MX:
	_require(eps > 0.0, "eps must be positive")
	return 0.5 * (1 + ca.tanh(ca.MX(x) / float(eps)))


def smooth_valve_lift(t: CasType, t_open: float, t_close: float, L_max: float, eps: float) -> ca.MX:
	_require(t_close > t_open, "t_close must be greater than t_open")
	_require(L_max >= 0.0, "L_max must be non-negative")
	s_open = _smooth_step(ca.MX(t) - float(t_open), float(eps))
	s_close = _smooth_step(float(t_close) - ca.MX(t), float(eps))
	return float(L_max) * s_open * s_close


def smooth_valve_lift_d2(t: CasType, t_open: float, t_close: float, L_max: float, eps: float) -> ca.MX:
	# Second derivative via symbolic differentiation
	tv = ca.MX.sym("tv")
	expr = smooth_valve_lift(tv, t_open, t_close, L_max, eps)
	d2 = ca.hessian(expr, tv)[0]
	f = ca.Function("d2_valve", [tv], [d2])
	return f(t)


def _smooth_relu(x: CasType, k: float = 40.0) -> ca.MX:
	x = ca.MX(x)
	return (1.0 / k) * ca.log1p(ca.exp(k * x))


def wiebe_heat_release(phi: CasType, a: float, m: float, theta0: float, theta_b: float) -> ca.MX:
	_require(a > 0.0, "a must be positive")
	_require(m >= 0.0, "m must be non-negative")
	_require(theta_b > 0.0, "theta_b must be positive")
	z_raw = (ca.MX(phi) - float(theta0)) / float(theta_b)
	z = _smooth_relu(z_raw)
	return 1 - ca.exp(-float(a) * z ** (float(m) + 1.0))


def wiebe_heat_release_d2(phi: CasType, a: float, m: float, theta0: float, theta_b: float) -> ca.MX:
	pv = ca.MX.sym("pv")
	expr = wiebe_heat_release(pv, a, m, theta0, theta_b)
	d2 = ca.hessian(expr, pv)[0]
	f = ca.Function("d2_wiebe", [pv], [d2])
	return f(phi)


def smooth_friction_stribeck(v: CasType, fs: float, fc: float, vs: float, k_visc: float) -> ca.MX:
	_require(vs > 0.0, "vs must be positive")
	v = ca.MX(v)
	return float(fc) + (float(fs) - float(fc)) * ca.exp(- (v / float(vs)) ** 2) + float(k_visc) * v


def smooth_friction_stribeck_d2(v: CasType, fs: float, fc: float, vs: float, k_visc: float) -> ca.MX:
	vv = ca.MX.sym("vv")
	expr = smooth_friction_stribeck(vv, fs, fc, vs, k_visc)
	d2 = ca.hessian(expr, vv)[0]
	f = ca.Function("d2_stribeck", [vv], [d2])
	return f(v)
