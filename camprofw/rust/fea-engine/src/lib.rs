//! High-Performance FEA Engine for CamProV5
//!
//! This crate provides a high-performance Finite Element Analysis (FEA) engine
//! optimized for cam profile simulation. It is designed to work with the Python
//! design layer of CamProV5, providing native Rust implementations of performance-critical
//! components.
//!
//! # Architecture
//!
//! The FEA engine is part of a multi-language architecture:
//!
//! - **Design & Analysis Layer (Python)**: For rapid iteration, visualization, and optimization
//! - **High-Performance Simulation Layer (Rust)**: For efficient FEA computation
//! - **Orchestration & Visualization Layer (Python + Kotlin/Scala)**: For workflow management
//!
//! # Key Features
//!
//! - Native motion law implementation for maximum performance
//! - Mathematical equivalence with Python design layer
//! - Memory-efficient data structures for large simulations
//! - Parallel computation support via rayon
//! - Real-time boundary condition calculation

// Import crates
#[macro_use]
extern crate lazy_static;

// Export modules
pub mod motion_law;
pub mod error;
pub mod logging;
pub mod jni;

// Re-export types
pub use motion_law::{MotionLaw, MotionParameters, KinematicAnalysis};
pub use error::{FEAError, FEAResult, ErrorReport};
pub use logging::{LogLevel, LogRecord, init_default_logger, init_file_logger, init_json_file_logger, init_memory_logger, get_last_logs, get_all_logs, clear_logs};

/// Version information
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Load motion parameters from a TOML file
pub fn load_motion_parameters_from_toml(toml_str: &str) -> FEAResult<MotionParameters> {
    toml::from_str(toml_str)
        .map_err(|e| FEAError::Deserialization(format!("Failed to parse TOML: {}", e)))
}

/// Load motion parameters from a JSON file
pub fn load_motion_parameters_from_json(json_str: &str) -> FEAResult<MotionParameters> {
    serde_json::from_str(json_str)
        .map_err(|e| FEAError::Deserialization(format!("Failed to parse JSON: {}", e)))
}

/// Create a new motion law from parameters
pub fn create_motion_law(params: MotionParameters) -> FEAResult<MotionLaw> {
    MotionLaw::new(params)
}

/// Export motion parameters to TOML
pub fn export_motion_parameters_to_toml(params: &MotionParameters) -> FEAResult<String> {
    toml::to_string(params)
        .map_err(|e| FEAError::Serialization(format!("Failed to serialize to TOML: {}", e)))
}

/// Export motion parameters to JSON
pub fn export_motion_parameters_to_json(params: &MotionParameters) -> FEAResult<String> {
    serde_json::to_string_pretty(params)
        .map_err(|e| FEAError::Serialization(format!("Failed to serialize to JSON: {}", e)))
}

/// Get the last error as a JSON string
pub fn get_last_error() -> String {
    // This is a placeholder for a more sophisticated error reporting system
    // In a real implementation, we would maintain a thread-local error log
    // and return the last error from it
    "{\"error\": \"No error information available\"}".to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_load_motion_parameters_from_toml() {
        let toml_str = r#"
            base_circle_radius = 25.0
            max_lift = 10.0
            cam_duration = 180.0
            rise_duration = 90.0
            dwell_duration = 45.0
            fall_duration = 90.0
            jerk_limit = 1000.0
            acceleration_limit = 500.0
            velocity_limit = 100.0
            rpm = 3000.0
        "#;

        let params = load_motion_parameters_from_toml(toml_str).unwrap();
        assert_eq!(params.base_circle_radius, 25.0);
        assert_eq!(params.max_lift, 10.0);
        assert_eq!(params.rpm, 3000.0);
    }

    #[test]
    fn test_load_motion_parameters_from_json() {
        let json_str = r#"
        {
            "base_circle_radius": 25.0,
            "max_lift": 10.0,
            "cam_duration": 180.0,
            "rise_duration": 90.0,
            "dwell_duration": 45.0,
            "fall_duration": 90.0,
            "jerk_limit": 1000.0,
            "acceleration_limit": 500.0,
            "velocity_limit": 100.0,
            "rpm": 3000.0
        }
        "#;

        let params = load_motion_parameters_from_json(json_str).unwrap();
        assert_eq!(params.base_circle_radius, 25.0);
        assert_eq!(params.max_lift, 10.0);
        assert_eq!(params.rpm, 3000.0);
    }

    #[test]
    fn test_create_motion_law() {
        let params = MotionParameters::default();
        let motion = create_motion_law(params).unwrap();
        
        // Test displacement calculation
        let disp = motion.displacement(45.0);
        assert!(disp > 0.0 && disp < 10.0);
        
        // Test velocity at start (should be zero)
        let vel = motion.velocity(0.0);
        assert_relative_eq!(vel, 0.0, epsilon = 1e-10);
    }
    
    #[test]
    fn test_parameter_validation() {
        // Test invalid parameters
        let invalid_params = MotionParameters {
            max_lift: -10.0, // Invalid: negative lift
            ..MotionParameters::default()
        };
        
        let result = create_motion_law(invalid_params);
        assert!(result.is_err());
        
        if let Err(err) = result {
            match err {
                FEAError::ParameterValidation(msg) => {
                    assert!(msg.contains("Maximum lift must be positive"));
                },
                _ => panic!("Expected ParameterValidation error, got {:?}", err),
            }
        }
    }
    
    #[test]
    fn test_export_parameters() {
        let params = MotionParameters::default();
        
        // Test TOML export
        let toml_str = export_motion_parameters_to_toml(&params).unwrap();
        assert!(toml_str.contains("base_circle_radius"));
        assert!(toml_str.contains("max_lift"));
        
        // Test JSON export
        let json_str = export_motion_parameters_to_json(&params).unwrap();
        assert!(json_str.contains("base_circle_radius"));
        assert!(json_str.contains("max_lift"));
        
        // Round-trip test
        let params2 = load_motion_parameters_from_toml(&toml_str).unwrap();
        assert_eq!(params.base_circle_radius, params2.base_circle_radius);
        assert_eq!(params.max_lift, params2.max_lift);
        
        let params3 = load_motion_parameters_from_json(&json_str).unwrap();
        assert_eq!(params.base_circle_radius, params3.base_circle_radius);
        assert_eq!(params.max_lift, params3.max_lift);
    }
}