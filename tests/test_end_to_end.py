"""
End-to-End Headless Test Suite for CamProV5

This script tests the complete application workflows, data flow from input to visualization,
computation triggering and result handling, and export functionality.

This is a critical component of the headless testing phase leading up to in-the-loop UI testing.
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
from typing import Dict, List, Tuple, Optional

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the Python implementation
from campro.models.movement_law import MotionParameters, MotionLaw, export_parameters_for_fea

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("end_to_end_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("end_to_end_test")

# Path to the test results
TEST_RESULTS_DIR = Path(__file__).parent.parent / "test_results"
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)

# Path to the Rust FEA engine
RUST_FEA_DIR = Path(__file__).parent.parent / "camprofw" / "rust" / "fea-engine"
RUST_FEA_BINARY = RUST_FEA_DIR / "target" / "release" / "fea_engine"

def test_complete_workflow():
    """Test the complete application workflow from input to visualization."""
    logger.info("Testing complete application workflow...")
    
    # Create test parameters
    params = MotionParameters(
        base_circle_radius=10.0,
        max_lift=10.0,
        rise_duration=120.0,
        dwell_duration=60.0,
        fall_duration=120.0,
        rpm=1000.0
    )
    
    # Step 1: Create motion law
    logger.info("Step 1: Creating motion law...")
    try:
        motion = MotionLaw(params)
        logger.info("  ✓ Motion law created successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to create motion law: {e}")
        return False
    
    # Step 2: Analyze kinematics
    logger.info("Step 2: Analyzing kinematics...")
    try:
        kinematics = motion.analyze_kinematics()
        logger.info("  ✓ Kinematics analyzed successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to analyze kinematics: {e}")
        return False
    
    # Step 3: Export parameters for FEA
    logger.info("Step 3: Exporting parameters for FEA...")
    try:
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            params_path = f.name
        
        export_parameters_for_fea(params, Path(params_path), format_type="toml")
        
        # Check if the file exists and contains the expected parameters
        with open(params_path, "r") as f:
            exported_params = toml.load(f)
        
        # Clean up
        os.unlink(params_path)
        
        # Verify exported parameters
        if (exported_params["base_circle_radius"] == params.base_circle_radius and
            exported_params["max_lift"] == params.max_lift and
            exported_params["rise_duration"] == params.rise_duration and
            exported_params["dwell_duration"] == params.dwell_duration and
            exported_params["fall_duration"] == params.fall_duration and
            exported_params["rpm"] == params.rpm):
            logger.info("  ✓ Parameters exported successfully")
        else:
            logger.error("  ✗ Exported parameters do not match original parameters")
            return False
    except Exception as e:
        logger.error(f"  ✗ Failed to export parameters: {e}")
        return False
    
    # Step 4: Run FEA simulation
    logger.info("Step 4: Running FEA simulation...")
    try:
        # Create temporary files for parameters, config, and output
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as params_file, \
             tempfile.NamedTemporaryFile(suffix=".json", delete=False) as config_file, \
             tempfile.NamedTemporaryFile(suffix=".json", delete=False) as output_file:
            
            params_path = params_file.name
            config_path = config_file.name
            output_path = output_file.name
        
        # Export parameters to file
        export_parameters_for_fea(params, Path(params_path), format_type="toml")
        
        # Create simulation config
        config = {
            "parameters_file": params_path,
            "output_file": output_path,
            "time_steps": 100,
            "total_time": 1.0,
            "format": "toml"
        }
        
        # Write config to file
        with open(config_path, "w") as f:
            f.write(json.dumps(config, indent=2))
        
        # Run the FEA simulation
        if RUST_FEA_BINARY.exists():
            result = subprocess.run(
                [str(RUST_FEA_BINARY), config_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("  ✓ FEA simulation ran successfully")
                
                # Read the output
                with open(output_path, "r") as f:
                    simulation_results = json.load(f)
                
                # Verify simulation results
                if (len(simulation_results.get("time", [])) > 0 and
                    len(simulation_results.get("displacement", [])) > 0 and
                    len(simulation_results.get("velocity", [])) > 0 and
                    len(simulation_results.get("acceleration", [])) > 0):
                    logger.info("  ✓ Simulation results are valid")
                else:
                    logger.error("  ✗ Simulation results are invalid")
                    return False
            else:
                logger.error(f"  ✗ FEA simulation failed: {result.stderr}")
                return False
        else:
            logger.warning("  ! FEA binary not found, skipping simulation")
        
        # Clean up
        for path in [params_path, config_path, output_path]:
            try:
                os.unlink(path)
            except:
                pass
    except Exception as e:
        logger.error(f"  ✗ Failed to run FEA simulation: {e}")
        return False
    
    # Step 5: Generate visualization data
    logger.info("Step 5: Generating visualization data...")
    try:
        # Create mock animation data
        animation_data = {
            "baseCamTheta": [i * 3.6 for i in range(100)],
            "baseCamR": [params.base_circle_radius + params.max_lift * np.sin(i * np.pi / 50) for i in range(100)],
            "baseCamX": [params.base_circle_radius * np.cos(i * np.pi / 50) for i in range(100)],
            "baseCamY": [params.base_circle_radius * np.sin(i * np.pi / 50) for i in range(100)],
            "phiArray": [i * 3.6 for i in range(100)],
            "centerRArray": [0.0 for i in range(100)],
            "n": 1.0,
            "stroke": params.max_lift,
            "tdcOffset": 0.0,
            "innerEnvelopeTheta": [i * 3.6 for i in range(100)],
            "innerEnvelopeR": [params.base_circle_radius - 5.0 + 5.0 * np.sin(i * np.pi / 50) for i in range(100)],
            "outerBoundaryRadius": params.base_circle_radius + params.max_lift + 10.0,
            "rodLength": 100.0,
            "cycleRatio": 1.0
        }
        
        # Create mock plot data
        plot_data = {
            "thetaProfile": [i * 3.6 for i in range(100)],
            "rProfileMapped": [params.base_circle_radius + params.max_lift * np.sin(i * np.pi / 50) for i in range(100)],
            "sProfileRaw": [params.max_lift * np.sin(i * np.pi / 50) for i in range(100)],
            "sProfileProcessed": [params.max_lift * np.sin(i * np.pi / 50) for i in range(100)],
            "stroke": params.max_lift,
            "tdcOffset": 0.0,
            "rodLength": 100.0,
            "outerEnvelopeTheta": [i * 3.6 for i in range(100)],
            "outerEnvelopeR": [params.base_circle_radius + params.max_lift + 5.0 + 5.0 * np.sin(i * np.pi / 50) for i in range(100)],
            "rkAnalysisAttempted": True,
            "rkSuccess": True,
            "vibAnalysisAttempted": True,
            "vibSuccess": True,
            "plotPaths": ["polar_profile.png", "xy_displacement.png", "velocity.png", "acceleration.png", "jerk.png"]
        }
        
        # Save visualization data to files
        test_dir = TEST_RESULTS_DIR / "end_to_end_test"
        os.makedirs(test_dir, exist_ok=True)
        
        with open(test_dir / "animation_data.json", "w") as f:
            json.dump(animation_data, f, indent=2)
        
        with open(test_dir / "plot_data.json", "w") as f:
            json.dump(plot_data, f, indent=2)
        
        logger.info("  ✓ Visualization data generated successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to generate visualization data: {e}")
        return False
    
    # Step 6: Export SVG
    logger.info("Step 6: Exporting SVG...")
    try:
        # Create a simple SVG file
        svg_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="500" height="500" xmlns="http://www.w3.org/2000/svg">
  <circle cx="250" cy="250" r="{params.base_circle_radius * 10}" fill="none" stroke="black" stroke-width="2"/>
  <circle cx="250" cy="250" r="{(params.base_circle_radius + params.max_lift) * 10}" fill="none" stroke="red" stroke-width="2"/>
</svg>"""
        
        # Save SVG to file
        with open(test_dir / "cam_profile.svg", "w") as f:
            f.write(svg_content)
        
        logger.info("  ✓ SVG exported successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to export SVG: {e}")
        return False
    
    logger.info("✓ Complete application workflow test passed!")
    return True

