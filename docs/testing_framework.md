# Test Suite Organization and Execution

## Overview

The CamProV5 test suite provides comprehensive validation coverage for both the frontend Kotlin components and the collocation solver system. This document outlines the test organization, execution procedures, and coverage requirements.

## Test Suite Structure

### 1. Core Frontend Tests (`desktop/src/test/kotlin/com/campro/v5/animation/`)

#### Data Handling and Fixtures
- **`FixtureLoaderTest.kt`** - Validates loading of motion law fixtures from JSON
- **`AngleInterpolatorTest.kt`** - Tests circular domain interpolation utilities

#### Motion Law Generation and Processing
- **`MotionIngestionTest.kt`** - Tests periodicity, interpolation, and grid-agnostic rendering
- **`MotionLawEngineIntegrationTest.kt`** - Robust integration tests for the public API
- **`ComprehensiveCollocationValidationTest.kt`** - Cross-validation between piecewise and collocation solvers

#### UI and Rendering Validation
- **`RenderingPathSelectionTest.kt`** - Ensures correct rendering path selection (Litvin vs. fallback)
- **`TransmissionUsageTest.kt`** - Validates transmission data usage and denominator handling
- **`KinematicConsistencyTest.kt`** - Verifies `getComponentPositions` accuracy against Litvin tables
- **`CamPathGenerationTest.kt`** - Data-based tests for cam profile generation

#### Performance and Robustness
- **`InterpolationPerformanceTest.kt`** - Performance testing for interpolation utilities (10k queries)
- **`PerformanceBenchmarkTest.kt`** - Solver performance benchmarking and stress testing
- **`ErrorHandlingTest.kt`** - Error handling with invalid/missing fixtures

### 2. Validation and Integration Tests

#### Collocation System Validation
- **`CollocationSpecificValidationTest.kt`** - Mathematical validation for discretization accuracy
- **`CollocationValidationTest.kt`** - Basic collocation framework validation
- **`CollocationMathTest.kt`** - Comprehensive mathematical core testing

#### Feature Integration
- **`FeatureFlagIntegrationTest.kt`** - Feature flag behavior across UI and solver availability
- **`CollocationPythonBridgeIntegrationTest.kt`** - Python-Kotlin bridge validation

#### Regression and Quality Assurance
- **`RegressionFixturesTest.kt`** - Regression testing against known-good fixtures
- **`NumericalStabilityTest.kt`** - Edge case testing with extreme parameter values
- **`MockBasedComponentTest.kt`** - Testing components isolated from external dependencies

## Test Execution

### Local Development

```bash
# Run all tests
./gradlew :desktop:test

# Run specific test categories
./gradlew :desktop:test --tests "*MotionLaw*"
./gradlew :desktop:test --tests "*Collocation*"
./gradlew :desktop:test --tests "*Integration*"

# Run with coverage report
./gradlew :desktop:test :desktop:jacocoTestReport

# View coverage report
open desktop/build/reports/jacoco/test/html/index.html
```

### Continuous Integration

Tests are automatically executed via GitHub Actions in `.github/workflows/desktop-tests.yml`:

```yaml
- name: Run desktop tests
  run: ./gradlew :desktop:test --no-daemon --stacktrace
  
- name: Generate coverage report
  run: ./gradlew :desktop:jacocoTestReport
  
- name: Verify coverage thresholds
  run: ./gradlew :desktop:jacocoTestCoverageVerification
```

## Coverage Requirements

### Minimum Thresholds
- **Overall Coverage**: 60% minimum
- **Branch Coverage**: 50% minimum

### Coverage Focus Areas
1. **Motion Law Generation**: Core algorithms and parameter handling
2. **UI Components**: Data ingestion, interpolation, rendering logic
3. **Collocation System**: Mathematical core, constraint generation, solver integration
4. **Error Handling**: Graceful degradation and error propagation

### Excluded from Coverage
- Native JNI interface code (tested via integration)
- External library integrations (mocked in tests)
- UI layout code (tested via manual/visual testing)

## Test Categories and Their Purpose

### 1. Unit Tests
- **Purpose**: Test individual components in isolation
- **Examples**: `AngleInterpolatorTest`, `FixtureLoaderTest`
- **Characteristics**: Fast, deterministic, no external dependencies

