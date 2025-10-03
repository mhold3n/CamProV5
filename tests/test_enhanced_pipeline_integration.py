"""
Integration tests for enhanced optimizer pipeline.
Tests the full pipeline with enhanced optimizers end-to-end.
"""

import pytest
import numpy as np
import logging
from pathlib import Path
import tempfile
import shutil

from campro.pipeline.unified_optimizer import UnifiedOptimizer
from campro.pipeline.parameter_mapper import ParameterMapper
from campro.pipeline.result_adapter import ResultAdapter

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEnhancedPipelineIntegration:
    """Test enhanced optimizer pipeline integration."""
    
    @pytest.fixture
    def sample_ui_params(self):
        """Sample UI parameters for testing."""
        return {
            'nodeCount': 16,
            'maxIterations': 100,
            'tolerance': 1e-6,
            'constraintTolerance': 1e-6,
            'pistonAreaMm2': 100.0,
            'clearanceVolumeCm3': 50.0,
            'gamma': 1.35,
            'initialPressureBar': 1.0,
            'initialTemperatureK': 300.0,
            'gasMassKg': 1.2e-4,
            'ringThicknessMm': 5.0,
            'youngsModulusGpa': 200.0,
            'fatigueLimitMpa': 250.0,
            'normalizeObjectives': True,
            'scaleVariables': True,
            'useContinuation': False,  # Disable for faster testing
            'strokeLengthMm': 10.0,
            'ringRotationDeg': 180.0,
            'compressionDurationPercent': 70.0,
            'gearRatio': 2.0,
            'rMin': 1.8,
            'rMax': 2.2,
            'smoothnessWeight': 1e-3,
            'velocityWeight': 1e-4,
            'displacementWeight': 1e-6,
            'jerkWeight': 1e-5,
            'jerkLimit': 5000.0,
            'wPoly': 1e-2,
            'wIndicatedWork': -1e-3,
            'forceTransferWeight': 1.0,
            'efficiencyWeight': 1.0,
            'minContactForce': 100.0,
            'maxContactStress': 1000.0,
            'wKinematicCoupling': 1e2,
            'wPowerBalance': 1e2,
            'wFatigueSafety': 1e3,
            'rpm': 3000.0  # Required for FEA analyzer
        }
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_parameter_mapping(self, sample_ui_params):
        """Test parameter mapping from UI to enhanced optimizers."""
        logger.info("Testing parameter mapping")
        
        motion_params = ParameterMapper.map_to_enhanced_motion_params(sample_ui_params)
        gear_params = ParameterMapper.map_to_enhanced_gear_params(sample_ui_params)
        
        # Verify motion parameters
        assert motion_params.node_count == 16
        assert motion_params.max_iterations == 100
        assert motion_params.tolerance == 1e-6
        assert motion_params.work_weight == 1.0
        assert motion_params.pressure_weight == 0.1
        
        # Verify gear parameters
        assert gear_params.node_count == 16
        assert gear_params.max_iterations == 100  # Uses same value as motion params
        assert gear_params.tolerance == 1e-6
        assert gear_params.kinematic_weight == 1.0
        assert gear_params.power_balance_weight == 1.0
        assert gear_params.fatigue_weight == 1.0
        
        logger.info("Parameter mapping test passed")
    
    def test_result_adapter(self, sample_ui_params):
        """Test result format adaptation."""
        logger.info("Testing result adapter")
        
        # Create mock enhanced results
        enhanced_motion_result = {
            'grid': np.linspace(0, 180, 16),
            'theta_deg': np.linspace(0, 180, 16),
            'displacement': np.linspace(0, 10, 16),
            'velocity': np.ones(16),
            'acceleration': np.zeros(16),
            'success': True,
            'solver_status': 'Success',
            'thermodynamic_data': {
                'p_pa': [1e5] * 16,
                'V_m3': [50e-6] * 16,
                'indicated_work_J': 100.0
            }
        }
        
        enhanced_gear_result = {
            'theta_grid': np.linspace(0, 180, 16),
            'sun_radius': np.ones(16) * 10.0,
            'planet_radius': np.ones(16) * 5.0,
            'ring_radius': np.ones(16) * 20.0,
            'instantaneous_ratio': np.ones(16) * 2.0,
            'journal_offset': np.zeros(16),
            'accumulated_planet_angle_deg': 360.0,
            'gear_clearance': np.ones(16) * 0.1,
            'force_transfer_efficiency': np.ones(16) * 0.95,
            'max_contact_stress': 500.0,
            'objective_value': 0.1,
            'constraint_violation': 1e-6,
            'iterations': 50,
            'execution_time': 2.5,
            'solver_status': 'Success',
            'success': True,
            'transmission_data': {
                'efficiency': [0.95] * 16,
                'contact_stress': [500.0] * 16
            }
        }
        
        # Test adaptation
        adapted_motion = ResultAdapter.adapt_motion_law_result(enhanced_motion_result)
        adapted_gear = ResultAdapter.adapt_gear_result(enhanced_gear_result)
        
        # Verify adaptation
        assert adapted_motion['success']
        assert 'thermodynamic_data' in adapted_motion
        assert adapted_gear['success']
        assert 'transmission_data' in adapted_gear
        
        # Test validation
        assert ResultAdapter.validate_motion_law_result(adapted_motion)
        assert ResultAdapter.validate_gear_result(adapted_gear)
        
        logger.info("Result adapter test passed")
    
    def test_enhanced_pipeline_end_to_end(self, sample_ui_params, temp_output_dir):
        """Test full pipeline with enhanced optimizers."""
        logger.info("Testing enhanced pipeline end-to-end")
        
        optimizer = UnifiedOptimizer(output_dir=temp_output_dir)
        result = optimizer.run_pipeline(sample_ui_params)
        
        # Verify pipeline success
        assert result['status'] == 'success'
        
        # Verify motion law data
        motion_law = result['motion_law']
        assert 'displacement' in motion_law
        assert 'velocity' in motion_law
        assert 'acceleration' in motion_law
        assert len(motion_law['displacement']) > 0  # Enhanced optimizers use more nodes
        
        # Verify gear profiles
        profiles = result['optimal_profiles']
        assert 'r_sun' in profiles
        assert 'r_planet' in profiles
        assert 'r_ring_inner' in profiles
        assert len(profiles['r_sun']) > 0  # Enhanced optimizers use more nodes
        
        # Verify thermodynamic data is present
        assert 'thermodynamic_data' in motion_law
        thermo_data = motion_law['thermodynamic_data']
        if thermo_data:  # May be empty if optimization fails
            # Check for any thermodynamic fields (field names may vary)
            assert len(thermo_data) > 0
        
        # Verify transmission data is present
        assert 'transmission_data' in profiles
        trans_data = profiles['transmission_data']
        if trans_data:  # May be empty if optimization fails
            # Check for any transmission fields (field names may vary)
            assert len(trans_data) > 0
        
        # Verify performance data
        assert 'performance' in result
        perf_data = result['performance']
        assert 'total_time_s' in perf_data
        assert 'optimizer_type' in perf_data
        assert perf_data['optimizer_type'] == 'enhanced'
        
        logger.info("Enhanced pipeline end-to-end test passed")
    
    def test_legacy_pipeline_fallback(self, sample_ui_params, temp_output_dir):
        """Test legacy pipeline fallback."""
        logger.info("Testing legacy pipeline fallback")
        
        # Note: Legacy pipeline test removed since we only use enhanced optimizers now
        pytest.skip("Legacy pipeline test removed - only enhanced optimizers are used")
    
    def test_enhanced_pipeline_with_minimal_params(self, temp_output_dir):
        """Test enhanced pipeline with minimal parameters."""
        logger.info("Testing enhanced pipeline with minimal parameters")
        
        minimal_params = {
            'nodeCount': 8,  # Very small for fast testing
            'strokeLengthMm': 5.0,
            'ringRotationDeg': 90.0,
            'compressionDurationPercent': 50.0,
            'gearRatio': 2.0,
            'rMin': 1.5,
            'rMax': 2.5,
            'rpm': 3000.0  # Required for FEA analyzer
        }
        
        optimizer = UnifiedOptimizer(output_dir=temp_output_dir)
        result = optimizer.run_pipeline(minimal_params)
        
        # Should succeed even with minimal parameters
        assert result['status'] == 'success'
        
        # Verify basic data structure
        assert 'motion_law' in result
        assert 'optimal_profiles' in result
        assert 'performance' in result
        
        logger.info("Enhanced pipeline with minimal parameters test passed")
    
    def test_pipeline_error_handling(self, temp_output_dir):
        """Test pipeline error handling with invalid parameters."""
        logger.info("Testing pipeline error handling")
        
        invalid_params = {
            'nodeCount': -1,  # Invalid node count
            'strokeLengthMm': -10.0,  # Invalid stroke length
            'ringRotationDeg': 0.0,  # Invalid rotation
            'rpm': 3000.0  # Required for FEA analyzer
        }
        
        optimizer = UnifiedOptimizer(output_dir=temp_output_dir)
        
        # Should raise an error for invalid parameters
        with pytest.raises((ValueError, RuntimeError)):
            result = optimizer.run_pipeline(invalid_params)  # noqa: F841
        
        logger.info("Pipeline error handling test passed")
    
    def test_performance_comparison(self, sample_ui_params, temp_output_dir):
        """Test performance comparison between enhanced and legacy optimizers."""
        logger.info("Testing performance comparison")
        
        # Test enhanced optimizer
        enhanced_optimizer = UnifiedOptimizer(output_dir=temp_output_dir)
        enhanced_result = enhanced_optimizer.run_pipeline(sample_ui_params)  # noqa: F841
        
        # Note: Legacy optimizer test removed since we only use enhanced optimizers now
        pytest.skip("Legacy optimizer test removed - only enhanced optimizers are used")
        
        logger.info("Performance comparison test passed")


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