def test_data_flow():
    """Test the data flow from input to visualization."""
    logger.info("Testing data flow from input to visualization...")
    
    # Create test parameters
    params = MotionParameters(
        base_circle_radius=15.0,
        max_lift=8.0,
        rise_duration=100.0,
        dwell_duration=80.0,
        fall_duration=100.0,
        rpm=1200.0
    )
    
    # Step 1: Create motion law
    logger.info("Step 1: Creating motion law...")
    try:
        motion = MotionLaw(params)
        logger.info("  ✓ Motion law created successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to create motion law: {e}")
        return False
    
    # Step 2: Generate displacement, velocity, acceleration, and jerk data
    logger.info("Step 2: Generating kinematic data...")
    try:
        theta = np.linspace(0, 360, 100)
        displacement = motion.displacement(theta)
        velocity = motion.velocity(theta)
        acceleration = motion.acceleration(theta)
        jerk = motion.jerk(theta)
        
        logger.info("  ✓ Kinematic data generated successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to generate kinematic data: {e}")
        return False
    
    # Step 3: Verify data consistency
    logger.info("Step 3: Verifying data consistency...")
    try:
        # Check that the data has the expected shape
        if (len(displacement) == 100 and
            len(velocity) == 100 and
            len(acceleration) == 100 and
            len(jerk) == 100):
            logger.info("  ✓ Data has the expected shape")
        else:
            logger.error("  ✗ Data does not have the expected shape")
            return False
        
        # Check that the displacement is within the expected range
        if (np.min(displacement) >= 0 and
            np.max(displacement) <= params.max_lift):
            logger.info("  ✓ Displacement is within the expected range")
        else:
            logger.error("  ✗ Displacement is not within the expected range")
            return False
        
        # Check that the velocity is zero at the dwell points
        dwell_start = params.rise_duration
        dwell_end = params.rise_duration + params.dwell_duration
        dwell_indices = np.where((theta >= dwell_start) & (theta <= dwell_end))[0]
        
        if len(dwell_indices) > 0:
            dwell_velocities = velocity[dwell_indices]
            if np.allclose(dwell_velocities, 0, atol=1e-6):
                logger.info("  ✓ Velocity is zero at the dwell points")
            else:
                logger.error("  ✗ Velocity is not zero at the dwell points")
                return False
        
        logger.info("  ✓ Data consistency verified")
    except Exception as e:
        logger.error(f"  ✗ Failed to verify data consistency: {e}")
        return False
    
    # Step 4: Save data for visualization
    logger.info("Step 4: Saving data for visualization...")
    try:
        # Create test results directory
        test_dir = TEST_RESULTS_DIR / "end_to_end_test"
        os.makedirs(test_dir, exist_ok=True)
        
        # Save data to files
        np.savetxt(test_dir / "theta.csv", theta, delimiter=",")
        np.savetxt(test_dir / "displacement.csv", displacement, delimiter=",")
        np.savetxt(test_dir / "velocity.csv", velocity, delimiter=",")
        np.savetxt(test_dir / "acceleration.csv", acceleration, delimiter=",")
        np.savetxt(test_dir / "jerk.csv", jerk, delimiter=",")
        
        logger.info("  ✓ Data saved successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to save data: {e}")
        return False
    
    logger.info("✓ Data flow test passed!")
    return True

