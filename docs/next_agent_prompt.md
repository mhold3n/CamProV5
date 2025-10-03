# Next Agent Prompt: Implement Unified Specification Theory in Codebase

## Mission Statement

You are tasked with implementing the theoretical framework from `engine_optimization_unified.md` into the actual codebase. The current enhanced optimizers are only 20% compliant with the specification and return non-converging solutions (default values of 0.5). Your goal is to achieve 100% compliance with the unified specification while ensuring all 318 tests pass.

## Current State Analysis

### Critical Issues Identified
- **Non-converging optimizations**: Enhanced optimizers return default values instead of solving
- **Missing core physics**: Thermodynamic and transmission models are placeholders
- **Incomplete constraints**: Missing essential constraints from specification
- **Suboptimal solver settings**: IPOPT configuration doesn't match specification
- **46 failing tests**: Out of 318 total tests

### Specification Compliance Status
- **Overall**: 20% compliant
- **Phase 1 (Gas Dynamics)**: 30% - Basic structure, missing physics
- **Phase 2 (Transmission)**: 25% - Basic structure, missing coupling
- **Solver Configuration**: 40% - Partial IPOPT setup
- **Physics Implementation**: 15% - Placeholder implementations

## Implementation Requirements

### Phase 1: Gas Dynamics Implementation

#### 1.1 Motion Law Parameterization
**Specification Target**: B-spline (order≥4) over t∈[0,T_cyc] with C² smoothness

**Current Implementation**: Simple finite differences
```python
# Current (problematic)
velocity = ca.SX.sym('v', n-1)
for i in range(n-1):
    velocity[i] = (x[i+1] - x[i]) / (grid_ca[i+1] - grid_ca[i])
```

**Required Implementation**:
```python
# Target (specification compliant)
def create_b_spline_basis(grid, order=4):
    """Create B-spline basis functions with C² continuity."""
    # Implement B-spline basis with proper continuity
    # Ensure clamped ends: x(0)=0, x(T_cyc)=S
    pass

def parameterize_motion_law(grid, coefficients):
    """Parameterize motion law using B-splines."""
    # x(t) = Σ b_k φ_k(t) where φ_k are B-spline basis functions
    pass
```

#### 1.2 Thermodynamic Physics Implementation
**Specification Target**: Complete thermodynamic cycle with proper physics

**Required Components**:
1. **Volume calculation**: V(t) = V_c + A_p x(t)
2. **Polytropic process**: pV^γ = const for adiabatic segments
3. **Indicated work**: W_id = ∮ p dV
4. **Valve modeling**: C¹ sigmoid lift profiles with timing
5. **Combustion modeling**: Wiebe function implementation

**Implementation Template**:
```python
class ThermodynamicPhysics:
    def __init__(self, params):
        self.gamma = params.gamma
        self.piston_area = params.piston_area_m2
        self.clearance_volume = params.clearance_volume_m3
    
    def calculate_volume(self, displacement):
        """V(t) = V_c + A_p x(t)"""
        return self.clearance_volume + self.piston_area * displacement
    
    def calculate_pressure(self, volume, initial_pressure, initial_volume):
        """pV^γ = const for adiabatic process"""
        return initial_pressure * (initial_volume / volume) ** self.gamma
    
    def calculate_indicated_work(self, pressure, volume, grid):
        """W_id = ∮ p dV using trapezoidal rule"""
        work = 0
        for i in range(len(grid) - 1):
            dV = volume[i+1] - volume[i]
            p_avg = (pressure[i] + pressure[i+1]) / 2
            work += p_avg * dV
        return work
    
    def enforce_adiabatic_constraint(self, pressure, volume, initial_pressure, initial_volume):
        """Enforce pV^γ = const constraint"""
        return pressure * (volume ** self.gamma) - initial_pressure * (initial_volume ** self.gamma)
```

#### 1.3 Objective Function Implementation
**Specification Target**: J₁ = w_v*J_v + w_j*J_j + w_S*W_id

**Required Objectives**:
1. **Work output**: Ŵ = W / W̄ (maximize)
2. **Velocity flatness**: Ĵ_flat = ∫ (v-v_targ)² dt / J̄_flat (minimize)
3. **Jerk regularization**: Ĵ_jerk = ∫ (x‴)² dt / J̄_jerk (minimize)
4. **Exergy loss**: Ĵ_ex = ∫ T₀ Ṡ_gen dt / Ê̄ (minimize)

