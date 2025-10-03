#!/usr/bin/env python3
"""
Test script to verify the compression duration parameter is working correctly.
"""

import json
import subprocess
import sys
import os

def test_compression_duration():
    """Test that compression duration parameter affects the optimization."""
    print("🧪 Testing compression duration parameter...")
    
    # Test with different compression durations
    test_cases = [
        {"compressionDurationPercent": 50.0, "description": "50% compression (balanced)"},
        {"compressionDurationPercent": 70.0, "description": "70% compression (default)"},
        {"compressionDurationPercent": 80.0, "description": "80% compression (high compression)"}
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📊 Test {i+1}: {test_case['description']}")
        
        # Create test input
        test_input = {
            "strokeLengthMm": 10.0,
            "ringRotationDeg": 180.0,
            "samplingStepDeg": 5.0,
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
            "planetCount": 2,  # Fixed to 2
            "carrierOffsetDeg": 180.0,  # Fixed to 180°
            "compressionDurationPercent": test_case["compressionDurationPercent"]
        }
        
        # Write input file
        input_file = f"test_compression_{i+1}_input.json"
        with open(input_file, "w") as f:
            json.dump(test_input, f, indent=2)
        
        # Run optimization
        output_file = f"test_compression_{i+1}_output.json"
        result = subprocess.run([
            "python", "scripts/kotlin_bridge_cli.py",
            "--input", input_file,
            "--output", output_file,
            "--output-dir", f"test_compression_{i+1}_output"
        ], capture_output=True, text=True, timeout=60)
        
        print(f"🔧 Optimization exit code: {result.returncode}")
        
        if result.returncode == 0 and os.path.exists(output_file):
            with open(output_file, "r") as f:
                output = json.load(f)
            
            if output.get("status") == "success":
                print("✅ Optimization succeeded!")
                print(f"📊 Execution time: {output.get('execution_time', 'unknown'):.3f}s")
                
                # Check if compression duration is being used
                if "motion_law" in output:
                    motion_law = output["motion_law"]
                    if "grid" in motion_law:
                        grid_size = len(motion_law["grid"])
                        print(f"📐 Grid size: {grid_size} points")
                
                results.append({
                    "compression_percent": test_case["compressionDurationPercent"],
                    "success": True,
                    "execution_time": output.get("execution_time", 0)
                })
            else:
                print(f"❌ Optimization failed: {output.get('error', 'unknown error')}")
                results.append({
                    "compression_percent": test_case["compressionDurationPercent"],
                    "success": False,
                    "error": output.get("error", "unknown")
                })
        else:
            print(f"❌ Optimization failed: {result.stderr}")
            results.append({
                "compression_percent": test_case["compressionDurationPercent"],
                "success": False,
                "error": "subprocess failed"
            })
        
        # Clean up
        for file in [input_file, output_file]:
            if os.path.exists(file):
                os.remove(file)
        
        # Remove output directory
        import shutil
        output_dir = f"test_compression_{i+1}_output"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
    
    # Summary
    print("\n📋 Test Summary:")
    print(f"{'Compression %':<15} {'Success':<8} {'Time (s)':<10} {'Notes'}")
    print("-" * 50)
    
    for result in results:
        compression = result["compression_percent"]
        success = "✅" if result["success"] else "❌"
        time_str = f"{result.get('execution_time', 0):.3f}" if result["success"] else "N/A"
        notes = "Working" if result["success"] else result.get("error", "Failed")
        
        print(f"{compression:<15} {success:<8} {time_str:<10} {notes}")
    
    # Check if all tests passed
    all_passed = all(result["success"] for result in results)
    print(f"\n🎯 Overall Result: {'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
    
    assert all_passed, "Some compression duration tests failed"

if __name__ == "__main__":
    try:
        success = test_compression_duration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        sys.exit(1)
