from __future__ import annotations

from typing import Callable, Dict, Any, Iterable, Optional, List
from copy import deepcopy

import casadi as ca

from campro.logging import get_logger

log = get_logger(__name__)


DEFAULT_IPOPT_OPTS: Dict[str, Any] = {
	"print_time": False,
	"ipopt": {
		"tol": 1e-6,
		"acceptable_tol": 1e-4,
		"mu_strategy": "adaptive",
		"hessian_approximation": "exact",
		"linear_solver": "mumps",
		"max_iter": 2000,
		"print_level": 0,
	},
}


def make_solver(nlp: Dict[str, Any], opts: Optional[Dict[str, Any]] = None) -> ca.Function:
	merged = deepcopy(DEFAULT_IPOPT_OPTS)
	if opts:
		for k, v in opts.items():
			if k == "ipopt" and isinstance(v, dict):
				merged.setdefault("ipopt", {}).update(v)
			else:
				merged[k] = v
	log.debug("Creating IPOPT solver with options: %s", merged)
	return ca.nlpsol("ipopt", "ipopt", nlp, merged)


def build_scaling_vector_from_bounds(lbs: ca.DM, ubs: ca.DM, min_scale: float = 1e-3, max_scale: float = 1e3) -> ca.DM:
	span = ca.fmax(ubs - lbs, 1e-9)
	scale = 1.0 / span
	scale = ca.fmax(scale, min_scale)
	scale = ca.fmin(scale, max_scale)
	return scale


def homotopy_stages(
	build_nlp_fn: Callable[[float], Dict[str, Any]],
	smoothing_sequence: Iterable[float],
	initial_guess: Optional[ca.DM] = None,
	option_sequence: Optional[List[Dict[str, Any]]] = None,
	scaling_from_bounds: bool = True,
) -> Dict[str, Any]:
	"""
	Run staged homotopy with per-stage IPOPT options and optional variable scaling.
	"""
	current_guess: Optional[ca.DM] = initial_guess
	last_res: Optional[Dict[str, Any]] = None
	for stage_idx, s in enumerate(smoothing_sequence):
		log.info("Homotopy stage %d, s=%s", stage_idx + 1, s)
		nlp = build_nlp_fn(float(s))
		opts = option_sequence[stage_idx] if option_sequence and stage_idx < len(option_sequence) else None
		if scaling_from_bounds and all(k in nlp for k in ("lbx", "ubx")):
			try:
				sx = build_scaling_vector_from_bounds(ca.DM(nlp["lbx"]), ca.DM(nlp["ubx"]))
				nlp["x"] = ca.diag(sx) @ nlp["x"]
				if "x0" in nlp:
					nlp["x0"] = ca.diag(sx) @ nlp["x0"]
				if current_guess is not None:
					current_guess = ca.diag(sx) @ current_guess
			except Exception as exc:
				log.debug("Scaling skipped: %s", exc)
		solver = make_solver(nlp, opts)
		args: Dict[str, Any] = {}
		if current_guess is not None:
			args["x0"] = current_guess
		res = solver(**args)
		last_res = {k: res[k] for k in res.keys()}
		current_guess = ca.DM(last_res["x"]) if "x" in last_res else None
		# Emit diagnostics if available
		if "lam_g" in last_res and "f" in last_res:
			log.info("Stage %d diagnostics: f=%.3e, ||lam_g||_inf=%.3e", stage_idx + 1, float(last_res["f"]), float(ca.norm_inf(last_res["lam_g"])) )
	return last_res or {}


def homotopy_run(
	build_nlp_fn: Callable[[float], Dict[str, Any]],
	smoothing_sequence: Iterable[float],
	initial_guess: Optional[ca.DM] = None,
	solver_opts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	"""Backward-compatible simple homotopy using a single options dict for all stages."""
	option_sequence: Optional[List[Dict[str, Any]]] = None
	if solver_opts is not None:
		option_sequence = [solver_opts for _ in smoothing_sequence]
	return homotopy_stages(build_nlp_fn, smoothing_sequence, initial_guess=initial_guess, option_sequence=option_sequence, scaling_from_bounds=False)
