from pathlib import Path
from typing import Dict, Any, Optional
import logging
import time

# Enhanced optimizers with full physics
from campro.optimization.enhanced_motion_law_optimizer import EnhancedMotionLawOptimizer
from campro.optimization.enhanced_gear_optimizer import EnhancedGearOptimizer


# Other components
from campro.gears.tooth_generator import ToothProfileGenerator
from campro.analysis.fea_analyzer import FEAAnalyzer

# Parameter mapping and result adaptation
from campro.pipeline.parameter_mapper import ParameterMapper
from campro.pipeline.result_adapter import ResultAdapter

log = logging.getLogger(__name__)


class UnifiedOptimizer:
	"""Unified optimization pipeline orchestrating all components with enhanced physics."""

	def __init__(self, output_dir: Path | None = None) -> None:
		self.output_dir = Path(output_dir) if output_dir else Path("./pipeline_outputs")
		self.output_dir.mkdir(parents=True, exist_ok=True)
		
		# Enhanced optimizers will be initialized in run_pipeline with mapped parameters
		self.enhanced_motion_optimizer: Optional[EnhancedMotionLawOptimizer] = None
		self.enhanced_gear_optimizer: Optional[EnhancedGearOptimizer] = None
		log.info("UnifiedOptimizer initialized with enhanced optimizers")
		
		# Common components
		self.tooth_generator = ToothProfileGenerator()
		self.fea_analyzer = FEAAnalyzer()

	def run_pipeline(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Run the unified optimization pipeline end-to-end with enhanced physics.

		Parameters
		----------
		input_params : Dict[str, Any]
			Input parameters for motion law and gear optimization.

		Returns
		-------
		Dict[str, Any]
			Compiled results including motion law, profiles, tooth geometry, and FEA summary.
		"""
		return self._run_enhanced_pipeline(input_params)
	
	def _run_enhanced_pipeline(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
		"""Run pipeline with enhanced optimizers and full physics."""
		log.info("Starting enhanced optimization pipeline with thermodynamic and transmission physics")
		start_time = time.time()
		
		# Map UI parameters to enhanced optimizer parameters
		enhanced_motion_params = ParameterMapper.map_to_enhanced_motion_params(input_params)
		enhanced_gear_params = ParameterMapper.map_to_enhanced_gear_params(input_params)
		
		# Initialize enhanced optimizers with mapped parameters
		self.enhanced_motion_optimizer = EnhancedMotionLawOptimizer(enhanced_motion_params)
		self.enhanced_gear_optimizer = EnhancedGearOptimizer(enhanced_gear_params)
		
		# Phase 1: Enhanced motion law optimization with thermodynamics
		phase1_start = time.time()
		log.info("Phase 1: Enhanced motion law optimization with thermodynamic physics")
		motion_solution = self.enhanced_motion_optimizer.optimize_motion_law(input_params)
		phase1_time = time.time() - phase1_start
		log.info(f"Enhanced Phase 1 completed in {phase1_time:.3f}s")
		
		# Adapt enhanced motion law result to expected format
		motion_law = ResultAdapter.adapt_motion_law_result(motion_solution)
		
		# Validate the adapted result
		if not ResultAdapter.validate_motion_law_result(motion_law):
			raise ValueError("Motion law result validation failed")

		# Phase 2: Enhanced gear profile optimization with transmission physics
		phase2_start = time.time()
		log.info("Phase 2: Enhanced gear profile optimization with transmission physics")
		gear_solution = self.enhanced_gear_optimizer.optimize_gear_profiles(motion_law, input_params)
		phase2_time = time.time() - phase2_start
		log.info(f"Enhanced Phase 2 completed in {phase2_time:.3f}s")
	
		# Adapt enhanced gear solution to expected format
		optimal_profiles = ResultAdapter.adapt_gear_result(gear_solution)
		
		# Validate the adapted result
		if not ResultAdapter.validate_gear_result(optimal_profiles):
			raise ValueError("Gear result validation failed")

		# Phase 3: Efficiency Analysis and Comparison
		# Note: Efficiency analysis is now integrated into the enhanced optimizers
		efficiency_analysis = {
			"motion_law_efficiency": motion_solution.get("efficiency", 0.0),
			"gear_efficiency": gear_solution.get("efficiency", 0.0),
			"overall_efficiency": (motion_solution.get("efficiency", 0.0) + gear_solution.get("efficiency", 0.0)) / 2.0
		}
		
		# Phase 4: Tooth profile generation
		# Use the optimal profiles directly from Phase 2
		tooth_profiles = self.tooth_generator.generate_tooth_profiles(optimal_profiles, input_params)

		# Phase 5: FEA analysis
		# TODO: FUTURE ENHANCEMENT - Add RPM sweep analysis capability
		# The FEA analyzer will be extended to support RPM sweep analysis across multiple
		# operating speeds (e.g., 500-10000 RPM in 500 RPM steps) to identify resonant
		# frequencies and critical operating speeds. This will provide much more comprehensive
		# analysis results but is not currently a priority.
		fea_results = self.fea_analyzer.analyze_assembly(optimal_profiles, tooth_profiles, motion_law, input_params)

		total_time = time.time() - start_time
		log.info(f"Enhanced optimization pipeline completed in {total_time:.3f}s")

		# Ensure all arrays are numpy arrays for consistency
		motion_law = ResultAdapter.ensure_numpy_arrays(motion_law)
		optimal_profiles = ResultAdapter.ensure_numpy_arrays(optimal_profiles)
		
		compiled = {
			'status': 'success',
			'motion_law': motion_law,
			'optimal_profiles': optimal_profiles,
			'efficiency_analysis': efficiency_analysis,
			'tooth_profiles': tooth_profiles,
			'fea': fea_results,
			# Add performance data
			'performance': {
				'phase1_time_s': phase1_time,
				'phase2_time_s': phase2_time,
				'total_time_s': total_time,
				'optimizer_type': 'enhanced'
			}
		}
		return compiled
	
