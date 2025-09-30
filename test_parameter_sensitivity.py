#!/usr/bin/env python3
"""
Test script to verify that different input parameters actually affect the optimization results.
"""

import json
import subprocess
import sys
import os
import numpy as np

def create_test_input(stroke_length, sampling_step, rpm, planet_count):
    """Create a test input with specific parameters."""
    return {
        "strokeLengthMm": stroke_length,
        "ringRotationDeg": 180.0,
        "samplingStepDeg": sampling_step,
        "maxAcceleration": 200.0,
        "maxVelocity": 100.0,
        "nodeCount": 16,
        "maxIterations": 100,
        "tolerance": 1e-4,
        "constraintTolerance": 1e-4,
        "tdcZeroAccelDurationDeg": 10.0,
        "bdcZeroAccelDurationDeg": 10.0,
        "travelZeroAccelDurationDeg": 20.0,
        "tdcPhaseStartDeg": 0.0,
        "bdcPhaseStartDeg": 90.0,
        "travelPhaseStartDeg": 45.0,
        "forceTransferWeight": 1.0,
        "efficiencyWeight": 1.0,
        "smoothnessWeight": 0.1,
        "clearanceSafetyMargin": 0.1,
        "minGearClearance": 0.05,
        "pistonAreaMm2": 100.0,
        "cylinderPressureBar": 10.0,
        "materialStrengthMpa": 500.0,
        "rpm": rpm,
        "planetCount": planet_count,
        "gearRatio": 2.0,
        "rodLength": 80.0,
        "journalRadius": 5.0,
        "interferenceBuffer": 0.5,
        "ringThickness": 5.0,
        "carrierOffsetDeg": 120.0,
        "rampBeforeTdcDeg": 20.0,
        "rampAfterTdcDeg": 20.0,
        "dwellTdcDeg": 10.0,
        "rampBeforeBdcDeg": 20.0,
        "rampAfterBdcDeg": 20.0,
        "dwellBdcDeg": 10.0,
        "constantVelocityTdcDeg": 30.0,
        "constantVelocityBdcDeg": 40.0,
        "planetRadiusBaseFactor": 0.2,
        "planetRadiusVariationFactor": 0.1,
        "sunRadiusBaseFactor": 0.15,
        "sunRadiusVariationFactor": 0.05,
        "strokeAchievableFactor": 0.9,
        "clearanceSafetyMargin": 0.2,
        "adjustmentSplitFactor": 0.6
    }

def run_optimization(input_data, test_name):
    """Run optimization with given input data."""
    input_file = f"test_{test_name}_input.json"
    output_file = f"test_{test_name}_output.json"
    
    # Write input file
    with open(input_file, "w") as f:
        json.dump(input_data, f, indent=2)
    
    # Run optimization
    result = subprocess.run([
        "python", "scripts/kotlin_bridge_cli.py",
        "--input", input_file,
        "--output", output_file,
        "--output-dir", f"test_{test_name}_output"
    ], capture_output=True, text=True, timeout=30)
    
    if result.returncode != 0:
        print(f"❌ {test_name} optimization failed: {result.stderr}")
        return None
    
    # Read results
    if not os.path.exists(output_file):
        print(f"❌ {test_name} output file not created")
        return None
    
    with open(output_file, "r") as f:
        return json.load(f)

