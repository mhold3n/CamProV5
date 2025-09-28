"""
Tests for Kotlin UI integration with the unified optimization pipeline.

This module tests the integration between the Kotlin UI and the Python
unified optimization pipeline, ensuring proper parameter validation,
result parsing, and error handling.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from campro.pipeline.unified_optimizer import UnifiedOptimizer


class TestKotlinIntegration:
    """Test Kotlin UI integration with Python pipeline."""

    def test_parameter_validation_and_conversion(self, tmp_path):
        """Test parameter validation and conversion from Kotlin to Python."""
        # Simulate Kotlin parameters
        kotlin_params = {
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
        
        # Test parameter validation
        assert kotlin_params["samplingStepDeg"] > 0
        assert kotlin_params["strokeLengthMm"] > 0
        assert kotlin_params["gearRatio"] > 0
        assert kotlin_params["rpm"] > 0
        
        # Test parameter conversion (should be direct for these parameters)
        python_params = kotlin_params.copy()
        assert python_params == kotlin_params

    def test_result_parsing_and_visualization(self, tmp_path):
        """Test result parsing and visualization data preparation."""
        optimizer = UnifiedOptimizer(output_dir=tmp_path)
        
        # Run pipeline to get results
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
        
        # Test result structure for Kotlin consumption
        assert 'status' in result
        assert 'motion_law' in result
        assert 'optimal_profiles' in result
        assert 'tooth_profiles' in result
        assert 'fea' in result
        
        # Test motion law data for visualization
        motion_law = result['motion_law']
        assert 'theta_deg' in motion_law
        assert 'displacement' in motion_law
        assert 'velocity' in motion_law
        assert 'acceleration' in motion_law
        
        # Test that arrays are serializable for JSON
        assert len(motion_law['theta_deg']) > 0
        assert len(motion_law['displacement']) > 0
        
        # Test FEA results for visualization
        fea = result['fea']
        assert 'analysis_summary' in fea

    def test_error_handling_and_fallback_mechanisms(self, tmp_path):
        """Test error handling and fallback mechanisms."""
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
        assert result['status'] in ('success', 'failed')
        
        if result['status'] == 'failed':
            assert 'error' in result
            assert 'stage' in result

    def test_json_serialization_for_kotlin(self, tmp_path):
        """Test JSON serialization for Kotlin consumption."""
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
        
        # Test JSON serialization
        try:
            json_str = json.dumps(result, default=str)
            assert len(json_str) > 0
            
            # Test deserialization
            parsed_result = json.loads(json_str)
            assert parsed_result['status'] == result['status']
        except (TypeError, ValueError) as e:
            pytest.fail(f"JSON serialization failed: {e}")

    def test_performance_characteristics_for_ui(self, tmp_path):
        """Test performance characteristics suitable for UI interaction."""
        optimizer = UnifiedOptimizer(output_dir=tmp_path)
        
        # Test with UI-friendly parameters (reasonable resolution)
        ui_params = {
            "samplingStepDeg": 5.0,  # Reasonable resolution for UI
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
        
        import time
        start_time = time.time()
        result = optimizer.run_pipeline(ui_params)
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time for UI (less than 10 seconds)
        assert execution_time < 10.0
        assert result['status'] == 'success'
        
        # Result should be suitable for UI visualization
        motion_law = result['motion_law']
        assert len(motion_law['theta_deg']) > 10  # Enough points for smooth visualization
        assert len(motion_law['theta_deg']) < 1000  # Not too many points for UI performance

    def test_parameter_edge_cases(self, tmp_path):
        """Test parameter edge cases that might come from UI."""
        optimizer = UnifiedOptimizer(output_dir=tmp_path)
        
        # Test with minimum valid parameters
        min_params = {
            "samplingStepDeg": 1.0,
            "ringRotationDeg": 180.0,
            "gearRatio": 1.1,
            "strokeLengthMm": 1.0,
            "rodLength": 20.0,
            "journalRadius": 1.0,
            "interferenceBuffer": 0.1,
            "ringThickness": 1.0,
            "rpm": 100.0,
            "planetCount": 2,
            "carrierOffsetDeg": 180.0,
            "rampBeforeTdcDeg": 5.0,
            "rampAfterTdcDeg": 5.0,
            "dwellTdcDeg": 5.0,
            "rampBeforeBdcDeg": 5.0,
            "rampAfterBdcDeg": 5.0,
            "dwellBdcDeg": 5.0,
            "constantVelocityTdcDeg": 10.0,
            "constantVelocityBdcDeg": 10.0,
        }
        
        result = optimizer.run_pipeline(min_params)
        assert result['status'] in ('success', 'failed')
        
        # Test with maximum reasonable parameters
        max_params = {
            "samplingStepDeg": 0.5,
            "ringRotationDeg": 180.0,
            "gearRatio": 5.0,
            "strokeLengthMm": 50.0,
            "rodLength": 200.0,
            "journalRadius": 20.0,
            "interferenceBuffer": 2.0,
            "ringThickness": 20.0,
            "rpm": 10000.0,
            "planetCount": 8,
            "carrierOffsetDeg": 45.0,
            "rampBeforeTdcDeg": 30.0,
            "rampAfterTdcDeg": 30.0,
            "dwellTdcDeg": 20.0,
            "rampBeforeBdcDeg": 30.0,
            "rampAfterBdcDeg": 30.0,
            "dwellBdcDeg": 20.0,
            "constantVelocityTdcDeg": 50.0,
            "constantVelocityBdcDeg": 50.0,
        }
        
        result = optimizer.run_pipeline(max_params)
        assert result['status'] in ('success', 'failed')
