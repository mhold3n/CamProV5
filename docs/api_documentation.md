# CamProV5 API Documentation

This document provides comprehensive API documentation for the CamProV5 project, covering both the Python design layer and the Rust simulation layer.

## Table of Contents

1. [Python API](#python-api)
   - [Motion Law](#python-motion-law)
   - [Logging](#python-logging)
   - [Error Handling](#python-error-handling)
2. [Rust API](#rust-api)
   - [Motion Law](#rust-motion-law)
   - [Logging](#rust-logging)
   - [Error Handling](#rust-error-handling)
3. [Integration](#integration)
   - [Parameter Passing](#parameter-passing)
   - [Error Propagation](#error-propagation)
   - [Logging Across Boundaries](#logging-across-boundaries)

## Python API

### Python Motion Law

The Python motion law implementation is located in `campro/models/movement_law.py`. It provides a design laboratory for cam profile development.

#### `MotionParameters` Class

```python
class MotionParameters:
    """
    Motion parameters for cam profile definition.
    
    This class stores the parameters that define a cam profile, including
    base circle radius, maximum lift, cam duration, rise/dwell/fall durations,
    and kinematic limits.
    """
    
    def __init__(
        self,
        base_circle_radius: float = 25.0,
        max_lift: float = 10.0,
        cam_duration: float = 180.0,
        rise_duration: float = 90.0,
        dwell_duration: float = 45.0,
        fall_duration: float = 90.0,
        jerk_limit: float = 1000.0,
        acceleration_limit: float = 500.0,
        velocity_limit: float = 100.0,
        rpm: float = 3000.0
    ):
        """
        Initialize motion parameters.
        
        Args:
            base_circle_radius: Base circle radius in mm
            max_lift: Maximum lift in mm
            cam_duration: Total cam duration in degrees
            rise_duration: Rise duration in degrees
            dwell_duration: Dwell duration in degrees
            fall_duration: Fall duration in degrees
            jerk_limit: Jerk limit in mm/s³
            acceleration_limit: Acceleration limit in mm/s²
            velocity_limit: Velocity limit in mm/s
            rpm: Engine RPM
        """
        # ...
    
    def to_dict(self) -> Dict[str, float]:
        """Convert parameters to a dictionary."""
        # ...
    
    def to_json(self) -> str:
        """Convert parameters to a JSON string."""
        # ...
    
    def to_toml(self) -> str:
        """Convert parameters to a TOML string."""
        # ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "MotionParameters":
        """Create parameters from a dictionary."""
        # ...
    
    @classmethod
    def from_json(cls, json_str: str) -> "MotionParameters":
        """Create parameters from a JSON string."""
        # ...
    
    @classmethod
    def from_toml(cls, toml_str: str) -> "MotionParameters":
        """Create parameters from a TOML string."""
        # ...
```

#### `MotionLaw` Class

```python
class MotionLaw:
    """
    Motion law for cam profile calculation.
    
    This class implements the motion law for cam profile calculation,
    including displacement, velocity, acceleration, and jerk calculations.
    """
    
    def __init__(self, parameters: MotionParameters):
        """
        Initialize motion law.
        
        Args:
            parameters: Motion parameters
        """
        # ...
    
    def displacement(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cam follower displacement.
        
        Args:
            theta: Cam angle in degrees
            
        Returns:
            Displacement in mm
        """
        # ...
    
    def velocity(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cam follower velocity.
        
        Args:
            theta: Cam angle in degrees
            
        Returns:
            Velocity in mm/s
        """
        # ...
    
    def acceleration(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cam follower acceleration.
        
        Args:
            theta: Cam angle in degrees
            
        Returns:
            Acceleration in mm/s²
        """
        # ...
    
    def jerk(self, theta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate cam follower jerk.
        
        Args:
            theta: Cam angle in degrees
            
        Returns:
            Jerk in mm/s³
        """
        # ...
    
    def analyze_kinematics(self, num_points: int = 1000) -> Dict[str, Any]:
        """
        Perform comprehensive kinematic analysis.
        
        Args:
            num_points: Number of points to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # ...
    
    def plot_kinematics(self, save_path: Optional[Path] = None) -> None:
        """
        Plot kinematic analysis results.
        
        Args:
            save_path: Path to save the plot (None for display only)
        """
        # ...
```

#### `MotionOptimizer` Class

```python
class MotionOptimizer:
    """
    Motion parameter optimizer.
    
    This class optimizes motion parameters to minimize acceleration,
    jerk, or other objective functions.
    """
    
    def __init__(self, base_parameters: MotionParameters):
        """
        Initialize motion optimizer.
        
        Args:
            base_parameters: Base motion parameters
        """
        # ...
    
    def objective_function(self, x: np.ndarray, objective_type: str = 'rms_acceleration') -> float:
        """
        Calculate objective function value.
        
        Args:
            x: Parameter vector
            objective_type: Objective function type
            
        Returns:
            Objective function value
        """
        # ...
    
    def optimize(
        self,
        bounds: Optional[List[Tuple[float, float]]] = None,
        objective_type: str = 'rms_acceleration',
        method: str = 'differential_evolution'
    ) -> MotionParameters:
        """
        Optimize motion parameters.
        
        Args:
            bounds: Parameter bounds
            objective_type: Objective function type
            method: Optimization method
            
        Returns:
            Optimized motion parameters
        """
        # ...
```

#### Utility Functions

```python
def export_parameters_for_fea(
    parameters: MotionParameters,
    output_path: Path,
    format_type: str = 'toml'
) -> None:
    """
    Export motion parameters for FEA engine.
    
    Args:
        parameters: Motion parameters
        output_path: Output file path
        format_type: Output format type ('toml' or 'json')
    """
    # ...
```

### Python Logging

The Python logging implementation is located in `campro/utils/logging.py`. It provides a unified logging experience across the Python and Rust components of CamProV5.

#### `LogLevel` Enum

```python
class LogLevel(enum.Enum):
    """Log levels for CamProV5."""
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    FATAL = 5
    
    @classmethod
    def from_string(cls, level: str) -> "LogLevel":
        """Convert a string to a LogLevel."""
        # ...
    
    @classmethod
    def from_python_level(cls, level: int) -> "LogLevel":
        """Convert a Python logging level to a LogLevel."""
        # ...
    
    def to_python_level(self) -> int:
        """Convert a LogLevel to a Python logging level."""
        # ...
```

#### `LogRecord` Class

```python
class LogRecord:
    """Log record for CamProV5."""
    
    def __init__(
        self,
        level: LogLevel,
        message: str,
        target: str,
        timestamp: float,
        thread_id: int,
        file: str,
        line: int,
    ):
        """Initialize a log record."""
        # ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogRecord":
        """Create a log record from a dictionary."""
        # ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert a log record to a dictionary."""
        # ...
    
    def __str__(self) -> str:
        """Convert a log record to a string."""
        # ...
```

#### Logging Functions

```python
def init_logging(
    level: Union[LogLevel, str, int] = LogLevel.INFO,
    console: bool = True,
    file: Optional[Union[str, Path]] = None,
    json_file: Optional[Union[str, Path]] = None,
    memory: bool = True,
    memory_size: int = 1000,
) -> None:
    """
    Initialize the logging system.
    
    Args:
        level: Minimum log level (LogLevel, string, or Python logging level)
        console: Whether to log to console
        file: Path to log file (None to disable)
        json_file: Path to JSON log file (None to disable)
        memory: Whether to keep logs in memory
        memory_size: Maximum number of log records to keep in memory
    """
    # ...

def log(
    level: Union[LogLevel, str, int],
    message: str,
    target: str = "campro",
    file: Optional[str] = None,
    line: Optional[int] = None,
) -> None:
    """
    Log a message.
    
    Args:
        level: Log level (LogLevel, string, or Python logging level)
        message: Log message
        target: Log target (module, file, etc.)
        file: Source file (None for automatic detection)
        line: Source line (None for automatic detection)
    """
    # ...

def trace(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log a trace message."""
    # ...

def debug(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log a debug message."""
    # ...

def info(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log an info message."""
    # ...

def warn(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log a warning message."""
    # ...

def error(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log an error message."""
    # ...

def fatal(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log a fatal message."""
    # ...

def get_logs(n: Optional[int] = None) -> List[LogRecord]:
    """
    Get log records.
    
    Args:
        n: Number of log records to retrieve (None for all)
        
    Returns:
        List of log records
    """
    # ...

def clear_logs() -> None:
    """Clear all log records."""
    # ...
```

### Python Error Handling

The Python error handling implementation is located in `campro/utils/logging.py`. It provides error classes and utilities for handling errors from the Rust implementation.

#### Error Classes

```python
class FEAError(Exception):
    """Base class for FEA engine errors."""
    
    def __init__(self, message: str, error_type: str = "Unknown"):
        """Initialize an FEA error."""
        # ...

class ParameterValidationError(FEAError):
    """Parameter validation error."""
    
    def __init__(self, message: str):
        """Initialize a parameter validation error."""
        # ...

class CalculationError(FEAError):
    """Calculation error."""
    
    def __init__(self, message: str):
        """Initialize a calculation error."""
        # ...

class SerializationError(FEAError):
    """Serialization error."""
    
    def __init__(self, message: str):
        """Initialize a serialization error."""
        # ...

class DeserializationError(FEAError):
    """Deserialization error."""
    
    def __init__(self, message: str):
        """Initialize a deserialization error."""
        # ...

class BoundaryConditionError(FEAError):
    """Boundary condition error."""
    
    def __init__(self, message: str):
        """Initialize a boundary condition error."""
        # ...

class SimulationError(FEAError):
    """Simulation error."""
    
    def __init__(self, message: str):
        """Initialize a simulation error."""
        # ...
```

#### Error Handling Decorator

```python
def handle_fea_errors(func):
    """Decorator to handle FEA engine errors."""
    # ...
```

## Rust API

### Rust Motion Law

The Rust motion law implementation is located in `camprofw/rust/fea-engine/src/motion_law.rs`. It provides a high-performance implementation for FEA simulation.

#### `MotionParameters` Struct

```rust
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

impl MotionParameters {
    /// Validate motion parameters for physical feasibility
    pub fn validate(&self) -> FEAResult<()> {
        // ...
    }
    
    /// Calculate total cam duration
    pub fn total_duration(&self) -> f64 {
        // ...
    }
    
    /// Calculate angular velocity in rad/s
    pub fn omega(&self) -> f64 {
        // ...
    }
}
```

#### `KinematicAnalysis` Struct

```rust
/// Kinematic analysis results
#[derive(Debug, Clone)]
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
```

#### `MotionLaw` Struct

```rust
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
        // ...
    }
    
    /// Get motion parameters
    pub fn parameters(&self) -> &MotionParameters {
        // ...
    }
    
    /// Calculate cam follower displacement for a single angle
    #[inline]
    pub fn displacement(&self, theta: f64) -> f64 {
        // ...
    }
    
    /// Calculate cam follower velocity for a single angle
    #[inline]
    pub fn velocity(&self, theta: f64) -> f64 {
        // ...
    }
    
    /// Calculate cam follower acceleration for a single angle
    #[inline]
    pub fn acceleration(&self, theta: f64) -> f64 {
        // ...
    }
    
    /// Calculate cam follower jerk for a single angle
    #[inline]
    pub fn jerk(&self, theta: f64) -> f64 {
        // ...
    }
    
    /// Calculate displacement for multiple angles in parallel
    pub fn displacement_parallel(&self, theta_values: &[f64]) -> Vec<f64> {
        // ...
    }
    
    /// Calculate velocity for multiple angles in parallel
    pub fn velocity_parallel(&self, theta_values: &[f64]) -> Vec<f64> {
        // ...
    }
    
    /// Calculate acceleration for multiple angles in parallel
    pub fn acceleration_parallel(&self, theta_values: &[f64]) -> Vec<f64> {
        // ...
    }
    
    /// Calculate jerk for multiple angles in parallel
    pub fn jerk_parallel(&self, theta_values: &[f64]) -> Vec<f64> {
        // ...
    }
    
    /// Perform comprehensive kinematic analysis
    pub fn analyze_kinematics(&self, num_points: usize) -> KinematicAnalysis {
        // ...
    }
    
    /// Calculate boundary conditions for FEA at specific time steps
    pub fn boundary_conditions(&self, time_steps: &[f64]) -> Vec<(f64, f64, f64)> {
        // ...
    }
    
    /// Optimized method for real-time boundary condition calculation
    #[inline]
    pub fn boundary_condition_at_time(&self, time: f64) -> (f64, f64, f64) {
        // ...
    }
}
```

### Rust Logging

The Rust logging implementation is located in `camprofw/rust/fea-engine/src/logging.rs`. It provides a logging system that can be used across language boundaries.

#### `LogLevel` Enum

```rust
/// Log level
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum LogLevel {
    /// Trace level (most verbose)
    Trace = 0,
    /// Debug level
    Debug = 1,
    /// Info level
    Info = 2,
    /// Warning level
    Warn = 3,
    /// Error level
    Error = 4,
    /// Fatal level (least verbose)
    Fatal = 5,
}
```

#### `LogRecord` Struct

```rust
/// Log record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogRecord {
    /// Log level
    pub level: LogLevel,
    /// Log message
    pub message: String,
    /// Log target (module, file, etc.)
    pub target: String,
    /// Log timestamp (seconds since UNIX epoch)
    pub timestamp: f64,
    /// Log thread ID
    pub thread_id: u64,
    /// Log file
    pub file: String,
    /// Log line
    pub line: u32,
}

impl LogRecord {
    /// Create a new log record
    pub fn new<S: Into<String>>(
        level: LogLevel,
        message: S,
        target: S,
        file: S,
        line: u32,
    ) -> Self {
        // ...
    }
    
    /// Convert the log record to a JSON string
    pub fn to_json(&self) -> String {
        // ...
    }
    
    /// Format the log record as a string
    pub fn format(&self) -> String {
        // ...
    }
}
```

#### `LogTarget` Trait and Implementations

```rust
/// Log target trait
pub trait LogTarget: Send + Sync {
    /// Write a log record to the target
    fn write(&self, record: &LogRecord);
    
    /// Flush the target
    fn flush(&self);
}

/// Console log target
#[derive(Debug)]
pub struct ConsoleTarget;

/// File log target
#[derive(Debug)]
pub struct FileTarget {
    /// File handle
    file: Mutex<File>,
}

/// JSON file log target
#[derive(Debug)]
pub struct JsonFileTarget {
    /// File handle
    file: Mutex<File>,
}

/// Memory log target
#[derive(Debug)]
pub struct MemoryTarget {
    /// Log records
    records: Mutex<Vec<LogRecord>>,
    /// Maximum number of records to keep
    max_records: usize,
}
```

#### `Logger` Struct

```rust
/// Logger
#[derive(Debug)]
pub struct Logger {
    /// Log targets
    targets: Vec<Arc<dyn LogTarget>>,
    /// Minimum log level
    min_level: LogLevel,
}

impl Logger {
    /// Create a new logger
    pub fn new(min_level: LogLevel) -> Self {
        // ...
    }
    
    /// Add a log target
    pub fn add_target(&mut self, target: Arc<dyn LogTarget>) {
        // ...
    }
    
    /// Set the minimum log level
    pub fn set_min_level(&mut self, level: LogLevel) {
        // ...
    }
    
    /// Log a message
    pub fn log(&self, record: LogRecord) {
        // ...
    }
    
    /// Flush all targets
    pub fn flush(&self) {
        // ...
    }
}
```

#### Logging Functions and Macros

```rust
/// Initialize the global logger
pub fn init_logger(min_level: LogLevel) {
    // ...
}

/// Add a target to the global logger
pub fn add_target(target: Arc<dyn LogTarget>) {
    // ...
}

/// Set the minimum log level for the global logger
pub fn set_min_level(level: LogLevel) {
    // ...
}

/// Log a message to the global logger
pub fn log(record: LogRecord) {
    // ...
}

/// Flush the global logger
pub fn flush() {
    // ...
}

/// Log a trace message
#[macro_export]
macro_rules! trace {
    // ...
}

/// Log a debug message
#[macro_export]
macro_rules! debug {
    // ...
}

/// Log an info message
#[macro_export]
macro_rules! info {
    // ...
}

/// Log a warning message
#[macro_export]
macro_rules! warn {
    // ...
}

/// Log an error message
#[macro_export]
macro_rules! error {
    // ...
}

/// Log a fatal message
#[macro_export]
macro_rules! fatal {
    // ...
}
```

### Rust Error Handling

The Rust error handling implementation is located in `camprofw/rust/fea-engine/src/error.rs`. It provides error types and utilities for error handling in the FEA engine.

#### `FEAError` Enum

```rust
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
    
    /// Unknown error
    #[error("Unknown error: {0}")]
    Unknown(String),
}

/// Result type for the FEA engine
pub type FEAResult<T> = Result<T, FEAError>;
```

#### Error Conversion Functions

```rust
/// Convert a string error to a FEAError::ParameterValidation
pub fn parameter_validation_error<S: Into<String>>(msg: S) -> FEAError {
    // ...
}

/// Convert a string error to a FEAError::Calculation
pub fn calculation_error<S: Into<String>>(msg: S) -> FEAError {
    // ...
}

/// Convert a string error to a FEAError::Serialization
pub fn serialization_error<S: Into<String>>(msg: S) -> FEAError {
    // ...
}

/// Convert a string error to a FEAError::Deserialization
pub fn deserialization_error<S: Into<String>>(msg: S) -> FEAError {
    // ...
}

/// Convert a string error to a FEAError::BoundaryCondition
pub fn boundary_condition_error<S: Into<String>>(msg: S) -> FEAError {
    // ...
}

/// Convert a string error to a FEAError::Simulation
pub fn simulation_error<S: Into<String>>(msg: S) -> FEAError {
    // ...
}

/// Convert a string error to a FEAError::Unknown
pub fn unknown_error<S: Into<String>>(msg: S) -> FEAError {
    // ...
}
```

#### `ErrorReport` Struct

```rust
/// Error reporting utility
///
/// This struct provides a way to report errors with context information
/// such as the file, line, and function where the error occurred.
#[derive(Debug)]
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
        // ...
    }
    
    /// Convert the error report to a JSON string
    pub fn to_json(&self) -> String {
        // ...
    }
}
```

#### Error Handling Macros

```rust
/// Macro to create an error report
#[macro_export]
macro_rules! error_report {
    // ...
}

/// Macro to get the current function name
#[macro_export]
macro_rules! function_name {
    // ...
}

/// Macro to log an error
#[macro_export]
macro_rules! log_error {
    // ...
}

/// Macro to return an error with an error report
#[macro_export]
macro_rules! return_error {
    // ...
}

/// Macro to panic with an error report
#[macro_export]
macro_rules! panic_error {
    // ...
}
```

## Integration

### Parameter Passing

Parameters are passed between the Python and Rust implementations using JSON or TOML files. The Python `MotionParameters` class and the Rust `MotionParameters` struct have compatible serialization/deserialization methods.

#### Python to Rust

```python
# Python code
from campro.models.movement_law import MotionParameters, export_parameters_for_fea
from pathlib import Path

# Create motion parameters
params = MotionParameters(
    base_circle_radius=25.0,
    max_lift=10.0,
    cam_duration=180.0,
    rise_duration=90.0,
    dwell_duration=45.0,
    fall_duration=90.0,
    jerk_limit=1000.0,
    acceleration_limit=500.0,
    velocity_limit=100.0,
    rpm=3000.0
)

# Export parameters for FEA engine
export_parameters_for_fea(params, Path("params.toml"), format_type="toml")
```

```rust
// Rust code
use fea_engine::{load_motion_parameters_from_toml, create_motion_law};
use std::fs;

// Load parameters from file
let toml_str = fs::read_to_string("params.toml").expect("Failed to read file");
let params = load_motion_parameters_from_toml(&toml_str).expect("Failed to parse parameters");

// Create motion law
let motion = create_motion_law(params).expect("Failed to create motion law");
```

#### Rust to Python

```rust
// Rust code
use fea_engine::{MotionParameters, export_motion_parameters_to_toml};
use std::fs;

// Create motion parameters
let params = MotionParameters {
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
};

// Export parameters to file
let toml_str = export_motion_parameters_to_toml(&params).expect("Failed to serialize parameters");
fs::write("params.toml", toml_str).expect("Failed to write file");
```

```python
# Python code
from campro.models.movement_law import MotionParameters
from pathlib import Path

# Load parameters from file
with open("params.toml", "r") as f:
    toml_str = f.read()
params = MotionParameters.from_toml(toml_str)
```

### Error Propagation

Errors are propagated between the Python and Rust implementations using error types and error handling utilities.

#### Rust to Python

```rust
// Rust code
use fea_engine::{FEAError, FEAResult, MotionParameters};

fn validate_parameters(params: &MotionParameters) -> FEAResult<()> {
    if params.max_lift <= 0.0 {
        return Err(FEAError::ParameterValidation("Maximum lift must be positive".to_string()));
    }
    Ok(())
}
```

```python
# Python code
from campro.utils.logging import handle_fea_errors, ParameterValidationError

@handle_fea_errors
def validate_parameters(params):
    # Call Rust function via FFI or subprocess
    # If the Rust function returns an error, the handle_fea_errors decorator
    # will convert it to a Python exception
    pass

try:
    validate_parameters(params)
except ParameterValidationError as e:
    print(f"Parameter validation error: {e}")
```

### Logging Across Boundaries

Logs are shared between the Python and Rust implementations using the logging system.

#### Python to Rust

```python
# Python code
from campro.utils.logging import init_logging, info, error

# Initialize logging
init_logging(level="INFO", console=True, memory=True)

# Log messages
info("Starting simulation")
error("Simulation failed")
```

#### Rust to Python

```rust
// Rust code
use fea_engine::logging::{init_default_logger, info, error};

// Initialize logging
init_default_logger();

// Log messages
info!("fea_engine", "Starting simulation");
error!("fea_engine", "Simulation failed");
```

#### Retrieving Logs

```python
# Python code
from campro.utils.logging import get_logs

# Get logs
logs = get_logs()
for log in logs:
    print(log)
```