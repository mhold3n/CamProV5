package com.campro.v5.animation

import androidx.compose.ui.geometry.Offset
import com.campro.v5.emitError
import com.campro.v5.fea.DataTransfer
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.roundToInt
import com.campro.v5.data.litvin.validate
import com.campro.v5.data.litvin.toJniArgs
import com.campro.v5.data.litvin.litvinParamsFromMap
import com.campro.v5.data.litvin.jniArgsToMap
import org.slf4j.LoggerFactory
import com.campro.v5.SessionInfo

/**
 * Engine for interfacing with the Rust motion law implementation.
 * This class provides a high-level interface to the Rust motion law implementation
 * through JNI.
 */
object PerfDiag {
    @Volatile var lastLitvinDiagnostics: com.campro.v5.data.litvin.DiagnosticsDTO? = null
    @Volatile var fps: Double = 0.0
    @Volatile var accelMaxAbs: Double? = null
    @Volatile var jerkMaxAbs: Double? = null
}

class MotionLawEngine {
    // Add this property to store parameters
    private var parameters: Map<String, String> = mapOf()
    private var warnedLitvinFallback: Boolean = false

    // Litvin integration state (Phase 3)
    private var litvinId: Long = 0
    private var litvinCurves: com.campro.v5.data.litvin.PitchCurvesDTO? = null
    private var litvinTables: com.campro.v5.data.litvin.LitvinTablesDTO? = null
    private var lastLitvinSignature: String? = null
    // Phase 1a/1b Kotlin-side cache
    private var motionSamples: com.campro.v5.data.litvin.MotionLawSamples? = null
    private var transmission: com.campro.v5.data.litvin.TransmissionAndPitch? = null

    fun isLitvinActive(): Boolean = litvinTables != null

    fun getLitvinCurves(): com.campro.v5.data.litvin.PitchCurvesDTO? = litvinCurves
    fun getLitvinTables(): com.campro.v5.data.litvin.LitvinTablesDTO? = litvinTables
    // Phase 1a/1b UI previews getters
    fun getMotionLawSamples(): com.campro.v5.data.litvin.MotionLawSamples? = motionSamples
    fun getTransmissionPreview(): com.campro.v5.data.litvin.TransmissionAndPitch? = transmission

    /**
     * Export the last generated motion-law samples to a JSON file (if available).
     */
    fun exportMotionLawToJson(targetFile: java.io.File) {
        motionSamples?.let { com.campro.v5.data.litvin.MotionLawSerialization.writeToFile(targetFile, it) }
    }

    data class LitvinFrameState(
        val centerX: List<Double>,
        val centerY: List<Double>,
        val spinPsiDeg: List<Double>,
        val journalX: List<Double>,
        val journalY: List<Double>,
        val pistonS: List<Double>
    )

    fun getLitvinFrameState(angleDeg: Double): LitvinFrameState? {
        val tables = litvinTables ?: return null
        val alphas = tables.alphaDeg
        if (alphas.isEmpty()) return null
        val step = if (alphas.size > 1) alphas[1] - alphas[0] else 1.0
        var idx = if (step > 0) ((angleDeg / step).roundToInt() % alphas.size + alphas.size) % alphas.size else 0
        if (idx < 0 || idx >= alphas.size) idx = (alphas.size - 1).coerceAtLeast(0)
        val cx = ArrayList<Double>(tables.planets.size)
        val cy = ArrayList<Double>(tables.planets.size)
        val spin = ArrayList<Double>(tables.planets.size)
        val jx = ArrayList<Double>(tables.planets.size)
        val jy = ArrayList<Double>(tables.planets.size)
        val ps = ArrayList<Double>(tables.planets.size)
        for (p in tables.planets) {
            cx.add(p.centerX[idx])
            cy.add(p.centerY[idx])
            spin.add(p.spinPsiDeg[idx])
            jx.add(p.journalX[idx])
            jy.add(p.journalY[idx])
            ps.add(p.pistonS[idx])
        }
        return LitvinFrameState(cx, cy, spin, jx, jy, ps)
    }
    
