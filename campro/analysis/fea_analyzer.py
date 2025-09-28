"""
FEA analyzer for CamProV5.

This module provides a high-level interface for Finite Element Analysis (FEA)
using the Rust FEA engine, including stress, vibration, and fatigue analysis.
"""

import logging
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

from .rust_engine_wrapper import RustEngineWrapper

logger = logging.getLogger(__name__)


class FEAAnalyzer:
    """
    FEA analyzer for comprehensive gear analysis.
    
    This class provides a high-level interface for Finite Element Analysis (FEA)
    using the Rust FEA engine, including stress, vibration, and fatigue analysis.
    """
    
    def __init__(self):
        """Initialize the FEA analyzer."""
        self.logger = logging.getLogger(__name__)
        self.rust_engine = RustEngineWrapper()
        
        # Check if Rust engine is available
        if not self.rust_engine.is_available():
            self.logger.warning("Rust FEA engine is not available - using simulation mode")
    
    def is_available(self) -> bool:
        """
        Check if the FEA analyzer is available.
        
        Returns:
            True if the analyzer is available, False otherwise
        """
        return self.rust_engine.is_available()
    
    def get_version(self) -> str:
        """
        Get the version of the FEA analyzer.
        
        Returns:
            Version string of the FEA analyzer
        """
        return self.rust_engine.get_version()
    
    def analyze_assembly(self, gear_profiles: Dict[str, np.ndarray], 
                        tooth_profiles: Dict[str, np.ndarray],
                        motion_law: Dict[str, Any], 
                        params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive assembly analysis including stress, vibration, and fatigue.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            tooth_profiles: Dictionary containing tooth profile data
            motion_law: Motion law data
            params: Analysis parameters
            
        Returns:
            Dictionary containing comprehensive analysis results
            
        Raises:
            ValueError: If input data is invalid
        """
        self.logger.info("Starting comprehensive assembly analysis")
        
        try:
            # Validate input data
            self._validate_input_data(gear_profiles, tooth_profiles, motion_law, params)
            
            # Create model file
            model_file = self._create_model_file(gear_profiles, tooth_profiles, motion_law, params)
            
            # Run stress analysis
            stress_analysis = self.run_stress_analysis(gear_profiles, tooth_profiles, params)
            
            # Run vibration analysis
            vibration_analysis = self.run_vibration_analysis(gear_profiles, motion_law, params)
            
            # Run fatigue analysis
            fatigue_analysis = self.run_fatigue_analysis(gear_profiles, tooth_profiles, params)
            
            # Compile analysis summary
            analysis_summary = self._compile_analysis_summary(
                stress_analysis, vibration_analysis, fatigue_analysis
            )
            
            result = {
                'stress_analysis': stress_analysis,
                'vibration_analysis': vibration_analysis,
                'fatigue_analysis': fatigue_analysis,
                'analysis_summary': analysis_summary
            }
            
            self.logger.info("Comprehensive assembly analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Assembly analysis failed: {str(e)}")
            raise
    
    def run_stress_analysis(self, gear_profiles: Dict[str, np.ndarray], 
                           tooth_profiles: Dict[str, np.ndarray],
                           params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run stress analysis on gear profiles.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            tooth_profiles: Dictionary containing tooth profile data
            params: Analysis parameters
            
        Returns:
            Dictionary containing stress analysis results
            
        Raises:
            ValueError: If input data is invalid
        """
        self.logger.info("Running stress analysis")
        
        try:
            # Validate input data
            self._validate_gear_profiles(gear_profiles)
            self._validate_tooth_profiles(tooth_profiles)
            
            # Create model file
            model_file = self._create_stress_model_file(gear_profiles, tooth_profiles, params)
            
            # Set up analysis parameters
            analysis_params = {
                'analysis_type': 'stress',
                'mesh_density': params.get('mesh_density', 'medium'),
                'solver_type': params.get('solver_type', 'direct'),
                'material_model': params.get('material_model', 'linear_elastic')
            }
            
            # Run analysis through Rust engine
            result = self.rust_engine.run_stress_analysis(model_file, analysis_params)
            
            # Post-process results
            processed_result = self._process_stress_results(result, gear_profiles, params)
            
            self.logger.info("Stress analysis completed successfully")
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Stress analysis failed: {str(e)}")
            raise
    
    def run_vibration_analysis(self, gear_profiles: Dict[str, np.ndarray], 
                              motion_law: Dict[str, Any], 
                              params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run vibration analysis on gear profiles.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            motion_law: Motion law data
            params: Analysis parameters
            
        Returns:
            Dictionary containing vibration analysis results
            
        Raises:
            ValueError: If input data is invalid
        """
        self.logger.info("Running vibration analysis")
        
        try:
            # Validate input data
            self._validate_gear_profiles(gear_profiles)
            self._validate_motion_law(motion_law)
            
            # Create model file
            model_file = self._create_vibration_model_file(gear_profiles, motion_law, params)
            
            # Set up analysis parameters
            analysis_params = {
                'analysis_type': 'vibration',
                'num_modes': params.get('num_modes', 10),
                'frequency_range': params.get('frequency_range', [0, 1000]),
                'damping_model': params.get('damping_model', 'rayleigh')
            }
            
            # Run analysis through Rust engine
            result = self.rust_engine.run_vibration_analysis(model_file, analysis_params)
            
            # Post-process results
            processed_result = self._process_vibration_results(result, gear_profiles, params)
            
            self.logger.info("Vibration analysis completed successfully")
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Vibration analysis failed: {str(e)}")
            raise
    
    def run_fatigue_analysis(self, gear_profiles: Dict[str, np.ndarray], 
                            tooth_profiles: Dict[str, np.ndarray],
                            params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run fatigue analysis on gear profiles.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            tooth_profiles: Dictionary containing tooth profile data
            params: Analysis parameters
            
        Returns:
            Dictionary containing fatigue analysis results
            
        Raises:
            ValueError: If input data is invalid
        """
        self.logger.info("Running fatigue analysis")
        
        try:
            # Validate input data
            self._validate_gear_profiles(gear_profiles)
            self._validate_tooth_profiles(tooth_profiles)
            
            # Create model file
            model_file = self._create_fatigue_model_file(gear_profiles, tooth_profiles, params)
            
            # Set up analysis parameters
            analysis_params = {
                'analysis_type': 'fatigue',
                'material_model': params.get('material_model', 'soderberg'),
                'safety_factor': params.get('safety_factor', 2.0),
                'load_cycles': params.get('load_cycles', 1000000)
            }
            
            # Run analysis through Rust engine
            result = self.rust_engine.run_fatigue_analysis(model_file, analysis_params)
            
            # Post-process results
            processed_result = self._process_fatigue_results(result, gear_profiles, params)
            
            self.logger.info("Fatigue analysis completed successfully")
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Fatigue analysis failed: {str(e)}")
            raise
    
    def _validate_input_data(self, gear_profiles: Dict[str, np.ndarray], 
                            tooth_profiles: Dict[str, np.ndarray],
                            motion_law: Dict[str, Any], 
                            params: Dict[str, Any]) -> None:
        """
        Validate input data for analysis.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            tooth_profiles: Dictionary containing tooth profile data
            motion_law: Motion law data
            params: Analysis parameters
            
        Raises:
            ValueError: If input data is invalid
        """
        self._validate_gear_profiles(gear_profiles)
        self._validate_tooth_profiles(tooth_profiles)
        self._validate_motion_law(motion_law)
        self._validate_params(params)
    
    def _validate_gear_profiles(self, gear_profiles: Dict[str, np.ndarray]) -> None:
        """
        Validate gear profiles data.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            
        Raises:
            ValueError: If gear profiles are invalid
        """
        if not isinstance(gear_profiles, dict):
            raise ValueError("Gear profiles must be a dictionary")
        
        required_keys = ['r_sun', 'r_planet', 'r_ring_inner']
        for key in required_keys:
            if key not in gear_profiles:
                raise ValueError(f"Missing required gear profile: {key}")
            
            if not isinstance(gear_profiles[key], np.ndarray):
                raise ValueError(f"Gear profile {key} must be a numpy array")
            
            if gear_profiles[key].size == 0:
                raise ValueError(f"Gear profile {key} cannot be empty")
    
    def _validate_tooth_profiles(self, tooth_profiles: Dict[str, np.ndarray]) -> None:
        """
        Validate tooth profiles data.
        
        Args:
            tooth_profiles: Dictionary containing tooth profile data
            
        Raises:
            ValueError: If tooth profiles are invalid
        """
        if not isinstance(tooth_profiles, dict):
            raise ValueError("Tooth profiles must be a dictionary")
        
        required_keys = ['sun_teeth', 'planet_teeth', 'ring_teeth']
        for key in required_keys:
            if key not in tooth_profiles:
                raise ValueError(f"Missing required tooth profile: {key}")
            
            if not isinstance(tooth_profiles[key], np.ndarray):
                raise ValueError(f"Tooth profile {key} must be a numpy array")
            
            if tooth_profiles[key].size == 0:
                raise ValueError(f"Tooth profile {key} cannot be empty")
    
    def _validate_motion_law(self, motion_law: Dict[str, Any]) -> None:
        """
        Validate motion law data.
        
        Args:
            motion_law: Motion law data
            
        Raises:
            ValueError: If motion law is invalid
        """
        if not isinstance(motion_law, dict):
            raise ValueError("Motion law must be a dictionary")
        
        required_keys = ['theta_deg', 'displacement', 'velocity', 'acceleration']
        for key in required_keys:
            if key not in motion_law:
                raise ValueError(f"Missing required motion law key: {key}")
            
            if not isinstance(motion_law[key], np.ndarray):
                raise ValueError(f"Motion law {key} must be a numpy array")
            
            if motion_law[key].size == 0:
                raise ValueError(f"Motion law {key} cannot be empty")
    
    def _validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate analysis parameters.
        
        Args:
            params: Analysis parameters
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(params, dict):
            raise ValueError("Parameters must be a dictionary")
        
        # Check for required parameters
        required_params = ['rpm', 'strokeLengthMm']
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
            
            if not isinstance(params[param], (int, float)):
                raise ValueError(f"Parameter {param} must be a number")
            
            if params[param] <= 0:
                raise ValueError(f"Parameter {param} must be positive")
    
    def _create_model_file(self, gear_profiles: Dict[str, np.ndarray], 
                          tooth_profiles: Dict[str, np.ndarray],
                          motion_law: Dict[str, Any], 
                          params: Dict[str, Any]) -> str:
        """
        Create model file for analysis.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            tooth_profiles: Dictionary containing tooth profile data
            motion_law: Motion law data
            params: Analysis parameters
            
        Returns:
            Path to the created model file
        """
        model_data = {
            'geometry': {
                'gear_profiles': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in gear_profiles.items()},
                'tooth_profiles': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in tooth_profiles.items()}
            },
            'motion_law': {
                'theta_deg': motion_law['theta_deg'].tolist(),
                'displacement': motion_law['displacement'].tolist(),
                'velocity': motion_law['velocity'].tolist(),
                'acceleration': motion_law['acceleration'].tolist()
            },
            'parameters': params
        }
        
        # Create temporary model file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(model_data, f, indent=2)
            return f.name
    
    def _create_stress_model_file(self, gear_profiles: Dict[str, np.ndarray], 
                                 tooth_profiles: Dict[str, np.ndarray],
                                 params: Dict[str, Any]) -> str:
        """
        Create model file for stress analysis.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            tooth_profiles: Dictionary containing tooth profile data
            params: Analysis parameters
            
        Returns:
            Path to the created model file
        """
        model_data = {
            'geometry': {
                'gear_profiles': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in gear_profiles.items()},
                'tooth_profiles': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in tooth_profiles.items()}
            },
            'material': {
                'youngs_modulus': params.get('youngs_modulus', 200000.0),
                'poisson_ratio': params.get('poisson_ratio', 0.3),
                'density': params.get('density', 7850.0)
            },
            'loads': {
                'contact_force': params.get('contact_force', 1000.0),
                'rpm': params.get('rpm', 3000.0)
            }
        }
        
        # Create temporary model file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(model_data, f, indent=2)
            return f.name
    
    def _create_vibration_model_file(self, gear_profiles: Dict[str, np.ndarray], 
                                    motion_law: Dict[str, Any], 
                                    params: Dict[str, Any]) -> str:
        """
        Create model file for vibration analysis.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            motion_law: Motion law data
            params: Analysis parameters
            
        Returns:
            Path to the created model file
        """
        model_data = {
            'geometry': {
                'gear_profiles': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in gear_profiles.items()}
            },
            'material': {
                'youngs_modulus': params.get('youngs_modulus', 200000.0),
                'poisson_ratio': params.get('poisson_ratio', 0.3),
                'density': params.get('density', 7850.0)
            },
            'boundary_conditions': {
                'fixed_nodes': params.get('fixed_nodes', [1, 2, 3]),
                'applied_forces': params.get('applied_forces', [1000.0, 1500.0, 2000.0])
            },
            'motion_law': {
                'theta_deg': motion_law['theta_deg'].tolist(),
                'displacement': motion_law['displacement'].tolist(),
                'velocity': motion_law['velocity'].tolist(),
                'acceleration': motion_law['acceleration'].tolist()
            }
        }
        
        # Create temporary model file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(model_data, f, indent=2)
            return f.name
    
    def _create_fatigue_model_file(self, gear_profiles: Dict[str, np.ndarray], 
                                  tooth_profiles: Dict[str, np.ndarray],
                                  params: Dict[str, Any]) -> str:
        """
        Create model file for fatigue analysis.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            tooth_profiles: Dictionary containing tooth profile data
            params: Analysis parameters
            
        Returns:
            Path to the created model file
        """
        model_data = {
            'geometry': {
                'gear_profiles': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in gear_profiles.items()},
                'tooth_profiles': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in tooth_profiles.items()}
            },
            'material': {
                'youngs_modulus': params.get('youngs_modulus', 200000.0),
                'poisson_ratio': params.get('poisson_ratio', 0.3),
                'density': params.get('density', 7850.0),
                'fatigue_limit': params.get('fatigue_limit', 300.0),
                'endurance_limit': params.get('endurance_limit', 250.0)
            },
            'load_cycles': {
                'max_stress': params.get('max_stress', 400.0),
                'min_stress': params.get('min_stress', 50.0),
                'cycles_per_second': params.get('cycles_per_second', 50.0)
            }
        }
        
        # Create temporary model file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(model_data, f, indent=2)
            return f.name
    
    def _process_stress_results(self, result: Dict[str, Any], 
                               gear_profiles: Dict[str, np.ndarray], 
                               params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process stress analysis results.
        
        Args:
            result: Raw stress analysis results
            gear_profiles: Dictionary containing gear profile data
            params: Analysis parameters
            
        Returns:
            Processed stress analysis results
        """
        # Add additional processing if needed
        processed_result = result.copy()
        
        # Add gear-specific stress analysis
        processed_result['gear_stress_analysis'] = {
            'sun_max_stress': result['max_stress'] * 0.8,
            'planet_max_stress': result['max_stress'] * 1.0,
            'ring_max_stress': result['max_stress'] * 0.9
        }
        
        return processed_result
    
    def _process_vibration_results(self, result: Dict[str, Any], 
                                  gear_profiles: Dict[str, np.ndarray], 
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process vibration analysis results.
        
        Args:
            result: Raw vibration analysis results
            gear_profiles: Dictionary containing gear profile data
            params: Analysis parameters
            
        Returns:
            Processed vibration analysis results
        """
        # Add additional processing if needed
        processed_result = result.copy()
        
        # Add gear-specific vibration analysis
        processed_result['gear_vibration_analysis'] = {
            'sun_natural_frequencies': result['natural_frequencies'][:3],
            'planet_natural_frequencies': result['natural_frequencies'][3:6],
            'ring_natural_frequencies': result['natural_frequencies'][6:9]
        }
        
        return processed_result
    
    def _process_fatigue_results(self, result: Dict[str, Any], 
                                gear_profiles: Dict[str, np.ndarray], 
                                params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process fatigue analysis results.
        
        Args:
            result: Raw fatigue analysis results
            gear_profiles: Dictionary containing gear profile data
            params: Analysis parameters
            
        Returns:
            Processed fatigue analysis results
        """
        # Add additional processing if needed
        processed_result = result.copy()
        
        # Add gear-specific fatigue analysis
        processed_result['gear_fatigue_analysis'] = {
            'sun_fatigue_life': result['fatigue_life'] * 1.2,
            'planet_fatigue_life': result['fatigue_life'] * 1.0,
            'ring_fatigue_life': result['fatigue_life'] * 1.1
        }
        
        return processed_result
    
    def _compile_analysis_summary(self, stress_analysis: Dict[str, Any], 
                                 vibration_analysis: Dict[str, Any], 
                                 fatigue_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compile analysis summary from all analysis results.
        
        Args:
            stress_analysis: Stress analysis results
            vibration_analysis: Vibration analysis results
            fatigue_analysis: Fatigue analysis results
            
        Returns:
            Analysis summary
        """
        return {
            'overall_status': 'ok',
            'max_stress': stress_analysis['max_stress'],
            'safety_factor': stress_analysis['safety_factor'],
            'natural_frequencies': vibration_analysis['natural_frequencies'],
            'fatigue_life': fatigue_analysis['fatigue_life'],
            'recommendations': self._generate_recommendations(
                stress_analysis, vibration_analysis, fatigue_analysis
            )
        }
    
    def _generate_recommendations(self, stress_analysis: Dict[str, Any], 
                                 vibration_analysis: Dict[str, Any], 
                                 fatigue_analysis: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on analysis results.
        
        Args:
            stress_analysis: Stress analysis results
            vibration_analysis: Vibration analysis results
            fatigue_analysis: Fatigue analysis results
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Stress-based recommendations
        if stress_analysis['safety_factor'] < 2.0:
            recommendations.append("Consider increasing material strength or reducing loads")
        
        # Vibration-based recommendations
        if any(freq < 50 for freq in vibration_analysis['natural_frequencies']):
            recommendations.append("Consider stiffening the structure to avoid low-frequency vibrations")
        
        # Fatigue-based recommendations
        if fatigue_analysis['fatigue_life'] < 1000000:
            recommendations.append("Consider improving surface finish or using fatigue-resistant materials")
        
        return recommendations
    
    def _convert_python_to_rust(self, python_data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Python data format to Rust engine format.
        
        Args:
            python_data: Python data dictionary
            params: Analysis parameters
            
        Returns:
            Rust engine compatible data dictionary
        """
        # In a real implementation, this would convert Python data
        # to the format expected by the Rust engine
        return python_data.copy()
    
    def _convert_rust_to_python(self, rust_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Rust engine data format to Python format.
        
        Args:
            rust_data: Rust engine data dictionary
            
        Returns:
            Python compatible data dictionary
        """
        # In a real implementation, this would convert Rust engine data
        # to Python format
        return rust_data.copy()
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """
        Get information about the FEA analyzer.
        
        Returns:
            Dictionary containing analyzer information
        """
        return {
            'analyzer_type': 'fea',
            'description': 'FEA analyzer for comprehensive gear analysis',
            'features': [
                'stress_analysis',
                'vibration_analysis',
                'fatigue_analysis',
                'assembly_analysis'
            ],
            'dependencies': ['rust_fea_engine', 'jni'],
            'version': self.get_version(),
            'available': self.is_available()
        }
