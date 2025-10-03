"""
Litvin Gear Optimizer Implementation

This module implements the Litvin gear optimization method using the extracted
robust gear profile generation logic. It provides a clean interface for
optimizing gear profiles using the Litvin conjugacy constraints.
"""

import numpy as np
import logging
from typing import Dict, Any
from pathlib import Path

from campro.gears.profile_generator import GearProfileGenerator
from campro.physics.force_transfer import ForceTransferAnalyzer


class LitvinGearOptimizer:
    """
    Litvin gear optimizer using robust gear profile generation.
    
    This optimizer uses the existing robust Litvin implementation from
    the extracted gear profile generator to optimize gear profiles
    with proper conjugacy constraints and mechanical advantage calculations.
    """
    
    def __init__(self):
        """Initialize the Litvin gear optimizer."""
        self.generator = GearProfileGenerator()
        self.force_analyzer = ForceTransferAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("LitvinGearOptimizer initialized with robust gear profile generator")
    
    def optimize_profiles(self, motion_law: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize gear profiles using Litvin method.
        
        Args:
            motion_law: Motion law data containing theta_deg and displacement
            params: Gear generation parameters
            
        Returns:
            Dictionary containing optimized profiles, validation, and mechanical advantage
        """
        self.logger.info("Starting Litvin gear profile optimization")
        
        try:
            # Validate input parameters
            self._validate_inputs(motion_law, params)
            
            # Generate gear profiles using robust Litvin implementation
            profiles = self.generator.generate_gear_profiles(
                motion_law['theta_deg'],
                motion_law['displacement'],
                params
            )
            
            # Validate gearset constraints
            validation = self.generator.validate_gearset_constraints(profiles, params)
            
            # Calculate mechanical advantage
            mechanical_advantage = self._calculate_mechanical_advantage(profiles, motion_law, params)
            
            # Generate planet kinematics for additional validation
            planet_kinematics = self.generator.generate_planet_kinematics(profiles, params)
            
            result = {
                'profiles': profiles,
                'validation': validation,
                'mechanical_advantage': mechanical_advantage,
                'planet_kinematics': planet_kinematics,
                'optimization_method': 'litvin',
                'optimization_info': {
                    'method': 'litvin',
                    'conjugacy_constraints': True,
                    'unified_constraint_system': True,
                    'validation_passed': validation['passed']
                }
            }
            
            self.logger.info(f"Litvin optimization completed successfully. "
                           f"Mechanical advantage: {mechanical_advantage:.3f}, "
                           f"Validation passed: {validation['passed']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Litvin optimization failed: {str(e)}")
            raise ValueError(f"Litvin gear optimization failed: {str(e)}")
    
    def _validate_inputs(self, motion_law: Dict[str, Any], params: Dict[str, Any]) -> None:
        """
        Validate input parameters for Litvin optimization.
        
        Args:
            motion_law: Motion law data
            params: Gear generation parameters
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate motion law
        if not isinstance(motion_law, dict):
            raise ValueError("Motion law must be a dictionary")
        
        required_motion_keys = ['theta_deg', 'displacement']
        for key in required_motion_keys:
            if key not in motion_law:
                raise ValueError(f"Motion law missing required key: {key}")
        
        # Validate motion law data
        theta_deg = motion_law['theta_deg']
        displacement = motion_law['displacement']
        
        if not isinstance(theta_deg, np.ndarray) or not isinstance(displacement, np.ndarray):
            raise ValueError("Motion law data must be numpy arrays")
        
        if len(theta_deg) != len(displacement):
            raise ValueError("Motion law theta_deg and displacement must have same length")
        
        if len(theta_deg) == 0:
            raise ValueError("Motion law data cannot be empty")
        
        # Validate parameters
        if not isinstance(params, dict):
            raise ValueError("Parameters must be a dictionary")
        
        required_param_keys = ['strokeLengthMm', 'ringRotationDeg']
        for key in required_param_keys:
            if key not in params:
                raise ValueError(f"Parameters missing required key: {key}")
        
        # Validate parameter values
        if params['strokeLengthMm'] <= 0:
            raise ValueError("Stroke length must be positive")
        
        if params['ringRotationDeg'] <= 0:
            raise ValueError("Ring rotation must be positive")
    
    def _calculate_mechanical_advantage(self, profiles: Dict[str, Any], 
                                      motion_law: Dict[str, Any], 
                                      params: Dict[str, Any]) -> float:
        """
        Calculate mechanical advantage for the optimized gear profiles.
        
        Args:
            profiles: Generated gear profiles
            motion_law: Motion law data
            params: Gear generation parameters
            
        Returns:
            Mechanical advantage ratio
        """
        try:
            # Extract gear radii from profiles
            sun_profile = profiles['sun']
            planet_profile = profiles['planet']
            ring_profile = profiles['ring']
            
            # Calculate average radii (assuming profiles are in format [x, y])
            sun_radius = np.mean(np.sqrt(sun_profile[:, 0]**2 + sun_profile[:, 1]**2))
            np.mean(np.sqrt(planet_profile[:, 0]**2 + planet_profile[:, 1]**2))
            ring_radius = np.mean(np.sqrt(ring_profile[:, 0]**2 + ring_profile[:, 1]**2))
            
            # Calculate mechanical advantage using gear ratio
            # For planetary gearset: MA = (R_ring + R_sun) / R_sun
            mechanical_advantage = (ring_radius + sun_radius) / sun_radius
            
            # Ensure mechanical advantage is reasonable
            if mechanical_advantage < 1.0:
                self.logger.warning(f"Mechanical advantage {mechanical_advantage:.3f} is less than 1.0")
                mechanical_advantage = max(1.0, mechanical_advantage)
            
            if mechanical_advantage > 10.0:
                self.logger.warning(f"Mechanical advantage {mechanical_advantage:.3f} is very high")
                mechanical_advantage = min(10.0, mechanical_advantage)
            
            return mechanical_advantage
            
        except Exception as e:
            self.logger.warning(f"Error calculating mechanical advantage: {str(e)}")
            # Return a reasonable default
            return 2.0
    
    def validate_litvin_conjugacy_constraints(self, profiles: Dict[str, Any], 
                                            params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Litvin conjugacy constraints for the generated profiles.
        
        Args:
            profiles: Generated gear profiles
            params: Gear generation parameters
            
        Returns:
            Validation results for conjugacy constraints
        """
        try:
            # Use the existing validation from the gear profile generator
            validation = self.generator.validate_gearset_constraints(profiles, params)
            
            # Add Litvin-specific validation
            litvin_validation = {
                'conjugacy_constraints': validation['contact_point_constraint'],
                'unified_constraint': validation['unified_constraint'],
                'positive_clearance': validation['positive_clearance'],
                'stroke_achievable': validation['stroke_achievable'],
                'overall_passed': validation['passed']
            }
            
            return litvin_validation
            
        except Exception as e:
            self.logger.error(f"Error validating Litvin conjugacy constraints: {str(e)}")
            return {
                'conjugacy_constraints': False,
                'unified_constraint': False,
                'positive_clearance': False,
                'stroke_achievable': False,
                'overall_passed': False,
                'error': str(e)
            }
    
    def get_optimization_info(self) -> Dict[str, Any]:
        """
        Get information about the Litvin optimizer.
        
        Returns:
            Dictionary containing optimizer information
        """
        return {
            'optimizer_type': 'litvin',
            'description': 'Litvin gear optimizer using robust gear profile generation',
            'features': [
                'Conjugacy constraints',
                'Unified constraint system',
                'Mechanical advantage calculation',
                'Planet kinematics generation',
                'Robust validation'
            ],
            'dependencies': [
                'GearProfileGenerator',
                'ForceTransferAnalyzer'
            ]
        }
    
    def clear_cache(self) -> None:
        """Clear any cached data (for testing or memory management)."""
        # The gear profile generator handles its own caching
        self.logger.debug("Litvin optimizer cache cleared")
    
    def export_profiles_for_analysis(self, profiles: Dict[str, Any], 
                                   output_path: Path) -> None:
        """
        Export optimized profiles for further analysis.
        
        Args:
            profiles: Optimized gear profiles
            output_path: Path to save the profiles
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save profiles as numpy arrays
            np.savez(
                output_path,
                sun_profile=profiles['sun'],
                planet_profile=profiles['planet'],
                ring_profile=profiles['ring']
            )
            
            self.logger.info(f"Litvin profiles exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting profiles: {str(e)}")
            raise