def compare_results(result1, result2, name1, name2):
    """Compare two optimization results."""
    print(f"\n🔍 Comparing {name1} vs {name2}:")
    
    # Compare motion law
    motion1 = result1["motion_law"]
    motion2 = result2["motion_law"]
    
    disp1 = np.array(motion1["displacement"])
    disp2 = np.array(motion2["displacement"])
    vel1 = np.array(motion1["velocity"])
    vel2 = np.array(motion2["velocity"])
    acc1 = np.array(motion1["acceleration"])
    acc2 = np.array(motion2["acceleration"])
    
    disp_diff = np.max(np.abs(disp1 - disp2))
    vel_diff = np.max(np.abs(vel1 - vel2))
    acc_diff = np.max(np.abs(acc1 - acc2))
    
    print(f"  Displacement max difference: {disp_diff:.6f}")
    print(f"  Velocity max difference: {vel_diff:.6f}")
    print(f"  Acceleration max difference: {acc_diff:.6f}")
    
    # Compare gear profiles
    gear1 = result1["optimal_profiles"]
    gear2 = result2["optimal_profiles"]
    
    r_sun1 = np.array(gear1["r_sun"])
    r_sun2 = np.array(gear2["r_sun"])
    r_planet1 = np.array(gear1["r_planet"])
    r_planet2 = np.array(gear2["r_planet"])
    r_ring1 = np.array(gear1["r_ring_inner"])
    r_ring2 = np.array(gear2["r_ring_inner"])
    
    sun_diff = np.max(np.abs(r_sun1 - r_sun2))
    planet_diff = np.max(np.abs(r_planet1 - r_planet2))
    ring_diff = np.max(np.abs(r_ring1 - r_ring2))
    
    print(f"  Sun radius max difference: {sun_diff:.6f}")
    print(f"  Planet radius max difference: {planet_diff:.6f}")
    print(f"  Ring radius max difference: {ring_diff:.6f}")
    
    # Compare efficiency
    eff1 = gear1["force_transfer_efficiency"]
    eff2 = gear2["force_transfer_efficiency"]
    print(f"  Force transfer efficiency: {eff1:.6f} vs {eff2:.6f} (diff: {abs(eff1-eff2):.6f})")
    
    # Check if results are significantly different
    significant_diff = (disp_diff > 1e-3 or vel_diff > 1e-3 or acc_diff > 1e-3 or 
                       sun_diff > 1e-3 or planet_diff > 1e-3 or ring_diff > 1e-3 or 
                       abs(eff1 - eff2) > 1e-3)
    
    if significant_diff:
        print(f"  ✅ Results are significantly different - parameters are being used!")
    else:
        print(f"  ❌ Results are nearly identical - possible fallback or caching issue")
    
    return significant_diff

def test_parameter_sensitivity():
    """Test that different parameters produce different results."""
    print("🧪 Testing parameter sensitivity...")
    
    # Test 1: Different stroke lengths
    print("\n📏 Test 1: Different stroke lengths")
    input1 = create_test_input(stroke_length=10.0, sampling_step=1.0, rpm=1000.0, planet_count=2)
    input2 = create_test_input(stroke_length=20.0, sampling_step=1.0, rpm=1000.0, planet_count=2)
    
    result1 = run_optimization(input1, "stroke10")
    result2 = run_optimization(input2, "stroke20")
    
    if result1 and result2:
        diff1 = compare_results(result1, result2, "Stroke 10mm", "Stroke 20mm")
    else:
        diff1 = False
    
    # Test 2: Different sampling steps
    print("\n📐 Test 2: Different sampling steps")
    input3 = create_test_input(stroke_length=10.0, sampling_step=0.5, rpm=1000.0, planet_count=2)
    input4 = create_test_input(stroke_length=10.0, sampling_step=2.0, rpm=1000.0, planet_count=2)
    
    result3 = run_optimization(input3, "step05")
    result4 = run_optimization(input4, "step20")
    
    if result3 and result4:
        diff2 = compare_results(result3, result4, "Step 0.5°", "Step 2.0°")
    else:
        diff2 = False
    
    # Test 3: Different RPM
    print("\n⚡ Test 3: Different RPM")
    input5 = create_test_input(stroke_length=10.0, sampling_step=1.0, rpm=500.0, planet_count=2)
    input6 = create_test_input(stroke_length=10.0, sampling_step=1.0, rpm=2000.0, planet_count=2)
    
    result5 = run_optimization(input5, "rpm500")
    result6 = run_optimization(input6, "rpm2000")
    
    if result5 and result6:
        diff3 = compare_results(result5, result6, "RPM 500", "RPM 2000")
    else:
        diff3 = False
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  Stroke length sensitivity: {'✅ PASS' if diff1 else '❌ FAIL'}")
    print(f"  Sampling step sensitivity: {'✅ PASS' if diff2 else '❌ FAIL'}")
    print(f"  RPM sensitivity: {'✅ PASS' if diff3 else '❌ FAIL'}")
    
    if diff1 and diff2 and diff3:
        print(f"\n🎉 All tests passed! Parameters are being used correctly.")
        return True
    else:
        print(f"\n⚠️  Some tests failed. There may be fallback logic or caching issues.")
        return False

def cleanup():
    """Clean up test files."""
    test_files = [
        "test_stroke10_input.json", "test_stroke10_output.json",
        "test_stroke20_input.json", "test_stroke20_output.json",
        "test_step05_input.json", "test_step05_output.json",
        "test_step20_input.json", "test_step20_output.json",
        "test_rpm500_input.json", "test_rpm500_output.json",
        "test_rpm2000_input.json", "test_rpm2000_output.json"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
    
    # Remove output directories
    import shutil
    for dir_name in ["test_stroke10_output", "test_stroke20_output", "test_step05_output", 
                     "test_step20_output", "test_rpm500_output", "test_rpm2000_output"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

if __name__ == "__main__":
    try:
        success = test_parameter_sensitivity()
        sys.exit(0 if success else 1)
    finally:
        cleanup()
