# Technical Implementation Guide: Enhanced Optimizers Recovery

**Date**: 2025-10-01  
**Target**: Achieve 100% compliance with unified specification  
**Approach**: Systematic implementation of missing physics and constraints  

## Phase 1: Foundation Stabilization

### 1.1 Solver Configuration Fixes

#### Current Issues
```python
# Current (problematic)
solver_opts = {
    'ipopt': {
        'max_iter': 1000,
        'tol': 1e-8,  # Too tight
        'constr_viol_tol': 1e-6,
        'linear_solver': 'mumps',
        'mu_strategy': 'adaptive'
    }
}
```

#### Target Implementation
```python
# Target (specification compliant)
solver_opts = {
    'ipopt': {
        'max_iter': 5000,  # Allow generous iterations
        'tol': 1e-6,  # Specification target
        'acceptable_tol': 1e-4,  # Early acceptance
        'constr_viol_tol': 1e-6,
        'nlp_scaling_method': 'user-scaling',  # We provide scaling
        'hessian_approximation': 'exact',  # Use exact Hessian initially
        'linear_solver': 'mumps',  # Or ma57 if available
        'mu_strategy': 'adaptive',
        'bound_relax_factor': 1e-8,
        'honor_original_bounds': 'yes'
    }
}
```

#### Implementation Steps
1. **Update EnhancedMotionLawOptimizer**
   - File: `campro/optimization/enhanced_motion_law_optimizer.py`
   - Method: `_solve_enhanced_nlp()`
   - Lines: 550-565

2. **Update EnhancedGearOptimizer**
   - File: `campro/optimization/enhanced_gear_optimizer.py`
   - Method: `_solve_enhanced_gear_nlp()`
   - Lines: 590-601

3. **Update SolverParameters class**
   - File: `campro/optimization/solver_improvements.py`
   - Add missing IPOPT options

### 1.2 Variable and Objective Scaling

#### Current Issues
- No variable scaling implemented
- No objective normalization
- Poor numerical conditioning

#### Target Implementation
```python
class VariableScaler:
    """Implement specification-compliant variable scaling."""
    
    def __init__(self, reference_values: Dict[str, float]):
        self.ref_values = reference_values
    
    def scale_variables(self, variables: Dict[str, ca.SX]) -> Dict[str, ca.SX]:
        """Scale variables according to specification."""
        scaled = {}
        for name, var in variables.items():
            if name in self.ref_values:
                scaled[name] = var / self.ref_values[name]
            else:
                scaled[name] = var
        return scaled
    
    def unscale_solution(self, scaled_solution: np.ndarray, 
                        variable_names: List[str]) -> np.ndarray:
        """Unscale solution back to original units."""
        unscaled = scaled_solution.copy()
        for i, name in enumerate(variable_names):
            if name in self.ref_values:
                unscaled[i] *= self.ref_values[name]
        return unscaled

class ObjectiveNormalizer:
    """Implement specification-compliant objective normalization."""
    
    def __init__(self, reference_objectives: Dict[str, float]):
        self.ref_objectives = reference_objectives
    
    def normalize_objectives(self, objectives: Dict[str, ca.SX]) -> Dict[str, ca.SX]:
        """Normalize objectives according to specification."""
        normalized = {}
        for name, obj in objectives.items():
            if name in self.ref_objectives:
                normalized[name] = obj / self.ref_objectives[name]
            else:
                normalized[name] = obj
        return normalized
```

#### Implementation Steps
1. **Create scaling utilities**
   - File: `campro/optimization/scaling_utils.py`
   - Implement VariableScaler and ObjectiveNormalizer classes

2. **Integrate scaling into optimizers**
   - Update both enhanced optimizers to use scaling
   - Add reference value calculation from baseline solutions

### 1.3 Array Shape Issue Resolution

#### Current Issues
```python
# CasADi returns (n,1) arrays
result = solver(x0=x0, lbx=lbx, ubx=ubx, lbg=lbg, ubg=ubg)
x_opt = np.array(result['x'])  # Shape: (n,1)
```

