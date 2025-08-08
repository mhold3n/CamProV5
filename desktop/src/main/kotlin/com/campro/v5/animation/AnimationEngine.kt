package com.campro.v5.animation

import androidx.compose.runtime.Composable
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.DrawScope
import kotlinx.coroutines.flow.StateFlow
import java.io.File

/**
 * Interface for animation engines.
 * This interface defines the common functionality for different types of animations.
 */
interface AnimationEngine {
    /**
     * Get the current animation angle in degrees.
     */
    fun getCurrentAngle(): Float
    
    /**
     * Set the animation angle in degrees.
     * 
     * @param angle The angle in degrees
     */
    fun setAngle(angle: Float)
    
    /**
     * Update the animation parameters.
     * 
     * @param parameters The new parameters
     */
    fun updateParameters(parameters: Map<String, String>)
    
    /**
     * Draw the animation frame.
     * 
     * @param drawScope The draw scope to use for drawing
     * @param canvasWidth The width of the canvas
     * @param canvasHeight The height of the canvas
     * @param scale The scale factor
     * @param offset The offset
     */
    fun drawFrame(
        drawScope: DrawScope,
        canvasWidth: Float,
        canvasHeight: Float,
        scale: Float,
        offset: Offset
    )
    
    /**
     * Get the animation parameters.
     * 
     * @return The animation parameters
     */
    fun getParameters(): Map<String, String>
    
    /**
     * Get the animation type.
     * 
     * @return The animation type
     */
    fun getType(): AnimationType
    
    /**
     * Clean up resources when the engine is no longer needed.
     */
    fun dispose()
}

/**
 * Types of animations.
 */
enum class AnimationType {
    COMPONENT_BASED,
    FEA_BASED
}

/**
 * Factory for creating animation engines.
 */
object AnimationEngineFactory {
    /**
     * Create an animation engine of the specified type.
     * 
     * @param type The type of animation engine to create
     * @param parameters The initial parameters for the animation
     * @return The created animation engine
     */
    fun createEngine(type: AnimationType, parameters: Map<String, String>): AnimationEngine {
        return when (type) {
            AnimationType.COMPONENT_BASED -> ComponentBasedAnimationEngine(parameters)
            AnimationType.FEA_BASED -> FeaBasedAnimationEngine(parameters)
        }
    }
}


/**
 * Animation engine for component-based animation.
 * This engine uses the motion law implementation from the Rust FEA engine.
 */
class ComponentBasedAnimationEngine(private var parameters: Map<String, String>) : AnimationEngine {
    private var currentAngle: Float = 0f
    private val motionLawEngine = MotionLawEngine()
    private var lastDrawnAngle: Float = -1f
    private var cachedComponentPositions: ComponentPositions? = null
    
    init {
        // Initialize the motion law engine with the parameters
        motionLawEngine.updateParameters(parameters)
    }
    
    override fun getCurrentAngle(): Float = currentAngle
    
    override fun setAngle(angle: Float) {
        currentAngle = angle % 360f
        // Clear cached positions when angle changes
        if (Math.abs(currentAngle - lastDrawnAngle) > 0.1f) {
            cachedComponentPositions = null
        }
    }
    
    override fun updateParameters(parameters: Map<String, String>) {
        this.parameters = parameters
        motionLawEngine.updateParameters(parameters)
        // Clear cached positions when parameters change
        cachedComponentPositions = null
    }
    
    override fun drawFrame(
        drawScope: DrawScope,
        canvasWidth: Float,
        canvasHeight: Float,
        scale: Float,
        offset: Offset
    ) {
        // Get component positions from the motion law engine
        // Use cached positions if available and angle hasn't changed significantly
        val componentPositions = if (cachedComponentPositions != null && Math.abs(currentAngle - lastDrawnAngle) < 0.1f) {
            cachedComponentPositions!!
        } else {
            val positions = motionLawEngine.getComponentPositions(currentAngle.toDouble())
            cachedComponentPositions = positions
            lastDrawnAngle = currentAngle
            positions
        }
        
        // Draw the components
        ComponentBasedAnimationRenderer.drawFrame(
            drawScope,
            canvasWidth,
            canvasHeight,
            scale,
            offset,
            currentAngle,
            parameters,
            componentPositions
        )
    }
    
