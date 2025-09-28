package com.campro.v5.pipeline

import com.campro.v5.models.OptimizationParameters
import com.campro.v5.models.OptimizationResult
import com.campro.v5.models.MotionLawData
import com.campro.v5.models.GearProfileData
import com.campro.v5.models.FEAAnalysisData
import com.campro.v5.models.ToothProfileData
import com.campro.v5.utils.SimpleJsonUtils
import com.campro.v5.utils.FileUtils
import java.io.File
import java.nio.file.Path
import java.nio.file.Paths
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import org.slf4j.LoggerFactory

/**
 * Bridge between Kotlin UI and Python unified optimization pipeline.
 * 
 * This class handles parameter validation, conversion, result parsing,
 * and error handling for the unified optimization pipeline.
 */
class UnifiedOptimizationBridge {
    
    private val logger = LoggerFactory.getLogger(UnifiedOptimizationBridge::class.java)
    
    companion object {
        private const val PYTHON_SCRIPT_PATH = "../scripts/kotlin_bridge_cli.py"
        private const val DEFAULT_TIMEOUT_SECONDS = 30L
        private const val MAX_RETRIES = 3
    }
    
    /**
     * Run unified optimization pipeline with Kotlin parameters.
     * 
     * @param parameters Optimization parameters from UI
     * @param outputDir Output directory for results
     * @return CompletableFuture with optimization result
     */
    suspend fun runOptimization(
        parameters: OptimizationParameters,
        outputDir: Path
    ): CompletableFuture<OptimizationResult> = withContext(Dispatchers.IO) {
        
        return@withContext CompletableFuture.supplyAsync {
            try {
                logger.info("Starting unified optimization pipeline")
                
                // Validate parameters
                validateParameters(parameters)
                
                // Convert Kotlin parameters to Python format
                val pythonParams = convertParametersToPython(parameters)
                
                // Create temporary files for communication
                val inputFile = createInputFile(pythonParams, outputDir)
                val outputFile = createOutputFile(outputDir)
                
                // Run Python pipeline
                val success = runPythonPipeline(inputFile, outputFile, outputDir)
                
                if (success) {
                    // Parse results
                    val result = parseResults(outputFile)
                    logger.info("Optimization completed successfully")
                    result
                } else {
                    logger.error("Python pipeline execution failed")
                    createErrorResult("Pipeline execution failed")
                }
                
            } catch (e: Exception) {
                logger.error("Optimization failed: ${e.message}", e)
                createErrorResult(e.message ?: "Unknown error")
            }
        }
    }
    
    /**
     * Validate optimization parameters.
     */
    private fun validateParameters(parameters: OptimizationParameters) {
        require(parameters.samplingStepDeg > 0) { "Sampling step must be positive" }
        require(parameters.strokeLengthMm > 0) { "Stroke length must be positive" }
        require(parameters.gearRatio > 0) { "Gear ratio must be positive" }
        require(parameters.rpm > 0) { "RPM must be positive" }
        require(parameters.planetCount > 0) { "Planet count must be positive" }
        require(parameters.rodLength > 0) { "Rod length must be positive" }
        require(parameters.journalRadius > 0) { "Journal radius must be positive" }
        require(parameters.ringThickness > 0) { "Ring thickness must be positive" }
        require(parameters.interferenceBuffer >= 0) { "Interference buffer must be non-negative" }
    }
    
    /**
     * Convert Kotlin parameters to Python format.
     */
    private fun convertParametersToPython(parameters: OptimizationParameters): Map<String, Any> {
        return mapOf(
            "samplingStepDeg" to parameters.samplingStepDeg,
            "ringRotationDeg" to parameters.ringRotationDeg,
            "gearRatio" to parameters.gearRatio,
            "strokeLengthMm" to parameters.strokeLengthMm,
            "rodLength" to parameters.rodLength,
            "journalRadius" to parameters.journalRadius,
            "interferenceBuffer" to parameters.interferenceBuffer,
            "ringThickness" to parameters.ringThickness,
            "rpm" to parameters.rpm,
            "planetCount" to parameters.planetCount,
            "carrierOffsetDeg" to parameters.carrierOffsetDeg,
            "rampBeforeTdcDeg" to parameters.rampBeforeTdcDeg,
            "rampAfterTdcDeg" to parameters.rampAfterTdcDeg,
            "dwellTdcDeg" to parameters.dwellTdcDeg,
            "rampBeforeBdcDeg" to parameters.rampBeforeBdcDeg,
            "rampAfterBdcDeg" to parameters.rampAfterBdcDeg,
            "dwellBdcDeg" to parameters.dwellBdcDeg,
            "constantVelocityTdcDeg" to parameters.constantVelocityTdcDeg,
            "constantVelocityBdcDeg" to parameters.constantVelocityBdcDeg,
            // Add additional parameters that might be needed
            "planetRadiusBaseFactor" to 0.2,
            "planetRadiusVariationFactor" to 0.1,
            "sunRadiusBaseFactor" to 0.15,
            "sunRadiusVariationFactor" to 0.05,
            "strokeAchievableFactor" to 0.9,
            "clearanceSafetyMargin" to 0.2,
            "adjustmentSplitFactor" to 0.6
        )
    }
    