    companion object {
        private val logger = LoggerFactory.getLogger(MotionLawEngine::class.java)
        // Flag to track whether the native library is available
        private var nativeLibraryAvailable = false
        
        // Load the native library
        init {
            try {
                var loaded = false
                val attempted = mutableListOf<String>()

                fun tryLoadFromDir(dir: String?, names: List<String>): Boolean {
                    if (dir.isNullOrBlank()) return false
                    val base = java.nio.file.Path.of(dir)
                    if (!java.nio.file.Files.isDirectory(base)) return false
                    var ok = false
                    for (n in names) {
                        val p = base.resolve(System.mapLibraryName(n))
                        attempted += p.toString()
                        if (!java.nio.file.Files.exists(p)) continue
                        try { System.load(p.toString()); ok = true } catch (_: Throwable) {}
                    }
                    return ok
                }

                val dllBaseNames = listOf("campro_motion", "campro_fea", "fea_engine")

                // 1) FEA_ENGINE_LIB_DIR
                loaded = loaded || tryLoadFromDir(System.getenv("FEA_ENGINE_LIB_DIR"), dllBaseNames)

                // 2) System.loadLibrary by base name (in dependency order)
                if (!loaded) {
                    for (n in dllBaseNames) { try { System.loadLibrary(n); loaded = true } catch (_: UnsatisfiedLinkError) {} }
                }

                // 3) Classpath resource dir (when running from build/resources)
                if (!loaded) {
                    val res = MotionLawEngine::class.java.classLoader.getResource("native/${getOsName()}/${getOsArch()}")
                    if (res != null && res.protocol == "file") {
                        loaded = loaded || tryLoadFromDir(java.nio.file.Paths.get(res.toURI()).toString(), dllBaseNames)
                    }
                }

                // 4) Rust target directories (useful during dev/CI)
                if (!loaded) loaded = loaded || tryLoadFromDir(java.nio.file.Paths.get("CamProV5","camprofw","rust","fea-engine","target","debug").toString(), dllBaseNames)
                if (!loaded) loaded = loaded || tryLoadFromDir(java.nio.file.Paths.get("CamProV5","camprofw","rust","fea-engine","target","debug","deps").toString(), dllBaseNames)
                if (!loaded) loaded = loaded || tryLoadFromDir(java.nio.file.Paths.get("CamProV5","camprofw","rust","fea-engine","target","release").toString(), dllBaseNames)
                if (!loaded) loaded = loaded || tryLoadFromDir(java.nio.file.Paths.get("CamProV5","camprofw","rust","fea-engine","target","release","deps").toString(), dllBaseNames)

                // Initialize Rust logger (best-effort)
                try {
                    val session = SessionInfo.sessionId
                    val level = System.getProperty("log.level")
                    val dir = System.getProperty("campro.log.dir") ?: "logs"
                    LitvinNative.initRustLoggerNative(session, level, dir)
                    logger.info("Initialized Rust logger: session={} level={} dir={}", session, level ?: "(default)", dir)
                } catch (_: UnsatisfiedLinkError) { } catch (_: Throwable) { }

                nativeLibraryAvailable = verifyNativeLibrary()
                if (!nativeLibraryAvailable && System.getProperty("debug") == "true") {
                    val envDir = System.getenv("FEA_ENGINE_LIB_DIR")
                    val path = System.getenv("PATH") ?: "(unset)"
                    logger.warn("Native verification failed. FEA_ENGINE_LIB_DIR={}, PATH (truncated)={}...", envDir, path.take(200))
                    if (attempted.isNotEmpty()) {
                        logger.warn("Attempted DLL paths:\n{}", attempted.joinToString("\n"))
                    }
                }
            } catch (e: Exception) {
                logger.info("Note: Using fallback motion law implementation")
                nativeLibraryAvailable = false
                if (System.getProperty("debug") == "true") {
                    val errorMessage = when (e) {
                        is UnsatisfiedLinkError -> "Native library loading error: ${e.message}"
                        is IllegalStateException -> "Resource not found: ${e.message}"
                        is IOException -> "I/O error while extracting library: ${e.message}"
                        else -> "Unexpected error: ${e.message}"
                    }
                    logger.error("Detailed error: {}", errorMessage, e)
                }
            }
        }
        
        /**
         * Get the normalized OS name.
         */
        private fun getOsName(): String {
            return when {
                System.getProperty("os.name").toLowerCase().contains("win") -> "windows"
                System.getProperty("os.name").toLowerCase().contains("mac") -> "mac"
                System.getProperty("os.name").toLowerCase().contains("nix") || 
                System.getProperty("os.name").toLowerCase().contains("nux") -> "linux"
                else -> "unknown"
            }
        }
        
        /**
         * Get the normalized OS architecture.
         */
        private fun getOsArch(): String {
            return when {
                System.getProperty("os.arch").toLowerCase().contains("amd64") -> "x86_64"
                System.getProperty("os.arch").toLowerCase().contains("x86_64") -> "x86_64"
                System.getProperty("os.arch").toLowerCase().contains("arm") -> "arm64"
                else -> System.getProperty("os.arch").toLowerCase()
            }
        }
        
        /**
         * Get the library file extension for the current OS.
         */
        private fun getLibraryExtension(): String {
            return when (getOsName()) {
                "windows" -> "dll"
                "mac" -> "dylib"
                "linux" -> "so"
                else -> "unknown"
            }
        }
        
        /**
         * Extract the native library from the resources to a temporary file.
         * 
         * @return The path to the extracted native library
         */
        private fun extractNativeLibrary(): Path {
            // Normalize OS name to remove spaces and version numbers
            val osName = when {
                System.getProperty("os.name").toLowerCase().contains("win") -> "windows"
                System.getProperty("os.name").toLowerCase().contains("mac") -> "mac"
                System.getProperty("os.name").toLowerCase().contains("nix") || 
                System.getProperty("os.name").toLowerCase().contains("nux") -> "linux"
                else -> throw UnsupportedOperationException("Unsupported OS: ${System.getProperty("os.name")}")
            }
        
            // Normalize architecture
            val osArch = when {
                System.getProperty("os.arch").toLowerCase().contains("amd64") -> "x86_64"
                System.getProperty("os.arch").toLowerCase().contains("x86_64") -> "x86_64"
                // Add ARM support if needed
                else -> System.getProperty("os.arch").toLowerCase()
            }
        
            val libraryName = when {
                osName == "windows" -> "campro_motion.dll"
                osName == "mac" -> "libcampro_motion.dylib"
                osName == "linux" -> "libcampro_motion.so"
                else -> throw UnsupportedOperationException("Unsupported operating system: $osName")
            }
        
            val resourcePath = "/native/$osName/$osArch/$libraryName"
            logger.info("Attempting to load native library from resource path: {}", resourcePath)
        
            val inputStream = MotionLawEngine::class.java.getResourceAsStream(resourcePath)
                ?: throw IllegalStateException("Native library not found at $resourcePath")
        
            val tempDir = Files.createTempDirectory("campro_motion")
            val tempFile = tempDir.resolve(libraryName)
        
            inputStream.use { input ->
                Files.newOutputStream(tempFile).use { output ->
                    input.copyTo(output)
                }
            }
        
            logger.info("Extracted native library to: {}", tempFile)
        
            // Ensure the library is deleted when the JVM exits
            tempFile.toFile().deleteOnExit()
            tempDir.toFile().deleteOnExit()
        
            return tempFile
        }
        
        /**
         * Verify that the native library is working correctly.
         * 
         * @return true if the library is working correctly, false otherwise
         */
        private fun verifyNativeLibrary(): Boolean {
            try {
                // Try to call a simple native method to verify the library is working
                val testValue = testNativeLibraryNative()
                return testValue == 42 // Expected return value
            } catch (e: UnsatisfiedLinkError) {
                logger.warn("Native library verification failed: {}", e.message)
                return false
            }
        }
        
        /**
         * Test native method to verify that the library is working correctly.
         * The Rust implementation should return 42.
         */
        private external fun testNativeLibraryNative(): Int

        @JvmStatic fun isNativeAvailable(): Boolean = nativeLibraryAvailable
        @JvmStatic fun runNativeSmokeTest(): Int? {
            return try { testNativeLibraryNative() } catch (_: UnsatisfiedLinkError) { null } catch (_: Throwable) { null }
        }
    }
    
