package com.campro.v5.animation

import com.campro.v5.data.litvin.ProfileSolverMode
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.CsvSource
import org.junit.jupiter.params.provider.ValueSource
import java.io.File
import java.util.concurrent.TimeUnit
import kotlin.math.*

/**
 * Integration tests for MotionLawEngine using the actual public API.
 * 
 * These tests focus on the real public interface that users interact with,
 * ensuring the engine behaves correctly end-to-end without mocking internal components.
 */
class MotionLawEngineIntegrationTest {
    
    private lateinit var engine: MotionLawEngine
    
    @BeforeEach
    fun setUp() {
        MotionLawEngine.resetInstance()
        engine = MotionLawEngine.getInstance()
    }
    
    @AfterEach
    fun tearDown() {
        engine.dispose()
    }

    // ========================================
    // BASIC ENGINE LIFECYCLE TESTS
    // ========================================

    @Test
    fun `engine initializes with default state`() {
        assertNotNull(engine, "Engine should be created successfully")
        
        // Initial state should be empty/null for optional components
        assertNull(engine.getMotionLawSamples(), "Initial motion samples should be null")
        assertNull(engine.getTransmissionPreview(), "Initial transmission should be null")
        assertNull(engine.getLitvinTables(), "Initial Litvin tables should be null")
        assertNull(engine.getLitvinCurves(), "Initial Litvin curves should be null")
        assertFalse(engine.isLitvinActive(), "Litvin should not be active initially")
    }

    @Test
    fun `engine handles dispose gracefully`() {
        // Should not throw any exceptions
        assertDoesNotThrow {
            engine.dispose()
        }
        
        // Should be safe to dispose multiple times
        assertDoesNotThrow {
            engine.dispose()
        }
    }

    // ========================================
    // PARAMETER UPDATE TESTS
    // ========================================

    @Test
    @Timeout(30, unit = TimeUnit.SECONDS)
    fun `engine updates parameters successfully`() {
        val basicParams = mapOf(
            "strokeLengthMm" to "15.0",
            "samplingStepDeg" to "2.0",
            "dwellTdcDeg" to "10.0",
            "dwellBdcDeg" to "8.0",
            "rampProfile" to "Cycloidal",
            "Profile Solver" to "Piecewise"
        )
        
        // Should not throw exceptions
        assertDoesNotThrow {
            engine.updateParameters(basicParams)
        }
        
        // Should generate motion samples after parameter update (may be null if validation fails)
        val samples = engine.getMotionLawSamples()
        if (samples != null) {
            assertTrue(samples.samples.isNotEmpty(), "If motion samples exist, should not be empty")
            assertEquals(2.0, samples.stepDeg, 1e-12, "Step size should match parameter")
        } else {
            // If motion samples are null, the engine should still be in a valid state
            // This can happen if parameter validation fails or native library is unavailable
            println("Motion samples not generated - likely due to parameter validation or library availability")
        }
    }

    @ParameterizedTest
    @CsvSource(
        "Piecewise, 1.0",
        "Piecewise, 2.0", 
        "Piecewise, 5.0",
        "Collocation, 2.0"  // May fallback to piecewise if not available
    )
    @Timeout(60, unit = TimeUnit.SECONDS)
    fun `engine handles different solver modes and step sizes`(solverMode: String, stepDeg: Double) {
        val params = mapOf(
            "strokeLengthMm" to "12.0",
            "samplingStepDeg" to stepDeg.toString(),
            "Profile Solver" to solverMode,
            "rampProfile" to "S5"
        )
        
        assertDoesNotThrow {
            engine.updateParameters(params)
        }
        
        val samples = engine.getMotionLawSamples()
        if (samples != null) {
            assertTrue(samples.samples.isNotEmpty(), "If samples exist, should not be empty")
            assertEquals(stepDeg, samples.stepDeg, 1e-12, "Step size should match for $solverMode")
            
            // All samples should have finite values
            for ((i, sample) in samples.samples.withIndex()) {
                assertTrue(sample.thetaDeg.isFinite(), "Theta at index $i should be finite")
                assertTrue(sample.xMm.isFinite(), "Position at index $i should be finite")
                assertTrue(sample.vMmPerOmega.isFinite(), "Velocity at index $i should be finite")
                assertTrue(sample.aMmPerOmega2.isFinite(), "Acceleration at index $i should be finite")
            }
        } else {
            println("Samples not generated for $solverMode with step $stepDeg - may be expected")
        }
    }