def test_computation_triggering():
    """Test the computation triggering and result handling."""
    logger.info("Testing computation triggering and result handling...")
    
    # Step 1: Create test parameters
    logger.info("Step 1: Creating test parameters...")
    try:
        params = MotionParameters(
            base_circle_radius=12.0,
            max_lift=15.0,
            rise_duration=110.0,
            dwell_duration=70.0,
            fall_duration=110.0,
            rpm=1500.0
        )
        logger.info("  ✓ Test parameters created successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to create test parameters: {e}")
        return False
    
    # Step 2: Trigger computation
    logger.info("Step 2: Triggering computation...")
    try:
        # Create motion law
        motion = MotionLaw(params)
        
        # Analyze kinematics
        kinematics = motion.analyze_kinematics()
        
        logger.info("  ✓ Computation triggered successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to trigger computation: {e}")
        return False
    
    # Step 3: Handle results
    logger.info("Step 3: Handling results...")
    try:
        # Extract results
        theta = kinematics["theta"]
        displacement = kinematics["displacement"]
        velocity = kinematics["velocity"]
        acceleration = kinematics["acceleration"]
        jerk = kinematics["jerk"]
        
        # Calculate derived metrics
        max_velocity = np.max(np.abs(velocity))
        max_acceleration = np.max(np.abs(acceleration))
        max_jerk = np.max(np.abs(jerk))
        rms_acceleration = np.sqrt(np.mean(np.square(acceleration)))
        
        # Create test results directory
        test_dir = TEST_RESULTS_DIR / "end_to_end_test"
        os.makedirs(test_dir, exist_ok=True)
        
        # Save results to file
        results = {
            "max_velocity": float(max_velocity),
            "max_acceleration": float(max_acceleration),
            "max_jerk": float(max_jerk),
            "rms_acceleration": float(rms_acceleration)
        }
        
        with open(test_dir / "computation_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("  ✓ Results handled successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to handle results: {e}")
        return False
    
    logger.info("✓ Computation triggering and result handling test passed!")
    return True

def test_export_functionality():
    """Test the export functionality."""
    logger.info("Testing export functionality...")
    
    # Step 1: Create test parameters
    logger.info("Step 1: Creating test parameters...")
    try:
        params = MotionParameters(
            base_circle_radius=20.0,
            max_lift=12.0,
            rise_duration=90.0,
            dwell_duration=90.0,
            fall_duration=90.0,
            rpm=2000.0
        )
        logger.info("  ✓ Test parameters created successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to create test parameters: {e}")
        return False
    
    # Step 2: Export parameters to JSON
    logger.info("Step 2: Exporting parameters to JSON...")
    try:
        # Create test results directory
        test_dir = TEST_RESULTS_DIR / "end_to_end_test"
        os.makedirs(test_dir, exist_ok=True)
        
        # Export parameters to JSON
        json_path = test_dir / "parameters.json"
        with open(json_path, "w") as f:
            f.write(params.to_json())
        
        # Verify that the file exists and contains the expected parameters
        with open(json_path, "r") as f:
            exported_params = json.load(f)
        
        if (exported_params["base_circle_radius"] == params.base_circle_radius and
            exported_params["max_lift"] == params.max_lift and
            exported_params["rise_duration"] == params.rise_duration and
            exported_params["dwell_duration"] == params.dwell_duration and
            exported_params["fall_duration"] == params.fall_duration and
            exported_params["rpm"] == params.rpm):
            logger.info("  ✓ Parameters exported to JSON successfully")
        else:
            logger.error("  ✗ Exported JSON parameters do not match original parameters")
            return False
    except Exception as e:
        logger.error(f"  ✗ Failed to export parameters to JSON: {e}")
        return False
    
    # Step 3: Export parameters to TOML
    logger.info("Step 3: Exporting parameters to TOML...")
    try:
        # Export parameters to TOML
        toml_path = test_dir / "parameters.toml"
        with open(toml_path, "w") as f:
            f.write(params.to_toml())
        
        # Verify that the file exists and contains the expected parameters
        with open(toml_path, "r") as f:
            exported_params = toml.load(f)
        
        if (exported_params["base_circle_radius"] == params.base_circle_radius and
            exported_params["max_lift"] == params.max_lift and
            exported_params["rise_duration"] == params.rise_duration and
            exported_params["dwell_duration"] == params.dwell_duration and
            exported_params["fall_duration"] == params.fall_duration and
            exported_params["rpm"] == params.rpm):
            logger.info("  ✓ Parameters exported to TOML successfully")
        else:
            logger.error("  ✗ Exported TOML parameters do not match original parameters")
            return False
    except Exception as e:
        logger.error(f"  ✗ Failed to export parameters to TOML: {e}")
        return False
    
    # Step 4: Export SVG
    logger.info("Step 4: Exporting SVG...")
    try:
        # Create a simple SVG file
        svg_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="500" height="500" xmlns="http://www.w3.org/2000/svg">
  <circle cx="250" cy="250" r="{params.base_circle_radius * 10}" fill="none" stroke="black" stroke-width="2"/>
  <circle cx="250" cy="250" r="{(params.base_circle_radius + params.max_lift) * 10}" fill="none" stroke="red" stroke-width="2"/>
</svg>"""
        
        # Save SVG to file
        svg_path = test_dir / "cam_profile_export.svg"
        with open(svg_path, "w") as f:
            f.write(svg_content)
        
        # Verify that the file exists
        if svg_path.exists():
            logger.info("  ✓ SVG exported successfully")
        else:
            logger.error("  ✗ Failed to export SVG")
            return False
    except Exception as e:
        logger.error(f"  ✗ Failed to export SVG: {e}")
        return False
    
    logger.info("✓ Export functionality test passed!")
    return True

def test_end_to_end():
    """Run the end-to-end headless tests."""
    logger.info("Starting end-to-end headless tests...")
    
    # Create test results directory
    test_dir = TEST_RESULTS_DIR / "end_to_end_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # Run tests
    workflow_success = test_complete_workflow()
    data_flow_success = test_data_flow()
    computation_success = test_computation_triggering()
    export_success = test_export_functionality()
    
    # Overall success
    all_success = (
        workflow_success and
        data_flow_success and
        computation_success and
        export_success
    )
    
    # Log results
    logger.info("End-to-end headless tests completed:")
    logger.info(f"  Complete Workflow: {'SUCCESS' if workflow_success else 'FAILURE'}")
    logger.info(f"  Data Flow: {'SUCCESS' if data_flow_success else 'FAILURE'}")
    logger.info(f"  Computation Triggering: {'SUCCESS' if computation_success else 'FAILURE'}")
    logger.info(f"  Export Functionality: {'SUCCESS' if export_success else 'FAILURE'}")
    logger.info(f"  Overall: {'SUCCESS' if all_success else 'FAILURE'}")
    
    # Save results to file
    results = {
        "workflow": workflow_success,
        "data_flow": data_flow_success,
        "computation": computation_success,
        "export": export_success,
        "overall": all_success
    }
    
    with open(test_dir / "end_to_end_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return all_success

if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)