#### Target Implementation
```python
# Standardize to (n,) arrays
def ensure_1d_array(data):
    """Ensure array is 1D."""
    if isinstance(data, np.ndarray):
        return data.flatten()
    elif hasattr(data, 'full'):  # CasADi DM
        return np.array(data.full()).flatten()
    else:
        return np.array(data).flatten()

# Usage
x_opt = ensure_1d_array(result['x'])  # Shape: (n,)
```

#### Implementation Steps
1. **Create array utilities**
   - File: `campro/utils/array_utils.py`
   - Implement ensure_1d_array function

2. **Update all optimizers**
   - Replace array handling with standardized function
   - Update ResultAdapter to handle consistent arrays

## Phase 2: Core Physics Implementation

### 2.1 Phase 1 - Gas Dynamics Physics

#### Current Issues
- Missing volume calculation: V(t) = V_c + A_p x(t)
- No polytropic process: pV^γ = const
- No indicated work: W_id = ∮ p dV
- Placeholder valve and combustion models

#### Target Implementation
```python
class ThermodynamicPhysics:
    """Implement specification-compliant thermodynamic physics."""
    
    def __init__(self, params: ThermodynamicParameters):
        self.params = params
    
    def calculate_volume(self, displacement: ca.SX) -> ca.SX:
        """Calculate chamber volume: V(t) = V_c + A_p x(t)."""
        return self.params.clearance_volume_m3 + self.params.piston_area_m2 * displacement
    
    def calculate_pressure(self, volume: ca.SX, initial_pressure: float, 
                          initial_volume: float) -> ca.SX:
        """Calculate pressure from polytropic process: pV^γ = const."""
        return initial_pressure * (initial_volume / volume) ** self.params.gamma
    
    def calculate_indicated_work(self, pressure: ca.SX, volume: ca.SX, 
                                grid: np.ndarray) -> ca.SX:
        """Calculate indicated work: W_id = ∮ p dV."""
        # Use trapezoidal rule for integration
        work = 0
        for i in range(len(grid) - 1):
            dV = volume[i+1] - volume[i]
            p_avg = (pressure[i] + pressure[i+1]) / 2
            work += p_avg * dV
        return work
    
    def enforce_adiabatic_constraint(self, pressure: ca.SX, volume: ca.SX, 
                                   initial_pressure: float, initial_volume: float) -> ca.SX:
        """Enforce adiabatic constraint: pV^γ = const."""
        return pressure * (volume ** self.params.gamma) - initial_pressure * (initial_volume ** self.params.gamma)
```

#### Implementation Steps
1. **Create thermodynamic physics module**
   - File: `campro/physics/thermodynamic_physics.py`
   - Implement ThermodynamicPhysics class

2. **Update EnhancedMotionLawOptimizer**
   - Integrate thermodynamic physics into objective function
   - Add adiabatic constraints
   - Implement indicated work maximization

### 2.2 Phase 2 - Transmission Physics

#### Current Issues
- Missing kinematic coupling: θ̇ = i(x)·ẋ
- No power balance: τ_out·θ̇ = F_p·ẋ − P_loss
- No transmission efficiency calculation
- Placeholder contact mechanics

#### Target Implementation
```python
class TransmissionPhysics:
    """Implement specification-compliant transmission physics."""
    
    def __init__(self, params: TransmissionParameters):
        self.params = params
    
    def calculate_kinematic_coupling(self, instantaneous_ratio: ca.SX, 
                                   velocity: ca.SX) -> ca.SX:
        """Calculate kinematic coupling: θ̇ = i(x)·ẋ."""
        return instantaneous_ratio * velocity
    
    def calculate_power_balance(self, output_torque: ca.SX, angular_velocity: ca.SX,
                               piston_force: ca.SX, piston_velocity: ca.SX,
                               power_loss: ca.SX) -> ca.SX:
        """Calculate power balance: τ_out·θ̇ = F_p·ẋ − P_loss."""
        return output_torque * angular_velocity - (piston_force * piston_velocity - power_loss)
    
    def calculate_transmission_efficiency(self, power_loss: ca.SX, 
                                        input_power: ca.SX) -> ca.SX:
        """Calculate transmission efficiency: η = (P_in - P_loss) / P_in."""
        return (input_power - power_loss) / input_power
    
    def calculate_contact_stress(self, contact_force: ca.SX, 
                               contact_radius: ca.SX) -> ca.SX:
        """Calculate Hertzian contact stress."""
        # Simplified Hertzian contact calculation
        return (contact_force / (np.pi * contact_radius**2)) ** 0.5
```