    fun runNativeDiagnostics(): String? {
        return try {
            if (!isNativeAvailable()) return null
            if (litvinId <= 0L) return null
            // lastLitvinSignature is computed on parameter updates
            val sig = lastLitvinSignature
            LitvinNative.runDiagnosticsNative(litvinId, SessionInfo.sessionId, sig)
        } catch (_: UnsatisfiedLinkError) { null } catch (_: Throwable) { null }
    }
    
    private var motionLawId: Long = 0
    private val dataTransfer = DataTransfer()
    
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
    
    /**
     * Create a new motion law engine.
     */
    init {
        // Create a default motion law
        val defaultParameters = mapOf(
            "base_circle_radius" to "25.0",
            "max_lift" to "10.0",
            "cam_duration" to "180.0",
            "rise_duration" to "90.0",
            "dwell_duration" to "45.0",
            "fall_duration" to "90.0",
            "jerk_limit" to "1000.0",
            "acceleration_limit" to "500.0",
            "velocity_limit" to "100.0",
            "rpm" to "3000.0"
        )
        
        // Store the default parameters
        this.parameters = defaultParameters
        
        try {
            if (nativeLibraryAvailable) {
                motionLawId = createMotionLawNative(defaultParameters.entries.flatMap { listOf(it.key, it.value) }.toTypedArray())
            } else {
                // Initialize parameters for the fallback implementation
                updateFallbackParameters(defaultParameters)
            }
        } catch (e: Exception) {
            emitError("Failed to create motion law: ${e.message}")
            e.printStackTrace()
        }
    }
    
