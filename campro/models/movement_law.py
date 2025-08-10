"""
Movement Law Implementation for CamProV5 Design Layer

This module provides the Python implementation of cam motion laws for design,
analysis, and parameter optimization. It serves as the design laboratory where
engineers can rapidly iterate on motion parameters, visualize kinematic behavior,
and optimize designs before committing to expensive FEA simulations.

Key Features:
- Interactive motion law design and analysis
- Parameter optimization using scipy/numpy
- Kinematic analysis and visualization
- Design validation and reporting
- Mathematical foundation for Rust FEA engine parameters

Author: CamPro Team
Version: 5.0.0
"""

from typing import Dict, List, Optional, Tuple, Union, Callable
import numpy as np
from scipy.optimize import minimize, differential_evolution
from scipy.interpolate import CubicSpline, interp1d
import matplotlib.pyplot as plt
from dataclasses import dataclass, asdict
import json
import toml
from pathlib import Path
import logging

# Setup logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@dataclass
class MotionParameters:
    """
    Data class for motion law parameters that will be passed to the Rust FEA engine.

    This serves as the interface between the Python design layer and the Rust
    high-performance simulation layer.
    """
    # Cam geometry parameters
    base_circle_radius: float = 25.0  # mm
    max_lift: float = 10.0  # mm
    # Total duration of the cam profile. This value is derived from the rise,
    # dwell and fall segments and is normalised during initialisation to avoid
    # inconsistencies between individual segment durations and the reported
    # total cam duration.
    cam_duration: float = 180.0  # degrees

    # Motion profile parameters
    rise_duration: float = 90.0  # degrees
    dwell_duration: float = 45.0  # degrees
    fall_duration: float = 90.0  # degrees

    # Advanced parameters
    jerk_limit: float = 1000.0  # mm/s³
    acceleration_limit: float = 500.0  # mm/s²
    velocity_limit: float = 100.0  # mm/s

    # Engine operating parameters
    rpm: float = 3000.0  # revolutions per minute
    
    def __post_init__(self):
        """Validate parameters after initialization."""
        # Ensure cam_duration always matches the sum of all motion segments.
        # The original implementation left ``cam_duration`` unchanged which
        # meant that providing custom rise/dwell/fall durations could result in
        # a mismatched total duration.  This in turn caused serialization
        # round-trips and downstream calculations to work with inconsistent
        # data.  By normalising the value here we guarantee that the reported
        # total duration is always self‑consistent.
        self.cam_duration = (
            self.rise_duration + self.dwell_duration + self.fall_duration
        )
        self.validate()
        
    def validate(self) -> None:
        """Validate parameters for physical feasibility."""
        if self.base_circle_radius <= 0:
            raise ValueError("Base circle radius must be positive")
        
        if self.max_lift <= 0:
            raise ValueError("Maximum lift must be positive")
        
        if self.rise_duration < 0:
            raise ValueError("Rise duration must be non-negative")
        
        if self.dwell_duration < 0:
            raise ValueError("Dwell duration must be non-negative")
        
        if self.fall_duration < 0:
            raise ValueError("Fall duration must be non-negative")
        
        if self.rpm <= 0:
            raise ValueError("RPM must be positive")
        
        total_duration = self.rise_duration + self.dwell_duration + self.fall_duration
        if total_duration > 360.0:
            raise ValueError("Total cam duration must not exceed 360 degrees")

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_toml(self) -> str:
        """Serialize to TOML string."""
        return toml.dumps(self.to_dict())

    @classmethod
    def _validate_data(cls, data: Dict) -> None:
        """Validate data dictionary for required fields and types."""
        required_fields = ['base_circle_radius', 'max_lift', 'rise_duration', 
                          'dwell_duration', 'fall_duration', 'rpm']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check field types
        for field in required_fields:
            if not isinstance(data[field], (int, float)):
                raise ValueError(f"Field {field} must be a number")
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MotionParameters':
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'MotionParameters':
        """Create from JSON string."""
        try:
            data = json.loads(json_str)
            cls._validate_data(data)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing JSON: {e}")

    @classmethod
    def from_toml(cls, toml_str: str) -> 'MotionParameters':
        """Create from TOML string."""
        try:
            data = toml.loads(toml_str)
            cls._validate_data(data)
            return cls.from_dict(data)
        except toml.TomlDecodeError as e:
            raise ValueError(f"Invalid TOML format: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing TOML: {e}")


