import numpy as np
import pytest
from campro.pipeline.unified_optimizer import UnifiedOptimizer


def test_pipeline_integration_basic(tmp_path):
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	params = {
		"samplingStepDeg": 10.0,
		"ringRotationDeg": 180.0,
		"gearRatio": 2.0,
		"strokeLengthMm": 8.0,
		"rodLength": 60.0,
		"journalRadius": 4.0,
		"interferenceBuffer": 0.5,
		"ringThickness": 4.0,
		"rpm": 2500.0,
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
	res = optimizer.run_pipeline(params)
	assert res['status'] == 'success'
	assert 'fea' in res


def test_pipeline_integration_component_validation(tmp_path):
	"""Test that all pipeline components are properly integrated."""
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	params = {
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
	
	result = optimizer.run_pipeline(params)
	
	# Validate motion law
	assert 'motion_law' in result
	ml = result['motion_law']
	assert 'theta_deg' in ml
	assert 'displacement' in ml
	assert 'velocity' in ml
	assert 'acceleration' in ml
	
	# Validate optimal profiles
	assert 'optimal_profiles' in result
	optimal_profiles = result['optimal_profiles']
	assert 'optimal_profiles' in optimal_profiles
	assert 'efficiency_analysis' in optimal_profiles
	assert 'comparison_metrics' in optimal_profiles
	
	# Validate tooth profiles
	assert 'tooth_profiles' in result
	tooth = result['tooth_profiles']
	assert 'sun_teeth' in tooth or 'sun' in tooth
	assert 'planet_teeth' in tooth or 'planet' in tooth
	assert 'ring_teeth' in tooth or 'ring' in tooth
	
	# Validate FEA results
	assert 'fea' in result
	fea = result['fea']
	assert 'analysis_summary' in fea


def test_pipeline_integration_error_handling(tmp_path):
	"""Test pipeline error handling with invalid parameters."""
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	
	# Test with edge case parameters (still valid but challenging)
	edge_case_params = {
		"samplingStepDeg": 1.0,  # Very high resolution
		"ringRotationDeg": 180.0,
		"gearRatio": 2.0,
		"strokeLengthMm": 1.0,  # Very small stroke
		"rodLength": 60.0,
		"journalRadius": 4.0,
		"interferenceBuffer": 0.1,  # Very tight clearance
		"ringThickness": 4.0,
		"rpm": 2500.0,
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
	
	# Should handle edge case parameters gracefully
	result = optimizer.run_pipeline(edge_case_params)
	# The pipeline should either succeed or fail gracefully
	assert result['status'] in ('success', 'failed')


def test_pipeline_integration_data_consistency(tmp_path):
	"""Test that pipeline maintains data consistency across components."""
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	params = {
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
	
	result = optimizer.run_pipeline(params)
	
	# Check data consistency
	ml = result['motion_law']
	optimal_profiles = result['optimal_profiles']
	profiles = optimal_profiles['optimal_profiles']
	
	# Motion law arrays should have same length
	ml_length = len(ml['theta_deg'])
	assert len(ml['displacement']) == ml_length
	assert len(ml['velocity']) == ml_length
	assert len(ml['acceleration']) == ml_length
	
	# Profile arrays should have same length
	profile_length = len(profiles['r_sun'])
	assert len(profiles['r_planet']) == profile_length
	assert len(profiles['r_ring_inner']) == profile_length
	
	# Gear ratio should be consistent
	assert profiles['gear_ratio'] == params['gearRatio']


def test_pipeline_integration_output_directory(tmp_path):
	"""Test that pipeline creates output directory and files."""
	optimizer = UnifiedOptimizer(output_dir=tmp_path)
	params = {
		"samplingStepDeg": 10.0,
		"ringRotationDeg": 180.0,
		"gearRatio": 2.0,
		"strokeLengthMm": 8.0,
		"rodLength": 60.0,
		"journalRadius": 4.0,
		"interferenceBuffer": 0.5,
		"ringThickness": 4.0,
		"rpm": 2500.0,
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
	
	result = optimizer.run_pipeline(params)
	
	# Check that output directory exists
	assert tmp_path.exists()
	assert tmp_path.is_dir()
	
	# Pipeline should complete successfully
	assert result['status'] == 'success'