    override fun getParameters(): Map<String, String> = parameters
    
    override fun getType(): AnimationType = AnimationType.COMPONENT_BASED
    
    override fun dispose() {
        motionLawEngine.dispose()
    }
}

/**
 * Animation engine for FEA-based animation.
 * This engine uses the results of the FEA engine to generate the animation.
 */
class FeaBasedAnimationEngine(private var parameters: Map<String, String>) : AnimationEngine {
    private var currentAngle: Float = 0f
    private var feaResults: File? = null
    private var analysisData: AnalysisData? = null
    
    override fun getCurrentAngle(): Float = currentAngle
    
    override fun setAngle(angle: Float) {
        currentAngle = angle % 360f
    }
    
    override fun updateParameters(parameters: Map<String, String>) {
        this.parameters = parameters
    }
    
    /**
     * Set the FEA results file.
     * 
     * @param resultsFile The FEA results file
     */
    fun setFeaResults(resultsFile: File) {
        feaResults = resultsFile
        // Load the FEA results
        analysisData = FeaResultsLoader.loadResults(resultsFile)
    }
    
    override fun drawFrame(
        drawScope: DrawScope,
        canvasWidth: Float,
        canvasHeight: Float,
        scale: Float,
        offset: Offset
    ) {
        // Draw the FEA results
        FeaBasedAnimationRenderer.drawFrame(
            drawScope,
            canvasWidth,
            canvasHeight,
            scale,
            offset,
            currentAngle,
            parameters,
            analysisData
        )
    }
    
    override fun getParameters(): Map<String, String> = parameters
    
    override fun getType(): AnimationType = AnimationType.FEA_BASED
    
    override fun dispose() {
        // Clean up resources
        analysisData = null
    }
}

/**
 * Manager for animation engines.
 * This class provides a centralized way to manage animation engines.
 */
class AnimationManager {
    private var currentEngine: AnimationEngine? = null
    
    /**
     * Set the current animation engine.
     * 
     * @param engine The animation engine to set as current
     */
    fun setCurrentEngine(engine: AnimationEngine) {
        currentEngine?.dispose()
        currentEngine = engine
    }
    
    /**
     * Get the current animation engine.
     * 
     * @return The current animation engine, or null if none is set
     */
    fun getCurrentEngine(): AnimationEngine? = currentEngine
    
    /**
     * Create a new animation engine and set it as current.
     * 
     * @param type The type of animation engine to create
     * @param parameters The initial parameters for the animation
     * @return The created animation engine
     */
    fun createAndSetEngine(type: AnimationType, parameters: Map<String, String>): AnimationEngine {
        val engine = AnimationEngineFactory.createEngine(type, parameters)
        setCurrentEngine(engine)
        return engine
    }
    
    /**
     * Clean up resources when the manager is no longer needed.
     */
    fun dispose() {
        currentEngine?.dispose()
        currentEngine = null
    }
}

// MotionLawEngine is now defined in MotionLawEngine.kt

/**
 * Data class for component positions.
 */
data class ComponentPositions(
    val pistonPosition: Offset,
    val rodPosition: Offset,
    val camPosition: Offset
)

/**
 * Placeholder for the FEA results loader.
 */
object FeaResultsLoader {
    /**
     * Load FEA results from a file.
     * 
     * @param resultsFile The FEA results file
     * @return The loaded analysis data
     */
    fun loadResults(resultsFile: File): AnalysisData {
        // Implementation would load and parse the FEA results
        // For now, return a placeholder
        return AnalysisData(
            displacements = emptyMap(),
            stresses = emptyMap(),
            timeSteps = emptyList()
        )
    }
}

/**
 * Data class for FEA analysis data.
 */
data class AnalysisData(
    val displacements: Map<Int, Offset>,
    val stresses: Map<Int, Float>,
    val timeSteps: List<Float>
)

// Renderer classes are now defined in their own files:
// - CycloidalAnimationRenderer.kt
// - ComponentBasedAnimationRenderer.kt
// - FeaBasedAnimationRenderer.kt