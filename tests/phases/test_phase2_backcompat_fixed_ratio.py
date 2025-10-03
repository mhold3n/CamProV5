import numpy as np

from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters


def _synthetic_motion_law(num_points: int = 37, ring_rotation_deg: float = 180.0):
	theta_deg = np.linspace(0.0, ring_rotation_deg, num_points)
	displacement = 0.1 * np.sin(np.deg2rad(theta_deg))
	velocity = np.gradient(displacement, np.deg2rad(theta_deg + 1e-9))
	acceleration = np.gradient(velocity, np.deg2rad(theta_deg + 1e-9))
	return {
		'grid': theta_deg,
		'displacement': displacement,
		'velocity': velocity,
		'acceleration': acceleration,
	}


def test_fixed_ratio_mode_matches_two_to_one_mapping():
	motion_law = _synthetic_motion_law()
	step = motion_law['grid'][1] - motion_law['grid'][0]
	gear_params = {
		'ringRotationDeg': 180.0,
		'samplingStepDeg': step,
		# Lock r to 2 everywhere
		'rMin': 2.0,
		'rMax': 2.0,
	}

	opt = Phase2GearOptimizer(Phase2Parameters(node_count=len(motion_law['grid'])))
	sol = opt.optimize_gear_profiles(motion_law, gear_params)
	assert sol.success

	# instantaneous ratio should be all 2.0
	r_inst = sol.instantaneous_ratio
	assert np.allclose(r_inst, 2.0)

	# accumulated φ should equal 2 * Θ
	Theta = 180.0
	# Accumulate over intervals (exclude last node)
	phi_accum = np.sum(r_inst[:-1]) * step
	assert np.isclose(phi_accum, 2.0 * Theta, rtol=1e-4, atol=1e-6)


