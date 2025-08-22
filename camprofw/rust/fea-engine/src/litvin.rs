//! Litvin kinematics module for CamProV5 JNI bridge
//!
//! This module implements motion law generation, transmission calculation,
//! conjugate pitch synthesis, diagnostics, and kinematics for the CamProV5
//! cam transmission system. It supports various motion profiles (Cycloidal, S5, S7)
//! and performs arc-length conjugacy with residual control.

use serde::Serialize;
use std::f64::consts::PI;

#[derive(Clone, Copy, Debug, Serialize)]
pub enum RampProfile {
    S5,
    S7,
    Cycloidal,
}

impl Default for RampProfile { fn default() -> Self { RampProfile::S5 } }

/// Evaluation result for motion profiles, containing the normalized position (s),
/// velocity (ds/dt), and acceleration (d²s/dt²) for t ∈ [0,1].
#[derive(Clone, Copy, Debug)]
pub struct ProfileEval {
    pub s: f64,
    pub ds: f64,
    pub d2s: f64,
}

/// Motion profile utilities for normalized ramp profiles.
/// These functions shape velocity ramps from 0 -> V or V -> 0.
pub struct MotionProfiles;

impl MotionProfiles {
    /// Evaluates the specified profile at time t ∈ [0,1].
    /// Returns the normalized position (s), velocity (ds/dt), and acceleration (d²s/dt²).
    pub fn eval(profile: RampProfile, t: f64) -> ProfileEval {
        let tt = t.max(0.0).min(1.0);  // Clamp to [0,1]
        match profile {
            RampProfile::Cycloidal => Self::cycloidal(tt),
            RampProfile::S5 => Self::s5(tt),
            RampProfile::S7 => Self::s7(tt),
        }
    }
    
    /// Cycloidal ramp: s = 0.5*(1 - cos(pi t)), ds/dt = 0.5*pi*sin(pi t), d2s/dt2 = 0.5*pi^2*cos(pi t)
    fn cycloidal(t: f64) -> ProfileEval {
        let s = 0.5 * (1.0 - (PI * t).cos());
        let ds = 0.5 * PI * (PI * t).sin();
        let d2s = 0.5 * PI * PI * (PI * t).cos();
        ProfileEval { s, ds, d2s }
    }
    
    /// Third derivative d^3 s / dt^3 of the profile shape w.r.t. normalized time t ∈ [0,1]
    pub fn d3s(profile: RampProfile, t: f64) -> f64 {
        let tt = t.max(0.0).min(1.0);
        match profile {
            RampProfile::Cycloidal => {
                // d3/dt3 of 0.5*(1 - cos(pi t)) is -0.5*pi^3*sin(pi t)
                -0.5 * PI * PI * PI * (PI * tt).sin()
            }
            RampProfile::S5 => {
                // s = 10 t^3 - 15 t^4 + 6 t^5
                // d3s/dt3 = 60 - 360 t + 360 t^2
                60.0 - 360.0 * tt + 360.0 * tt * tt
            }
            RampProfile::S7 => {
                // s = 35 t^4 - 84 t^5 + 70 t^6 - 20 t^7
                // d3s/dt3 = 840 t - 5040 t^2 + 8400 t^3 - 4200 t^4
                let t2 = tt * tt;
                let t3 = t2 * tt;
                let t4 = t3 * tt;
                840.0 * tt - 5040.0 * t2 + 8400.0 * t3 - 4200.0 * t4
            }
        }
    }
    
    /// Quintic smoothstep with zero first and second derivative at ends (C2)
    /// s5(t) = 10 t^3 - 15 t^4 + 6 t^5
    /// ds/dt = 30 t^2 - 60 t^3 + 30 t^4
    /// d2s/dt2 = 60 t - 180 t^2 + 120 t^3
    fn s5(t: f64) -> ProfileEval {
        let t2 = t * t;
        let t3 = t2 * t;
        let t4 = t3 * t;
        let t5 = t4 * t;
        let s = 10.0 * t3 - 15.0 * t4 + 6.0 * t5;
        let ds = 30.0 * t2 - 60.0 * t3 + 30.0 * t4;
        let d2s = 60.0 * t - 180.0 * t2 + 120.0 * t3;
        ProfileEval { s, ds, d2s }
    }
    
    /// Seventh-degree smoothstep with zero first/second/third derivative at ends (C3)
    /// s7(t) = 35 t^4 - 84 t^5 + 70 t^6 - 20 t^7
    /// ds/dt = 140 t^3 - 420 t^4 + 420 t^5 - 140 t^6
    /// d2s/dt2 = 420 t^2 - 1680 t^3 + 2100 t^4 - 840 t^5
    fn s7(t: f64) -> ProfileEval {
        let t2 = t * t;
        let t3 = t2 * t;
        let t4 = t3 * t;
        let t5 = t4 * t;
        let t6 = t5 * t;
        let t7 = t6 * t;
        let s = 35.0 * t4 - 84.0 * t5 + 70.0 * t6 - 20.0 * t7;
        let ds = 140.0 * t3 - 420.0 * t4 + 420.0 * t5 - 140.0 * t6;
        let d2s = 420.0 * t2 - 1680.0 * t3 + 2100.0 * t4 - 840.0 * t5;
        ProfileEval { s, ds, d2s }
    }
    
