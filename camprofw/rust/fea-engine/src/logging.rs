//! Logging system for the FEA engine
//!
//! This module provides a logging system that can be used across language boundaries.
//! It supports different log levels, log targets, and log formatters.
//! The logs can be written to files, the console, or custom targets.

use std::fs::{File, OpenOptions};
use std::io::{self, Write};
use std::path::Path;
use std::sync::{Arc, Mutex, Once};
use std::time::{SystemTime, UNIX_EPOCH};
use std::fmt;
use serde::{Serialize, Deserialize};

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

impl fmt::Display for LogLevel {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LogLevel::Trace => write!(f, "TRACE"),
            LogLevel::Debug => write!(f, "DEBUG"),
            LogLevel::Info => write!(f, "INFO"),
            LogLevel::Warn => write!(f, "WARN"),
            LogLevel::Error => write!(f, "ERROR"),
            LogLevel::Fatal => write!(f, "FATAL"),
        }
    }
}

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
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs_f64();
        
        Self {
            level,
            message: message.into(),
            target: target.into(),
            timestamp,
            thread_id: thread_id::get(),
            file: file.into(),
            line,
        }
    }
    
    /// Convert the log record to a JSON string
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_else(|_| {
            format!(
                r#"{{
                    "level": "{}", 
                    "message": "{}", 
                    "target": "{}", 
                    "timestamp": {}, 
                    "thread_id": {}, 
                    "file": "{}", 
                    "line": {}
                }}"#,
                self.level, self.message, self.target, self.timestamp, self.thread_id, self.file, self.line
            )
        })
    }
    
    /// Format the log record as a string
    pub fn format(&self) -> String {
        format!(
            "[{:.6}] [{}] [{}:{}] [{}] {}",
            self.timestamp,
            self.level,
            self.file,
            self.line,
            self.target,
            self.message
        )
    }
}

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

impl LogTarget for ConsoleTarget {
    fn write(&self, record: &LogRecord) {
        let formatted = record.format();
        match record.level {
            LogLevel::Error | LogLevel::Fatal => {
                eprintln!("{}", formatted);
            }
            _ => {
                println!("{}", formatted);
            }
        }
    }
    
    fn flush(&self) {
        io::stdout().flush().ok();
        io::stderr().flush().ok();
    }
}

/// File log target
#[derive(Debug)]
pub struct FileTarget {
    /// File handle
    file: Mutex<File>,
}

impl FileTarget {
    /// Create a new file target
    pub fn new<P: AsRef<Path>>(path: P) -> io::Result<Self> {
        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(path)?;
        
        Ok(Self {
            file: Mutex::new(file),
        })
    }
}

impl LogTarget for FileTarget {
    fn write(&self, record: &LogRecord) {
        if let Ok(mut file) = self.file.lock() {
            let formatted = record.format();
            writeln!(file, "{}", formatted).ok();
        }
    }
    
    fn flush(&self) {
        if let Ok(mut file) = self.file.lock() {
            file.flush().ok();
        }
    }
}

/// JSON file log target
#[derive(Debug)]
pub struct JsonFileTarget {
    /// File handle
    file: Mutex<File>,
}

impl JsonFileTarget {
    /// Create a new JSON file target
    pub fn new<P: AsRef<Path>>(path: P) -> io::Result<Self> {
        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(path)?;
        
        Ok(Self {
            file: Mutex::new(file),
        })
    }
}

impl LogTarget for JsonFileTarget {
    fn write(&self, record: &LogRecord) {
        if let Ok(mut file) = self.file.lock() {
            let json = record.to_json();
            writeln!(file, "{}", json).ok();
        }
    }
    
    fn flush(&self) {
        if let Ok(mut file) = self.file.lock() {
            file.flush().ok();
        }
    }
}

/// Memory log target
#[derive(Debug)]
pub struct MemoryTarget {
    /// Log records
    records: Mutex<Vec<LogRecord>>,
    /// Maximum number of records to keep
    max_records: usize,
}

impl MemoryTarget {
    /// Create a new memory target
    pub fn new(max_records: usize) -> Self {
        Self {
            records: Mutex::new(Vec::with_capacity(max_records)),
            max_records,
        }
    }
    
