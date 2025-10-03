# CamProV5 Test Suite Structure

This document describes the organized structure of the CamProV5 test suite after refactoring.

## Directory Structure

```
tests/
├── __init__.py
├── README.md
├── test_summary.md
├── cli_pipeline/           # CLI and pipeline tests
│   ├── __init__.py
│   ├── test_cli_placeholder_fallback.py
│   └── test_pipeline_cli.py
├── collocation/            # Collocation method tests
│   ├── __init__.py
│   ├── test_collocation_constraint_relaxation.py
│   ├── test_constraint_relaxation_improved.py
│   ├── test_discretization_periodic_nodes.py
│   └── test_extracted_collocation.py
├── fea/                    # Finite Element Analysis tests
│   ├── __init__.py
│   ├── test_fea_analyzer.py
│   └── test_rust_engine_wrapper.py
├── gear_generation/        # Gear profile generation tests
│   ├── __init__.py
│   ├── test_extracted_gear_generation.py
│   ├── test_profile_generator_uses_r_inst.py
│   └── test_tooth_generator.py
├── integration/            # Integration and end-to-end tests
│   ├── __init__.py
│   ├── test_kotlin_integration.py
│   ├── test_pipeline_integration.py
│   ├── test_python_bridge_roundtrip.py
│   ├── test_unified_pipeline.py
│   └── test_unified_pipeline_backcompat_ratio.py
├── optimization/           # Optimization algorithm tests
│   ├── __init__.py
│   ├── test_collocation_gear_optimizer.py
│   ├── test_efficiency_comparison.py
│   ├── test_efficiency_optimizer.py
│   └── test_litvin_optimizer.py
├── phases/                 # Phase-specific optimization tests
│   ├── __init__.py
│   ├── test_phase1_motion_law_unit.py
│   ├── test_phase2_backcompat_fixed_ratio.py
│   ├── test_phase2_gear_optimization_unit.py
│   ├── test_phase2_global_ratio.py
│   ├── test_phase2_r_no_slip.py
│   ├── test_piecewise_initial_guess.py
│   └── test_simplified_models_replacement.py
├── physics/                # Physics and calculation tests
│   ├── __init__.py
│   ├── test_extracted_physics.py
│   ├── test_force_transfer_analyzer.py
│   ├── test_litvin_physics.py
│   └── test_physics_calculations.py
├── robust_design/          # Robust design and TDD tests
│   ├── __init__.py
│   ├── test_robust_gear_design.py
│   └── test_robust_gear_design_tdd.py
└── ui/                     # User interface component tests
    ├── __init__.py
    └── test_ui_components.py
```

## Test Categories

### 1. Physics Tests (`physics/`)
Tests for physics calculations, force transfer analysis, and motion law physics.

### 2. Optimization Tests (`optimization/`)
Tests for various optimization algorithms including collocation, efficiency optimization, and Litvin optimization.

### 3. Phase Tests (`phases/`)
Tests specific to Phase 1 (motion law optimization) and Phase 2 (gear profile optimization) of the system.

### 4. Integration Tests (`integration/`)
End-to-end tests, pipeline integration, and cross-language integration tests.

### 5. UI Tests (`ui/`)
User interface component tests and widget functionality tests.

### 6. FEA Tests (`fea/`)
Finite Element Analysis tests and Rust engine wrapper tests.

### 7. Gear Generation Tests (`gear_generation/`)
Tests for gear profile generation, tooth generation, and profile calculations.

### 8. Collocation Tests (`collocation/`)
Tests for collocation methods, constraint relaxation, and discretization.

### 9. Robust Design Tests (`robust_design/`)
Tests for robust design methodologies and Test-Driven Development approaches.

### 10. CLI Pipeline Tests (`cli_pipeline/`)
Command-line interface tests and pipeline execution tests.

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Tests by Category
```bash
# Physics tests
pytest tests/physics/

# Optimization tests
pytest tests/optimization/

# Phase tests
pytest tests/phases/

# Integration tests
pytest tests/integration/

# UI tests
pytest tests/ui/

# FEA tests
pytest tests/fea/

# Gear generation tests
pytest tests/gear_generation/

# Collocation tests
pytest tests/collocation/

# Robust design tests
pytest tests/robust_design/

# CLI pipeline tests
pytest tests/cli_pipeline/
```

### Run Specific Test Files
```bash
pytest tests/physics/test_physics_calculations.py
pytest tests/optimization/test_efficiency_optimizer.py
pytest tests/phases/test_phase1_motion_law_unit.py
```

### Run Tests with TDD Runner
```bash
python run_unit_tests_tdd.py
```

## Test Configuration

The test configuration is managed through:
- `pytest.ini`: Main pytest configuration
- `run_unit_tests_tdd.py`: TDD test runner with difficulty levels
- `run_integration_tests.sh`: Integration test runner

## Migration Notes

This structure was created by refactoring the previously flat test directory structure. All import paths and references have been updated to maintain functionality. The refactoring preserves:

1. All existing test functionality
2. Import statements and module references
3. Test runner compatibility
4. CI/CD integration
5. Documentation references

## Future Enhancements

1. Add category-specific test runners
2. Implement test coverage reporting by category
3. Add performance benchmarks by category
4. Create category-specific documentation
5. Implement parallel test execution by category
