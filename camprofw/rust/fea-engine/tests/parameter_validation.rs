
//! Parameter validation test for CamProV5
//!
//! This binary reads motion parameters from a JSON file, performs calculations,
//! and writes the results to another JSON file for comparison with Python.

use fea_engine::{load_motion_parameters_from_json, create_motion_law};
use std::fs;
use std::env;
use std::path::Path;

fn main() {
    // Get input and output file paths from command line arguments
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <input_json_path> <output_json_path>", args[0]);
        std::process::exit(1);
    }
    
    let input_path = &args[1];
    let output_path = &args[2];
    
    // Read input JSON
    let json_str = fs::read_to_string(input_path)
        .expect("Failed to read input file");
    
    // Parse motion parameters
    let params = load_motion_parameters_from_json(&json_str)
        .expect("Failed to parse motion parameters");
    
    // Create motion law
    let motion = create_motion_law(params)
        .expect("Failed to create motion law");
    
    // Generate test points
    let theta_values: Vec<f64> = (0..360).map(|i| i as f64).collect();
    
    // Calculate kinematics
    let displacement: Vec<f64> = theta_values.iter()
        .map(|&theta| motion.displacement(theta))
        .collect();
    
    let velocity: Vec<f64> = theta_values.iter()
        .map(|&theta| motion.velocity(theta))
        .collect();
    
    let acceleration: Vec<f64> = theta_values.iter()
        .map(|&theta| motion.acceleration(theta))
        .collect();
    
    let jerk: Vec<f64> = theta_values.iter()
        .map(|&theta| motion.jerk(theta))
        .collect();
    
    // Create output JSON
    let output = serde_json::json!({
        "theta": theta_values,
        "displacement": displacement,
        "velocity": velocity,
        "acceleration": acceleration,
        "jerk": jerk
    });
    
    // Write output JSON
    fs::write(output_path, serde_json::to_string_pretty(&output).unwrap())
        .expect("Failed to write output file");
}