    /**
     * Update parameters for the fallback implementation.
     */
    private fun updateFallbackParameters(parameters: Map<String, String>) {
        baseCircleRadius = parameters["base_circle_radius"]?.toDoubleOrNull() ?: 25.0
        maxLift = parameters["max_lift"]?.toDoubleOrNull() ?: 10.0
        camDuration = parameters["cam_duration"]?.toDoubleOrNull() ?: 180.0
        riseDuration = parameters["rise_duration"]?.toDoubleOrNull() ?: 90.0
        dwellDuration = parameters["dwell_duration"]?.toDoubleOrNull() ?: 45.0
        fallDuration = parameters["fall_duration"]?.toDoubleOrNull() ?: 90.0
        jerkLimit = parameters["jerk_limit"]?.toDoubleOrNull() ?: 1000.0
        accelerationLimit = parameters["acceleration_limit"]?.toDoubleOrNull() ?: 500.0
        velocityLimit = parameters["velocity_limit"]?.toDoubleOrNull() ?: 100.0
        rpm = parameters["rpm"]?.toDoubleOrNull() ?: 3000.0
    }
    
    /**
     * Update the motion law parameters.
     * 
     * @param parameters The new parameters
     */
    fun updateParameters(parameters: Map<String, String>) {
        // Store the parameters for use in calculateComponentPositions
        this.parameters = parameters
        try {
            if (nativeLibraryAvailable) {
                val parameterArray = parameters.entries.flatMap { listOf(it.key, it.value) }.toTypedArray()

                // Always keep legacy radial-cam path up to date for non-Litvin
                updateMotionLawParametersNative(motionLawId, parameterArray)

                run {
                    // Build Kotlin-side Litvin params, validate, and construct JNI args per guide
                    val litvinParams = com.campro.v5.data.litvin.litvinParamsFromMap(parameters)
                    val errs = litvinParams.validate()
                    if (errs.isNotEmpty()) {
                        emitError("Invalid Litvin parameters: ${errs.joinToString("; ")}")
                        // Skip Litvin rebuild on invalid input; fallback path already updated above
                    } else {
                        // Phase 1a/1b Kotlin-side generation (always available for UI)
                        try {
                            motionSamples = MotionLawGenerator.generateMotion(litvinParams)
                            // Phase 1a baseline diagnostics from motion-law (accel/jerk maxima)
                            motionSamples?.let { ms ->
                                val md = MotionDiagnosticsComputer.compute(ms)
                                PerfDiag.accelMaxAbs = md.accelMaxAbsPerOmega2
                                PerfDiag.jerkMaxAbs = md.jerkMaxAbsPerOmega3
                                try {
                                    logger.info(
                                        "Motion diagnostics: stepDeg=${"%.6f".format(ms.stepDeg)} accelMaxAbs=${"%.6f".format(md.accelMaxAbsPerOmega2)} jerkMaxAbs=${"%.6f".format(md.jerkMaxAbsPerOmega3)}"
                                    )
                                } catch (_: Throwable) { }
                                // Optional feasibility gate: surface error and short-circuit if accel exceeds user limit
                                val accelLimit = parameters["accel_limit_per_omega2"]?.toDoubleOrNull()
                                if (accelLimit != null && md.accelMaxAbsPerOmega2 > accelLimit) {
                                    emitError("Acceleration limit exceeded: ${md.accelMaxAbsPerOmega2} > $accelLimit")
                                    return
                                }
                            }
                            transmission = motionSamples?.let { TransmissionSynthesis.computeTransmissionAndPitch(it, litvinParams) }
                            try {
                                val meanI = transmission?.iOfTheta?.map { it.second }?.average()
                                val resI = transmission?.residualArcLenRms
                                logger.info(
                                    "Litvin preview: stepDeg=${motionSamples?.stepDeg}, meanI=${"%.6f".format(meanI ?: Double.NaN)}, residual=${"%.6f".format(resI ?: Double.NaN)}"
                                )
                            } catch (_: Throwable) { }
                        } catch (e: Exception) {
                            emitError("Motion law synthesis failed: ${e.message}")
                        }
                        val litvinArgs = litvinParams.toJniArgs()
                        // Compute signature from the normalized Litvin args (order-insensitive)
                        val sigMap = com.campro.v5.data.litvin.jniArgsToMap(litvinArgs)
                        val sig = LitvinSignature.compute(sigMap)
                        logger.info("Litvin update: sig=${sig.take(16)}...")
                        logger.debug(
                            "Params: up=${litvinParams.upFraction}, ramps=[${litvinParams.rampBeforeTdcDeg},${litvinParams.rampAfterTdcDeg},${litvinParams.rampBeforeBdcDeg},${litvinParams.rampAfterBdcDeg}], " +
                                    "rpm=${litvinParams.rpm}, R=${litvinParams.journalRadius}, beta=${litvinParams.journalPhaseBetaDeg}, step=${litvinParams.samplingStepDeg}"
                        )
                        val changed = sig != lastLitvinSignature
                        if (!changed) {
                            // Skip rebuild; keep existing tables
                        } else {
                            lastLitvinSignature = sig
                            // Create or update Litvin law and prefetch JSON payloads
                            if (litvinId == 0L) {
                                litvinId = try { LitvinNative.createLitvinLawNative(litvinArgs) } catch (e: UnsatisfiedLinkError) { 0L }
                            } else {
                                try { LitvinNative.updateLitvinLawParametersNative(litvinId, litvinArgs) } catch (_: UnsatisfiedLinkError) {}
                            }
                            if (litvinId > 0L) {
                                try {
                                    val curvesPath = LitvinNative.getLitvinPitchCurvesNative(litvinId)
                                    val tablesPath = LitvinNative.getLitvinKinematicsTablesNative(litvinId)
                                    val boundaryPath = try { LitvinNative.getLitvinFeaBoundaryNative(litvinId) } catch (_: UnsatisfiedLinkError) { null }
                                    // gear_mode removed: Litvin is always active
                                    val curvesFile = File(curvesPath)
                                    val tablesFile = File(tablesPath)
                                    if (curvesFile.exists()) {
                                        litvinCurves = com.campro.v5.data.litvin.LitvinJsonLoader.loadPitchCurves(curvesFile)
                                    }
                                    if (tablesFile.exists()) {
                                        litvinTables = com.campro.v5.data.litvin.LitvinJsonLoader.loadTables(tablesFile)
                                        // Update shared diagnostics for UI
                                        PerfDiag.lastLitvinDiagnostics = litvinTables?.diagnostics
                                    }
                                    // Optionally load boundary for external FEA pipeline usage
                                    if (boundaryPath != null) {
                                        val bFile = File(boundaryPath)
                                        if (bFile.exists()) {
                                            // Load to validate format and warm cache; consumers can request again
                                            try { com.campro.v5.data.litvin.LitvinJsonLoader.loadFeaBoundary(bFile) } catch (_: Exception) {}
                                        }
                                    }
                                } catch (e: Exception) {
                                    emitError("Failed to prefetch Litvin JSON: ${e.message}")
                                }
                            }
                        }
                    }
                }
            } else {
                // Update parameters for the fallback implementation
                updateFallbackParameters(parameters)
            }
        } catch (e: Exception) {
            emitError("Failed to update motion law parameters: ${e.message}")
            e.printStackTrace()
        }
    }
    