**Implementation Template**:
```python
def build_phase1_objective(self, x, v, a, j, grid, motion_params):
    """Build Phase 1 objective according to specification."""
    
    # 1. Work output maximization (negative for minimization)
    volume = self.thermo_physics.calculate_volume(x)
    pressure = self.thermo_physics.calculate_pressure(volume, ...)
    indicated_work = self.thermo_physics.calculate_indicated_work(pressure, volume, grid)
    work_objective = -self.params.work_weight * indicated_work
    
    # 2. Velocity flatness
    target_velocity = self.calculate_target_velocity(grid, motion_params)
    velocity_flatness = self.params.velocity_weight * ca.sum1((v - target_velocity)**2)
    
    # 3. Jerk regularization
    jerk_objective = self.params.jerk_weight * ca.sum1(j**2)
    
    # 4. Exergy loss (surrogate: pressure smoothness)
    exergy_loss = self.params.pressure_weight * ca.sum1(ca.diff(pressure)**2)
    
    return work_objective + velocity_flatness + jerk_objective + exergy_loss
```

### Phase 2: Transmission Implementation

#### 2.1 Kinematic Coupling
**Specification Target**: θ̇ = i(x)·ẋ

**Implementation Template**:
```python
def enforce_kinematic_coupling(self, instantaneous_ratio, velocity, angular_velocity):
    """Enforce kinematic coupling: θ̇ = i(x)·ẋ"""
    return angular_velocity - instantaneous_ratio * velocity
```

#### 2.2 Power Balance
**Specification Target**: τ_out·θ̇ = F_p·ẋ − P_loss

**Implementation Template**:
```python
def enforce_power_balance(self, output_torque, angular_velocity, piston_force, piston_velocity, power_loss):
    """Enforce power balance: τ_out·θ̇ = F_p·ẋ − P_loss"""
    return output_torque * angular_velocity - (piston_force * piston_velocity - power_loss)
```

#### 2.3 Transmission Efficiency
**Specification Target**: η̂ = η/η̄

**Implementation Template**:
```python
def calculate_transmission_efficiency(self, power_loss, input_power):
    """Calculate transmission efficiency: η = (P_in - P_loss) / P_in"""
    return (input_power - power_loss) / input_power
```

### Solver Configuration

#### IPOPT Settings (Specification Compliant)
```python
solver_opts = {
    'ipopt': {
        'max_iter': 5000,  # Allow generous iterations for continuation
        'tol': 1e-6,  # Specification target
        'acceptable_tol': 1e-4,  # Early acceptance during continuation
        'constr_viol_tol': 1e-6,
        'nlp_scaling_method': 'user-scaling',  # We provide variable/objective scaling
        'hessian_approximation': 'exact',  # Use CasADi exact Hessian initially
        'linear_solver': 'mumps',  # Or ma57 if available
        'mu_strategy': 'adaptive',  # Barrier update strategy
        'bound_relax_factor': 1e-8,
        'honor_original_bounds': 'yes'
    }
}
```

#### Continuation (Homotopy) Implementation
**Specification Target**: 3-stage continuation with parameter scheduling

```python
continuation_stages = [
    {'epsilon_valve': 1e-1, 'epsilon_friction': 1e-1, 'stress_factor': 0.7},  # Very smooth, relaxed limits
    {'epsilon_valve': 5e-2, 'epsilon_friction': 5e-2, 'stress_factor': 0.85},  # Tighten bounds
    {'epsilon_valve': 1e-2, 'epsilon_friction': 1e-2, 'stress_factor': 1.0}   # Final physics-like limits
]
```

### Multi-Objective Optimization

#### Augmented Tchebyshev Scalarization
**Specification Target**: Use augmented Tchebyshev for multi-objective optimization

```python
class AugmentedTchebyshevScalarizer:
    def __init__(self, weights, reference_point):
        self.weights = weights
        self.reference_point = reference_point
    
    def scalarize(self, objectives):
        """Scalarize using augmented Tchebyshev method."""
        # Normalize objectives
        normalized = {name: obj / self.reference_point[name] for name, obj in objectives.items()}
        
        # Calculate Tchebyshev distance
        max_distance = 0
        for name, obj in normalized.items():
            distance = self.weights[name] * (obj - self.reference_point[name])
            max_distance = ca.fmax(max_distance, distance)
        
        # Add augmentation term
        augmentation = sum(0.01 * self.weights[name] * (obj - self.reference_point[name]) 
                          for name, obj in normalized.items())
        
        return max_distance + augmentation
```

## Implementation Priority Order

### Critical Path (Must Complete First)
1. **Fix solver configuration** - Get basic convergence working
2. **Implement volume calculation** - V(t) = V_c + A_p x(t)
3. **Add polytropic process** - pV^γ = const
4. **Implement indicated work** - W_id = ∮ p dV
5. **Add basic constraints** - Boundary conditions and monotonicity

### High Priority
1. **Implement kinematic coupling** - θ̇ = i(x)·ẋ
2. **Add power balance** - τ_out·θ̇ = F_p·ẋ − P_loss
3. **Implement transmission efficiency** - η̂ = η/η̄
4. **Add contact stress constraints** - σ_contact ≤ σ_allow