#### Implementation Steps
1. **Create transmission physics module**
   - File: `campro/physics/transmission_physics.py`
   - Implement TransmissionPhysics class

2. **Update EnhancedGearOptimizer**
   - Integrate transmission physics into objective function
   - Add kinematic coupling constraints
   - Implement power balance constraints

### 2.3 Constraint Implementation

#### Current Issues
- Missing essential constraints from specification
- No adiabatic process enforcement
- No kinematic coupling constraints
- No power balance constraints

#### Target Implementation
```python
def add_thermodynamic_constraints(self, g: List[ca.SX], lbg: List[float], 
                                 ubg: List[float], x: ca.SX, v: ca.SX, 
                                 grid: np.ndarray, motion_params: Dict[str, Any]):
    """Add thermodynamic constraints according to specification."""
    
    # Calculate volume and pressure
    volume = self.thermo_physics.calculate_volume(x)
    pressure = self.thermo_physics.calculate_pressure(volume, 
                                                     self.params.initial_pressure_Pa,
                                                     self.params.clearance_volume_m3)
    
    # Adiabatic constraint: pV^γ = const
    adiabatic_constraint = self.thermo_physics.enforce_adiabatic_constraint(
        pressure, volume, self.params.initial_pressure_Pa, 
        self.params.clearance_volume_m3)
    
    for i in range(len(grid)):
        g.append(adiabatic_constraint[i])
        lbg.append(-1e-6)  # Small tolerance
        ubg.append(1e-6)

def add_transmission_constraints(self, g: List[ca.SX], lbg: List[float], 
                                ubg: List[float], sun_radius: ca.SX, 
                                planet_radius: ca.SX, ring_radius: ca.SX,
                                r_inst: ca.SX, displacement: ca.SX, 
                                velocity: ca.SX, grid: np.ndarray):
    """Add transmission constraints according to specification."""
    
    # Kinematic coupling: θ̇ = i(x)·ẋ
    angular_velocity = self.trans_physics.calculate_kinematic_coupling(r_inst, velocity)
    
    # Power balance: τ_out·θ̇ = F_p·ẋ − P_loss
    # (Implementation depends on specific power balance model)
    
    # Contact stress constraints: σ_contact ≤ σ_allow
    contact_stress = self.trans_physics.calculate_contact_stress(
        contact_force, contact_radius)
    
    for i in range(len(grid)):
        g.append(contact_stress[i])
        lbg.append(0.0)
        ubg.append(self.params.max_contact_stress)
```

## Phase 3: Advanced Optimization

### 3.1 Multi-Objective Framework

#### Current Issues
- Simple linear combination of objectives
- No proper normalization
- No Pareto analysis

#### Target Implementation
```python
class AugmentedTchebyshevScalarizer:
    """Implement augmented Tchebyshev scalarization."""
    
    def __init__(self, weights: Dict[str, float], reference_point: Dict[str, float]):
        self.weights = weights
        self.reference_point = reference_point
    
    def scalarize(self, objectives: Dict[str, ca.SX]) -> ca.SX:
        """Scalarize multiple objectives using augmented Tchebyshev."""
        # Normalize objectives
        normalized = {}
        for name, obj in objectives.items():
            if name in self.reference_point:
                normalized[name] = obj / self.reference_point[name]
            else:
                normalized[name] = obj
        
        # Calculate Tchebyshev distance
        max_distance = 0
        for name, obj in normalized.items():
            if name in self.weights:
                distance = self.weights[name] * (obj - self.reference_point[name])
                max_distance = ca.fmax(max_distance, distance)
        
        # Add augmentation term
        augmentation = 0
        for name, obj in normalized.items():
            if name in self.weights:
                augmentation += 0.01 * self.weights[name] * (obj - self.reference_point[name])
        
        return max_distance + augmentation
```

### 3.2 Continuation Implementation

#### Current Issues
- Basic 3-stage continuation
- No proper parameter scheduling
- Missing stress limit factors

