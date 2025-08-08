//! Native Motion Law Implementation for High-Performance FEA Engine
//!
//! This module provides the Rust implementation of cam motion laws that is mathematically
//! equivalent to the Python design layer implementation. It is optimized for high-performance
//! FEA simulation with no Python FFI calls during critical computation paths.
//!
//! Key Features:
//! - Native Rust implementation for maximum performance
//! - Mathematical equivalence with Python design layer
//! - Memory-efficient data structures for large simulations
//! - Parallel computation support via rayon
//! - Real-time boundary condition calculation

use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::f64::consts::PI;
use crate::error::{FEAError, FEAResult};

/// Motion parameters for cam profile definition
///
/// This struct is designed to be compatible with the Python MotionParameters
/// and supports serialization/deserialization from TOML/JSON configuration files.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MotionParameters {
    /// Base circle radius in mm
    pub base_circle_radius: f64,
    /// Maximum lift in mm
    pub max_lift: f64,
    /// Total cam duration in degrees
    pub cam_duration: f64,
    /// Rise duration in degrees
    pub rise_duration: f64,
    /// Dwell duration in degrees
    pub dwell_duration: f64,
    /// Fall duration in degrees
    pub fall_duration: f64,
    /// Jerk limit in mm/s³
    pub jerk_limit: f64,
    /// Acceleration limit in mm/s²
    pub acceleration_limit: f64,
    /// Velocity limit in mm/s
    pub velocity_limit: f64,
    /// Engine RPM
    pub rpm: f64,
}

impl Default for MotionParameters {
    fn default() -> Self {
        Self {
            base_circle_radius: 25.0,
            max_lift: 10.0,
            cam_duration: 180.0,
            rise_duration: 90.0,
            dwell_duration: 45.0,
            fall_duration: 90.0,
            jerk_limit: 1000.0,
            acceleration_limit: 500.0,
            velocity_limit: 100.0,
            rpm: 3000.0,
        }
    }
}

impl MotionParameters {
    /// Validate motion parameters for physical feasibility
    pub fn validate(&self) -> FEAResult<()> {
        if self.max_lift <= 0.0 {
            return Err(FEAError::ParameterValidation("Maximum lift must be positive".to_string()));
        }
        if self.base_circle_radius <= 0.0 {
            return Err(FEAError::ParameterValidation("Base circle radius must be positive".to_string()));
        }
        if self.total_duration() <= 0.0 {
            return Err(FEAError::ParameterValidation("Total cam duration must be positive".to_string()));
        }
        if self.rpm <= 0.0 {
            return Err(FEAError::ParameterValidation("RPM must be positive".to_string()));
        }
        
        // Additional validation for more robust error handling
        if self.rise_duration < 0.0 {
            return Err(FEAError::ParameterValidation("Rise duration cannot be negative".to_string()));
        }
        if self.dwell_duration < 0.0 {
            return Err(FEAError::ParameterValidation("Dwell duration cannot be negative".to_string()));
        }
        if self.fall_duration < 0.0 {
            return Err(FEAError::ParameterValidation("Fall duration cannot be negative".to_string()));
        }
        
        // Validate limits
        if self.velocity_limit <= 0.0 {
            return Err(FEAError::ParameterValidation("Velocity limit must be positive".to_string()));
        }
        if self.acceleration_limit <= 0.0 {
            return Err(FEAError::ParameterValidation("Acceleration limit must be positive".to_string()));
        }
        if self.jerk_limit <= 0.0 {
            return Err(FEAError::ParameterValidation("Jerk limit must be positive".to_string()));
        }
        
        Ok(())
    }

    /// Calculate total cam duration
    pub fn total_duration(&self) -> f64 {
        self.rise_duration + self.dwell_duration + self.fall_duration
    }

    /// Calculate angular velocity in rad/s
    pub fn omega(&self) -> f64 {
        2.0 * PI * self.rpm / 60.0
    }
}

