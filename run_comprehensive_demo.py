#!/usr/bin/env python3
"""
Comprehensive demo using the full test dataset from generate_gear_profiles.py.
"""

import sys
import json
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from campro.pipeline.unified_optimizer import UnifiedOptimizer


def get_comprehensive_test_parameters():
    """Get the comprehensive test parameters from generate_gear_profiles.py."""
    return {
        # CORRECTED: 2-stroke cycle over 180° ring rotation, 360° planet rotation
        "ringRotationDeg": 180.0,  # Ring rotates 180° for complete 2-stroke cycle
        "planetRotationDeg": 360.0,  # Planet rotates 360° for complete 2-stroke cycle
        "gearRatio": 2.0,  # Planet:Ring ratio = 360:180 = 2:1

        # Asymmetric stroke durations within 180° ring rotation
        "expansionDurationDeg": 110.0,  # 220° expansion scaled to 180° ring rotation
        "compressionDurationDeg": 70.0,  # 140° compression scaled to 180° ring rotation

        # CORRECTED: Motion law with small acceleration ramps and large constant velocity zones
        "rampBeforeTdcDeg": 6.0,   # Small ramp to accelerate to constant velocity
        "rampAfterTdcDeg": 5.0,    # Small ramp to decelerate from constant velocity
        "rampBeforeBdcDeg": 7.0,   # Small ramp to accelerate to constant velocity
        "rampAfterBdcDeg": 4.0,    # Small ramp to decelerate from constant velocity
        
        # Short dwell periods at TDC and BDC (3-5° each)
        "dwellTdcDeg": 4.0,        # Short dwell at TDC
        "dwellBdcDeg": 3.0,        # Short dwell at BDC
        
        # Linear acceleration periods (constant velocity through most of stroke)
        "linearAccelTdcDeg": 8.0,  # Small window for linear acceleration near TDC
        "linearAccelBdcDeg": 6.0,  # Small window for linear acceleration near BDC
        
        # Motion law parameters
        "strokeLengthMm": 100.0,
        "upFraction": 110.0 / 180.0,  # Asymmetric up/down ratio within 180° ring rotation
        "rodLength": 100.0,
        "rampProfile": "S5",

        # Planetary gearset parameters
        "samplingStepDeg": 1.0,
        "interferenceBuffer": 0.5,
        "planetCount": 2,
        "carrierOffsetDeg": 180.0,
        "ringThicknessVisual": 6.0,
        "arcResidualTolMm": 0.01,
        "sliderAxisDeg": 0.0,
        "journalPhaseBetaDeg": 0.0,
        "journalRadius": 5.0,
        
        # CORRECTED: Proper planetary gearset geometry
        "planetRadius": 15.0,  # Fixed planet radius (not max, but actual)
        "ringInnerRadiusBase": 70.0,  # Base ring inner radius (must be > planet radius)
        "ringInnerRadiusVariation": 10.0,  # Variation in ring inner radius for non-circular profile
        "ringThickness": 3.0,  # Ring gear thickness (outer - inner radius)
        "centerDistance": 85.0,  # Distance from center to planet centers
        "rpm": 3000.0,
        
        # Specific tooth meshing parameters
        "planetTeeth": 20,  # Number of teeth on planet gear
        "ringTeeth": 40,  # Number of teeth on ring gear (2:1 ratio)
        "toothModule": 2.0,  # Module for gear tooth sizing
        
        # Planet COM and journal parameters
        "journalOffsetRadius": 5.0,  # mm offset from planet COM to journal
        "journalAngleOffset": 0.0,  # degrees offset from planet COM to journal
        
        # Gear profile scaling parameters
        "planetRadiusBaseFactor": 0.15,  # Planet radius as fraction of max rod extension
        "planetRadiusVariationFactor": 0.05,  # Planet radius variation as fraction of max rod extension
        "sunRadiusBaseFactor": 0.1,  # Sun radius as fraction of max rod extension
        "sunRadiusVariationFactor": 0.02,  # Sun radius variation as fraction of max rod extension
        "planetRadiusMinFactor": 0.8,  # Minimum planet radius as fraction of base
        "sunRadiusMinFactor": 0.9,  # Minimum sun radius as fraction of base
        
        # Motion law phase parameters
        "constantVelocityTdcDeg": 30.0,  # Constant velocity duration at TDC
        "constantVelocityBdcDeg": 40.0,  # Constant velocity duration at BDC
        
        # Physics parameters for optimization
        "cylinderPressure": 2.0e5,  # Pa (2 bar cylinder pressure)
        "pistonArea": 0.01,  # m² (100 cm² piston area)
        "pistonMass": 5.0,  # kg piston mass
        "pistonLeverArm": 0.1,  # m effective piston lever arm
        "frictionCoefficient": 0.05,  # friction coefficient
        "feaYoungsModulus": 200e9,  # Pa (200 GPa steel)
        "feaPoissonsRatio": 0.3,  # Poisson's ratio
        "feaYieldStrength": 400e6,  # Pa (400 MPa steel)
        
        # Gear clearance parameters
        "strokeAchievableFactor": 0.8,  # Fraction of stroke that must be achievable
        "clearanceSafetyMargin": 0.1,  # mm safety margin for clearance adjustments
        "adjustmentSplitFactor": 0.5,  # How to split clearance adjustments between sun and ring
    }


