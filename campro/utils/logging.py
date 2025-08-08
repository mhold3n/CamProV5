"""
Logging utilities for CamProV5.

This module provides logging utilities for CamProV5, including:
- Logging to console, file, and memory
- Configuring log levels
- Error handling and reporting

This is a simplified version that only uses Python's built-in logging functionality.
"""

import os
import json
import enum
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# Set up Python logging
logger = logging.getLogger("campro")
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# In-memory log storage
memory_logs = []
memory_size_limit = 1000

# Log levels
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
        level = level.upper()
        if level == "TRACE":
            return cls.TRACE
        elif level == "DEBUG":
            return cls.DEBUG
        elif level == "INFO":
            return cls.INFO
        elif level == "WARN" or level == "WARNING":
            return cls.WARN
        elif level == "ERROR":
            return cls.ERROR
        elif level == "FATAL" or level == "CRITICAL":
            return cls.FATAL
        else:
            raise ValueError(f"Invalid log level: {level}")

    @classmethod
    def from_python_level(cls, level: int) -> "LogLevel":
        """Convert a Python logging level to a LogLevel."""
        if level <= logging.DEBUG:
            return cls.DEBUG
        elif level <= logging.INFO:
            return cls.INFO
        elif level <= logging.WARNING:
            return cls.WARN
        elif level <= logging.ERROR:
            return cls.ERROR
        else:
            return cls.FATAL

    def to_python_level(self) -> int:
        """Convert a LogLevel to a Python logging level."""
        if self == LogLevel.TRACE:
            return 5  # Lower than DEBUG
        elif self == LogLevel.DEBUG:
            return logging.DEBUG
        elif self == LogLevel.INFO:
            return logging.INFO
        elif self == LogLevel.WARN:
            return logging.WARNING
        elif self == LogLevel.ERROR:
            return logging.ERROR
        elif self == LogLevel.FATAL:
            return logging.CRITICAL
        else:
            return logging.NOTSET