#### Target Implementation
```python
class ContinuationScheduler:
    """Implement specification-compliant continuation."""
    
    def __init__(self):
        self.stages = [
            {'epsilon_valve': 1e-1, 'epsilon_friction': 1e-1, 'stress_factor': 0.7},
            {'epsilon_valve': 5e-2, 'epsilon_friction': 5e-2, 'stress_factor': 0.85},
            {'epsilon_valve': 1e-2, 'epsilon_friction': 1e-2, 'stress_factor': 1.0}
        ]
    
    def solve_with_continuation(self, nlp_info: Dict[str, Any], 
                               solver_factory: Callable) -> Dict[str, Any]:
        """Solve with continuation according to specification."""
        solution = None
        
        for stage_idx, stage_params in enumerate(self.stages):
            # Update problem parameters
            updated_nlp = self.update_nlp_parameters(nlp_info, stage_params)
            
            # Solve stage
            if solution is not None:
                # Use previous solution as initial guess
                updated_nlp['x0'] = solution['x']
            
            stage_solution = solver_factory(updated_nlp).solve()
            
            if stage_solution['success']:
                solution = stage_solution
            else:
                # Fallback to previous solution
                break
        
        return solution
```

## Phase 4: Integration and Testing

### 4.1 Test Suite Recovery

#### Current Issues
- 46 failing tests
- Legacy component references
- Incorrect expectations

#### Target Implementation
```python
# Example: Fix enhanced optimizer test
def test_enhanced_motion_law_optimization():
    """Test enhanced motion law optimization with proper expectations."""
    
    # Create test parameters
    params = EnhancedMotionLawParameters(
        node_count=32,
        work_weight=1.0,
        pressure_weight=0.1
    )
    
    # Create optimizer
    optimizer = EnhancedMotionLawOptimizer(params)
    
    # Run optimization
    result = optimizer.optimize_motion_law(test_motion_params)
    
    # Verify results
    assert result['success'] == True
    assert len(result['displacement']) > 0
    assert np.max(result['displacement']) > 0.1  # Should achieve meaningful displacement
    assert 'thermodynamic_data' in result
    assert result['thermodynamic_data']['indicated_work_J'] > 0.0
```

### 4.2 Performance Validation

#### Target Metrics
- **Convergence**: 95% of optimizations converge
- **Accuracy**: KKT error < 1e-6
- **Performance**: < 60s for typical problems
- **Memory**: < 1GB peak usage

#### Implementation
```python
class PerformanceValidator:
    """Validate optimizer performance against targets."""
    
    def validate_convergence(self, results: List[Dict]) -> bool:
        """Validate convergence rate."""
        successful = sum(1 for r in results if r['success'])
        return successful / len(results) >= 0.95
    
    def validate_accuracy(self, result: Dict) -> bool:
        """Validate solution accuracy."""
        return result.get('kkt_error', float('inf')) < 1e-6
    
    def validate_performance(self, result: Dict) -> bool:
        """Validate performance targets."""
        return result.get('execution_time', float('inf')) < 60.0
```

## Implementation Timeline

### Week 1-2: Foundation Stabilization
- [ ] Fix solver configuration
- [ ] Implement variable/objective scaling
- [ ] Resolve array shape issues
- [ ] Get basic convergence working

### Week 3-5: Core Physics Implementation
- [ ] Implement thermodynamic physics
- [ ] Implement transmission physics
- [ ] Add essential constraints
- [ ] Integrate physics into optimizers

### Week 6-8: Advanced Optimization
- [ ] Implement multi-objective framework
- [ ] Add continuation scheduling
- [ ] Implement advanced solver features
- [ ] Add robustness features

### Week 9-10: Integration and Testing
- [ ] Fix test suite
- [ ] Performance validation
- [ ] Documentation updates
- [ ] Final validation

## Success Criteria

### Technical Success
- [ ] 100% test suite compliance
- [ ] Specification compliance achieved
- [ ] Performance targets met
- [ ] Robust convergence achieved

### Quality Success
- [ ] Code quality maintained
- [ ] Documentation complete
- [ ] API consistency preserved
- [ ] Backward compatibility maintained

This technical implementation guide provides the specific code changes and implementation steps needed to achieve full compliance with the unified specification. Each phase builds upon the previous one, ensuring that the system remains stable throughout the implementation process.
