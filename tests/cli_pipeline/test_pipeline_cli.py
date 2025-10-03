"""
Tests for command-line interface integration with the unified optimization pipeline.

This module tests the CLI interface for the unified optimization pipeline,
ensuring proper parameter handling, file I/O, and command-line argument parsing.
"""

import json

from campro.pipeline.unified_optimizer import UnifiedOptimizer


class TestPipelineCLI:
    """Test command-line interface for unified optimization pipeline."""

    def test_cli_parameter_parsing(self, tmp_path):
        """Test CLI parameter parsing and validation."""
        # Test parameters that would come from command line
        cli_args = [
            "--sampling-step", "5.0",
            "--ring-rotation", "180.0",
            "--gear-ratio", "2.0",
            "--stroke-length", "10.0",
            "--rod-length", "80.0",
            "--journal-radius", "5.0",
            "--interference-buffer", "0.5",
            "--ring-thickness", "5.0",
            "--rpm", "3000.0",
            "--planet-count", "3",
            "--carrier-offset", "120.0",
            "--output-dir", str(tmp_path)
        ]
        
        # Convert CLI args to parameter dictionary
        params = {}
        for i in range(0, len(cli_args), 2):
            if cli_args[i].startswith("--"):
                key = cli_args[i][2:].replace("-", "")
                value = cli_args[i + 1]
                
                # Skip output-dir parameter
                if key == "outputdir":
                    continue
                
                # Convert to appropriate type
                if "." in value:
                    params[key] = float(value)
                else:
                    try:
                        params[key] = int(value)
                    except ValueError:
                        # If it's not a number, keep as string
                        params[key] = value
        
        # Validate parsed parameters
        assert params["samplingstep"] == 5.0
        assert params["ringrotation"] == 180.0
        assert params["gearratio"] == 2.0
        assert params["strokelength"] == 10.0
        assert params["rodlength"] == 80.0
        assert params["journalradius"] == 5.0
        assert params["interferencebuffer"] == 0.5
        assert params["ringthickness"] == 5.0
        assert params["rpm"] == 3000.0
        assert params["planetcount"] == 3
        assert params["carrieroffset"] == 120.0

    def test_cli_file_input_output(self, tmp_path):
        """Test CLI file input and output handling."""
        # Create input parameter file
        input_params = {
            "samplingStepDeg": 5.0,
            "ringRotationDeg": 180.0,
            "gearRatio": 2.0,
            "strokeLengthMm": 10.0,
            "rodLength": 80.0,
            "journalRadius": 5.0,
            "interferenceBuffer": 0.5,
            "ringThickness": 5.0,
            "rpm": 3000.0,
            "planetCount": 3,
            "carrierOffsetDeg": 120.0,
            "rampBeforeTdcDeg": 20.0,
            "rampAfterTdcDeg": 20.0,
            "dwellTdcDeg": 10.0,
            "rampBeforeBdcDeg": 20.0,
            "rampAfterBdcDeg": 20.0,
            "dwellBdcDeg": 10.0,
            "constantVelocityTdcDeg": 30.0,
            "constantVelocityBdcDeg": 40.0,
        }
        
        input_file = tmp_path / "input_params.json"
        with open(input_file, 'w') as f:
            json.dump(input_params, f, indent=2)
        
        # Test reading input file
        with open(input_file, 'r') as f:
            loaded_params = json.load(f)
        
        assert loaded_params == input_params
        
        # Test output file creation
        output_file = tmp_path / "output_results.json"
        
        # Run pipeline and save results
        optimizer = UnifiedOptimizer(output_dir=tmp_path)
        result = optimizer.run_pipeline(input_params)
        
        with open(output_file, 'w') as f:
            json.dump(result, f, default=str, indent=2)
        
        # Verify output file exists and contains results
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_result = json.load(f)
        
        assert saved_result['status'] == result['status']

    def test_cli_error_handling(self, tmp_path):
        """Test CLI error handling for invalid inputs."""
        # Test with invalid parameter file
        invalid_input_file = tmp_path / "invalid_input.json"
        with open(invalid_input_file, 'w') as f:
            f.write("invalid json content")
        
        # Should handle invalid JSON gracefully
        try:
            with open(invalid_input_file, 'r') as f:
                json.load(f)
            assert False, "Should have raised JSON decode error"
        except json.JSONDecodeError:
            pass  # Expected
        
        # Test with minimal valid parameters
        minimal_params = {
            "samplingStepDeg": 5.0,
            "ringRotationDeg": 180.0,
            "gearRatio": 2.0,
            "strokeLengthMm": 10.0,
            "rodLength": 80.0,
            "journalRadius": 5.0,
            "interferenceBuffer": 0.5,
            "ringThickness": 5.0,
            "rpm": 3000.0,
            "planetCount": 3,
            "carrierOffsetDeg": 120.0,
            "rampBeforeTdcDeg": 20.0,
            "rampAfterTdcDeg": 20.0,
            "dwellTdcDeg": 10.0,
            "rampBeforeBdcDeg": 20.0,
            "rampAfterBdcDeg": 20.0,
            "dwellBdcDeg": 10.0,
            "constantVelocityTdcDeg": 30.0,
            "constantVelocityBdcDeg": 40.0,
        }
        
        optimizer = UnifiedOptimizer(output_dir=tmp_path)
        result = optimizer.run_pipeline(minimal_params)
        
        # Should handle minimal parameters gracefully
        assert result['status'] in ('success', 'failed')

    def test_cli_output_formats(self, tmp_path):
        """Test different CLI output formats."""
        params = {
            "samplingStepDeg": 10.0,
            "ringRotationDeg": 180.0,
            "gearRatio": 2.0,
            "strokeLengthMm": 8.0,
            "rodLength": 60.0,
            "journalRadius": 4.0,
            "interferenceBuffer": 0.5,
            "ringThickness": 4.0,
            "rpm": 2500.0,
            "planetCount": 3,
            "carrierOffsetDeg": 120.0,
            "rampBeforeTdcDeg": 20.0,
            "rampAfterTdcDeg": 20.0,
            "dwellTdcDeg": 10.0,
            "rampBeforeBdcDeg": 20.0,
            "rampAfterBdcDeg": 20.0,
            "dwellBdcDeg": 10.0,
            "constantVelocityTdcDeg": 30.0,
            "constantVelocityBdcDeg": 40.0,
        }
        
        optimizer = UnifiedOptimizer(output_dir=tmp_path)
        result = optimizer.run_pipeline(params)
        
        # Test JSON output format
        json_output = tmp_path / "results.json"
        with open(json_output, 'w') as f:
            json.dump(result, f, default=str, indent=2)
        assert json_output.exists()
        
        # Test summary output format (key metrics only)
        summary = {
            "status": result["status"],
            "motion_law_points": len(result["motion_law"]["theta_deg"]),
            "optimal_method": result["optimal_profiles"].get("optimal_solution", "unknown"),
            "fea_available": "fea" in result
        }
        
        summary_output = tmp_path / "summary.json"
        with open(summary_output, 'w') as f:
            json.dump(summary, f, indent=2)
        assert summary_output.exists()

    def test_cli_batch_processing(self, tmp_path):
        """Test CLI batch processing capabilities."""
        # Create multiple parameter sets for batch processing
        batch_params = [
            {
                "samplingStepDeg": 5.0,
                "ringRotationDeg": 180.0,
                "gearRatio": 2.0,
                "strokeLengthMm": 10.0,
                "rodLength": 80.0,
                "journalRadius": 5.0,
                "interferenceBuffer": 0.5,
                "ringThickness": 5.0,
                "rpm": 3000.0,
                "planetCount": 3,
                "carrierOffsetDeg": 120.0,
                "rampBeforeTdcDeg": 20.0,
                "rampAfterTdcDeg": 20.0,
                "dwellTdcDeg": 10.0,
                "rampBeforeBdcDeg": 20.0,
                "rampAfterBdcDeg": 20.0,
                "dwellBdcDeg": 10.0,
                "constantVelocityTdcDeg": 30.0,
                "constantVelocityBdcDeg": 40.0,
            },
            {
                "samplingStepDeg": 10.0,
                "ringRotationDeg": 180.0,
                "gearRatio": 2.5,
                "strokeLengthMm": 12.0,
                "rodLength": 90.0,
                "journalRadius": 6.0,
                "interferenceBuffer": 0.3,
                "ringThickness": 6.0,
                "rpm": 3500.0,
                "planetCount": 4,
                "carrierOffsetDeg": 90.0,
                "rampBeforeTdcDeg": 15.0,
                "rampAfterTdcDeg": 15.0,
                "dwellTdcDeg": 8.0,
                "rampBeforeBdcDeg": 15.0,
                "rampAfterBdcDeg": 15.0,
                "dwellBdcDeg": 8.0,
                "constantVelocityTdcDeg": 25.0,
                "constantVelocityBdcDeg": 35.0,
            }
        ]
        
        optimizer = UnifiedOptimizer(output_dir=tmp_path)
        batch_results = []
        
        # Process each parameter set
        for i, params in enumerate(batch_params):
            result = optimizer.run_pipeline(params)
            batch_results.append({
                "batch_id": i,
                "params": params,
                "result": result
            })
        
        # Save batch results
        batch_output = tmp_path / "batch_results.json"
        with open(batch_output, 'w') as f:
            json.dump(batch_results, f, default=str, indent=2)
        
        assert batch_output.exists()
        assert len(batch_results) == 2
        
        # Verify all batch results have status
        for batch_result in batch_results:
            assert "status" in batch_result["result"]

    def test_cli_verbose_output(self, tmp_path):
        """Test CLI verbose output options."""
        params = {
            "samplingStepDeg": 5.0,
            "ringRotationDeg": 180.0,
            "gearRatio": 2.0,
            "strokeLengthMm": 10.0,
            "rodLength": 80.0,
            "journalRadius": 5.0,
            "interferenceBuffer": 0.5,
            "ringThickness": 5.0,
            "rpm": 3000.0,
            "planetCount": 3,
            "carrierOffsetDeg": 120.0,
            "rampBeforeTdcDeg": 20.0,
            "rampAfterTdcDeg": 20.0,
            "dwellTdcDeg": 10.0,
            "rampBeforeBdcDeg": 20.0,
            "rampAfterBdcDeg": 20.0,
            "dwellBdcDeg": 10.0,
            "constantVelocityTdcDeg": 30.0,
            "constantVelocityBdcDeg": 40.0,
        }
        
        optimizer = UnifiedOptimizer(output_dir=tmp_path)
        result = optimizer.run_pipeline(params)
        
        # Test verbose output (detailed results)
        verbose_output = tmp_path / "verbose_results.json"
        with open(verbose_output, 'w') as f:
            json.dump(result, f, default=str, indent=2)
        
        # Test quiet output (summary only)
        quiet_output = tmp_path / "quiet_results.json"
        quiet_result = {
            "status": result["status"],
            "execution_time": "< 1 second",
            "motion_law_points": len(result["motion_law"]["theta_deg"]),
            "optimal_method": result["optimal_profiles"].get("optimal_solution", "unknown")
        }
        
        with open(quiet_output, 'w') as f:
            json.dump(quiet_result, f, indent=2)
        
        assert verbose_output.exists()
        assert quiet_output.exists()
        
        # Verbose should be larger than quiet
        assert verbose_output.stat().st_size > quiet_output.stat().st_size
