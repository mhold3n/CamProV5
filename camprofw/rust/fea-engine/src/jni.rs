//! JNI Interface for the FEA Engine and Motion Law
//!
//! This module provides the JNI interface for the FEA engine and motion law.
//! It allows Kotlin code to call into the Rust implementation.

use jni::JNIEnv;
use jni::objects::{JClass, JString, JObject, JObjectArray, JValue};
use jni::sys::{jlong, jdouble, jint, jobjectArray, jstring, jboolean};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::fs::File;
use std::io::Write;
use std::path::Path;
use serde_json;

use crate::motion_law::{MotionLaw, MotionParameters, KinematicAnalysis};
use crate::error::FEAResult;

// Global storage for motion law instances
lazy_static! {
    static ref MOTION_LAWS: Mutex<HashMap<jlong, Arc<MotionLaw>>> = Mutex::new(HashMap::new());
    static ref NEXT_ID: Mutex<jlong> = Mutex::new(1);
}

/// Get the next available ID for a motion law
fn get_next_id() -> jlong {
    let mut id = NEXT_ID.lock().unwrap();
    let current = *id;
    *id += 1;
    current
}

/// Convert a Java string array to a Rust HashMap
fn string_array_to_map(env: &mut JNIEnv, array: jobjectArray) -> FEAResult<HashMap<String, String>> {
    let array_ref = unsafe { JObjectArray::from_raw(array) };
    let length = env.get_array_length(&array_ref)?;
    if length % 2 != 0 {
        return Err(crate::error::FEAError::JNI("String array length must be even".to_string()));
    }
    
    let mut map = HashMap::new();
    
    for i in 0..(length / 2) {
        let key_obj = env.get_object_array_element(&array_ref, i * 2)?;
        let value_obj = env.get_object_array_element(&array_ref, i * 2 + 1)?;
        
        let key_string = JString::from(key_obj);
        let value_string = JString::from(value_obj);
        
        let key: String = env.get_string(&key_string)?.into();
        let value: String = env.get_string(&value_string)?.into();
        
        map.insert(key, value);
    }
    
    Ok(map)
}

/// Convert a HashMap to a MotionParameters struct
fn map_to_motion_parameters(map: HashMap<String, String>) -> FEAResult<MotionParameters> {
    let base_circle_radius = map.get("base_circle_radius")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(25.0);
    
    let max_lift = map.get("max_lift")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(10.0);
    
    let cam_duration = map.get("cam_duration")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(180.0);
    
    let rise_duration = map.get("rise_duration")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(90.0);
    
    let dwell_duration = map.get("dwell_duration")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(45.0);
    
    let fall_duration = map.get("fall_duration")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(90.0);
    
    let jerk_limit = map.get("jerk_limit")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(1000.0);
    
    let acceleration_limit = map.get("acceleration_limit")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(500.0);
    
    let velocity_limit = map.get("velocity_limit")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(100.0);
    
    let rpm = map.get("rpm")
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(3000.0);
    
    Ok(MotionParameters {
        base_circle_radius,
        max_lift,
        cam_duration,
        rise_duration,
        dwell_duration,
        fall_duration,
        jerk_limit,
        acceleration_limit,
        velocity_limit,
        rpm,
    })
}

/// Get a motion law by ID
fn get_motion_law(id: jlong) -> FEAResult<Arc<MotionLaw>> {
    let motion_laws = MOTION_LAWS.lock().unwrap();
    motion_laws.get(&id)
        .cloned()
        .ok_or_else(|| crate::error::FEAError::JNI(format!("Motion law with ID {} not found", id)))
}

/// Create a new motion law
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_createMotionLawNative(
    mut env: JNIEnv,
    _class: JClass,
    parameters: jobjectArray,
) -> jlong {
    match string_array_to_map(&mut env, parameters)
        .and_then(map_to_motion_parameters)
        .and_then(MotionLaw::new)
    {
        Ok(motion_law) => {
            let id = get_next_id();
            let mut motion_laws = MOTION_LAWS.lock().unwrap();
            motion_laws.insert(id, Arc::new(motion_law));
            id
        }
        Err(e) => {
            let _ = env.throw(format!("Failed to create motion law: {}", e));
            0
        }
    }
}

