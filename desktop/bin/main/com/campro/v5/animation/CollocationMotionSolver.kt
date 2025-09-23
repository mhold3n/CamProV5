package com.campro.v5.animation

import com.campro.v5.animation.collocation.*
import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.MotionLawSamples
import com.campro.v5.data.litvin.MotionLawSample
import org.slf4j.LoggerFactory
import com.google.gson.Gson
import com.google.gson.JsonParser
import java.io.File
import kotlin.io.path.createTempDirectory
import kotlin.math.*
import com.campro.v5.config.FeatureFlags

/**
 * Collocation-based motion law solver using NLP optimization.
 * 
 * This solver treats profile generation as a global algebraic system,
 * enforcing dynamics and smoothness via differentiation matrices and
 * solving with a sparse linear solver.
 */
object CollocationMotionSolver {
    private val logger = LoggerFactory.getLogger(CollocationMotionSolver::class.java)
    
    // Cache discretization setups by node count for performance
    private val discretizationCache = mutableMapOf<Int, CollocationDiscretization>()

    /**
     * Solve motion law using collocation method.
     * 
     * @param params User parameters defining constraints and requirements
     * @return MotionLawSamples with uniform grid matching samplingStepDeg
     */
    fun solve(params: LitvinUserParams): MotionLawSamples {
        logger.info("Starting collocation solver with stepDeg=${params.samplingStepDeg}")
        
        // Check feature flags
        if (!FeatureFlags.Collocation.isEnabled()) {
            logger.warn("Collocation solver disabled by feature flag, falling back to piecewise")
            throw UnsupportedOperationException(
                "Collocation solver is disabled by feature flags. " +
                "Enable with collocation.enabled=true in ~/.campro/feature_flags.properties"
            )
        }
        
        if (FeatureFlags.Collocation.isForceFallback()) {
            logger.warn("Collocation forced to fallback by feature flag")
            throw UnsupportedOperationException(
                "Collocation solver is set to force fallback. " +
                "Disable with collocation.force_fallback=false in feature flags."
            )
        }
        
        try {
            // Phase 1: Set up collocation discretization
            val nodeCount = determineOptimalNodeCount(params)
            val discretization = getOrCreateDiscretization(nodeCount)
            logger.debug("Using ${discretization.nodeType} discretization with $nodeCount nodes")
            
            // Phase 2: Generate constraints from UI parameters
            val constraintSystem = CollocationConstraints(params, discretization)
            val constraints = constraintSystem.generateConstraints()
            logger.debug("Generated ${constraints.size} constraints")
            
            // Phase 3: Set up and solve NLP (placeholder for now)
            val solution = solveNLP(discretization, constraints, params)
            
            // Phase 4: Resample to uniform grid for MotionLawSamples
            val uniformSample = discretization.resampleToUniformGrid(solution, params.samplingStepDeg)
            
            // Phase 5: Convert to MotionLawSamples format
            return convertToMotionLawSamples(uniformSample)
            
        } catch (e: Exception) {
            logger.error("Collocation solver failed: ${e.message}", e)
            throw UnsupportedOperationException(
                "Collocation solver encountered an error: ${e.message}. " +
                "This feature is still in development. Please use Piecewise mode for now.",
                e
            )
        }
    }
    
    /**
     * Validate that collocation solver is available and properly configured.
     * 
     * @return true if solver is ready to use, false otherwise
     */
    fun isAvailable(): Boolean {
        // Check feature flags first
        if (!FeatureFlags.Collocation.isEnabled() || FeatureFlags.Collocation.isForceFallback()) {
            return false
        }
        
        // Test basic discretization creation
        return try {
            val testDiscretization = CollocationDiscretization(8, CollocationDiscretization.NodeType.LGL)
            testDiscretization.nodes.isNotEmpty()
        } catch (e: Exception) {
            logger.warn("Collocation discretization creation failed: ${e.message}")
            false
        }
    }
    
