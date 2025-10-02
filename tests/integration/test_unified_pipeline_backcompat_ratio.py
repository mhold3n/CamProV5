import numpy as np

from campro.pipeline.unified_optimizer import UnifiedOptimizer


def test_unified_pipeline_backcompat_fixed_ratio_two():
	# Configure pipeline input with r locked to 2 everywhere
	input_params = {
		'samplingStepDeg': 5.0,
		'ringRotationDeg': 180.0,
		'gearRatio': 2.0,
		'strokeLengthMm': 10.0,
		'rodLength': 80.0,
		'journalRadius': 5.0,
		'interferenceBuffer': 0.5,
		'ringThickness': 5.0,
		'rpm': 1000.0,
		'planetCount': 2,
		'carrierOffsetDeg': 180.0,
		'rampBeforeTdcDeg': 20.0,
		'rampAfterTdcDeg': 20.0,
		'dwellTdcDeg': 10.0,
		'rampBeforeBdcDeg': 20.0,
		'rampAfterBdcDeg': 20.0,
		'dwellBdcDeg': 10.0,
		'constantVelocityTdcDeg': 30.0,
		'constantVelocityBdcDeg': 40.0,
		# New instantaneous ratio hyperparameters (lock to 2)
		'rMin': 2.0,
		'rMax': 2.0,
	}

	pipeline = UnifiedOptimizer()
	result = pipeline.run_pipeline(input_params)
	assert result['status'] == 'success'

	profiles = result['optimal_profiles']
	r_inst = np.asarray(profiles['instantaneous_ratio'])
	assert r_inst.size > 0
	assert np.allclose(r_inst, 2.0)

	Theta = input_params['ringRotationDeg']
	# Use actual step size from the grid, not the input parameter
	theta_deg = np.array(profiles['theta_deg'])
	theta_rad = np.radians(theta_deg)
	
	# Calculate phi accumulation as integral of instantaneous ratio
	# For constant ratio r=2, phi should be 2 * theta
	phi_accum = float(np.sum(r_inst[:-1] * np.diff(theta_rad)))
	
	# Convert Theta from degrees to radians for comparison
	Theta_rad = np.radians(Theta)
	expected_phi = 2.0 * Theta_rad
	
	# Allow reasonable tolerance for numerical integration
	assert np.isclose(phi_accum, expected_phi, rtol=1e-2, atol=1e-2)


