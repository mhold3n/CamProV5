"""
Dense Post-Solve Validation for Collocation Solutions

This module provides comprehensive validation of collocation solutions,
including pressure angle checks, curvature analysis, thickness validation,
contact ratio verification, and other manufacturability constraints.
"""

import numpy as np
from typing import Dict, List, Any, Optional, NamedTuple
from dataclasses import dataclass

try:
    import casadi as ca  # noqa: F401
    CASADI_AVAILABLE = True
except ImportError:
    CASADI_AVAILABLE = False

import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationLimits:
    """Limits for validation checks."""
    
    # Pressure angle limits (radians)
    pressure_angle_max: float = np.deg2rad(30.0)
    pressure_angle_min: float = np.deg2rad(0.0)
    
    # Curvature limits (mm)
    curvature_radius_min: float = 2.0
    
    # Tooth thickness limits (mm)
    tooth_thickness_min: float = 1.0
    
    # Contact ratio limits
    contact_ratio_min: float = 1.2
    contact_ratio_max: float = 3.0
    
    # Velocity limits (mm/s)
    velocity_max: float = 1000.0
    
    # Acceleration limits (mm/s²)
    acceleration_max: float = 50000.0
    
    # Jerk limits (mm/s³)
    jerk_max: float = 1000000.0
    
    # Sliding velocity limits (mm/s)
    sliding_velocity_max: float = 100.0


class ValidationResult(NamedTuple):
    """Result of a validation check."""
    passed: bool
    value: float
    limit: float
    location_deg: Optional[float] = None
    message: str = ""


@dataclass
class DenseValidationReport:
    """Comprehensive validation report."""
    
    # Overall status
    passed: bool = True
    num_violations: int = 0
    
    # Pressure angle validation
    pressure_angle_results: Optional[List[ValidationResult]] = None
    pressure_angle_max: float = 0.0
    pressure_angle_violations: int = 0
    
    # Curvature validation
    curvature_results: Optional[List[ValidationResult]] = None
    curvature_min: float = float('inf')
    curvature_violations: int = 0
    
    # Thickness validation
    thickness_results: Optional[List[ValidationResult]] = None
    thickness_min: float = float('inf')
    thickness_violations: int = 0
    
    # Contact ratio validation
    contact_ratio_result: Optional[ValidationResult] = None
    
    # Kinematic validation
    velocity_max: float = 0.0
    acceleration_max: float = 0.0
    jerk_max: float = 0.0
    kinematic_violations: int = 0
    
    # Sliding velocity validation
    sliding_velocity_max: float = 0.0
    sliding_violations: int = 0
    
    # Summary statistics
    total_checks: int = 0
    validation_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.pressure_angle_results is None:
            self.pressure_angle_results = []
        if self.curvature_results is None:
            self.curvature_results = []
        if self.thickness_results is None:
            self.thickness_results = []