    /**
     * Create input parameter file for Python pipeline.
     */
    private fun createInputFile(parameters: Map<String, Any>, outputDir: Path): Path {
        val inputFile = outputDir.resolve("input_parameters.json")
        SimpleJsonUtils.writeJsonFile(parameters, inputFile)
        return inputFile
    }
    
    /**
     * Create output file path for Python pipeline results.
     */
    private fun createOutputFile(outputDir: Path): Path {
        return outputDir.resolve("optimization_results.json")
    }
    
    /**
     * Run Python pipeline with retry logic.
     */
    private fun runPythonPipeline(
        inputFile: Path,
        outputFile: Path,
        outputDir: Path
    ): Boolean {
        var retryCount = 0
        var lastException: Exception? = null
        
        while (retryCount < MAX_RETRIES) {
            try {
                val command = buildPythonCommand(inputFile, outputFile, outputDir)
                logger.debug("Running Python command: ${command.joinToString(" ")}")
                
                val process = ProcessBuilder(command)
                    .directory(File(System.getProperty("user.dir")))
                    .start()
                
                val success = process.waitFor(DEFAULT_TIMEOUT_SECONDS, TimeUnit.SECONDS)
                
                if (success && process.exitValue() == 0) {
                    logger.info("Python pipeline completed successfully")
                    return true
                } else {
                    val errorOutput = process.errorStream.bufferedReader().readText()
                    logger.warn("Python pipeline failed (attempt ${retryCount + 1}): $errorOutput")
                    lastException = RuntimeException("Pipeline failed: $errorOutput")
                }
                
            } catch (e: Exception) {
                logger.warn("Python pipeline exception (attempt ${retryCount + 1}): ${e.message}")
                lastException = e
            }
            
            retryCount++
            if (retryCount < MAX_RETRIES) {
                Thread.sleep(1000) // Wait 1 second before retry
            }
        }
        
        logger.error("Python pipeline failed after $MAX_RETRIES attempts", lastException)
        return false
    }
    
    /**
     * Build Python command for pipeline execution.
     */
    private fun buildPythonCommand(
        inputFile: Path,
        outputFile: Path,
        outputDir: Path
    ): List<String> {
        return listOf(
            "python", PYTHON_SCRIPT_PATH,
            "--input", inputFile.toString(),
            "--output", outputFile.toString(),
            "--output-dir", outputDir.toString()
        )
    }
    
    /**
     * Parse optimization results from Python output.
     */
    private fun parseResults(outputFile: Path): OptimizationResult {
        try {
            val resultData = SimpleJsonUtils.readJsonFile(outputFile)
            
            return OptimizationResult(
                status = resultData["status"] as String,
                motionLaw = parseMotionLaw(resultData["motion_law"] as Map<String, Any>),
                optimalProfiles = parseGearProfiles(resultData["optimal_profiles"] as Map<String, Any>),
                toothProfiles = parseToothProfiles(resultData["tooth_profiles"] as Map<String, Any>),
                feaAnalysis = parseFEAAnalysis(resultData["fea"] as Map<String, Any>),
                executionTime = resultData["execution_time"] as? Double ?: 0.0,
                error = resultData["error"] as? String
            )
            
        } catch (e: Exception) {
            logger.error("Failed to parse results: ${e.message}", e)
            return createErrorResult("Failed to parse results: ${e.message}")
        }
    }
    
    /**
     * Parse motion law data from Python result.
     */
    private fun parseMotionLaw(motionLawData: Map<String, Any>): MotionLawData {
        return MotionLawData(
            thetaDeg = (motionLawData["theta_deg"] as List<Double>).toDoubleArray(),
            displacement = (motionLawData["displacement"] as List<Double>).toDoubleArray(),
            velocity = (motionLawData["velocity"] as List<Double>).toDoubleArray(),
            acceleration = (motionLawData["acceleration"] as List<Double>).toDoubleArray()
        )
    }
    