    /**
     * Get the component positions for the given angle.
     * 
     * @param angle The angle in degrees
     * @return The component positions
     */
    fun getComponentPositions(angle: Double): ComponentPositions {
        try {
            // Get the displacement at the given angle
            val displacement = if (nativeLibraryAvailable) {
                getDisplacementNative(motionLawId, angle)
            } else {
                getDisplacementFallback(angle)
            }
            
            // Calculate component positions based on the displacement
            return calculateComponentPositions(angle, displacement)
        } catch (e: Exception) {
            emitError("Failed to get component positions: ${e.message}")
            e.printStackTrace()
            
            // Return default positions
            return ComponentPositions(
                pistonPosition = Offset(0f, 0f),
                rodPosition = Offset(0f, 0f),
                camPosition = Offset(0f, 0f)
            )
        }
    }
    
    /**
     * Fallback implementation of displacement calculation.
     */
    private fun getDisplacementFallback(angle: Double): Double {
        val thetaNorm = angle % 360.0
        val totalDuration = riseDuration + dwellDuration + fallDuration
        
        return when {
            thetaNorm <= riseDuration -> {
                // Rise phase
                val beta = thetaNorm / riseDuration
                maxLift * (beta - Math.sin(2.0 * Math.PI * beta) / (2.0 * Math.PI))
            }
            thetaNorm <= riseDuration + dwellDuration -> {
                // Dwell phase
                maxLift
            }
            thetaNorm <= totalDuration -> {
                // Fall phase
                val thetaFall = thetaNorm - (riseDuration + dwellDuration)
                val beta = thetaFall / fallDuration
                maxLift * (1.0 - (beta - Math.sin(2.0 * Math.PI * beta) / (2.0 * Math.PI)))
            }
            else -> {
                // Outside cam duration
                0.0
            }
        }
    }
    
    /**
     * Fallback implementation of velocity calculation.
     */
    private fun getVelocityFallback(angle: Double): Double {
        val thetaNorm = angle % 360.0
        val totalDuration = riseDuration + dwellDuration + fallDuration
        val degToRad = Math.PI / 180.0
        val omega = 2.0 * Math.PI * rpm / 60.0
        
        return when {
            thetaNorm <= riseDuration -> {
                // Rise phase
                val beta = thetaNorm / riseDuration
                val dbetaDtheta = 1.0 / riseDuration
                maxLift * dbetaDtheta * (1.0 - Math.cos(2.0 * Math.PI * beta)) * omega * degToRad
            }
            thetaNorm <= riseDuration + dwellDuration -> {
                // Dwell phase - velocity is zero
                0.0
            }
            thetaNorm <= totalDuration -> {
                // Fall phase
                val thetaFall = thetaNorm - (riseDuration + dwellDuration)
                val beta = thetaFall / fallDuration
                val dbetaDtheta = 1.0 / fallDuration
                -maxLift * dbetaDtheta * (1.0 - Math.cos(2.0 * Math.PI * beta)) * omega * degToRad
            }
            else -> {
                // Outside cam duration
                0.0
            }
        }
    }
    