    /// Get all log records
    pub fn records(&self) -> Vec<LogRecord> {
        if let Ok(records) = self.records.lock() {
            records.clone()
        } else {
            Vec::new()
        }
    }
    
    /// Clear all log records
    pub fn clear(&self) {
        if let Ok(mut records) = self.records.lock() {
            records.clear();
        }
    }
}

impl LogTarget for MemoryTarget {
    fn write(&self, record: &LogRecord) {
        if let Ok(mut records) = self.records.lock() {
            records.push(record.clone());
            if records.len() > self.max_records {
                records.remove(0);
            }
        }
    }
    
    fn flush(&self) {
        // Nothing to do
    }
}

/// Logger
pub struct Logger {
    /// Log targets
    targets: Vec<Arc<dyn LogTarget>>,
    /// Minimum log level
    min_level: LogLevel,
}

impl std::fmt::Debug for Logger {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Logger")
            .field("targets", &format!("{} targets", self.targets.len()))
            .field("min_level", &self.min_level)
            .finish()
    }
}

impl Logger {
    /// Create a new logger
    pub fn new(min_level: LogLevel) -> Self {
        Self {
            targets: Vec::new(),
            min_level,
        }
    }
    
    /// Add a log target
    pub fn add_target(&mut self, target: Arc<dyn LogTarget>) {
        self.targets.push(target);
    }
    
    /// Set the minimum log level
    pub fn set_min_level(&mut self, level: LogLevel) {
        self.min_level = level;
    }
    
    /// Log a message
    pub fn log(&self, record: LogRecord) {
        if record.level >= self.min_level {
            for target in &self.targets {
                target.write(&record);
            }
        }
    }
    
    /// Flush all targets
    pub fn flush(&self) {
        for target in &self.targets {
            target.flush();
        }
    }
}

/// Global logger
static mut LOGGER: Option<Arc<Mutex<Logger>>> = None;
static LOGGER_INIT: Once = Once::new();

/// Initialize the global logger
pub fn init_logger(min_level: LogLevel) {
    LOGGER_INIT.call_once(|| {
        let logger = Logger::new(min_level);
        unsafe {
            LOGGER = Some(Arc::new(Mutex::new(logger)));
        }
    });
}

/// Add a target to the global logger
pub fn add_target(target: Arc<dyn LogTarget>) {
    if let Some(logger) = unsafe { LOGGER.as_ref() } {
        if let Ok(mut logger) = logger.lock() {
            logger.add_target(target);
        }
    }
}

/// Set the minimum log level for the global logger
pub fn set_min_level(level: LogLevel) {
    if let Some(logger) = unsafe { LOGGER.as_ref() } {
        if let Ok(mut logger) = logger.lock() {
            logger.set_min_level(level);
        }
    }
}

/// Log a message to the global logger
pub fn log(record: LogRecord) {
    if let Some(logger) = unsafe { LOGGER.as_ref() } {
        if let Ok(logger) = logger.lock() {
            logger.log(record);
        }
    }
}

/// Flush the global logger
pub fn flush() {
    if let Some(logger) = unsafe { LOGGER.as_ref() } {
        if let Ok(logger) = logger.lock() {
            logger.flush();
        }
    }
}

/// Log a trace message
#[macro_export]
macro_rules! trace {
    ($target:expr, $($arg:tt)*) => {
        $crate::logging::log($crate::logging::LogRecord::new(
            $crate::logging::LogLevel::Trace,
            format!($($arg)*),
            $target,
            file!(),
            line!(),
        ));
    };
}

/// Log a debug message
#[macro_export]
macro_rules! debug {
    ($target:expr, $($arg:tt)*) => {
        $crate::logging::log($crate::logging::LogRecord::new(
            $crate::logging::LogLevel::Debug,
            format!($($arg)*),
            $target,
            file!(),
            line!(),
        ));
    };
}

/// Log an info message
#[macro_export]
macro_rules! info {
    ($target:expr, $($arg:tt)*) => {
        $crate::logging::log($crate::logging::LogRecord::new(
            $crate::logging::LogLevel::Info,
            format!($($arg)*),
            $target,
            file!(),
            line!(),
        ));
    };
}

