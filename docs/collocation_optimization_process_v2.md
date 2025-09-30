# Collocation Optimization Process v2.0 - Piston Kinematics Control & Force Transfer Efficiency

## Overview

This document describes the proper collocation-based optimization process for planetary gearset design, focusing on **piston kinematics control** and **force transfer efficiency optimization**. This approach addresses the critical need for precise control over acceleration profiles during specific phases of the piston cycle, particularly at TDC, BDC, and during primary piston travel phases.

## 🎯 Core Requirements

### Critical Piston Kinematics Constraints
- **TDC (Top Dead Center)**: Acceleration must equal 0
- **BDC (Bottom Dead Center)**: Acceleration must equal 0  
- **Primary Piston Travel**: Acceleration must equal 0 during main stroke phases
- **User-Defined Phase Durations**: Full control over constant acceleration periods
- **Smooth Transitions**: Collocation connects constrained phases seamlessly

### Force Transfer Efficiency Optimization
- **Piston Crown to Ring Output**: Optimize force transfer through the entire gearset
- **Contact Point Optimization**: Minimize energy losses at gear interfaces
- **Load Distribution**: Ensure uniform load distribution across all gear teeth
- **Friction Minimization**: Optimize for minimal frictional losses

## 🔄 Two-Phase Collocation Optimization Process

### Phase 1: Motion Law Optimization with Kinematic Constraints

#### Objective
Generate an optimal motion law that satisfies strict acceleration constraints at critical points while maintaining smooth, efficient piston motion.

#### Collocation Formulation

**Decision Variables:**
- `x(θ)`: Piston displacement as function of ring angle θ
- `v(θ)`: Piston velocity as function of ring angle θ  
- `a(θ)`: Piston acceleration as function of ring angle θ

**Objective Function:**
```
minimize: ∫[0,2π] (a(θ)² + λ₁·v(θ)² + λ₂·x(θ)²) dθ
```
Where:
- `a(θ)²`: Minimize acceleration (smooth motion)
- `λ₁·v(θ)²`: Penalize high velocities (efficiency)
- `λ₂·x(θ)²`: Penalize large displacements (compactness)

**Critical Constraints:**

1. **Zero Acceleration at TDC:**
   ```
   a(θ_TDC) = 0
   where θ_TDC ∈ [θ_TDC_start, θ_TDC_end]
   ```

2. **Zero Acceleration at BDC:**
   ```
   a(θ_BDC) = 0  
   where θ_BDC ∈ [θ_BDC_start, θ_BDC_end]
   ```

3. **Zero Acceleration During Primary Travel:**
   ```
   a(θ_travel) = 0
   where θ_travel ∈ [θ_travel_start, θ_travel_end]
   ```

4. **Kinematic Relationships:**
   ```
   v(θ) = dx/dθ
   a(θ) = dv/dθ = d²x/dθ²
   ```

5. **Boundary Conditions:**
   ```
   x(0) = 0, x(2π) = stroke_length
   v(0) = 0, v(2π) = 0
   ```

6. **User-Defined Phase Durations:**
   ```
   θ_TDC_end - θ_TDC_start = user_input_TDC_duration
   θ_BDC_end - θ_BDC_start = user_input_BDC_duration  
   θ_travel_end - θ_travel_start = user_input_travel_duration
   ```

#### Collocation Discretization

**Grid Points:**
- **Dense grid** in transition regions (acceleration/deceleration phases)
- **Sparse grid** in constant acceleration regions (TDC, BDC, travel)
- **Adaptive spacing** based on acceleration magnitude

**Collocation Points:**
- **Gauss-Lobatto points** for high accuracy
- **Radau points** for boundary condition handling
- **User-configurable** point density per phase

#### Implementation with CasADi + IPOPT

