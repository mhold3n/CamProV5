#include <jni.h>
#include "../include/CamAnimation.h"
#include <unordered_map>
#include <vector>
#include <iostream>

// Global map of animation contexts
std::unordered_map<jlong, CamAnimation*> g_animationContexts;
jlong g_nextContextId = 1;

// Helper function to convert Java float array to C++ vector
std::vector<float> jfloatArrayToVector(JNIEnv* env, jfloatArray jArray) {
    if (jArray == nullptr) {
        return std::vector<float>();
    }
    
    jsize length = env->GetArrayLength(jArray);
    std::vector<float> result(length);
    
    jfloat* elements = env->GetFloatArrayElements(jArray, nullptr);
    for (jsize i = 0; i < length; ++i) {
        result[i] = elements[i];
    }
    
    env->ReleaseFloatArrayElements(jArray, elements, JNI_ABORT);
    return result;
}

extern "C" {

// Initialize the native library
JNIEXPORT void JNICALL
Java_com_campro_v5_NativeLibrary_initialize(JNIEnv* env, jobject thiz) {
    // Initialize global resources if needed
    std::cout << "Native library initialized" << std::endl;
}

// Create an animation context
JNIEXPORT jlong JNICALL
Java_com_campro_v5_NativeLibrary_createAnimationContext(JNIEnv* env, jobject thiz, jint width, jint height) {
    CamAnimation* animation = new CamAnimation();
    if (!animation->initialize(width, height)) {
        std::cerr << "Failed to initialize animation context" << std::endl;
        delete animation;
        return 0;
    }
    
    jlong contextId = g_nextContextId++;
    g_animationContexts[contextId] = animation;
    std::cout << "Created animation context with ID: " << contextId << std::endl;
    return contextId;
}

// Destroy an animation context
JNIEXPORT void JNICALL
Java_com_campro_v5_NativeLibrary_destroyAnimationContext(JNIEnv* env, jobject thiz, jlong contextHandle) {
    auto it = g_animationContexts.find(contextHandle);
    if (it != g_animationContexts.end()) {
        delete it->second;
        g_animationContexts.erase(it);
        std::cout << "Destroyed animation context with ID: " << contextHandle << std::endl;
    } else {
        std::cerr << "Invalid animation context handle: " << contextHandle << std::endl;
    }
}

// Update animation data
JNIEXPORT void JNICALL
Java_com_campro_v5_NativeLibrary_updateAnimationData(
    JNIEnv* env, jobject thiz, jlong contextHandle,
    jfloatArray baseCamTheta, jfloatArray baseCamR,
    jfloatArray baseCamX, jfloatArray baseCamY,
    jfloatArray phiArray, jfloatArray centerRArray,
    jfloat n, jfloat stroke, jfloat tdcOffset,
    jfloatArray innerEnvelopeTheta, jfloatArray innerEnvelopeR,
    jfloat outerBoundaryRadius, jfloat rodLength, jfloat cycleRatio
) {
    auto it = g_animationContexts.find(contextHandle);
    if (it == g_animationContexts.end()) {
        std::cerr << "Invalid animation context handle: " << contextHandle << std::endl;
        return;
    }
    
    // Convert Java arrays to C++ vectors
    std::vector<float> baseCamThetaVec = jfloatArrayToVector(env, baseCamTheta);
    std::vector<float> baseCamRVec = jfloatArrayToVector(env, baseCamR);
    std::vector<float> baseCamXVec = jfloatArrayToVector(env, baseCamX);
    std::vector<float> baseCamYVec = jfloatArrayToVector(env, baseCamY);
    std::vector<float> phiArrayVec = jfloatArrayToVector(env, phiArray);
    std::vector<float> centerRArrayVec = jfloatArrayToVector(env, centerRArray);
    std::vector<float> innerEnvelopeThetaVec = jfloatArrayToVector(env, innerEnvelopeTheta);
    std::vector<float> innerEnvelopeRVec = jfloatArrayToVector(env, innerEnvelopeR);
    
    // Update animation data
    it->second->updateData(
        baseCamThetaVec, baseCamRVec, baseCamXVec, baseCamYVec,
        phiArrayVec, centerRArrayVec, n, stroke, tdcOffset,
        innerEnvelopeThetaVec, innerEnvelopeRVec,
        outerBoundaryRadius, rodLength, cycleRatio
    );
    
    std::cout << "Updated animation data for context: " << contextHandle << std::endl;
}

// Render a frame
JNIEXPORT void JNICALL
Java_com_campro_v5_NativeLibrary_renderFrame(JNIEnv* env, jobject thiz, jlong contextHandle) {
    auto it = g_animationContexts.find(contextHandle);
    if (it != g_animationContexts.end()) {
        it->second->render();
    } else {
        std::cerr << "Invalid animation context handle: " << contextHandle << std::endl;
    }
}

// Get the OpenGL texture ID
JNIEXPORT jint JNICALL
Java_com_campro_v5_NativeLibrary_getTextureId(JNIEnv* env, jobject thiz, jlong contextHandle) {
    auto it = g_animationContexts.find(contextHandle);
    if (it != g_animationContexts.end()) {
        return static_cast<jint>(it->second->getTextureId());
    } else {
        std::cerr << "Invalid animation context handle: " << contextHandle << std::endl;
        return 0;
    }
}

// Play the animation
JNIEXPORT void JNICALL
Java_com_campro_v5_NativeLibrary_play(JNIEnv* env, jobject thiz, jlong contextHandle) {
    auto it = g_animationContexts.find(contextHandle);
    if (it != g_animationContexts.end()) {
        it->second->play();
    } else {
        std::cerr << "Invalid animation context handle: " << contextHandle << std::endl;
    }
}

// Pause the animation
JNIEXPORT void JNICALL
Java_com_campro_v5_NativeLibrary_pause(JNIEnv* env, jobject thiz, jlong contextHandle) {
    auto it = g_animationContexts.find(contextHandle);
    if (it != g_animationContexts.end()) {
        it->second->pause();
    } else {
        std::cerr << "Invalid animation context handle: " << contextHandle << std::endl;
    }
}

// Reset the animation
JNIEXPORT void JNICALL
Java_com_campro_v5_NativeLibrary_reset(JNIEnv* env, jobject thiz, jlong contextHandle) {
    auto it = g_animationContexts.find(contextHandle);
    if (it != g_animationContexts.end()) {
        it->second->reset();
    } else {
        std::cerr << "Invalid animation context handle: " << contextHandle << std::endl;
    }
}

// Get the current frame
JNIEXPORT jint JNICALL
Java_com_campro_v5_NativeLibrary_getCurrentFrame(JNIEnv* env, jobject thiz, jlong contextHandle) {
    auto it = g_animationContexts.find(contextHandle);
    if (it != g_animationContexts.end()) {
        return it->second->getCurrentFrame();
    } else {
        std::cerr << "Invalid animation context handle: " << contextHandle << std::endl;
        return 0;
    }
}

// Set the current frame
JNIEXPORT void JNICALL
Java_com_campro_v5_NativeLibrary_setCurrentFrame(JNIEnv* env, jobject thiz, jlong contextHandle, jint frame) {
    auto it = g_animationContexts.find(contextHandle);
    if (it != g_animationContexts.end()) {
        it->second->setCurrentFrame(frame);
    } else {
        std::cerr << "Invalid animation context handle: " << contextHandle << std::endl;
    }
}

} // extern "C"