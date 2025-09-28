#!/usr/bin/env python3
"""
Demo script to run the unified optimization pipeline.
"""

import sys
import json
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from campro.pipeline.unified_optimizer import UnifiedOptimizer


def get_test_parameters():
    """Get comprehensive test parameters."""
    return {
        "samplingStepDeg": 1.0,
        "ringRotationDeg": 180.0,
        "gearRatio": 2.0,
        "strokeLengthMm": 100.0,
        "rodLength": 100.0,
        "journalRadius": 5.0,
        "interferenceBuffer": 0.5,
        "ringThickness": 3.0,
        "rpm": 3000.0,
        "planetCount": 2,
        "carrierOffsetDeg": 180.0,
        "rampBeforeTdcDeg": 6.0,
        "rampAfterTdcDeg": 5.0,
        "dwellTdcDeg": 4.0,
        "rampBeforeBdcDeg": 7.0,
        "rampAfterBdcDeg": 4.0,
        "dwellBdcDeg": 3.0,
        "constantVelocityTdcDeg": 30.0,
        "constantVelocityBdcDeg": 40.0,
        "planetRadiusBaseFactor": 0.15,
        "planetRadiusVariationFactor": 0.05,
        "sunRadiusBaseFactor": 0.1,
        "sunRadiusVariationFactor": 0.02,
        "strokeAchievableFactor": 0.8,
        "clearanceSafetyMargin": 0.1,
        "adjustmentSplitFactor": 0.5
    }


def main():
    """Run the unified optimization pipeline demo."""
    print("🚀 CAMPROV5 UNIFIED OPTIMIZATION PIPELINE DEMO")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("pipeline_demo_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get test parameters
    params = get_test_parameters()
    
    print(f"\n📋 TEST PARAMETERS:")
    print(f"  • Stroke Length: {params['strokeLengthMm']} mm")
    print(f"  • Gear Ratio: {params['gearRatio']}:1")
    print(f"  • Ring Rotation: {params['ringRotationDeg']}°")
    print(f"  • Planet Count: {params['planetCount']}")
    print(f"  • RPM: {params['rpm']}")
    
    # Initialize optimizer
    print(f"\n🔧 INITIALIZING UNIFIED OPTIMIZER...")
    optimizer = UnifiedOptimizer(output_dir=output_dir)
    
    # Run pipeline
    print(f"\n⚡ RUNNING UNIFIED OPTIMIZATION PIPELINE...")
    start_time = time.time()
    
    try:
        result = optimizer.run_pipeline(params)
        execution_time = time.time() - start_time
        
        print(f"\n📊 RESULTS:")
        print(f"  • Status: {result['status']}")
        print(f"  • Execution Time: {execution_time:.2f} seconds")
        
        if result['status'] == 'success':
            motion_law = result['motion_law']
            print(f"  • Motion Law Points: {len(motion_law['theta_deg'])}")
            print(f"  • Max Displacement: {max(motion_law['displacement']):.1f} mm")
            
            optimal_profiles = result['optimal_profiles']
            print(f"  • Optimal Method: {optimal_profiles['optimal_solution']}")
            
            print(f"\n✅ DEMO COMPLETED SUCCESSFULLY!")
        else:
            print(f"  • Error: {result.get('error', 'Unknown')}")
            print(f"\n⚠️  DEMO COMPLETED WITH ISSUES")
        
        # Save results
        results_file = output_dir / "results.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  • Results saved to: {results_file}")
        
    except Exception as e:
        print(f"\n❌ DEMO FAILED: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