# Log record
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
        self.level = level
        self.message = message
        self.target = target
        self.timestamp = timestamp
        self.thread_id = thread_id
        self.file = file
        self.line = line

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogRecord":
        """Create a log record from a dictionary."""
        return cls(
            level=LogLevel.from_string(data["level"]),
            message=data["message"],
            target=data["target"],
            timestamp=data["timestamp"],
            thread_id=data["thread_id"],
            file=data["file"],
            line=data["line"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert a log record to a dictionary."""
        return {
            "level": self.level.name,
            "message": self.message,
            "target": self.target,
            "timestamp": self.timestamp,
            "thread_id": self.thread_id,
            "file": self.file,
            "line": self.line,
        }

    def __str__(self) -> str:
        """Convert a log record to a string."""
        dt = datetime.fromtimestamp(self.timestamp)
        return f"[{dt.isoformat()}] [{self.level.name}] [{self.file}:{self.line}] [{self.target}] {self.message}"


# Initialize the Python logging system
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
    global memory_logs, memory_size_limit
    
    # Convert level to LogLevel
    if isinstance(level, str):
        level = LogLevel.from_string(level)
    elif isinstance(level, int):
        level = LogLevel.from_python_level(level)

    # Set Python logging level
    logger.setLevel(level.to_python_level())
    
    # Configure console logging
    if not console:
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                logger.removeHandler(handler)
    
    # Configure file logging
    if file:
        file_handler = logging.FileHandler(file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Configure JSON file logging
    if json_file:
        json_handler = logging.FileHandler(json_file)
        json_handler.setFormatter(logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'))
        logger.addHandler(json_handler)
    
    # Configure memory logging
    memory_logs = []
    memory_size_limit = memory_size if memory else 0
    
    logger.info(f"Logging initialized: level={level.name}, console={console}, file={file}, json_file={json_file}, memory={memory}")


# Log a message
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
    global memory_logs
    
    # Convert level to LogLevel
    if isinstance(level, str):
        level = LogLevel.from_string(level)
    elif isinstance(level, int):
        level = LogLevel.from_python_level(level)

    # Log to Python logger
    logger.log(level.to_python_level(), message)

    # Get file and line if not provided
    if file is None or line is None:
        import inspect
        frame = inspect.currentframe()
        if frame:
            frame = frame.f_back
            if frame:
                file = file or frame.f_code.co_filename
                line = line or frame.f_lineno
    
    # Store in memory if enabled
    if memory_size_limit > 0:
        # Create a log record
        log_record = LogRecord(
            level=level,
            message=message,
            target=target,
            timestamp=datetime.now().timestamp(),
            thread_id=0,  # Not tracking thread IDs in this simplified version
            file=file or "",
            line=line or 0,
        )
        
        # Add to memory logs
        memory_logs.append(log_record)
        
        # Trim if exceeding limit
        if len(memory_logs) > memory_size_limit:
            memory_logs = memory_logs[-memory_size_limit:]


# Convenience functions for logging at different levels
def trace(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log a trace message."""
    log(LogLevel.TRACE, message, target, file, line)


def debug(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log a debug message."""
    log(LogLevel.DEBUG, message, target, file, line)


def info(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log an info message."""
    log(LogLevel.INFO, message, target, file, line)


def warn(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log a warning message."""
    log(LogLevel.WARN, message, target, file, line)


def error(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log an error message."""
    log(LogLevel.ERROR, message, target, file, line)


def fatal(message: str, target: str = "campro", file: Optional[str] = None, line: Optional[int] = None) -> None:
    """Log a fatal message."""
    log(LogLevel.FATAL, message, target, file, line)


# Get logs
def get_logs(n: Optional[int] = None) -> List[LogRecord]:
    """
    Get log records.

    Args:
        n: Number of log records to retrieve (None for all)

    Returns:
        List of log records
    """
    global memory_logs
    
    if not memory_logs:
        return []
    
    if n is None:
        return memory_logs.copy()
    else:
        return memory_logs[-n:].copy()


# Clear logs
def clear_logs() -> None:
    """Clear all log records."""
    global memory_logs
    memory_logs = []
    logger.info("Cleared all log records from memory")


# Error handling
class FEAError(Exception):
    """Base class for FEA engine errors."""

    def __init__(self, message: str, error_type: str = "Unknown"):
        """Initialize an FEA error."""
        self.message = message
        self.error_type = error_type
        super().__init__(f"{error_type}: {message}")


class ParameterValidationError(FEAError):
    """Parameter validation error."""

    def __init__(self, message: str):
        """Initialize a parameter validation error."""
        super().__init__(message, "ParameterValidation")


class CalculationError(FEAError):
    """Calculation error."""

    def __init__(self, message: str):
        """Initialize a calculation error."""
        super().__init__(message, "Calculation")


class SerializationError(FEAError):
    """Serialization error."""

    def __init__(self, message: str):
        """Initialize a serialization error."""
        super().__init__(message, "Serialization")


class DeserializationError(FEAError):
    """Deserialization error."""

    def __init__(self, message: str):
        """Initialize a deserialization error."""
        super().__init__(message, "Deserialization")


class BoundaryConditionError(FEAError):
    """Boundary condition error."""

    def __init__(self, message: str):
        """Initialize a boundary condition error."""
        super().__init__(message, "BoundaryCondition")


class SimulationError(FEAError):
    """Simulation error."""

    def __init__(self, message: str):
        """Initialize a simulation error."""
        super().__init__(message, "Simulation")


# Error handling decorator
def handle_fea_errors(func):
    """Decorator to handle FEA engine errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            # Parse the error message from the Rust binary
            error_msg = e.stderr.strip()
            if "ParameterValidation" in error_msg:
                raise ParameterValidationError(error_msg)
            elif "Calculation" in error_msg:
                raise CalculationError(error_msg)
            elif "Serialization" in error_msg:
                raise SerializationError(error_msg)
            elif "Deserialization" in error_msg:
                raise DeserializationError(error_msg)
            elif "BoundaryCondition" in error_msg:
                raise BoundaryConditionError(error_msg)
            elif "Simulation" in error_msg:
                raise SimulationError(error_msg)
            else:
                raise FEAError(error_msg)
        except Exception as e:
            # Re-raise other exceptions
            raise e
    return wrapper


# Initialize default logging
init_logging()