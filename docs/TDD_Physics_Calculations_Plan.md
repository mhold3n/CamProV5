# TDD Plan for Missing Physics Calculations

## Overview

This document outlines a comprehensive Test-Driven Development (TDD) plan for implementing the missing physics calculations in the planetary gearset optimization system. The plan follows the TDD cycle: **Red → Green → Refactor**.

## 1. Core Physics Calculations Required

Based on the optimization results and theoretical framework, we need to implement:

### 1.1 Piston Force Calculations
- **Cylinder pressure forces** (combustion pressure)
- **Inertial forces** (piston acceleration)
- **Friction forces** (velocity-dependent)
- **Net piston force** (sum of all forces)

### 1.2 Contact Force Calculations
- **Sun-planet contact forces** (Hertzian contact model)
- **Planet-ring contact forces** (reaction forces)
- **Contact stiffness** (geometry-dependent)
- **Dynamic force amplification** (gear ratio effects)

### 1.3 Mechanical Advantage (MA) Calculations
- **MA from forces** (torque/force ratio)
- **MA from kinematics** (velocity ratio)
- **Effective lever arms** (geometry-dependent)
- **MA sensitivity** (profile change response)

### 1.4 Transfer Efficiency Calculations
- **Input power** (piston force × velocity)
- **Output power** (ring torque × angular velocity)
- **Energy losses** (Hertzian, friction, deformation, windage)
- **Net efficiency** (output/input power)

### 1.5 FEA Integration
- **Stress analysis** (Von Mises, Hertzian contact)
- **Vibration analysis** (modal, NVH)
- **Safety factors** (yield strength, fatigue)
- **FEA penalties** (optimization constraints)

## 2. TDD Implementation Plan

### Phase 1: Piston Force Calculations

#### Test 1.1: Basic Piston Force Calculation
```python
def test_piston_force_basic():
    """Test basic piston force calculation with known inputs."""
    # Given
    displacement = np.array([0.0, 50.0, 100.0])  # mm
    velocity = np.array([0.0, 100.0, 0.0])  # mm/s
    acceleration = np.array([1000.0, 0.0, -1000.0])  # mm/s²
    params = {
        "cylinderPressure": 2.0e5,  # Pa
        "pistonArea": 0.01,  # m²
        "pistonMass": 5.0,  # kg
        "frictionCoefficient": 0.05
    }
    
    # When
    forces = calculate_piston_forces(displacement, velocity, acceleration, params)
    
    # Then
    assert len(forces) == 3
    assert forces[0] > 0  # Positive force at TDC
    assert forces[1] > 0  # Positive force during expansion
    assert forces[2] < 0  # Negative force at BDC (compression)
    assert np.all(np.isfinite(forces))  # No NaN or infinite values
```

#### Test 1.2: Piston Force Sensitivity to Parameters
```python
def test_piston_force_sensitivity():
    """Test that piston forces change with parameter variations."""
    # Given baseline parameters
    baseline_params = get_baseline_physics_params()
    displacement, velocity, acceleration = get_baseline_motion_law()
    
    # When calculating baseline forces
    baseline_forces = calculate_piston_forces(displacement, velocity, acceleration, baseline_params)
    
    # Then test sensitivity to cylinder pressure
    high_pressure_params = baseline_params.copy()
    high_pressure_params["cylinderPressure"] *= 2.0
    high_pressure_forces = calculate_piston_forces(displacement, velocity, acceleration, high_pressure_params)
    
    # Forces should increase with pressure
    assert np.mean(high_pressure_forces) > np.mean(baseline_forces)
    assert np.all(high_pressure_forces > baseline_forces)
    
    # Test sensitivity to piston mass
    high_mass_params = baseline_params.copy()
    high_mass_params["pistonMass"] *= 2.0
    high_mass_forces = calculate_piston_forces(displacement, velocity, acceleration, high_mass_params)
    
    # Inertial forces should increase with mass
    assert np.std(high_mass_forces) > np.std(baseline_forces)  # More variation due to inertia
```

