# Animation Engine Implementation Guide

## Overview

The CamProV5 animation engine uses native libraries written in Rust for high-performance calculations:
- `campro_motion.dll`: Motion law calculations
- `campro_fea.dll`: Finite Element Analysis

This document explains how to build, install, and use these native libraries.

## Building the Native Libraries

### Prerequisites
- Rust toolchain (rustc, cargo)
- JDK 11 or later
- Gradle

### Automated Build
The native libraries are now built automatically as part of the Gradle build process:

```bash
./gradlew desktop:build
```

### Manual Build
If you need to build the libraries manually:

1. Build the Rust libraries:
   ```bash
   cd camprofw/rust/fea-engine
   cargo build --release
   ```

2. Copy the libraries to the resources directory:
   ```bash
   # On Windows
   mkdir -p ../../desktop/src/main/resources/native/windows/x86_64
   copy target\release\fea_engine.dll ..\..\desktop\src\main\resources\native\windows\x86_64\campro_motion.dll
   copy target\release\fea_engine.dll ..\..\desktop\src\main\resources\native\windows\x86_64\campro_fea.dll
   
   # On macOS
   mkdir -p ../../desktop/src/main/resources/native/mac/x86_64
   cp target/release/libfea_engine.dylib ../../desktop/src/main/resources/native/mac/x86_64/libcampro_motion.dylib
   cp target/release/libfea_engine.dylib ../../desktop/src/main/resources/native/mac/x86_64/libcampro_fea.dylib
   
   # On Linux
   mkdir -p ../../desktop/src/main/resources/native/linux/x86_64
   cp target/release/libfea_engine.so ../../desktop/src/main/resources/native/linux/x86_64/libcampro_motion.so
   cp target/release/libfea_engine.so ../../desktop/src/main/resources/native/linux/x86_64/libcampro_fea.so
   ```

## Architecture

### JNI Interface
The Rust code exposes functions through JNI that are called by the Kotlin code. The main classes involved are:

- `MotionLawEngine.kt`: Handles motion law calculations
- `FeaEngine.kt`: Handles finite element analysis

### Resource Loading
The libraries are packaged as resources and extracted at runtime. The path resolution logic handles different operating systems and architectures:

- Windows: `native/windows/x86_64/campro_motion.dll` and `native/windows/x86_64/campro_fea.dll`
- macOS: `native/mac/x86_64/libcampro_motion.dylib` and `native/mac/x86_64/libcampro_fea.dylib`
- Linux: `native/linux/x86_64/libcampro_motion.so` and `native/linux/x86_64/libcampro_fea.so`

## Debugging Native Library Issues

1. Check the console for error messages
2. Verify that the libraries are in the correct resource path
3. Use the verification methods to test library functionality
4. Check for JNI signature mismatches

Common error messages and their solutions:

- `Native library not found at /native/...`: The library is not in the expected resource path
- `UnsatisfiedLinkError`: The JNI function signatures don't match
- `Native library verification failed`: The library is loaded but not functioning correctly

## Adding New Native Functions

1. Add the native method declaration in the Kotlin class:
   ```kotlin
   private external fun myNewNativeMethod(param1: String, param2: Int): Double
   ```

2. Implement the JNI function in the Rust code:
   ```rust
   #[no_mangle]
   pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_myNewNativeMethod(
       env: JNIEnv,
       _class: JClass,
       param1: JString,
       param2: jint,
   ) -> jdouble {
       // Implementation
   }
   ```

3. Update the build process if necessary

## Maintenance

The native libraries should be maintained according to the following schedule:
- Monthly dependency updates
- Quarterly performance reviews
- Bi-annual compatibility testing with new OS versions