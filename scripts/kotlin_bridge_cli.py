#!/usr/bin/env python3
"""
CLI wrapper for the unified optimizer to support Kotlin bridge integration.
This script provides the command-line interface that the Kotlin bridge expects.
"""

import sys
import json
import argparse
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from campro.pipeline.unified_optimizer import UnifiedOptimizer


def main():
    """Main CLI entry point for Kotlin bridge integration."""
    parser = argparse.ArgumentParser(description='Unified Optimization Pipeline CLI for Kotlin Bridge')
    parser.add_argument('--input', required=True, help='Input parameters JSON file')
    parser.add_argument('--output', required=True, help='Output results JSON file')
    parser.add_argument('--output-dir', required=True, help='Output directory for results')
    
    args = parser.parse_args()
    
    try:
        # Read input parameters
        with open(args.input, 'r') as f:
            parameters = json.load(f)
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize optimizer
        optimizer = UnifiedOptimizer(output_dir=output_dir)
        
        # Run pipeline
        start_time = time.time()
        result = optimizer.run_pipeline(parameters)
        execution_time = time.time() - start_time
        
        # Add execution time to result
        result['execution_time'] = execution_time
        
        # Convert numpy arrays to lists for JSON serialization
        def convert_numpy_to_list(obj):
            if isinstance(obj, Path):
                return str(obj)
            if isinstance(obj, dict):
                return {k: convert_numpy_to_list(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_numpy_to_list(elem) for elem in obj]
            if hasattr(obj, 'tolist'):  # numpy arrays
                return obj.tolist()
            return obj
        
        serializable_result = convert_numpy_to_list(result)
        
        # Write results
        with open(args.output, 'w') as f:
            json.dump(serializable_result, f, indent=2)
        
        print(f"Optimization completed successfully in {execution_time:.2f} seconds")
        return 0
        
    except Exception as e:
        # Create error result
        error_result = {
            "status": "failed",
            "error": str(e),
            "execution_time": 0.0,
            "stage": "pipeline_execution"
        }
        
        try:
            with open(args.output, 'w') as f:
                json.dump(error_result, f, indent=2)
        except:
            pass
        
        print(f"Optimization failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