#### Test 1.3: Friction Force Dependencies
```python
def test_friction_force_dependencies():
    """Test that friction forces depend on velocity and direction."""
    # Given
    displacement = np.array([50.0, 50.0, 50.0])
    velocity = np.array([-100.0, 0.0, 100.0])  # Negative, zero, positive
    acceleration = np.array([0.0, 0.0, 0.0])
    params = get_baseline_physics_params()
    
    # When
    forces = calculate_piston_forces(displacement, velocity, acceleration, params)
    
    # Then
    # Friction should oppose motion
    assert forces[0] > forces[1]  # Negative velocity → higher friction
    assert forces[2] > forces[1]  # Positive velocity → higher friction
    assert forces[1] == forces[1]  # Zero velocity → no friction
```

### Phase 2: Contact Force Calculations

#### Test 2.1: Basic Contact Force Calculation
```python
def test_contact_force_basic():
    """Test basic contact force calculation between gears."""
    # Given
    gear_profiles = {
        "r_sun": np.array([110.0, 115.0, 120.0]),  # mm
        "r_planet": np.array([175.0, 180.0, 185.0]),  # mm
        "r_ring_inner": np.array([460.0, 470.0, 480.0])  # mm
    }
    planets = [{"omega": 100.0, "alpha": 10.0}]  # rad/s, rad/s²
    params = get_baseline_physics_params()
    piston_forces = np.array([1000.0, 1200.0, 800.0])  # N
    
    # When
    contact_forces = calculate_contact_forces(gear_profiles, planets, params, piston_forces)
    
    # Then
    assert "sun_planet" in contact_forces
    assert "planet_ring" in contact_forces
    assert "total_contact" in contact_forces
    assert len(contact_forces["sun_planet"]) == 3
    assert np.all(contact_forces["sun_planet"] > 0)  # Positive contact forces
    assert np.all(contact_forces["planet_ring"] > 0)  # Positive reaction forces
```

#### Test 2.2: Contact Force Sensitivity to Gear Geometry
```python
def test_contact_force_geometry_sensitivity():
    """Test that contact forces change with gear profile variations."""
    # Given baseline profiles
    baseline_profiles = get_baseline_gear_profiles()
    planets = get_baseline_planets()
    params = get_baseline_physics_params()
    piston_forces = get_baseline_piston_forces()
    
    # When calculating baseline contact forces
    baseline_contact = calculate_contact_forces(baseline_profiles, planets, params, piston_forces)
    
    # Then test sensitivity to gear size changes
    modified_profiles = baseline_profiles.copy()
    modified_profiles["r_planet"] *= 1.1  # 10% larger planet
    
    modified_contact = calculate_contact_forces(modified_profiles, planets, params, piston_forces)
    
    # Contact forces should change with gear geometry
    assert not np.allclose(baseline_contact["sun_planet"], modified_contact["sun_planet"], rtol=1e-6)
    assert not np.allclose(baseline_contact["planet_ring"], modified_contact["planet_ring"], rtol=1e-6)
    
    # Test sensitivity to gear ratio changes
    ratio_modified_profiles = baseline_profiles.copy()
    ratio_modified_profiles["r_sun"] *= 0.9  # 10% smaller sun
    ratio_modified_profiles["r_ring_inner"] *= 0.9  # 10% smaller ring
    
    ratio_modified_contact = calculate_contact_forces(ratio_modified_profiles, planets, params, piston_forces)
    
    # Contact forces should change with gear ratio
    assert not np.allclose(baseline_contact["total_contact"], ratio_modified_contact["total_contact"], rtol=1e-6)
```

#### Test 2.3: Hertzian Contact Model
```python
def test_hertzian_contact_model():
    """Test that contact forces follow Hertzian contact theory."""
    # Given
    gear_profiles = {
        "r_sun": np.array([110.0, 110.0, 110.0]),  # Constant radius
        "r_planet": np.array([175.0, 175.0, 175.0]),  # Constant radius
        "r_ring_inner": np.array([460.0, 460.0, 460.0])  # Constant radius
    }
    planets = [{"omega": 100.0, "alpha": 0.0}]
    params = get_baseline_physics_params()
    piston_forces = np.array([1000.0, 1000.0, 1000.0])  # Constant force
    
    # When
    contact_forces = calculate_contact_forces(gear_profiles, planets, params, piston_forces)
    
    # Then
    # For constant geometry and force, contact forces should be constant
    assert np.allclose(contact_forces["sun_planet"], contact_forces["sun_planet"][0], rtol=1e-6)
    assert np.allclose(contact_forces["planet_ring"], contact_forces["planet_ring"][0], rtol=1e-6)
    
    # Test Hertzian scaling: force ∝ (radius)^(-0.5)
    small_gear_profiles = gear_profiles.copy()
    small_gear_profiles["r_planet"] *= 0.5  # Half radius
    
    small_contact = calculate_contact_forces(small_gear_profiles, planets, params, piston_forces)
    
    # Smaller gears should have higher contact forces (Hertzian scaling)
    assert np.all(small_contact["sun_planet"] > contact_forces["sun_planet"])
```

