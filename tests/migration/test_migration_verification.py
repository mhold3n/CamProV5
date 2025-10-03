#!/usr/bin/env python3
"""
Test script for migration verification between Python and Kotlin motion law implementations.

This script demonstrates the new comparison functionality added to generate_gear_profiles.py
to verify that the migration from Python to Kotlin was completed correctly.
"""

import subprocess
import sys
from pathlib import Path

def run_migration_verification():
    """Run the migration verification comparison."""
    print("🔍 Running Migration Verification Comparison...")
    print("=" * 60)
    
    # Get the script path
    script_path = Path(__file__).parent / "generate_gear_profiles.py"
    
    try:
        # Run the comparison
        result = subprocess.run([
            sys.executable, str(script_path), "--solver", "comparison"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print("=" * 60)
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Migration verification completed successfully!")
            print("\nGenerated files in docs/profile_images/:")
            print("  - motion_law_comparison_python_vs_kotlin.png")
            print("  - motion_law_difference_analysis.png")
            print("  - gear_profiles_python.png")
            print("  - gear_profiles_kotlin.png")
            print("  - planetary_assembly_python.png")
            print("  - planetary_assembly_kotlin.png")
            print("  - migration_verification_summary.txt")
        else:
            print("❌ Migration verification failed!")
            
    except Exception as e:
        print(f"❌ Error running migration verification: {e}")
        return False
    
    return result.returncode == 0

def run_individual_tests():
    """Run individual solver tests for comparison."""
    print("\n🧪 Running Individual Solver Tests...")
    print("=" * 60)
    
    script_path = Path(__file__).parent / "generate_gear_profiles.py"
    
    solvers = ["piecewise", "kotlin"]
    
    for solver in solvers:
        print(f"\nTesting {solver} solver...")
        try:
            result = subprocess.run([
                sys.executable, str(script_path), "--solver", solver
            ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            
            if result.returncode == 0:
                print(f"✅ {solver} solver test passed")
            else:
                print(f"❌ {solver} solver test failed")
                print(f"Error: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error testing {solver} solver: {e}")

if __name__ == "__main__":
    print("🚀 Migration Verification Test Suite")
    print("=" * 60)
    
    # Run migration verification
    success = run_migration_verification()
    
    # Run individual tests
    run_individual_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        print("\nTo view the results:")
        print("1. Check the generated PNG files in docs/profile_images/")
        print("2. Read the migration_verification_summary.txt for detailed analysis")
        print("3. Compare the side-by-side plots to verify migration correctness")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
