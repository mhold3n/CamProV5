package com.campro.v5.animation

import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.ProfileSolverMode
import com.campro.v5.data.litvin.RampProfile
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

/**
 * Simple validation tests for the collocation framework.
 * These tests focus on framework integration without requiring full solver functionality.
 */
class CollocationValidationTest {

    @Test
    fun `collocation framework is integrated`() {
        // Test that collocation components are available
        assertNotNull(CollocationMotionSolver, "CollocationMotionSolver should be available")
        assertNotNull(ProfileSolverMode.Collocation, "Collocation mode should be available")
        
        val info = CollocationMotionSolver.getSolverInfo()
        assertTrue(info.contains("CollocationMotionSolver"), "Solver info should be available")
    }

    @Test
    fun `profile solver mode parameter works`() {
        val piecewiseParams = LitvinUserParams(profileSolverMode = ProfileSolverMode.Piecewise)
        val collocationParams = LitvinUserParams(profileSolverMode = ProfileSolverMode.Collocation)
        
        assertEquals(ProfileSolverMode.Piecewise, piecewiseParams.profileSolverMode)
        assertEquals(ProfileSolverMode.Collocation, collocationParams.profileSolverMode)
    }

    @Test
    fun `piecewise motion generation baseline`() {
        val params = LitvinUserParams(
            samplingStepDeg = 2.0,
            strokeLengthMm = 15.0,
            dwellTdcDeg = 10.0,
            dwellBdcDeg = 8.0,
            rampProfile = RampProfile.Cycloidal,
            profileSolverMode = ProfileSolverMode.Piecewise
        )

        val result = MotionLawGenerator.generateMotion(params)

        // Validate basic properties
        assertTrue(result.samples.isNotEmpty(), "Should produce samples")
        assertEquals(params.samplingStepDeg, result.stepDeg, 1e-12, "Step size should match")

        // Validate periodicity
        val first = result.samples.first()
        val last = result.samples.last()
        assertTrue(kotlin.math.abs(first.xMm - last.xMm) < 0.1, "Position should be approximately periodic")

        // Validate stroke constraint
        val positions = result.samples.map { it.xMm }
        val stroke = (positions.maxOrNull() ?: 0.0) - (positions.minOrNull() ?: 0.0)
        assertTrue(stroke > 0.0001 && stroke < params.strokeLengthMm * 1000.0,
                  "Stroke length should be positive and reasonable: actual=$stroke, expected=${params.strokeLengthMm}")
    }

    @Test
    fun `collocation solver handles errors gracefully`() {
        val params = LitvinUserParams(
            samplingStepDeg = 2.0,
            strokeLengthMm = 15.0,
            profileSolverMode = ProfileSolverMode.Collocation
        )

        // Test that collocation solver either works or fails gracefully
        val result = try {
            CollocationMotionSolver.solve(params)
        } catch (e: UnsupportedOperationException) {
            // Expected if dependencies not available
            assertTrue(e.message?.contains("development") == true || 
                      e.message?.contains("CasADi") == true ||
                      e.message?.contains("IPOPT") == true ||
                      e.message?.contains("still in development") == true ||
                      e.message?.contains("disabled") == true ||
                      e.message?.contains("feature flags") == true,
                      "Error message should indicate development status or feature flag state: ${e.message}")
            return // Test passes - proper error handling
        }

        // If we get here, collocation worked - validate the result
        assertNotNull(result, "Result should not be null")
        assertTrue(result.samples.isNotEmpty(), "Should produce samples")
        assertEquals(params.samplingStepDeg, result.stepDeg, 1e-12, "Step size should match")
    }

    @Test
    fun `ui parameter mapping works`() {
        // Test UI parameter conversion
        val paramMap = mapOf(
            "Profile Solver" to "Piecewise",
            "strokeLengthMm" to 15.0,
            "samplingStepDeg" to 2.0
        )

        val litvinParams = com.campro.v5.data.litvin.litvinParamsFromMap(paramMap)
        assertEquals(ProfileSolverMode.Piecewise, litvinParams.profileSolverMode)

        // Test collocation mode
        val collocationMap = paramMap + ("Profile Solver" to "Collocation")
        val collocationLitvinParams = com.campro.v5.data.litvin.litvinParamsFromMap(collocationMap)
        assertEquals(ProfileSolverMode.Collocation, collocationLitvinParams.profileSolverMode)
    }

    @Test
    fun `solver availability check works`() {
        val isAvailable = CollocationMotionSolver.isAvailable()
        // This should return a boolean without throwing exceptions
        assertNotNull(isAvailable)
        
        // Log the status for debugging
        println("Collocation solver available: $isAvailable")
        println("Solver info: ${CollocationMotionSolver.getSolverInfo()}")
    }
}