### Phase 3: Mechanical Advantage Calculations

#### Test 3.1: Basic MA Calculation
```python
def test_mechanical_advantage_basic():
    """Test basic mechanical advantage calculation."""
    # Given
    piston_forces = np.array([1000.0, 1200.0, 800.0])  # N
    contact_forces = {
        "sun_planet": np.array([500.0, 600.0, 400.0]),  # N
        "planet_ring": np.array([500.0, 600.0, 400.0])  # N
    }
    gear_profiles = {
        "r_sun": np.array([110.0, 115.0, 120.0]),  # mm
        "r_planet": np.array([175.0, 180.0, 185.0]),  # mm
        "r_ring_inner": np.array([460.0, 470.0, 480.0])  # mm
    }
    params = get_baseline_physics_params()
    
    # When
    ma = calculate_mechanical_advantage(piston_forces, contact_forces, gear_profiles, params)
    
    # Then
    assert len(ma) == 3
    assert np.all(ma > 0)  # Positive MA
    assert np.all(np.isfinite(ma))  # No NaN or infinite values
    
    # MA should be reasonable (typically 0.5 to 5.0 for planetary gearsets)
    assert np.all(ma >= 0.1)
    assert np.all(ma <= 10.0)
```

#### Test 3.2: MA Sensitivity to Profile Changes
```python
def test_ma_sensitivity_to_profile_changes():
    """Test that MA changes with gear profile modifications."""
    # Given baseline setup
    baseline_profiles = get_baseline_gear_profiles()
    baseline_planets = get_baseline_planets()
    baseline_params = get_baseline_physics_params()
    
    # Generate baseline motion law
    theta_deg, displacement, velocity, acceleration = generate_motion_law(baseline_params)
    baseline_piston_forces = calculate_piston_forces(displacement, velocity, acceleration, baseline_params)
    baseline_contact_forces = calculate_contact_forces(baseline_profiles, baseline_planets, baseline_params, baseline_piston_forces)
    baseline_ma = calculate_mechanical_advantage(baseline_piston_forces, baseline_contact_forces, baseline_profiles, baseline_params)
    
    # When modifying gear profiles
    modified_profiles = baseline_profiles.copy()
    modified_profiles["r_planet"] *= 1.1  # 10% larger planet
    modified_profiles["r_sun"] *= 1.1     # 10% larger sun
    modified_profiles["r_ring_inner"] *= 1.1  # 10% larger ring
    
    modified_contact_forces = calculate_contact_forces(modified_profiles, baseline_planets, baseline_params, baseline_piston_forces)
    modified_ma = calculate_mechanical_advantage(baseline_piston_forces, modified_contact_forces, modified_profiles, baseline_params)
    
    # Then MA should change
    ma_difference = np.mean(np.abs(modified_ma - baseline_ma))
    assert ma_difference > 0.01  # At least 1% change in MA
    
    # Test with optimization variables
    opt_vars = {
        "planet_coeff_1": 0.1,
        "planet_coeff_2": 0.05,
        "sun_coeff_1": -0.1,
        "sun_coeff_2": -0.05
    }
    
    opt_modified_profiles = apply_profile_optimization(baseline_profiles, opt_vars, baseline_params)
    opt_modified_contact_forces = calculate_contact_forces(opt_modified_profiles, baseline_planets, baseline_params, baseline_piston_forces)
    opt_modified_ma = calculate_mechanical_advantage(baseline_piston_forces, opt_modified_contact_forces, opt_modified_profiles, baseline_params)
    
    # MA should change with optimization variables
    opt_ma_difference = np.mean(np.abs(opt_modified_ma - baseline_ma))
    assert opt_ma_difference > 0.005  # At least 0.5% change in MA
```

