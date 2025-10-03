#!/usr/bin/env python3
"""
Demo script to run the unified optimization pipeline.
"""

import sys
import json
import time
from pathlib import Path
import argparse

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from campro.pipeline.unified_optimizer import UnifiedOptimizer  # noqa: E402
from campro.logging import get_logger  # noqa: E402
from campro.solver_config import homotopy_stages  # noqa: E402

# Set up logging
logger = get_logger(__name__)


def get_test_parameters():
	"""Get comprehensive test parameters."""
	return {
		"samplingStepDeg": 1.0,
		"ringRotationDeg": 180.0,
		"gearRatio": 2.0,
		"strokeLengthMm": 100.0,
		"rodLength": 100.0,
		"journalRadius": 5.0,
		"interferenceBuffer": 0.5,
		"ringThickness": 3.0,
		"rpm": 3000.0,
		"planetCount": 2,
		"carrierOffsetDeg": 180.0,
		"rampBeforeTdcDeg": 6.0,
		"rampAfterTdcDeg": 5.0,
		"dwellTdcDeg": 4.0,
		"rampBeforeBdcDeg": 7.0,
		"rampAfterBdcDeg": 4.0,
		"dwellBdcDeg": 3.0,
		"constantVelocityTdcDeg": 30.0,
		"constantVelocityBdcDeg": 40.0,
		"planetRadiusBaseFactor": 0.15,
		"planetRadiusVariationFactor": 0.05,
		"sunRadiusBaseFactor": 0.1,
		"sunRadiusVariationFactor": 0.02,
		"strokeAchievableFactor": 0.8,
		"clearanceSafetyMargin": 0.1,
		"adjustmentSplitFactor": 0.5
	}


def main():
	"""Run the unified optimization pipeline demo."""
	parser = argparse.ArgumentParser(description="CamProV5 unified demo")
	parser.add_argument("--free-piston", action="store_true", dest="free_piston", help="Run free-piston Radau NLP demo with homotopy")
	parser.add_argument("--N", type=int, default=40, help="Grid points for free-piston demo")
	args = parser.parse_args()

	logger.info("🚀 CAMPROV5 UNIFIED OPTIMIZATION PIPELINE DEMO")
	logger.info("=" * 60)
	
	# Create output directory
	output_dir = Path("pipeline_demo_output")
	output_dir.mkdir(parents=True, exist_ok=True)
	
	if args.free_piston:
		logger.info("\n🔧 RUNNING FREE-PISTON RADAU NLP DEMO (staged homotopy)...")
		stages = [
			{"ipopt": {"tol": 1e-3, "acceptable_tol": 1e-2, "max_iter": 500, "print_level": 0}},
			{"ipopt": {"tol": 1e-5, "acceptable_tol": 1e-4, "max_iter": 1000, "print_level": 0}},
			{"ipopt": {"tol": 1e-6, "acceptable_tol": 1e-5, "max_iter": 2000, "print_level": 0}},
		]

		def _build_nlp(s: float):
			# Delegate to free-piston builder through run_problem_with_N pattern
			# For staged homotopy demo, we just rebuild with same smoothing (currently unused)
			from campro.optimization.free_piston import _build_free_piston_radau  # type: ignore
			nlp, nlp_args = _build_free_piston_radau(N=int(args.N), degree=3, smoothing=s)
			nlp.update(nlp_args)
			return nlp

		res = homotopy_stages(_build_nlp, smoothing_sequence=[1.0, 0.5, 0.1], initial_guess=None, option_sequence=stages, scaling_from_bounds=True)
		J = float(res.get("f", float("nan")))
		logger.info(f"  • Free-piston objective J: {J:.6e}")
		# Persist artifacts
		artifacts = {
			"grid_points": int(args.N),
			"stages": stages,
			"objective": J,
		}
		with open(output_dir / "free_piston_artifacts.json", "w") as f:
			json.dump(artifacts, f, indent=2)
		logger.info("\n✅ FREE-PISTON DEMO COMPLETED!")
		return 0

	# Standard pipeline path
	params = get_test_parameters()
	
	logger.info("\n📋 TEST PARAMETERS:")
	logger.info(f"  • Stroke Length: {params['strokeLengthMm']} mm")
	logger.info(f"  • Gear Ratio: {params['gearRatio']}:1")
	logger.info(f"  • Ring Rotation: {params['ringRotationDeg']}°")
	logger.info(f"  • Planet Count: {params['planetCount']}")
	logger.info(f"  • RPM: {params['rpm']}")
	
	logger.info("\n🔧 INITIALIZING UNIFIED OPTIMIZER...")
	optimizer = UnifiedOptimizer(output_dir=output_dir)
	
	logger.info("\n⚡ RUNNING UNIFIED OPTIMIZATION PIPELINE...")
	start_time = time.time()
	
	try:
		result = optimizer.run_pipeline(params)
		execution_time = time.time() - start_time
		
		logger.info("\n📊 RESULTS:")
		logger.info(f"  • Status: {result['status']}")
		logger.info(f"  • Execution Time: {execution_time:.2f} seconds")
		
		if result['status'] == 'success':
			motion_law = result['motion_law']
			logger.info(f"  • Motion Law Points: {len(motion_law['theta_deg'])}")
			logger.info(f"  • Max Displacement: {max(motion_law['displacement']):.1f} mm")
			
			optimal_profiles = result['optimal_profiles']
			logger.info(f"  • Optimal Method: {optimal_profiles['optimal_solution']}")
			
			logger.info("\n✅ DEMO COMPLETED SUCCESSFULLY!")
		else:
			logger.info(f"  • Error: {result.get('error', 'Unknown')}")
			logger.info("\n⚠️  DEMO COMPLETED WITH ISSUES")
		
		results_file = output_dir / "results.json"
		with open(results_file, 'w') as f:
			json.dump(result, f, indent=2, default=str)
		logger.info(f"  • Results saved to: {results_file}")
		
	except Exception as e:
		logger.info(f"\n❌ DEMO FAILED: {str(e)}")
		return 1
	
	return 0


if __name__ == "__main__":
	sys.exit(main())