```python
def optimize_motion_law_with_kinematic_constraints(params):
    """Optimize motion law with strict acceleration constraints."""
    
    # Extract user-defined phase durations
    tdc_duration = params['tdc_zero_accel_duration_deg']
    bdc_duration = params['bdc_zero_accel_duration_deg'] 
    travel_duration = params['travel_zero_accel_duration_deg']
    
    # Create adaptive collocation grid
    grid = create_adaptive_collocation_grid(
        tdc_duration, bdc_duration, travel_duration, params
    )
    
    # Decision variables
    x = ca.SX.sym('x', len(grid))  # Displacement
    v = ca.SX.sym('v', len(grid))  # Velocity  
    a = ca.SX.sym('a', len(grid))  # Acceleration
    
    # Objective: minimize acceleration + velocity + displacement
    f = ca.sum1(a**2) + lambda1 * ca.sum1(v**2) + lambda2 * ca.sum1(x**2)
    
    # Constraints
    g = []
    lbg = []
    ubg = []
    
    # 1. Kinematic relationships (finite differences)
    for i in range(len(grid)-1):
        g.append(v[i] - (x[i+1] - x[i]) / (grid[i+1] - grid[i]))
        lbg.append(0.0)
        ubg.append(0.0)
        
        g.append(a[i] - (v[i+1] - v[i]) / (grid[i+1] - grid[i]))
        lbg.append(0.0) 
        ubg.append(0.0)
    
    # 2. Zero acceleration constraints at TDC
    tdc_indices = get_phase_indices(grid, 'TDC', tdc_duration)
    for idx in tdc_indices:
        g.append(a[idx])
        lbg.append(0.0)
        ubg.append(0.0)
    
    # 3. Zero acceleration constraints at BDC  
    bdc_indices = get_phase_indices(grid, 'BDC', bdc_duration)
    for idx in bdc_indices:
        g.append(a[idx])
        lbg.append(0.0)
        ubg.append(0.0)
    
    # 4. Zero acceleration constraints during travel
    travel_indices = get_phase_indices(grid, 'TRAVEL', travel_duration)
    for idx in travel_indices:
        g.append(a[idx])
        lbg.append(0.0)
        ubg.append(0.0)
    
    # 5. Boundary conditions
    g.append(x[0])      # Start at zero displacement
    lbg.append(0.0)
    ubg.append(0.0)
    
    g.append(x[-1])     # End at stroke length
    lbg.append(params['stroke_length'])
    ubg.append(params['stroke_length'])
    
    # Solve with IPOPT
    nlp = {'x': ca.vertcat(x, v, a), 'f': f, 'g': ca.vertcat(*g)}
    solver = ca.nlpsol('solver', 'ipopt', nlp)
    
    result = solver(x0=initial_guess, lbg=lbg, ubg=ubg)
    
    return extract_motion_law_solution(result, grid)
```

### Phase 2: Gear Profile Optimization for Force Transfer Efficiency

#### Objective
Generate optimal gear profiles that maximize force transfer efficiency from piston crown to ring output, following the motion law from Phase 1.

#### Force Transfer Efficiency Formulation

**Decision Variables:**
- `R_sun(θ)`: Sun gear radius profile
- `R_planet(θ)`: Planet gear radius profile  
- `R_ring(θ)`: Ring gear radius profile
- `φ(θ)`: Planet rotation angle profile

**Objective Function:**
```
maximize: η_force_transfer = ∫[0,2π] (F_piston(θ) · v_piston(θ) - P_losses(θ)) dθ
```

Where:
- `F_piston(θ)`: Piston force from motion law
- `v_piston(θ)`: Piston velocity from motion law
- `P_losses(θ)`: Power losses in gearset

**Power Loss Components:**
```
P_losses(θ) = P_friction(θ) + P_contact(θ) + P_inertia(θ)
```

1. **Friction Losses:**
   ```
   P_friction(θ) = μ · F_contact(θ) · v_sliding(θ)
   ```

2. **Contact Losses:**
   ```
   P_contact(θ) = k_contact · F_contact(θ)² · δ(θ)
   ```

3. **Inertia Losses:**
   ```
   P_inertia(θ) = I_gear · α_gear(θ)²
   ```

**Critical Constraints:**

1. **UNIFIED CONSTRAINT SYSTEM:**
   ```
   R_ring(θ) = R_sun(θ) + 2·R_planet(θ)
   ```

2. **Contact Point Constraints:**
   ```
   R_ring(θ) - R_planet(θ) = R_sun(θ) + R_planet(θ)
   ```

3. **Motion Law Compatibility:**
   ```
   dφ/dθ = gear_ratio (from Phase 1 motion law)
   ```

4. **Force Balance:**
   ```
   F_piston(θ) = F_sun(θ) + F_planet(θ) + F_ring(θ)
   ```

5. **Contact Force Limits:**
   ```
   F_contact(θ) ≤ F_max_contact
   ```