### 2. Integration Tests
- **Purpose**: Test component interactions and system behavior
- **Examples**: `MotionLawEngineIntegrationTest`, `FeatureFlagIntegrationTest`
- **Characteristics**: Test real API interactions, may involve multiple modules

### 3. Validation Tests
- **Purpose**: Verify mathematical correctness and solver accuracy
- **Examples**: `ComprehensiveCollocationValidationTest`, `CollocationMathTest`
- **Characteristics**: Cross-validate different implementations, verify constraints

### 4. Performance Tests
- **Purpose**: Ensure acceptable performance characteristics
- **Examples**: `PerformanceBenchmarkTest`, `InterpolationPerformanceTest`
- **Characteristics**: Measure timing, memory usage, stress testing

### 5. Regression Tests
- **Purpose**: Prevent unintended changes to established behavior
- **Examples**: `RegressionFixturesTest`
- **Characteristics**: Compare against golden fixtures, detect behavioral drift

## Test Data and Fixtures

### Fixture Organization
```
desktop/fixtures/
├── motion_samples_small.json    # Coarse grid motion data
├── motion_samples_fine.json     # Fine grid motion data
└── [future fixtures]
```

### Fixture Metadata
All fixtures include embedded generator metadata:
```json
{
  "generator": {
    "version": "1.0.0",
    "commit": "abc123",
    "created_utc": "2025-01-01T00:00:00Z",
    "params": {
      "samplingStepDeg": 5.0,
      "strokeLengthMm": 10.0,
      ...
    }
  },
  "stepDeg": 5.0,
  "samples": [...]
}
```

### Fixture Regeneration
Use `FixtureRegenerator.kt` to programmatically update fixtures when algorithm changes are intentional:

```kotlin
// Regenerate fixtures with current algorithm
val regenerator = FixtureRegenerator()
regenerator.regenerateSmallFixture()
```

## Debugging and Troubleshooting

### Common Issues

1. **Test Timeout**: Reduce sample sizes or use coarser grids for performance tests
2. **Numerical Precision**: Adjust tolerances based on expected algorithm precision
3. **Fixture Mismatch**: Use regression test debug output to understand differences
4. **External Dependencies**: Check mock configurations and fallback behavior

### Debug Output
Many tests include debug output for troubleshooting:
```
Requested stroke: 10.0 mm, Actual stroke: 0.086 mm, Ratio: 0.0086
RPM: 1000.0, Max velocity: 0.278 mm/rad
```

### Test Reports
Detailed test reports are generated at:
- **Test Results**: `desktop/build/reports/tests/test/index.html`
- **Coverage Report**: `desktop/build/reports/jacoco/test/html/index.html`

## Best Practices

### Writing New Tests
1. **Descriptive Names**: Use backtick syntax for readable test names
2. **Isolated Setup**: Each test should be independent
3. **Clear Assertions**: Include descriptive failure messages
4. **Appropriate Tolerances**: Balance precision with practical numerical limits

### Maintaining Tests
1. **Regular Review**: Update tolerances as algorithms improve
2. **Performance Monitoring**: Watch for test execution time increases
3. **Fixture Management**: Keep fixtures current with algorithm changes
4. **Documentation**: Update this document when adding new test categories

### Contributing Tests
1. **Follow Existing Patterns**: Maintain consistency with existing test structure
2. **Add Coverage**: Focus on untested code paths
3. **Include Edge Cases**: Test boundary conditions and error paths
4. **Document Intent**: Explain what the test validates and why it's important

## Future Enhancements

### Planned Additions
1. **Parameterized Testing Framework**: Systematic solver comparison across parameter space
2. **Visual Regression Tests**: Automated comparison of generated plots/visualizations
3. **Load Testing**: Multi-threaded stress testing for concurrent operations
4. **Property-Based Testing**: Use Hypothesis-style testing for mathematical properties

### Integration Opportunities
1. **Native Library Testing**: Direct testing of Rust components
2. **UI Testing**: Automated testing of Compose UI components
3. **End-to-End Testing**: Full workflow validation from parameter input to visualization
4. **Performance Benchmarking**: Automated performance regression detection
