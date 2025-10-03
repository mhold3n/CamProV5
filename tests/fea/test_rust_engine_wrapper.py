"""
Test suite for Rust engine wrapper implementation.

This test suite follows TDD principles to validate the Python wrapper
for the Rust FEA engine JNI integration.
"""

import pytest
import tempfile
import json
from pathlib import Path


from campro.analysis.rust_engine_wrapper import RustEngineWrapper


class TestRustEngineWrapper:
    """Test suite for Rust engine wrapper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.wrapper = RustEngineWrapper()
    
    def test_rust_engine_wrapper_initialization(self):
        """Test that Rust engine wrapper can be initialized."""
        assert self.wrapper is not None
        assert hasattr(self.wrapper, 'is_available')
        assert hasattr(self.wrapper, 'get_version')
        assert hasattr(self.wrapper, 'run_stress_analysis')
        assert hasattr(self.wrapper, 'run_vibration_analysis')
        assert hasattr(self.wrapper, 'run_fatigue_analysis')
        assert hasattr(self.wrapper, 'generate_mesh')
    
    def test_rust_engine_wrapper_availability(self):
        """Test Rust engine availability check."""
        # Test availability check
        is_available = self.wrapper.is_available()
        assert isinstance(is_available, bool)
        
        # Test version retrieval
        version = self.wrapper.get_version()
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_rust_engine_wrapper_run_stress_analysis(self):
        """Test stress analysis execution through Rust engine."""
        # Create test model file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            model_data = {
                'geometry': {
                    'sun_radius': 10.0,
                    'planet_radius': 15.0,
                    'ring_radius': 25.0
                },
                'material': {
                    'youngs_modulus': 200000.0,
                    'poisson_ratio': 0.3,
                    'density': 7850.0
                },
                'loads': {
                    'contact_force': 1000.0,
                    'rpm': 3000.0
                }
            }
            json.dump(model_data, f)
            model_file = f.name
        
        try:
            # Create test parameters
            parameters = {
                'analysis_type': 'stress',
                'mesh_density': 'medium',
                'solver_type': 'direct'
            }
            
            # Run stress analysis
            result = self.wrapper.run_stress_analysis(model_file, parameters)
            
            # Validate results
            assert result is not None
            assert 'status' in result
            assert 'max_stress' in result
            assert 'stress_distribution' in result
            assert 'safety_factor' in result
            
            # Check result status
            assert result['status'] == 'ok'
            
            # Check stress values are reasonable
            assert result['max_stress'] > 0
            assert result['safety_factor'] > 0
            
        finally:
            # Clean up test file
            Path(model_file).unlink()
    
    def test_rust_engine_wrapper_run_vibration_analysis(self):
        """Test vibration analysis execution through Rust engine."""
        # Create test model file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            model_data = {
                'geometry': {
                    'sun_radius': 10.0,
                    'planet_radius': 15.0,
                    'ring_radius': 25.0
                },
                'material': {
                    'youngs_modulus': 200000.0,
                    'poisson_ratio': 0.3,
                    'density': 7850.0
                },
                'boundary_conditions': {
                    'fixed_nodes': [1, 2, 3],
                    'applied_forces': [1000.0, 1500.0, 2000.0]
                }
            }
            json.dump(model_data, f)
            model_file = f.name
        
        try:
            # Create test parameters
            parameters = {
                'analysis_type': 'vibration',
                'num_modes': 10,
                'frequency_range': [0, 1000]
            }
            
            # Run vibration analysis
            result = self.wrapper.run_vibration_analysis(model_file, parameters)
            
            # Validate results
            assert result is not None
            assert 'status' in result
            assert 'natural_frequencies' in result
            assert 'mode_shapes' in result
            assert 'damping_ratios' in result
            
            # Check result status
            assert result['status'] == 'ok'
            
            # Check natural frequencies
            natural_frequencies = result['natural_frequencies']
            assert isinstance(natural_frequencies, list)
            assert len(natural_frequencies) > 0
            assert all(freq > 0 for freq in natural_frequencies)
            
        finally:
            # Clean up test file
            Path(model_file).unlink()
    
    def test_rust_engine_wrapper_run_fatigue_analysis(self):
        """Test fatigue analysis execution through Rust engine."""
        # Create test model file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            model_data = {
                'geometry': {
                    'sun_radius': 10.0,
                    'planet_radius': 15.0,
                    'ring_radius': 25.0
                },
                'material': {
                    'youngs_modulus': 200000.0,
                    'poisson_ratio': 0.3,
                    'density': 7850.0,
                    'fatigue_limit': 300.0,
                    'endurance_limit': 250.0
                },
                'load_cycles': {
                    'max_stress': 400.0,
                    'min_stress': 50.0,
                    'cycles_per_second': 50.0
                }
            }
            json.dump(model_data, f)
            model_file = f.name
        
        try:
            # Create test parameters
            parameters = {
                'analysis_type': 'fatigue',
                'material_model': 'soderberg',
                'safety_factor': 2.0
            }
            
            # Run fatigue analysis
            result = self.wrapper.run_fatigue_analysis(model_file, parameters)
            
            # Validate results
            assert result is not None
            assert 'status' in result
            assert 'fatigue_life' in result
            assert 'damage_accumulation' in result
            assert 'safety_margin' in result
            
            # Check result status
            assert result['status'] == 'ok'
            
            # Check fatigue life
            fatigue_life = result['fatigue_life']
            assert isinstance(fatigue_life, (int, float))
            assert fatigue_life > 0
            
        finally:
            # Clean up test file
            Path(model_file).unlink()
    
    def test_rust_engine_wrapper_generate_mesh(self):
        """Test mesh generation through Rust engine."""
        # Create test model file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            model_data = {
                'geometry': {
                    'sun_radius': 10.0,
                    'planet_radius': 15.0,
                    'ring_radius': 25.0
                },
                'mesh_parameters': {
                    'element_size': 1.0,
                    'mesh_quality': 'high'
                }
            }
            json.dump(model_data, f)
            model_file = f.name
        
        try:
            # Create test parameters
            parameters = {
                'mesh_type': 'quadrilateral',
                'element_size': 1.0,
                'mesh_quality': 'high'
            }
            
            # Generate mesh
            result = self.wrapper.generate_mesh(model_file, parameters)
            
            # Validate results
            assert result is not None
            assert 'status' in result
            assert 'mesh_file' in result
            assert 'num_elements' in result
            assert 'num_nodes' in result
            
            # Check result status
            assert result['status'] == 'ok'
            
            # Check mesh statistics
            assert result['num_elements'] > 0
            assert result['num_nodes'] > 0
            
        finally:
            # Clean up test file
            Path(model_file).unlink()
    
    def test_rust_engine_wrapper_data_conversion(self):
        """Test data conversion between Python and Rust formats."""
        # Test Python to Rust conversion
        python_data = {
            'geometry': {'radius': 10.0},
            'material': {'youngs_modulus': 200000.0},
            'loads': {'force': 1000.0}
        }
        
        rust_data = self.wrapper._convert_python_to_rust(python_data)
        assert isinstance(rust_data, dict)
        assert 'geometry' in rust_data
        assert 'material' in rust_data
        assert 'loads' in rust_data
        
        # Test Rust to Python conversion
        python_result = self.wrapper._convert_rust_to_python(rust_data)
        assert isinstance(python_result, dict)
        assert 'geometry' in python_result
        assert 'material' in python_result
        assert 'loads' in python_result
    
    def test_rust_engine_wrapper_error_handling(self):
        """Test error handling in Rust engine wrapper."""
        # Test with invalid model file
        invalid_model_file = "/nonexistent/path/model.json"
        
        # Should handle errors gracefully
        with pytest.raises(FileNotFoundError):
            self.wrapper.run_stress_analysis(invalid_model_file, {})
    
    def test_rust_engine_wrapper_performance(self):
        """Test performance of Rust engine wrapper."""
        # Create test model file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            model_data = {
                'geometry': {
                    'sun_radius': 10.0,
                    'planet_radius': 15.0,
                    'ring_radius': 25.0
                },
                'material': {
                    'youngs_modulus': 200000.0,
                    'poisson_ratio': 0.3,
                    'density': 7850.0
                }
            }
            json.dump(model_data, f)
            model_file = f.name
        
        try:
            # Create test parameters
            parameters = {
                'analysis_type': 'stress',
                'mesh_density': 'low'  # Use low density for faster execution
            }
            
            # Time the analysis
            import time
            start_time = time.time()
            
            # Run stress analysis
            result = self.wrapper.run_stress_analysis(model_file, parameters)
            
            end_time = time.time()
            
            # Should complete in reasonable time (less than 10 seconds)
            assert (end_time - start_time) < 10.0
            
            # Result should be valid
            assert result is not None
            assert 'status' in result
            
        finally:
            # Clean up test file
            Path(model_file).unlink()
    
    def test_rust_engine_wrapper_get_wrapper_info(self):
        """Test wrapper info retrieval."""
        info = self.wrapper.get_wrapper_info()
        
        assert isinstance(info, dict)
        assert 'wrapper_type' in info
        assert 'description' in info
        assert 'features' in info
        assert 'dependencies' in info
        
        assert info['wrapper_type'] == 'rust_engine'
        assert 'rust' in info['description'].lower()
        assert 'jni' in str(info['dependencies']).lower()