6. **Stress Constraints:**
   ```
   σ_contact(θ) ≤ σ_yield
   σ_bending(θ) ≤ σ_yield
   ```

#### Implementation with CasADi + IPOPT

```python
def optimize_gear_profiles_for_force_transfer(motion_law, params):
    """Optimize gear profiles for maximum force transfer efficiency."""
    
    # Extract motion law data
    theta = motion_law['theta']
    displacement = motion_law['displacement'] 
    velocity = motion_law['velocity']
    acceleration = motion_law['acceleration']
    
    # Create gear profile grid (may be different from motion law grid)
    gear_grid = create_gear_profile_grid(params)
    
    # Decision variables
    R_sun = ca.SX.sym('R_sun', len(gear_grid))
    R_planet = ca.SX.sym('R_planet', len(gear_grid))
    R_ring = ca.SX.sym('R_ring', len(gear_grid))
    phi = ca.SX.sym('phi', len(gear_grid))
    
    # Interpolate motion law to gear grid
    F_piston = interpolate_force(theta, displacement, velocity, acceleration, gear_grid)
    v_piston = interpolate_velocity(theta, velocity, gear_grid)
    
    # Calculate power losses
    P_friction = calculate_friction_losses(R_sun, R_planet, R_ring, phi, gear_grid, params)
    P_contact = calculate_contact_losses(R_sun, R_planet, R_ring, phi, gear_grid, params)
    P_inertia = calculate_inertia_losses(R_sun, R_planet, R_ring, phi, gear_grid, params)
    
    P_losses = P_friction + P_contact + P_inertia
    
    # Objective: maximize force transfer efficiency
    f = -ca.sum1(F_piston * v_piston - P_losses)  # Negative for maximization
    
    # Constraints
    g = []
    lbg = []
    ubg = []
    
    # 1. UNIFIED CONSTRAINT SYSTEM
    for i in range(len(gear_grid)):
        g.append(R_ring[i] - (R_sun[i] + 2.0 * R_planet[i]))
        lbg.append(0.0)
        ubg.append(0.0)
    
    # 2. Contact point constraints
    for i in range(len(gear_grid)):
        g.append((R_ring[i] - R_planet[i]) - (R_sun[i] + R_planet[i]))
        lbg.append(0.0)
        ubg.append(0.0)
    
    # 3. Motion law compatibility
    for i in range(len(gear_grid)-1):
        g.append(phi[i+1] - phi[i] - params['gear_ratio'] * (gear_grid[i+1] - gear_grid[i]))
        lbg.append(0.0)
        ubg.append(0.0)
    
    # 4. Force balance
    F_sun = calculate_sun_force(R_sun, phi, gear_grid, params)
    F_planet = calculate_planet_force(R_planet, phi, gear_grid, params)
    F_ring = calculate_ring_force(R_ring, phi, gear_grid, params)
    
    for i in range(len(gear_grid)):
        g.append(F_piston[i] - (F_sun[i] + F_planet[i] + F_ring[i]))
        lbg.append(0.0)
        ubg.append(0.0)
    
    # 5. Contact force limits
    F_contact = calculate_contact_forces(R_sun, R_planet, R_ring, phi, gear_grid, params)
    for i in range(len(gear_grid)):
        g.append(F_contact[i])
        lbg.append(0.0)
        ubg.append(params['max_contact_force'])
    
    # 6. Stress constraints
    sigma_contact = calculate_contact_stress(R_sun, R_planet, R_ring, phi, gear_grid, params)
    sigma_bending = calculate_bending_stress(R_sun, R_planet, R_ring, phi, gear_grid, params)
    
    for i in range(len(gear_grid)):
        g.append(sigma_contact[i])
        lbg.append(0.0)
        ubg.append(params['yield_strength'])
        
        g.append(sigma_bending[i])
        lbg.append(0.0)
        ubg.append(params['yield_strength'])
    
    # Solve with IPOPT
    nlp = {'x': ca.vertcat(R_sun, R_planet, R_ring, phi), 'f': f, 'g': ca.vertcat(*g)}
    solver = ca.nlpsol('solver', 'ipopt', nlp)
    
    result = solver(x0=initial_gear_guess, lbg=lbg, ubg=ubg)
    
    return extract_gear_profile_solution(result, gear_grid)
```