    /**
     * Determine optimal number of collocation nodes based on problem parameters.
     * 
     * This adaptive algorithm balances accuracy and computational cost by analyzing
     * the complexity of the motion profile requirements.
     */
    private fun determineOptimalNodeCount(params: LitvinUserParams): Int {
        // Validate input parameters
        require(params.samplingStepDeg > 0.0) { "Sampling step must be positive" }
        require(params.strokeLengthMm > 0.0) { "Stroke length must be positive" }
        
        // Base node count on complexity of the motion profile
        var baseNodes = 12 // Minimum for reasonable accuracy
        
        // Add nodes for dwell regions (need fine resolution for smooth transitions)
        if (params.dwellTdcDeg > 0.0) {
            baseNodes += minOf(6, (params.dwellTdcDeg / 10.0).toInt() + 2) // Scale with dwell size
        }
        if (params.dwellBdcDeg > 0.0) {
            baseNodes += minOf(6, (params.dwellBdcDeg / 10.0).toInt() + 2)
        }
        
        // Add nodes for ramp regions (complex acceleration profiles need resolution)
        val totalRampDeg = params.rampAfterTdcDeg + params.rampBeforeBdcDeg + 
                          params.rampAfterBdcDeg + params.rampBeforeTdcDeg
        baseNodes += max(0, (totalRampDeg / 15.0).toInt()) // 1 node per 15 degrees of ramp
        
        // Consider high RPM cases (need more nodes for stability)
        if (params.rpm > 3000.0) {
            baseNodes += 4
        }
        
        // Ensure even number for symmetry and cap at reasonable maximum
        val optimalNodes = baseNodes + (baseNodes % 2)
        val finalNodes = optimalNodes.coerceIn(8, 48)
        
        logger.debug("Node count adaptation: base=$baseNodes, optimal=$optimalNodes, final=$finalNodes")
        return finalNodes
    }
    
    /**
     * Get or create discretization setup, using cache for performance.
     * 
     * This cache dramatically improves performance for repeated solves with
     * similar complexity parameters.
     */
    private fun getOrCreateDiscretization(nodeCount: Int): CollocationDiscretization {
        require(nodeCount >= 3) { "Node count must be at least 3, got $nodeCount" }
        require(nodeCount <= 64) { "Node count too large for practical computation: $nodeCount" }
        
        val startTime = System.currentTimeMillis()
        val discretization = discretizationCache.getOrPut(nodeCount) {
            logger.debug("Creating new discretization with $nodeCount nodes")
            
            // Choose node type based on requirements (LGL for accuracy, UNIFORM for debugging)
            val nodeType = if (FeatureFlags.isEnabled("debug.use_uniform_nodes")) {
                CollocationDiscretization.NodeType.UNIFORM
            } else {
                CollocationDiscretization.NodeType.LGL
            }
            
            CollocationDiscretization(nodeCount, nodeType)
        }
        
        val cacheHit = System.currentTimeMillis() - startTime < 5 // Fast retrieval indicates cache hit
        logger.debug("Discretization ${if (cacheHit) "retrieved from cache" else "created"} in ${System.currentTimeMillis() - startTime}ms")
        
        return discretization
    }
    
    /**
     * Solve the NLP optimization problem using Python CasADi + IPOPT solver.
     * 
     * This integrates with the Python collocation solver through file-based communication.
     */
    private fun solveNLP(
        discretization: CollocationDiscretization,
        constraints: List<MotionConstraint>,
        params: LitvinUserParams
    ): CollocationState {
        logger.info("Solving NLP with ${discretization.nodeCount} nodes and ${constraints.size} constraints")
        
        try {
            // Use Python CasADi solver if available
            val pythonSolution = solvePythonCollocation(discretization, params)
            if (pythonSolution != null) {
                return pythonSolution
            }
        } catch (e: Exception) {
            logger.warn("Python CasADi solver failed, falling back to placeholder: ${e.message}")
        }
        
        // Fallback: Generate a simple test motion that satisfies basic constraints
        logger.info("Using placeholder sinusoidal solution")
        val nodes = discretization.nodes
        val values = DoubleArray(nodes.size) { i ->
            val theta = nodes[i]
            // Simple sinusoidal motion for testing
            val amplitude = params.strokeLengthMm / 2.0
            amplitude * (1.0 - cos(theta))
        }
        
        // Compute derivatives using discretization system
        return discretization.computeDerivatives(values)
    }
    
