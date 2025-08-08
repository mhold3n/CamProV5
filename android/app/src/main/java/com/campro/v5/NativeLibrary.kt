package com.campro.v5

/**
 * Native library interface for CamProV5
 * Provides JNI bindings to the C++ animation engine
 */
object NativeLibrary {
    init {
        try {
            System.loadLibrary("campro-animation")
        } catch (e: UnsatisfiedLinkError) {
            // Log error but don't crash - we'll handle missing library gracefully
            android.util.Log.e("NativeLibrary", "Failed to load native library: ${e.message}")
        }
    }
    
    /**
     * Initialize the native library
     * This should be called once when the application starts
     */
    external fun initialize()
    
    /**
     * Create an animation context
     * @param width Width of the animation surface
     * @param height Height of the animation surface
     * @return Handle to the animation context
     */
    external fun createAnimationContext(width: Int, height: Int): Long
    
    /**
     * Destroy an animation context
     * @param contextHandle Handle to the animation context
     */
    external fun destroyAnimationContext(contextHandle: Long)
    
    /**
     * Update animation data
     * @param contextHandle Handle to the animation context
     * @param baseCamTheta Array of theta values for the base cam profile
     * @param baseCamR Array of radius values for the base cam profile
     * @param baseCamX Array of X coordinates for the base cam profile
     * @param baseCamY Array of Y coordinates for the base cam profile
     * @param phiArray Array of phi values for animation
     * @param centerRArray Array of center radius values for animation
     * @param n Cam profile parameter
     * @param stroke Stroke length
     * @param tdcOffset Top dead center offset
     * @param innerEnvelopeTheta Array of theta values for inner envelope
     * @param innerEnvelopeR Array of radius values for inner envelope
     * @param outerBoundaryRadius Radius of outer boundary
     * @param rodLength Length of connecting rod
     * @param cycleRatio Ratio of cycle
     */
    external fun updateAnimationData(
        contextHandle: Long,
        baseCamTheta: FloatArray,
        baseCamR: FloatArray,
        baseCamX: FloatArray,
        baseCamY: FloatArray,
        phiArray: FloatArray,
        centerRArray: FloatArray,
        n: Float,
        stroke: Float,
        tdcOffset: Float,
        innerEnvelopeTheta: FloatArray,
        innerEnvelopeR: FloatArray,
        outerBoundaryRadius: Float,
        rodLength: Float,
        cycleRatio: Float
    )
    
    /**
     * Render a frame of the animation
     * @param contextHandle Handle to the animation context
     */
    external fun renderFrame(contextHandle: Long)
    
    /**
     * Get the OpenGL texture ID for the animation
     * @param contextHandle Handle to the animation context
     * @return OpenGL texture ID
     */
    external fun getTextureId(contextHandle: Long): Int
    
    /**
     * Start playing the animation
     * @param contextHandle Handle to the animation context
     */
    external fun play(contextHandle: Long)
    
    /**
     * Pause the animation
     * @param contextHandle Handle to the animation context
     */
    external fun pause(contextHandle: Long)
    
    /**
     * Reset the animation to the first frame
     * @param contextHandle Handle to the animation context
     */
    external fun reset(contextHandle: Long)
    
    /**
     * Get the current frame of the animation
     * @param contextHandle Handle to the animation context
     * @return Current frame index
     */
    external fun getCurrentFrame(contextHandle: Long): Int
    
    /**
     * Set the current frame of the animation
     * @param contextHandle Handle to the animation context
     * @param frame Frame index
     */
    external fun setCurrentFrame(contextHandle: Long, frame: Int)
}