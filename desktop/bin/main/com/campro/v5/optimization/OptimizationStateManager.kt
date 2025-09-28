package com.campro.v5.optimization

import com.campro.v5.models.OptimizationParameters
import com.campro.v5.models.OptimizationResult
import com.campro.v5.pipeline.UnifiedOptimizationBridge
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.nio.file.Path
import org.slf4j.LoggerFactory

/**
 * State manager for optimization operations.
 * 
 * This class manages the state of optimization operations, including
 * running, completed, and failed states, with reactive state updates
 * using StateFlow.
 */
class OptimizationStateManager(
    private val bridge: UnifiedOptimizationBridge
) {
    private val logger = LoggerFactory.getLogger(OptimizationStateManager::class.java)
    
    private val _optimizationState = MutableStateFlow<OptimizationState>(OptimizationState.Idle)
    val optimizationState: StateFlow<OptimizationState> = _optimizationState.asStateFlow()
    
    private var currentJob: Job? = null
    
    /**
     * Run optimization with given parameters.
     * 
     * @param parameters Optimization parameters
     * @param outputDir Output directory for results
     */
    suspend fun runOptimization(
        parameters: OptimizationParameters,
        outputDir: Path
    ) {
        // Cancel any existing optimization
        currentJob?.cancel()
        
        currentJob = CoroutineScope(Dispatchers.Main).launch {
            try {
                logger.info("Starting optimization with parameters: $parameters")
                _optimizationState.value = OptimizationState.Running(0.0)
                
                // Run optimization in background
                val result = withContext(Dispatchers.IO) {
                    bridge.runOptimization(parameters, outputDir).get()
                }
                
                _optimizationState.value = OptimizationState.Completed(result)
                logger.info("Optimization completed successfully")
                
            } catch (e: CancellationException) {
                logger.info("Optimization was cancelled")
                _optimizationState.value = OptimizationState.Idle
                throw e
            } catch (e: Exception) {
                logger.error("Optimization failed", e)
                _optimizationState.value = OptimizationState.Failed(e)
            }
        }
        
        currentJob?.join()
    }
    
    /**
     * Cancel current optimization.
     */
    fun cancelOptimization() {
        currentJob?.cancel()
        _optimizationState.value = OptimizationState.Idle
        logger.info("Optimization cancelled by user")
    }
    
    /**
     * Reset state to idle.
     */
    fun resetState() {
        currentJob?.cancel()
        _optimizationState.value = OptimizationState.Idle
    }
    
    /**
     * Check if optimization is currently running.
     */
    fun isRunning(): Boolean {
        return _optimizationState.value is OptimizationState.Running
    }
    
    /**
     * Get current state.
     */
    fun getCurrentState(): OptimizationState {
        return _optimizationState.value
    }
}

/**
 * Sealed class representing optimization states.
 */
sealed class OptimizationState {
    object Idle : OptimizationState()
    data class Running(val progress: Double) : OptimizationState()
    data class Completed(val result: OptimizationResult) : OptimizationState()
    data class Failed(val error: Throwable) : OptimizationState()
}