"""
Gear Profile Generation for Planetary Gearset Optimization

This module extracts the robust gear profile generation logic from the scripts
and provides it as a modular component for the unified optimization pipeline.
"""

import numpy as np
from typing import Dict, List, Tuple, Any
import logging

from campro.utils.angle_units import (
    ensure_percent_grid,
    percent_to_degrees,
    percent_to_radians,
    resolve_cycle_percent,
    degrees_to_percent,
)

logger = logging.getLogger(__name__)


class GearProfileGenerator:
    """
    Gear profile generator for planetary gearset optimization.
    
    This class extracts the robust gear profile generation logic from the scripts
    and provides it as modular methods for the unified optimization pipeline.
    """
    
    def __init__(self):
        """Initialize the gear profile generator."""
        self.logger = logger
    
    def generate_motion_law_piecewise(self, params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate motion law using piecewise method with proper acceleration profile.
        
        Extracted from GearProfileGenerator.generate_motion_law_piecewise()
        
        Args:
            params: Motion law parameters dictionary
            
        Returns:
            Tuple of (theta_deg, displacement, velocity, acceleration)
        """
        self.logger.info("Generating motion law using piecewise method with proper acceleration profile...")
        
        # CORRECTED: Generate motion law using percent of the ring rotation.
        ring_rotation_pct = resolve_cycle_percent(params, "ringRotation")
        sampling_step_pct = ensure_percent_grid(
            resolve_cycle_percent(params, "samplingStep")
        )

        theta_pct = np.arange(0.0, ring_rotation_pct, sampling_step_pct)
        theta_rad = percent_to_radians(theta_pct)
        theta_deg = percent_to_degrees(theta_pct)
        n = len(theta_pct)
        
        # Initialize arrays
        displacement = np.zeros(n)
        velocity = np.zeros(n)
        acceleration = np.zeros(n)
        
        # Motion law parameters
        stroke_length = params["strokeLengthMm"]  # Full stroke length in mm
        ramp_before_tdc = resolve_cycle_percent(params, "rampBeforeTdc")
        ramp_after_tdc = resolve_cycle_percent(params, "rampAfterTdc")
        dwell_tdc = resolve_cycle_percent(params, "dwellTdc")
        ramp_before_bdc = resolve_cycle_percent(params, "rampBeforeBdc")
        ramp_after_bdc = resolve_cycle_percent(params, "rampAfterBdc")
        dwell_bdc = resolve_cycle_percent(params, "dwellBdc")

        # Calculate phase boundaries (FIXED: use parameterized values)
        constant_velocity_tdc = resolve_cycle_percent(
            params, "constantVelocityTdc", default_percent=degrees_to_percent(30.0)
        )
        constant_velocity_bdc = resolve_cycle_percent(
            params, "constantVelocityBdc", default_percent=degrees_to_percent(40.0)
        )
        
        # CORRECTED: Motion law represents piston stroke from BDC (0) to TDC (stroke_length)
        # Phase 1: Acceleration from BDC to constant velocity
        phase1_end = ramp_before_bdc
        # Phase 2: Constant velocity during upstroke
        phase2_end = phase1_end + constant_velocity_bdc
        # Phase 3: Deceleration to dwell at TDC
        phase3_end = phase2_end + ramp_after_bdc
        # Phase 4: Dwell at TDC (maximum displacement)
        phase4_end = phase3_end + dwell_bdc
        # Phase 5: Acceleration from TDC to constant velocity during downstroke
        phase5_end = phase4_end + ramp_before_tdc
        # Phase 6: Constant velocity during downstroke
        phase6_end = phase5_end + constant_velocity_tdc
        # Phase 7: Deceleration to dwell at BDC
        phase7_end = phase6_end + ramp_after_tdc
        # Phase 8: Dwell at BDC (zero displacement)
        phase8_end = phase7_end + dwell_tdc
        
        # Scale phases to fit requested ring rotation percent
        total_phases = phase8_end
        scale_factor = ring_rotation_pct / total_phases

        phase1_end *= scale_factor
        phase2_end *= scale_factor
        phase3_end *= scale_factor
        phase4_end *= scale_factor
        phase5_end *= scale_factor
        phase6_end *= scale_factor
        phase7_end *= scale_factor
        phase8_end *= scale_factor

        self.logger.info(
            f"Motion law phases (scaled to {ring_rotation_pct:.3f}% of cycle):"
        )
        self.logger.info(
            "  0-{:.3f}%: Acceleration from BDC to constant velocity".format(phase1_end)
        )
        self.logger.info(
            "  {:.3f}-{:.3f}%: Constant velocity during upstroke".format(
                phase1_end, phase2_end
            )
        )
        self.logger.info(
            "  {:.3f}-{:.3f}%: Deceleration to dwell at TDC".format(
                phase2_end, phase3_end
            )
        )
        self.logger.info(
            "  {:.3f}-{:.3f}%: Dwell at TDC (max displacement: {}mm)".format(
                phase3_end, phase4_end, stroke_length
            )
        )
        self.logger.info(
            "  {:.3f}-{:.3f}%: Acceleration from TDC to constant velocity".format(
                phase4_end, phase5_end
            )
        )
        self.logger.info(
            "  {:.3f}-{:.3f}%: Constant velocity during downstroke".format(
                phase5_end, phase6_end
            )
        )
        self.logger.info(
            "  {:.3f}-{:.3f}%: Deceleration to dwell at BDC".format(
                phase6_end, phase7_end
            )
        )
        self.logger.info(
            "  {:.3f}-{:.3f}%: Dwell at BDC (zero displacement)".format(
                phase7_end, phase8_end
            )
        )

        phase1_end_rad = percent_to_radians(phase1_end)
        phase2_end_rad = percent_to_radians(phase2_end)
        phase3_end_rad = percent_to_radians(phase3_end)
        phase4_end_rad = percent_to_radians(phase4_end)
        phase5_end_rad = percent_to_radians(phase5_end)
        phase6_end_rad = percent_to_radians(phase6_end)
        phase7_end_rad = percent_to_radians(phase7_end)
        # phase8_end_rad = percent_to_radians(phase8_end)  # Currently unused
        
        # Generate motion law - CORRECTED to represent proper piston stroke
        for i, (theta_percent, theta_value_rad) in enumerate(zip(theta_pct, theta_rad)):
            if theta_percent <= phase1_end:
                # Phase 1: Acceleration from BDC to constant velocity during upstroke
                if phase1_end_rad == 0.0:
                    beta = 0.0
                else:
                    beta = theta_value_rad / phase1_end_rad
                displacement[i] = stroke_length * 0.5 * (
                    beta - np.sin(2 * np.pi * beta) / (2 * np.pi)
                )
                if phase1_end_rad:
                    velocity[i] = (
                        stroke_length
                        * 0.5
                        * (1 - np.cos(2 * np.pi * beta))
                        / phase1_end_rad
                    )
                    acceleration[i] = (
                        stroke_length
                        * np.pi
                        * np.sin(2 * np.pi * beta)
                        / (phase1_end_rad**2)
                    )
                else:
                    velocity[i] = 0.0
                    acceleration[i] = 0.0

            elif theta_percent <= phase2_end:
                # Phase 2: Constant velocity during upstroke
                displacement[i] = stroke_length * 0.5 + stroke_length * 0.5 * (
                    (theta_percent - phase1_end) / (phase2_end - phase1_end)
                )
                if phase2_end_rad > phase1_end_rad:
                    velocity[i] = (
                        stroke_length
                        * 0.5
                        / (phase2_end_rad - phase1_end_rad)
                    )
                else:
                    velocity[i] = 0.0
                acceleration[i] = 0.0

            elif theta_percent <= phase3_end:
                # Phase 3: Deceleration to dwell at TDC (stay at max displacement)
                beta = (theta_percent - phase2_end) / (phase3_end - phase2_end)
                displacement[i] = stroke_length
                if phase2_end_rad > phase1_end_rad:
                    velocity[i] = (
                        stroke_length
                        * 0.5
                        * (1 - beta)
                        / (phase2_end_rad - phase1_end_rad)
                    )
                else:
                    velocity[i] = 0.0
                if (phase2_end_rad > phase1_end_rad) and (phase3_end_rad > phase2_end_rad):
                    acceleration[i] = (
                        -stroke_length
                        * 0.5
                        / (phase2_end_rad - phase1_end_rad)
                        / (phase3_end_rad - phase2_end_rad)
                    )
                else:
                    acceleration[i] = 0.0

            elif theta_percent <= phase4_end:
                # Phase 4: Dwell at TDC (maximum displacement)
                displacement[i] = stroke_length
                velocity[i] = 0.0
                acceleration[i] = 0.0

            elif theta_percent <= phase5_end:
                # Phase 5: Acceleration from TDC to constant velocity during downstroke
                if phase5_end_rad > phase4_end_rad:
                    beta = (theta_value_rad - phase4_end_rad) / (
                        phase5_end_rad - phase4_end_rad
                    )
                else:
                    beta = 0.0
                displacement[i] = stroke_length * (
                    1 - 0.5 * (beta - np.sin(2 * np.pi * beta) / (2 * np.pi))
                )
                if phase5_end_rad > phase4_end_rad:
                    velocity[i] = (
                        -stroke_length
                        * 0.5
                        * (1 - np.cos(2 * np.pi * beta))
                        / (phase5_end_rad - phase4_end_rad)
                    )
                    acceleration[i] = (
                        -stroke_length
                        * np.pi
                        * np.sin(2 * np.pi * beta)
                        / (phase5_end_rad - phase4_end_rad) ** 2
                    )
                else:
                    velocity[i] = 0.0
                    acceleration[i] = 0.0

            elif theta_percent <= phase6_end:
                # Phase 6: Constant velocity during downstroke
                displacement[i] = stroke_length * 0.5 - stroke_length * 0.5 * (
                    (theta_percent - phase5_end) / (phase6_end - phase5_end)
                )
                if phase6_end_rad > phase5_end_rad:
                    velocity[i] = (
                        -stroke_length
                        * 0.5
                        / (phase6_end_rad - phase5_end_rad)
                    )
                else:
                    velocity[i] = 0.0
                acceleration[i] = 0.0

            elif theta_percent <= phase7_end:
                # Phase 7: Deceleration to dwell at BDC
                beta = (theta_percent - phase6_end) / (phase7_end - phase6_end)
                displacement[i] = 0.0
                if phase6_end_rad > phase5_end_rad:
                    velocity[i] = (
                        -stroke_length
                        * 0.5
                        * (1 - beta)
                        / (phase6_end_rad - phase5_end_rad)
                    )
                else:
                    velocity[i] = 0.0
                if (phase6_end_rad > phase5_end_rad) and (phase7_end_rad > phase6_end_rad):
                    acceleration[i] = (
                        stroke_length
                        * 0.5
                        / (phase6_end_rad - phase5_end_rad)
                        / (phase7_end_rad - phase6_end_rad)
                    )
                else:
                    acceleration[i] = 0.0

            elif theta_percent <= phase8_end:
                # Phase 8: Dwell at BDC (zero displacement)
                displacement[i] = 0.0
                velocity[i] = 0.0
                acceleration[i] = 0.0

            else:
                # Beyond defined phases - should not happen
                displacement[i] = 0.0
                velocity[i] = 0.0
                acceleration[i] = 0.0
        
        return theta_deg, displacement, velocity, acceleration
    
    def generate_gear_profiles(self, theta_deg: np.ndarray, displacement: np.ndarray, 
                             params: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Generate UNIFIED gear profiles using displacement and connecting rod length.
        
        Extracted from GearProfileGenerator.generate_gear_profiles()
        
        Args:
            theta_deg: Ring rotation angles (degrees)
            displacement: Piston displacement (mm)
            params: Gear generation parameters dictionary
            
        Returns:
            Dictionary containing gear profile data
        """
        self.logger.info("Generating UNIFIED gear profiles using displacement and connecting rod length...")

        n = len(theta_deg)
        step_percent = ensure_percent_grid(
            resolve_cycle_percent(params, "samplingStep")
        )
        step_deg = percent_to_degrees(step_percent)
        step_rad = percent_to_radians(step_percent)

        # UNIFIED CONSTRAINT SYSTEM WITH DISPLACEMENT AND CONNECTING ROD
        # ===============================================================
        # For planetary gearset: planets must be tangent to BOTH sun and ring
        # UNIFIED CONSTRAINT: contact_point_ring_planet = contact_point_sun_planet
        # This ensures: R_ring(θ) - R_planet(θ) = R_sun(θ) + R_planet(θ)
        # Therefore: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
        # 
        # CRITICAL: Use displacement + connecting rod length to determine system extension
        # The gearset must be sized to accommodate the full stroke + connecting rod extension

        # Step 1: Extract unified inputs
        stroke_length = params.get("strokeLengthMm", 10.0)
        rod_length = params.get("rodLength", 80.0)
        journal_radius = params.get("journalRadius", 5.0)
        
        # Step 2: Calculate system extension requirements
        # Maximum extension occurs when connecting rod is fully extended
        # This happens when piston is at TDC (maximum displacement)
        max_displacement = np.max(displacement)
        min_displacement = np.min(displacement)
        
        # Connecting rod extension varies with displacement
        # At TDC: rod extension = rod_length + max_displacement
        # At BDC: rod extension = rod_length + min_displacement
        rod_extension = rod_length + displacement
        
        # Maximum system extension (at TDC)
        max_rod_extension = np.max(rod_extension)
        
        # Step 3: Size gearset to accommodate system extension
        # The gearset must be large enough to handle the maximum rod extension
        # This ensures the stroke is achievable with the generated gearset
        
        # Base gearset sizing based on system requirements
        # Sun gear center is at the connecting rod journal (differentiated from gear center)
        sun_center_radius = journal_radius  # Sun gear center at journal radius
        
        # Planet radius must accommodate the connecting rod extension
        # Planet radius varies with displacement to match rod extension (FIXED: parameterized)
        planet_radius_base_factor = params.get("planetRadiusBaseFactor", 0.15)
        planet_radius_base = max_rod_extension * planet_radius_base_factor
        
        # CORRECTED: Variation should be proportional to stroke length, not just rod extension
        # For significant asymmetry, variation should be a substantial fraction of the stroke
        stroke_based_variation_factor = params.get("strokeBasedVariationFactor", 0.3)  # 30% of stroke
        planet_radius_variation = stroke_length * stroke_based_variation_factor
        
        # Normalize displacement to drive planet radius variation
        displacement_range = max_displacement - min_displacement
        if displacement_range > 0:
            displacement_normalized = (displacement - min_displacement) / displacement_range
        else:
            displacement_normalized = np.zeros_like(displacement)
        
        # Planet radius varies with displacement (SINGLE reference for all profiles) (FIXED: parameterized)
        planet_radius_min_factor = params.get("planetRadiusMinFactor", 0.8)
        r_planet = planet_radius_base + planet_radius_variation * displacement_normalized
        r_planet = np.maximum(r_planet, planet_radius_base * planet_radius_min_factor)  # Ensure minimum radius

        # Step 4: UNIFIED CONTACT POINT CONSTRAINT SYSTEM
        # ===============================================
        # For each angle θ, enforce contact point constraint:
        # contact_point_ring_planet(θ) = contact_point_sun_planet(θ)
        # This automatically ensures no overlap and proper meshing
        
        # Sun gear center is at the connecting rod journal (differentiated from gear center)
        # Sun gear radius must accommodate the connecting rod extension (FIXED: parameterized)
        sun_radius_base_factor = params.get("sunRadiusBaseFactor", 0.1)
        sun_radius_base = max_rod_extension * sun_radius_base_factor
        
        # CORRECTED: Sun gear variation should also be proportional to stroke length
        # Sun gear variation should be complementary to planet variation for proper meshing
        sun_radius_variation = stroke_length * stroke_based_variation_factor * 0.5  # 50% of planet variation
        
        # Sun gear radius varies with displacement (complementary to planet) (FIXED: parameterized)
        sun_radius_min_factor = params.get("sunRadiusMinFactor", 0.9)
        r_sun = sun_radius_base + sun_radius_variation * (1.0 - displacement_normalized)
        r_sun = np.maximum(r_sun, sun_radius_base * sun_radius_min_factor)  # Ensure minimum radius
        
        # UNIFIED CONSTRAINT: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
        # This is derived from: contact_point_ring_planet = contact_point_sun_planet
        r_ring_inner = r_sun + 2.0 * r_planet
        
        # Step 5: Validate gearset sizing for stroke achievability
        # The gearset must be large enough to accommodate the full stroke
        min_gearset_radius = np.min(r_ring_inner)
        max_gearset_radius = np.max(r_ring_inner)
        
        # Check if gearset can accommodate the stroke
        gearset_capacity = max_gearset_radius - min_gearset_radius
        stroke_achievable_factor = params.get("strokeAchievableFactor", 0.8)  # FIXED: parameterized
        stroke_achievable = gearset_capacity >= stroke_length * stroke_achievable_factor
        
        if not stroke_achievable:
            self.logger.warning(f"Gearset may be too small for stroke: capacity={gearset_capacity:.1f}mm, stroke={stroke_length:.1f}mm")
            # Scale up gearset to accommodate stroke (FIXED: use parameterized factor)
            scale_factor = (stroke_length * stroke_achievable_factor) / gearset_capacity
            r_planet *= scale_factor
            r_sun *= scale_factor
            r_ring_inner = r_sun + 2.0 * r_planet
            self.logger.info(f"Scaled gearset by factor {scale_factor:.2f} to accommodate stroke")
        
        self.logger.info("Gearset sizing for stroke achievability:")
        self.logger.info(f"  Stroke length: {stroke_length:.1f} mm")
        self.logger.info(f"  Max rod extension: {max_rod_extension:.1f} mm")
        self.logger.info(f"  Gearset capacity: {gearset_capacity:.1f} mm")
        self.logger.info(f"  Stroke achievable: {stroke_achievable}")
        self.logger.info(f"  Sun center radius: {sun_center_radius:.1f} mm (journal)")
        self.logger.info(f"  Sun gear radius: {np.min(r_sun):.1f} - {np.max(r_sun):.1f} mm")
        self.logger.info(f"  Planet radius: {np.min(r_planet):.1f} - {np.max(r_planet):.1f} mm")
        self.logger.info(f"  Ring inner radius: {np.min(r_ring_inner):.1f} - {np.max(r_ring_inner):.1f} mm")

        # Step 4: Extend 180° motion law to full 360° ring profile
        # For planetary gearset, the motion law spans 180° ring rotation
        # We need to extend this to 360° for the complete ring gear profile
        # Only extend if explicitly requested or if we're generating full cycle profiles
        if n < 360 and params.get("enableFullCycle", False):  # If we only have 180° of data and full cycle is requested
            # Extend the profiles to 360° by repeating the 180° pattern
            theta_deg_full = np.arange(0, 360, step_deg)
            n_full = len(theta_deg_full)

            # Helper to tile arrays to target length
            def _tile_to_length(arr: np.ndarray, length: int) -> np.ndarray:
                reps = int(np.ceil(length / arr.size)) if arr.size > 0 else 1
                return np.tile(arr, reps)[:length]

            r_planet_full = _tile_to_length(r_planet, n_full)
            r_sun_full = _tile_to_length(r_sun, n_full)
            r_ring_inner_full = _tile_to_length(r_ring_inner, n_full)

            # Update variables
            theta_deg = theta_deg_full
            r_planet = r_planet_full
            r_sun = r_sun_full
            r_ring_inner = r_ring_inner_full
            n = n_full

        # Step 5: Optional symmetry prior (disabled by default). Do not force 2:1.
        if params.get("enableSymmetryPrior", False):
            symmetry_weight = float(params.get("symmetryWeight", 0.5))
            for i in range(n):
                theta = theta_deg[i]
                sym_theta = theta + 180.0 if theta < 180.0 else theta - 180.0
                sym_idx = int(sym_theta / step_deg) % n
                avg_planet = (r_planet[i] + r_planet[sym_idx]) / 2.0
                avg_sun = (r_sun[i] + r_sun[sym_idx]) / 2.0
                # Blend towards symmetry without enforcing it strictly
                r_planet[i] = (1.0 - symmetry_weight) * r_planet[i] + symmetry_weight * avg_planet
                r_planet[sym_idx] = (1.0 - symmetry_weight) * r_planet[sym_idx] + symmetry_weight * avg_planet
                r_sun[i] = (1.0 - symmetry_weight) * r_sun[i] + symmetry_weight * avg_sun
                r_sun[sym_idx] = (1.0 - symmetry_weight) * r_sun[sym_idx] + symmetry_weight * avg_sun
                r_ring_inner[i] = r_sun[i] + 2.0 * r_planet[i]
                r_ring_inner[sym_idx] = r_sun[sym_idx] + 2.0 * r_planet[sym_idx]

        # Step 6: Compute φ(θ) from instantaneous ratio r(θ) if available
        if "instantaneous_ratio" in params:
            r_inst = np.asarray(params["instantaneous_ratio"]).astype(float)
            if r_inst.shape[0] != n:
                # Try to tile/crop to match length
                reps = int(np.ceil(n / r_inst.size))
                r_inst = np.tile(r_inst, reps)[:n]
            phi_of_theta_deg = np.cumsum(r_inst) * step_deg
        else:
            # Fallback: fixed mapping φ = gearRatio * θ
            gear_ratio = params.get("gearRatio", 2.0)
            phi_of_theta_deg = gear_ratio * theta_deg

        # Step 7: Arc-length conjugacy for proper tooth meshing
        # Each tooth must mesh with the same corresponding tooth throughout the cycle
        # CRITICAL: For 2:1 gear ratio, planet arc-length should be 2x ring arc-length
        def wrap_idx(i):
            return i % n

        # Calculate derivatives for arc-length calculation
        dr_planet_dtheta = np.zeros(n)
        dr_ring_dtheta = np.zeros(n)  # Ring derivative with respect to ring angle θ
        dr_sun_dtheta = np.zeros(n)   # Sun derivative with respect to ring angle θ

        for i in range(n):
            ip = wrap_idx(i + 1)
            im = wrap_idx(i - 1)
            dr_planet_dtheta[i] = (r_planet[ip] - r_planet[im]) / (2.0 * step_rad)
            dr_ring_dtheta[i] = (r_ring_inner[ip] - r_ring_inner[im]) / (2.0 * step_rad)
            dr_sun_dtheta[i] = (r_sun[ip] - r_sun[im]) / (2.0 * step_rad)

        # Calculate arc-lengths
        ds_planet = np.sqrt(r_planet**2 + dr_planet_dtheta**2) * step_rad
        ds_ring = np.sqrt(r_ring_inner**2 + dr_ring_dtheta**2) * step_rad
        ds_sun = np.sqrt(r_sun**2 + dr_sun_dtheta**2) * step_rad

        s_planet = np.cumsum(ds_planet)
        s_ring = np.cumsum(ds_ring)
        s_sun = np.cumsum(ds_sun)

        # Step 8: Verify global mapping consistency (diagnostic only)
        # actual_planet_angle_range = float(np.max(phi_of_theta_deg) - np.min(phi_of_theta_deg))  # TODO: Use for validation
        expected_planet_angle_range = float(2.0 * 360.0) if np.max(theta_deg) >= 360.0 else float(2.0 * np.max(theta_deg))
        self.logger.info("φ(θ) mapping diagnostic:")
        self.logger.info(f"  Ring angle range: {np.min(theta_deg):.1f}° - {np.max(theta_deg):.1f}°")
        self.logger.info(f"  Planet angle range: {np.min(phi_of_theta_deg):.1f}° - {np.max(phi_of_theta_deg):.1f}°")
        self.logger.info(f"  Expected planet angle range (~2× ring span): 0° - {expected_planet_angle_range:.1f}°")
        
        # The arc-length ratio should be close to 1:1 for proper tooth meshing
        # Both gears complete their respective cycles (ring: 180°, planet: 360°)
        arc_length_ratio = s_planet[-1] / s_ring[-1] if s_ring[-1] > 0 else 0
        self.logger.info(f"Arc-length ratio: {arc_length_ratio:.3f} (should be ~1.0 for proper meshing)")
        
        if abs(arc_length_ratio - 1.0) > 0.1:
            self.logger.warning(f"Arc-length ratio deviates from 1.0: {arc_length_ratio:.3f}")
            self.logger.info("This may indicate issues with profile generation or tooth synchronization")
        
        # Step 9: Final clearance check and validation
        clearance_buffer = params.get("interferenceBuffer", 0.5)
        clearance = r_ring_inner - r_planet - clearance_buffer
        min_clearance = np.min(clearance)

        if min_clearance < 0:
            self.logger.warning(f"Negative clearance detected: {min_clearance:.3f} mm")
            # Adjust profiles to ensure positive clearance while maintaining complementary relationship (FIXED: parameterized)
            clearance_safety_margin = params.get("clearanceSafetyMargin", 0.1)  # mm safety margin
            adjustment = -min_clearance + clearance_safety_margin
            
            # Adjust sun and ring together to maintain UNIFIED CONSTRAINT (FIXED: parameterized)
            adjustment_split_factor = params.get("adjustmentSplitFactor", 0.5)  # How to split adjustment
            r_sun += adjustment * adjustment_split_factor
            r_ring_inner += adjustment * adjustment_split_factor
            
            # Re-enforce UNIFIED CONSTRAINT: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
            r_ring_inner = r_sun + 2.0 * r_planet
            
            # Re-enforce symmetry after clearance adjustment
            for i in range(n):
                theta = theta_deg[i]
                # For 0-180° symmetry: if theta is in [0,180), symmetric point is theta+180
                # if theta is in [180,360), symmetric point is theta-180
                if theta < 180.0:
                    sym_theta = theta + 180.0
                else:
                    sym_theta = theta - 180.0
                sym_idx = int(sym_theta / step_deg) % n
                
                # Maintain UNIFIED CONSTRAINT after symmetry enforcement
                avg_planet = (r_planet[i] + r_planet[sym_idx]) / 2.0
                avg_sun = (r_sun[i] + r_sun[sym_idx]) / 2.0
                # UNIFIED CONSTRAINT: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
                avg_ring = avg_sun + 2.0 * avg_planet
                
                r_planet[i] = avg_planet
                r_planet[sym_idx] = avg_planet
                r_sun[i] = avg_sun
                r_sun[sym_idx] = avg_sun
                r_ring_inner[i] = avg_ring
                r_ring_inner[sym_idx] = avg_ring

            clearance = r_ring_inner - r_planet - params["interferenceBuffer"]

        # Step 10: Calculate ring outer radius based on inner radius + thickness
        ring_thickness = params.get("ringThickness", 5.0)
        r_ring_outer = r_ring_inner + ring_thickness

        # Step 11: Final validation of UNIFIED CONSTRAINT SYSTEM
        self.logger.info("UNIFIED CONSTRAINT SYSTEM VALIDATION:")
        self.logger.info(f"  Sun radius range: {np.min(r_sun):.2f} - {np.max(r_sun):.2f} mm")
        self.logger.info(f"  Planet radius range: {np.min(r_planet):.2f} - {np.max(r_planet):.2f} mm")
        self.logger.info(f"  Ring inner radius range: {np.min(r_ring_inner):.2f} - {np.max(r_ring_inner):.2f} mm")
        self.logger.info(f"  UNIFIED CONSTRAINT (R_ring = R_sun + 2*R_planet): {np.allclose(r_ring_inner, r_sun + 2.0 * r_planet, atol=0.01)}")
        self.logger.info(f"  Contact point constraint satisfied: {np.allclose(r_ring_inner - r_planet, r_sun + r_planet, atol=0.01)}")
        # Report effective instantaneous/global ratio for diagnostics
        ring_span = float(np.max(theta_deg) - np.min(theta_deg)) if n > 0 else 0.0
        planet_span = float(np.max(phi_of_theta_deg) - np.min(phi_of_theta_deg)) if n > 0 else 0.0
        effective_ratio = (planet_span / ring_span) if ring_span > 0 else 0.0
        self.logger.info(f"  φ(θ) effective global ratio: {effective_ratio:.3f}:1 (Planet:Ring)")
        self.logger.info(f"  Arc-length ratio: {s_planet[-1]/s_ring[-1]:.3f} (should be ~1.0)")
        self.logger.info(f"  Clearance range: {np.min(clearance):.2f} - {np.max(clearance):.2f} mm")

        return {
            "theta_deg": theta_deg,
            "r_planet": r_planet,  # Non-circular planet profile
            "r_sun": r_sun,  # Sun gear profile (circular or non-circular)
            "r_ring_inner": r_ring_inner,  # Non-circular ring inner profile
            "r_ring_outer": r_ring_outer,  # Ring outer profile (inner + thickness)
            "s_planet": s_planet,
            "s_ring": s_ring,
            "s_sun": s_sun,
            "phi_of_theta_deg": phi_of_theta_deg,
            "clearance": clearance,
            "gear_ratio": effective_ratio
        }
    
    def validate_gearset_constraints(self, gear_profiles: Dict[str, np.ndarray], 
                                   params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate gearset constraints.
        
        Extracted from gear profile generation validation logic.
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            params: Gear generation parameters dictionary
            
        Returns:
            Dictionary containing validation results
        """
        r_sun = gear_profiles["r_sun"]
        r_planet = gear_profiles["r_planet"]
        r_ring_inner = gear_profiles["r_ring_inner"]
        gear_profiles["r_ring_outer"]
        clearance = gear_profiles["clearance"]
        
        # Check UNIFIED CONSTRAINT: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
        unified_constraint = np.allclose(r_ring_inner, r_sun + 2.0 * r_planet, atol=0.01)
        
        # Check contact point constraint: R_ring - R_planet = R_sun + R_planet
        contact_point_constraint = np.allclose(r_ring_inner - r_planet, r_sun + r_planet, atol=0.01)
        
        # Check positive clearance
        positive_clearance = np.all(clearance > 0)
        
        # Check stroke achievability
        stroke_length = params["strokeLengthMm"]
        gearset_capacity = np.max(r_ring_inner) - np.min(r_ring_inner)
        stroke_achievable_factor = params.get("strokeAchievableFactor", 0.8)
        stroke_achievable = gearset_capacity >= stroke_length * stroke_achievable_factor
        
        # Log validation details for debugging
        self.logger.debug("Validation details:")
        self.logger.debug(f"  Unified constraint: {unified_constraint}")
        self.logger.debug(f"  Contact point constraint: {contact_point_constraint}")
        self.logger.debug(f"  Positive clearance: {positive_clearance}")
        self.logger.debug(f"  Stroke achievable: {stroke_achievable} (capacity: {gearset_capacity:.1f}mm, required: {stroke_length * stroke_achievable_factor:.1f}mm)")
        
        # All constraints must be satisfied
        all_constraints_satisfied = (
            unified_constraint and 
            contact_point_constraint and 
            positive_clearance and 
            stroke_achievable
        )
        
        return {
            "passed": bool(all_constraints_satisfied),
            "constraints": {
                "unified_constraint": bool(unified_constraint),
                "contact_point_constraint": bool(contact_point_constraint),
                "positive_clearance": bool(positive_clearance),
                "stroke_achievable": bool(stroke_achievable)
            },
            "metrics": {
                "gearset_capacity": gearset_capacity,
                "stroke_length": stroke_length,
                "min_clearance": np.min(clearance),
                "max_clearance": np.max(clearance)
            }
        }
    
    def generate_planet_kinematics(self, gear_profiles: Dict[str, np.ndarray], 
                                 params: Dict[str, Any]) -> List[Dict[str, np.ndarray]]:
        """
        Generate planet kinematics for CORRECT planetary gearset with COM and journal markers.
        
        Extracted from GearProfileGenerator.generate_planet_kinematics()
        
        Args:
            gear_profiles: Dictionary containing gear profile data
            params: Gear generation parameters dictionary
            
        Returns:
            List of planet kinematics dictionaries
        """
        self.logger.info("Generating planet kinematics for CORRECT planetary gearset with COM and journal markers...")
        
        r_planet = gear_profiles["r_planet"]
        r_ring_inner = gear_profiles["r_ring_inner"]
        r_sun = gear_profiles["r_sun"]
        theta_deg = gear_profiles["theta_deg"]
        gear_profiles["phi_of_theta_deg"]
        
        # Extract sun center radius (connecting rod journal)
        sun_center_radius = params.get("journalRadius", 5.0)  # 5.0 mm default
        
        planet_count = int(params.get("planetCount", 2))
        carrier_offset_deg = percent_to_degrees(
            resolve_cycle_percent(params, "carrierOffset", default_percent=degrees_to_percent(180.0))
        )
        
        planets = []
        
        for i in range(planet_count):
            # Planet angle relative to carrier
            planet_angle = i * carrier_offset_deg
            
            # Planet center positions (tangent to both sun and ring)
            # CORRECTED: Planet center distance = (r_ring_inner - r_sun) / 2
            # This ensures the planet is tangent to both sun and ring
            center_distance = (r_ring_inner - r_sun) / 2.0
            center_x = center_distance * np.cos(np.deg2rad(planet_angle))
            center_y = center_distance * np.sin(np.deg2rad(planet_angle))
            
            # Planet spin angle (2:1 gear ratio)
            # Planet rotates 2x faster than ring: ψ = 2α (mod 360°)
            alpha_deg = theta_deg  # Ring rotation angle
            psi_deg = (2.0 * alpha_deg) % 360.0  # Planet spin angle
            
            # Calculate planet COM (Center of Mass) for uniform density
            # For a non-circular planet gear, COM is at the geometric center
            # which is the average of the profile radii
            planet_com_radius = np.mean(r_planet)  # Average radius for COM calculation
            
            # Calculate journal position relative to COM
            # The journal is where the connecting rod connects to the planet
            # For now, we'll place it at a fixed offset from the COM
            # This should be calculated based on the actual connecting rod geometry
            journal_offset_radius = params.get("journalOffsetRadius", 5.0)  # mm offset from COM
            journal_angle_offset_deg = percent_to_degrees(
                resolve_cycle_percent(
                    params, "journalAngleOffset", default_percent=degrees_to_percent(0.0)
                )
            )  # offset from COM
            
            # Journal position relative to planet COM
            journal_angle_rad = np.deg2rad(psi_deg + journal_angle_offset_deg)
            journal_x = center_x + journal_offset_radius * np.cos(journal_angle_rad)
            journal_y = center_y + journal_offset_radius * np.sin(journal_angle_rad)
            
            planets.append({
                "planet_angle": planet_angle,
                "center_x": center_x,
                "center_y": center_y,
                "planet_radius": r_planet,
                "ring_inner_radius": r_ring_inner,
                "sun_radius": r_sun,
                "sun_center_radius": sun_center_radius,  # Connecting rod journal
                "psi_deg": psi_deg,
                "alpha_deg": alpha_deg,
                # New COM and journal data
                "planet_com_radius": planet_com_radius,
                "journal_x": journal_x,
                "journal_y": journal_y,
                "journal_offset_radius": journal_offset_radius,
                "journal_angle_offset_deg": journal_angle_offset_deg,
                "journal_angle_offset_percent": degrees_to_percent(journal_angle_offset_deg),
            })
        
        return planets
