"""
Backend Integration Test Suite for CamProV5

This script tests the backend integration components, including serialization/deserialization
functions, parameter handling and validation, and error handling and recovery mechanisms.

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
        logging.FileHandler("backend_integration_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backend_integration_test")

# Path to the test results
TEST_RESULTS_DIR = Path(__file__).parent.parent / "test_results"
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)

def test_serialization_deserialization():
    """Test serialization and deserialization of parameters."""
    logger.info("Testing serialization and deserialization...")
    
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
    
    # Test serialization and deserialization for each case
    all_success = True
    
    for i, params in enumerate(test_cases):
        logger.info(f"Testing case {i+1}/{len(test_cases)}:")
        logger.info(f"  Parameters: {params.to_dict()}")
        
        # Test JSON serialization/deserialization
        json_str = params.to_json()
        deserialized_params_json = MotionParameters.from_json(json_str)
        
        # Test TOML serialization/deserialization
        toml_str = params.to_toml()
        deserialized_params_toml = MotionParameters.from_toml(toml_str)
        
        # Compare original and deserialized parameters
        json_match = params.to_dict() == deserialized_params_json.to_dict()
        toml_match = params.to_dict() == deserialized_params_toml.to_dict()
        
        if json_match and toml_match:
            logger.info("  ✓ Serialization/deserialization test passed!")
        else:
            logger.error("  ✗ Serialization/deserialization test failed!")
            if not json_match:
                logger.error("    JSON serialization/deserialization failed")
            if not toml_match:
                logger.error("    TOML serialization/deserialization failed")
            all_success = False
    
    return all_success

def test_parameter_validation():
    """Test parameter validation."""
    logger.info("Testing parameter validation...")
    
    # Test cases with valid parameters
    valid_cases = [
        # Default parameters
        MotionParameters(),
        
        # Edge case: minimum values
        MotionParameters(
            base_circle_radius=1.0,
            max_lift=1.0,
            rise_duration=1.0,
            dwell_duration=1.0,
            fall_duration=1.0,
            rpm=1.0
        ),
        
        # Edge case: maximum values within limits
        MotionParameters(
            base_circle_radius=1000.0,
            max_lift=1000.0,
            rise_duration=120.0,
            dwell_duration=120.0,
            fall_duration=120.0,
            rpm=10000.0
        )
    ]
    
    # Test cases with invalid parameters
    invalid_cases = [
        # Negative base circle radius
        {"base_circle_radius": -1.0},
        
        # Negative max lift
        {"max_lift": -1.0},
        
        # Negative rise duration
        {"rise_duration": -1.0},
        
        # Negative dwell duration
        {"dwell_duration": -1.0},
        
        # Negative fall duration
        {"fall_duration": -1.0},
        
        # Negative RPM
        {"rpm": -1.0},
        
        # Total duration > 360 degrees
        {"rise_duration": 120.0, "dwell_duration": 120.0, "fall_duration": 121.0},
        
        # Zero base circle radius
        {"base_circle_radius": 0.0},
        
        # Zero max lift
        {"max_lift": 0.0},
        
        # Zero RPM
        {"rpm": 0.0}
    ]
    
    # Test valid cases
    all_success = True
    
    logger.info("Testing valid parameter cases...")
    for i, params in enumerate(valid_cases):
        logger.info(f"  Testing valid case {i+1}/{len(valid_cases)}:")
        logger.info(f"    Parameters: {params.to_dict()}")
        
        try:
            # Validate parameters by creating a motion law
            motion = MotionLaw(params)
            logger.info("    ✓ Valid parameters accepted")
        except Exception as e:
            logger.error(f"    ✗ Valid parameters rejected: {e}")
            all_success = False
    
    # Test invalid cases
    logger.info("Testing invalid parameter cases...")
    for i, invalid_params_dict in enumerate(invalid_cases):
        logger.info(f"  Testing invalid case {i+1}/{len(invalid_cases)}:")
        logger.info(f"    Invalid parameter: {invalid_params_dict}")
        
        # Create parameters with invalid value
        params_dict = MotionParameters().to_dict()
        params_dict.update(invalid_params_dict)
        
        try:
            # Create parameters object
            params = MotionParameters(**params_dict)
            
            # Try to create motion law (should raise exception)
            motion = MotionLaw(params)
            
            logger.error("    ✗ Invalid parameters accepted")
            all_success = False
        except Exception as e:
            logger.info(f"    ✓ Invalid parameters rejected: {e}")
    
    return all_success

def test_error_handling():
    """Test error handling and recovery mechanisms."""
    logger.info("Testing error handling and recovery mechanisms...")
    
    # Test cases for error handling
    error_cases = [
        # Case 1: Invalid JSON
        {
            "input": "{ invalid json",
            "format": "json",
            "expected_error": True
        },
        
        # Case 2: Invalid TOML
        {
            "input": "invalid toml",
            "format": "toml",
            "expected_error": True
        },
        
        # Case 3: Missing required fields in JSON
        {
            "input": '{"base_circle_radius": 10.0}',
            "format": "json",
            "expected_error": True
        },
        
        # Case 4: Missing required fields in TOML
        {
            "input": 'base_circle_radius = 10.0',
            "format": "toml",
            "expected_error": True
        },
        
        # Case 5: Invalid field types in JSON
        {
            "input": '{"base_circle_radius": "not a number", "max_lift": 10.0, "rise_duration": 120.0, "dwell_duration": 60.0, "fall_duration": 120.0, "rpm": 1000.0}',
            "format": "json",
            "expected_error": True
        },
        
        # Case 6: Invalid field types in TOML
        {
            "input": 'base_circle_radius = "not a number"\nmax_lift = 10.0\nrise_duration = 120.0\ndwell_duration = 60.0\nfall_duration = 120.0\nrpm = 1000.0',
            "format": "toml",
            "expected_error": True
        },
        
        # Case 7: Valid JSON with default values
        {
            "input": '{"base_circle_radius": 10.0, "max_lift": 10.0, "rise_duration": 120.0, "dwell_duration": 60.0, "fall_duration": 120.0, "rpm": 1000.0}',
            "format": "json",
            "expected_error": False
        },
        
        # Case 8: Valid TOML with default values
        {
            "input": 'base_circle_radius = 10.0\nmax_lift = 10.0\nrise_duration = 120.0\ndwell_duration = 60.0\nfall_duration = 120.0\nrpm = 1000.0',
            "format": "toml",
            "expected_error": False
        }
    ]
    
    # Test error handling for each case
    all_success = True
    
    for i, case in enumerate(error_cases):
        logger.info(f"Testing error case {i+1}/{len(error_cases)}:")
        logger.info(f"  Input: {case['input'][:50]}...")
        logger.info(f"  Format: {case['format']}")
        logger.info(f"  Expected error: {case['expected_error']}")
        
        try:
            # Try to deserialize parameters
            if case["format"] == "json":
                params = MotionParameters.from_json(case["input"])
            else:  # toml
                params = MotionParameters.from_toml(case["input"])
            
            if case["expected_error"]:
                logger.error("  ✗ Expected error not raised")
                all_success = False
            else:
                logger.info("  ✓ Successfully parsed valid input")
        except Exception as e:
            if case["expected_error"]:
                logger.info(f"  ✓ Expected error raised: {e}")
            else:
                logger.error(f"  ✗ Unexpected error raised: {e}")
                all_success = False
    
    return all_success

def test_backend_integration():
    """Run the backend integration tests."""
    logger.info("Starting backend integration tests...")
    
    # Create test results directory
    test_dir = TEST_RESULTS_DIR / "backend_integration_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # Run tests
    serialization_success = test_serialization_deserialization()
    parameter_validation_success = test_parameter_validation()
    error_handling_success = test_error_handling()
    
    # Overall success
    all_success = serialization_success and parameter_validation_success and error_handling_success
    
    # Log results
    logger.info("Backend integration tests completed:")
    logger.info(f"  Serialization/deserialization: {'SUCCESS' if serialization_success else 'FAILURE'}")
    logger.info(f"  Parameter validation: {'SUCCESS' if parameter_validation_success else 'FAILURE'}")
    logger.info(f"  Error handling: {'SUCCESS' if error_handling_success else 'FAILURE'}")
    logger.info(f"  Overall: {'SUCCESS' if all_success else 'FAILURE'}")
    
    return all_success

if __name__ == "__main__":
    success = test_backend_integration()
    sys.exit(0 if success else 1)