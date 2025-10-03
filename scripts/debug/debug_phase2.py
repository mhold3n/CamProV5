#!/usr/bin/env python3
"""
Debug script for Phase 2 gear optimization issues.
"""

import sys
import numpy as np
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters  # noqa: E402
from campro.logging import get_logger  # noqa: E402

# Set up logging
logger = get_logger(__name__)

def test_phase2_debug():
    """Test Phase 2 with minimal data to identify the issue."""
    logger.info("🔍 DEBUGGING PHASE 2 GEAR OPTIMIZATION")
    logger.info("=" * 50)
    
    # Create dummy motion law data (what Phase 1 would produce)
    n = 32  # Number of collocation points
    theta = np.linspace(0, 2*np.pi, n)
    
    motion_law = {
        'displacement': np.linspace(0, 20.0, n),  # 20mm stroke
        'velocity': np.sin(theta) * 10.0,  # Simple sinusoidal velocity
        'acceleration': np.cos(theta) * 5.0,  # Simple sinusoidal acceleration
        'grid': theta,
        'success': True,
        'objective_value': 0.016,
        'constraint_violation': 1e-14,
        'iterations': 5,
        'execution_time': 0.5,
        'solver_status': 'Solve_Succeeded'
    }
    
    # Create gear parameters
    gear_params = {
        'strokeLengthMm': 20.0,
        'ringRotationDeg': 180.0,
        'samplingStepDeg': 1.0,
        'maxAcceleration': 200.0,
        'maxVelocity': 100.0,
        'nodeCount': 32,
        'maxIterations': 1000,
        'tolerance': 1e-04,
        'constraintTolerance': 1e-04,
        'forceTransferWeight': 1.0,
        'efficiencyWeight': 1.0,
        'smoothnessWeight': 0.1,
        'clearanceSafetyMargin': 0.1,
        'minGearClearance': 0.05,
        'pistonAreaMm2': 100.0,
        'cylinderPressureBar': 10.0,
        'materialStrengthMpa': 500.0
    }
    
    # Create Phase 2 parameters
    phase2_params = Phase2Parameters(
        node_count=32,
        max_iterations=1000,
        tolerance=1e-02,
        constraint_tolerance=1e-02,
        force_transfer_weight=1.0,
        efficiency_weight=1.0,
        smoothness_weight=0.1,
        clearance_safety_margin=0.1,
        min_gear_clearance=0.05,
        piston_area_mm2=100.0,
        cylinder_pressure_bar=10.0,
        material_strength_mpa=500.0
    )
    
    # Create Phase 2 optimizer
    phase2_optimizer = Phase2GearOptimizer(phase2_params)
    
    logger.info("📊 Motion law data:")
    logger.info(f"  Displacement shape: {motion_law['displacement'].shape}")
    logger.info(f"  Velocity shape: {motion_law['velocity'].shape}")
    logger.info(f"  Acceleration shape: {motion_law['acceleration'].shape}")
    logger.info(f"  Grid shape: {motion_law['grid'].shape}")
    
    try:
        logger.info("\n🚀 Running Phase 2 optimization...")
        result = phase2_optimizer.optimize_gear_profiles(motion_law, gear_params)
        
        logger.info("✅ Phase 2 completed successfully!")
        logger.info(f"  Success: {result.success}")
        logger.info(f"  Execution time: {result.execution_time:.3f}s")
        logger.info(f"  Iterations: {result.iterations}")
        logger.info(f"  Objective value: {result.objective_value:.6f}")
        logger.info(f"  Constraint violation: {result.constraint_violation:.6f}")
        logger.info(f"  Solver status: {result.solver_status}")
        
    except Exception as e:
        logger.info(f"❌ Phase 2 failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_phase2_debug()