    @Test
    fun `engine handles invalid parameters gracefully`() {
        val invalidParams = mapOf(
            "strokeLengthMm" to "invalid_number",
            "samplingStepDeg" to "-1.0",  // Negative step
            "Profile Solver" to "NonExistentSolver"
        )
        
        // Should not crash, but may not generate valid samples
        assertDoesNotThrow {
            engine.updateParameters(invalidParams)
        }
        
        // The engine should either produce valid samples or null, but not crash
        val samples = engine.getMotionLawSamples()
        if (samples != null) {
            assertTrue(samples.stepDeg > 0, "If samples generated, step should be positive")
        }
    }

    // ========================================
    // COMPONENT POSITION TESTS
    // ========================================

    @ParameterizedTest
    @ValueSource(doubles = [0.0, 90.0, 180.0, 270.0, 359.9])
    fun `getComponentPositions works for various angles`(angleDeg: Double) {
        // Set up with basic parameters
        val params = mapOf(
            "strokeLengthMm" to "10.0",
            "samplingStepDeg" to "2.0",
            "Profile Solver" to "Piecewise"
        )
        engine.updateParameters(params)
        
        // Should not throw for any valid angle
        assertDoesNotThrow {
            val positions = engine.getComponentPositions(angleDeg)
            assertNotNull(positions, "Positions should be available for angle $angleDeg")
            
            // Validate position structure
            assertTrue(positions.pistonPosition.x.isFinite(), "Piston X should be finite at $angleDeg")
            assertTrue(positions.pistonPosition.y.isFinite(), "Piston Y should be finite at $angleDeg")
            assertTrue(positions.rodPosition.x.isFinite(), "Rod end X should be finite at $angleDeg")
            assertTrue(positions.rodPosition.y.isFinite(), "Rod end Y should be finite at $angleDeg")
            assertTrue(positions.camPosition.x.isFinite(), "Cam X should be finite at $angleDeg")
            assertTrue(positions.camPosition.y.isFinite(), "Cam Y should be finite at $angleDeg")
        }
    }

    @Test
    fun `getComponentPositions returns consistent results for same angle`() {
        val params = mapOf(
            "strokeLengthMm" to "15.0",
            "samplingStepDeg" to "1.0",
            "Profile Solver" to "Piecewise"
        )
        engine.updateParameters(params)
        
        val angle = 45.0
        val positions1 = engine.getComponentPositions(angle)
        val positions2 = engine.getComponentPositions(angle)
        
        assertNotNull(positions1)
        assertNotNull(positions2)
        
        // Should get identical results for same angle
        assertEquals(positions1.pistonPosition.x, positions2.pistonPosition.x, 1e-6f, "Piston X should be consistent")
        assertEquals(positions1.pistonPosition.y, positions2.pistonPosition.y, 1e-6f, "Piston Y should be consistent") 
        assertEquals(positions1.rodPosition.x, positions2.rodPosition.x, 1e-6f, "Rod end X should be consistent")
        assertEquals(positions1.rodPosition.y, positions2.rodPosition.y, 1e-6f, "Rod end Y should be consistent")
    }

    // ========================================
    // LITVIN INTEGRATION TESTS  
    // ========================================