/// Log a warning message
#[macro_export]
macro_rules! warn {
    ($target:expr, $($arg:tt)*) => {
        $crate::logging::log($crate::logging::LogRecord::new(
            $crate::logging::LogLevel::Warn,
            format!($($arg)*),
            $target,
            file!(),
            line!(),
        ));
    };
}

/// Log an error message
#[macro_export]
macro_rules! error {
    ($target:expr, $($arg:tt)*) => {
        $crate::logging::log($crate::logging::LogRecord::new(
            $crate::logging::LogLevel::Error,
            format!($($arg)*),
            $target,
            file!(),
            line!(),
        ));
    };
}

/// Log a fatal message
#[macro_export]
macro_rules! fatal {
    ($target:expr, $($arg:tt)*) => {
        $crate::logging::log($crate::logging::LogRecord::new(
            $crate::logging::LogLevel::Fatal,
            format!($($arg)*),
            $target,
            file!(),
            line!(),
        ));
    };
}

/// Get the current thread ID
mod thread_id {
    use std::sync::atomic::{AtomicU64, Ordering};
    
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    thread_local! {
        static ID: u64 = COUNTER.fetch_add(1, Ordering::SeqCst);
    }
    
    /// Get the current thread ID
    pub fn get() -> u64 {
        ID.with(|id| *id)
    }
}

/// Initialize the default logger
pub fn init_default_logger() {
    init_logger(LogLevel::Info);
    add_target(Arc::new(ConsoleTarget));
}

/// Initialize a file logger
pub fn init_file_logger<P: AsRef<Path>>(path: P, min_level: LogLevel) -> io::Result<()> {
    init_logger(min_level);
    let target = FileTarget::new(path)?;
    add_target(Arc::new(target));
    Ok(())
}

/// Initialize a JSON file logger
pub fn init_json_file_logger<P: AsRef<Path>>(path: P, min_level: LogLevel) -> io::Result<()> {
    init_logger(min_level);
    let target = JsonFileTarget::new(path)?;
    add_target(Arc::new(target));
    Ok(())
}

/// Initialize a memory logger
pub fn init_memory_logger(max_records: usize, min_level: LogLevel) {
    init_logger(min_level);
    let target = MemoryTarget::new(max_records);
    add_target(Arc::new(target));
}

/// Get the last N log records as a JSON string
pub fn get_last_logs(n: usize) -> String {
    if let Some(logger) = unsafe { LOGGER.as_ref() } {
        if let Ok(logger) = logger.lock() {
            for target in &logger.targets {
                if let Some(memory_target) = target.downcast_ref::<MemoryTarget>() {
                    let records = memory_target.records();
                    let start = if records.len() > n { records.len() - n } else { 0 };
                    let last_records = &records[start..];
                    return serde_json::to_string(last_records).unwrap_or_else(|_| "[]".to_string());
                }
            }
        }
    }
    "[]".to_string()
}

/// Get all log records as a JSON string
pub fn get_all_logs() -> String {
    if let Some(logger) = unsafe { LOGGER.as_ref() } {
        if let Ok(logger) = logger.lock() {
            for target in &logger.targets {
                if let Some(memory_target) = target.downcast_ref::<MemoryTarget>() {
                    let records = memory_target.records();
                    return serde_json::to_string(&records).unwrap_or_else(|_| "[]".to_string());
                }
            }
        }
    }
    "[]".to_string()
}

/// Clear all log records
pub fn clear_logs() {
    if let Some(logger) = unsafe { LOGGER.as_ref() } {
        if let Ok(logger) = logger.lock() {
            for target in &logger.targets {
                if let Some(memory_target) = target.downcast_ref::<MemoryTarget>() {
                    memory_target.clear();
                }
            }
        }
    }
}

/// Trait for downcasting
trait Downcast {
    /// Downcast to a specific type
    fn downcast_ref<T: 'static>(&self) -> Option<&T>;
}

impl<T: 'static> Downcast for T {
    fn downcast_ref<U: 'static>(&self) -> Option<&U> {
        if std::any::TypeId::of::<T>() == std::any::TypeId::of::<U>() {
            unsafe { Some(&*(self as *const T as *const U)) }
        } else {
            None
        }
    }
}