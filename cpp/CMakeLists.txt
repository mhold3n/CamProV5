cmake_minimum_required(VERSION 3.10)
project(campro-animation)

# Set C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(OpenGL REQUIRED)
find_package(GLEW REQUIRED)
find_package(glfw3 REQUIRED)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${OPENGL_INCLUDE_DIRS}
    ${GLEW_INCLUDE_DIRS}
)

# Source files
set(SOURCES
    src/CamAnimation.cpp
    src/campro_animation_NativeLibrary.cpp
)

# Define the library
add_library(campro-animation SHARED ${SOURCES})

# Link libraries
target_link_libraries(campro-animation
    ${OPENGL_LIBRARIES}
    ${GLEW_LIBRARIES}
    glfw
)

# Set output directory
set_target_properties(campro-animation PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../android/app/src/main/jniLibs/${ANDROID_ABI}"
)

# Android specific configurations
if(ANDROID)
    # Find Android NDK
    find_library(log-lib log)
    
    # Link Android specific libraries
    target_link_libraries(campro-animation ${log-lib})
    
    # Set library name prefix to "lib" and suffix to ".so"
    set_target_properties(campro-animation PROPERTIES
        PREFIX "lib"
        SUFFIX ".so"
    )
endif()