    /**
     * Fallback implementation of acceleration calculation.
     */
    private fun getAccelerationFallback(angle: Double): Double {
        val thetaNorm = angle % 360.0
        val totalDuration = riseDuration + dwellDuration + fallDuration
        val degToRad = Math.PI / 180.0
        val omega = 2.0 * Math.PI * rpm / 60.0
        
        return when {
            thetaNorm <= riseDuration -> {
                // Rise phase
                val beta = thetaNorm / riseDuration
                val dbetaDtheta = 1.0 / riseDuration
                maxLift * (dbetaDtheta * dbetaDtheta) * 2.0 * Math.PI * Math.sin(2.0 * Math.PI * beta) *
                    (omega * degToRad) * (omega * degToRad)
            }
            thetaNorm <= riseDuration + dwellDuration -> {
                // Dwell phase - acceleration is zero
                0.0
            }
            thetaNorm <= totalDuration -> {
                // Fall phase
                val thetaFall = thetaNorm - (riseDuration + dwellDuration)
                val beta = thetaFall / fallDuration
                val dbetaDtheta = 1.0 / fallDuration
                maxLift * (dbetaDtheta * dbetaDtheta) * 2.0 * Math.PI * Math.sin(2.0 * Math.PI * beta) *
                    (omega * degToRad) * (omega * degToRad)
            }
            else -> {
                // Outside cam duration
                0.0
            }
        }
    }
    
    /**
     * Fallback implementation of jerk calculation.
     */
    private fun getJerkFallback(angle: Double): Double {
        val thetaNorm = angle % 360.0
        val totalDuration = riseDuration + dwellDuration + fallDuration
        val degToRad = Math.PI / 180.0
        val omega = 2.0 * Math.PI * rpm / 60.0
        
        return when {
            thetaNorm <= riseDuration -> {
                // Rise phase
                val beta = thetaNorm / riseDuration
                val dbetaDtheta = 1.0 / riseDuration
                maxLift * (dbetaDtheta * dbetaDtheta * dbetaDtheta) * 4.0 * Math.PI * Math.PI * Math.cos(2.0 * Math.PI * beta) *
                    (omega * degToRad) * (omega * degToRad) * (omega * degToRad)
            }
            thetaNorm <= riseDuration + dwellDuration -> {
                // Dwell phase - jerk is zero
                0.0
            }
            thetaNorm <= totalDuration -> {
                // Fall phase
                val thetaFall = thetaNorm - (riseDuration + dwellDuration)
                val beta = thetaFall / fallDuration
                val dbetaDtheta = 1.0 / fallDuration
                -maxLift * (dbetaDtheta * dbetaDtheta * dbetaDtheta) * 4.0 * Math.PI * Math.PI * Math.cos(2.0 * Math.PI * beta) *
                    (omega * degToRad) * (omega * degToRad) * (omega * degToRad)
            }
            else -> {
                // Outside cam duration
                0.0
            }
        }
    }
    
    /**
     * Cache for component positions to improve performance
     * Key: Pair of angle (rounded to nearest 0.5 degree) and displacement (rounded to 3 decimal places)
     * Value: Calculated component positions
     * 
     * Using LRU (Least Recently Used) approach with a fixed size to prevent memory issues
     */
    private val positionCache = object : LinkedHashMap<Pair<Double, Double>, ComponentPositions>(100, 0.75f, true) {
        override fun removeEldestEntry(eldest: Map.Entry<Pair<Double, Double>, ComponentPositions>): Boolean {
            return size > 500 // Limit cache size to 500 entries
        }
    }
    