    /**
     * Solve using Python CasADi + IPOPT solver through file-based interface.
     */
    private fun solvePythonCollocation(
        discretization: CollocationDiscretization,
        params: LitvinUserParams
    ): CollocationState? {
        logger.debug("Attempting Python CasADi solver")
        
        try {
            // Create temporary files for communication
            val tempDir = createTempDirectory("collocation_solver").toFile()
            val inputFile = File(tempDir, "input_params.json")
            val outputFile = File(tempDir, "collocation_solution.json")
            val logFile = File(tempDir, "solver.log")
            
            // Prepare input parameters for Python solver
            val inputParamsMap = mapOf(
                "strokeLengthMm" to params.strokeLengthMm,
                "samplingStepDeg" to params.samplingStepDeg,
                "dwellTdcDeg" to params.dwellTdcDeg,
                "dwellBdcDeg" to params.dwellBdcDeg,
                "rampAfterTdcDeg" to params.rampAfterTdcDeg,
                "rampBeforeBdcDeg" to params.rampBeforeBdcDeg,
                "rampAfterBdcDeg" to params.rampAfterBdcDeg,
                "rampBeforeTdcDeg" to params.rampBeforeTdcDeg,
                "upFraction" to params.upFraction,
                "rpm" to params.rpm,
                "rampProfile" to params.rampProfile.name,
                "collocation_params" to mapOf(
                    "node_count" to discretization.nodeCount,
                    "node_type" to discretization.nodeType.name,
                    "max_iterations" to 1000,
                    "tolerance" to 1e-8,
                    "constraint_tolerance" to 1e-6,
                    "smoothness_weight" to 1e-3
                )
            )
            val inputParamsJson = Gson().toJson(inputParamsMap)
            
            // Write input file
            inputFile.writeText(inputParamsJson)
            
            // Execute Python solver
            val success = executePythonSolver(inputFile, outputFile, logFile)
            
            if (success && outputFile.exists()) {
                // Parse solution
                val solutionText = outputFile.readText()
                val solutionJson = JsonParser.parseString(solutionText).asJsonObject
                val solution = parseCollocationSolution(solutionJson, discretization)
                
                // Clean up temporary files
                tempDir.deleteRecursively()
                
                return solution
            } else {
                logger.warn("Python solver execution failed or no output produced")
                if (logFile.exists()) {
                    logger.debug("Python solver log: ${logFile.readText()}")
                }
            }
            
        } catch (e: Exception) {
            logger.error("Error in Python CasADi solver integration: ${e.message}", e)
        }
        
        return null
    }
    
    /**
     * Execute the Python collocation solver script.
     */
    private fun executePythonSolver(inputFile: File, outputFile: File, logFile: File): Boolean {
        return try {
            val pythonScript = findPythonSolverScript()
            if (pythonScript == null) {
                logger.warn("Python solver script not found")
                return false
            }
            
            val command = listOf(
                "python3", pythonScript.absolutePath,
                "--input", inputFile.absolutePath,
                "--output", outputFile.absolutePath,
                "--log", logFile.absolutePath
            )
            
            logger.debug("Executing: ${command.joinToString(" ")}")
            
            val process = ProcessBuilder(command)
                .redirectErrorStream(true)
                .start()
            
            val exitCode = process.waitFor()
            val output = process.inputStream.bufferedReader().readText()
            
            if (exitCode != 0) {
                logger.warn("Python solver exited with code $exitCode: $output")
                return false
            }
            
            logger.debug("Python solver completed successfully")
            true
            
        } catch (e: Exception) {
            logger.error("Failed to execute Python solver: ${e.message}", e)
            false
        }
    }
    
    /**
     * Find the Python collocation solver script.
     */
    private fun findPythonSolverScript(): File? {
        // Look for the solver script in the campro module
        val possiblePaths = listOf(
            "campro/scripts/collocation_solver_cli.py",
            "../campro/scripts/collocation_solver_cli.py",
            "../../campro/scripts/collocation_solver_cli.py"
        )
        
        for (path in possiblePaths) {
            val file = File(path)
            if (file.exists()) {
                return file
            }
        }
        
        logger.warn("Could not find Python collocation solver script")
        return null
    }
    