## 🔄 Integration with Current CasADi IPOPT Implementation

### Current Implementation Issues

The current CasADi IPOPT implementation in `collocation_optimizer.py` has several limitations:

1. **Generic Motion Law**: Uses simple acceleration minimization without kinematic constraints
2. **No Phase Control**: Cannot enforce zero acceleration at specific phases
3. **Single-Phase Optimization**: Only optimizes motion law, not gear profiles
4. **Missing Force Transfer**: No consideration of force transfer efficiency
5. **Simplified Constraints**: Basic boundary conditions only

### Required Modifications

#### 1. Enhanced Motion Law Optimization

**Current:**
```python
# Simple acceleration minimization
f = ca.sum1(acceleration**2)
```

**Required:**
```python
# Kinematic constraint-based optimization
f = ca.sum1(acceleration**2) + lambda1 * ca.sum1(velocity**2) + lambda2 * ca.sum1(displacement**2)

# Add zero acceleration constraints
for phase in ['TDC', 'BDC', 'TRAVEL']:
    indices = get_phase_indices(grid, phase, user_duration)
    for idx in indices:
        g.append(acceleration[idx])
        lbg.append(0.0)
        ubg.append(0.0)
```

#### 2. Gear Profile Optimization Module

**Current:** Missing entirely

**Required:** Complete gear profile optimization with force transfer efficiency

#### 3. User Input Interface

**Current:** Basic parameters only

**Required:**
```python
kinematic_constraints = {
    'tdc_zero_accel_duration_deg': user_input,
    'bdc_zero_accel_duration_deg': user_input, 
    'travel_zero_accel_duration_deg': user_input,
    'transition_smoothness_factor': user_input,
    'force_transfer_weight': user_input
}
```

#### 4. Adaptive Grid Generation

**Current:** Uniform grid

**Required:**
```python
def create_adaptive_collocation_grid(kinematic_constraints, params):
    """Create adaptive grid based on kinematic requirements."""
    
    # Dense grid in transition regions
    transition_points = generate_transition_points(kinematic_constraints)
    
    # Sparse grid in constant acceleration regions  
    constant_points = generate_constant_points(kinematic_constraints)
    
    # Combine and optimize
    return optimize_grid_density(transition_points, constant_points, params)
```

## 🎯 Implementation Roadmap

### Phase 1: Enhanced Motion Law Optimization (2-3 weeks)
1. **Modify `collocation_optimizer.py`** to support kinematic constraints
2. **Add user input interface** for phase duration control
3. **Implement adaptive grid generation**
4. **Add zero acceleration constraint enforcement**
5. **Test with various kinematic constraint combinations**

### Phase 2: Gear Profile Optimization (3-4 weeks)  
1. **Create new `gear_profile_optimizer.py`** module
2. **Implement force transfer efficiency calculation**
3. **Add UNIFIED CONSTRAINT SYSTEM**
4. **Implement contact force and stress calculations**
5. **Integrate with motion law optimization**

### Phase 3: Integration and Testing (2-3 weeks)
1. **Integrate both optimization phases**
2. **Add comprehensive validation**
3. **Performance optimization**
4. **User interface enhancement**
5. **Documentation and examples**

## 📊 Expected Benefits

### Motion Law Quality
- **Precise acceleration control** at critical phases
- **Smooth transitions** between constrained and free phases
- **User-defined phase durations** for optimal performance
- **Reduced vibration** and noise

### Force Transfer Efficiency
- **Optimized gear profiles** for maximum efficiency
- **Minimized power losses** through the gearset
- **Uniform load distribution** across all teeth
- **Reduced wear** and improved durability

### Design Flexibility
- **Full control** over piston kinematics
- **Optimization** for specific performance requirements
- **Adaptive algorithms** for different applications
- **Comprehensive validation** and quality control

## 🎯 Conclusion

The proposed two-phase collocation optimization process addresses the critical need for **piston kinematics control** and **force transfer efficiency optimization** in planetary gearset design. This approach provides:

1. **Precise control** over acceleration profiles at critical phases
2. **Optimal force transfer** from piston crown to ring output  
3. **User-defined constraints** for specific performance requirements
4. **Comprehensive optimization** of the entire system

This represents a significant advancement over the current generic CasADi implementation, providing the sophisticated control and optimization capabilities required for high-performance planetary gearset design.