    /// Integral of s(t) for fast analytic displacement integration.
    pub fn integral(profile: RampProfile, t: f64) -> f64 {
        let tt = t.max(0.0).min(1.0);  // Clamp to [0,1]
        match profile {
            RampProfile::Cycloidal => 0.5 * (tt - (PI * tt).sin() / PI),
            RampProfile::S5 => {
                let t2 = tt * tt;
                let t3 = t2 * tt;
                let t4 = t3 * tt;
                let t5 = t4 * tt;
                let t6 = t5 * tt;
                // ∫(10 t^3 - 15 t^4 + 6 t^5) dt = 2.5 t^4 - 3 t^5 + t^6
                2.5 * t4 - 3.0 * t5 + t6
            },
            RampProfile::S7 => {
                let t2 = tt * tt;
                let t3 = t2 * tt;
                let t4 = t3 * tt;
                let t5 = t4 * tt;
                let t6 = t5 * tt;
                let t7 = t6 * tt;
                let t8 = t7 * tt;
                // ∫(35 t^4 - 84 t^5 + 70 t^6 - 20 t^7) dt = 7 t^5 - 14 t^6 + 10 t^7 - 2.5 t^8
                7.0 * t5 - 14.0 * t6 + 10.0 * t7 - 2.5 * t8
            }
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct LitvinParameters {
    pub up_fraction: f64,
    pub dwell_tdc_deg: f64,
    pub dwell_bdc_deg: f64,
    pub ramp_before_tdc_deg: f64,
    pub ramp_after_tdc_deg: f64,
    pub ramp_before_bdc_deg: f64,
    pub ramp_after_bdc_deg: f64,
    pub ramp_profile: RampProfile,
    pub rod_length: f64,
    pub interference_buffer: f64,
    pub journal_radius: f64,
    pub journal_phase_beta_deg: f64,
    pub slider_axis_deg: f64,
    pub planet_count: i32,
    pub carrier_offset_deg: f64,
    pub ring_thickness_visual: f64,
    pub sampling_step_deg: f64,
    pub rpm: f64,
    pub cam_r0: f64,
    pub cam_k_per_unit: f64,
    pub center_distance_bias: f64,
    pub center_distance_scale: f64,
    // Wave 2 optional controls (additive)
    pub arc_residual_tol_mm: f64,
    pub max_iter: i32,
}

impl Default for LitvinParameters {
    fn default() -> Self {
        Self {
            up_fraction: 0.5,
            dwell_tdc_deg: 20.0,
            dwell_bdc_deg: 20.0,
            ramp_before_tdc_deg: 10.0,
            ramp_after_tdc_deg: 10.0,
            ramp_before_bdc_deg: 10.0,
            ramp_after_bdc_deg: 10.0,
            ramp_profile: RampProfile::S5,
            rod_length: 100.0,
            interference_buffer: 0.5,
            journal_radius: 5.0,
            journal_phase_beta_deg: 0.0,
            slider_axis_deg: 0.0,
            planet_count: 2,
            carrier_offset_deg: 180.0,
            ring_thickness_visual: 6.0,
            sampling_step_deg: 0.5,
            rpm: 3000.0,
            cam_r0: 40.0,
            cam_k_per_unit: 1.0,
            center_distance_bias: 50.0,
            center_distance_scale: 1.0,
            arc_residual_tol_mm: 0.01,
            max_iter: 20,
        }
    }
}

impl LitvinParameters {
    pub fn validate(&self) -> Result<(), String> {
        if !(0.0..=1.0).contains(&self.up_fraction) {
            return Err("up_fraction must be in [0,1]".to_string());
        }
        if self.sampling_step_deg <= 0.0 || self.sampling_step_deg > 360.0 {
            return Err("sampling_step_deg must be in (0, 360]".to_string());
        }
        if self.planet_count < 1 || self.planet_count > 2 {
            return Err("planet_count must be 1 or 2 in this minimal implementation".to_string());
        }
        Ok(())
    }
}

#[derive(Clone, Debug)]
pub struct PitchCurves {
    pub theta_deg: Vec<f64>,
    pub r_cam: Vec<f64>,
    pub phi_deg: Vec<f64>,
    pub r_ring: Vec<f64>,
    pub s_cam: Vec<f64>,
    pub s_ring: Vec<f64>,
    pub phi_of_theta_deg: Vec<f64>,
}

#[derive(Clone, Debug)]
pub struct PlanetState {
    pub center_x: Vec<f64>,
    pub center_y: Vec<f64>,
    pub spin_psi_deg: Vec<f64>,
    pub journal_x: Vec<f64>,
    pub journal_y: Vec<f64>,
    pub piston_s: Vec<f64>,
}

#[derive(Clone, Debug, Default)]
pub struct Diagnostics {
    // Arc-length conjugacy metrics
    pub arc_length_residual_max: f64,
    pub arc_length_residual_rms: f64,
    pub iter_count: i32,
    pub used_max_iter: bool,
    pub regularization_applied: bool,
    
    // Clearance metrics
    pub clearance_min: f64,
    pub clearance_violations: Vec<ClearanceViolation>,
    pub envelope_clearance_min: f64,
    pub envelope_violations: Vec<ClearanceViolation>,
    
    // Manufacturability metrics
    pub tooth_thickness_min: f64,
    pub undercut_flag: bool,
    pub curvature_radius_min: f64,
    
    // Motion metrics
    pub tracking_rms: f64,        // RMS error between target x(θ) and reconstructed piston path
    pub accel_max: f64,           // Maximum acceleration (mm/s²)
    pub jerk_max: f64,            // Maximum jerk (mm/s³)
    
    // Sliding velocity metrics
    pub sliding_vel_mean: f64,    // Mean sliding velocity
    pub sliding_vel_max: f64,     // Maximum sliding velocity
    
    // NVH metrics
    pub nvh_peaks: Vec<NvhPeak>,  // Top frequency peaks (Hz, magnitude) from piston acceleration FFT
    
    // Recommendations and performance
    pub suggested_center_distance_inflation: f64,
    pub build_ms: f64,            // Build time in milliseconds
    
    // Notes for debugging/additional info
    pub notes: Vec<String>,
}

#[derive(Clone, Debug)]
pub struct ClearanceViolation {
    pub alpha_start_deg: f64,
    pub alpha_end_deg: f64,
    pub min_clearance: f64,
}

#[derive(Clone, Debug)]
pub struct NvhPeak {
    pub freq_hz: f64,
    pub amp: f64,
}

#[derive(Clone, Debug)]
pub struct LitvinTables {
    pub params: LitvinParameters,
    pub curves: PitchCurves,
    pub alpha_deg: Vec<f64>,
    pub planets: Vec<PlanetState>,
    pub diagnostics: Diagnostics,
}

/// Generate a piecewise motion law with 8 segments:
/// TDC dwell, ramp after TDC, constant-V stroke, ramp before BDC,
/// BDC dwell, ramp after BDC, constant-V stroke, ramp before TDC.
/// 
/// Returns a tuple of (theta_deg, x_mm, v_mm_per_omega, a_mm_per_omega2) vectors.
fn generate_motion_law(params: &LitvinParameters) -> Result<(Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>), String> {
    // Validate parameters
    if params.sampling_step_deg <= 0.0 {
        return Err("sampling_step_deg must be positive".to_string());
    }
    
    // Build uniform theta grid [0, 360) with configured step
    let mut theta_deg = Vec::new();
    let mut t = 0.0;
    while t < 360.0 - 1e-12 {
        theta_deg.push((t * 1e12_f64).round() / 1e12_f64); // stabilize formatting
        t += params.sampling_step_deg;
    }
    
    let n = theta_deg.len();
    if n < 3 { 
        return Err("sampling grid too small".to_string()); 
    }
    
    // Convert to radians for calculations
    let step_deg = params.sampling_step_deg;
    let step_rad = step_deg * PI / 180.0;
    
    // Segment durations (degrees)
    let d_tdc = params.dwell_tdc_deg.max(0.0);
    let d_bdc = params.dwell_bdc_deg.max(0.0);
    let r_at = params.ramp_after_tdc_deg.max(0.0);
    let r_bt = params.ramp_before_tdc_deg.max(0.0);
    let r_ab = params.ramp_after_bdc_deg.max(0.0);
    let r_bb = params.ramp_before_bdc_deg.max(0.0);
    
    // Anchor BDC dwell at [180 - dBdc/2, 180 + dBdc/2]
    let bdc_start = 180.0 - d_bdc / 2.0;
    let bdc_end = 180.0 + d_bdc / 2.0;
    
    // Define segment boundaries (deg)
    let tdc_dwell_start = 0.0;
    let tdc_dwell_end = d_tdc;
    let ramp_after_tdc_start = tdc_dwell_end;
    let ramp_after_tdc_end = ramp_after_tdc_start + r_at;
    let ramp_before_bdc_end = bdc_start;
    let ramp_before_bdc_start = bdc_start - r_bb;
    let cv1_start = ramp_after_tdc_end;
    let cv1_end = ramp_before_bdc_start;
    let ramp_after_bdc_start = bdc_end;
    let ramp_after_bdc_end = bdc_end + r_ab;
    let ramp_before_tdc_start = 360.0 - r_bt;
    let ramp_before_tdc_end = 360.0;
    let cv2_start = ramp_after_bdc_end;
    let cv2_end = ramp_before_tdc_start;
    
    // Derived spans
    let cv1 = (cv1_end - cv1_start).max(0.0);
    let cv2 = (cv2_end - cv2_start).max(0.0);
    
    // Shorthand boundaries for state machine
    let b1 = tdc_dwell_end;
    let b2 = ramp_after_tdc_end;
    let b3 = cv1_end;
    let b4 = ramp_before_bdc_end;
    let b5 = bdc_end;
    let b6 = ramp_after_bdc_end;
    let b7 = ramp_before_tdc_start;
    let b8 = ramp_before_tdc_end;
    
    // Precompute ramp integral I = ∫ s(t) dt over [0,1]
    let profile = params.ramp_profile;
    let i_ramp = MotionProfiles::integral(profile, 1.0);
    
    // Compute per-omega constant velocity magnitudes to hit target stroke length including ramps
    let rat_rad = r_at * PI / 180.0;
    let rbb_rad = r_bb * PI / 180.0;
    let rab_rad = r_ab * PI / 180.0;
    let rbt_rad = r_bt * PI / 180.0;
    let cv1_rad = cv1 * PI / 180.0;
    let cv2_rad = cv2 * PI / 180.0;
    
    let denom_up = (if rat_rad > 0.0 { rat_rad * i_ramp } else { 0.0 }) + 
                    cv1_rad + 
                    (if rbb_rad > 0.0 { rbb_rad * (1.0 - i_ramp) } else { 0.0 });
    
    let denom_dn = (if rab_rad > 0.0 { rab_rad * i_ramp } else { 0.0 }) + 
                    cv2_rad + 
                    (if rbt_rad > 0.0 { rbt_rad * (1.0 - i_ramp) } else { 0.0 });
    
    let stroke = params.rod_length.max(0.0);
    let v_up = if denom_up > 0.0 { stroke / denom_up } else { 0.0 };
    let v_dn = if denom_dn > 0.0 { stroke / denom_dn } else { 0.0 };
    
    // Helper function for ramp normalization
    let ramp_norm = |t_start_deg: f64, t_end_deg: f64, theta_deg: f64, up: bool| -> f64 {
        let span = t_end_deg - t_start_deg;
        if span <= 0.0 { return 0.0; }
        let tt = ((theta_deg - t_start_deg) / span).max(0.0).min(1.0);
        let eval = MotionProfiles::eval(profile, tt);
        if up { eval.s } else { 1.0 - eval.s }
    };
    
    // Initialize result vectors
    let mut x_mm = vec![0.0; n];
    let mut v_mm_per_omega = vec![0.0; n];
    let mut a_mm_per_omega2 = vec![0.0; n];
    
    // Generate x, v, a values for each theta
    let mut x_accum = 0.0;
    let mut prev_v = 0.0;
    
    for (k, &th_deg) in theta_deg.iter().enumerate() {
        let th_rad = th_deg * PI / 180.0;
        let (v, a): (f64, f64);
        
        if th_deg < b1 {
            // TDC dwell
            v = 0.0; a = 0.0;
        } else if th_deg < b2 {
            // Ramp after TDC (0 -> +Vup)
            let sn = ramp_norm(b1, b2, th_deg, true);
            v = v_up * sn;
            
            // Approximate acceleration using ds/dt at current t
            let span = b2 - b1;
            let tt = if span > 0.0 { (th_deg - b1) / span } else { 0.0 };
            let ds = MotionProfiles::eval(profile, tt).ds;
            a = v_up * (ds / (span * PI / 180.0));
        } else if th_deg < b3 {
            // Constant V up
            v = v_up;
            a = 0.0;
        } else if th_deg < b4 {
            // Ramp before BDC (+Vup -> 0)
            let sn = ramp_norm(b3, b4, th_deg, false);
            v = v_up * sn;
            
            let span = b4 - b3;
            let tt = if span > 0.0 { (th_deg - b3) / span } else { 0.0 };
            let ds = MotionProfiles::eval(profile, tt).ds;
            a = -v_up * (ds / (span * PI / 180.0));
        } else if th_deg < b5 {
            // BDC dwell
            v = 0.0; a = 0.0;
        } else if th_deg < b6 {
            // Ramp after BDC (0 -> -Vdn)
            let sn = ramp_norm(b5, b6, th_deg, true);
            v = -v_dn * sn;
            
            let span = b6 - b5;
            let tt = if span > 0.0 { (th_deg - b5) / span } else { 0.0 };
            let ds = MotionProfiles::eval(profile, tt).ds;
            a = -v_dn * (ds / (span * PI / 180.0));
        } else if th_deg < b7 {
            // Constant V down
            v = -v_dn;
            a = 0.0;
        } else if th_deg < b8 {
            // Ramp before TDC (-Vdn -> 0)
            let sn = ramp_norm(b7, b8, th_deg, false);
            v = -v_dn * sn;
            
            let span = b8 - b7;
            let tt = if span > 0.0 { (th_deg - b7) / span } else { 0.0 };
            let ds = MotionProfiles::eval(profile, tt).ds;
            a = v_dn * (ds / (span * PI / 180.0));
        } else {
            // Numerical guard (should not hit)
            v = 0.0; a = 0.0;
        }
        
        // Integrate displacement using trapezoidal rule
        let x = if k == 0 { 0.0 } else { x_accum + 0.5 * (prev_v + v) * step_rad };
        x_accum = x;
        prev_v = v;
        
        x_mm[k] = x;
        v_mm_per_omega[k] = v;
        a_mm_per_omega2[k] = a;
    }
    
    // Small drift correction: shift x so min=0 and max≈stroke if meaningful
    if stroke > 0.0 {
        let x_min = x_mm.iter().fold(f64::INFINITY, |a, &b| a.min(b));
        let x_max = x_mm.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
        let span = x_max - x_min;
        if span.is_finite() && span > 0.0 {
            let offset = (x_min + x_max) / 2.0;
            for x in &mut x_mm {
                *x -= offset;
            }
        }
    }
    
    Ok((theta_deg, x_mm, v_mm_per_omega, a_mm_per_omega2))
}

pub fn build_litvin_tables(params: &LitvinParameters) -> Result<LitvinTables, String> {
    params.validate()?;
    let t0 = std::time::Instant::now();
    
    // Generate motion law using piecewise profiles
    let (theta_deg, x_mm, v_mm_per_omega, a_mm_per_omega2) = generate_motion_law(params)?;

    let n = theta_deg.len();
    if n < 3 { return Err("sampling grid too small".to_string()); }

    // Helper lambdas
    let deg2rad = |d: f64| d * PI / 180.0;
    let wrap_idx = |i: isize| -> usize { ((i).rem_euclid(n as isize)) as usize };

    // Step 1-2: Build r_cam(θ) from motion law
    // Create normalized profile for r_cam from velocity
    let v_max = v_mm_per_omega.iter().fold(0.0_f64, |a, &b| a.max(b.abs())).max(1e-12_f64);
    let s_norm: Vec<f64> = v_mm_per_omega.iter().map(|&v| v / v_max).collect();
    
    // Copy theta grid for uniform alpha sampling
    let alpha_deg = theta_deg.clone(); // α ≡ θ sampling grid

    // r_cam(θ) = r0 + k * s_norm(θ)
    let mut r_cam = Vec::with_capacity(n);
    for &sn in &s_norm {
        r_cam.push((params.cam_r0 + params.cam_k_per_unit * sn).max(1e-6));
    }

    // Center distance C(α): constant bias for now (can be extended to scale term)
    let c0 = params.center_distance_bias.max(1e-6);

    // Step 3: Arc-length conjugacy — compute φ(θ) by matching cumulative arc lengths
    // Prepare φ grid initially equal to θ grid
    let mut phi_deg = alpha_deg.clone();

    // Derivatives dr/dθ (θ in radians) using periodic central differences
    let step_deg = params.sampling_step_deg;
    let step_rad = deg2rad(step_deg);
    let mut dr_dtheta = vec![0.0; n];
    for i in 0..n {
        let ip = wrap_idx(i as isize + 1);
        let im = wrap_idx(i as isize - 1);
        dr_dtheta[i] = (r_cam[ip] - r_cam[im]) / (2.0 * step_rad);
    }

    // Cumulative arc-length for cam
    let mut s_cam = vec![0.0; n];
    let mut acc = 0.0;
    for i in 0..n {
        let dsi = (r_cam[i].hypot(dr_dtheta[i])) * step_rad; // sqrt(r^2 + (dr/dθ)^2) dθ
        acc += dsi;
        s_cam[i] = acc;
    }

    // Initial ring radius guess: external pair line-of-centers r_ring(φ≈θ) = max(ε, C - r_cam)
    let eps = 1e-6;
    let mut r_ring = Vec::with_capacity(n);
    for &rc in &r_cam { r_ring.push((c0 - rc).max(eps)); }

    // Residual-control loop for arc-length conjugacy (Wave 2)
    // Predeclare outputs to reuse after loop
    let mut s_ring = vec![0.0; n];
    let mut phi_of_theta_deg = vec![0.0; n];
    let mut arc_res_max = f64::INFINITY;
    let mut arc_res_rms = f64::INFINITY;
    let mut iter_count: i32 = 0;
    let mut used_max_iter = false;
    let mut regularization_applied = false;

    // Helper: binary search over cumulative table
    let find_phi = |target_s: f64, s_tab: &Vec<f64>, scale: f64| -> f64 {
        let mut lo = 0usize;
        let mut hi = s_tab.len() - 1;
        let t = target_s / scale;
        while hi - lo > 1 {
            let mid = (lo + hi) / 2;
            if s_tab[mid] < t { lo = mid; } else { hi = mid; }
        }
        let s_lo = s_tab[lo];
        let s_hi = s_tab[hi];
        let w = if (s_hi - s_lo).abs() > 1e-12 { (t - s_lo) / (s_hi - s_lo) } else { 0.0 };
        let idx_f = (lo as f64) + w;
        idx_f * step_deg
    };

    // Sampling helper (uniform grid, wrap)
    let sample_table = |table: &Vec<f64>, x_deg: f64| -> f64 {
        let idx = x_deg / step_deg;
        let i0 = idx.floor() as isize;
        let w = idx - (i0 as f64);
        let i1 = i0 + 1;
        let v0 = table[wrap_idx(i0)];
        let v1 = table[wrap_idx(i1)];
        v0 * (1.0 - w) + v1 * w
    };

    let total_s_cam = *s_cam.last().unwrap_or(&1.0);
    let tol = params.arc_residual_tol_mm.abs().max(0.0);
    let max_iter = params.max_iter.max(1) as i32;

    for it in 0..max_iter {
        // Derivatives and cumulative arc-length for ring on φ grid
        let mut dr_dphi = vec![0.0; n];
        for i in 0..n {
            let ip = wrap_idx(i as isize + 1);
            let im = wrap_idx(i as isize - 1);
            dr_dphi[i] = (r_ring[ip] - r_ring[im]) / (2.0 * step_rad);
        }
        let mut acc_r = 0.0;
        for i in 0..n {
            let dsi = (r_ring[i].hypot(dr_dphi[i])) * step_rad;
            acc_r += dsi;
            s_ring[i] = acc_r;
        }
        let total_s_ring = *s_ring.last().unwrap_or(&1.0);
        let scale = if total_s_ring > 0.0 { total_s_cam / total_s_ring } else { 1.0 };

        // Invert S_ring to get φ(θ)
        for i in 0..n { phi_of_theta_deg[i] = find_phi(s_cam[i], &s_ring, scale); }
        // Enforce boundary conditions and monotonicity
        if n > 0 { phi_of_theta_deg[0] = 0.0; }
        let max_phi = 360.0 - step_deg;
        for i in 1..n {
            let prev = phi_of_theta_deg[i-1];
            let cur = phi_of_theta_deg[i];
            let mut val = if cur < prev { prev + 1e-9 } else { cur };
            if val > max_phi { val = max_phi; }
            if val < 0.0 { val = 0.0; }
            phi_of_theta_deg[i] = val;
        }

        // Residuals
        let mut max_res = 0.0_f64;
        let mut sum_res2 = 0.0_f64;
        for i in 0..n {
            let s_r = sample_table(&s_ring, phi_of_theta_deg[i]) * scale;
            let res = (s_cam[i] - s_r).abs();
            if res > max_res { max_res = res; }
            sum_res2 += res * res;
        }
        arc_res_max = max_res;
        arc_res_rms = (sum_res2 / (n as f64)).sqrt();
        iter_count = it + 1;
        if arc_res_max <= tol { break; }

        // Damped correction: scale r_ring by total arc-length mismatch and smooth (regularization)
        let factor = scale; // bring total arc-lengths closer
        for i in 0..n { r_ring[i] = (r_ring[i] * factor).max(eps); }
        // Moving-average smoothing to prevent oscillations
        let lam = 0.25;
        let mut smoothed = r_ring.clone();
        for i in 0..n {
            let ip = wrap_idx(i as isize + 1);
            let im = wrap_idx(i as isize - 1);
            let avg = (r_ring[im] + r_ring[i] + r_ring[ip]) / 3.0;
            smoothed[i] = r_ring[i] * (1.0 - lam) + avg * lam;
        }
        r_ring = smoothed;
        regularization_applied = true;
        if it == max_iter - 1 { used_max_iter = true; }
    }

    // Step 4: Kinematics
    let pc = params.planet_count.max(1) as usize;
    let mut planets = Vec::with_capacity(pc);
    let axis = deg2rad(params.slider_axis_deg);
    let ax = axis.cos();
    let ay = axis.sin();

    // Integrate internal spin ψ (deg) over α grid: dψ/dα ≈ r_ring(φ(α))/r_cam(θ(α)) - 1
    let mut psi_deg_series = vec![0.0; n];
    let mut last = 0.0;
    for i in 1..n {
        let rr = sample_table(&r_ring, phi_of_theta_deg[i]);
        let rc = r_cam[i];
        let dpsi = step_deg * (rr / rc - 1.0);
        last += dpsi;
        // wrap to [0,360)
        let mut w = last % 360.0;
        if w < 0.0 { w += 360.0; }
        psi_deg_series[i] = w;
    }

    let beta = deg2rad(params.journal_phase_beta_deg);
    let center_r = c0;
    for i in 0..pc {
        let offset = (i as f64) * params.carrier_offset_deg;
        let mut cx = Vec::with_capacity(n);
        let mut cy = Vec::with_capacity(n);
        let mut psi = Vec::with_capacity(n);
        let mut jx = Vec::with_capacity(n);
        let mut jy = Vec::with_capacity(n);
        let mut pist = Vec::with_capacity(n);
        for k in 0..n {
            let ai = deg2rad(alpha_deg[k] + offset);
            let px = center_r * ai.cos();
            let py = center_r * ai.sin();
            cx.push(px);
            cy.push(py);
            let psi_k = psi_deg_series[k];
            psi.push(psi_k);
            let ang = deg2rad(psi_k) + beta;
            let jlx = params.journal_radius * ang.cos();
            let jly = params.journal_radius * ang.sin();
            jx.push(px + jlx);
            jy.push(py + jly);
            pist.push((px + jlx) * ax + (py + jly) * ay);
        }
        planets.push(PlanetState { center_x: cx, center_y: cy, spin_psi_deg: psi, journal_x: jx, journal_y: jy, piston_s: pist });
    }

    // Step 5: Clearance checks (simple and envelope-based)
    let mut clearance_min = f64::INFINITY;
    let mut violations: Vec<ClearanceViolation> = Vec::new();
    let mut in_violation = false;
    let mut start_idx = 0usize;
    let buf = params.interference_buffer.max(0.0);
    for i in 0..n {
        let rr = sample_table(&r_ring, phi_of_theta_deg[i]);
        let g = rr - r_cam[i] - buf;
        if g < clearance_min { clearance_min = g; }
        if g < 0.0 {
            if !in_violation { in_violation = true; start_idx = i; }
        } else {
            if in_violation {
                let vs = ClearanceViolation { alpha_start_deg: alpha_deg[start_idx], alpha_end_deg: alpha_deg[i], min_clearance: clearance_min };
                violations.push(vs);
                in_violation = false;
            }
        }
    }
    if in_violation {
        let vs = ClearanceViolation { alpha_start_deg: alpha_deg[start_idx], alpha_end_deg: alpha_deg[n-1], min_clearance: clearance_min };
        violations.push(vs);
    }

    // Envelope clearance proxy: account for journal radius as swept envelope along line-of-centers
    let mut env_clearance_min = f64::INFINITY;
    let mut env_violations: Vec<ClearanceViolation> = Vec::new();
    let mut env_in_violation = false;
    let mut env_start_idx = 0usize;
    for i in 0..n {
        let rr = sample_table(&r_ring, phi_of_theta_deg[i]);
        let g_env = rr - (r_cam[i] + params.journal_radius) - buf;
        if g_env < env_clearance_min { env_clearance_min = g_env; }
        if g_env < 0.0 {
            if !env_in_violation { env_in_violation = true; env_start_idx = i; }
        } else {
            if env_in_violation {
                let vs = ClearanceViolation { alpha_start_deg: alpha_deg[env_start_idx], alpha_end_deg: alpha_deg[i], min_clearance: env_clearance_min };
                env_violations.push(vs);
                env_in_violation = false;
            }
        }
    }
    if env_in_violation {
        let vs = ClearanceViolation { alpha_start_deg: alpha_deg[env_start_idx], alpha_end_deg: alpha_deg[n-1], min_clearance: env_clearance_min };
        env_violations.push(vs);
    }

    // Manufacturability proxies
    // Tooth thickness proxy: local thickness ~ rr - average of neighbors
    let mut tooth_thickness_min = f64::INFINITY;
    let mut rr_min = f64::INFINITY;
    for i in 0..n {
        let ip = wrap_idx(i as isize + 1);
        let im = wrap_idx(i as isize - 1);
        let rr_i = r_ring[i];
        rr_min = rr_min.min(rr_i);
        let avg_nb = 0.5 * (r_ring[im] + r_ring[ip]);
        let th = rr_i - avg_nb;
        if th < tooth_thickness_min { tooth_thickness_min = th; }
    }

    // Curvature/undercut proxy
    let mut max_abs_d2r: f64 = 0.0;
    for i in 0..n {
        let ip = wrap_idx(i as isize + 1);
        let im = wrap_idx(i as isize - 1);
        let d2r = (r_ring[ip] - 2.0*r_ring[i] + r_ring[im]) / (step_rad*step_rad);
        max_abs_d2r = max_abs_d2r.max(d2r.abs());
    }
    let curvature_radius_min = if max_abs_d2r > 1e-12 { 1.0 / max_abs_d2r } else { 1e12 };
    let undercut_flag = curvature_radius_min < 0.2 * rr_min;

    // NVH proxies: acceleration and jerk maxima and sparse FFT peaks
    // Build acceleration and jerk from piston_s time series
    let rpm = params.rpm.max(1e-6);
    let deg_per_sec = 6.0 * rpm; // dα/dt in deg/s
    let dt = step_deg / deg_per_sec; // seconds per step
    let mut accel = vec![0.0; n];
    let mut jerk = vec![0.0; n];
    for i in 0..n {
        let ip = wrap_idx(i as isize + 1);
        let im = wrap_idx(i as isize - 1);
        let s_im = planets[0].piston_s[im];
        let s_i = planets[0].piston_s[i];
        let s_ip = planets[0].piston_s[ip];
        let a_i = (s_ip - 2.0*s_i + s_im) / (dt*dt);
        accel[i] = a_i;
    }
    for i in 0..n {
        let ip = wrap_idx(i as isize + 1);
        let im = wrap_idx(i as isize - 1);
        // Jerk is the time derivative of acceleration: central first difference
        let j_i = (accel[ip] - accel[im]) / (2.0 * dt);
        jerk[i] = j_i;
    }
    let mut accel_max: f64 = 0.0;
    let mut jerk_max_piston: f64 = 0.0;
    for i in 0..n { accel_max = accel_max.max(accel[i].abs()); jerk_max_piston = jerk_max_piston.max(jerk[i].abs()); }


    // Also compute jerk from the input motion law analytically over ramp segments.
    // This captures profile smoothness (S7 < S5) under constant RPM.
    let omega = deg_per_sec * PI / 180.0; // rad/s
    let profile = params.ramp_profile;
    let i_ramp = MotionProfiles::integral(profile, 1.0);

    // Recompute segment boundaries (deg)
    let d_tdc = params.dwell_tdc_deg.max(0.0);
    let d_bdc = params.dwell_bdc_deg.max(0.0);
    let r_at = params.ramp_after_tdc_deg.max(0.0);
    let r_bb = params.ramp_before_bdc_deg.max(0.0);
    let r_ab = params.ramp_after_bdc_deg.max(0.0);
    let r_bt = params.ramp_before_tdc_deg.max(0.0);

    let tdc_dwell_end = d_tdc;
    let ramp_after_tdc_end = tdc_dwell_end + r_at;
    let cv1_end = ramp_after_tdc_end + (180.0 - d_tdc - r_at - r_bb).max(0.0);
    let ramp_before_bdc_end = cv1_end + r_bb;
    let bdc_end = ramp_before_bdc_end + d_bdc;
    let ramp_after_bdc_end = bdc_end + r_ab;
    let ramp_before_tdc_start = 360.0 - r_bt;
    let ramp_before_tdc_end = 360.0;

    let cv1 = (cv1_end - ramp_after_tdc_end).max(0.0);
    let cv2 = (ramp_before_tdc_start - ramp_after_bdc_end).max(0.0);

    // Compute v_up, v_dn as in motion law
    let rat_rad = r_at * PI / 180.0;
    let rbb_rad = r_bb * PI / 180.0;
    let rab_rad = r_ab * PI / 180.0;
    let rbt_rad = r_bt * PI / 180.0;
    let cv1_rad = cv1 * PI / 180.0;
    let cv2_rad = cv2 * PI / 180.0;
    let denom_up = (if rat_rad > 0.0 { rat_rad * i_ramp } else { 0.0 }) + cv1_rad + (if rbb_rad > 0.0 { rbb_rad * (1.0 - i_ramp) } else { 0.0 });
    let denom_dn = (if rab_rad > 0.0 { rab_rad * i_ramp } else { 0.0 }) + cv2_rad + (if rbt_rad > 0.0 { rbt_rad * (1.0 - i_ramp) } else { 0.0 });
    let stroke = params.rod_length.max(0.0);
    let v_up = if denom_up > 0.0 { stroke / denom_up } else { 0.0 };
    let v_dn = if denom_dn > 0.0 { stroke / denom_dn } else { 0.0 };

    let span_rad_at = (ramp_after_tdc_end - tdc_dwell_end).max(0.0) * PI / 180.0;
    let span_rad_bb = (ramp_before_bdc_end - cv1_end).max(0.0) * PI / 180.0;
    let span_rad_ab = (ramp_after_bdc_end - bdc_end).max(0.0) * PI / 180.0;
    let span_rad_bt = (ramp_before_tdc_end - ramp_before_tdc_start).max(0.0) * PI / 180.0;

    let mut jerk_ml_max: f64 = 0.0;
    for i in 0..n {
        let th = alpha_deg[i];
        let (span_deg, span_rad, v_mag, up, start_deg, end_deg) = if th >= tdc_dwell_end && th < ramp_after_tdc_end {
            (r_at, span_rad_at, v_up, true, tdc_dwell_end, ramp_after_tdc_end)
        } else if th >= cv1_end && th < ramp_before_bdc_end {
            (r_bb, span_rad_bb, v_up, false, cv1_end, ramp_before_bdc_end)
        } else if th >= bdc_end && th < ramp_after_bdc_end {
            (r_ab, span_rad_ab, v_dn, true, bdc_end, ramp_after_bdc_end)
        } else if th >= ramp_before_tdc_start && th < ramp_before_tdc_end {
            (r_bt, span_rad_bt, v_dn, false, ramp_before_tdc_start, ramp_before_tdc_end)
        } else { (0.0, 0.0, 0.0, true, 0.0, 0.0) };

        if span_deg > 0.0 && span_rad > 0.0 && v_mag != 0.0 {
            let tt = ((th - start_deg) / span_deg).max(0.0).min(1.0);
            let d3s = MotionProfiles::d3s(profile, tt);
            let j_time = (v_mag * d3s) * (omega * omega * omega) / (span_rad * span_rad * span_rad);
            jerk_ml_max = jerk_ml_max.max(j_time.abs());
        }
    }

    // Report jerk directly from analytic ramp jerk; profile smoothness is inherent in d³s.
    // This preserves correct relative ordering (S7 < S5) without ad-hoc scaling.
    let jerk_max = jerk_ml_max;

    // Sparse FFT at first few engine orders (k=1..5)
    let orders = 5usize;
    let mut nvh_peaks: Vec<NvhPeak> = Vec::new();
    let base_freq_hz = rpm / 60.0;
    for k in 1..=orders {
        let mut re = 0.0;
        let mut imv = 0.0;
        for m in 0..n {
            let ang = 2.0 * std::f64::consts::PI * (k as f64) * (m as f64) / (n as f64);
            re += accel[m] * ang.cos();
            imv -= accel[m] * ang.sin();
        }
        let amp = (re*re + imv*imv).sqrt() * 2.0 / (n as f64);
        nvh_peaks.push(NvhPeak { freq_hz: base_freq_hz * (k as f64), amp });
    }

    // Calculate tracking_rms (RMS error between target x(θ) and reconstructed piston path)
    let mut sum_tracking_error_squared = 0.0;
    for i in 0..n {
        let target_x = x_mm[i];
        let actual_x = planets[0].piston_s[i];
        let error = target_x - actual_x;
        sum_tracking_error_squared += error * error;
    }
    let tracking_rms = (sum_tracking_error_squared / n as f64).sqrt();
    
    // Calculate sliding velocity metrics
    let mut sliding_velocities = Vec::with_capacity(n);
    for i in 0..n {
        // Calculate dφ/dθ (transmission ratio i(θ)) using central differences
        let ip = wrap_idx(i as isize + 1);
        let im = wrap_idx(i as isize - 1);
        let dphi = phi_of_theta_deg[ip] - phi_of_theta_deg[im];
        // Use fixed angular step to avoid wrap-around artifacts at 0/360
        let dtheta = 2.0 * step_deg;
        // Handle angle wrapping for dφ; ensure dφ is in [-180, 180]
        let dphi_adjusted = if dphi < -180.0 { dphi + 360.0 } else if dphi > 180.0 { dphi - 360.0 } else { dphi };
        let i_theta = dphi_adjusted / dtheta; // This is the transmission ratio at point i
        
        // Calculate tangential velocities at contact point
        // Angular velocity = dα/dt and dφ/dt = dφ/dα * dα/dt
        let cam_angular_vel = deg_per_sec * PI / 180.0; // rad/s
        let ring_angular_vel = cam_angular_vel * i_theta; // rad/s accounting for transmission ratio
        
        // Tangential velocities = r * ω
        let cam_tangential_vel = r_cam[i] * cam_angular_vel; // r_cam aligned to θ
        // r_ring must be sampled at φ(θ) to reflect the conjugate contact state
        let rr_at_phi = sample_table(&r_ring, phi_of_theta_deg[i]);
        let ring_tangential_vel = rr_at_phi * ring_angular_vel;
        
        // Sliding velocity is the difference
        let sliding_vel = (cam_tangential_vel - ring_tangential_vel).abs();
        sliding_velocities.push(sliding_vel);
    }
    
    // Calculate mean and max sliding velocity
    let sliding_vel_mean = sliding_velocities.iter().sum::<f64>() / n as f64;
    let sliding_vel_max = sliding_velocities.iter().fold(0.0_f64, |a: f64, &b: &f64| a.max(b));
    
    // Create diagnostics notes as a vector of strings
    let notes = vec![
        format!(
            "Iterations: {}/{}, Arc residual: {:.6e}, Tracking RMS: {:.6e}, Build time: {:.2}ms",
            iter_count, params.max_iter, arc_res_max, tracking_rms, t0.elapsed().as_secs_f64() * 1000.0
        ),
        format!(
            "Sliding velocity: mean={:.6e}, max={:.6e}",
            sliding_vel_mean, sliding_vel_max
        ),
        format!(
            "Profile={:?}, jerk_max_piston={:.6e}, jerk_max_rampAnalytic={:.6e}",
            params.ramp_profile, jerk_max_piston, jerk_ml_max
        )
    ];

    let diagnostics = Diagnostics {
        arc_length_residual_max: arc_res_max,
        arc_length_residual_rms: arc_res_rms,
        iter_count,
        used_max_iter,
        regularization_applied,
        clearance_min,
        clearance_violations: violations,
        envelope_clearance_min: env_clearance_min,
        envelope_violations: env_violations,
        tooth_thickness_min,
        undercut_flag,
        curvature_radius_min,
        tracking_rms,
        accel_max,
        jerk_max,
        sliding_vel_mean,
        sliding_vel_max,
        nvh_peaks,
        suggested_center_distance_inflation: if clearance_min < 0.0 { -clearance_min + 0.01 } else { 0.0 },
        build_ms: t0.elapsed().as_secs_f64() * 1000.0,
        notes,
    };

    // Pitch curves to emit
    let curves = PitchCurves { theta_deg, r_cam, phi_deg, r_ring, s_cam, s_ring, phi_of_theta_deg };

    Ok(LitvinTables { params: params.clone(), curves, alpha_deg, planets, diagnostics })
}


#[cfg(test)]
mod tests {
    use super::*;

    fn test_params() -> LitvinParameters {
        let mut p = LitvinParameters::default();
        // Finer grid to reflect Gate B residual expectations while keeping runtime modest
        p.sampling_step_deg = 2.0;
        // Set explicit tolerance we can assert against without changing defaults
        p.arc_residual_tol_mm = 0.08;
        p.max_iter = 25;
        p
    }

    #[test]
    fn gateb_arc_length_residual_respects_tolerance() {
        let p = test_params();
        let tables = build_litvin_tables(&p).expect("build_litvin_tables failed");
        let d = tables.diagnostics;
        assert!(d.arc_length_residual_max.is_finite());
        assert!(d.arc_length_residual_rms.is_finite());
        assert!(d.arc_length_residual_max <= p.arc_residual_tol_mm + 1e-9,
            "Arc residual max {:.6e} > tol {:.6e}", d.arc_length_residual_max, p.arc_residual_tol_mm);
    }

    #[test]
    fn gateb_phi_monotonic_and_periodic() {
        let p = test_params();
        let tables = build_litvin_tables(&p).expect("build_litvin_tables failed");
        let phi = &tables.curves.phi_of_theta_deg;
        let n = phi.len();
        assert!(n > 3, "phi_of_theta length too small");
        // Periodic endpoints and range
        assert!((phi[0] - 0.0).abs() < 1e-9, "phi(0) should be 0");
        let max_phi = 360.0 - p.sampling_step_deg;
        assert!(phi[n - 1] <= max_phi + 1e-9, "phi(last) <= 360 - step");
        // Monotone non-decreasing
        for i in 1..n {
            assert!(phi[i] + 1e-12 >= phi[i - 1], "phi not monotone at i={}, {} < {}", i, phi[i], phi[i - 1]);
        }
    }

    #[test]
    fn gateb_determinism_same_params_same_output() {
        let p = test_params();
        let t1 = build_litvin_tables(&p).expect("build 1 failed");
        let t2 = build_litvin_tables(&p).expect("build 2 failed");
        let a1 = &t1.curves.phi_of_theta_deg;
        let a2 = &t2.curves.phi_of_theta_deg;
        assert_eq!(a1.len(), a2.len());
        for i in 0..a1.len() {
            let d = (a1[i] - a2[i]).abs();
            assert!(d < 1e-12, "determinism violated at {}: {} vs {} (|Δ|={})", i, a1[i], a2[i], d);
        }
    }

    #[test]
    fn gateb_transmission_from_phi_is_finite_positive_and_mean_near_one() {
        let p = test_params();
        let tables = build_litvin_tables(&p).expect("build_litvin_tables failed");
        let phi = &tables.curves.phi_of_theta_deg;
        let n = phi.len();
        let step = p.sampling_step_deg;
        let denom = 2.0 * step;
        assert!(denom > 0.0);
        let mut i_vals: Vec<f64> = Vec::with_capacity(n);
        for i in 0..n {
            let ip = (i + 1) % n;
            let im = (i + n - 1) % n;
            let mut dphi = phi[ip] - phi[im];
            if dphi < -180.0 { dphi += 360.0; } else if dphi > 180.0 { dphi -= 360.0; }
            let i_theta = dphi / denom;
            assert!(i_theta.is_finite(), "i(θ) not finite at {}", i);
            i_vals.push(i_theta);
        }
        let min_i = i_vals
            .iter()
            .fold(f64::INFINITY, |a, &b| a.min(b));
        assert!(min_i > 0.0, "transmission contains non-positive values: min={}", min_i);
        let mean = i_vals.iter().sum::<f64>() / (i_vals.len() as f64);
        // Expect mean close to 1.0 within a moderate tolerance
        assert!((mean - 1.0).abs() <= 0.2, "mean(i) not near 1.0: {}", mean);
    }
}
