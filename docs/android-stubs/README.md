# Android Packaging Stubs

This directory contains minimal stubs and documentation for future Android packaging of CamProV5.

## Current Status

Android support has been temporarily removed from the main project to focus development efforts on the desktop application. These stubs are provided for future reference when mobile support is needed.

## Future Implementation Plan

When Android support is re-introduced, the following components will need to be implemented:

### 1. Gradle Configuration
- `android/build.gradle` - Top-level Android build configuration
- `android/app/build.gradle` - App-level build configuration
- `android/gradle.properties` - Android-specific properties
- `android/settings.gradle` - Android module settings

### 2. Android Manifest
- `android/app/src/main/AndroidManifest.xml` - Application manifest with permissions and activities

### 3. Kotlin/Compose UI Components
- `MainActivity.kt` - Main activity with Compose UI
- `InputTab.kt` - Parameter input interface
- `VisualizationTab.kt` - Results visualization
- `CamProV5App.kt` - Application class
- `NativeLibrary.kt` - Native library integration

### 4. Resources
- `colors.xml` - Material Design color scheme
- `strings.xml` - Localized strings
- `styles.xml` - UI styling

### 5. Native Integration
- CMake configuration for C++ components
- JNI bindings for Python bridge
- Native library packaging

## Key Considerations for Future Implementation

1. **UI Adaptation**: Desktop Compose UI will need adaptation for mobile screens
2. **Performance**: Mobile devices have different performance characteristics
3. **Native Libraries**: C++ and Python components need mobile-compatible packaging
4. **Permissions**: Android permissions for file access and native libraries
5. **Testing**: Mobile-specific testing infrastructure

## Integration Points

The Android app will integrate with:
- Desktop Kotlin/Compose UI components (shared)
- Python optimization pipeline (via bridge)
- C++ native components
- Rust FEA engine

## References

- Original Android implementation was removed in [commit/PR reference]
- Desktop implementation: `desktop/` module
- Python bridge: `scripts/kotlin_bridge_cli.py`
- Native components: `cpp/` directory