/// Kinematic analysis results
#[derive(Debug, Clone, serde::Serialize)]
pub struct KinematicAnalysis {
    pub theta: Vec<f64>,
    pub displacement: Vec<f64>,
    pub velocity: Vec<f64>,
    pub acceleration: Vec<f64>,
    pub jerk: Vec<f64>,
    pub max_velocity: f64,
    pub max_acceleration: f64,
    pub max_jerk: f64,
    pub rms_acceleration: f64,
    pub rms_jerk: f64,
    pub velocity_violation: bool,
    pub acceleration_violation: bool,
    pub jerk_violation: bool,
}

/// High-performance motion law implementation
///
/// This struct provides the core motion law calculations optimized for FEA simulation.
/// All methods are designed to be called millions of times per simulation without
/// performance degradation.
#[derive(Debug, Clone)]
pub struct MotionLaw {
    params: MotionParameters,
    omega: f64,
    total_duration: f64,
    deg_to_rad: f64,
}

impl MotionLaw {
    /// Create a new motion law instance
    pub fn new(parameters: MotionParameters) -> FEAResult<Self> {
        // Validate parameters
        parameters.validate()?;

        let omega = parameters.omega();
        let total_duration = parameters.total_duration();
        let deg_to_rad = PI / 180.0;

        // Create the motion law
        let motion_law = Self {
            params: parameters,
            omega,
            total_duration,
            deg_to_rad,
        };

        // Perform additional validation
        if motion_law.total_duration > 360.0 {
            return Err(FEAError::ParameterValidation(
                "Total cam duration cannot exceed 360 degrees".to_string()
            ));
        }

        Ok(motion_law)
    }

    /// Get motion parameters
    pub fn parameters(&self) -> &MotionParameters {
        &self.params
    }

    /// Calculate cam follower displacement for a single angle
    ///
    /// This is the performance-critical function that will be called millions of times
    /// during FEA simulation. It uses the modified sine motion law for smooth acceleration.
    #[inline]
    pub fn displacement(&self, theta: f64) -> f64 {
        let theta_norm = theta % 360.0;

        if theta_norm <= self.params.rise_duration {
            // Rise phase
            let beta = theta_norm / self.params.rise_duration;
            self.params.max_lift * (beta - (2.0 * PI * beta).sin() / (2.0 * PI))
        } else if theta_norm <= self.params.rise_duration + self.params.dwell_duration {
            // Dwell phase
            self.params.max_lift
        } else if theta_norm <= self.total_duration {
            // Fall phase
            let theta_fall = theta_norm - (self.params.rise_duration + self.params.dwell_duration);
            let beta = theta_fall / self.params.fall_duration;
            self.params.max_lift * (1.0 - (beta - (2.0 * PI * beta).sin() / (2.0 * PI)))
        } else {
            // Outside cam duration
            0.0
        }
    }

    /// Calculate cam follower velocity for a single angle
    #[inline]
    pub fn velocity(&self, theta: f64) -> f64 {
        let theta_norm = theta % 360.0;

        if theta_norm <= self.params.rise_duration {
            // Rise phase
            let beta = theta_norm / self.params.rise_duration;
            let dbeta_dtheta = 1.0 / self.params.rise_duration;
            self.params.max_lift * dbeta_dtheta * (1.0 - (2.0 * PI * beta).cos()) * self.omega * self.deg_to_rad
        } else if theta_norm <= self.params.rise_duration + self.params.dwell_duration {
            // Dwell phase - velocity is zero
            0.0
        } else if theta_norm <= self.total_duration {
            // Fall phase
            let theta_fall = theta_norm - (self.params.rise_duration + self.params.dwell_duration);
            let beta = theta_fall / self.params.fall_duration;
            let dbeta_dtheta = 1.0 / self.params.fall_duration;
            -self.params.max_lift * dbeta_dtheta * (1.0 - (2.0 * PI * beta).cos()) * self.omega * self.deg_to_rad
        } else {
            // Outside cam duration
            0.0
        }
    }

