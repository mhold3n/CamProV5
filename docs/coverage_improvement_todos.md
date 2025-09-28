# Coverage Improvement TODOs

## Current Status
- JaCoCo thresholds temporarily reduced to 0.5% instruction, 0% branch coverage
- Root cause of 0% coverage fixed (JaCoCo 0.8.12, proper class directories, exclusions)
- Need to add comprehensive tests to raise thresholds back to production levels

## Phase 1: Core Animation Tests (Target: 5% instruction, 3% branch)

### MotionLawGenerator Tests
- [ ] **Unit tests for piecewise output size and continuity**
  - Test output array length matches input parameters
  - Test continuity at phase boundaries (position, velocity, acceleration)
  - Test bounds compliance (position within [0, stroke])
  - Test smooth transitions between rise/return/dwell phases

- [ ] **Property-based tests across RampProfile variants**
  - Test all RampProfile enum values (CYCLOIDAL, MODIFIED_SINE, etc.)
  - Test various dwell ranges (0%, 10%, 50%, 90% of cycle)
  - Test edge cases: very short cycles, very long cycles
  - Test parameter combinations that should fail gracefully

### CollocationMotionSolver Tests
- [ ] **Integration tests for stroke attainment and periodicity validation**
  - Test stroke attainment within ±5% tolerance
  - Test periodicity validation (x, v, a at start/end)
  - Test validation failure scenarios (invalid solutions)
  - Test error handling when Python bridge fails

## Phase 2: FEA Integration Tests (Target: 8% instruction, 5% branch)

### FeaResultsLoader Tests
- [ ] **Edge-case tests for missing fields and short time series**
  - Test parsing with missing timeSteps field
  - Test parsing with empty displacements array
  - Test parsing with malformed stress data
  - Test handling of very short time series (1-2 points)
  - Test schema validation and error reporting

### FeaEngine Tests
- [ ] **Error paths and diagnostics reporting**
  - Test JNI failure scenarios
  - Test invalid input parameter handling
  - Test memory allocation failures
  - Test diagnostic message formatting
  - Test error propagation to calling code

## Phase 3: Configuration and CLI Tests (Target: 10% instruction, 8% branch)

### Config Package Tests
- [ ] **CLI parsing and argument handling**
  - Test valid --input/--output argument parsing
  - Test invalid argument combinations
  - Test file path validation
  - Test error message formatting
  - Test help text generation

## Phase 4: Full Coverage (Target: 15% instruction, 12% branch)

### Comprehensive Integration
- [ ] **End-to-end workflow tests**
  - Test complete motion law generation pipeline
  - Test FEA analysis round-trip
  - Test error handling across module boundaries
  - Test performance under various load conditions

## Threshold Progression Plan

| Phase | Instruction | Branch | Status |
|-------|-------------|--------|---------|
| Current | 0.5% | 0% | ✅ Active |
| Phase 1 | 5% | 3% | 🔄 In Progress |
| Phase 2 | 8% | 5% | ⏳ Pending |
| Phase 3 | 10% | 8% | ⏳ Pending |
| Phase 4 | 15% | 12% | ⏳ Pending |
| Production | 20% | 15% | 🎯 Goal |

## Implementation Notes

- Each phase should be completed before moving to the next
- Tests should be added incrementally to avoid breaking existing functionality
- Coverage reports should be generated after each phase to verify progress
- Exclusions should be gradually removed as coverage improves
- Final production thresholds should be realistic but meaningful

## Files to Modify

- `desktop/src/test/kotlin/com/campro/v5/animation/MotionLawGeneratorTest.kt` (new)
- `desktop/src/test/kotlin/com/campro/v5/animation/CollocationMotionSolverTest.kt` (new)
- `desktop/src/test/kotlin/com/campro/v5/animation/FeaResultsLoaderTest.kt` (expand)
- `desktop/src/test/kotlin/com/campro/v5/animation/FeaEngineTest.kt` (new)
- `desktop/src/test/kotlin/com/campro/v5/config/ConfigTest.kt` (new)
- `desktop/build.gradle.kts` (update thresholds)
