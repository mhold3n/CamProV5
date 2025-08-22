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
use crate::litvin::{self, LitvinParameters, LitvinTables, PitchCurves, PlanetState};

// Global storage for motion law instances
lazy_static! {
    static ref MOTION_LAWS: Mutex<HashMap<jlong, Arc<MotionLaw>>> = Mutex::new(HashMap::new());
    static ref NEXT_ID: Mutex<jlong> = Mutex::new(1);
    // Separate store for Litvin tables
    static ref LITVIN_TABLES: Mutex<HashMap<jlong, Arc<LitvinTables>>> = Mutex::new(HashMap::new());
    // Temp directories per Litvin ID (for JSON file cleanup)
    static ref LITVIN_TMPDIRS: Mutex<HashMap<jlong, std::path::PathBuf>> = Mutex::new(HashMap::new());
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

// -----------------------------
// Litvin JNI bridge (Phase 2)
// -----------------------------

fn map_to_litvin_parameters(mut map: HashMap<String, String>) -> FEAResult<LitvinParameters> {
    fn get_f(map: &mut HashMap<String, String>, k: &str, d: f64) -> f64 {
        map.remove(k).and_then(|s| s.parse::<f64>().ok()).unwrap_or(d)
    }
    fn get_i(map: &mut HashMap<String, String>, k: &str, d: i32) -> i32 {
        map.remove(k).and_then(|s| s.parse::<i32>().ok()).unwrap_or(d)
    }
    let def = LitvinParameters::default();

    // take and normalize ramp_profile first via remove (no immutable borrow)
    let ramp_profile = match map.remove("ramp_profile").map(|s| s.to_lowercase()) {
        Some(s) if s == "cycloidal" => litvin::RampProfile::Cycloidal,
        Some(s) if s == "s7" => litvin::RampProfile::S7,
        _ => litvin::RampProfile::S5,
    };

    let up_fraction = get_f(&mut map, "up_fraction", def.up_fraction);
    let dwell_tdc_deg = get_f(&mut map, "dwell_tdc_deg", def.dwell_tdc_deg);
    let dwell_bdc_deg = get_f(&mut map, "dwell_bdc_deg", def.dwell_bdc_deg);
    let ramp_before_tdc_deg = get_f(&mut map, "ramp_before_tdc_deg", def.ramp_before_tdc_deg);
    let ramp_after_tdc_deg = get_f(&mut map, "ramp_after_tdc_deg", def.ramp_after_tdc_deg);
    let ramp_before_bdc_deg = get_f(&mut map, "ramp_before_bdc_deg", def.ramp_before_bdc_deg);
    let ramp_after_bdc_deg = get_f(&mut map, "ramp_after_bdc_deg", def.ramp_after_bdc_deg);
    let rod_length = get_f(&mut map, "rod_length", def.rod_length);
    let interference_buffer = get_f(&mut map, "interference_buffer", def.interference_buffer);
    let journal_radius = get_f(&mut map, "journal_radius", def.journal_radius);
    let journal_phase_beta_deg = get_f(&mut map, "journal_phase_beta_deg", def.journal_phase_beta_deg);
    let slider_axis_deg = get_f(&mut map, "slider_axis_deg", def.slider_axis_deg);
    let planet_count = get_i(&mut map, "planet_count", def.planet_count);
    let carrier_offset_deg = get_f(&mut map, "carrier_offset_deg", def.carrier_offset_deg);
    let ring_thickness_visual = get_f(&mut map, "ring_thickness_visual", def.ring_thickness_visual);
    let sampling_step_deg = get_f(&mut map, "sampling_step_deg", def.sampling_step_deg);
    let rpm = get_f(&mut map, "rpm", def.rpm);
    let cam_r0 = get_f(&mut map, "cam_r0", def.cam_r0);
    let cam_k_per_unit = get_f(&mut map, "cam_k_per_unit", def.cam_k_per_unit);
    let center_distance_bias = get_f(&mut map, "center_distance_bias", def.center_distance_bias);
    let center_distance_scale = get_f(&mut map, "center_distance_scale", def.center_distance_scale);

    let arc_residual_tol_mm = get_f(&mut map, "arc_residual_tol_mm", def.arc_residual_tol_mm);
    let max_iter = get_i(&mut map, "max_iter", def.max_iter);

    let params = LitvinParameters {
        up_fraction,
        dwell_tdc_deg,
        dwell_bdc_deg,
        ramp_before_tdc_deg,
        ramp_after_tdc_deg,
        ramp_before_bdc_deg,
        ramp_after_bdc_deg,
        ramp_profile,
        rod_length,
        interference_buffer,
        journal_radius,
        journal_phase_beta_deg,
        slider_axis_deg,
        planet_count,
        carrier_offset_deg,
        ring_thickness_visual,
        sampling_step_deg,
        rpm,
        cam_r0,
        cam_k_per_unit,
        center_distance_bias,
        center_distance_scale,
        arc_residual_tol_mm,
        max_iter,
    };
    params.validate().map_err(|e| crate::error::FEAError::JNI(e))?;
    Ok(params)
}

fn ensure_tmp_dir_for_id(id: jlong) -> std::path::PathBuf {
    use std::fs;
    let mut map = LITVIN_TMPDIRS.lock().unwrap();
    if let Some(p) = map.get(&id) { return p.clone(); }
    let dir = std::env::temp_dir().join(format!("campro_litvin_{}", id));
    let _ = fs::create_dir_all(&dir);
    map.insert(id, dir.clone());
    dir
}

fn write_pitch_curves_json(path: &Path, curves: &PitchCurves) -> std::io::Result<()> {
    use std::time::Instant;
    let t0 = Instant::now();
    let json = serde_json::json!({
        "theta": curves.theta_deg,
        "rCam": curves.r_cam,
        "phi": curves.phi_deg,
        "rRing": curves.r_ring,
        "sCam": curves.s_cam,
        "sRing": curves.s_ring,
        "phiOfTheta": curves.phi_of_theta_deg,
    });
    let mut file = File::create(path)?;
    let data = serde_json::to_string_pretty(&json).unwrap();
    file.write_all(data.as_bytes())?;
    let ms = t0.elapsed().as_secs_f64() * 1000.0;
    println!("[PERF][JNI] write_pitch_curves_json: bytes={}, ms={:.3}", data.len(), ms);
    Ok(())
}

fn write_tables_json(path: &Path, tables: &LitvinTables) -> std::io::Result<()> {
    use std::time::Instant;
    let t0 = Instant::now();

    // Sanity: all per-planet arrays must equal alpha_deg length
    let n = tables.alpha_deg.len();
    for (pi, p) in tables.planets.iter().enumerate() {
        if p.center_x.len() != n || p.center_y.len() != n || p.spin_psi_deg.len() != n
            || p.journal_x.len() != n || p.journal_y.len() != n || p.piston_s.len() != n {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                format!("LitvinTables planet {} arrays length mismatch with alphaDeg ({}).", pi, n)
            ));
        }
    }

    let planets: Vec<serde_json::Value> = tables.planets.iter().map(|p| serde_json::json!({
        "centerX": p.center_x,
        "centerY": p.center_y,
        "spinPsiDeg": p.spin_psi_deg,
        "journalX": p.journal_x,
        "journalY": p.journal_y,
        "pistonS": p.piston_s,
    })).collect();

    let diag = &tables.diagnostics;
    let json = serde_json::json!({
        // Force params to be a flat object; fallback to {} to preserve shape
        "params": match serde_json::to_value(&tables.params) {
            Ok(v) if v.is_object() => v,
            _ => serde_json::json!({}),
        },
        "alphaDeg": tables.alpha_deg,
        "planets": planets,
        // Optional curves block included for cross-implementation tests (DTOs ignore unknown fields)
        "curves": {
            "phiOfTheta": tables.curves.phi_of_theta_deg,
        },
        "diagnostics": {
            "version": "1.0",
            "arcLengthResidualMax": diag.arc_length_residual_max,
            "arcLengthResidualRms": diag.arc_length_residual_rms,
            "iterCount": diag.iter_count,
            "usedMaxIter": diag.used_max_iter,
            "regularizationApplied": diag.regularization_applied,
            "clearanceMin": diag.clearance_min,
            "clearanceViolations": diag.clearance_violations.iter().map(|v| serde_json::json!({
                "alphaStartDeg": v.alpha_start_deg,
                "alphaEndDeg": v.alpha_end_deg,
                "minClearance": v.min_clearance,
            })).collect::<Vec<_>>(),
            "envelopeClearanceMin": diag.envelope_clearance_min,
            "envelopeViolations": diag.envelope_violations.iter().map(|v| serde_json::json!({
                "alphaStartDeg": v.alpha_start_deg,
                "alphaEndDeg": v.alpha_end_deg,
                "minClearance": v.min_clearance,
            })).collect::<Vec<_>>(),
            "toothThicknessMin": diag.tooth_thickness_min,
            "undercutFlag": diag.undercut_flag,
            "curvatureRadiusMin": diag.curvature_radius_min,
            "trackingRms": diag.tracking_rms,
            "accelMax": diag.accel_max,
            "jerkMax": diag.jerk_max,
            "slidingVelMean": diag.sliding_vel_mean,
            "slidingVelMax": diag.sliding_vel_max,
            "nvhPeaks": diag.nvh_peaks.iter().map(|p| serde_json::json!({
                "freqHz": p.freq_hz,
                "amp": p.amp
            })).collect::<Vec<_>>(),
            "notes": diag.notes,
            "suggestedCenterDistanceInflation": diag.suggested_center_distance_inflation,
            "buildMs": diag.build_ms
        }
    });
    let mut file = File::create(path)?;
    let data = serde_json::to_string_pretty(&json).unwrap();
    file.write_all(data.as_bytes())?;
    let ms = t0.elapsed().as_secs_f64() * 1000.0;
    println!("[PERF][JNI] write_tables_json: bytes={}, ms={:.3}", data.len(), ms);
    Ok(())
}