    /**
     * Parse gear profile data from Python result.
     */
    private fun parseGearProfiles(profilesData: Map<String, Any>): GearProfileData {
        val optimalProfiles = profilesData["optimal_profiles"] as Map<String, Any>
        
        return GearProfileData(
            rSun = (optimalProfiles["r_sun"] as List<Double>).toDoubleArray(),
            rPlanet = (optimalProfiles["r_planet"] as List<Double>).toDoubleArray(),
            rRingInner = (optimalProfiles["r_ring_inner"] as List<Double>).toDoubleArray(),
            gearRatio = optimalProfiles["gear_ratio"] as Double,
            optimalMethod = profilesData["optimal_solution"] as String,
            efficiencyAnalysis = profilesData["efficiency_analysis"] as? Map<String, Any>
        )
    }
    
    /**
     * Parse tooth profile data from Python result.
     */
    private fun parseToothProfiles(toothData: Map<String, Any>): ToothProfileData {
        return ToothProfileData(
            sunTeeth = parseToothArray(toothData["sun_teeth"]),
            planetTeeth = parseToothArray(toothData["planet_teeth"]),
            ringTeeth = parseToothArray(toothData["ring_teeth"])
        )
    }
    
    /**
     * Parse tooth array data.
     */
    private fun parseToothArray(toothData: Any?): Array<DoubleArray>? {
        return if (toothData is List<*>) {
            toothData.map { tooth ->
                if (tooth is List<*>) {
                    tooth.map { it as Double }.toDoubleArray()
                } else {
                    doubleArrayOf()
                }
            }.toTypedArray()
        } else {
            null
        }
    }
    
    /**
     * Parse FEA analysis data from Python result.
     */
    private fun parseFEAAnalysis(feaData: Map<String, Any>): FEAAnalysisData {
        val analysisSummary = feaData["analysis_summary"] as? Map<String, Any> ?: emptyMap()
        
        return FEAAnalysisData(
            maxStress = analysisSummary["max_stress"] as? Double ?: 0.0,
            naturalFrequencies = (analysisSummary["natural_frequencies"] as? List<Double>)?.toDoubleArray() ?: doubleArrayOf(),
            fatigueLife = analysisSummary["fatigue_life"] as? Double ?: 0.0,
            modeShapes = (feaData["mode_shapes"] as? List<String>)?.toTypedArray() ?: emptyArray(),
            recommendations = (feaData["recommendations"] as? List<String>)?.toTypedArray() ?: emptyArray()
        )
    }
    
    /**
     * Create error result for failed optimization.
     */
    private fun createErrorResult(errorMessage: String): OptimizationResult {
        return OptimizationResult(
            status = "failed",
            motionLaw = MotionLawData(doubleArrayOf(), doubleArrayOf(), doubleArrayOf(), doubleArrayOf()),
            optimalProfiles = GearProfileData(doubleArrayOf(), doubleArrayOf(), doubleArrayOf(), 0.0, "none", null),
            toothProfiles = ToothProfileData(null, null, null),
            feaAnalysis = FEAAnalysisData(0.0, doubleArrayOf(), 0.0, emptyArray(), emptyArray()),
            executionTime = 0.0,
            error = errorMessage
        )
    }
    
    /**
     * Check if Python pipeline is available.
     */
    fun isPipelineAvailable(): Boolean {
        return try {
            val command = listOf("python", "-c", "import campro.pipeline.unified_optimizer; print('OK')")
            val process = ProcessBuilder(command).start()
            val success = process.waitFor(5, TimeUnit.SECONDS)
            success && process.exitValue() == 0
        } catch (e: Exception) {
            logger.warn("Python pipeline not available: ${e.message}")
            false
        }
    }
    
    /**
     * Get pipeline version information.
     */
    fun getPipelineVersion(): String {
        return try {
            val command = listOf("python", "-c", "import campro; print(campro.__version__)")
            val process = ProcessBuilder(command).start()
            val success = process.waitFor(5, TimeUnit.SECONDS)
            
            if (success && process.exitValue() == 0) {
                process.inputStream.bufferedReader().readText().trim()
            } else {
                "unknown"
            }
        } catch (e: Exception) {
            logger.warn("Could not get pipeline version: ${e.message}")
            "unknown"
        }
    }
}
