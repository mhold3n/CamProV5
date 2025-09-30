from pathlib import Path
from typing import Dict, Any
import logging

import numpy as np

from campro.optimization.collocation_optimizer import CollocationOptimizer, CollocationParameters
from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters
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
		self.phase2_gear_optimizer = Phase2GearOptimizer()
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
			'grid': motion_solution.theta_grid,
			'theta_deg': motion_solution.theta_grid,  # Also provide theta_deg for FEA analyzer
			'displacement': motion_solution.position,
			'velocity': motion_solution.velocity,
			'acceleration': motion_solution.acceleration,
		}

		# Phase 2: Gear profiles using our new Phase 2 system
		# Create Phase 2 parameters from input
		phase2_params = Phase2Parameters(
			node_count=input_params.get('nodeCount', 32),
			max_iterations=input_params.get('maxIterations', 200),
			tolerance=input_params.get('tolerance', 1e-6),
			constraint_tolerance=input_params.get('constraintTolerance', 1e-6),
			force_transfer_weight=input_params.get('forceTransferWeight', 1.0),
			efficiency_weight=input_params.get('efficiencyWeight', 1.0),
			smoothness_weight=input_params.get('smoothnessWeight', 0.1),
			clearance_safety_margin=input_params.get('clearanceSafetyMargin', 0.1),
			min_gear_clearance=input_params.get('minGearClearance', 0.05),
			piston_area_mm2=input_params.get('pistonAreaMm2', 100.0),
			cylinder_pressure_bar=input_params.get('cylinderPressureBar', 10.0),
			material_strength_mpa=input_params.get('materialStrengthMpa', 500.0)
		)
		
		# Create Phase 2 optimizer with parameters
		phase2_optimizer = Phase2GearOptimizer(phase2_params)
		
		# Run Phase 2 optimization
		gear_solution = phase2_optimizer.optimize_gear_profiles(motion_law, input_params)
		
		if not gear_solution.success:
			return {
				'status': 'failed',
				'stage': 'gear_optimization',
				'error': gear_solution.solver_status,
			}
		
		# Convert gear solution to the format expected by downstream components
		optimal_profiles = {
			# Use the keys expected by tooth generator
			'theta_deg': gear_solution.theta_grid,
			'r_sun': gear_solution.sun_radius,
			'r_planet': gear_solution.planet_radius,
			'r_ring_inner': gear_solution.ring_radius,
			# Keep additional data for analysis
			'gear_clearance': gear_solution.gear_clearance,
			'force_transfer_efficiency': gear_solution.force_transfer_efficiency,
			'max_contact_stress': gear_solution.max_contact_stress,
			'objective_value': gear_solution.objective_value,
			'constraint_violation': gear_solution.constraint_violation,
			'iterations': gear_solution.iterations,
			'execution_time': gear_solution.execution_time,
			'solver_status': gear_solution.solver_status
		}

		# Phase 3: Tooth profile generation
		# Use the optimal profiles directly from Phase 2
		tooth_profiles = self.tooth_generator.generate_tooth_profiles(optimal_profiles, input_params)

		# Phase 4: FEA analysis
		fea_results = self.fea_analyzer.analyze_assembly(optimal_profiles, tooth_profiles, motion_law, input_params)

		compiled = {
			'status': 'success',
			'motion_law': motion_law,
			'optimal_profiles': optimal_profiles,
			'tooth_profiles': tooth_profiles,
			'fea': fea_results,
		}
		log.info("Unified optimization pipeline completed")
		return compiled
