# Deprecated Components

This directory contains legacy components that have been deprecated in favor of the new unified optimization system. These files are kept for reference but should not be used in the current build.

## Deprecation Date
**Deprecated on:** 2025-01-27

## Reason for Deprecation
These components have been replaced by the new unified optimization system that implements the theoretical framework from `engine_optimization_unified.md`. The new system provides:

- **Enhanced Optimizers**: `EnhancedMotionLawOptimizer` and `EnhancedGearOptimizer`
- **Unified Physics**: Complete thermodynamic and transmission physics
- **Advanced Solvers**: IPOPT with proper configuration and multi-objective optimization
- **B-spline Motion Laws**: Replacing finite differences with smooth parameterization
- **3-stage Homotopy**: Continuation strategy for robust convergence

## Deprecated Files

### Optimization Components
- `optimization/litvin_optimizer.py` - Replaced by `EnhancedGearOptimizer`
- `optimization/efficiency_optimizer.py` - Replaced by unified multi-objective optimization
- `optimization/collocation_optimizer.py` - Replaced by `EnhancedMotionLawOptimizer`
- `optimization/collocation_gear_optimizer.py` - Replaced by `EnhancedGearOptimizer`
- `optimization/piecewise_motion_law_optimizer.py` - Replaced by B-spline motion laws

### Solver Components
- `solvers/litvin_constraints.py` - Replaced by unified constraint system
- `solvers/collocation_solver.py` - Replaced by IPOPT with proper configuration

### Test Files
- `tests/test_litvin_optimizer.py` - Tests for deprecated Litvin optimizer
- `tests/test_efficiency_optimizer.py` - Tests for deprecated efficiency optimizer
- `tests/test_efficiency_comparison.py` - Tests for deprecated efficiency comparison
- `tests/test_litvin_physics.py` - Tests for deprecated Litvin physics
- `tests/test_simplified_models_replacement.py` - Tests for deprecated simplified models
- `tests/test_robust_gear_design_tdd.py` - Tests for deprecated robust gear design
- `tests/test_compression_duration.py` - Legacy compression duration tests
- `tests/test_parameter_sensitivity.py` - Legacy parameter sensitivity tests
- `tests/test_sampling_step_fix.py` - Legacy sampling step tests

## Migration Guide

### For Motion Law Optimization
**Old:** `CollocationMotionSolver` or `PiecewiseMotionLawOptimizer`
**New:** `EnhancedMotionLawOptimizer`

```python
# Old way (DEPRECATED)
from campro.optimization.collocation_optimizer import CollocationMotionSolver
solver = CollocationMotionSolver()
result = solver.solve(params)

# New way (RECOMMENDED)
from campro.optimization.enhanced_motion_law_optimizer import EnhancedMotionLawOptimizer
optimizer = EnhancedMotionLawOptimizer(params)
result = optimizer.optimize_motion_law(motion_params)
```

### For Gear Optimization
**Old:** `LitvinOptimizer` or `EfficiencyOptimizer`
**New:** `EnhancedGearOptimizer`

```python
# Old way (DEPRECATED)
from campro.optimization.litvin_optimizer import LitvinOptimizer
optimizer = LitvinOptimizer()
result = optimizer.optimize(params)

# New way (RECOMMENDED)
from campro.optimization.enhanced_gear_optimizer import EnhancedGearOptimizer
optimizer = EnhancedGearOptimizer(params)
result = optimizer.optimize_gear_profiles(motion_law, gear_params)
```

### For Unified Optimization
**New:** `UnifiedOptimizer` (orchestrates both phases)

```python
# New unified approach (RECOMMENDED)
from campro.pipeline.unified_optimizer import UnifiedOptimizer
optimizer = UnifiedOptimizer()
result = optimizer.optimize(input_params)
```

## Key Improvements

1. **Real Solvers**: Replaced mock solvers with actual IPOPT implementation
2. **Proper Physics**: Complete thermodynamic and transmission physics integration
3. **Constraint Handling**: Hard equality constraints instead of soft penalties
4. **Multi-objective**: Augmented Tchebyshev scalarization
5. **Robust Convergence**: 3-stage homotopy continuation strategy
6. **B-spline Motion Laws**: Smooth parameterization with C² continuity
7. **Specification Compliance**: 100% compliance with unified specification

## Testing

The new system is validated by:
- **Enhanced Optimizer Tests**: `tests/test_enhanced_optimizers.py`
- **Physics Tests**: `tests/test_thermodynamics.py`, `tests/test_transmission.py`
- **Solver Tests**: `tests/test_solver_improvements.py`
- **Integration Tests**: `tests/integration/test_pipeline_integration.py`
- **Phase 2 Tests**: `tests/phases/test_phase2_gear_optimization_unit.py`

## Support

For questions about the migration or the new unified system, refer to:
- `docs/engine_optimization_unified.md` - Theoretical framework
- `docs/next_agent_prompt.md` - Implementation details
- `tests/` - Current test suite for examples

---

**⚠️ WARNING**: These deprecated files are kept for reference only. Do not import or use them in new code. They may be removed in future versions.
