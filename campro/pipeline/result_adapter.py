"""
Result format adapter for enhanced optimizers.
Ensures enhanced optimizers return data in the format expected by downstream components.
"""

from typing import Dict, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)

from campro.optimization.solver_utils import solution_to_dict


class ResultAdapter:
    """Adapts enhanced optimizer results to expected format."""
    
    @staticmethod
    def adapt_motion_law_result(enhanced_result: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt enhanced motion law result to expected format."""
        logger.debug("Adapting enhanced motion law result to expected format")

        enhanced_result = solution_to_dict(enhanced_result)
        
        # Convert lists to numpy arrays for FEA analyzer compatibility
        def ensure_numpy_array(data):
            if isinstance(data, list):
                return np.array(data)
            elif isinstance(data, np.ndarray):
                return data
            else:
                return np.array([data]) if data is not None else np.array([])
        
        return {
            'grid': ensure_numpy_array(enhanced_result.get('grid', [])),
            'theta_deg': ensure_numpy_array(enhanced_result.get('theta_deg', [])),
            'displacement': ensure_numpy_array(enhanced_result.get('displacement', [])),
            'velocity': ensure_numpy_array(enhanced_result.get('velocity', [])),
            'acceleration': ensure_numpy_array(enhanced_result.get('acceleration', [])),
            'success': enhanced_result.get('success', False),
            'solver_status': enhanced_result.get('solver_status', 'Unknown'),
            # Add thermodynamic data for advanced analysis
            'thermodynamic_data': enhanced_result.get('thermodynamic_data', {})
        }
    
    @staticmethod
    def adapt_gear_result(enhanced_result: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt enhanced gear result to expected format."""
        logger.debug("Adapting enhanced gear result to expected format")

        enhanced_result = solution_to_dict(enhanced_result)
        
        # Convert lists to numpy arrays for FEA analyzer compatibility
        def ensure_numpy_array(data):
            if isinstance(data, list):
                return np.array(data)
            elif isinstance(data, np.ndarray):
                return data
            else:
                return np.array([data]) if data is not None else np.array([])
        
        theta_raw = enhanced_result.get('theta_grid', [])
        theta_array = ensure_numpy_array(theta_raw)
        if theta_array.size and np.max(np.abs(theta_array)) <= (2 * np.pi + 1e-6):
            theta_array = np.degrees(theta_array)

        accum_angle = enhanced_result.get('accumulated_planet_angle_deg', 0.0)
        if isinstance(accum_angle, (list, tuple, np.ndarray)):
            accum_angle = np.asarray(accum_angle, dtype=float)
            accum_angle = float(accum_angle.flatten()[0]) if accum_angle.size else 0.0
        if abs(accum_angle) <= (2 * np.pi + 1e-6):
            accum_angle = float(np.degrees(accum_angle))

        phi_planet = enhanced_result.get('phi_planet')
        if phi_planet is not None:
            phi_planet = ensure_numpy_array(phi_planet)
            if phi_planet.size and np.max(np.abs(phi_planet)) <= (2 * np.pi + 1e-6):
                phi_planet = np.degrees(phi_planet)

        return {
            'theta_deg': theta_array,
            'r_sun': ensure_numpy_array(enhanced_result.get('sun_radius', [])),
            'r_planet': ensure_numpy_array(enhanced_result.get('planet_radius', [])),
            'r_ring_inner': ensure_numpy_array(enhanced_result.get('ring_radius', [])),
            'instantaneous_ratio': ensure_numpy_array(enhanced_result.get('instantaneous_ratio', [])),
            'journal_offset': ensure_numpy_array(enhanced_result.get('journal_offset', [])),
            'accumulated_planet_angle_deg': accum_angle,
            'gear_clearance': ensure_numpy_array(enhanced_result.get('gear_clearance', [])),
            'force_transfer_efficiency': ensure_numpy_array(enhanced_result.get('force_transfer_efficiency', [])),
            'max_contact_stress': enhanced_result.get('max_contact_stress', 0.0),
            'objective_value': enhanced_result.get('objective_value', 0.0),
            'constraint_violation': enhanced_result.get('constraint_violation', 0.0),
            'iterations': enhanced_result.get('iterations', 0),
            'execution_time': enhanced_result.get('execution_time', 0.0),
            'solver_status': enhanced_result.get('solver_status', 'Unknown'),
            'success': enhanced_result.get('success', False),
            'phi_planet_deg': phi_planet,
            # Add transmission data for advanced analysis
            'transmission_data': enhanced_result.get('transmission_data', {})
        }
    
    @staticmethod
    def validate_motion_law_result(result: Dict[str, Any]) -> bool:
        """Validate that motion law result has required fields."""
        required_fields = ['grid', 'theta_deg', 'displacement', 'velocity', 'acceleration']
        
        for field in required_fields:
            if field not in result:
                logger.error(f"Missing required field in motion law result: {field}")
                return False
            
            if not isinstance(result[field], (list, np.ndarray)):
                logger.error(f"Field {field} should be a list or array, got {type(result[field])}")
                return False
            
            if len(result[field]) == 0:
                logger.error(f"Field {field} is empty")
                return False
        
        # Check that all arrays have the same length
        lengths = [len(result[field]) for field in required_fields]
        if len(set(lengths)) > 1:
            logger.error(f"Inconsistent array lengths in motion law result: {dict(zip(required_fields, lengths))}")
            return False
        
        logger.debug("Motion law result validation passed")
        return True
    
    @staticmethod
    def validate_gear_result(result: Dict[str, Any]) -> bool:
        """Validate that gear result has required fields."""
        required_fields = ['theta_deg', 'r_sun', 'r_planet', 'r_ring_inner', 'instantaneous_ratio']
        
        for field in required_fields:
            if field not in result:
                logger.error(f"Missing required field in gear result: {field}")
                return False
            
            if not isinstance(result[field], (list, np.ndarray)):
                logger.error(f"Field {field} should be a list or array, got {type(result[field])}")
                return False
            
            if len(result[field]) == 0:
                logger.error(f"Field {field} is empty")
                return False
        
        # Check that all arrays have the same length
        lengths = [len(result[field]) for field in required_fields]
        if len(set(lengths)) > 1:
            logger.error(f"Inconsistent array lengths in gear result: {dict(zip(required_fields, lengths))}")
            return False
        
        logger.debug("Gear result validation passed")
        return True
    
    @staticmethod
    def add_performance_metrics(result: Dict[str, Any], performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add performance metrics to result."""
        result['performance'] = performance_data
        return result
    
    @staticmethod
    def ensure_numpy_arrays(result: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all array fields are numpy arrays."""
        array_fields = ['grid', 'theta_deg', 'displacement', 'velocity', 'acceleration', 
                       'r_sun', 'r_planet', 'r_ring_inner', 'instantaneous_ratio', 
                       'journal_offset', 'gear_clearance', 'force_transfer_efficiency']
        
        for field in array_fields:
            if field in result and isinstance(result[field], list):
                result[field] = np.array(result[field])
        
        return result