class MotionLaw:
    """
    Core motion law implementation for cam profile design and analysis.

    This class provides the mathematical foundation for cam motion laws,
    including various motion profiles (polynomial, cycloidal, harmonic, etc.)
    and their kinematic analysis.
    """

    def __init__(self, parameters: MotionParameters):
        """
        Initialize motion law with given parameters.

        Args:
            parameters: Motion parameters defining the cam profile
        """
        self.params = parameters
        self.logger = logging.getLogger(f"{__name__}.MotionLaw")

        # Derived parameters
        self.omega = 2 * np.pi * self.params.rpm / 60.0  # rad/s
        self.total_duration = (self.params.rise_duration +
                              self.params.dwell_duration +
                              self.params.fall_duration)

        # Validate parameters
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Validate motion parameters for physical feasibility."""
        if self.params.max_lift <= 0:
            raise ValueError("Maximum lift must be positive")

        if self.params.base_circle_radius <= 0:
            raise ValueError("Base circle radius must be positive")

        if self.params.rise_duration < 0:
            raise ValueError("Rise duration must be non-negative")

        if self.params.dwell_duration < 0:
            raise ValueError("Dwell duration must be non-negative")

        if self.params.fall_duration < 0:
            raise ValueError("Fall duration must be non-negative")

        if self.total_duration <= 0:
            raise ValueError("Total cam duration must be positive")

        if self.total_duration > 360.0:
            raise ValueError("Total cam duration must not exceed 360 degrees")

        if self.params.rpm <= 0:
            raise ValueError("RPM must be positive")

        self.logger.info(f"Motion parameters validated successfully")

    def displacement(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cam follower displacement as a function of cam angle.

        Args:
            theta: Cam angle in degrees

        Returns:
            Follower displacement in mm
        """
        theta = np.asarray(theta)
        theta_norm = np.mod(theta, 360.0)  # Normalize to 0-360 degrees

        displacement = np.zeros_like(theta_norm)

        # Rise phase (0 to rise_duration)
        rise_mask = theta_norm <= self.params.rise_duration
        if np.any(rise_mask):
            theta_rise = theta_norm[rise_mask]
            # Use modified sine motion law for smooth acceleration
            beta = theta_rise / self.params.rise_duration
            displacement[rise_mask] = self.params.max_lift * (
                beta - np.sin(2 * np.pi * beta) / (2 * np.pi)
            )

        # Dwell phase (rise_duration to rise_duration + dwell_duration)
        dwell_start = self.params.rise_duration
        dwell_end = dwell_start + self.params.dwell_duration
        dwell_mask = (theta_norm > dwell_start) & (theta_norm <= dwell_end)
        displacement[dwell_mask] = self.params.max_lift

        # Fall phase (dwell_end to total_duration)
        fall_mask = (theta_norm > dwell_end) & (theta_norm <= self.total_duration)
        if np.any(fall_mask):
            theta_fall = theta_norm[fall_mask] - dwell_end
            # Use modified sine motion law for smooth deceleration
            beta = theta_fall / self.params.fall_duration
            displacement[fall_mask] = self.params.max_lift * (
                1 - (beta - np.sin(2 * np.pi * beta) / (2 * np.pi))
            )

        return displacement

    def velocity(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cam follower velocity as a function of cam angle.

        Args:
            theta: Cam angle in degrees

        Returns:
            Follower velocity in mm/s
        """
        theta = np.asarray(theta)
        theta_norm = np.mod(theta, 360.0)

        velocity = np.zeros_like(theta_norm)

        # Convert degrees to radians for derivatives
        deg_to_rad = np.pi / 180.0

        # Rise phase
        rise_mask = theta_norm <= self.params.rise_duration
        if np.any(rise_mask):
            theta_rise = theta_norm[rise_mask]
            beta = theta_rise / self.params.rise_duration
            dbeta_dtheta = 1.0 / self.params.rise_duration

            velocity[rise_mask] = (self.params.max_lift * dbeta_dtheta *
                                 (1 - np.cos(2 * np.pi * beta)) *
                                 self.omega * deg_to_rad)

        # Dwell phase - velocity is zero
        dwell_start = self.params.rise_duration
        dwell_end = dwell_start + self.params.dwell_duration
        dwell_mask = (theta_norm > dwell_start) & (theta_norm <= dwell_end)
        velocity[dwell_mask] = 0.0

        # Fall phase
        fall_mask = (theta_norm > dwell_end) & (theta_norm <= self.total_duration)
        if np.any(fall_mask):
            theta_fall = theta_norm[fall_mask] - dwell_end
            beta = theta_fall / self.params.fall_duration
            dbeta_dtheta = 1.0 / self.params.fall_duration

            velocity[fall_mask] = (-self.params.max_lift * dbeta_dtheta *
                                 (1 - np.cos(2 * np.pi * beta)) *
                                 self.omega * deg_to_rad)

        return velocity

    def acceleration(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cam follower acceleration as a function of cam angle.

        Args:
            theta: Cam angle in degrees

        Returns:
            Follower acceleration in mm/s²
        """
        theta = np.asarray(theta)
        theta_norm = np.mod(theta, 360.0)

        acceleration = np.zeros_like(theta_norm)

        # Convert degrees to radians for derivatives
        deg_to_rad = np.pi / 180.0

        # Rise phase
        rise_mask = theta_norm <= self.params.rise_duration
        if np.any(rise_mask):
            theta_rise = theta_norm[rise_mask]
            beta = theta_rise / self.params.rise_duration
            dbeta_dtheta = 1.0 / self.params.rise_duration

            acceleration[rise_mask] = (self.params.max_lift * (dbeta_dtheta ** 2) *
                                     2 * np.pi * np.sin(2 * np.pi * beta) *
                                     (self.omega * deg_to_rad) ** 2)

        # Dwell phase - acceleration is zero
        dwell_start = self.params.rise_duration
        dwell_end = dwell_start + self.params.dwell_duration
        dwell_mask = (theta_norm > dwell_start) & (theta_norm <= dwell_end)
        acceleration[dwell_mask] = 0.0

        # Fall phase
        fall_mask = (theta_norm > dwell_end) & (theta_norm <= self.total_duration)
        if np.any(fall_mask):
            theta_fall = theta_norm[fall_mask] - dwell_end
            beta = theta_fall / self.params.fall_duration
            dbeta_dtheta = 1.0 / self.params.fall_duration

            acceleration[fall_mask] = (self.params.max_lift * (dbeta_dtheta ** 2) *
                                     2 * np.pi * np.sin(2 * np.pi * beta) *
                                     (self.omega * deg_to_rad) ** 2)

        return acceleration

    def jerk(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cam follower jerk as a function of cam angle.

        Args:
            theta: Cam angle in degrees

        Returns:
            Follower jerk in mm/s³
        """
        theta = np.asarray(theta)
        theta_norm = np.mod(theta, 360.0)

        jerk = np.zeros_like(theta_norm)

        # Convert degrees to radians for derivatives
        deg_to_rad = np.pi / 180.0

        # Rise phase
        rise_mask = theta_norm <= self.params.rise_duration
        if np.any(rise_mask):
            theta_rise = theta_norm[rise_mask]
            beta = theta_rise / self.params.rise_duration
            dbeta_dtheta = 1.0 / self.params.rise_duration

            jerk[rise_mask] = (self.params.max_lift * (dbeta_dtheta ** 3) *
                             4 * (np.pi ** 2) * np.cos(2 * np.pi * beta) *
                             (self.omega * deg_to_rad) ** 3)

        # Dwell phase - jerk is zero
        dwell_start = self.params.rise_duration
        dwell_end = dwell_start + self.params.dwell_duration
        dwell_mask = (theta_norm > dwell_start) & (theta_norm <= dwell_end)
        jerk[dwell_mask] = 0.0

        # Fall phase
        fall_mask = (theta_norm > dwell_end) & (theta_norm <= self.total_duration)
        if np.any(fall_mask):
            theta_fall = theta_norm[fall_mask] - dwell_end
            beta = theta_fall / self.params.fall_duration
            dbeta_dtheta = 1.0 / self.params.fall_duration

            jerk[fall_mask] = (-self.params.max_lift * (dbeta_dtheta ** 3) *
                             4 * (np.pi ** 2) * np.cos(2 * np.pi * beta) *
                             (self.omega * deg_to_rad) ** 3)

        return jerk

    def analyze_kinematics(self, num_points: int = 1000) -> Dict:
        """
        Perform comprehensive kinematic analysis of the motion law.

        Args:
            num_points: Number of points for analysis

        Returns:
            Dictionary containing kinematic analysis results
        """
        theta = np.linspace(0, self.total_duration, num_points)

        s = self.displacement(theta)
        v = self.velocity(theta)
        a = self.acceleration(theta)
        j = self.jerk(theta)

        analysis = {
            'theta': theta,
            'displacement': s,
            'velocity': v,
            'acceleration': a,
            'jerk': j,
            'max_velocity': np.max(np.abs(v)),
            'max_acceleration': np.max(np.abs(a)),
            'max_jerk': np.max(np.abs(j)),
            'rms_acceleration': np.sqrt(np.mean(a**2)),
            'rms_jerk': np.sqrt(np.mean(j**2)),
            'parameters': self.params
        }

        # Check constraint violations
        analysis['velocity_violation'] = analysis['max_velocity'] > self.params.velocity_limit
        analysis['acceleration_violation'] = analysis['max_acceleration'] > self.params.acceleration_limit
        analysis['jerk_violation'] = analysis['max_jerk'] > self.params.jerk_limit

        self.logger.info(f"Kinematic analysis completed: "
                        f"max_v={analysis['max_velocity']:.2f}, "
                        f"max_a={analysis['max_acceleration']:.2f}, "
                        f"max_j={analysis['max_jerk']:.2f}")

        return analysis

    def plot_kinematics(self, save_path: Optional[Path] = None) -> None:
        """
        Generate comprehensive kinematic plots for design visualization.

        Args:
            save_path: Optional path to save the plot
        """
        analysis = self.analyze_kinematics()

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f'Cam Motion Law Analysis (RPM: {self.params.rpm})', fontsize=14)

        # Displacement plot
        axes[0, 0].plot(analysis['theta'], analysis['displacement'], 'b-', linewidth=2)
        axes[0, 0].set_xlabel('Cam Angle (degrees)')
        axes[0, 0].set_ylabel('Displacement (mm)')
        axes[0, 0].set_title('Follower Displacement')
        axes[0, 0].grid(True, alpha=0.3)

        # Velocity plot
        axes[0, 1].plot(analysis['theta'], analysis['velocity'], 'g-', linewidth=2)
        axes[0, 1].axhline(y=self.params.velocity_limit, color='r', linestyle='--',
                          label=f'Limit: {self.params.velocity_limit}')
        axes[0, 1].axhline(y=-self.params.velocity_limit, color='r', linestyle='--')
        axes[0, 1].set_xlabel('Cam Angle (degrees)')
        axes[0, 1].set_ylabel('Velocity (mm/s)')
        axes[0, 1].set_title('Follower Velocity')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].legend()

        # Acceleration plot
        axes[1, 0].plot(analysis['theta'], analysis['acceleration'], 'orange', linewidth=2)
        axes[1, 0].axhline(y=self.params.acceleration_limit, color='r', linestyle='--',
                          label=f'Limit: {self.params.acceleration_limit}')
        axes[1, 0].axhline(y=-self.params.acceleration_limit, color='r', linestyle='--')
        axes[1, 0].set_xlabel('Cam Angle (degrees)')
        axes[1, 0].set_ylabel('Acceleration (mm/s²)')
        axes[1, 0].set_title('Follower Acceleration')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].legend()

        # Jerk plot
        axes[1, 1].plot(analysis['theta'], analysis['jerk'], 'purple', linewidth=2)
        axes[1, 1].axhline(y=self.params.jerk_limit, color='r', linestyle='--',
                          label=f'Limit: {self.params.jerk_limit}')
        axes[1, 1].axhline(y=-self.params.jerk_limit, color='r', linestyle='--')
        axes[1, 1].set_xlabel('Cam Angle (degrees)')
        axes[1, 1].set_ylabel('Jerk (mm/s³)')
        axes[1, 1].set_title('Follower Jerk')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Kinematic plots saved to {save_path}")

        plt.show()


class MotionOptimizer:
    """
    Motion law parameter optimizer for design optimization.

    This class provides optimization capabilities to find optimal motion
    parameters that minimize various objective functions while satisfying
    kinematic constraints.
    """

    def __init__(self, base_parameters: MotionParameters):
        """
        Initialize optimizer with base parameters.

        Args:
            base_parameters: Starting point for optimization
        """
        self.base_params = base_parameters
        self.logger = logging.getLogger(f"{__name__}.MotionOptimizer")

    def objective_function(self, x: np.ndarray, objective_type: str = 'rms_acceleration') -> float:
        """
        Objective function for optimization.

        Args:
            x: Parameter vector [max_lift, rise_duration, fall_duration]
            objective_type: Type of objective ('rms_acceleration', 'max_jerk', 'energy')

        Returns:
            Objective function value
        """
        try:
            # Update parameters
            params = MotionParameters(
                base_circle_radius=self.base_params.base_circle_radius,
                max_lift=x[0],
                rise_duration=x[1],
                dwell_duration=self.base_params.dwell_duration,
                fall_duration=x[2],
                rpm=self.base_params.rpm,
                jerk_limit=self.base_params.jerk_limit,
                acceleration_limit=self.base_params.acceleration_limit,
                velocity_limit=self.base_params.velocity_limit
            )

            # Create motion law and analyze
            motion = MotionLaw(params)
            analysis = motion.analyze_kinematics()

            # Apply penalty for constraint violations
            penalty = 0.0
            if analysis['velocity_violation']:
                penalty += 1000 * (analysis['max_velocity'] - params.velocity_limit)
            if analysis['acceleration_violation']:
                penalty += 1000 * (analysis['max_acceleration'] - params.acceleration_limit)
            if analysis['jerk_violation']:
                penalty += 1000 * (analysis['max_jerk'] - params.jerk_limit)

            # Calculate objective based on type
            if objective_type == 'rms_acceleration':
                objective = analysis['rms_acceleration']
            elif objective_type == 'max_jerk':
                objective = analysis['max_jerk']
            elif objective_type == 'energy':
                # Approximate energy as integral of acceleration squared
                objective = analysis['rms_acceleration'] ** 2
            else:
                raise ValueError(f"Unknown objective type: {objective_type}")

            return objective + penalty

        except Exception as e:
            self.logger.warning(f"Objective function evaluation failed: {e}")
            return 1e6  # Large penalty for invalid parameters

    def optimize(self,
                 bounds: Optional[List[Tuple[float, float]]] = None,
                 objective_type: str = 'rms_acceleration',
                 method: str = 'differential_evolution') -> Dict:
        """
        Optimize motion parameters.

        Args:
            bounds: Parameter bounds [(min_lift, max_lift), (min_rise, max_rise), (min_fall, max_fall)]
            objective_type: Optimization objective
            method: Optimization method ('differential_evolution', 'minimize')

        Returns:
            Optimization results dictionary
        """
        if bounds is None:
            bounds = [
                (5.0, 20.0),    # max_lift bounds
                (45.0, 135.0),  # rise_duration bounds
                (45.0, 135.0)   # fall_duration bounds
            ]

        x0 = [self.base_params.max_lift,
              self.base_params.rise_duration,
              self.base_params.fall_duration]

        self.logger.info(f"Starting optimization with method: {method}, objective: {objective_type}")

        if method == 'differential_evolution':
            result = differential_evolution(
                lambda x: self.objective_function(x, objective_type),
                bounds,
                seed=42,
                maxiter=100,
                popsize=15
            )
        elif method == 'minimize':
            result = minimize(
                lambda x: self.objective_function(x, objective_type),
                x0,
                bounds=bounds,
                method='L-BFGS-B'
            )
        else:
            raise ValueError(f"Unknown optimization method: {method}")

        # Create optimized parameters
        optimized_params = MotionParameters(
            base_circle_radius=self.base_params.base_circle_radius,
            max_lift=result.x[0],
            rise_duration=result.x[1],
            dwell_duration=self.base_params.dwell_duration,
            fall_duration=result.x[2],
            rpm=self.base_params.rpm,
            jerk_limit=self.base_params.jerk_limit,
            acceleration_limit=self.base_params.acceleration_limit,
            velocity_limit=self.base_params.velocity_limit
        )

        # Analyze optimized design
        optimized_motion = MotionLaw(optimized_params)
        optimized_analysis = optimized_motion.analyze_kinematics()

        optimization_result = {
            'success': result.success,
            'message': result.message if hasattr(result, 'message') else 'Optimization completed',
            'iterations': result.nit if hasattr(result, 'nit') else result.nfev,
            'objective_value': result.fun,
            'optimized_parameters': optimized_params,
            'original_parameters': self.base_params,
            'kinematic_analysis': optimized_analysis,
            'improvement': {
                'rms_acceleration_reduction': (
                    MotionLaw(self.base_params).analyze_kinematics()['rms_acceleration'] -
                    optimized_analysis['rms_acceleration']
                ),
                'max_jerk_reduction': (
                    MotionLaw(self.base_params).analyze_kinematics()['max_jerk'] -
                    optimized_analysis['max_jerk']
                )
            }
        }

        self.logger.info(f"Optimization completed: success={result.success}, "
                        f"objective={result.fun:.4f}")

        return optimization_result


def export_parameters_for_fea(parameters: MotionParameters,
                             output_path: Path,
                             format_type: str = 'toml') -> None:
    """
    Export motion parameters in format suitable for Rust FEA engine.

    Args:
        parameters: Motion parameters to export
        output_path: Path for output file
        format_type: Export format ('toml', 'json')
    """
    logger = logging.getLogger(f"{__name__}.export_parameters_for_fea")

    if format_type.lower() == 'toml':
        content = parameters.to_toml()
        output_path = output_path.with_suffix('.toml')
    elif format_type.lower() == 'json':
        content = parameters.to_json()
        output_path = output_path.with_suffix('.json')
    else:
        raise ValueError(f"Unsupported format: {format_type}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)

    logger.info(f"Motion parameters exported to {output_path} in {format_type.upper()} format")


# Example usage and testing
if __name__ == "__main__":
    # Create example motion parameters
    params = MotionParameters(
        base_circle_radius=25.0,
        max_lift=12.0,
        rise_duration=90.0,
        dwell_duration=45.0,
        fall_duration=90.0,
        rpm=3000.0
    )

    # Create motion law and analyze
    motion = MotionLaw(params)
    analysis = motion.analyze_kinematics()

    print("Motion Law Analysis Results:")
    print(f"Max Velocity: {analysis['max_velocity']:.2f} mm/s")
    print(f"Max Acceleration: {analysis['max_acceleration']:.2f} mm/s²")
    print(f"Max Jerk: {analysis['max_jerk']:.2f} mm/s³")
    print(f"RMS Acceleration: {analysis['rms_acceleration']:.2f} mm/s²")

    # Generate plots
    motion.plot_kinematics()

    # Demonstrate optimization
    optimizer = MotionOptimizer(params)
    opt_result = optimizer.optimize(objective_type='rms_acceleration')

    if opt_result['success']:
        print("\nOptimization Results:")
        print(f"RMS Acceleration Reduction: {opt_result['improvement']['rms_acceleration_reduction']:.2f} mm/s²")
        print(f"Max Jerk Reduction: {opt_result['improvement']['max_jerk_reduction']:.2f} mm/s³")

        # Export optimized parameters for FEA engine
        export_parameters_for_fea(
            opt_result['optimized_parameters'],
            Path("fea_config/optimized_motion_params"),
            format_type='toml'
        )