# CamProV5 User Guide

This document provides a comprehensive guide to using CamProV5 for cam profile design and simulation.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Design Workflow](#design-workflow)
   - [Creating Motion Parameters](#creating-motion-parameters)
   - [Analyzing Kinematics](#analyzing-kinematics)
   - [Optimizing Parameters](#optimizing-parameters)
   - [Visualizing Results](#visualizing-results)
4. [Simulation Workflow](#simulation-workflow)
   - [Exporting Parameters](#exporting-parameters)
   - [Running FEA Simulation](#running-fea-simulation)
   - [Analyzing Results](#analyzing-results)
5. [Error Handling](#error-handling)
6. [Logging](#logging)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Introduction

CamProV5 is a multi-language cam profile design and simulation tool that combines the flexibility of Python for design with the performance of Rust for simulation. It provides a complete workflow from initial design to final simulation, with comprehensive error handling and logging.

### Architecture

CamProV5 consists of three main layers:

1. **Design & Analysis Layer (Python)**
   - Rapid iteration on motion parameters
   - Visualization of acceleration curves and kinematic behavior
   - Optimization studies with scipy/numpy
   - Generation of publication-quality plots with matplotlib
   - Validation of designs before committing to expensive FEA runs

2. **High-Performance Simulation Layer (Rust)**
   - Native motion law implementation for maximum performance
   - FEA solver core
   - Real-time boundary condition calculation
   - Memory-efficient data structures
   - Parallel computation capabilities

3. **Orchestration & Visualization Layer (Python + Kotlin/Scala)**
   - Simulation launcher and parameter passing
   - Results post-processing with Pandas
   - GUI for visualization and control
   - Animation rendering and export

## Installation

### Prerequisites

- Python 3.8 or later
- Rust 1.50 or later
- Cargo package manager

### Installing Python Dependencies

```bash
pip install numpy scipy matplotlib pandas toml
```

### Building the Rust FEA Engine

```bash
cd camprofw/rust/fea-engine
cargo build --release
```

## Design Workflow

The design workflow in CamProV5 involves creating motion parameters, analyzing kinematics, optimizing parameters, and visualizing results.

### Creating Motion Parameters

Motion parameters define the cam profile, including base circle radius, maximum lift, cam duration, rise/dwell/fall durations, and kinematic limits.

```python
from campro.models.movement_law import MotionParameters

# Create motion parameters with default values
params = MotionParameters()

# Create motion parameters with custom values
params = MotionParameters(
    base_circle_radius=25.0,
    max_lift=10.0,
    cam_duration=180.0,
    rise_duration=90.0,
    dwell_duration=45.0,
    fall_duration=90.0,
    jerk_limit=1000.0,
    acceleration_limit=500.0,
    velocity_limit=100.0,
    rpm=3000.0
)
```

### Analyzing Kinematics

Once you have created motion parameters, you can analyze the kinematics of the cam profile.

```python
from campro.models.movement_law import MotionLaw

# Create motion law
motion = MotionLaw(params)

# Calculate displacement, velocity, acceleration, and jerk at a specific angle
theta = 45.0  # degrees
displacement = motion.displacement(theta)
velocity = motion.velocity(theta)
acceleration = motion.acceleration(theta)
jerk = motion.jerk(theta)

print(f"Displacement: {displacement} mm")
print(f"Velocity: {velocity} mm/s")
print(f"Acceleration: {acceleration} mm/s²")
print(f"Jerk: {jerk} mm/s³")

# Perform comprehensive kinematic analysis
analysis = motion.analyze_kinematics(num_points=1000)

print(f"Maximum velocity: {analysis['max_velocity']} mm/s")
print(f"Maximum acceleration: {analysis['max_acceleration']} mm/s²")
print(f"Maximum jerk: {analysis['max_jerk']} mm/s³")
print(f"RMS acceleration: {analysis['rms_acceleration']} mm/s²")
print(f"RMS jerk: {analysis['rms_jerk']} mm/s³")

# Check for constraint violations
if analysis['velocity_violation']:
    print("Warning: Velocity limit exceeded")
if analysis['acceleration_violation']:
    print("Warning: Acceleration limit exceeded")
if analysis['jerk_violation']:
    print("Warning: Jerk limit exceeded")
```

### Optimizing Parameters

CamProV5 provides a `MotionOptimizer` class for optimizing motion parameters to minimize acceleration, jerk, or other objective functions.

```python
from campro.models.movement_law import MotionOptimizer

# Create motion optimizer
optimizer = MotionOptimizer(params)

# Define parameter bounds
bounds = [
    (20.0, 30.0),  # base_circle_radius
    (5.0, 15.0),   # max_lift
    (180.0, 180.0),  # cam_duration (fixed)
    (60.0, 120.0),  # rise_duration
    (30.0, 60.0),   # dwell_duration
    (60.0, 120.0),  # fall_duration
    (1000.0, 1000.0),  # jerk_limit (fixed)
    (500.0, 500.0),    # acceleration_limit (fixed)
    (100.0, 100.0),    # velocity_limit (fixed)
    (3000.0, 3000.0)   # rpm (fixed)
]

# Optimize parameters to minimize RMS acceleration
optimized_params = optimizer.optimize(
    bounds=bounds,
    objective_type='rms_acceleration',
    method='differential_evolution'
)

# Create motion law with optimized parameters
optimized_motion = MotionLaw(optimized_params)

# Analyze optimized kinematics
optimized_analysis = optimized_motion.analyze_kinematics()

print(f"Original RMS acceleration: {analysis['rms_acceleration']} mm/s²")
print(f"Optimized RMS acceleration: {optimized_analysis['rms_acceleration']} mm/s²")
print(f"Improvement: {(1 - optimized_analysis['rms_acceleration'] / analysis['rms_acceleration']) * 100:.2f}%")
```

### Visualizing Results

CamProV5 provides methods for visualizing kinematic analysis results.

```python
from pathlib import Path

# Plot kinematic analysis results
motion.plot_kinematics()

# Save plot to file
motion.plot_kinematics(save_path=Path("kinematic_analysis.png"))

# Compare original and optimized kinematics
import matplotlib.pyplot as plt
import numpy as np

# Generate angle array
theta = np.linspace(0, 360, 1000)

# Calculate kinematics
original_displacement = motion.displacement(theta)
original_acceleration = motion.acceleration(theta)
optimized_displacement = optimized_motion.displacement(theta)
optimized_acceleration = optimized_motion.acceleration(theta)

# Create plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# Plot displacement
ax1.plot(theta, original_displacement, 'b-', label="Original")
ax1.plot(theta, optimized_displacement, 'r--', label="Optimized")
ax1.set_xlabel("Cam Angle (degrees)")
ax1.set_ylabel("Displacement (mm)")
ax1.set_title("Displacement Comparison")
ax1.grid(True, alpha=0.3)
ax1.legend()

# Plot acceleration
ax2.plot(theta, original_acceleration, 'b-', label="Original")
ax2.plot(theta, optimized_acceleration, 'r--', label="Optimized")
ax2.set_xlabel("Cam Angle (degrees)")
ax2.set_ylabel("Acceleration (mm/s²)")
ax2.set_title("Acceleration Comparison")
ax2.grid(True, alpha=0.3)
ax2.legend()

plt.tight_layout()
plt.savefig("comparison.png", dpi=300, bbox_inches='tight')
plt.show()
```

## Simulation Workflow

The simulation workflow in CamProV5 involves exporting parameters from the Python design layer, running the FEA simulation in the Rust layer, and analyzing the results.

### Exporting Parameters

Parameters are exported from the Python design layer to the Rust simulation layer using JSON or TOML files.

```python
from campro.models.movement_law import export_parameters_for_fea
from pathlib import Path

# Export parameters for FEA engine
export_parameters_for_fea(params, Path("params.toml"), format_type="toml")
```

### Running FEA Simulation

The FEA simulation is run using the Rust FEA engine.

```bash
# Run FEA simulation
./camprofw/rust/fea-engine/target/release/fea_engine simulate params.toml results.json
```

Alternatively, you can run the simulation from Python:

```python
import subprocess
from pathlib import Path

# Run FEA simulation
result = subprocess.run(
    [
        str(Path("camprofw/rust/fea-engine/target/release/fea_engine")),
        "simulate",
        "params.toml",
        "results.json"
    ],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"Simulation failed: {result.stderr}")
else:
    print("Simulation completed successfully")
```

### Analyzing Results

The simulation results can be analyzed using Python.

```python
import json
import matplotlib.pyplot as plt
import numpy as np

# Load simulation results
with open("results.json", "r") as f:
    results = json.load(f)

# Extract data
time = np.array(results["time"])
displacement = np.array(results["displacement"])
velocity = np.array(results["velocity"])
acceleration = np.array(results["acceleration"])

# Create plot
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))

# Plot displacement
ax1.plot(time, displacement, 'b-')
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Displacement (mm)")
ax1.set_title("Displacement vs Time")
ax1.grid(True, alpha=0.3)

# Plot velocity
ax2.plot(time, velocity, 'g-')
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Velocity (mm/s)")
ax2.set_title("Velocity vs Time")
ax2.grid(True, alpha=0.3)

# Plot acceleration
ax3.plot(time, acceleration, 'r-')
ax3.set_xlabel("Time (s)")
ax3.set_ylabel("Acceleration (mm/s²)")
ax3.set_title("Acceleration vs Time")
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("simulation_results.png", dpi=300, bbox_inches='tight')
plt.show()

# Calculate statistics
max_displacement = np.max(displacement)
max_velocity = np.max(np.abs(velocity))
max_acceleration = np.max(np.abs(acceleration))
rms_acceleration = np.sqrt(np.mean(np.square(acceleration)))

print(f"Maximum displacement: {max_displacement} mm")
print(f"Maximum velocity: {max_velocity} mm/s")
print(f"Maximum acceleration: {max_acceleration} mm/s²")
print(f"RMS acceleration: {rms_acceleration} mm/s²")
```

## Error Handling

CamProV5 provides comprehensive error handling for both the Python and Rust implementations.

### Python Error Handling

```python
from campro.utils.logging import handle_fea_errors, ParameterValidationError

# Use the handle_fea_errors decorator to handle FEA engine errors
@handle_fea_errors
def run_simulation(params):
    # Run simulation code here
    pass

try:
    # Run simulation
    run_simulation(params)
except ParameterValidationError as e:
    print(f"Parameter validation error: {e}")
    # Handle parameter validation error
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

### Rust Error Handling

```rust
use fea_engine::{FEAError, FEAResult, MotionParameters};

fn run_simulation(params: &MotionParameters) -> FEAResult<()> {
    // Validate parameters
    params.validate()?;
    
    // Run simulation code here
    
    Ok(())
}

fn main() {
    let params = MotionParameters::default();
    
    match run_simulation(&params) {
        Ok(_) => println!("Simulation completed successfully"),
        Err(e) => match e {
            FEAError::ParameterValidation(msg) => {
                eprintln!("Parameter validation error: {}", msg);
                // Handle parameter validation error
            },
            _ => {
                eprintln!("Simulation error: {}", e);
                // Handle other errors
            }
        }
    }
}
```

## Logging

CamProV5 provides a unified logging experience across the Python and Rust components.

### Python Logging

```python
from campro.utils.logging import init_logging, info, error, get_logs

# Initialize logging
init_logging(
    level="INFO",
    console=True,
    file="camproV5.log",
    json_file="camproV5.json",
    memory=True,
    memory_size=1000
)

# Log messages
info("Starting simulation")
error("Simulation failed")

# Get logs
logs = get_logs()
for log in logs:
    print(log)
```

### Rust Logging

```rust
use fea_engine::logging::{init_default_logger, info, error};

// Initialize logging
init_default_logger();

// Log messages
info!("fea_engine", "Starting simulation");
error!("fea_engine", "Simulation failed");
```

## Best Practices

### Design Best Practices

1. **Start with reasonable defaults**: Begin with the default motion parameters and adjust them as needed.
2. **Validate designs before simulation**: Use the Python design layer to validate designs before running expensive FEA simulations.
3. **Optimize for specific objectives**: Use the `MotionOptimizer` class to optimize parameters for specific objectives, such as minimizing acceleration or jerk.
4. **Visualize results**: Always visualize the kinematic analysis results to ensure the design meets requirements.
5. **Check for constraint violations**: Always check for velocity, acceleration, and jerk limit violations.

### Simulation Best Practices

1. **Use appropriate time steps**: Use enough time steps to capture the motion accurately, but not so many that the simulation becomes unnecessarily slow.
2. **Validate parameters**: Always validate parameters before running the simulation to catch errors early.
3. **Use parallel computation**: For large simulations, use the parallel computation capabilities of the Rust implementation.
4. **Monitor memory usage**: For very large simulations, monitor memory usage to avoid running out of memory.
5. **Log important events**: Use the logging system to log important events during the simulation.

## Troubleshooting

### Common Issues

1. **Parameter validation errors**: Ensure all parameters are physically feasible (e.g., positive lift, positive base circle radius).
2. **Simulation crashes**: Check for memory issues or invalid parameters.
3. **Poor performance**: Use the performance tuning guidelines to optimize the simulation.
4. **Inconsistent results**: Ensure the Python and Rust implementations are using the same parameters.
5. **File not found errors**: Check file paths and ensure all required files exist.

### Getting Help

If you encounter issues not covered in this guide, please:

1. Check the API documentation for detailed information about the functions and classes.
2. Review the error messages and logs for clues about the issue.
3. Contact the CamProV5 team for assistance.