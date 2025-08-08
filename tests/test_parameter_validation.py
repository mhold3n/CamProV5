"""
Parameter Validation Test Suite for CamProV5

This script tests the mathematical equivalence between the Python and Rust
implementations of the motion law. It exports parameters from Python, imports
them in Rust (via subprocess), performs calculations in both languages, and
compares the results to ensure they match within acceptable error margins.

This is a critical component of Phase 1 (Parameter Validation) of the CamProV5
implementation strategy.
"""

import os
import sys
import json
import toml
import numpy as np
import subprocess
import tempfile
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the Python implementation
from campro.models.movement_law import MotionParameters, MotionLaw

# Constants for numerical precision
DISPLACEMENT_EPSILON = 1e-10  # mm
VELOCITY_EPSILON = 1e-8       # mm/s
ACCELERATION_EPSILON = 1e-6   # mm/s²
JERK_EPSILON = 1e-4           # mm/s³

# Path to the Rust test binary (will be compiled as part of the test)
RUST_TEST_DIR = Path(__file__).parent.parent / "camprofw" / "rust" / "fea-engine"
RUST_TEST_BINARY = RUST_TEST_DIR / "target" / "debug" / "parameter_validation"


def compile_rust_test_binary() -> bool:
    """Compile the Rust test binary."""
    print("Compiling Rust test binary...")
    
    # Create the Rust test file
    rust_test_file = RUST_TEST_DIR / "tests" / "parameter_validation.rs"
    os.makedirs(rust_test_file.parent, exist_ok=True)
    
    with open(rust_test_file, "w") as f:
        f.write("""
//! Parameter validation test for CamProV5
//!
//! This binary reads motion parameters from a JSON file, performs calculations,
//! and writes the results to another JSON file for comparison with Python.

use fea_engine::{load_motion_parameters_from_json, create_motion_law};
use std::fs;
use std::env;
use std::path::Path;

fn main() {
    // Get input and output file paths from command line arguments
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <input_json_path> <output_json_path>", args[0]);
        std::process::exit(1);
    }
    
    let input_path = &args[1];
    let output_path = &args[2];
    
    // Read input JSON
    let json_str = fs::read_to_string(input_path)
        .expect("Failed to read input file");
    
    // Parse motion parameters
    let params = load_motion_parameters_from_json(&json_str)
        .expect("Failed to parse motion parameters");
    
    // Create motion law
    let motion = create_motion_law(params)
        .expect("Failed to create motion law");
    
    // Generate test points
    let theta_values: Vec<f64> = (0..360).map(|i| i as f64).collect();
    
    // Calculate kinematics
    let displacement: Vec<f64> = theta_values.iter()
        .map(|&theta| motion.displacement(theta))
        .collect();
    
    let velocity: Vec<f64> = theta_values.iter()
        .map(|&theta| motion.velocity(theta))
        .collect();
    
    let acceleration: Vec<f64> = theta_values.iter()
        .map(|&theta| motion.acceleration(theta))
        .collect();
    
    let jerk: Vec<f64> = theta_values.iter()
        .map(|&theta| motion.jerk(theta))
        .collect();
    
    // Create output JSON
    let output = serde_json::json!({
        "theta": theta_values,
        "displacement": displacement,
        "velocity": velocity,
        "acceleration": acceleration,
        "jerk": jerk
    });
    
    // Write output JSON
    fs::write(output_path, serde_json::to_string_pretty(&output).unwrap())
        .expect("Failed to write output file");
}
""")
    
    # Create a Cargo.toml for the test binary
    with open(RUST_TEST_DIR / "Cargo.toml", "r") as f:
        cargo_toml = toml.loads(f.read())
    
    # Add the binary target
    if "bin" not in cargo_toml:
        cargo_toml["bin"] = []
    
    cargo_toml["bin"].append({
        "name": "parameter_validation",
        "path": "tests/parameter_validation.rs"
    })
    
    # Write the updated Cargo.toml
    with open(RUST_TEST_DIR / "Cargo.toml", "w") as f:
        f.write(toml.dumps(cargo_toml))
    
    # Compile the Rust test binary
    result = subprocess.run(
        ["cargo", "build"],
        cwd=RUST_TEST_DIR,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Failed to compile Rust test binary:")
        print(result.stderr)
        return False
    
    print("Rust test binary compiled successfully.")
    return True


def run_rust_calculation(params: MotionParameters) -> Dict:
    """Run the Rust implementation with the given parameters."""
    # Create temporary files for input and output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as input_file, \
         tempfile.NamedTemporaryFile(suffix=".json", delete=False) as output_file:
        
        input_path = input_file.name
        output_path = output_file.name
    
    try:
        # Write parameters to input file
        with open(input_path, "w") as f:
            f.write(params.to_json())
        
        # Run the Rust binary
        result = subprocess.run(
            [str(RUST_TEST_BINARY), input_path, output_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Failed to run Rust calculation:")
            print(result.stderr)
            return {}
        
        # Read the output
        with open(output_path, "r") as f:
            return json.load(f)
    
    finally:
        # Clean up temporary files
        for path in [input_path, output_path]:
            try:
                os.unlink(path)
            except:
                pass


def run_python_calculation(params: MotionParameters) -> Dict:
    """Run the Python implementation with the given parameters."""
    motion = MotionLaw(params)
    
    # Generate test points
    theta_values = np.arange(0, 360)
    
    # Calculate kinematics
    displacement = motion.displacement(theta_values)
    velocity = motion.velocity(theta_values)
    acceleration = motion.acceleration(theta_values)
    jerk = motion.jerk(theta_values)
    
    return {
        "theta": theta_values.tolist(),
        "displacement": displacement.tolist(),
        "velocity": velocity.tolist(),
        "acceleration": acceleration.tolist(),
        "jerk": jerk.tolist()
    }


def compare_results(python_results: Dict, rust_results: Dict) -> Tuple[bool, Dict]:
    """Compare the Python and Rust results."""
    if not python_results or not rust_results:
        return False, {}
    
    # Check that the theta values match
    if python_results["theta"] != rust_results["theta"]:
        print("Theta values do not match")
        return False, {}
    
    # Compare the results
    max_diff = {
        "displacement": 0.0,
        "velocity": 0.0,
        "acceleration": 0.0,
        "jerk": 0.0
    }
    
    for key in max_diff.keys():
        python_values = np.array(python_results[key])
        rust_values = np.array(rust_results[key])
        
        diff = np.abs(python_values - rust_values)
        max_diff[key] = np.max(diff)
    
    # Check if the differences are within acceptable limits
    success = (
        max_diff["displacement"] <= DISPLACEMENT_EPSILON and
        max_diff["velocity"] <= VELOCITY_EPSILON and
        max_diff["acceleration"] <= ACCELERATION_EPSILON and
        max_diff["jerk"] <= JERK_EPSILON
    )
    
    return success, max_diff


def plot_comparison(python_results: Dict, rust_results: Dict, max_diff: Dict, save_path: Optional[Path] = None):
    """Plot the comparison between Python and Rust results."""
    theta = python_results["theta"]
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 16))
    fig.suptitle("Python vs Rust Implementation Comparison", fontsize=16)
    
    for i, key in enumerate(["displacement", "velocity", "acceleration", "jerk"]):
        ax = axes[i]
        
        # Plot Python results
        ax.plot(theta, python_results[key], 'b-', label="Python", linewidth=2, alpha=0.7)
        
        # Plot Rust results
        ax.plot(theta, rust_results[key], 'r--', label="Rust", linewidth=1)
        
        ax.set_xlabel("Cam Angle (degrees)")
        ax.set_ylabel(key.capitalize())
        ax.set_title(f"{key.capitalize()} Comparison (Max Diff: {max_diff[key]:.2e})")
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()


def test_parameter_validation():
    """Run the parameter validation test."""
    # Compile the Rust test binary if needed
    if not RUST_TEST_BINARY.exists():
        if not compile_rust_test_binary():
            print("Failed to compile Rust test binary. Aborting test.")
            return False
    
    # Create test parameters
    test_cases = [
        # Default parameters
        MotionParameters(),
        
        # High RPM case
        MotionParameters(rpm=6000.0),
        
        # Low lift case
        MotionParameters(max_lift=5.0),
        
        # High lift case
        MotionParameters(max_lift=20.0),
        
        # Asymmetric case
        MotionParameters(rise_duration=60.0, fall_duration=120.0),
        
        # Short dwell case
        MotionParameters(dwell_duration=15.0),
        
        # Edge case: minimum values
        MotionParameters(
            base_circle_radius=1.0,
            max_lift=1.0,
            rise_duration=1.0,
            dwell_duration=1.0,
            fall_duration=1.0,
            rpm=1.0
        )
    ]
    
    # Run tests for each case
    all_success = True
    
    for i, params in enumerate(test_cases):
        print(f"\nTesting case {i+1}/{len(test_cases)}:")
        print(f"  Parameters: {params.to_dict()}")
        
        # Run calculations
        python_results = run_python_calculation(params)
        rust_results = run_rust_calculation(params)
        
        # Compare results
        success, max_diff = compare_results(python_results, rust_results)
        
        if success:
            print("  ✓ Test passed!")
            print(f"  Max differences: {max_diff}")
        else:
            print("  ✗ Test failed!")
            print(f"  Max differences: {max_diff}")
            all_success = False
        
        # Plot comparison for the first case
        if i == 0:
            plot_comparison(
                python_results, 
                rust_results, 
                max_diff,
                save_path=Path(__file__).parent / "parameter_validation_comparison.png"
            )
    
    return all_success


if __name__ == "__main__":
    success = test_parameter_validation()
    
    if success:
        print("\nAll parameter validation tests passed!")
        print("The Python and Rust implementations are mathematically equivalent within acceptable error margins.")
        sys.exit(0)
    else:
        print("\nSome parameter validation tests failed!")
        print("The Python and Rust implementations are not mathematically equivalent.")
        sys.exit(1)