    /**
     * Calculate component positions based on the angle and displacement.
     * Enhanced with more accurate mechanical modeling and caching.
     * 
     * @param angle The angle in degrees
     * @param displacement The displacement
     * @return The component positions
     */
    private fun calculateComponentPositions(angle: Double, displacement: Double): ComponentPositions {
        try {
            // Round values for cache key to reduce cache size while maintaining accuracy
            val cacheKeyAngle = (angle * 2).toInt() / 2.0  // Round to nearest 0.5 degree
            val cacheKeyDisplacement = (displacement * 1000).toInt() / 1000.0  // Round to 3 decimal places
            val cacheKey = Pair(cacheKeyAngle, cacheKeyDisplacement)

            // Check cache first
            positionCache[cacheKey]?.let { return it }

            // 1) Prefer Litvin kinematics tables if available (Phase 0 native JSONs)
            litvinTables?.let {
                val fs = getLitvinFrameState(angle)
                if (fs != null && fs.centerX.isNotEmpty()) {
                    val cx = fs.centerX[0].toFloat()
                    val cy = fs.centerY[0].toFloat()
                    val jx = fs.journalX[0].toFloat()
                    val jy = fs.journalY[0].toFloat()
                    val ps = fs.pistonS[0].toFloat()
                    val positions = ComponentPositions(
                        pistonPosition = Offset(0f, ps),
                        rodPosition = Offset(jx, jy),
                        camPosition = Offset(cx, cy)
                    )
                    positionCache[cacheKey] = positions
                    return positions
                }
            }

            // 2) If no native tables, use Kotlin-generated motion samples for a simple prototype visualization
            motionSamples?.let { ml ->
                val step = ml.stepDeg.coerceAtLeast(1e-6)
                val n = ml.samples.size
                if (n > 0) {
                    val idx = (((angle / step).roundToInt() % n) + n) % n
                    val x = ml.samples[idx].xMm.toFloat()
                    val positions = ComponentPositions(
                        pistonPosition = Offset(0f, x),
                        rodPosition = Offset(0f, x),
                        camPosition = Offset(0f, 0f)
                    )
                    positionCache[cacheKey] = positions
                    return positions
                }
            }

            // 3) Legacy radial-cam fallback (previous behavior)
            // Convert angle to radians
            val angleRad = Math.toRadians(angle)

            // Get parameters from the motion law with proper defaults
            val baseCircleRadius = baseCircleRadius.toFloat()

            // Get rod length and piston diameter from parameters or use defaults
            val rodLength = try { parameters["rod_length"]?.toFloatOrNull() ?: 40f } catch (e: Exception) { 40f }
            val pistonDiameter = try { parameters["piston_diameter"]?.toFloatOrNull() ?: 70f } catch (e: Exception) { 70f }
            val followerOffset = try { parameters["follower_offset"]?.toFloatOrNull() ?: 0f } catch (e: Exception) { 0f }
            val camOffset = try { parameters["cam_offset"]?.toFloatOrNull() ?: 0f } catch (e: Exception) { 0f }

            val camPosition = Offset(camOffset, 0f)

            val baseCircleX = (baseCircleRadius * cos(angleRad)).toFloat() + camOffset
            val baseCircleY = (baseCircleRadius * sin(angleRad)).toFloat()

            val followerX = baseCircleX + followerOffset
            val followerY = baseCircleY + displacement.toFloat()

            val rodAngle = try {
                Math.atan2((pistonDiameter / 2 - followerX).toDouble(), (rodLength - (followerY - baseCircleY)).toDouble())
            } catch (_: Exception) { 0.0 }

            val pistonX = followerX
            val pistonY = followerY + rodLength * Math.cos(rodAngle).toFloat()

            val positions = ComponentPositions(
                pistonPosition = Offset(pistonX, pistonY),
                rodPosition = Offset(followerX, followerY),
                camPosition = camPosition
            )

            positionCache[cacheKey] = positions
            return positions
        } catch (e: Exception) {
            logger.error("Failed to calculate component positions: {}", e.message, e)
            return ComponentPositions(
                pistonPosition = Offset(0f, 0f),
                rodPosition = Offset(0f, 0f),
                camPosition = Offset(0f, 0f)
            )
        }
    }
    
    /**
     * Perform a kinematic analysis of the motion law.
     * 
     * @param numPoints The number of points to analyze
     * @return The kinematic analysis results
     */
    suspend fun analyzeKinematics(numPoints: Int): KinematicAnalysis = withContext(Dispatchers.IO) {
        try {
            if (nativeLibraryAvailable) {
                // Create a temporary file for the results
                val resultsFile = File.createTempFile("kinematic_analysis_", ".json")
                resultsFile.deleteOnExit()
                
                // Call the native method
                analyzeKinematicsNative(
                    motionLawId,
                    numPoints,
                    resultsFile.absolutePath
                )
                
                // Parse the results
                val analysis = dataTransfer.transferFromRust(resultsFile, KinematicAnalysis::class.java)
                
                return@withContext analysis
            } else {
                // Use fallback implementation to generate analysis
                return@withContext analyzeKinematicsFallback(numPoints)
            }
        } catch (e: Exception) {
            emitError("Failed to analyze kinematics: ${e.message}")
            throw e
        }
    }
    
