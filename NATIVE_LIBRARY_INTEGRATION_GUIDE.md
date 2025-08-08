# Native Library Integration Guide

## Overview

CamProV5 uses native libraries written in Rust for high-performance calculations:
- `campro_motion.dll`: Motion law calculations
- `campro_fea.dll`: Finite Element Analysis

This guide explains the architecture, implementation details, and best practices for working with these native libraries.

## Architecture

### High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Kotlin UI      │────▶│  JNI Interface  │────▶│  Rust Libraries │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

The application is divided into three main components:
1. **Kotlin UI**: The user interface and application logic
2. **JNI Interface**: The bridge between Kotlin and Rust
3. **Rust Libraries**: High-performance native code for calculations

### Resource Loading

The native libraries are packaged as resources in the JAR file and extracted at runtime. The path resolution logic handles different operating systems and architectures:

```
src/main/resources/
└── native/
    ├── windows/
    │   └── x86_64/
    │       ├── campro_motion.dll
    │       └── campro_fea.dll
    ├── mac/
    │   └── x86_64/
    │       ├── libcampro_motion.dylib
    │       └── libcampro_fea.dylib
    └── linux/
        └── x86_64/
            ├── libcampro_motion.so
            └── libcampro_fea.so
```

## Implementation Details

### JNI Interface

The JNI interface is implemented in the following Kotlin classes:
- `MotionLawEngine.kt`: Handles motion law calculations
- `FeaEngine.kt`: Handles finite element analysis

These classes declare native methods using the `external` keyword:

```kotlin
private external fun createMotionLawNative(parameters: Array<String>): Long
private external fun getDisplacementNative(motionLawId: Long, angle: Double): Double
// ...
```

### Rust Implementation

The Rust implementation is in the `fea-engine` crate. The JNI functions are implemented using the `jni` crate:

```rust
#[no_mangle]
pub extern "system" fn Java_com_campro_v5_animation_MotionLawEngine_createMotionLawNative(
    env: JNIEnv,
    _class: JClass,
    parameters: JObject,
) -> jlong {
    // Implementation
}
```

### Library Loading

The libraries are loaded at runtime using the following process:

1. Determine the OS and architecture
2. Construct the resource path
3. Extract the library to a temporary file
4. Load the library using `System.load()`
5. Verify the library is working correctly

```kotlin
// Normalize OS name
val osName = when {
    System.getProperty("os.name").lowercase().contains("win") -> "windows"
    System.getProperty("os.name").lowercase().contains("mac") -> "mac"
    System.getProperty("os.name").lowercase().contains("nix") || 
    System.getProperty("os.name").lowercase().contains("nux") -> "linux"
    else -> throw UnsupportedOperationException("Unsupported OS: ${System.getProperty("os.name")}")
}

// Construct resource path
val resourcePath = "/native/$osName/$osArch/$libraryName"

// Extract and load the library
// ...
```

## Best Practices

### Error Handling

Always handle errors gracefully when working with native libraries:

```kotlin
try {
    // Extract and load the library
    // ...
} catch (e: Exception) {
    val errorMessage = when (e) {
        is UnsatisfiedLinkError -> "Native library loading error: ${e.message}"
        is IllegalStateException -> "Resource not found: ${e.message}"
        is IOException -> "I/O error while extracting library: ${e.message}"
        else -> "Unexpected error: ${e.message}"
    }
    println("Failed to load native library: $errorMessage")
    // Handle the error
}
```

### Library Verification

Always verify that the library is working correctly after loading:

```kotlin
if (verifyNativeLibrary()) {
    println("Native library verification successful")
} else {
    println("Native library verification failed")
    // Handle the error
}
```

### Memory Management

Be careful with memory management when working with native libraries:

1. Always dispose of native resources when they are no longer needed
2. Be aware of the JNI global references and local references
3. Use `try-finally` blocks to ensure resources are released

```kotlin
try {
    // Use native resources
} finally {
    // Dispose of native resources
    disposeMotionLawNative(motionLawId)
}
```

## Troubleshooting

### Common Issues

1. **Library not found**: Check that the library is in the correct resource path
2. **UnsatisfiedLinkError**: Check that the JNI function signatures match
3. **Verification failed**: Check that the library is compiled correctly

### Debugging Tips

1. Enable detailed logging:
   ```kotlin
   println("Attempting to load native library from resource path: $resourcePath")
   println("Extracted native library to: $tempFile")
   ```

2. Use the verification method to test library functionality:
   ```kotlin
   if (verifyNativeLibrary()) {
       println("Native library verification successful")
   } else {
       println("Native library verification failed")
   }
   ```

3. Check the JNI function signatures:
   ```bash
   javap -s -p com.campro.v5.animation.MotionLawEngine
   ```

## Conclusion

By following this guide, you should be able to understand, maintain, and extend the native library integration in CamProV5. For more information on building the libraries, see the [Animation Engine Implementation Guide](ANIMATION_ENGINE_IMPLEMENTATION.md).