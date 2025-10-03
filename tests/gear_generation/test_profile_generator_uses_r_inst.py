import numpy as np

from campro.gears.profile_generator import GearProfileGenerator


def test_profile_generator_accumulates_phi_from_r_inst():
	gen = GearProfileGenerator()
	n = 37
	step = 5.0
	theta = np.linspace(0.0, 180.0, n)
	disp = 0.1 * np.sin(np.deg2rad(theta))
	params = {
		'samplingStepDeg': step,
		'ringRotationDeg': 180.0,
		'strokeLengthMm': 10.0,
		'rodLength': 80.0,
		'journalRadius': 5.0,
		'interferenceBuffer': 0.5,
		'ringThickness': 5.0,
		# Provide an explicitly varying instantaneous ratio
		'instantaneous_ratio': np.linspace(1.8, 2.2, n).tolist()
	}

	profiles = gen.generate_gear_profiles(theta, disp, params)
	phi = np.asarray(profiles['phi_of_theta_deg'])

	# Expected φ from r: cumulative sum * Δθ
	r_inst = np.linspace(1.8, 2.2, n)
	expected_phi = np.cumsum(r_inst) * step
	assert np.allclose(phi, expected_phi, rtol=1e-6, atol=1e-6)


