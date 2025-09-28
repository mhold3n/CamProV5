"""
Tests for ToothProfileGenerator (Phase 6).
"""

import numpy as np
from campro.gears.profile_generator import GearProfileGenerator
from campro.gears.tooth_generator import ToothProfileGenerator


def _baseline_params():
	return {
		"ringRotationDeg": 180.0,
		"planetRotationDeg": 360.0,
		"gearRatio": 2.0,
		"expansionDurationDeg": 110.0,
		"compressionDurationDeg": 70.0,
		"rampBeforeTdcDeg": 6.0,
		"rampAfterTdcDeg": 5.0,
		"rampBeforeBdcDeg": 7.0,
		"rampAfterBdcDeg": 4.0,
		"dwellTdcDeg": 4.0,
		"dwellBdcDeg": 3.0,
		"strokeLengthMm": 15.0,
		"rodLength": 100.0,
		"journalRadius": 5.0,
		"interferenceBuffer": 0.5,
		"ringThickness": 5.0,
		"samplingStepDeg": 1.0,
		"upFraction": 0.6,
		"rpm": 3000.0,
		"planetRadiusBaseFactor": 0.8,
		"planetRadiusVariationFactor": 0.3,
		"sunRadiusBaseFactor": 0.6,
		"sunRadiusVariationFactor": 0.2,
		"strokeAchievableFactor": 0.3,
		"rampProfile": "MODIFIED_SINE",
	}


def test_tooth_profile_generation():
	gen = GearProfileGenerator()
	tgen = ToothProfileGenerator()
	params = _baseline_params()

	theta, disp, vel, acc = gen.generate_motion_law_piecewise(params)
	profiles = gen.generate_gear_profiles(theta, disp, params)

	# If XY not present, ensure polar keys are present (contract of generator)
	assert 'theta_deg' in profiles and 'r_sun' in profiles and 'r_planet' in profiles and 'r_ring_inner' in profiles

	teeth = tgen.generate_tooth_profiles(profiles, params)
	assert set(teeth.keys()) == {'sun_teeth', 'planet_teeth', 'ring_teeth'}

	for key in teeth:
		arr = teeth[key]
		assert isinstance(arr, np.ndarray)
		assert arr.ndim == 2 and arr.shape[1] == 4  # [x_u, y_u, x_l, y_l]
		assert np.all(np.isfinite(arr))

	# Basic monotonicity/continuity check: no NaNs, reasonable bounds
	all_vals = np.concatenate([teeth['sun_teeth'].ravel(), teeth['planet_teeth'].ravel(), teeth['ring_teeth'].ravel()])
	assert not np.any(np.isnan(all_vals))
	assert np.max(np.abs(all_vals)) < 1e5


def test_tooth_thickness_scaling_reasonable():
	gen = GearProfileGenerator()
	tgen = ToothProfileGenerator()
	params = _baseline_params()

	theta, disp, *_ = gen.generate_motion_law_piecewise(params)
	profiles = gen.generate_gear_profiles(theta, disp, params)
	# Provide optional XY hints by converting polar to XY
	theta_deg = profiles['theta_deg']
	r_to_xy = lambda r: np.stack([r * np.cos(np.deg2rad(theta_deg)), r * np.sin(np.deg2rad(theta_deg))], axis=1)
	profiles_xy = {
		'sun': r_to_xy(profiles['r_sun']),
		'planet': r_to_xy(profiles['r_planet']),
		'ring': r_to_xy(profiles['r_ring_inner']),
		**profiles
	}

	teeth = tgen.generate_tooth_profiles(profiles_xy, params)
	# Expect non-zero width between upper/lower borders
	for key in ('sun_teeth', 'planet_teeth', 'ring_teeth'):
		upper = teeth[key][:, :2]
		lower = teeth[key][:, 2:]
		width = np.linalg.norm(upper - lower, axis=1)
		assert np.all(width > 0.0)
		assert np.percentile(width, 5) > 0.01  # at least 10 microns


def test_tooth_generator_input_validation():
	tgen = ToothProfileGenerator()
	bad = {'sun': np.array([]), 'planet': np.array([[0, 0]]), 'ring': np.array([[0, 0]])}
	try:
		tgen.generate_tooth_profiles(bad, _baseline_params())
	except ValueError:
		pass
	else:
		assert False, "Expected ValueError for empty sun profile"
