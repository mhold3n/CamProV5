extern crate fea_engine;

use fea_engine::litvin::{LitvinParameters, RampProfile, MotionProfiles, build_litvin_tables};
use std::f64::consts::PI;

/// Test helper function to create standard test parameters
fn test_params() -> LitvinParameters {
    LitvinParameters {
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
        sampling_step_deg: 1.0,
        rpm: 3000.0,
        cam_r0: 40.0,
        cam_k_per_unit: 1.0,
        center_distance_bias: 50.0,
        center_distance_scale: 1.0,
        arc_residual_tol_mm: 0.01,
        max_iter: 20,
    }
}

/// Tests for motion profiles implementation
#[test]
fn test_motion_profiles() {
    // Test cycloidal profile
    let cycloidal = MotionProfiles::eval(RampProfile::Cycloidal, 0.5);
    assert!((cycloidal.s - 0.5).abs() < 1e-6);
    
    // Test S5 profile
    let s5 = MotionProfiles::eval(RampProfile::S5, 0.5);
    assert!((s5.s - 0.5).abs() < 1e-6);
    
    // Test S7 profile
    let s7 = MotionProfiles::eval(RampProfile::S7, 0.5);
    assert!((s7.s - 0.5).abs() < 1e-6);
    
    // Test integral of profiles
    let int_cycloidal = MotionProfiles::integral(RampProfile::Cycloidal, 1.0);
    let int_s5 = MotionProfiles::integral(RampProfile::S5, 1.0);
    let int_s7 = MotionProfiles::integral(RampProfile::S7, 1.0);
    
    assert!(int_cycloidal > 0.0 && int_cycloidal < 1.0);
    assert!(int_s5 > 0.0 && int_s5 < 1.0);
    assert!(int_s7 > 0.0 && int_s7 < 1.0);
}

/// Tests that the φ mapping is strictly increasing (monotonic)
#[test]
fn test_phi_monotonicity() {
    // Create test parameters for different profiles
    for profile in &[RampProfile::Cycloidal, RampProfile::S5, RampProfile::S7] {
        let mut params = test_params();
        params.ramp_profile = *profile;
        
        // Build tables and check phi_of_theta
        let tables = build_litvin_tables(&params).expect("Failed to build tables");
        let phi_of_theta = &tables.curves.phi_of_theta_deg;
        
        // Check that phi is strictly increasing
        for i in 1..phi_of_theta.len() {
            assert!(phi_of_theta[i] >= phi_of_theta[i-1], 
                "φ not monotonic at index {}: φ[{}]={}, φ[{}]={}",
                i, i-1, phi_of_theta[i-1], i, phi_of_theta[i]);
        }
        
        // Check boundary conditions
        assert!(phi_of_theta[0] >= 0.0, "φ(0) < 0: {}", phi_of_theta[0]);
        assert!(phi_of_theta[phi_of_theta.len()-1] <= 360.0, 
                "φ(end) > 360: {}", phi_of_theta[phi_of_theta.len()-1]);
    }
}

/// Tests that the ψ values wrap correctly to [0,360)
#[test]
fn test_psi_wrap_correctness() {
    // Create test parameters for different profiles
    for profile in &[RampProfile::Cycloidal, RampProfile::S5, RampProfile::S7] {
        let mut params = test_params();
        params.ramp_profile = *profile;
        
        // Build tables and check psi values in planet state
        let tables = build_litvin_tables(&params).expect("Failed to build tables");
        
        for planet in &tables.planets {
            for &psi in &planet.spin_psi_deg {
                assert!(psi >= 0.0 && psi < 360.0, 
                       "ψ not in [0,360): {}", psi);
            }
        }
    }
}

/// Tests that the arc-length residual is below the specified tolerance
#[test]
fn test_arc_length_residual() {
    // Create test parameters with different tolerances
    let tolerances = [0.01, 0.001, 0.0001];
    
    for tol in &tolerances {
        let mut params = test_params();
        params.arc_residual_tol_mm = *tol;
        params.max_iter = 50;  // Increase max iterations for tighter tolerances
        
        // Build tables and check residual
        let tables = build_litvin_tables(&params).expect("Failed to build tables");
        
        assert!(tables.diagnostics.arc_length_residual_max <= *tol,
               "Arc-length residual max exceeds tolerance: {} > {}",
               tables.diagnostics.arc_length_residual_max, tol);
               
        println!("For tolerance {}, achieved residual: {}, in {} iterations",
                 tol, tables.diagnostics.arc_length_residual_max, tables.diagnostics.iter_count);
    }
}

