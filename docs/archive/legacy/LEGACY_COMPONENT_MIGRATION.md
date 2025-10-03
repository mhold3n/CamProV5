# Legacy Component Migration Guide

## Overview

This guide explains how to safely transition from the old workflow components to the new unified optimization pipeline without permanently removing code. We use feature flags to deactivate problematic components while ensuring the new workflow is complete.

## Feature Flag System

### Old Workflow Components (Currently Deactivated)

| Component | Feature Flag | Status | Reason for Deactivation |
|-----------|--------------|--------|------------------------|
| `MotionLawEngine` | `ENABLE_OLD_MOTION_LAW_ENGINE` | ❌ Deactivated | Complex fallback logic and native method calls |
| `MotionLawGenerator` | `ENABLE_OLD_MOTION_LAW_GENERATOR` | ❌ Deactivated | Piecewise fallback with 360° periodicity issues |
| `DiagnosticsPreflight` | `ENABLE_OLD_DIAGNOSTICS_PREFLIGHT` | ❌ Deactivated | Diagnostics for removed system |
| `PerfDiag` | `ENABLE_OLD_PERF_DIAG` | ❌ Deactivated | Performance diagnostics for old system |
| `CollocationMotionSolver` | `ENABLE_OLD_COLLOCATION_MOTION_SOLVER` | ❌ Deactivated | Problematic Python bridge implementation |

### New Workflow Components (Currently Active)

| Component | Feature Flag | Status | Description |
|-----------|--------------|--------|-------------|
| `UnifiedOptimizationPipeline` | `ENABLE_NEW_UNIFIED_OPTIMIZATION` | ✅ Active | New robust optimization workflow |
| `OptimizationStateManager` | `ENABLE_NEW_OPTIMIZATION_STATE_MANAGER` | ✅ Active | New state management system |
| `UnifiedOptimizationBridge` | `ENABLE_NEW_OPTIMIZATION_BRIDGE` | ✅ Active | New Python bridge |
| `VisualizationComponents` | `ENABLE_NEW_VISUALIZATION_COMPONENTS` | ✅ Active | New visualization system |
| `AdvancedFeatures` | `ENABLE_NEW_ADVANCED_FEATURES` | ✅ Active | Presets, export, batch processing |

## Migration Steps

### Step 1: Update Code to Use Feature Flags

Instead of directly accessing old components, use the `LegacyComponentWrapper`:

```kotlin
// OLD WAY (Direct access - will cause compilation errors)
val motionLaw = MotionLawEngine.generateMotionLaw(params)

// NEW WAY (Safe access with feature flags)
val motionLaw = LegacyComponentWrapper.withMotionLawEngine {
    MotionLawEngine.generateMotionLaw(params)
} ?: run {
    // Fallback to new workflow
    UnifiedOptimizationBridge.runOptimization(params)
}
```

### Step 2: Replace Old Component Usage

#### Motion Law Generation
```kotlin
// OLD: MotionLawEngine
// NEW: UnifiedOptimizationBridge
val result = UnifiedOptimizationBridge.runOptimization(parameters)
```

#### Diagnostics
```kotlin
// OLD: DiagnosticsPreflight
// NEW: ErrorHandler and PerformanceOptimizer
ErrorHandler.reportError(error)
PerformanceOptimizer.trackPerformance(metrics)
```

#### Performance Monitoring
```kotlin
// OLD: PerfDiag
// NEW: PerformanceOptimizer
PerformanceOptimizer.trackRenderTime(componentName, renderTime)
```

### Step 3: Update UI Components

#### CamProTiles.kt
```kotlin
// Replace old tile configurations with new ones
TileConfig(
    id = "unified_optimization",
    title = "Unified Optimization",
    content = { UnifiedOptimizationTile(onResultsReceived = it) }
)
```

#### DesktopMain.kt
```kotlin
// Remove old component initialization
// OLD: MotionLawEngine.initialize()
// NEW: UnifiedOptimizationBridge.initialize()
```

## Safe Deactivation Process

### Phase 1: Deactivate with Warnings
1. Set feature flags to `false`
2. Enable `SHOW_OLD_FEATURE_WARNINGS = true`
3. Enable `LOG_OLD_FEATURE_USAGE = true`
4. Test that new workflow works correctly

### Phase 2: Validate New Workflow
1. Run comprehensive test suite
2. Verify all functionality is replicated
3. Check performance is maintained or improved
4. Validate user experience is equivalent or better

### Phase 3: Remove Legacy Code (Future)
1. Once new workflow is fully validated
2. Remove old component files
3. Clean up unused imports and dependencies
4. Update documentation

## Compilation Fixes

### Missing Imports
Add these imports to fix compilation errors:

```kotlin
// For Compose UI
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.layout.padding
import androidx.compose.ui.graphics.Color

// For Coroutines
import kotlinx.coroutines.sync.Semaphore

// For File I/O
import java.nio.file.Paths
```

### API Mismatches
Replace Android APIs with Desktop equivalents:

```kotlin
// OLD: android.graphics.Color
// NEW: androidx.compose.ui.graphics.Color

// OLD: android.graphics.Paint
// NEW: androidx.compose.ui.graphics.Paint
```

## Testing Strategy

### 1. Feature Flag Testing
```kotlin
@Test
fun testOldFeaturesDeactivated() {
    assertFalse(FeatureFlags.ENABLE_OLD_MOTION_LAW_ENGINE)
    assertFalse(FeatureFlags.ENABLE_OLD_MOTION_LAW_GENERATOR)
    assertFalse(FeatureFlags.ENABLE_OLD_DIAGNOSTICS_PREFLIGHT)
}

@Test
fun testNewFeaturesActive() {
    assertTrue(FeatureFlags.ENABLE_NEW_UNIFIED_OPTIMIZATION)
    assertTrue(FeatureFlags.ENABLE_NEW_OPTIMIZATION_STATE_MANAGER)
    assertTrue(FeatureFlags.ENABLE_NEW_OPTIMIZATION_BRIDGE)
}
```

### 2. Legacy Wrapper Testing
```kotlin
@Test
fun testLegacyWrapperBlocksDeactivatedFeatures() {
    val result = LegacyComponentWrapper.withMotionLawEngine {
        MotionLawEngine.generateMotionLaw(params)
    }
    assertNull(result) // Should be null when deactivated
}
```

### 3. New Workflow Testing
```kotlin
@Test
fun testNewWorkflowReplacesOldFunctionality() {
    val result = UnifiedOptimizationBridge.runOptimization(params)
    assertNotNull(result)
    assertTrue(result.isSuccess())
}
```

## Rollback Plan

If issues arise with the new workflow:

1. **Immediate Rollback**: Set old feature flags to `true`
2. **Investigate**: Use logging to identify issues
3. **Fix**: Address problems in new workflow
4. **Re-test**: Validate fixes work correctly
5. **Re-deactivate**: Set old feature flags to `false` again

## Benefits of This Approach

1. **Safety**: No permanent code removal until new workflow is validated
2. **Gradual Migration**: Can transition component by component
3. **Rollback Capability**: Can quickly revert if issues arise
4. **Testing**: Can compare old vs new workflow results
5. **Documentation**: Clear migration path and status

## Next Steps

1. ✅ Create feature flag system
2. ✅ Create legacy component wrapper
3. 🔄 Update code to use feature flags
4. 🔄 Fix compilation errors in new components
5. 🔄 Run comprehensive test suite
6. 🔄 Validate new workflow completeness
7. 🔄 Remove legacy code (future)

This approach ensures a safe transition while maintaining the ability to rollback if needed.