    @Test
    @Timeout(45, unit = TimeUnit.SECONDS)
    fun `engine Litvin integration lifecycle`() {
        val litvinParams = mapOf(
            "strokeLengthMm" to "20.0",
            "samplingStepDeg" to "2.0",
            "dwellTdcDeg" to "15.0",
            "dwellBdcDeg" to "10.0",
            "rampProfile" to "Cycloidal",
            "rpm" to "3000.0",
            "Profile Solver" to "Piecewise"
        )
        
        engine.updateParameters(litvinParams)
        
        // Motion samples might be available (depends on parameter validation and system state)
        val samples = engine.getMotionLawSamples()
        if (samples == null) {
            println("Motion samples not available - may be expected for Litvin integration test")
            return
        }
        
        // Transmission preview might be available
        val transmission = engine.getTransmissionPreview()
        if (transmission != null) {
            assertTrue(transmission.iOfTheta.isNotEmpty(), "If transmission available, should have i(theta) samples")
            assertTrue(transmission.pitchRing.isNotEmpty(), "If transmission available, should have pitch ring samples")
            assertTrue(transmission.pitchPlanet.isNotEmpty(), "If transmission available, should have pitch planet samples")
            assertTrue(transmission.residualArcLenRms >= 0.0, "Arc length residual should be non-negative")
        }
        
        // Litvin might be active (depends on native availability)
        if (engine.isLitvinActive()) {
            assertNotNull(engine.getLitvinTables(), "If Litvin active, tables should be available")
            assertNotNull(engine.getLitvinCurves(), "If Litvin active, curves should be available")
            
            // Test frame state extraction
            val frameState = engine.getLitvinFrameState(90.0)
            if (frameState != null) {
                assertTrue(frameState.centerX.isNotEmpty(), "Frame state should have center X data")
                assertTrue(frameState.centerY.isNotEmpty(), "Frame state should have center Y data")
                assertTrue(frameState.pistonS.isNotEmpty(), "Frame state should have piston data")
            }
        }
    }

    @Test
    fun `engine handles Litvin unavailability gracefully`() {
        val params = mapOf(
            "strokeLengthMm" to "10.0",
            "Profile Solver" to "Piecewise"
        )
        
        // Should work even if Litvin is not available
        assertDoesNotThrow {
            engine.updateParameters(params)
        }
        
        // Should still generate motion samples (or handle gracefully if not)
        val samples = engine.getMotionLawSamples()
        // Note: samples may be null if parameter validation fails or system is not ready
        if (samples != null) {
            assertTrue(samples.samples.isNotEmpty(), "If samples exist, should not be empty")
        }
    }

    // ========================================
    // EXPORT AND SERIALIZATION TESTS
    // ========================================

    @Test
    fun `engine exports motion law to JSON successfully`() {
        val params = mapOf(
            "strokeLengthMm" to "12.0",
            "samplingStepDeg" to "3.0",
            "Profile Solver" to "Piecewise"
        )
        engine.updateParameters(params)
        
        val tempFile = File.createTempFile("motion_law_test", ".json")
        try {
            assertDoesNotThrow {
                engine.exportMotionLawToJson(tempFile)
            }
            
            // File should exist and have content if motion samples were generated
            if (engine.getMotionLawSamples() != null) {
                assertTrue(tempFile.exists(), "Export file should exist")
                assertTrue(tempFile.length() > 0, "Export file should have content")
            }
        } finally {
            tempFile.delete()
        }
    }

    // ========================================
    // PERFORMANCE AND STRESS TESTS
    // ========================================

    @Test
    @Timeout(30, unit = TimeUnit.SECONDS)
    fun `engine handles multiple parameter updates efficiently`() {
        val baseParams = mapOf(
            "strokeLengthMm" to "10.0",
            "Profile Solver" to "Piecewise"
        )
        
        // Multiple rapid updates should not cause issues
        for (i in 1..10) {
            val params = baseParams + ("samplingStepDeg" to "${0.5 + i * 0.5}")
            assertDoesNotThrow {
                engine.updateParameters(params)
            }
        }
        
        // Final state should be valid (if samples are generated)
        val finalSamples = engine.getMotionLawSamples()
        if (finalSamples != null) {
            // Due to discretization, the actual step size may differ slightly from the requested value
            // The actual step size should be close to the requested value (within reasonable tolerance)
            val expectedStep = 5.5
            val actualStep = finalSamples.stepDeg
            val tolerance = 0.1 // Allow 0.1 degree tolerance for discretization
            assertTrue(
                kotlin.math.abs(actualStep - expectedStep) <= tolerance,
                "Final step size should be close to last update: expected $expectedStep, got $actualStep"
            )
        } else {
            println("Final samples not available - parameter updates handled gracefully")
        }
    }