    /// Calculate cam follower acceleration for a single angle
    #[inline]
    pub fn acceleration(&self, theta: f64) -> f64 {
        let theta_norm = theta % 360.0;

        if theta_norm <= self.params.rise_duration {
            // Rise phase
            let beta = theta_norm / self.params.rise_duration;
            let dbeta_dtheta = 1.0 / self.params.rise_duration;
            self.params.max_lift * (dbeta_dtheta * dbeta_dtheta) * 2.0 * PI * (2.0 * PI * beta).sin() *
                (self.omega * self.deg_to_rad) * (self.omega * self.deg_to_rad)
        } else if theta_norm <= self.params.rise_duration + self.params.dwell_duration {
            // Dwell phase - acceleration is zero
            0.0
        } else if theta_norm <= self.total_duration {
            // Fall phase
            let theta_fall = theta_norm - (self.params.rise_duration + self.params.dwell_duration);
            let beta = theta_fall / self.params.fall_duration;
            let dbeta_dtheta = 1.0 / self.params.fall_duration;
            self.params.max_lift * (dbeta_dtheta * dbeta_dtheta) * 2.0 * PI * (2.0 * PI * beta).sin() *
                (self.omega * self.deg_to_rad) * (self.omega * self.deg_to_rad)
        } else {
            // Outside cam duration
            0.0
        }
    }

    /// Calculate cam follower jerk for a single angle
    #[inline]
    pub fn jerk(&self, theta: f64) -> f64 {
        let theta_norm = theta % 360.0;

        if theta_norm <= self.params.rise_duration {
            // Rise phase
            let beta = theta_norm / self.params.rise_duration;
            let dbeta_dtheta = 1.0 / self.params.rise_duration;
            self.params.max_lift * (dbeta_dtheta * dbeta_dtheta * dbeta_dtheta) * 4.0 * PI * PI * (2.0 * PI * beta).cos() *
                (self.omega * self.deg_to_rad) * (self.omega * self.deg_to_rad) * (self.omega * self.deg_to_rad)
        } else if theta_norm <= self.params.rise_duration + self.params.dwell_duration {
            // Dwell phase - jerk is zero
            0.0
        } else if theta_norm <= self.total_duration {
            // Fall phase
            let theta_fall = theta_norm - (self.params.rise_duration + self.params.dwell_duration);
            let beta = theta_fall / self.params.fall_duration;
            let dbeta_dtheta = 1.0 / self.params.fall_duration;
            -self.params.max_lift * (dbeta_dtheta * dbeta_dtheta * dbeta_dtheta) * 4.0 * PI * PI * (2.0 * PI * beta).cos() *
                (self.omega * self.deg_to_rad) * (self.omega * self.deg_to_rad) * (self.omega * self.deg_to_rad)
        } else {
            // Outside cam duration
            0.0
        }
    }

    /// Calculate displacement for multiple angles in parallel
    ///
    /// This method leverages rayon for parallel computation when processing
    /// large arrays of angles, which is common in FEA simulations.
    pub fn displacement_parallel(&self, theta_values: &[f64]) -> Vec<f64> {
        theta_values
            .par_iter()
            .map(|&theta| self.displacement(theta))
            .collect()
    }

    /// Calculate velocity for multiple angles in parallel
    pub fn velocity_parallel(&self, theta_values: &[f64]) -> Vec<f64> {
        theta_values
            .par_iter()
            .map(|&theta| self.velocity(theta))
            .collect()
    }

    /// Calculate acceleration for multiple angles in parallel
    pub fn acceleration_parallel(&self, theta_values: &[f64]) -> Vec<f64> {
        theta_values
            .par_iter()
            .map(|&theta| self.acceleration(theta))
            .collect()
    }

    /// Calculate jerk for multiple angles in parallel
    pub fn jerk_parallel(&self, theta_values: &[f64]) -> Vec<f64> {
        theta_values
            .par_iter()
            .map(|&theta| self.jerk(theta))
            .collect()
    }