def main():
    """Run the comprehensive unified optimization pipeline demo."""
    print("🚀 CAMPROV5 COMPREHENSIVE UNIFIED OPTIMIZATION PIPELINE DEMO")
    print("=" * 70)
    print("Using the complete test dataset from generate_gear_profiles.py")
    print("This demonstrates the full capabilities of the unified pipeline")
    print("=" * 70)
    
    # Create output directory
    output_dir = Path("comprehensive_demo_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get comprehensive test parameters
    params = get_comprehensive_test_parameters()
    
    print(f"\n📋 COMPREHENSIVE TEST PARAMETERS:")
    print(f"  • Stroke Length: {params['strokeLengthMm']} mm")
    print(f"  • Gear Ratio: {params['gearRatio']}:1 (Planet:Ring)")
    print(f"  • Ring Rotation: {params['ringRotationDeg']}°")
    print(f"  • Planet Rotation: {params['planetRotationDeg']}°")
    print(f"  • Planet Count: {params['planetCount']}")
    print(f"  • RPM: {params['rpm']}")
    print(f"  • Sampling Step: {params['samplingStepDeg']}°")
    print(f"  • Rod Length: {params['rodLength']} mm")
    print(f"  • Journal Radius: {params['journalRadius']} mm")
    print(f"  • Planet Radius: {params['planetRadius']} mm")
    print(f"  • Ring Inner Radius Base: {params['ringInnerRadiusBase']} mm")
    print(f"  • Ring Thickness: {params['ringThickness']} mm")
    print(f"  • Planet Teeth: {params['planetTeeth']}")
    print(f"  • Ring Teeth: {params['ringTeeth']}")
    print(f"  • Tooth Module: {params['toothModule']} mm")
    
    # Initialize the unified optimizer
    print(f"\n🔧 INITIALIZING UNIFIED OPTIMIZER...")
    optimizer = UnifiedOptimizer(output_dir=output_dir)
    
    # Run the complete pipeline
    print(f"\n⚡ RUNNING COMPREHENSIVE UNIFIED OPTIMIZATION PIPELINE...")
    print("   This will execute all phases with the full test dataset:")
    print("   1. Motion Law Generation (with piecewise motion law)")
    print("   2. Dual Solution Methods (Litvin + Collocation)")
    print("   3. Efficiency Optimization (comparing both methods)")
    print("   4. Tooth Profile Generation (detailed tooth geometry)")
    print("   5. FEA Analysis (stress, vibration, fatigue)")
    
    start_time = time.time()
    
    try:
        result = optimizer.run_pipeline(params)
        execution_time = time.time() - start_time
        
        print(f"\n📊 COMPREHENSIVE RESULTS:")
        print(f"  • Status: {result['status']}")
        print(f"  • Execution Time: {execution_time:.2f} seconds")
        
        if result['status'] == 'success':
            # Motion Law Results
            motion_law = result['motion_law']
            print(f"\n📈 MOTION LAW RESULTS:")
            print(f"  • Data Points: {len(motion_law['theta_deg'])}")
            print(f"  • Max Displacement: {max(motion_law['displacement']):.1f} mm")
            print(f"  • Max Velocity: {max(motion_law['velocity']):.1f} mm/deg")
            print(f"  • Max Acceleration: {max(motion_law['acceleration']):.1f} mm/deg²")
            
            # Optimal Profiles Results
            optimal_profiles = result['optimal_profiles']
            print(f"\n⚙️  OPTIMAL GEAR PROFILES:")
            print(f"  • Optimal Method: {optimal_profiles['optimal_solution'].upper()}")
            
            profiles = optimal_profiles['optimal_profiles']
            print(f"  • Sun Radius Range: {min(profiles['r_sun']):.1f} - {max(profiles['r_sun']):.1f} mm")
            print(f"  • Planet Radius Range: {min(profiles['r_planet']):.1f} - {max(profiles['r_planet']):.1f} mm")
            print(f"  • Ring Inner Radius Range: {min(profiles['r_ring_inner']):.1f} - {max(profiles['r_ring_inner']):.1f} mm")
            print(f"  • Gear Ratio: {profiles['gear_ratio']:.1f}:1")
            
            # Efficiency Analysis
            if 'efficiency_analysis' in optimal_profiles:
                eff_analysis = optimal_profiles['efficiency_analysis']
                print(f"\n⚡ EFFICIENCY ANALYSIS:")
                print(f"  • Litvin Method Efficiency: {eff_analysis.get('litvin_efficiency', 'N/A')}")
                print(f"  • Collocation Method Efficiency: {eff_analysis.get('collocation_efficiency', 'N/A')}")
                print(f"  • Optimal Method: {eff_analysis.get('optimal_method', 'N/A')}")
            
            # Tooth Profiles Results
            tooth_profiles = result['tooth_profiles']
            print(f"\n🦷 TOOTH PROFILE GENERATION:")
            for gear_type in ['sun_teeth', 'planet_teeth', 'ring_teeth']:
                if gear_type in tooth_profiles and tooth_profiles[gear_type] is not None:
                    print(f"  • {gear_type.replace('_', ' ').title()}: Generated")
                else:
                    print(f"  • {gear_type.replace('_', ' ').title()}: Not available")
            
            # FEA Analysis Results
            fea = result['fea']
            print(f"\n🔬 FEA ANALYSIS RESULTS:")
            print(f"  • Analysis Status: {fea.get('status', 'Unknown')}")
            
            if 'analysis_summary' in fea:
                summary = fea['analysis_summary']
                print(f"  • Max Stress: {summary.get('max_stress', 'N/A')} Pa")
                print(f"  • Natural Frequencies: {len(summary.get('natural_frequencies', []))} modes")
                print(f"  • Fatigue Life: {summary.get('fatigue_life', 'N/A')} cycles")
            
            print(f"\n🎉 COMPREHENSIVE DEMO COMPLETED SUCCESSFULLY!")
            print("   The unified optimization pipeline processed the full test dataset")
            print("   and produced comprehensive analysis results across all phases.")
            
        else:
            print(f"\n❌ OPTIMIZATION FAILED:")
            if 'error' in result:
                print(f"  • Error: {result['error']}")
            if 'stage' in result:
                print(f"  • Failed at stage: {result['stage']}")
        
        # Save comprehensive results
        results_file = output_dir / "comprehensive_results.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Comprehensive results saved to: {results_file}")
        
        # Save parameters for reference
        params_file = output_dir / "test_parameters.json"
        with open(params_file, 'w') as f:
            json.dump(params, f, indent=2, default=str)
        print(f"💾 Test parameters saved to: {params_file}")
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"\n❌ COMPREHENSIVE DEMO FAILED:")
        print(f"   Error: {str(e)}")
        print(f"   Execution time: {execution_time:.2f} seconds")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
