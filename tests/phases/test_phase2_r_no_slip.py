import numpy as np

from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters


def _synthetic_motion_law(num_points: int = 37, ring_rotation_deg: float = 180.0):

	theta_deg = np.linspace(0.0, ring_rotation_deg, num_points)
	# Simple symmetric motion: small displacement/velocity/accel to keep solver easy
	displacement = 0.1 * np.sin(np.deg2rad(theta_deg))
	velocity = np.gradient(displacement, np.deg2rad(theta_deg + 1e-9))
	acceleration = np.gradient(velocity, np.deg2rad(theta_deg + 1e-9))
	return {
		'grid': theta_deg,
		'displacement': displacement,
		'velocity': velocity,
		'acceleration': acceleration,
	}


def test_no_slip_enforced_per_node():
	motion_law = _synthetic_motion_law()
	gear_params = {
		'ringRotationDeg': 180.0,
		'samplingStepDeg': motion_law['grid'][1] - motion_law['grid'][0],
		# Set broad bounds so optimizer can choose
		'rMin': 1.2,
		'rMax': 3.2,
	}

	opt = Phase2GearOptimizer(Phase2Parameters(node_count=len(motion_law['grid'])))
	sol = opt.optimize_gear_profiles(motion_law, gear_params)

	assert sol.success, f"Phase 2 solver failed: {sol.solver_status}"

	# No-slip implies r_i * R_planet_i == R_ring_i (reformulated to avoid division)
	assert 'instantaneous_ratio' in sol.__dict__ or hasattr(sol, 'instantaneous_ratio')
	r_inst = sol.instantaneous_ratio

	# Allow reasonable numerical tolerance for optimization solver
	assert np.allclose(r_inst * sol.planet_radius, sol.ring_radius, rtol=1e-2, atol=1e-2)