    /**
     * Fallback implementation of kinematic analysis.
     */
    private fun analyzeKinematicsFallback(numPoints: Int): KinematicAnalysis {
        // Generate angle array
        val theta = List(numPoints) { i -> i * 360.0 / (numPoints - 1) }
        
        // Calculate kinematics
        val displacement = theta.map { getDisplacementFallback(it) }
        val velocity = theta.map { getVelocityFallback(it) }
        val acceleration = theta.map { getAccelerationFallback(it) }
        val jerk = theta.map { getJerkFallback(it) }
        
        // Calculate statistics
        val maxVelocity = velocity.maxOfOrNull { kotlin.math.abs(it) } ?: 0.0
        val maxAcceleration = acceleration.maxOfOrNull { kotlin.math.abs(it) } ?: 0.0
        val maxJerk = jerk.maxOfOrNull { kotlin.math.abs(it) } ?: 0.0
        
        val rmsAcceleration = kotlin.math.sqrt(acceleration.map { it * it }.average())
        val rmsJerk = kotlin.math.sqrt(jerk.map { it * it }.average())
        
        // Check constraint violations
        val velocityViolation = maxVelocity > velocityLimit
        val accelerationViolation = maxAcceleration > accelerationLimit
        val jerkViolation = maxJerk > jerkLimit
        
        return KinematicAnalysis(
            theta = theta,
            displacement = displacement,
            velocity = velocity,
            acceleration = acceleration,
            jerk = jerk,
            maxVelocity = maxVelocity,
            maxAcceleration = maxAcceleration,
            maxJerk = maxJerk,
            rmsAcceleration = rmsAcceleration,
            rmsJerk = rmsJerk,
            velocityViolation = velocityViolation,
            accelerationViolation = accelerationViolation,
            jerkViolation = jerkViolation
        )
    }
    
    /**
     * Clean up resources when the engine is no longer needed.
     */
    fun dispose() {
        try {
            // Only try to dispose the native motion law if the native library is available
            if (nativeLibraryAvailable) {
                disposeMotionLawNative(motionLawId)
                if (litvinId != 0L) {
                    try { LitvinNative.disposeLitvinLawNative(litvinId) } catch (_: UnsatisfiedLinkError) {}
                    litvinId = 0
                    litvinCurves = null
                    litvinTables = null
                }
            }
            // No cleanup needed for the fallback implementation
        } catch (e: Exception) {
            emitError("Failed to dispose motion law: ${e.message}")
            e.printStackTrace()
        }
    }
    
    // Native methods
    
    /**
     * Native method to create a motion law.
     * 
     * @param parameters The parameters for the motion law
     * @return The ID of the created motion law
     */
    private external fun createMotionLawNative(parameters: Array<String>): Long
    
    /**
     * Native method to update motion law parameters.
     * 
     * @param motionLawId The ID of the motion law
     * @param parameters The new parameters
     */
    private external fun updateMotionLawParametersNative(motionLawId: Long, parameters: Array<String>)
    
    /**
     * Native method to get the displacement at a specific angle.
     * 
     * @param motionLawId The ID of the motion law
     * @param angle The angle in degrees
     * @return The displacement
     */
    private external fun getDisplacementNative(motionLawId: Long, angle: Double): Double
    
    /**
     * Native method to get the velocity at a specific angle.
     * 
     * @param motionLawId The ID of the motion law
     * @param angle The angle in degrees
     * @return The velocity
     */
    private external fun getVelocityNative(motionLawId: Long, angle: Double): Double
    
    /**
     * Native method to get the acceleration at a specific angle.
     * 
     * @param motionLawId The ID of the motion law
     * @param angle The angle in degrees
     * @return The acceleration
     */
    private external fun getAccelerationNative(motionLawId: Long, angle: Double): Double
    
    /**
     * Native method to get the jerk at a specific angle.
     * 
     * @param motionLawId The ID of the motion law
     * @param angle The angle in degrees
     * @return The jerk
     */
    private external fun getJerkNative(motionLawId: Long, angle: Double): Double
    
    /**
     * Native method to analyze kinematics.
     * 
     * @param motionLawId The ID of the motion law
     * @param numPoints The number of points to analyze
     * @param resultsFilePath The path to the results file
     */
    private external fun analyzeKinematicsNative(
        motionLawId: Long,
        numPoints: Int,
        resultsFilePath: String
    )
    
    /**
     * Native method to dispose a motion law.
     * 
     * @param motionLawId The ID of the motion law
     */
    private external fun disposeMotionLawNative(motionLawId: Long)
    
}

/**
 * Data class for kinematic analysis results.
 */
data class KinematicAnalysis(
    val theta: List<Double>,
    val displacement: List<Double>,
    val velocity: List<Double>,
    val acceleration: List<Double>,
    val jerk: List<Double>,
    val maxVelocity: Double,
    val maxAcceleration: Double,
    val maxJerk: Double,
    val rmsAcceleration: Double,
    val rmsJerk: Double,
    val velocityViolation: Boolean,
    val accelerationViolation: Boolean,
    val jerkViolation: Boolean
)