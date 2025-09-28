from pathlib import Path
from typing import Dict, Any
import logging

import numpy as np

from campro.optimization.collocation_optimizer import CollocationOptimizer, CollocationParameters
from campro.optimization.litvin_optimizer import LitvinGearOptimizer
from campro.optimization.collocation_gear_optimizer import CollocationGearOptimizer
from campro.optimization.efficiency_optimizer import EfficiencyOptimizer
from campro.gears.tooth_generator import ToothProfileGenerator
from campro.analysis.fea_analyzer import FEAAnalyzer

log = logging.getLogger(__name__)


class UnifiedOptimizer:
	"""Unified optimization pipeline orchestrating all components."""

	def __init__(self, output_dir: Path | None = None) -> None:
		self.output_dir = Path(output_dir) if output_dir else Path("./pipeline_outputs")
		self.output_dir.mkdir(parents=True, exist_ok=True)

		self.collocation_optimizer = CollocationOptimizer()
		self.litvin_optimizer = LitvinGearOptimizer()
		self.collocation_gear_optimizer = CollocationGearOptimizer()
		self.efficiency_optimizer = EfficiencyOptimizer()
		self.tooth_generator = ToothProfileGenerator()
		self.fea_analyzer = FEAAnalyzer()

	def run_pipeline(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Run the unified optimization pipeline end-to-end.

		Parameters
		----------
		input_params : Dict[str, Any]
			Input parameters for motion law and gear optimization.

		Returns
		-------
		Dict[str, Any]
			Compiled results including motion law, profiles, tooth geometry, and FEA summary.
		"""
		log.info("Starting unified optimization pipeline")

		# Phase 1: Motion law via collocation
		motion_solution = self.collocation_optimizer.optimize_motion_law(input_params)
		if not motion_solution.success:
			return {
				'status': 'failed',
				'stage': 'motion_law',
				'error': motion_solution.solver_status,
			}
		motion_law = {
			'theta_deg': motion_solution.theta_grid,
			'displacement': motion_solution.position,
			'velocity': motion_solution.velocity,
			'acceleration': motion_solution.acceleration,
		}

		# Phase 2: Gear profiles from both methods
		litvin_profiles = self.litvin_optimizer.optimize_profiles(motion_law, input_params)
		
		# Create collocation parameters for gear optimization
		collocation_params = CollocationParameters(
			node_count=len(motion_law['theta_deg']),
			continuation_steps=5,
			tolerance=1e-6
		)
		collocation_profiles = self.collocation_gear_optimizer.optimize_profiles(motion_law, input_params, collocation_params)

		# Phase 3: Efficiency comparison and selection
		optimal_profiles = self.efficiency_optimizer.compare_solutions(
			litvin_profiles, collocation_profiles, motion_law, input_params
		)

		# Phase 4: Tooth profile generation
		# Extract actual profiles from optimal solution
		if 'optimal_profiles' in optimal_profiles:
			# Efficiency optimizer returned nested structure
			actual_profiles = optimal_profiles['optimal_profiles']
		else:
			# Direct structure
			actual_profiles = optimal_profiles
		
		tooth_profiles = self.tooth_generator.generate_tooth_profiles(actual_profiles, input_params)

		# Phase 5: FEA analysis
		fea_results = self.fea_analyzer.analyze_assembly(actual_profiles, tooth_profiles, motion_law, input_params)

		compiled = {
			'status': 'success',
			'motion_law': motion_law,
			'optimal_profiles': optimal_profiles,
			'tooth_profiles': tooth_profiles,
			'fea': fea_results,
		}
		log.info("Unified optimization pipeline completed")
		return compiled