fn write_state_json(path: &Path, alpha_deg: f64, tables: &LitvinTables) -> std::io::Result<()> {
    use std::time::Instant;
    let t0 = Instant::now();
    // nearest index
    let n = tables.alpha_deg.len();
    let step = if n > 1 { tables.alpha_deg[1] - tables.alpha_deg[0] } else { 1.0 };
    let mut idx = if step > 0.0 { ((alpha_deg / step).round() as isize).rem_euclid(n as isize) as usize } else { 0 };
    if idx >= n { idx = n - 1; }

    // Sanity guard: ensure per-planet arrays match alphaDeg length
    let expected_len = n;
    for (pi, p) in tables.planets.iter().enumerate() {
        debug_assert_eq!(p.center_x.len(), expected_len, "center_x length mismatch for planet {}", pi);
        debug_assert_eq!(p.center_y.len(), expected_len, "center_y length mismatch for planet {}", pi);
        debug_assert_eq!(p.spin_psi_deg.len(), expected_len, "spin_psi_deg length mismatch for planet {}", pi);
        debug_assert_eq!(p.journal_x.len(), expected_len, "journal_x length mismatch for planet {}", pi);
        debug_assert_eq!(p.journal_y.len(), expected_len, "journal_y length mismatch for planet {}", pi);
        debug_assert_eq!(p.piston_s.len(), expected_len, "piston_s length mismatch for planet {}", pi);
    }

    let mut center_x = Vec::with_capacity(tables.planets.len());
    let mut center_y = Vec::with_capacity(tables.planets.len());
    let mut spin = Vec::with_capacity(tables.planets.len());
    let mut jx = Vec::with_capacity(tables.planets.len());
    let mut jy = Vec::with_capacity(tables.planets.len());
    let mut pist = Vec::with_capacity(tables.planets.len());
    for p in &tables.planets {
        center_x.push(p.center_x[idx]);
        center_y.push(p.center_y[idx]);
        spin.push(p.spin_psi_deg[idx]);
        jx.push(p.journal_x[idx]);
        jy.push(p.journal_y[idx]);
        pist.push(p.piston_s[idx]);
    }

    let json = serde_json::json!({
        "alphaDeg": tables.alpha_deg[idx],
        // Optional context fields (safe additions per DTO stability policy)
        "requestedAlphaDeg": alpha_deg,
        "alphaIndex": idx,
        "centerX": center_x,
        "centerY": center_y,
        "spinPsiDeg": spin,
        "journalX": jx,
        "journalY": jy,
        "pistonS": pist,
    });
    let mut file = File::create(path)?;
    let data = serde_json::to_string_pretty(&json).unwrap();
    file.write_all(data.as_bytes())?;
    let ms = t0.elapsed().as_secs_f64() * 1000.0;
    println!("[PERF][JNI] write_state_json: bytes={}, ms={:.3}", data.len(), ms);
    Ok(())
}

