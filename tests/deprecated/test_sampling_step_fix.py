#!/usr/bin/env python3
"""
Test script to verify that the sampling step fix works for small values.
"""

import json
import subprocess
import sys
import os

def test_sampling_step_fix():
    """Test that small sampling steps don't break the optimization."""
    print("🧪 Testing sampling step fix...")
    
    # Test with very small sampling step that would create too many points
    test_input = {
        "strokeLengthMm": 10.0,
        "ringRotationDeg": 180.0,
        "samplingStepDeg": 0.1,  # This would create 1800 points without the fix
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
        "rpm": 1000.0,
        "planetCount": 2,
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
        # "clearanceSafetyMargin": 0.2,  # Duplicate removed
        "adjustmentSplitFactor": 0.6
    }
    
    # Write input file
    with open("test_sampling_fix_input.json", "w") as f:
        json.dump(test_input, f, indent=2)
    
    print("📝 Created test input with sampling step 0.1° (would create 1800 points)")
    
    # Run optimization
    result = subprocess.run([
        "python", "scripts/kotlin_bridge_cli.py",
        "--input", "test_sampling_fix_input.json",
        "--output", "test_sampling_fix_output.json",
        "--output-dir", "test_sampling_fix_output"
    ], capture_output=True, text=True, timeout=60)
    
    print(f"🔧 Optimization exit code: {result.returncode}")
    
    if result.returncode != 0:
        print(f"❌ Optimization failed: {result.stderr}")
        return False
    
    # Check if output file was created
    if not os.path.exists("test_sampling_fix_output.json"):
        print("❌ Output file not created")
        return False
    
    # Read and check results
    with open("test_sampling_fix_output.json", "r") as f:
        output = json.load(f)
    
    if output.get("status") == "success":
        print("✅ Optimization succeeded with small sampling step!")
        print(f"📊 Execution time: {output.get('execution_time', 'unknown'):.3f}s")
        assert True, "Optimization succeeded with small sampling step"
    else:
        print(f"❌ Optimization failed: {output.get('error', 'unknown error')}")
        assert False, f"Optimization failed: {output.get('error', 'unknown error')}"

def cleanup():
    """Clean up test files."""
    test_files = [
        "test_sampling_fix_input.json",
        "test_sampling_fix_output.json"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
    
    # Remove output directory
    import shutil
    if os.path.exists("test_sampling_fix_output"):
        shutil.rmtree("test_sampling_fix_output")

if __name__ == "__main__":
    try:
        success = test_sampling_step_fix()
        sys.exit(0 if success else 1)
    finally:
        cleanup()