#### Test 3.3: MA Target Range Compliance
```python
def test_ma_target_range_compliance():
    """Test that MA calculations can achieve target ranges."""
    # Given target MA range
    target_ma_min = 0.8
    target_ma_max = 1.15
    
    # When calculating MA for different configurations
    configs = [
        {"planetRadiusBaseFactor": 0.1, "sunRadiusBaseFactor": 0.05},  # Small gears
        {"planetRadiusBaseFactor": 0.2, "sunRadiusBaseFactor": 0.15},  # Large gears
        {"planetRadiusBaseFactor": 0.15, "sunRadiusBaseFactor": 0.1},  # Baseline
    ]
    
    ma_results = []
    for config in configs:
        params = get_baseline_physics_params()
        params.update(config)
        
        profiles = generate_gear_profiles(params)
        planets = generate_planet_kinematics(profiles, params)
        theta_deg, displacement, velocity, acceleration = generate_motion_law(params)
        piston_forces = calculate_piston_forces(displacement, velocity, acceleration, params)
        contact_forces = calculate_contact_forces(profiles, planets, params, piston_forces)
        ma = calculate_mechanical_advantage(piston_forces, contact_forces, profiles, params)
        
        ma_results.append(ma)
    
    # Then at least one configuration should be in target range
    in_range_count = 0
    for ma in ma_results:
        if np.all(ma >= target_ma_min) and np.all(ma <= target_ma_max):
            in_range_count += 1
    
    assert in_range_count > 0, "No configuration achieved target MA range"
```

### Phase 4: Transfer Efficiency Calculations

#### Test 4.1: Basic Efficiency Calculation
```python
def test_efficiency_calculation_basic():
    """Test basic transfer efficiency calculation."""
    # Given
    gear_profiles = get_baseline_gear_profiles()
    planets = get_baseline_planets()
    params = get_baseline_physics_params()
    piston_forces = np.array([1000.0, 1200.0, 800.0])  # N
    contact_forces = {
        "sun_planet": np.array([500.0, 600.0, 400.0]),  # N
        "planet_ring": np.array([500.0, 600.0, 400.0])  # N
    }
    displacement = np.array([0.0, 50.0, 100.0])  # mm
    velocity = np.array([0.0, 100.0, 0.0])  # mm/s
    acceleration = np.array([1000.0, 0.0, -1000.0])  # mm/s²
    
    # When
    efficiency = calculate_efficiency_from_losses(
        gear_profiles, planets, params, piston_forces, contact_forces,
        displacement, velocity, acceleration
    )
    
    # Then
    assert len(efficiency) == 3
    assert np.all(efficiency >= 0.0)  # Non-negative efficiency
    assert np.all(efficiency <= 1.0)  # Efficiency ≤ 100%
    assert np.all(np.isfinite(efficiency))  # No NaN or infinite values
    
    # Efficiency should be reasonable (typically 70-95% for planetary gearsets)
    assert np.mean(efficiency) >= 0.5
    assert np.mean(efficiency) <= 1.0
```