    /// Perform comprehensive kinematic analysis
    ///
    /// This method provides the same analysis as the Python version but with
    /// optimized parallel computation for large datasets.
    pub fn analyze_kinematics(&self, num_points: usize) -> KinematicAnalysis {
        // Generate angle array
        let theta: Vec<f64> = (0..num_points)
            .map(|i| i as f64 * self.total_duration / (num_points - 1) as f64)
            .collect();

        // Calculate kinematics in parallel
        let displacement = self.displacement_parallel(&theta);
        let velocity = self.velocity_parallel(&theta);
        let acceleration = self.acceleration_parallel(&theta);
        let jerk = self.jerk_parallel(&theta);

        // Calculate statistics
        let max_velocity = velocity.iter().map(|v| v.abs()).fold(0.0, f64::max);
        let max_acceleration = acceleration.iter().map(|a| a.abs()).fold(0.0, f64::max);
        let max_jerk = jerk.iter().map(|j| j.abs()).fold(0.0, f64::max);

        let rms_acceleration = (acceleration.iter().map(|a| a * a).sum::<f64>() / acceleration.len() as f64).sqrt();
        let rms_jerk = (jerk.iter().map(|j| j * j).sum::<f64>() / jerk.len() as f64).sqrt();

        // Check constraint violations
        let velocity_violation = max_velocity > self.params.velocity_limit;
        let acceleration_violation = max_acceleration > self.params.acceleration_limit;
        let jerk_violation = max_jerk > self.params.jerk_limit;

        KinematicAnalysis {
            theta,
            displacement,
            velocity,
            acceleration,
            jerk,
            max_velocity,
            max_acceleration,
            max_jerk,
            rms_acceleration,
            rms_jerk,
            velocity_violation,
            acceleration_violation,
            jerk_violation,
        }
    }

    /// Calculate boundary conditions for FEA at specific time steps
    ///
    /// This is a critical method for FEA integration that provides displacement,
    /// velocity, and acceleration boundary conditions at specified time points.
    pub fn boundary_conditions(&self, time_steps: &[f64]) -> Vec<(f64, f64, f64)> {
        time_steps
            .par_iter()
            .map(|&t| {
                // Convert time to cam angle
                let theta = (t * self.omega * 180.0 / PI) % 360.0;

                let displacement = self.displacement(theta);
                let velocity = self.velocity(theta);
                let acceleration = self.acceleration(theta);

                (displacement, velocity, acceleration)
            })
            .collect()
    }

