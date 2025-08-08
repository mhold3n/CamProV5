//! Error handling for the FEA engine
//!
//! This module provides error types and utilities for error handling
//! in the FEA engine. It ensures that errors are properly propagated
//! across language boundaries and provides meaningful error messages.

use std::fmt;
use std::error::Error as StdError;
use thiserror::Error;

/// Error type for the FEA engine
#[derive(Error, Debug)]
pub enum FEAError {
    /// Parameter validation error
    #[error("Parameter validation error: {0}")]
    ParameterValidation(String),
    
    /// Calculation error
    #[error("Calculation error: {0}")]
    Calculation(String),
    
    /// I/O error
    #[error("I/O error: {0}")]
    IO(#[from] std::io::Error),
    
    /// Serialization error
    #[error("Serialization error: {0}")]
    Serialization(String),
    
    /// Deserialization error
    #[error("Deserialization error: {0}")]
    Deserialization(String),
    
    /// Boundary condition error
    #[error("Boundary condition error: {0}")]
    BoundaryCondition(String),
    
    /// Simulation error
    #[error("Simulation error: {0}")]
    Simulation(String),
    
    /// JNI error
    #[error("JNI error: {0}")]
    JNI(String),
    
    /// Unknown error
    #[error("Unknown error: {0}")]
    Unknown(String),
}

/// Result type for the FEA engine
pub type FEAResult<T> = Result<T, FEAError>;

/// Convert a string error to a FEAError::ParameterValidation
pub fn parameter_validation_error<S: Into<String>>(msg: S) -> FEAError {
    FEAError::ParameterValidation(msg.into())
}

/// Convert a string error to a FEAError::Calculation
pub fn calculation_error<S: Into<String>>(msg: S) -> FEAError {
    FEAError::Calculation(msg.into())
}

/// Convert a string error to a FEAError::Serialization
pub fn serialization_error<S: Into<String>>(msg: S) -> FEAError {
    FEAError::Serialization(msg.into())
}

/// Convert a string error to a FEAError::Deserialization
pub fn deserialization_error<S: Into<String>>(msg: S) -> FEAError {
    FEAError::Deserialization(msg.into())
}

/// Convert a string error to a FEAError::BoundaryCondition
pub fn boundary_condition_error<S: Into<String>>(msg: S) -> FEAError {
    FEAError::BoundaryCondition(msg.into())
}

/// Convert a string error to a FEAError::Simulation
pub fn simulation_error<S: Into<String>>(msg: S) -> FEAError {
    FEAError::Simulation(msg.into())
}

/// Convert a string error to a FEAError::Unknown
pub fn unknown_error<S: Into<String>>(msg: S) -> FEAError {
    FEAError::Unknown(msg.into())
}

/// Convert a serde_json error to a FEAError
impl From<serde_json::Error> for FEAError {
    fn from(err: serde_json::Error) -> Self {
        if err.is_data() {
            FEAError::Deserialization(format!("JSON data error: {}", err))
        } else if err.is_syntax() {
            FEAError::Deserialization(format!("JSON syntax error: {}", err))
        } else if err.is_eof() {
            FEAError::Deserialization(format!("JSON EOF error: {}", err))
        } else {
            FEAError::Deserialization(format!("JSON error: {}", err))
        }
    }
}

/// Convert a toml error to a FEAError
impl From<toml::de::Error> for FEAError {
    fn from(err: toml::de::Error) -> Self {
        FEAError::Deserialization(format!("TOML deserialization error: {}", err))
    }
}

/// Convert a toml serialization error to a FEAError
impl From<toml::ser::Error> for FEAError {
    fn from(err: toml::ser::Error) -> Self {
        FEAError::Serialization(format!("TOML serialization error: {}", err))
    }
}

/// Convert a JNI error to a FEAError
impl From<jni::errors::Error> for FEAError {
    fn from(err: jni::errors::Error) -> Self {
        FEAError::JNI(format!("JNI error: {}", err))
    }
}

/// Convert a string error to a FEAError
impl From<String> for FEAError {
    fn from(err: String) -> Self {
        FEAError::Unknown(err)
    }
}

/// Convert a &str error to a FEAError
impl From<&str> for FEAError {
    fn from(err: &str) -> Self {
        FEAError::Unknown(err.to_string())
    }
}

/// Error reporting utility
///
/// This struct provides a way to report errors with context information
/// such as the file, line, and function where the error occurred.
#[derive(Debug, serde::Serialize)]
pub struct ErrorReport {
    /// The error message
    pub message: String,
    /// The error type
    pub error_type: String,
    /// The file where the error occurred
    pub file: String,
    /// The line where the error occurred
    pub line: u32,
    /// The function where the error occurred
    pub function: String,
    /// The timestamp when the error occurred
    pub timestamp: String,
}

impl ErrorReport {
    /// Create a new error report
    pub fn new<S: Into<String>>(
        message: S,
        error_type: S,
        file: S,
        line: u32,
        function: S,
    ) -> Self {
        use chrono::prelude::*;
        
        Self {
            message: message.into(),
            error_type: error_type.into(),
            file: file.into(),
            line,
            function: function.into(),
            timestamp: Utc::now().to_rfc3339(),
        }
    }
    
    /// Convert the error report to a JSON string
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_else(|_| {
            format!(
                r#"{{
                    "message": "{}", 
                    "error_type": "{}", 
                    "file": "{}", 
                    "line": {}, 
                    "function": "{}", 
                    "timestamp": "{}"
                }}"#,
                self.message, self.error_type, self.file, self.line, self.function, self.timestamp
            )
        })
    }
}

impl fmt::Display for ErrorReport {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "[{}] {} in {}:{} ({}): {}",
            self.timestamp, self.error_type, self.file, self.line, self.function, self.message
        )
    }
}

/// Macro to create an error report
#[macro_export]
macro_rules! error_report {
    ($message:expr, $error_type:expr) => {
        $crate::error::ErrorReport::new(
            $message,
            $error_type,
            file!(),
            line!(),
            function_name!(),
        )
    };
}

/// Macro to get the current function name
#[macro_export]
macro_rules! function_name {
    () => {{
        fn f() {}
        fn type_name_of<T>(_: T) -> &'static str {
            std::any::type_name::<T>()
        }
        let name = type_name_of(f);
        &name[..name.len() - 3]
    }};
}

/// Macro to log an error
#[macro_export]
macro_rules! log_error {
    ($message:expr, $error_type:expr) => {
        let report = error_report!($message, $error_type);
        eprintln!("{}", report);
        report
    };
}

/// Macro to return an error with an error report
#[macro_export]
macro_rules! return_error {
    ($message:expr, $error_type:expr) => {
        return Err($crate::error::FEAError::from(
            error_report!($message, $error_type).to_string()
        ));
    };
}

/// Macro to panic with an error report
#[macro_export]
macro_rules! panic_error {
    ($message:expr, $error_type:expr) => {
        panic!("{}", error_report!($message, $error_type));
    };
}