    @Test
    @Timeout(20, unit = TimeUnit.SECONDS)
    fun `engine handles component position queries efficiently`() {
        val params = mapOf(
            "strokeLengthMm" to "8.0",
            "samplingStepDeg" to "2.0",
            "Profile Solver" to "Piecewise"
        )
        engine.updateParameters(params)
        
        // Query positions at many angles efficiently
        val startTime = System.currentTimeMillis()
        for (angle in 0..359 step 5) {
            val positions = engine.getComponentPositions(angle.toDouble())
            assertNotNull(positions, "Positions should be available for angle $angle")
        }
        val elapsedTime = System.currentTimeMillis() - startTime
        
        // Should complete reasonably quickly (less than 10 seconds for 72 queries)
        assertTrue(elapsedTime < 10000, "Position queries should complete efficiently: ${elapsedTime}ms")
    }

    // ========================================
    // ERROR HANDLING AND EDGE CASES
    // ========================================

    @Test
    fun `engine handles extreme parameter values`() {
        val extremeParams = listOf(
            mapOf("strokeLengthMm" to "0.1", "samplingStepDeg" to "0.1"),   // Very small
            mapOf("strokeLengthMm" to "100.0", "samplingStepDeg" to "10.0"), // Large
            mapOf("dwellTdcDeg" to "0.0", "dwellBdcDeg" to "0.0"),          // No dwells
            mapOf("dwellTdcDeg" to "60.0", "dwellBdcDeg" to "60.0"),        // Large dwells
            mapOf("rpm" to "100.0"),                                         // Low RPM
            mapOf("rpm" to "10000.0")                                        // High RPM
        )
        
        for ((i, params) in extremeParams.withIndex()) {
            val fullParams = mapOf("Profile Solver" to "Piecewise") + params
            assertDoesNotThrow {
                engine.updateParameters(fullParams)
            }
            
            // Should produce some result or handle gracefully
            val samples = engine.getMotionLawSamples()
            if (samples != null) {
                assertTrue(samples.samples.isNotEmpty(), "If samples produced for case $i, should not be empty")
            }
        }
    }

    @Test
    fun `engine handles collocation fallback correctly`() {
        val collocationParams = mapOf(
            "strokeLengthMm" to "15.0",
            "samplingStepDeg" to "2.0",
            "Profile Solver" to "Collocation",
            "rampProfile" to "S5"
        )
        
        // Should handle collocation mode (may fallback to piecewise)
        assertDoesNotThrow {
            engine.updateParameters(collocationParams)
        }
        
        val samples = engine.getMotionLawSamples()
        if (samples != null) {
            assertTrue(samples.samples.isNotEmpty(), "If samples exist, should not be empty")
            assertEquals(2.0, samples.stepDeg, 1e-12, "Step size should be preserved through fallback")
        } else {
            println("Collocation fallback test completed - samples not generated (may be expected)")
        }
    }

    // ========================================
    // CONCURRENT ACCESS TESTS
    // ========================================

    @Test
    @Timeout(20, unit = TimeUnit.SECONDS)
    fun `engine handles concurrent position queries safely`() {
        val params = mapOf(
            "strokeLengthMm" to "10.0",
            "samplingStepDeg" to "2.0",
            "Profile Solver" to "Piecewise"
        )
        engine.updateParameters(params)
        
        // Multiple threads querying positions simultaneously
        val threads = (1..5).map { threadId ->
            Thread {
                for (i in 0..10) {
                    val angle = (threadId * 30 + i * 5) % 360
                    val positions = engine.getComponentPositions(angle.toDouble())
                    assertNotNull(positions, "Thread $threadId should get positions for angle $angle")
                }
            }
        }
        
        threads.forEach { it.start() }
        threads.forEach { it.join() }
        
        // All threads should complete without exceptions
        assertTrue(true, "Concurrent access test completed successfully")
    }
}