    /// Optimized method for real-time boundary condition calculation
    ///
    /// This method is designed for maximum performance during FEA simulation
    /// where boundary conditions need to be calculated at every time step.
    #[inline]
    pub fn boundary_condition_at_time(&self, time: f64) -> (f64, f64, f64) {
        let theta = (time * self.omega * 180.0 / PI) % 360.0;
        (
            self.displacement(theta),
            self.velocity(theta),
            self.acceleration(theta),
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_motion_parameters_default() {
        let params = MotionParameters::default();
        assert_eq!(params.base_circle_radius, 25.0);
        assert_eq!(params.max_lift, 10.0);
        assert_eq!(params.rpm, 3000.0);
    }

    #[test]
    fn test_motion_parameters_validation() {
        let mut params = MotionParameters::default();
        assert!(params.validate().is_ok());

        params.max_lift = -1.0;
        assert!(params.validate().is_err());
    }

    #[test]
    fn test_motion_law_creation() {
        let params = MotionParameters::default();
        let motion = MotionLaw::new(params);
        assert!(motion.is_ok());
    }

    #[test]
    fn test_displacement_calculation() {
        let params = MotionParameters::default();
        let motion = MotionLaw::new(params).unwrap();

        // Test at start of rise
        let disp_start = motion.displacement(0.0);
        assert_relative_eq!(disp_start, 0.0, epsilon = 1e-10);

        // Test at end of rise (should be close to max_lift)
        let disp_end_rise = motion.displacement(90.0);
        assert!(disp_end_rise > 9.0 && disp_end_rise <= 10.0);

        // Test during dwell
        let disp_dwell = motion.displacement(120.0);
        assert_relative_eq!(disp_dwell, 10.0, epsilon = 1e-10);
    }

    #[test]
    fn test_velocity_calculation() {
        let params = MotionParameters::default();
        let motion = MotionLaw::new(params).unwrap();

        // Test at start and end of rise (should be zero)
        let vel_start = motion.velocity(0.0);
        let vel_end_rise = motion.velocity(90.0);
        assert_relative_eq!(vel_start, 0.0, epsilon = 1e-6);
        assert_relative_eq!(vel_end_rise, 0.0, epsilon = 1e-6);

        // Test during dwell (should be zero)
        let vel_dwell = motion.velocity(120.0);
        assert_relative_eq!(vel_dwell, 0.0, epsilon = 1e-10);
    }

    #[test]
    fn test_parallel_computation() {
        let params = MotionParameters::default();
        let motion = MotionLaw::new(params).unwrap();

        let angles: Vec<f64> = (0..1000).map(|i| i as f64 * 0.225).collect();

        // Test that parallel and sequential give same results
        let disp_sequential: Vec<f64> = angles.iter().map(|&theta| motion.displacement(theta)).collect();
        let disp_parallel = motion.displacement_parallel(&angles);

        for (seq, par) in disp_sequential.iter().zip(disp_parallel.iter()) {
            assert_relative_eq!(seq, par, epsilon = 1e-12);
        }
    }

    #[test]
    fn test_kinematic_analysis() {
        let params = MotionParameters::default();
        let motion = MotionLaw::new(params).unwrap();

        let analysis = motion.analyze_kinematics(1000);

        assert_eq!(analysis.theta.len(), 1000);
        assert_eq!(analysis.displacement.len(), 1000);
        assert_eq!(analysis.velocity.len(), 1000);
        assert_eq!(analysis.acceleration.len(), 1000);
        assert_eq!(analysis.jerk.len(), 1000);

        assert!(analysis.max_velocity > 0.0);
        assert!(analysis.max_acceleration > 0.0);
        assert!(analysis.rms_acceleration > 0.0);
    }

    #[test]
    fn test_boundary_conditions() {
        let params = MotionParameters::default();
        let motion = MotionLaw::new(params).unwrap();

        let time_steps: Vec<f64> = (0..100).map(|i| i as f64 * 0.001).collect();
        let boundary_conditions = motion.boundary_conditions(&time_steps);

        assert_eq!(boundary_conditions.len(), 100);

        // Test that boundary conditions are reasonable
        for (disp, vel, acc) in boundary_conditions.iter() {
            assert!(disp.is_finite());
            assert!(vel.is_finite());
            assert!(acc.is_finite());
        }
    }

    #[test]
    fn test_boundary_condition_at_time() {
        let params = MotionParameters::default();
        let motion = MotionLaw::new(params).unwrap();

        let (disp, vel, acc) = motion.boundary_condition_at_time(0.01);

        assert!(disp.is_finite());
        assert!(vel.is_finite());
        assert!(acc.is_finite());
        assert!(disp >= 0.0);
    }
}

#[cfg(test)]
mod benchmarks {
    use super::*;
    use std::time::Instant;

    #[test]
    fn benchmark_single_displacement() {
        let params = MotionParameters::default();
        let motion = MotionLaw::new(params).unwrap();

        let start = Instant::now();
        for i in 0..1_000_000 {
            let _ = motion.displacement(i as f64 * 0.0001);
        }
        let duration = start.elapsed();

        println!("Single displacement calculation: {:?} for 1M calls", duration);
        println!("Average per call: {:?}", duration / 1_000_000);
    }

    #[test]
    fn benchmark_parallel_displacement() {
        let params = MotionParameters::default();
        let motion = MotionLaw::new(params).unwrap();

        let angles: Vec<f64> = (0..100_000).map(|i| i as f64 * 0.001).collect();

        let start = Instant::now();
        let _ = motion.displacement_parallel(&angles);
        let duration = start.elapsed();

        println!("Parallel displacement calculation: {:?} for 100K values", duration);
    }
}