#### Test 4.2: Efficiency Sensitivity to Profile Changes
```python
def test_efficiency_sensitivity_to_profile_changes():
    """Test that efficiency changes with gear profile modifications."""
    # Given baseline setup
    baseline_profiles = get_baseline_gear_profiles()
    baseline_planets = get_baseline_planets()
    baseline_params = get_baseline_physics_params()
    
    # Generate baseline data
    theta_deg, displacement, velocity, acceleration = generate_motion_law(baseline_params)
    baseline_piston_forces = calculate_piston_forces(displacement, velocity, acceleration, baseline_params)
    baseline_contact_forces = calculate_contact_forces(baseline_profiles, baseline_planets, baseline_params, baseline_piston_forces)
    baseline_efficiency = calculate_efficiency_from_losses(
        baseline_profiles, baseline_planets, baseline_params,
        baseline_piston_forces, baseline_contact_forces,
        displacement, velocity, acceleration
    )
    
    # When modifying gear profiles
    modified_profiles = baseline_profiles.copy()
    modified_profiles["r_planet"] *= 1.1  # 10% larger planet
    
    modified_contact_forces = calculate_contact_forces(modified_profiles, baseline_planets, baseline_params, baseline_piston_forces)
    modified_efficiency = calculate_efficiency_from_losses(
        modified_profiles, baseline_planets, baseline_params,
        baseline_piston_forces, modified_contact_forces,
        displacement, velocity, acceleration
    )
    
    # Then efficiency should change
    efficiency_difference = np.mean(np.abs(modified_efficiency - baseline_efficiency))
    assert efficiency_difference > 0.001  # At least 0.1% change in efficiency
    
    # Test with optimization variables
    opt_vars = {
        "planet_coeff_1": 0.1,
        "planet_coeff_2": 0.05
    }
    
    opt_modified_profiles = apply_profile_optimization(baseline_profiles, opt_vars, baseline_params)
    opt_modified_contact_forces = calculate_contact_forces(opt_modified_profiles, baseline_planets, baseline_params, baseline_piston_forces)
    opt_modified_efficiency = calculate_efficiency_from_losses(
        opt_modified_profiles, baseline_planets, baseline_params,
        baseline_piston_forces, opt_modified_contact_forces,
        displacement, velocity, acceleration
    )
    
    # Efficiency should change with optimization variables
    opt_efficiency_difference = np.mean(np.abs(opt_modified_efficiency - baseline_efficiency))
    assert opt_efficiency_difference > 0.0005  # At least 0.05% change in efficiency
```

#### Test 4.3: Energy Loss Components
```python
def test_energy_loss_components():
    """Test individual energy loss components."""
    # Given
    gear_profiles = get_baseline_gear_profiles()
    planets = get_baseline_planets()
    params = get_baseline_physics_params()
    contact_forces = {
        "sun_planet": np.array([500.0, 600.0, 400.0]),
        "planet_ring": np.array([500.0, 600.0, 400.0]),
        "total_contact": np.array([1000.0, 1200.0, 800.0])
    }
    
    # When calculating individual loss components
    hertzian_losses = calculate_hertzian_losses(contact_forces, gear_profiles, params)
    friction_losses = calculate_friction_losses(contact_forces, gear_profiles, params)
    deformation_losses = calculate_deformation_losses(contact_forces, gear_profiles, params)
    windage_losses = calculate_windage_losses(gear_profiles, params)
    
    # Then all loss components should be non-negative
    assert np.all(hertzian_losses >= 0)
    assert np.all(friction_losses >= 0)
    assert np.all(deformation_losses >= 0)
    assert np.all(windage_losses >= 0)
    
    # Loss components should be finite
    assert np.all(np.isfinite(hertzian_losses))
    assert np.all(np.isfinite(friction_losses))
    assert np.all(np.isfinite(deformation_losses))
    assert np.all(np.isfinite(windage_losses))
    
    # Total losses should be sum of components
    total_losses = hertzian_losses + friction_losses + deformation_losses + windage_losses
    assert len(total_losses) == len(hertzian_losses)
```

### Phase 5: FEA Integration

#### Test 5.1: FEA Penalty Calculation
```python
def test_fea_penalty_calculation():
    """Test FEA penalty calculation for optimization constraints."""
    # Given
    gear_profiles = get_baseline_gear_profiles()
    planets = get_baseline_planets()
    params = get_baseline_physics_params()
    contact_forces = {
        "sun_planet": np.array([500.0, 600.0, 400.0]),
        "planet_ring": np.array([500.0, 600.0, 400.0])
    }
    
    # When
    fea_penalty = calculate_fea_penalty(gear_profiles, planets, params, contact_forces)
    
    # Then
    assert fea_penalty >= 0.0  # Non-negative penalty
    assert np.isfinite(fea_penalty)  # Finite penalty
    
    # Test penalty sensitivity to stress levels
    high_stress_contact_forces = {
        "sun_planet": np.array([1000.0, 1200.0, 800.0]),  # 2x higher forces
        "planet_ring": np.array([1000.0, 1200.0, 800.0])
    }
    
    high_stress_penalty = calculate_fea_penalty(gear_profiles, planets, params, high_stress_contact_forces)
    
    # Higher forces should result in higher penalties
    assert high_stress_penalty > fea_penalty
```

