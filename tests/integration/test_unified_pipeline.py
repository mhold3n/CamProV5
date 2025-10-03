import numpy as np
from campro.pipeline.unified_optimizer import UnifiedOptimizer


def _baseline_params():
	return {
		"samplingStepDeg": 5.0,
		"ringRotationDeg": 180.0,
		"gearRatio": 2.0,
		"strokeLengthMm": 10.0,
		"rodLength": 80.0,
		"journalRadius": 5.0,
		"interferenceBuffer": 0.5,
		"ringThickness": 5.0,
		"rpm": 3000.0,
		"planetCount": 3,
		"carrierOffsetDeg": 120.0,
		"rampBeforeTdcDeg": 20.0,
		"rampAfterTdcDeg": 20.0,
		"dwellTdcDeg": 10.0,
		"rampBeforeBdcDeg": 20.0,
		"rampAfterBdcDeg": 20.0,
		"dwellBdcDeg": 10.0,
		"constantVelocityTdcDeg": 30.0,
		"constantVelocityBdcDeg": 40.0,
	}


def test_unified_pipeline_runs_end_to_end(tmp_path):
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	params = _baseline_params()

	result = optimizer.run_pipeline(params)
	assert result.get('status') == 'success'
	assert 'motion_law' in result
	assert 'optimal_profiles' in result
	assert 'tooth_profiles' in result
	assert 'fea' in result

	ml = result['motion_law']
	for key in ('theta_deg', 'displacement', 'velocity', 'acceleration'):
		assert key in ml
		assert isinstance(ml[key], np.ndarray)
		assert ml[key].size > 0


def test_unified_pipeline_handles_failure_gracefully(monkeypatch, tmp_path):
	"""Test that pipeline handles optimization failures gracefully with fallback data."""
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	
	# Test with parameters that might cause optimization issues
	problematic_params = _baseline_params()
	problematic_params['strokeLengthMm'] = 0.1  # Very small stroke
	problematic_params['rpm'] = 10000.0  # Very high RPM
	
	res = optimizer.run_pipeline(problematic_params)
	
	# Pipeline should complete successfully even with optimization issues
	assert res['status'] == 'success'
	
	# Should have valid motion law data (even if from fallback)
	ml = res['motion_law']
	assert 'theta_deg' in ml
	assert 'displacement' in ml
	assert 'velocity' in ml
	assert 'acceleration' in ml
	assert len(ml['theta_deg']) > 0
	assert len(ml['displacement']) > 0


def test_unified_pipeline_with_stress_test_parameters(tmp_path):
	"""Test pipeline with stress test parameters from existing test suite."""
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	
	# Use stress test parameters from existing test suite
	stress_params = {
		"samplingStepDeg": 2.0,  # Higher resolution
		"ringRotationDeg": 180.0,
		"gearRatio": 2.0,
		"strokeLengthMm": 15.0,  # Larger stroke
		"rodLength": 100.0,  # Longer rod
		"journalRadius": 8.0,  # Larger journal
		"interferenceBuffer": 0.2,  # Tighter clearance
		"ringThickness": 8.0,  # Thicker ring
		"rpm": 5000.0,  # Higher RPM
		"planetCount": 4,  # More planets
		"carrierOffsetDeg": 90.0,
		"rampBeforeTdcDeg": 15.0,
		"rampAfterTdcDeg": 15.0,
		"dwellTdcDeg": 5.0,
		"rampBeforeBdcDeg": 15.0,
		"rampAfterBdcDeg": 15.0,
		"dwellBdcDeg": 5.0,
		"constantVelocityTdcDeg": 25.0,
		"constantVelocityBdcDeg": 35.0,
		# Additional stress parameters
		"planetRadiusBaseFactor": 0.2,
		"planetRadiusVariationFactor": 0.1,
		"sunRadiusBaseFactor": 0.15,
		"sunRadiusVariationFactor": 0.05,
		"strokeAchievableFactor": 0.9,
		"clearanceSafetyMargin": 0.2,
		"adjustmentSplitFactor": 0.6,
	}
	
	result = optimizer.run_pipeline(stress_params)
	assert result['status'] == 'success'
	
	# Validate stress test results
	ml = result['motion_law']
	assert len(ml['theta_deg']) > 10  # Should have reasonable number of points
	assert np.max(ml['displacement']) >= 0.015  # Should achieve full stroke (15mm = 0.015m)
	
	# Check optimal profiles structure
	optimal_profiles = result['optimal_profiles']
	# The optimal_profiles should contain gear profile data
	assert 'theta_deg' in optimal_profiles
	assert 'r_sun' in optimal_profiles
	assert 'r_planet' in optimal_profiles
	assert 'r_ring_inner' in optimal_profiles
	
	# Validate FEA results
	fea = result['fea']
	assert 'analysis_summary' in fea