    /**
     * Parse collocation solution from JSON output.
     */
    private fun parseCollocationSolution(
        solutionJson: com.google.gson.JsonObject,
        discretization: CollocationDiscretization
    ): CollocationState {
        val success = solutionJson.get("success")?.asBoolean ?: false
        
        if (!success) {
            throw RuntimeException("Python solver reported failure")
        }
        
        // Extract solution arrays
        val thetaArray = solutionJson.getAsJsonArray("theta_grid")?.map { 
            it.asDouble 
        }?.toDoubleArray() ?: doubleArrayOf()
        
        val positionArray = solutionJson.getAsJsonArray("position")?.map { 
            it.asDouble 
        }?.toDoubleArray() ?: doubleArrayOf()
        
        val velocityArray = solutionJson.getAsJsonArray("velocity")?.map { 
            it.asDouble 
        }?.toDoubleArray() ?: doubleArrayOf()
        
        val accelerationArray = solutionJson.getAsJsonArray("acceleration")?.map { 
            it.asDouble 
        }?.toDoubleArray() ?: doubleArrayOf()
        
        // Validate solution dimensions
        if (positionArray.size != discretization.nodeCount) {
            throw RuntimeException("Solution dimension mismatch: expected ${discretization.nodeCount}, got ${positionArray.size}")
        }
        
        return CollocationState(
            nodes = thetaArray,
            values = positionArray,
            firstDerivative = velocityArray,
            secondDerivative = accelerationArray
        )
    }
    
    /**
     * Convert uniform grid sample to MotionLawSamples format.
     */
    private fun convertToMotionLawSamples(uniformSample: UniformGridSample): MotionLawSamples {
        val samples = mutableListOf<MotionLawSample>()
        
        for (i in uniformSample.nodes.indices) {
            val thetaDeg = uniformSample.nodes[i] * 180.0 / PI
            val sample = MotionLawSample(
                thetaDeg = thetaDeg,
                xMm = uniformSample.values[i],
                vMmPerOmega = uniformSample.firstDerivative[i],
                aMmPerOmega2 = uniformSample.secondDerivative[i]
            )
            samples.add(sample)
        }
        
        return MotionLawSamples(
            stepDeg = uniformSample.stepDeg,
            samples = samples
        )
    }
    
    /**
     * Clear discretization cache (for testing or memory management).
     */
    fun clearCache() {
        logger.debug("Clearing discretization cache (${discretizationCache.size} entries)")
        discretizationCache.clear()
    }
    
    /**
     * Get cache statistics for performance monitoring.
     */
    fun getCacheStats(): Map<String, Any> {
        return mapOf(
            "size" to discretizationCache.size,
            "nodeCountsCached" to discretizationCache.keys.sorted(),
            "totalNodes" to discretizationCache.values.sumOf { it.nodeCount },
            "nodeTypes" to discretizationCache.values.map { it.nodeType.name }.distinct().sorted()
        )
    }
    
    /**
     * Get information about current solver state.
     */
    fun getSolverInfo(): String {
        return buildString {
            appendLine("CollocationMotionSolver Status:")
            appendLine("  Available: ${isAvailable()}")
            appendLine("  Feature flags:")
            appendLine("    Enabled: ${FeatureFlags.Collocation.isEnabled()}")
            appendLine("    Force fallback: ${FeatureFlags.Collocation.isForceFallback()}")
            appendLine("    Python bridge: ${FeatureFlags.Collocation.isPythonBridgeEnabled()}")
            appendLine("    Matrix caching: ${FeatureFlags.Advanced.isMatrixCachingEnabled()}")
            appendLine("  Cached discretizations: ${discretizationCache.size}")
            discretizationCache.forEach { (nodes, disc) ->
                appendLine("    $nodes nodes: ${disc.nodeType} (${disc.nodes.size} actual nodes)")
            }
            
            if (discretizationCache.isEmpty()) {
                appendLine("    (No discretizations cached yet)")
            }
        }
    }
}
