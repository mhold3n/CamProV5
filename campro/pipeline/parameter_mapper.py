"""
Parameter mapping layer for enhanced optimizers.
Converts UI parameters to enhanced optimizer parameter structures.
"""

from typing import Dict, Any
from campro.optimization.enhanced_motion_law_optimizer import EnhancedMotionLawParameters
from campro.optimization.enhanced_gear_optimizer import EnhancedGearParameters
import logging
import math

logger = logging.getLogger(__name__)


class ParameterMapper:
    """Maps UI parameters to enhanced optimizer parameters."""
    
    @staticmethod
    def map_to_enhanced_motion_params(ui_params: Dict[str, Any]) -> EnhancedMotionLawParameters:
        """Convert UI parameters to enhanced motion law parameters."""
        logger.info("Mapping UI parameters to enhanced motion law parameters")

        # Validate and sanitize parameters
        node_count = ui_params.get('nodeCount', 32)
        if node_count < 4:
            logger.warning(f"Invalid node count {node_count}, using minimum of 4")
            node_count = 4

        piston_area_mm2 = ui_params.get('pistonAreaMm2')
        piston_diameter_mm = ui_params.get('pistonDiameterMm')
        if piston_area_mm2 is None and piston_diameter_mm is not None:
            try:
                piston_area_mm2 = math.pi * float(piston_diameter_mm) ** 2 / 4.0
            except (TypeError, ValueError):
                piston_area_mm2 = None

        if piston_area_mm2 is not None:
            try:
                piston_area_m2 = float(piston_area_mm2) * 1e-6
            except (TypeError, ValueError):
                piston_area_m2 = 0.01
                logger.warning("Invalid pistonAreaMm2 provided; falling back to default 0.01 m^2")
        else:
            piston_area_m2 = 0.01
            logger.debug("pistonAreaMm2 not provided; using default 0.01 m^2")

        return EnhancedMotionLawParameters(
            # Map existing UI parameters
            node_count=node_count,
            max_iterations=ui_params.get('maxIterations', 1000),
            tolerance=ui_params.get('tolerance', 1e-8),
            constraint_tolerance=ui_params.get('constraintTolerance', 1e-6),
            smoothness_weight=ui_params.get('smoothnessWeight', 1e-3),
            velocity_weight=ui_params.get('velocityWeight', 1e-4),
            displacement_weight=ui_params.get('displacementWeight', 1e-6),
            jerk_weight=ui_params.get('jerkWeight', 1e-5),

            # Map thermodynamic optimization weights
            work_weight=ui_params.get('workWeight', 1.0),
            pressure_weight=ui_params.get('pressureWeight', 0.1),
            valve_weight=ui_params.get('valveWeight', 0.01),
            combustion_weight=ui_params.get('combustionWeight', 0.1),

            piston_area_m2=piston_area_m2
        )
    
    @staticmethod
    def map_to_enhanced_gear_params(ui_params: Dict[str, Any]) -> EnhancedGearParameters:
        """Convert UI parameters to enhanced gear parameters."""
        logger.info("Mapping UI parameters to enhanced gear parameters")
        
        # Validate and sanitize parameters
        node_count = ui_params.get('nodeCount', 32)
        if node_count < 4:
            logger.warning(f"Invalid node count {node_count}, using minimum of 4")
            node_count = 4

        piston_area_mm2 = ui_params.get('pistonAreaMm2')
        piston_diameter_mm = ui_params.get('pistonDiameterMm')
        if piston_area_mm2 is None and piston_diameter_mm is not None:
            try:
                piston_area_mm2 = math.pi * float(piston_diameter_mm) ** 2 / 4.0
            except (TypeError, ValueError):
                piston_area_mm2 = None

        if piston_area_mm2 is not None:
            try:
                piston_area_mm2 = float(piston_area_mm2)
            except (TypeError, ValueError):
                logger.warning("Invalid pistonAreaMm2 provided; falling back to default 100.0 mm^2")
                piston_area_mm2 = 100.0
        else:
            piston_area_mm2 = 100.0
            logger.debug("pistonAreaMm2 not provided; using default 100 mm^2")

        return EnhancedGearParameters(
            # Map existing UI parameters
            node_count=node_count,
            max_iterations=ui_params.get('maxIterations', 500),
            tolerance=ui_params.get('tolerance', 1e-6),
            constraint_tolerance=ui_params.get('constraintTolerance', 1e-6),
            force_transfer_weight=ui_params.get('forceTransferWeight', 1.0),
            efficiency_weight=ui_params.get('efficiencyWeight', 1.0),
            smoothness_weight=ui_params.get('smoothnessWeight', 0.1),
            min_contact_force=ui_params.get('minContactForce', 100.0),
            max_contact_stress=ui_params.get('maxContactStress', 1000.0),  # MPa
            
            # Map transmission optimization weights
            kinematic_weight=ui_params.get('kinematicWeight', 1.0),
            power_balance_weight=ui_params.get('powerBalanceWeight', 1.0),
            contact_stress_weight=ui_params.get('contactStressWeight', 0.1),
            friction_weight=ui_params.get('frictionWeight', 0.1),
            fatigue_weight=ui_params.get('fatigueWeight', 1.0),

            piston_area_mm2=piston_area_mm2
        )