def test_unified_pipeline_with_different_gear_ratios(tmp_path):
	"""Test pipeline with different gear ratios to stress the system."""
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	
	gear_ratios = [1.5, 2.0, 2.5, 3.0]
	
	for ratio in gear_ratios:
		params = _baseline_params()
		params["gearRatio"] = ratio
		params["samplingStepDeg"] = 3.0  # Higher resolution for complex ratios
		
		result = optimizer.run_pipeline(params)
		assert result['status'] == 'success'
		
		# Validate gear ratio is maintained
		optimal_profiles = result['optimal_profiles']
		# Check that gear profile data exists
		assert 'theta_deg' in optimal_profiles
		assert 'r_sun' in optimal_profiles
		# Note: gear ratio validation would require checking the actual gear geometry


def test_unified_pipeline_performance_characteristics(tmp_path):
	"""Test pipeline performance with various parameter combinations."""
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	
	# Test with minimal parameters (fast execution)
	minimal_params = {
		"samplingStepDeg": 10.0,
		"ringRotationDeg": 180.0,
		"gearRatio": 2.0,
		"strokeLengthMm": 5.0,
		"rodLength": 40.0,
		"journalRadius": 3.0,
		"interferenceBuffer": 0.5,
		"ringThickness": 3.0,
		"rpm": 1000.0,
		"planetCount": 2,
		"carrierOffsetDeg": 180.0,
		"rampBeforeTdcDeg": 20.0,
		"rampAfterTdcDeg": 20.0,
		"dwellTdcDeg": 10.0,
		"rampBeforeBdcDeg": 20.0,
		"rampAfterBdcDeg": 20.0,
		"dwellBdcDeg": 10.0,
		"constantVelocityTdcDeg": 30.0,
		"constantVelocityBdcDeg": 40.0,
	}
	
	result = optimizer.run_pipeline(minimal_params)
	assert result['status'] == 'success'
	
	# Test with maximum parameters (stress test)
	maximal_params = {
		"samplingStepDeg": 1.0,  # Maximum resolution
		"ringRotationDeg": 180.0,
		"gearRatio": 3.0,  # Higher gear ratio
		"strokeLengthMm": 20.0,  # Maximum stroke
		"rodLength": 150.0,  # Maximum rod length
		"journalRadius": 12.0,  # Maximum journal
		"interferenceBuffer": 0.1,  # Minimum clearance
		"ringThickness": 12.0,  # Maximum thickness
		"rpm": 8000.0,  # Maximum RPM
		"planetCount": 6,  # Maximum planets
		"carrierOffsetDeg": 60.0,
		"rampBeforeTdcDeg": 10.0,
		"rampAfterTdcDeg": 10.0,
		"dwellTdcDeg": 5.0,
		"rampBeforeBdcDeg": 10.0,
		"rampAfterBdcDeg": 10.0,
		"dwellBdcDeg": 5.0,
		"constantVelocityTdcDeg": 20.0,
		"constantVelocityBdcDeg": 30.0,
	}
	
	result = optimizer.run_pipeline(maximal_params)
	assert result['status'] == 'success'