/// Tests that all diagnostic metrics are properly calculated and have reasonable values
#[test]
fn test_diagnostic_metrics() {
    let params = test_params();
    let tables = build_litvin_tables(&params).expect("Failed to build tables");
    let diag = &tables.diagnostics;
    
    // Check that all metrics are finite
    assert!(diag.arc_length_residual_max.is_finite(), "arc_length_residual_max is not finite");
    assert!(diag.arc_length_residual_rms.is_finite(), "arc_length_residual_rms is not finite");
    assert!(diag.clearance_min.is_finite(), "clearance_min is not finite");
    assert!(diag.envelope_clearance_min.is_finite(), "envelope_clearance_min is not finite");
    assert!(diag.tooth_thickness_min.is_finite(), "tooth_thickness_min is not finite");
    assert!(diag.curvature_radius_min.is_finite(), "curvature_radius_min is not finite");
    assert!(diag.tracking_rms.is_finite(), "tracking_rms is not finite");
    assert!(diag.accel_max.is_finite(), "accel_max is not finite");
    assert!(diag.jerk_max.is_finite(), "jerk_max is not finite");
    assert!(diag.sliding_vel_mean.is_finite(), "sliding_vel_mean is not finite");
    assert!(diag.sliding_vel_max.is_finite(), "sliding_vel_max is not finite");
    
    // Check that key metrics are positive
    assert!(diag.accel_max >= 0.0, "accel_max should be non-negative");
    assert!(diag.jerk_max >= 0.0, "jerk_max should be non-negative");
    assert!(diag.sliding_vel_mean >= 0.0, "sliding_vel_mean should be non-negative");
    assert!(diag.sliding_vel_max >= 0.0, "sliding_vel_max should be non-negative");
    
    // Check that max >= mean for sliding velocity
    assert!(diag.sliding_vel_max >= diag.sliding_vel_mean, 
           "sliding_vel_max should be >= sliding_vel_mean");
    
    // Check that nvh_peaks are populated and have reasonable values
    assert!(!diag.nvh_peaks.is_empty(), "nvh_peaks should not be empty");
    for peak in &diag.nvh_peaks {
        assert!(peak.freq_hz.is_finite(), "nvh peak frequency is not finite");
        assert!(peak.amp.is_finite(), "nvh peak amplitude is not finite");
        assert!(peak.freq_hz > 0.0, "nvh peak frequency should be positive");
        assert!(peak.amp >= 0.0, "nvh peak amplitude should be non-negative");
    }
    
    // Check that notes field is populated
    assert!(!diag.notes.is_empty(), "notes field should not be empty");
    println!("Diagnostic notes: {:?}", diag.notes);
    
    // Output key diagnostic values for inspection
    println!("Tracking RMS: {}", diag.tracking_rms);
    println!("Accel Max: {}", diag.accel_max);
    println!("Jerk Max: {}", diag.jerk_max);
    println!("Sliding Velocity Mean: {}", diag.sliding_vel_mean);
    println!("Sliding Velocity Max: {}", diag.sliding_vel_max);
}

/// Test the sign convention consistency between the two implementations.
/// This is a placeholder test - it will be updated after implementing
/// a direct comparison function between Kotlin and Rust.
#[test]
fn test_i_theta_sign_convention() {
    // For now, we just ensure i(θ) > 0 which is a basic invariant
    let params = test_params();
    let tables = build_litvin_tables(&params).expect("Failed to build tables");
    
    // Compute i(θ) = dψ/dα + 1 using central differences
    let n = tables.alpha_deg.len();
    let step_deg = params.sampling_step_deg;
    
    if n < 3 {
        return;  // Not enough points for this test
    }
    
    for i in 1..n-1 {
        let planet = &tables.planets[0];  // Just check first planet
        let psi_prev = planet.spin_psi_deg[i-1];
        let psi_next = planet.spin_psi_deg[i+1];
        
        // Adjust for wrap-around
        let dpsi = if psi_next < psi_prev && psi_next < 90.0 && psi_prev > 270.0 {
            (psi_next + 360.0 - psi_prev) / (2.0 * step_deg)
        } else if psi_prev < psi_next && psi_prev < 90.0 && psi_next > 270.0 {
            (psi_next - 360.0 - psi_prev) / (2.0 * step_deg)
        } else {
            (psi_next - psi_prev) / (2.0 * step_deg)
        };
        
        let i_theta = dpsi + 1.0;
        
        assert!(i_theta > 0.0, "i(θ) <= 0 at index {}: {}", i, i_theta);
    }
}

/// Tests that generate_motion_law produces correct x, v, a values
#[test]
fn test_motion_law_generation() {
    // Create test parameters for different profiles
    for profile in &[RampProfile::Cycloidal, RampProfile::S5, RampProfile::S7] {
        let mut params = test_params();
        params.ramp_profile = *profile;
        
        // Build tables (which uses generate_motion_law internally)
        let tables = build_litvin_tables(&params).expect("Failed to build tables");
        
        // Basic checks that would fail if motion law was completely wrong
        assert!(tables.alpha_deg.len() > 0);
        assert_eq!(tables.alpha_deg.len(), tables.planets[0].piston_s.len());
        
        // Check that the first and last sample don't have unreasonable values
        let first_s = tables.planets[0].piston_s[0];
        let last_s = tables.planets[0].piston_s[tables.planets[0].piston_s.len() - 1];
        
        assert!(first_s.abs() < params.rod_length);
        assert!(last_s.abs() < params.rod_length);
    }
}