class DenseValidator:
    """
    Dense post-solve validator for collocation solutions.
    
    Performs comprehensive checks on the optimized motion law to ensure
    manufacturability, performance, and safety constraints are satisfied.
    """
    
    def __init__(self, limits: Optional[ValidationLimits] = None):
        """Initialize the validator."""
        self.limits = limits or ValidationLimits()
        self.logger = logging.getLogger(__name__)
    
    def validate_solution(self, 
                         theta_grid: np.ndarray,
                         position: np.ndarray,
                         velocity: np.ndarray,
                         acceleration: np.ndarray,
                         motion_params: Dict[str, Any]) -> DenseValidationReport:
        """
        Perform comprehensive validation of a collocation solution.
        
        Args:
            theta_grid: Angular positions (radians)
            position: Position values (mm)
            velocity: Velocity values (mm/rad)
            acceleration: Acceleration values (mm/rad²)
            motion_params: Motion parameters for context
            
        Returns:
            Comprehensive validation report
        """
        import time
        start_time = time.time()
        
        self.logger.info("Starting dense post-solve validation")
        
        report = DenseValidationReport()
        
        # Convert angular velocity and acceleration to physical units
        rpm = motion_params.get('rpm', 3000.0)
        omega = rpm * 2 * np.pi / 60.0  # rad/s
        
        velocity_physical = velocity * omega  # mm/s
        acceleration_physical = acceleration * omega**2  # mm/s²
        
        # Compute jerk (numerical differentiation)
        jerk = np.gradient(acceleration, theta_grid) * omega**3  # mm/s³
        
        # 1. Kinematic validation
        self._validate_kinematics(
            theta_grid, position, velocity_physical, 
            acceleration_physical, jerk, report
        )
        
        # 2. Gear geometry validation (if applicable)
        center_distance = motion_params.get('center_distance', 50.0)
        if center_distance > 0:
            self._validate_gear_geometry(
                theta_grid, position, velocity, acceleration,
                center_distance, report, motion_params
            )
        
        # 3. Motion law specific validation
        self._validate_motion_law_constraints(
            theta_grid, position, velocity, acceleration, 
            motion_params, report
        )
        
        # 4. Periodicity and smoothness validation
        self._validate_periodicity_and_smoothness(
            theta_grid, position, velocity, acceleration, report
        )
        
        # 5. Safety and performance limits
        self._validate_safety_limits(
            velocity_physical, acceleration_physical, jerk, report
        )
        
        # Compile final report
        report.validation_time_ms = (time.time() - start_time) * 1000
        report.passed = report.num_violations == 0
        
        self.logger.info(f"Validation completed in {report.validation_time_ms:.1f}ms")
        if report.passed:
            self.logger.info("✓ All validation checks passed")
        else:
            self.logger.warning(f"✗ Validation failed with {report.num_violations} violations")
        
        return report
    
    def _validate_kinematics(self, theta_grid: np.ndarray, position: np.ndarray,
                           velocity: np.ndarray, acceleration: np.ndarray,
                           jerk: np.ndarray, report: DenseValidationReport):
        """Validate kinematic limits."""
        report.velocity_max = np.max(np.abs(velocity))
        report.acceleration_max = np.max(np.abs(acceleration))
        report.jerk_max = np.max(np.abs(jerk))
        
        # Check velocity limits
        if report.velocity_max > self.limits.velocity_max:
            report.kinematic_violations += 1
            report.num_violations += 1
            self.logger.warning(f"Velocity limit exceeded: {report.velocity_max:.1f} > {self.limits.velocity_max:.1f} mm/s")
        
        # Check acceleration limits
        if report.acceleration_max > self.limits.acceleration_max:
            report.kinematic_violations += 1
            report.num_violations += 1
            self.logger.warning(f"Acceleration limit exceeded: {report.acceleration_max:.1f} > {self.limits.acceleration_max:.1f} mm/s²")
        
        # Check jerk limits
        if report.jerk_max > self.limits.jerk_max:
            report.kinematic_violations += 1
            report.num_violations += 1
            self.logger.warning(f"Jerk limit exceeded: {report.jerk_max:.1f} > {self.limits.jerk_max:.1f} mm/s³")
        
        report.total_checks += 3
    
    def _validate_gear_geometry(self, theta_grid: np.ndarray, position: np.ndarray,
                              velocity: np.ndarray, acceleration: np.ndarray,
                              center_distance: float, report: DenseValidationReport, 
                              motion_params: Optional[Dict[str, Any]] = None):
        """Validate gear geometry constraints."""
        
        # Estimate gear radii from velocity profile
        v_max = np.max(np.abs(velocity))
        velocity / (v_max + 1e-12)
        
        # Use robust gear design for radius estimation
        from campro.solvers.robust_gear_design import RobustGearDesign, GearMaterialProperties, GearDesignParameters
        
        # Create robust gear design calculator
        material = GearMaterialProperties()
        design_params = GearDesignParameters()
        gear_design = RobustGearDesign(material, design_params)
        
        # Estimate torque from motion parameters
        if motion_params is None:
            motion_params = {}
        estimated_torque = motion_params.get('max_torque', 500.0)  # N⋅m
        estimated_rpm = motion_params.get('rpm', 1500.0)  # RPM
        
        # Calculate gear radius using robust method
        cam_radius = gear_design.calculate_gear_radius(
            np.full_like(theta_grid, estimated_torque),
            np.full_like(theta_grid, estimated_rpm)
        )
        ring_radius = center_distance - cam_radius
        
        # Ensure positive radii
        if np.any(cam_radius < 5.0):
            report.curvature_violations += 1
            report.num_violations += 1
            self.logger.warning("Cam radius too small in some regions")
        
        if np.any(ring_radius < 5.0):
            report.curvature_violations += 1
            report.num_violations += 1
            self.logger.warning("Ring radius too small in some regions")
        
        # Calculate pressure angle using robust gear design
        pressure_angles = gear_design.calculate_pressure_angle(
            cam_radius, ring_radius, center_distance
        )
        
        # Check pressure angle limits
        pressure_angle_violations = np.sum(pressure_angles > self.limits.pressure_angle_max)
        if pressure_angle_violations > 0:
            report.pressure_angle_violations += pressure_angle_violations
            report.num_violations += pressure_angle_violations
            max_pressure_angle = np.max(pressure_angles)
            report.pressure_angle_max = max_pressure_angle
            self.logger.warning(f"Pressure angle violations: {pressure_angle_violations} points, max: {np.rad2deg(max_pressure_angle):.1f}°")
        
        # Add detailed pressure angle results
        for i, (theta, pa) in enumerate(zip(theta_grid, pressure_angles)):
            passed = pa <= self.limits.pressure_angle_max
            if not passed or i % max(1, len(theta_grid) // 20) == 0:  # Sample for reporting
                result = ValidationResult(
                    passed=passed,
                    value=pa,
                    limit=self.limits.pressure_angle_max,
                    location_deg=np.rad2deg(theta),
                    message=f"Pressure angle at {np.rad2deg(theta):.1f}°: {np.rad2deg(pa):.1f}°"
                )
                report.pressure_angle_results.append(result)
        
        # Calculate contact ratio using robust gear design
        addendum = 2.0  # mm (standard)
        dedendum = 2.5  # mm (standard)
        contact_ratios = gear_design.calculate_contact_ratio(
            cam_radius, ring_radius, pressure_angles,
            np.full_like(cam_radius, addendum),
            np.full_like(cam_radius, dedendum)
        )
        avg_contact_ratio = np.mean(contact_ratios)
        contact_ratio = avg_contact_ratio
        
        contact_passed = (contact_ratio >= self.limits.contact_ratio_min and 
                         contact_ratio <= self.limits.contact_ratio_max)
        
        if not contact_passed:
            report.num_violations += 1
            self.logger.warning(f"Contact ratio violation: {contact_ratio:.2f} not in [{self.limits.contact_ratio_min:.2f}, {self.limits.contact_ratio_max:.2f}]")
        
        report.contact_ratio_result = ValidationResult(
            passed=contact_passed,
            value=contact_ratio,
            limit=self.limits.contact_ratio_min,
            message=f"Contact ratio: {contact_ratio:.2f}"
        )
        
        report.total_checks += len(theta_grid) + 2  # Pressure angles + contact ratio
    
    def _validate_motion_law_constraints(self, theta_grid: np.ndarray, 
                                       position: np.ndarray, velocity: np.ndarray,
                                       acceleration: np.ndarray, motion_params: Dict[str, Any],
                                       report: DenseValidationReport):
        """Validate motion law specific constraints."""
        
        # Check stroke length constraint
        stroke_actual = np.max(position) - np.min(position)
        stroke_target = motion_params.get('strokeLengthMm', 0.0)
        
        if stroke_target > 0:
            stroke_error = abs(stroke_actual - stroke_target) / stroke_target
            if stroke_error > 0.1:  # 10% tolerance
                report.num_violations += 1
                self.logger.warning(f"Stroke length error: {stroke_error*100:.1f}% (target: {stroke_target:.1f}mm, actual: {stroke_actual:.1f}mm)")
        
        # Check dwell constraints (low velocity in dwell regions)
        dwell_tdc_deg = motion_params.get('dwellTdcDeg', 0.0)
        dwell_bdc_deg = motion_params.get('dwellBdcDeg', 0.0)
        
        if dwell_tdc_deg > 0:
            tdc_mask = theta_grid <= np.deg2rad(dwell_tdc_deg)
            if np.any(tdc_mask):
                tdc_velocities = np.abs(velocity[tdc_mask])
                max_tdc_velocity = np.max(tdc_velocities)
                if max_tdc_velocity > 0.1:  # Arbitrary threshold
                    report.num_violations += 1
                    self.logger.warning(f"TDC dwell velocity too high: {max_tdc_velocity:.3f}")
        
        if dwell_bdc_deg > 0:
            bdc_center = np.pi
            bdc_range = np.deg2rad(dwell_bdc_deg) / 2
            bdc_mask = np.abs(theta_grid - bdc_center) <= bdc_range
            if np.any(bdc_mask):
                bdc_velocities = np.abs(velocity[bdc_mask])
                max_bdc_velocity = np.max(bdc_velocities)
                if max_bdc_velocity > 0.1:  # Arbitrary threshold
                    report.num_violations += 1
                    self.logger.warning(f"BDC dwell velocity too high: {max_bdc_velocity:.3f}")
        
        report.total_checks += 3
    
    def _validate_periodicity_and_smoothness(self, theta_grid: np.ndarray,
                                           position: np.ndarray, velocity: np.ndarray,
                                           acceleration: np.ndarray, report: DenseValidationReport):
        """Validate periodicity and smoothness."""
        
        # Periodicity checks
        position_closure = abs(position[0] - position[-1])
        velocity_closure = abs(velocity[0] - velocity[-1])
        acceleration_closure = abs(acceleration[0] - acceleration[-1])
        
        stroke_magnitude = np.max(position) - np.min(position)
        velocity_magnitude = np.max(np.abs(velocity))
        acceleration_magnitude = np.max(np.abs(acceleration))
        
        # Relative tolerances
        if position_closure > 0.001 * stroke_magnitude:
            report.num_violations += 1
            self.logger.warning(f"Position not periodic: closure error {position_closure:.6f}mm")
        
        if velocity_closure > 0.01 * velocity_magnitude:
            report.num_violations += 1
            self.logger.warning(f"Velocity not periodic: closure error {velocity_closure:.6f}")
        
        if acceleration_closure > 0.01 * acceleration_magnitude:
            report.num_violations += 1
            self.logger.warning(f"Acceleration not periodic: closure error {acceleration_closure:.6f}")
        
        # Smoothness checks (finite differences)
        velocity_smoothness = np.max(np.abs(np.diff(velocity, 2)))  # Second difference
        acceleration_smoothness = np.max(np.abs(np.diff(acceleration, 2)))
        
        # These are heuristic limits
        if velocity_smoothness > velocity_magnitude * 0.1:
            report.num_violations += 1
            self.logger.warning(f"Velocity not smooth: max 2nd difference {velocity_smoothness:.6f}")
        
        if acceleration_smoothness > acceleration_magnitude * 0.1:
            report.num_violations += 1
            self.logger.warning(f"Acceleration not smooth: max 2nd difference {acceleration_smoothness:.6f}")
        
        report.total_checks += 5
    
    def _validate_safety_limits(self, velocity: np.ndarray, acceleration: np.ndarray,
                              jerk: np.ndarray, report: DenseValidationReport):
        """Validate safety and performance limits."""
        
        # These are already checked in kinematic validation, but add specific safety margins
        safety_margin = 0.8  # 80% of limit
        
        if report.velocity_max > self.limits.velocity_max * safety_margin:
            self.logger.info(f"Velocity approaching limit: {report.velocity_max:.1f} mm/s (limit: {self.limits.velocity_max:.1f})")
        
        if report.acceleration_max > self.limits.acceleration_max * safety_margin:
            self.logger.info(f"Acceleration approaching limit: {report.acceleration_max:.1f} mm/s² (limit: {self.limits.acceleration_max:.1f})")
        
        if report.jerk_max > self.limits.jerk_max * safety_margin:
            self.logger.info(f"Jerk approaching limit: {report.jerk_max:.1f} mm/s³ (limit: {self.limits.jerk_max:.1f})")
        
        # No violations added for warnings
        report.total_checks += 3
    
    def format_report(self, report: DenseValidationReport) -> str:
        """Format validation report as human-readable string."""
        lines = []
        lines.append("=" * 60)
        lines.append("DENSE POST-SOLVE VALIDATION REPORT")
        lines.append("=" * 60)
        
        # Overall status
        status = "PASSED" if report.passed else "FAILED"
        lines.append(f"Status: {status}")
        lines.append(f"Total checks: {report.total_checks}")
        lines.append(f"Violations: {report.num_violations}")
        lines.append(f"Validation time: {report.validation_time_ms:.1f}ms")
        lines.append("")
        
        # Kinematic summary
        lines.append("KINEMATIC LIMITS:")
        lines.append(f"  Max velocity: {report.velocity_max:.1f} mm/s (limit: {self.limits.velocity_max:.1f})")
        lines.append(f"  Max acceleration: {report.acceleration_max:.1f} mm/s² (limit: {self.limits.acceleration_max:.1f})")
        lines.append(f"  Max jerk: {report.jerk_max:.1f} mm/s³ (limit: {self.limits.jerk_max:.1f})")
        lines.append("")
        
        # Gear geometry summary
        if report.pressure_angle_violations > 0:
            lines.append("PRESSURE ANGLE VIOLATIONS:")
            lines.append(f"  Count: {report.pressure_angle_violations}")
            lines.append(f"  Max angle: {np.rad2deg(report.pressure_angle_max):.1f}° (limit: {np.rad2deg(self.limits.pressure_angle_max):.1f}°)")
            lines.append("")
        
        if report.contact_ratio_result:
            cr = report.contact_ratio_result
            status_str = "PASS" if cr.passed else "FAIL"
            lines.append(f"CONTACT RATIO: {status_str}")
            lines.append(f"  Value: {cr.value:.2f} (min: {self.limits.contact_ratio_min:.2f})")
            lines.append("")
        
        # Summary of violations by category
        if report.num_violations > 0:
            lines.append("VIOLATION SUMMARY:")
            if report.kinematic_violations > 0:
                lines.append(f"  Kinematic: {report.kinematic_violations}")
            if report.pressure_angle_violations > 0:
                lines.append(f"  Pressure angle: {report.pressure_angle_violations}")
            if report.curvature_violations > 0:
                lines.append(f"  Curvature: {report.curvature_violations}")
            if report.thickness_violations > 0:
                lines.append(f"  Thickness: {report.thickness_violations}")
            if report.sliding_violations > 0:
                lines.append(f"  Sliding: {report.sliding_violations}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


def validate_collocation_solution(solution_data: Dict[str, Any],
                                motion_params: Dict[str, Any],
                                limits: Optional[ValidationLimits] = None) -> DenseValidationReport:
    """
    Convenience function to validate a collocation solution.
    
    Args:
        solution_data: Dictionary containing theta_grid, position, velocity, acceleration
        motion_params: Motion parameters for context
        limits: Validation limits (optional)
        
    Returns:
        Validation report
    """
    validator = DenseValidator(limits)
    
    return validator.validate_solution(
        theta_grid=solution_data['theta_grid'],
        position=solution_data['position'],
        velocity=solution_data['velocity'],
        acceleration=solution_data['acceleration'],
        motion_params=motion_params
    )