fn get_litvin_tables(id: jlong) -> FEAResult<Arc<LitvinTables>> {
    let map = LITVIN_TABLES.lock().unwrap();
    map.get(&id).cloned().ok_or_else(|| crate::error::FEAError::JNI(format!("Litvin law with ID {} not found", id)))
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_LitvinNative_createLitvinLawNative(
    mut env: JNIEnv,
    _class: JClass,
    parameters: jobjectArray,
) -> jlong {
    let res = string_array_to_map(&mut env, parameters)
        .and_then(map_to_litvin_parameters)
        .and_then(|p| litvin::build_litvin_tables(&p).map_err(|e| crate::error::FEAError::JNI(e)));
    match res {
        Ok(tables) => {
            let id = get_next_id();
            LITVIN_TABLES.lock().unwrap().insert(id, Arc::new(tables));
            // ensure tmp dir
            let _ = ensure_tmp_dir_for_id(id);
            id
        }
        Err(e) => { let _ = env.throw(format!("Failed to create Litvin law: {}", e)); 0 }
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_LitvinNative_updateLitvinLawParametersNative(
    mut env: JNIEnv,
    _class: JClass,
    id: jlong,
    parameters: jobjectArray,
) {
    let res = string_array_to_map(&mut env, parameters)
        .and_then(map_to_litvin_parameters)
        .and_then(|p| litvin::build_litvin_tables(&p).map_err(|e| crate::error::FEAError::JNI(e)));
    match res {
        Ok(tables) => { LITVIN_TABLES.lock().unwrap().insert(id, Arc::new(tables)); }
        Err(e) => { let _ = env.throw(format!("Failed to update Litvin law: {}", e)); }
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_LitvinNative_getLitvinPitchCurvesNative(
    mut env: JNIEnv,
    _class: JClass,
    id: jlong,
) -> jstring {
    match get_litvin_tables(id) {
        Ok(tables) => {
            let dir = ensure_tmp_dir_for_id(id);
            let path = dir.join("pitch_curves.json");
            if let Err(e) = write_pitch_curves_json(&path, &tables.curves) {
                let _ = env.throw(format!("Failed to write pitch curves JSON: {}", e));
                return std::ptr::null_mut();
            }
            env.new_string(path.to_string_lossy().to_string()).map(|s| s.into_raw()).unwrap_or(std::ptr::null_mut())
        }
        Err(e) => { let _ = env.throw(format!("Failed to get Litvin tables: {}", e)); std::ptr::null_mut() }
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_LitvinNative_getLitvinKinematicsTablesNative(
    mut env: JNIEnv,
    _class: JClass,
    id: jlong,
) -> jstring {
    match get_litvin_tables(id) {
        Ok(tables) => {
            let dir = ensure_tmp_dir_for_id(id);
            let path = dir.join("litvin_tables.json");
            if let Err(e) = write_tables_json(&path, &tables) {
                let _ = env.throw(format!("Failed to write kinematics tables JSON: {}", e));
                return std::ptr::null_mut();
            }
            env.new_string(path.to_string_lossy().to_string()).map(|s| s.into_raw()).unwrap_or(std::ptr::null_mut())
        }
        Err(e) => { let _ = env.throw(format!("Failed to get Litvin tables: {}", e)); std::ptr::null_mut() }
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_LitvinNative_getLitvinSystemStateNative(
    mut env: JNIEnv,
    _class: JClass,
    id: jlong,
    alpha_deg: jdouble,
) -> jstring {
    match get_litvin_tables(id) {
        Ok(tables) => {
            let dir = ensure_tmp_dir_for_id(id);
            let path = dir.join("state.json");
            if let Err(e) = write_state_json(&path, alpha_deg, &tables) {
                let _ = env.throw(format!("Failed to write system state JSON: {}", e));
                return std::ptr::null_mut();
            }
            env.new_string(path.to_string_lossy().to_string()).map(|s| s.into_raw()).unwrap_or(std::ptr::null_mut())
        }
        Err(e) => { let _ = env.throw(format!("Failed to get Litvin tables: {}", e)); std::ptr::null_mut() }
    }
}

fn write_boundary_json(path: &Path, tables: &LitvinTables) -> std::io::Result<()> {
    // Export only what's needed for FEA boundary conditions
    let n = tables.alpha_deg.len();
    for (pi, p) in tables.planets.iter().enumerate() {
        if p.journal_x.len() != n || p.journal_y.len() != n || p.piston_s.len() != n {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                format!("Boundary planet {} arrays length mismatch with alphaDeg ({}).", pi, n)
            ));
        }
    }
    let planets: Vec<serde_json::Value> = tables.planets.iter().map(|p| serde_json::json!({
        "journalX": p.journal_x,
        "journalY": p.journal_y,
        "pistonS": p.piston_s,
    })).collect();
    let json = serde_json::json!({
        "alphaDeg": tables.alpha_deg,
        "planets": planets,
    });
    let mut file = File::create(path)?;
    file.write_all(serde_json::to_string_pretty(&json).unwrap().as_bytes())
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_LitvinNative_getLitvinFeaBoundaryNative(
    mut env: JNIEnv,
    _class: JClass,
    id: jlong,
) -> jstring {
    match get_litvin_tables(id) {
        Ok(tables) => {
            let dir = ensure_tmp_dir_for_id(id);
            let path = dir.join("litvin_fea_boundary.json");
            if let Err(e) = write_boundary_json(&path, &tables) {
                let _ = env.throw(format!("Failed to write FEA boundary JSON: {}", e));
                return std::ptr::null_mut();
            }
            env.new_string(path.to_string_lossy().to_string()).map(|s| s.into_raw()).unwrap_or(std::ptr::null_mut())
        }
        Err(e) => { let _ = env.throw(format!("Failed to get Litvin tables: {}", e)); std::ptr::null_mut() }
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_LitvinNative_initRustLoggerNative(
    mut env: JNIEnv,
    _class: JClass,
    session_id: JString,
    level: JObject,
    log_dir: JObject,
) {
    // Minimal, safe logger init stub: accept parameters and print once.
    fn get_opt_string(env: &mut JNIEnv, obj: JObject) -> Option<String> {
        if obj.is_null() { None } else { env.get_string(&JString::from(obj)).ok().map(|s| s.into()) }
    }
    let session: String = env.get_string(&session_id).map(|s| s.into()).unwrap_or_else(|_| String::new());
    let lvl = get_opt_string(&mut env, level).unwrap_or_default();
    let dir = get_opt_string(&mut env, log_dir).unwrap_or_default();
    println!("[RustLogger] session_id={}, level={}, dir={}", session, lvl, dir);
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_LitvinNative_disposeLitvinLawNative(
    mut env: JNIEnv,
    _class: JClass,
    id: jlong,
) {
    let mut map = LITVIN_TABLES.lock().unwrap();
    if map.remove(&id).is_none() {
        let _ = env.throw(format!("Litvin law with ID {} not found", id));
    }
    // cleanup temp dir
    if let Some(dir) = LITVIN_TMPDIRS.lock().unwrap().remove(&id) {
        let _ = std::fs::remove_dir_all(dir);
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_LitvinNative_runDiagnosticsNative(
    mut env: JNIEnv,
    _class: JClass,
    id: jlong,
    session_id: JString,
    param_hash: JObject,
) -> jstring {
    // Helper to extract optional string from JObject
    fn get_opt_string(env: &mut JNIEnv, obj: JObject) -> Option<String> {
        if obj.is_null() { None } else { env.get_string(&JString::from(obj)).ok().map(|s| s.into()) }
    }
    let session: String = match env.get_string(&session_id) { Ok(s) => s.into(), Err(_) => String::new() };
    let p_hash = get_opt_string(&mut env, param_hash);

    match get_litvin_tables(id) {
        Ok(tables) => {
            let d = &tables.diagnostics;
            let json = serde_json::json!({
                "version": "1.0",
                "sessionId": session,
                "paramHash": p_hash,
                "arcLengthResidualRms": d.arc_length_residual_rms,
                "arcLengthResidualMax": d.arc_length_residual_max,
                "accelMax": d.accel_max,
                "jerkMax": d.jerk_max
            });
            let s = serde_json::to_string(&json).unwrap_or_else(|_| "{}".to_string());
            env.new_string(s).map(|s| s.into_raw()).unwrap_or(std::ptr::null_mut())
        }
        Err(e) => { let _ = env.throw(format!("Failed to get Litvin tables: {}", e)); std::ptr::null_mut() }
    }
}

// --- FeaEngine JNI stubs (to resolve UnsatisfiedLinkError for declared natives) ---

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_fea_FeaEngine_runAnalysisNative(
    mut env: JNIEnv,
    _class: JClass,
    model_file_path: JString,
    results_file_path: JString,
    _parameters: jobjectArray,
) {
    let model: String = match env.get_string(&model_file_path) { Ok(s) => s.into(), Err(e) => {
        let _ = env.throw(format!("runAnalysisNative: invalid model path: {}", e)); return;
    }};
    let results: String = match env.get_string(&results_file_path) { Ok(s) => s.into(), Err(e) => {
        let _ = env.throw(format!("runAnalysisNative: invalid results path: {}", e)); return;
    }};

    let payload = serde_json::json!({
        "status": "ok",
        "sourceModel": model,
        "metrics": { "placeHolder": true }
    });
    if let Err(e) = std::fs::write(&results, serde_json::to_string_pretty(&payload).unwrap()) {
        let _ = env.throw(format!("runAnalysisNative: failed to write results: {}", e));
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_fea_FeaEngine_runStressAnalysisNative(
    mut env: JNIEnv,
    _class: JClass,
    model_file_path: JString,
    results_file_path: JString,
    _parameters: jobjectArray,
) {
    let model: String = match env.get_string(&model_file_path) { Ok(s) => s.into(), Err(e) => {
        let _ = env.throw(format!("runStressAnalysisNative: invalid model path: {}", e)); return;
    }};
    let results: String = match env.get_string(&results_file_path) { Ok(s) => s.into(), Err(e) => {
        let _ = env.throw(format!("runStressAnalysisNative: invalid results path: {}", e)); return;
    }};

    let payload = serde_json::json!({
        "status": "ok",
        "sourceModel": model,
        "stress": { "maxVonMises": 0.0, "placeHolder": true }
    });
    if let Err(e) = std::fs::write(&results, serde_json::to_string_pretty(&payload).unwrap()) {
        let _ = env.throw(format!("runStressAnalysisNative: failed to write results: {}", e));
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_fea_FeaEngine_runVibrationAnalysisNative(
    mut env: JNIEnv,
    _class: JClass,
    model_file_path: JString,
    results_file_path: JString,
    _parameters: jobjectArray,
) {
    let model: String = match env.get_string(&model_file_path) { Ok(s) => s.into(), Err(e) => {
        let _ = env.throw(format!("runVibrationAnalysisNative: invalid model path: {}", e)); return;
    }};
    let results: String = match env.get_string(&results_file_path) { Ok(s) => s.into(), Err(e) => {
        let _ = env.throw(format!("runVibrationAnalysisNative: invalid results path: {}", e)); return;
    }};

    let payload = serde_json::json!({
        "status": "ok",
        "sourceModel": model,
        "modes": [],
        "placeHolder": true
    });
    if let Err(e) = std::fs::write(&results, serde_json::to_string_pretty(&payload).unwrap()) {
        let _ = env.throw(format!("runVibrationAnalysisNative: failed to write results: {}", e));
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_fea_FeaEngine_generateMeshNative(
    mut env: JNIEnv,
    _class: JClass,
    model_file_path: JString,
    mesh_file_path: JString,
    _parameters: jobjectArray,
) {
    let model: String = match env.get_string(&model_file_path) { Ok(s) => s.into(), Err(e) => {
        let _ = env.throw(format!("generateMeshNative: invalid model path: {}", e)); return;
    }};
    let mesh: String = match env.get_string(&mesh_file_path) { Ok(s) => s.into(), Err(e) => {
        let _ = env.throw(format!("generateMeshNative: invalid mesh path: {}", e)); return;
    }};

    let payload = serde_json::json!({
        "status": "ok",
        "sourceModel": model,
        "mesh": { "elements": 0, "nodes": 0, "placeHolder": true }
    });
    if let Err(e) = std::fs::write(&mesh, serde_json::to_string_pretty(&payload).unwrap()) {
        let _ = env.throw(format!("generateMeshNative: failed to write mesh: {}", e));
    }
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_fea_FeaEngine_checkAvailabilityNative(
    _env: JNIEnv,
    _class: JClass,
) {
    // No-op: availability is checked via testNativeLibraryNative (already implemented)
}

#[no_mangle]
pub extern "system" fn Java_com_campro_v5_fea_FeaEngine_getVersionNative(
    mut env: JNIEnv,
    _class: JClass,
) -> jstring {
    env.new_string(crate::VERSION).map(|s| s.into_raw()).unwrap_or(std::ptr::null_mut())
}