### Medium Priority
1. **Implement B-splines** - Replace finite differences
2. **Add valve modeling** - C¹ sigmoid lift profiles
3. **Implement combustion modeling** - Wiebe function
4. **Add multi-objective framework** - Augmented Tchebyshev

## Success Criteria

### Technical Success
- [ ] **100% test compliance** - All 318 tests pass
- [ ] **100% specification compliance** - All specification targets met
- [ ] **>95% convergence rate** - Optimizations converge to meaningful solutions
- [ ] **Performance targets** - <60s for typical problems
- [ ] **Accuracy targets** - KKT error <1e-6

### Implementation Success
- [ ] **Working thermodynamic physics** - Volume, pressure, work calculations
- [ ] **Working transmission physics** - Kinematic coupling, power balance
- [ ] **Proper constraints** - Adiabatic, kinematic, power balance
- [ ] **Robust solver** - IPOPT configuration matches specification
- [ ] **Multi-objective optimization** - Augmented Tchebyshev scalarization

## Validation Approach

### Test-Driven Development
1. **Start with failing tests** - Fix one test at a time
2. **Implement minimal code** - Just enough to make test pass
3. **Refactor and improve** - Clean up implementation
4. **Add new tests** - For new functionality

### Specification Validation
1. **Check each specification target** - Ensure implementation matches theory
2. **Validate physics equations** - Test against known solutions
3. **Verify constraint satisfaction** - Ensure all constraints are enforced
4. **Performance benchmarking** - Compare against specification targets

## Key Files to Modify

### Primary Files
- `campro/optimization/enhanced_motion_law_optimizer.py` - Phase 1 implementation
- `campro/optimization/enhanced_gear_optimizer.py` - Phase 2 implementation
- `campro/optimization/solver_improvements.py` - Solver configuration
- `campro/physics/thermodynamic_physics.py` - Thermodynamic models (create)
- `campro/physics/transmission_physics.py` - Transmission models (create)

### Supporting Files
- `campro/optimization/scaling_utils.py` - Variable/objective scaling (create)
- `campro/utils/array_utils.py` - Array handling utilities (create)
- `campro/pipeline/result_adapter.py` - Result format adaptation
- `tests/test_enhanced_optimizers.py` - Enhanced optimizer tests

## Expected Challenges

### Technical Challenges
1. **Numerical stability** - Complex physics may cause convergence issues
2. **Performance** - Additional constraints may slow optimization
3. **Integration** - New components must work with existing system
4. **Validation** - Ensuring physics implementation is correct

### Mitigation Strategies
1. **Robust solver framework** - Multiple fallback strategies
2. **Performance profiling** - Identify and optimize bottlenecks
3. **Incremental integration** - Test components individually
4. **Validation against known solutions** - Test physics against analytical results

## Deliverables

### Code Deliverables
1. **Enhanced Motion Law Optimizer** - Full thermodynamic physics implementation
2. **Enhanced Gear Optimizer** - Full transmission physics implementation
3. **Physics Modules** - Thermodynamic and transmission physics classes
4. **Solver Framework** - Robust solver with continuation and fallbacks
5. **Test Suite** - Comprehensive tests with 100% pass rate

### Documentation Deliverables
1. **API Documentation** - Updated user guides
2. **Implementation Notes** - Technical implementation details
3. **Performance Benchmarks** - Validation results
4. **Migration Guide** - How to use new features

## Success Metrics

### Immediate Success (Week 1-2)
- [ ] Basic convergence achieved - No more default values
- [ ] 50% of failing tests pass
- [ ] Solver configuration matches specification

### Short-term Success (Week 3-5)
- [ ] Core physics implemented and working
- [ ] 75% of failing tests pass
- [ ] Essential constraints enforced

### Medium-term Success (Week 6-8)
- [ ] Advanced features implemented
- [ ] 90% of failing tests pass
- [ ] Multi-objective optimization working

### Final Success (Week 9-10)
- [ ] 100% test compliance achieved
- [ ] 100% specification compliance achieved
- [ ] Performance targets met
- [ ] Documentation complete

## Conclusion

Your mission is to transform the current placeholder implementation into a fully compliant, robust optimization system that mirrors the theoretical framework in `engine_optimization_unified.md`. Focus on implementing the core physics first, then build up the advanced features. Use test-driven development to ensure each component works correctly before moving to the next.

The key to success is maintaining focus on the specification targets while ensuring that each implementation step delivers working, testable code. Regular validation against the test suite will ensure that progress is measurable and that the final implementation meets all requirements.

**Remember**: The current system is only 20% compliant. Your goal is to achieve 100% compliance while ensuring all 318 tests pass. This is a significant undertaking that requires systematic implementation of the missing physics, constraints, and objectives according to the unified specification.