#### Test 5.2: FEA Stress Analysis
```python
def test_fea_stress_analysis():
    """Test FEA stress analysis calculations."""
    # Given
    gear_profiles = get_baseline_gear_profiles()
    planets = get_baseline_planets()
    params = get_baseline_physics_params()
    contact_forces = {
        "sun_planet": np.array([500.0, 600.0, 400.0]),
        "planet_ring": np.array([500.0, 600.0, 400.0])
    }
    
    # When
    stress_results = calculate_fea_stress_analysis(gear_profiles, planets, params, contact_forces)
    
    # Then
    assert "von_mises_stress" in stress_results
    assert "hertzian_contact_stress" in stress_results
    assert "safety_factor" in stress_results
    
    # All stress values should be positive
    assert np.all(stress_results["von_mises_stress"] > 0)
    assert np.all(stress_results["hertzian_contact_stress"] > 0)
    assert np.all(stress_results["safety_factor"] > 0)
    
    # Safety factor should be reasonable (typically 1.5-5.0)
    assert np.all(stress_results["safety_factor"] >= 1.0)
    assert np.all(stress_results["safety_factor"] <= 10.0)
```

### Phase 6: Integration Tests

#### Test 6.1: End-to-End Physics Calculation
```python
def test_end_to_end_physics_calculation():
    """Test complete physics calculation pipeline."""
    # Given
    params = get_baseline_physics_params()
    
    # When running complete pipeline
    profiles = generate_gear_profiles(params)
    planets = generate_planet_kinematics(profiles, params)
    theta_deg, displacement, velocity, acceleration = generate_motion_law(params)
    piston_forces = calculate_piston_forces(displacement, velocity, acceleration, params)
    contact_forces = calculate_contact_forces(profiles, planets, params, piston_forces)
    ma = calculate_mechanical_advantage(piston_forces, contact_forces, profiles, params)
    efficiency = calculate_efficiency_from_losses(
        profiles, planets, params, piston_forces, contact_forces,
        displacement, velocity, acceleration
    )
    fea_penalty = calculate_fea_penalty(profiles, planets, params, contact_forces)
    
    # Then all calculations should complete successfully
    assert len(ma) == len(displacement)
    assert len(efficiency) == len(displacement)
    assert np.all(np.isfinite(ma))
    assert np.all(np.isfinite(efficiency))
    assert np.isfinite(fea_penalty)
    
    # Results should be physically reasonable
    assert np.all(ma > 0)
    assert np.all(efficiency >= 0)
    assert np.all(efficiency <= 1)
    assert fea_penalty >= 0
```

