"""
Integration Test Suite for CamProV5

This script tests the complete workflow from Python design to Rust simulation.
It verifies result consistency across the entire pipeline and tests error
handling and recovery mechanisms.

This is a critical component of Phase 3 (Integration Testing) of the CamProV5
implementation strategy.
"""

import os
import sys
import json
import toml
import numpy as np
import subprocess
import tempfile
import logging
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Union, Any

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the Python implementation
from campro.models.movement_law import MotionParameters, MotionLaw, export_parameters_for_fea

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integration_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("integration_test")

# Constants for numerical precision
DISPLACEMENT_EPSILON = 1e-10  # mm
VELOCITY_EPSILON = 1e-8       # mm/s
ACCELERATION_EPSILON = 1e-6   # mm/s²
JERK_EPSILON = 1e-4           # mm/s³

# Path to the Rust FEA engine
RUST_FEA_DIR = Path(__file__).parent.parent / "camprofw" / "rust" / "fea-engine"
RUST_FEA_BINARY = RUST_FEA_DIR / "target" / "release" / "fea_engine"

# Path for test results
TEST_RESULTS_DIR = Path(__file__).parent.parent / "test_results"
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)


def compile_fea_engine() -> bool:
    """Compile the Rust FEA engine in release mode."""
    logger.info("Compiling Rust FEA engine...")
    
    # Compile the Rust FEA engine
    result = subprocess.run(
        ["cargo", "build", "--release"],
        cwd=RUST_FEA_DIR,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error("Failed to compile Rust FEA engine:")
        logger.error(result.stderr)
        return False
    
    logger.info("Rust FEA engine compiled successfully.")
    return True


def create_fea_simulation_binary() -> bool:
    """Create a Rust binary for FEA simulation."""
    logger.info("Creating FEA simulation binary...")
    
    # Create the Rust simulation file
    rust_sim_file = RUST_FEA_DIR / "src" / "bin" / "fea_simulation.rs"
    os.makedirs(rust_sim_file.parent, exist_ok=True)
    
    with open(rust_sim_file, "w") as f:
        f.write("""
//! FEA Simulation for CamProV5
//!
//! This binary reads motion parameters from a file, performs FEA simulation,
//! and writes the results to another file.

use fea_engine::motion_law::{MotionParameters, MotionLaw};
use serde::{Deserialize, Serialize};
use std::fs;
use std::env;
use std::path::Path;
use std::error::Error;
use std::time::Instant;

#[derive(Debug, Serialize, Deserialize)]
struct SimulationConfig {
    /// Path to the motion parameters file
    parameters_file: String,
    /// Output file path
    output_file: String,
    /// Number of time steps
    time_steps: usize,
    /// Total simulation time in seconds
    total_time: f64,
    /// Format of the parameters file (json or toml)
    format: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct SimulationResults {
    /// Time steps
    time: Vec<f64>,
    /// Displacement at each time step
    displacement: Vec<f64>,
    /// Velocity at each time step
    velocity: Vec<f64>,
    /// Acceleration at each time step
    acceleration: Vec<f64>,
    /// Execution time in milliseconds
    execution_time_ms: f64,
    /// Any errors that occurred during simulation
    errors: Vec<String>,
}

fn load_parameters(file_path: &str, format: &str) -> Result<MotionParameters, Box<dyn Error>> {
    let file_content = fs::read_to_string(file_path)?;
    
    match format {
        "json" => {
            let params: MotionParameters = serde_json::from_str(&file_content)?;
            Ok(params)
        },
        "toml" => {
            let params: MotionParameters = toml::from_str(&file_content)?;
            Ok(params)
        },
        _ => Err(format!("Unsupported format: {}", format).into())
    }
}

fn run_simulation(config: SimulationConfig) -> Result<SimulationResults, Box<dyn Error>> {
    // Load parameters
    let params = load_parameters(&config.parameters_file, &config.format)?;
    
    // Create motion law
    let motion = MotionLaw::new(params)?;
    
    // Generate time steps
    let time: Vec<f64> = (0..config.time_steps)
        .map(|i| i as f64 * config.total_time / (config.time_steps - 1) as f64)
        .collect();
    
    // Start timing
    let start = Instant::now();
    
    // Calculate boundary conditions
    let mut displacement = Vec::with_capacity(config.time_steps);
    let mut velocity = Vec::with_capacity(config.time_steps);
    let mut acceleration = Vec::with_capacity(config.time_steps);
    let mut errors = Vec::new();
    
    for &t in &time {
        match std::panic::catch_unwind(|| motion.boundary_condition_at_time(t)) {
            Ok((d, v, a)) => {
                displacement.push(d);
                velocity.push(v);
                acceleration.push(a);
            },
            Err(_) => {
                errors.push(format!("Calculation failed at time {}", t));
                displacement.push(0.0);
                velocity.push(0.0);
                acceleration.push(0.0);
            }
        }
    }
    
    // End timing
    let execution_time_ms = start.elapsed().as_secs_f64() * 1000.0;
    
    Ok(SimulationResults {
        time,
        displacement,
        velocity,
        acceleration,
        execution_time_ms,
        errors,
    })
}

fn main() -> Result<(), Box<dyn Error>> {
    // Get config file path from command line arguments
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <config_file>", args[0]);
        std::process::exit(1);
    }
    
    let config_path = &args[1];
    
    // Read config file
    let config_str = fs::read_to_string(config_path)?;
    let config: SimulationConfig = serde_json::from_str(&config_str)?;
    
    // Run simulation
    match run_simulation(config) {
        Ok(results) => {
            // Write results to output file
            fs::write(
                &config.output_file,
                serde_json::to_string_pretty(&results)?
            )?;
            
            println!("Simulation completed successfully.");
            println!("Execution time: {:.2} ms", results.execution_time_ms);
            
            if !results.errors.is_empty() {
                println!("Warnings:");
                for error in &results.errors {
                    println!("  - {}", error);
                }
            }
            
            Ok(())
        },
        Err(e) => {
            eprintln!("Simulation failed: {}", e);
            
            // Write error to output file
            let error_results = SimulationResults {
                time: vec![],
                displacement: vec![],
                velocity: vec![],
                acceleration: vec![],
                execution_time_ms: 0.0,
                errors: vec![format!("Fatal error: {}", e)],
            };
            
            fs::write(
                &config.output_file,
                serde_json::to_string_pretty(&error_results)?
            )?;
            
            Err(e)
        }
    }
}
""")
    
    # Update Cargo.toml to include the binary
    with open(RUST_FEA_DIR / "Cargo.toml", "r") as f:
        cargo_toml = toml.loads(f.read())
    
    # Add the binary target if it doesn't exist
    if "bin" not in cargo_toml:
        cargo_toml["bin"] = []
    
    # Check if the binary is already defined
    binary_exists = False
    for bin_entry in cargo_toml.get("bin", []):
        if bin_entry.get("name") == "fea_simulation":
            binary_exists = True
            break
    
    if not binary_exists:
        cargo_toml["bin"].append({
            "name": "fea_simulation",
            "path": "src/bin/fea_simulation.rs"
        })
    
    # Write the updated Cargo.toml
    with open(RUST_FEA_DIR / "Cargo.toml", "w") as f:
        f.write(toml.dumps(cargo_toml))
    
    # Compile the Rust FEA engine with the new binary
    return compile_fea_engine()


def run_fea_simulation(
    params: MotionParameters,
    time_steps: int = 1000,
    total_time: float = 1.0,
    format_type: str = "json"
) -> Dict:
    """Run the FEA simulation with the given parameters."""
    logger.info(f"Running FEA simulation with {time_steps} time steps...")
    
    # Create temporary files for parameters, config, and output
    with tempfile.NamedTemporaryFile(suffix=f".{format_type}", delete=False) as params_file, \
         tempfile.NamedTemporaryFile(suffix=".json", delete=False) as config_file, \
         tempfile.NamedTemporaryFile(suffix=".json", delete=False) as output_file:
        
        params_path = params_file.name
        config_path = config_file.name
        output_path = output_file.name
    
    try:
        # Export parameters to file
        if format_type == "json":
            with open(params_path, "w") as f:
                f.write(params.to_json())
        else:  # toml
            with open(params_path, "w") as f:
                f.write(params.to_toml())
        
        # Create simulation config
        config = {
            "parameters_file": params_path,
            "output_file": output_path,
            "time_steps": time_steps,
            "total_time": total_time,
            "format": format_type
        }
        
        # Write config to file
        with open(config_path, "w") as f:
            f.write(json.dumps(config, indent=2))
        
        # Run the FEA simulation
        result = subprocess.run(
            [str(RUST_FEA_BINARY), config_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error("Failed to run FEA simulation:")
            logger.error(result.stderr)
            return {"errors": [f"Simulation failed: {result.stderr}"]}
        
        # Read the output
        try:
            with open(output_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Failed to parse simulation results")
            return {"errors": ["Failed to parse simulation results"]}
    
    finally:
        # Clean up temporary files
        for path in [params_path, config_path, output_path]:
            try:
                os.unlink(path)
            except:
                pass


def run_python_simulation(
    params: MotionParameters,
    time_steps: int = 1000,
    total_time: float = 1.0
) -> Dict:
    """Run the Python simulation with the given parameters."""
    logger.info(f"Running Python simulation with {time_steps} time steps...")
    
    try:
        # Create motion law
        motion = MotionLaw(params)
        
        # Generate time steps
        time = np.linspace(0, total_time, time_steps)
        
        # Calculate kinematics
        displacement = []
        velocity = []
        acceleration = []
        errors = []
        
        for t in time:
            try:
                # Convert time to cam angle
                theta = (t * params.omega()) % 360.0
                
                # Calculate kinematics
                d = motion.displacement(theta)
                v = motion.velocity(theta)
                a = motion.acceleration(theta)
                
                displacement.append(float(d))
                velocity.append(float(v))
                acceleration.append(float(a))
            except Exception as e:
                logger.error(f"Error in Python simulation at time {t}: {e}")
                errors.append(f"Error at time {t}: {str(e)}")
                displacement.append(0.0)
                velocity.append(0.0)
                acceleration.append(0.0)
        
        return {
            "time": time.tolist(),
            "displacement": displacement,
            "velocity": velocity,
            "acceleration": acceleration,
            "errors": errors
        }
    
    except Exception as e:
        logger.error(f"Failed to run Python simulation: {e}")
        return {"errors": [f"Simulation failed: {str(e)}"]}


def compare_simulation_results(
    python_results: Dict,
    fea_results: Dict
) -> Tuple[bool, Dict]:
    """Compare the Python and FEA simulation results."""
    logger.info("Comparing simulation results...")
    
    # Check for errors
    python_errors = python_results.get("errors", [])
    fea_errors = fea_results.get("errors", [])
    
    if python_errors or fea_errors:
        logger.warning("Errors occurred during simulation:")
        for error in python_errors:
            logger.warning(f"Python: {error}")
        for error in fea_errors:
            logger.warning(f"FEA: {error}")
    
    # Check that the time values match
    python_time = np.array(python_results.get("time", []))
    fea_time = np.array(fea_results.get("time", []))
    
    if len(python_time) != len(fea_time) or not np.allclose(python_time, fea_time):
        logger.error("Time values do not match")
        return False, {}
    
    # Compare the results
    max_diff = {
        "displacement": 0.0,
        "velocity": 0.0,
        "acceleration": 0.0
    }
    
    for key in max_diff.keys():
        python_values = np.array(python_results.get(key, []))
        fea_values = np.array(fea_results.get(key, []))
        
        if len(python_values) != len(fea_values):
            logger.error(f"{key} arrays have different lengths")
            return False, {}
        
        diff = np.abs(python_values - fea_values)
        max_diff[key] = np.max(diff)
    
    # Check if the differences are within acceptable limits
    success = (
        max_diff["displacement"] <= DISPLACEMENT_EPSILON and
        max_diff["velocity"] <= VELOCITY_EPSILON and
        max_diff["acceleration"] <= ACCELERATION_EPSILON
    )
    
    if success:
        logger.info("Simulation results match within acceptable limits")
    else:
        logger.warning("Simulation results exceed acceptable limits:")
        for key, value in max_diff.items():
            logger.warning(f"  {key}: {value}")
    
    return success, max_diff


def plot_simulation_results(
    python_results: Dict,
    fea_results: Dict,
    max_diff: Dict,
    save_path: Optional[Path] = None
):
    """Plot the comparison between Python and FEA simulation results."""
    logger.info("Plotting simulation results...")
    
    time = python_results.get("time", [])
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 12))
    fig.suptitle("Python vs FEA Simulation Comparison", fontsize=16)
    
    for i, key in enumerate(["displacement", "velocity", "acceleration"]):
        ax = axes[i]
        
        # Plot Python results
        ax.plot(time, python_results.get(key, []), 'b-', label="Python", linewidth=2, alpha=0.7)
        
        # Plot FEA results
        ax.plot(time, fea_results.get(key, []), 'r--', label="FEA", linewidth=1)
        
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(key.capitalize())
        ax.set_title(f"{key.capitalize()} Comparison (Max Diff: {max_diff.get(key, 0):.2e})")
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Plot saved to {save_path}")
    
    plt.close()


def test_error_handling(error_type: str) -> Dict:
    """Test error handling with invalid inputs."""
    logger.info(f"Testing error handling: {error_type}")
    
    try:
        if error_type == "invalid_parameters":
            # Create invalid parameters
            params = MotionParameters(max_lift=-10.0)  # Negative lift is invalid
            
            # Run FEA simulation
            return run_fea_simulation(params)
        
        elif error_type == "missing_file":
            # Create a simulation config with a non-existent file
            config = {
                "parameters_file": "non_existent_file.json",
                "output_file": "output.json",
                "time_steps": 100,
                "total_time": 1.0,
                "format": "json"
            }
            
            # Write config to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as config_file:
                config_path = config_file.name
                json.dump(config, config_file)
            
            # Run the FEA simulation
            result = subprocess.run(
                [str(RUST_FEA_BINARY), config_path],
                capture_output=True,
                text=True
            )
            
            # Clean up
            os.unlink(config_path)
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        
        elif error_type == "invalid_format":
            # Create valid parameters
            params = MotionParameters()
            
            # Run FEA simulation with invalid format
            return run_fea_simulation(params, format_type="invalid")
        
        else:
            return {"errors": [f"Unknown error type: {error_type}"]}
    
    except Exception as e:
        logger.error(f"Error in test_error_handling: {e}")
        return {"errors": [f"Test failed: {str(e)}"]}


def run_integration_tests():
    """Run the integration tests."""
    logger.info("Starting integration tests...")
    
    # Create the FEA simulation binary if needed
    if not RUST_FEA_BINARY.exists() or not create_fea_simulation_binary():
        logger.error("Failed to create FEA simulation binary. Aborting tests.")
        return False
    
    # Create test results directory
    test_dir = TEST_RESULTS_DIR / f"integration_test_{Path(__file__).stem}"
    os.makedirs(test_dir, exist_ok=True)
    
    # Test cases
    test_cases = [
        # Default parameters
        ("default", MotionParameters()),
        
        # High RPM case
        ("high_rpm", MotionParameters(rpm=6000.0)),
        
        # Low lift case
        ("low_lift", MotionParameters(max_lift=5.0)),
        
        # High lift case
        ("high_lift", MotionParameters(max_lift=20.0)),
        
        # Asymmetric case
        ("asymmetric", MotionParameters(rise_duration=60.0, fall_duration=120.0)),
        
        # Short dwell case
        ("short_dwell", MotionParameters(dwell_duration=15.0)),
        
        # Edge case: minimum values
        ("min_values", MotionParameters(
            base_circle_radius=1.0,
            max_lift=1.0,
            cam_duration=90.0,
            rise_duration=30.0,
            dwell_duration=30.0,
            fall_duration=30.0,
            rpm=1000.0
        )),
    ]
    
    # Run tests for each case
    all_success = True
    
    for name, params in test_cases:
        logger.info(f"Testing case: {name}")
        
        # Run Python simulation
        python_results = run_python_simulation(params)
        
        # Run FEA simulation
        fea_results = run_fea_simulation(params)
        
        # Compare results
        success, max_diff = compare_simulation_results(python_results, fea_results)
        
        # Plot results
        plot_path = test_dir / f"{name}_comparison.png"
        plot_simulation_results(python_results, fea_results, max_diff, plot_path)
        
        # Save results
        with open(test_dir / f"{name}_python_results.json", "w") as f:
            json.dump(python_results, f, indent=2)
        
        with open(test_dir / f"{name}_fea_results.json", "w") as f:
            json.dump(fea_results, f, indent=2)
        
        # Update overall success
        all_success = all_success and success
        
        logger.info(f"Test case {name}: {'SUCCESS' if success else 'FAILURE'}")
    
    # Test error handling
    logger.info("Testing error handling...")
    
    error_types = ["invalid_parameters", "missing_file", "invalid_format"]
    
    for error_type in error_types:
        error_results = test_error_handling(error_type)
        
        with open(test_dir / f"error_{error_type}_results.json", "w") as f:
            json.dump(error_results, f, indent=2)
        
        logger.info(f"Error handling test {error_type}: COMPLETE")
    
    logger.info(f"Integration tests completed: {'SUCCESS' if all_success else 'FAILURE'}")
    return all_success


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)