/// Update motion law parameters
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_updateMotionLawParametersNative(
    mut env: JNIEnv,
    _class: JClass,
    motion_law_id: jlong,
    parameters: jobjectArray,
) {
    match string_array_to_map(&mut env, parameters)
        .and_then(map_to_motion_parameters)
        .and_then(MotionLaw::new)
    {
        Ok(motion_law) => {
            let mut motion_laws = MOTION_LAWS.lock().unwrap();
            motion_laws.insert(motion_law_id, Arc::new(motion_law));
        }
        Err(e) => {
            let _ = env.throw(format!("Failed to update motion law parameters: {}", e));
        }
    }
}

/// Get displacement at a specific angle
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_getDisplacementNative(
    mut env: JNIEnv,
    _class: JClass,
    motion_law_id: jlong,
    angle: jdouble,
) -> jdouble {
    match get_motion_law(motion_law_id) {
        Ok(motion_law) => motion_law.displacement(angle),
        Err(e) => {
            let _ = env.throw(format!("Failed to get displacement: {}", e));
            0.0
        }
    }
}

/// Get velocity at a specific angle
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_getVelocityNative(
    mut env: JNIEnv,
    _class: JClass,
    motion_law_id: jlong,
    angle: jdouble,
) -> jdouble {
    match get_motion_law(motion_law_id) {
        Ok(motion_law) => motion_law.velocity(angle),
        Err(e) => {
            let _ = env.throw(format!("Failed to get velocity: {}", e));
            0.0
        }
    }
}

/// Get acceleration at a specific angle
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_getAccelerationNative(
    mut env: JNIEnv,
    _class: JClass,
    motion_law_id: jlong,
    angle: jdouble,
) -> jdouble {
    match get_motion_law(motion_law_id) {
        Ok(motion_law) => motion_law.acceleration(angle),
        Err(e) => {
            let _ = env.throw(format!("Failed to get acceleration: {}", e));
            0.0
        }
    }
}

/// Get jerk at a specific angle
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_getJerkNative(
    mut env: JNIEnv,
    _class: JClass,
    motion_law_id: jlong,
    angle: jdouble,
) -> jdouble {
    match get_motion_law(motion_law_id) {
        Ok(motion_law) => motion_law.jerk(angle),
        Err(e) => {
            let _ = env.throw(format!("Failed to get jerk: {}", e));
            0.0
        }
    }
}

/// Analyze kinematics
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_analyzeKinematicsNative(
    mut env: JNIEnv,
    _class: JClass,
    motion_law_id: jlong,
    num_points: jint,
    results_file_path: JString,
) {
    let results_file_path: String = match env.get_string(&results_file_path) {
        Ok(s) => s.into(),
        Err(e) => {
            let _ = env.throw(format!("Failed to get results file path: {}", e));
            return;
        }
    };
    
    match get_motion_law(motion_law_id) {
        Ok(motion_law) => {
            let analysis = motion_law.analyze_kinematics(num_points as usize);
            
            // Serialize the analysis to JSON
            match serde_json::to_string_pretty(&analysis) {
                Ok(json) => {
                    // Write the JSON to the results file
                    match File::create(Path::new(&results_file_path)) {
                        Ok(mut file) => {
                            if let Err(e) = file.write_all(json.as_bytes()) {
                                let _ = env.throw(format!("Failed to write to results file: {}", e));
                            }
                        }
                        Err(e) => {
                            let _ = env.throw(format!("Failed to create results file: {}", e));
                        }
                    }
                }
                Err(e) => {
                    let _ = env.throw(format!("Failed to serialize analysis: {}", e));
                }
            }
        }
        Err(e) => {
            let _ = env.throw(format!("Failed to analyze kinematics: {}", e));
        }
    }
}

/// Dispose a motion law
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_disposeMotionLawNative(
    mut env: JNIEnv,
    _class: JClass,
    motion_law_id: jlong,
) {
    let mut motion_laws = MOTION_LAWS.lock().unwrap();
    if motion_laws.remove(&motion_law_id).is_none() {
        let _ = env.throw(format!("Motion law with ID {} not found", motion_law_id));
    }
}

/// Test function to verify that the library is working correctly
/// The function should return 42 as expected by the Kotlin code
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_00024Companion_testNativeLibraryNative(
    _env: JNIEnv,
    _class: JClass,
) -> jint {
    42
}

/// Test function to verify that the FEA library is working correctly
/// The function should return 42 as expected by the Kotlin code
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_fea_FeaEngine_00024Companion_testNativeLibraryNative(
    _env: JNIEnv,
    _class: JClass,
) -> jint {
    42
}

// FEA Engine JNI methods (already implemented in the existing code)
// ...