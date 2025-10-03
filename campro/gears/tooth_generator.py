"""
Tooth profile generator for CamProV5.

This module generates tooth profiles using robust gear design calculations.
"""

from typing import Dict, Any
import numpy as np
import logging
from campro.solvers.robust_gear_design import RobustGearDesign, GearMaterialProperties, GearDesignParameters

log = logging.getLogger(__name__)


class ToothProfileGenerator:
	"""Generate tooth profiles leveraging RobustGearDesign calculations."""

	def __init__(self) -> None:
		material = GearMaterialProperties()
		design = GearDesignParameters()
		self.designer = RobustGearDesign(material, design)

	def generate_tooth_profiles(self, gear_profiles: Dict[str, np.ndarray], params: Dict[str, Any]) -> Dict[str, np.ndarray]:
		"""
		Generate tooth profiles for sun, planet, and ring gears.

		Parameters
		----------
		gear_profiles : Dict[str, np.ndarray]
			Either XY centerlines for 'sun'/'planet'/'ring' or polar fields with
			'theta_deg' and 'r_sun'/'r_planet'/'r_ring_inner'.
		params : Dict[str, Any]
			Design parameters including loads and material data consumed by RobustGearDesign.

		Returns
		-------
		Dict[str, np.ndarray]
			Tooth profiles for 'sun_teeth', 'planet_teeth', 'ring_teeth'.
		"""
		# Normalize input: ensure XY centerlines exist; synthesize if needed
		profiles_xy = self._ensure_xy_centerlines(gear_profiles)

		# Derive simple contact force trace to size thickness; fall back if not provided
		contact_force = self._estimate_contact_force_trace(params, profiles_xy)

		# Radii per-gear; if scalar provided in profiles dict, broadcast or compute from XY
		r_sun = self._extract_radius(gear_profiles, 'r_sun', default_mm=10.0, fallback_curve_key='sun')
		r_planet = self._extract_radius(gear_profiles, 'r_planet', default_mm=15.0, fallback_curve_key='planet')
		r_ring = self._extract_radius(gear_profiles, 'r_ring_inner', default_mm=25.0, fallback_curve_key='ring')

		# Compute tooth thickness fields
		th_sun = self.designer.calculate_tooth_thickness(r_sun, contact_force)
		th_planet = self.designer.calculate_tooth_thickness(r_planet, contact_force)
		th_ring = self.designer.calculate_tooth_thickness(r_ring, contact_force)

		# Build simple rectangular tooth strips around pitch curve as placeholder geometry
		sun_teeth = self._sweep_tooth_strip(profiles_xy['sun'], th_sun)
		planet_teeth = self._sweep_tooth_strip(profiles_xy['planet'], th_planet)
		ring_teeth = self._sweep_tooth_strip(profiles_xy['ring'], th_ring)

		return {
			'sun_teeth': sun_teeth,
			'planet_teeth': planet_teeth,
			'ring_teeth': ring_teeth,
		}

	def _ensure_xy_centerlines(self, gp: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
		# If XY arrays exist, validate and return
		if all(k in gp for k in ('sun', 'planet', 'ring')):
			self._validate_inputs(gp)
			return { 'sun': gp['sun'], 'planet': gp['planet'], 'ring': gp['ring'] }
		# Otherwise, synthesize from polar radii with CORRECT planetary gearset kinematics
		if 'theta_deg' in gp and all(k in gp for k in ('r_sun','r_planet','r_ring_inner')):
			theta_rad = np.deg2rad(np.asarray(gp['theta_deg']))
			r_sun = np.asarray(gp['r_sun'])
			r_planet = np.asarray(gp['r_planet'])
			r_ring_inner = np.asarray(gp['r_ring_inner'])
			
			# CORRECTED: Planetary gearset kinematics
			# 1. Sun gear: centered at origin (0,0)
			sun_xy = np.stack([r_sun * np.cos(theta_rad), r_sun * np.sin(theta_rad)], axis=1)
			
			# 2. Ring gear: centered at origin (0,0) - stationary
			ring_xy = np.stack([r_ring_inner * np.cos(theta_rad), r_ring_inner * np.sin(theta_rad)], axis=1)
			
			# 3. Planet gear: orbits around the sun gear with proper kinematics
			# Planet center distance from sun center = (r_ring_inner - r_sun) / 2
			# This ensures the planet is tangent to both sun and ring
			planet_center_distance = (r_ring_inner - r_sun) / 2.0
			
			# Planet center positions (orbiting around sun)
			planet_center_x = planet_center_distance * np.cos(theta_rad)
			planet_center_y = planet_center_distance * np.sin(theta_rad)
			
			# CRITICAL: Planet gear must rotate as it orbits to maintain proper meshing
			# For a 2:1 gear ratio, the planet rotates 2x the ring rotation
			# This is the key insight - the planet gear profile is not static!
			gear_ratio = 2.0  # This should come from parameters
			planet_rotation_angle = gear_ratio * theta_rad
			
			# Planet gear profile relative to its own center, accounting for rotation
			planet_xy = np.stack([
				planet_center_x + r_planet * np.cos(planet_rotation_angle),
				planet_center_y + r_planet * np.sin(planet_rotation_angle)
			], axis=1)
			
			return {
				'sun': sun_xy,
				'planet': planet_xy,
				'ring': ring_xy,
			}
		raise ValueError("Expected XY centerlines ('sun','planet','ring') or polar fields ('theta_deg','r_sun','r_planet','r_ring_inner')")

	def _validate_inputs(self, gear_profiles: Dict[str, np.ndarray]) -> None:
		for key in ('sun', 'planet', 'ring'):
			if key not in gear_profiles:
				raise ValueError(f"Missing gear profile: {key}")
			if not isinstance(gear_profiles[key], np.ndarray) or gear_profiles[key].size == 0:
				raise ValueError(f"Gear profile '{key}' must be a non-empty numpy array")
			if gear_profiles[key].ndim != 2 or gear_profiles[key].shape[1] != 2:
				raise ValueError(f"Gear profile '{key}' must be an Nx2 array of XY points")

	def _estimate_contact_force_trace(self, params: Dict[str, Any], profiles_xy: Dict[str, np.ndarray]) -> np.ndarray:
		rpm = float(params.get('rpm', 3000.0))
		base_force = float(params.get('contact_force', 1000.0))
		n = profiles_xy['sun'].shape[0]
		phi = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
		return base_force * (1.0 + 0.1 * np.sin(phi * max(1.0, rpm / 3000.0)))

	def _extract_radius(self, profiles: Dict[str, np.ndarray], scalar_key: str, default_mm: float, fallback_curve_key: str) -> np.ndarray:
		if scalar_key in profiles and isinstance(profiles[scalar_key], (int, float)):
			r = float(profiles[scalar_key])
			n = (profiles[fallback_curve_key].shape[0] if isinstance(profiles.get(fallback_curve_key), np.ndarray)
				else np.asarray(profiles.get('theta_deg')).shape[0] if 'theta_deg' in profiles else 360)
			return np.full(n, r, dtype=float)
		# Prefer direct radius array if provided
		if scalar_key in profiles and isinstance(profiles[scalar_key], np.ndarray):
			return np.asarray(profiles[scalar_key])
		# Fallback: approximate radius from curve extents
		if isinstance(profiles.get(fallback_curve_key), np.ndarray):
			curve = profiles[fallback_curve_key]
			xy_radius = np.linalg.norm(curve, axis=1)
			return np.maximum(xy_radius, default_mm)
		# Last resort: default constant
		n = np.asarray(profiles.get('theta_deg')).shape[0] if 'theta_deg' in profiles else 360
		return np.full(n, default_mm, dtype=float)

	def _sweep_tooth_strip(self, centerline: np.ndarray, thickness_mm: np.ndarray) -> np.ndarray:
		n = centerline.shape[0]
		diff = np.gradient(centerline, axis=0)
		norm = np.stack([-diff[:,1], diff[:,0]], axis=1)
		norm_mag = np.linalg.norm(norm, axis=1, keepdims=True)
		norm_unit = np.where(norm_mag > 1e-9, norm / norm_mag, 0.0)
		half_w = (thickness_mm / 2.0).reshape(n, 1)
		upper = centerline + norm_unit * half_w
		lower = centerline - norm_unit * half_w
		return np.hstack([upper, lower])
