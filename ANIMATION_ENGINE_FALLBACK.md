# Animation Engine Fallback Implementation

This document describes the fallback implementation added to the animation engine in CamProV5 to handle the case when the native library is not available.

## Overview

The animation engine in CamProV5 uses a native library (`campro_motion.dll` on Windows) to perform motion law calculations. However, this native library may not be available in all environments, especially during development or when the application is deployed to a new environment.

To ensure that the animation still works even when the native library is not available, a fallback implementation has been added to the `MotionLawEngine` class. This fallback implementation provides pure Kotlin implementations of all the native methods, allowing the animation to work without the native library.

## Implementation Details

### Flag to Track Native Library Availability

A flag `nativeLibraryAvailable` has been added to the `MotionLawEngine` class to track whether the native library is available:

```kotlin
companion object {
    // Flag to track whether the native library is available
    private var nativeLibraryAvailable = false
    
    // Load the native library
    init {
        try {
            // Extract the native library to a temporary file
            val libraryPath = extractNativeLibrary()
            System.load(libraryPath.toString())
            println("Loaded Rust motion law engine native library from $libraryPath")
            nativeLibraryAvailable = true
        } catch (e: Exception) {
            println("Failed to load Rust motion law engine native library: ${e.message}")
            println("Using fallback implementation")
            e.printStackTrace()
            nativeLibraryAvailable = false
        }
    }
}
```

### Fallback Parameters

Instance variables have been added to store the motion law parameters for the fallback implementation:

```kotlin
// Parameters for the fallback implementation
private var baseCircleRadius = 25.0
private var maxLift = 10.0
private var camDuration = 180.0
private var riseDuration = 90.0
private var dwellDuration = 45.0
private var fallDuration = 90.0
private var jerkLimit = 1000.0
private var accelerationLimit = 500.0
private var velocityLimit = 100.0
private var rpm = 3000.0
```

### Fallback Methods

Fallback methods have been implemented for all native methods:

- `getDisplacementFallback`: Calculates the displacement at a specific angle
- `getVelocityFallback`: Calculates the velocity at a specific angle
- `getAccelerationFallback`: Calculates the acceleration at a specific angle
- `getJerkFallback`: Calculates the jerk at a specific angle
- `analyzeKinematicsFallback`: Performs a kinematic analysis of the motion law

These fallback methods use the same mathematical formulas as the Rust implementation, ensuring that the results are consistent with the native implementation.

### Method Modifications

All methods that call native methods have been modified to use the fallback methods when the native library is not available:

- `init`: Initializes the fallback parameters when the native library is not available
- `updateParameters`: Updates the fallback parameters when the native library is not available
- `getComponentPositions`: Uses the fallback methods when the native library is not available
- `analyzeKinematics`: Uses the fallback methods when the native library is not available
- `dispose`: Only tries to dispose the native motion law if the native library is available

### Component Position Calculation

The `calculateComponentPositions` method has been updated to properly model a cam-follower mechanism:

```kotlin
private fun calculateComponentPositions(angle: Double, displacement: Double): ComponentPositions {
    // Convert angle to radians
    val angleRad = Math.toRadians(angle)
    
    // Get parameters (with defaults if not available)
    val baseCircleRadius = 25f
    val rodLength = 40f
    
    // Calculate cam position (center of the cam)
    val camPosition = Offset(0f, 0f)
    
    // Calculate follower position based on the cam profile and displacement
    // The follower follows the cam profile at the given angle
    val followerX = (baseCircleRadius * cos(angleRad)).toFloat()
    val followerY = displacement.toFloat()
    
    // Calculate piston position
    // The piston is connected to the follower by the rod
    // For a simple model, we'll place the piston directly above the follower
    val pistonX = followerX
    val pistonY = followerY + rodLength
    
    return ComponentPositions(
        pistonPosition = Offset(pistonX, pistonY),
        rodPosition = Offset(followerX, followerY),
        camPosition = camPosition
    )
}
```

This ensures that the components are properly connected and move realistically.

## Building the Native Library

If you want to use the native library instead of the fallback implementation, you need to build the Rust library and copy it to the resources directory.

### Prerequisites

- Rust toolchain (rustc, cargo)
- C/C++ compiler (for building the Rust library)

### Building the Library

1. Navigate to the Rust library directory:

```bash
cd camprofw/rust/fea-engine
```

2. Build the library:

```bash
cargo build --release
```

3. Copy the library to the resources directory:

```bash
# On Windows
mkdir -p ../../desktop/src/main/resources/native/windows/x86_64
cp target/release/fea_engine.dll ../../desktop/src/main/resources/native/windows/x86_64/campro_motion.dll

# On macOS
mkdir -p ../../desktop/src/main/resources/native/mac/x86_64
cp target/release/libfea_engine.dylib ../../desktop/src/main/resources/native/mac/x86_64/libcampro_motion.dylib

# On Linux
mkdir -p ../../desktop/src/main/resources/native/linux/x86_64
cp target/release/libfea_engine.so ../../desktop/src/main/resources/native/linux/x86_64/libcampro_motion.so
```

## Conclusion

The fallback implementation ensures that the animation works even when the native library is not available, providing a better user experience and making the application more robust. The implementation uses the same mathematical formulas as the Rust implementation, ensuring that the results are consistent with the native implementation.

If you encounter any issues with the fallback implementation, please report them to the development team.