#### Test 6.2: Optimization Variable Impact
```python
def test_optimization_variable_impact():
    """Test that optimization variables actually impact physics calculations."""
    # Given baseline setup
    baseline_params = get_baseline_physics_params()
    baseline_profiles = generate_gear_profiles(baseline_params)
    baseline_planets = generate_planet_kinematics(baseline_profiles, baseline_params)
    theta_deg, displacement, velocity, acceleration = generate_motion_law(baseline_params)
    baseline_piston_forces = calculate_piston_forces(displacement, velocity, acceleration, baseline_params)
    baseline_contact_forces = calculate_contact_forces(baseline_profiles, baseline_planets, baseline_params, baseline_piston_forces)
    baseline_ma = calculate_mechanical_advantage(baseline_piston_forces, baseline_contact_forces, baseline_profiles, baseline_params)
    baseline_efficiency = calculate_efficiency_from_losses(
        baseline_profiles, baseline_planets, baseline_params,
        baseline_piston_forces, baseline_contact_forces,
        displacement, velocity, acceleration
    )
    
    # When applying optimization variables
    opt_vars = {
        "journal_offset_radius": 10.0,  # mm
        "journal_angle_offset": 45.0,   # degrees
        "sun_phase_offset": 30.0,       # degrees
        "planet_coeff_1": 0.2,
        "planet_coeff_2": 0.1,
        "ring_coeff_1": -0.1,
        "ring_coeff_2": -0.05,
        "sun_coeff_1": 0.15,
        "sun_coeff_2": 0.08,
        "profile_phase_shift": 10.0
    }
    
    # Apply optimization variables
    opt_params = baseline_params.copy()
    opt_params["optimization_variables"] = opt_vars
    
    opt_profiles = generate_gear_profiles(opt_params)
    opt_planets = generate_planet_kinematics(opt_profiles, opt_params)
    opt_contact_forces = calculate_contact_forces(opt_profiles, opt_planets, opt_params, baseline_piston_forces)
    opt_ma = calculate_mechanical_advantage(baseline_piston_forces, opt_contact_forces, opt_profiles, opt_params)
    opt_efficiency = calculate_efficiency_from_losses(
        opt_profiles, opt_planets, opt_params,
        baseline_piston_forces, opt_contact_forces,
        displacement, velocity, acceleration
    )
    
    # Then optimization variables should impact results
    ma_difference = np.mean(np.abs(opt_ma - baseline_ma))
    efficiency_difference = np.mean(np.abs(opt_efficiency - baseline_efficiency))
    
    assert ma_difference > 0.01, f"MA difference too small: {ma_difference}"
    assert efficiency_difference > 0.001, f"Efficiency difference too small: {efficiency_difference}"
    
    # Results should be physically reasonable
    assert np.all(opt_ma > 0)
    assert np.all(opt_efficiency >= 0)
    assert np.all(opt_efficiency <= 1)
```

## 3. Implementation Order

### Phase 1: Core Physics Engine (Week 1)
1. **Piston Force Calculations** - Implement basic force calculations
2. **Contact Force Calculations** - Implement Hertzian contact model
3. **Basic Integration Tests** - Ensure components work together

### Phase 2: Performance Metrics (Week 2)
1. **Mechanical Advantage Calculations** - Implement MA from forces and kinematics
2. **Transfer Efficiency Calculations** - Implement efficiency with energy losses
3. **Sensitivity Tests** - Ensure calculations respond to profile changes

### Phase 3: FEA Integration (Week 3)
1. **FEA Penalty Calculations** - Implement stress-based constraints
2. **FEA Stress Analysis** - Implement Von Mises and Hertzian stress
3. **Safety Factor Calculations** - Implement fatigue and yield safety factors

### Phase 4: Optimization Integration (Week 4)
1. **Optimization Variable Application** - Implement profile modifications
2. **Objective Function Integration** - Combine MA, efficiency, and FEA penalties
3. **End-to-End Testing** - Complete system validation

## 4. Success Criteria

### Functional Requirements
- ✅ All physics calculations complete without errors
- ✅ Results are physically reasonable (positive forces, efficiency 0-100%, etc.)
- ✅ Calculations are sensitive to profile changes
- ✅ Optimization variables impact results
- ✅ FEA penalties provide meaningful constraints

### Performance Requirements
- ✅ Calculations complete in < 1 second for 360-point profiles
- ✅ Memory usage < 100MB for typical optimization runs
- ✅ Numerical stability (no NaN or infinite values)
- ✅ Reproducible results (deterministic calculations)

### Quality Requirements
- ✅ 100% test coverage for physics calculations
- ✅ All tests pass consistently
- ✅ Clear error messages for invalid inputs
- ✅ Comprehensive documentation

## 5. Risk Mitigation

### Technical Risks
- **Numerical Instability**: Use robust numerical methods, add validation
- **Performance Issues**: Profile code, optimize critical paths
- **Integration Complexity**: Implement incrementally, test each component

### Implementation Risks
- **Scope Creep**: Stick to core physics calculations first
- **Testing Complexity**: Start with simple test cases, build complexity
- **Documentation Debt**: Document as you implement

## 6. Next Steps

1. **Create test file structure** - Set up `tests/test_physics_calculations.py`
2. **Implement helper functions** - Create `get_baseline_*()` functions
3. **Start with Phase 1** - Implement piston force calculations
4. **Follow TDD cycle** - Red → Green → Refactor for each test
5. **Integrate with existing system** - Connect to gear profile generation

This TDD plan provides a systematic approach to implementing the missing physics calculations with proper testing and validation at each step.
