use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use fea_engine::motion_law::{MotionLaw, MotionParameters};
use std::time::Duration;

// Helper function to create a motion law with default parameters
fn create_default_motion_law() -> MotionLaw {
    let params = MotionParameters::default();
    MotionLaw::new(params).unwrap()
}

// Helper function to create a motion law with high RPM
fn create_high_rpm_motion_law() -> MotionLaw {
    let mut params = MotionParameters::default();
    params.rpm = 6000.0;
    MotionLaw::new(params).unwrap()
}

// Helper function to create a vector of angles for testing
fn create_angle_vector(size: usize) -> Vec<f64> {
    (0..size).map(|i| (i as f64 * 360.0) / size as f64).collect()
}

// Helper function to create a vector of time steps for testing
fn create_time_vector(size: usize) -> Vec<f64> {
    let motion = create_default_motion_law();
    let omega = motion.parameters().omega();
    let period = 2.0 * std::f64::consts::PI / omega;
    (0..size).map(|i| (i as f64 * period) / size as f64).collect()
}

// Benchmark single-threaded performance
fn bench_single_threaded(c: &mut Criterion) {
    let motion = create_default_motion_law();
    let high_rpm_motion = create_high_rpm_motion_law();
    
    // Benchmark displacement calculation
    let mut group = c.benchmark_group("displacement");
    group.measurement_time(Duration::from_secs(10));
    
    for angle in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0].iter() {
        group.bench_with_input(BenchmarkId::new("default_rpm", angle), angle, |b, &angle| {
            b.iter(|| motion.displacement(black_box(angle)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", angle), angle, |b, &angle| {
            b.iter(|| high_rpm_motion.displacement(black_box(angle)))
        });
    }
    group.finish();
    
    // Benchmark velocity calculation
    let mut group = c.benchmark_group("velocity");
    group.measurement_time(Duration::from_secs(10));
    
    for angle in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0].iter() {
        group.bench_with_input(BenchmarkId::new("default_rpm", angle), angle, |b, &angle| {
            b.iter(|| motion.velocity(black_box(angle)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", angle), angle, |b, &angle| {
            b.iter(|| high_rpm_motion.velocity(black_box(angle)))
        });
    }
    group.finish();
    
    // Benchmark acceleration calculation
    let mut group = c.benchmark_group("acceleration");
    group.measurement_time(Duration::from_secs(10));
    
    for angle in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0].iter() {
        group.bench_with_input(BenchmarkId::new("default_rpm", angle), angle, |b, &angle| {
            b.iter(|| motion.acceleration(black_box(angle)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", angle), angle, |b, &angle| {
            b.iter(|| high_rpm_motion.acceleration(black_box(angle)))
        });
    }
    group.finish();
    
    // Benchmark jerk calculation
    let mut group = c.benchmark_group("jerk");
    group.measurement_time(Duration::from_secs(10));
    
    for angle in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0].iter() {
        group.bench_with_input(BenchmarkId::new("default_rpm", angle), angle, |b, &angle| {
            b.iter(|| motion.jerk(black_box(angle)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", angle), angle, |b, &angle| {
            b.iter(|| high_rpm_motion.jerk(black_box(angle)))
        });
    }
    group.finish();
    
    // Benchmark boundary condition calculation
    let mut group = c.benchmark_group("boundary_condition_at_time");
    group.measurement_time(Duration::from_secs(10));
    
    let time_steps = create_time_vector(8);
    for &time in time_steps.iter() {
        group.bench_with_input(BenchmarkId::new("default_rpm", time), &time, |b, &time| {
            b.iter(|| motion.boundary_condition_at_time(black_box(*time)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", time), &time, |b, &time| {
            b.iter(|| high_rpm_motion.boundary_condition_at_time(black_box(*time)))
        });
    }
    group.finish();
}

// Benchmark parallel performance
fn bench_parallel(c: &mut Criterion) {
    let motion = create_default_motion_law();
    let high_rpm_motion = create_high_rpm_motion_law();
    
    // Benchmark parallel displacement calculation with different input sizes
    let mut group = c.benchmark_group("displacement_parallel");
    group.measurement_time(Duration::from_secs(10));
    
    for size in [100, 1000, 10000, 100000].iter() {
        let angles = create_angle_vector(*size);
        
        group.bench_with_input(BenchmarkId::new("default_rpm", size), size, |b, _| {
            b.iter(|| motion.displacement_parallel(black_box(&angles)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", size), size, |b, _| {
            b.iter(|| high_rpm_motion.displacement_parallel(black_box(&angles)))
        });
    }
    group.finish();
    
    // Benchmark parallel velocity calculation with different input sizes
    let mut group = c.benchmark_group("velocity_parallel");
    group.measurement_time(Duration::from_secs(10));
    
    for size in [100, 1000, 10000, 100000].iter() {
        let angles = create_angle_vector(*size);
        
        group.bench_with_input(BenchmarkId::new("default_rpm", size), size, |b, _| {
            b.iter(|| motion.velocity_parallel(black_box(&angles)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", size), size, |b, _| {
            b.iter(|| high_rpm_motion.velocity_parallel(black_box(&angles)))
        });
    }
    group.finish();
    
    // Benchmark parallel acceleration calculation with different input sizes
    let mut group = c.benchmark_group("acceleration_parallel");
    group.measurement_time(Duration::from_secs(10));
    
    for size in [100, 1000, 10000, 100000].iter() {
        let angles = create_angle_vector(*size);
        
        group.bench_with_input(BenchmarkId::new("default_rpm", size), size, |b, _| {
            b.iter(|| motion.acceleration_parallel(black_box(&angles)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", size), size, |b, _| {
            b.iter(|| high_rpm_motion.acceleration_parallel(black_box(&angles)))
        });
    }
    group.finish();
    
    // Benchmark parallel jerk calculation with different input sizes
    let mut group = c.benchmark_group("jerk_parallel");
    group.measurement_time(Duration::from_secs(10));
    
    for size in [100, 1000, 10000, 100000].iter() {
        let angles = create_angle_vector(*size);
        
        group.bench_with_input(BenchmarkId::new("default_rpm", size), size, |b, _| {
            b.iter(|| motion.jerk_parallel(black_box(&angles)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", size), size, |b, _| {
            b.iter(|| high_rpm_motion.jerk_parallel(black_box(&angles)))
        });
    }
    group.finish();
    
    // Benchmark boundary conditions calculation with different input sizes
    let mut group = c.benchmark_group("boundary_conditions");
    group.measurement_time(Duration::from_secs(10));
    
    for size in [100, 1000, 10000, 100000].iter() {
        let time_steps = create_time_vector(*size);
        
        group.bench_with_input(BenchmarkId::new("default_rpm", size), size, |b, _| {
            b.iter(|| motion.boundary_conditions(black_box(&time_steps)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", size), size, |b, _| {
            b.iter(|| high_rpm_motion.boundary_conditions(black_box(&time_steps)))
        });
    }
    group.finish();
    
    // Benchmark kinematic analysis with different input sizes
    let mut group = c.benchmark_group("analyze_kinematics");
    group.measurement_time(Duration::from_secs(10));
    
    for size in [100, 1000, 10000].iter() {
        group.bench_with_input(BenchmarkId::new("default_rpm", size), size, |b, &size| {
            b.iter(|| motion.analyze_kinematics(black_box(size)))
        });
        
        group.bench_with_input(BenchmarkId::new("high_rpm", size), size, |b, &size| {
            b.iter(|| high_rpm_motion.analyze_kinematics(black_box(size)))
        });
    }
    group.finish();
}

// Benchmark memory usage patterns during long simulations
fn bench_memory_usage(c: &mut Criterion) {
    let motion = create_default_motion_law();
    
    let mut group = c.benchmark_group("memory_usage");
    group.measurement_time(Duration::from_secs(30));
    group.sample_size(10);
    
    // Benchmark memory usage for large kinematic analysis
    for size in [10000, 100000, 1000000].iter() {
        group.bench_with_input(BenchmarkId::new("analyze_kinematics", size), size, |b, &size| {
            b.iter(|| motion.analyze_kinematics(black_box(size)))
        });
    }
    
    // Benchmark memory usage for large boundary condition calculations
    for size in [10000, 100000, 1000000].iter() {
        let time_steps = create_time_vector(*size);
        group.bench_with_input(BenchmarkId::new("boundary_conditions", size), size, |b, _| {
            b.iter(|| motion.boundary_conditions(black_box(&time_steps)))
        });
    }
    
    group.finish();
}

// Benchmark numerical stability over extended time periods
fn bench_numerical_stability(c: &mut Criterion) {
    let motion = create_default_motion_law();
    
    let mut group = c.benchmark_group("numerical_stability");
    group.measurement_time(Duration::from_secs(30));
    group.sample_size(10);
    
    // Test stability by calculating displacement at very small angle increments
    // over multiple complete rotations
    let rotations = 100;
    let points_per_rotation = 3600; // 0.1 degree increments
    let total_points = rotations * points_per_rotation;
    
    group.bench_function("displacement_stability", |b| {
        b.iter(|| {
            let mut sum = 0.0;
            for i in 0..total_points {
                let angle = (i as f64 * 360.0) / points_per_rotation as f64;
                sum += motion.displacement(black_box(angle));
            }
            sum
        })
    });
    
    // Test stability by calculating velocity at very small angle increments
    group.bench_function("velocity_stability", |b| {
        b.iter(|| {
            let mut sum = 0.0;
            for i in 0..total_points {
                let angle = (i as f64 * 360.0) / points_per_rotation as f64;
                sum += motion.velocity(black_box(angle));
            }
            sum
        })
    });
    
    // Test stability by calculating acceleration at very small angle increments
    group.bench_function("acceleration_stability", |b| {
        b.iter(|| {
            let mut sum = 0.0;
            for i in 0..total_points {
                let angle = (i as f64 * 360.0) / points_per_rotation as f64;
                sum += motion.acceleration(black_box(angle));
            }
            sum
        })
    });
    
    group.finish();
}

criterion_group!(
    benches,
    bench_single_threaded,
    bench_parallel,
    bench_memory_usage,
    bench_numerical_stability
);
criterion_main!(benches);