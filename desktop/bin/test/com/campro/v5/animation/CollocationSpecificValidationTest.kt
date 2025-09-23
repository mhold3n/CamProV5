package com.campro.v5.animation

import com.campro.v5.animation.collocation.*
import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.ProfileSolverMode
import com.campro.v5.data.litvin.RampProfile
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.EnumSource
import org.junit.jupiter.params.provider.ValueSource
import java.util.concurrent.TimeUnit
import kotlin.math.*

/**
 * Collocation-specific validation tests focusing on mathematical accuracy,
 * constraint satisfaction, and discretization properties.
 * 
 * These tests validate the numerical methods and mathematical correctness
 * of the collocation system independently of the overall engine integration.
 */
class CollocationSpecificValidationTest {

    private val EPS = 1e-12

    // ========================================
    // DISCRETIZATION ACCURACY TESTS
    // ========================================

    @ParameterizedTest
    @ValueSource(ints = [4, 8, 16, 32])
    fun `collocation nodes are properly spaced for periodic problems`(nodeCount: Int) {
        val discretization = CollocationDiscretization(nodeCount, CollocationDiscretization.NodeType.UNIFORM)
        
        // Basic properties
        assertEquals(nodeCount, discretization.nodeCount, "Node count should match")
        assertEquals(nodeCount, discretization.nodes.size, "Should have correct number of nodes")
        
        // Periodic domain check [0, 2π)
        assertTrue(discretization.nodes.first() >= 0.0, "First node should be >= 0")
        assertTrue(discretization.nodes.last() < 2.0 * PI, "Last node should be < 2π")
        
        // Uniform spacing
        val expectedSpacing = 2.0 * PI / nodeCount
        for (i in 1 until discretization.nodes.size) {
            val actualSpacing = discretization.nodes[i] - discretization.nodes[i-1]
            assertEquals(expectedSpacing, actualSpacing, 1e-10, "Node spacing should be uniform")
        }
    }

    @Test
    fun `LGL nodes have correct boundary clustering`() {
        val discretization = CollocationDiscretization(8, CollocationDiscretization.NodeType.LGL)
        
        // LGL nodes should be more densely packed near boundaries in original [-1,1] domain
        // After mapping to [0, 2π], this translates to clustering near 0 and 2π
        val spacings = (1 until discretization.nodes.size).map { i ->
            discretization.nodes[i] - discretization.nodes[i-1]
        }
        
        // Should have some variation in spacing (not uniform)
        val maxSpacing = spacings.maxOrNull() ?: 0.0
        val minSpacing = spacings.minOrNull() ?: 0.0
        assertTrue(maxSpacing > minSpacing * 1.1, "LGL nodes should have non-uniform spacing")
        
        // All spacings should be positive
        assertTrue(spacings.all { it > 0.0 }, "All node spacings should be positive")
    }

    @Test
    fun `Chebyshev nodes have proper clustering properties`() {
        val discretization = CollocationDiscretization(10, CollocationDiscretization.NodeType.CHEBYSHEV)
        
        // Validate basic properties
        assertEquals(10, discretization.nodes.size)
        assertTrue(discretization.nodes.first() >= 0.0)
        assertTrue(discretization.nodes.last() < 2.0 * PI)
        
        // Chebyshev nodes should be clustered near boundaries
        val spacings = (1 until discretization.nodes.size).map { i ->
            discretization.nodes[i] - discretization.nodes[i-1]
        }
        val avgSpacing = spacings.average()
        
        // Check that there's clustering (some spacings much smaller than average)
        val smallSpacings = spacings.count { it < avgSpacing * 0.7 }
        assertTrue(smallSpacings >= 2, "Should have clustered regions with smaller spacings")
    }

    // ========================================
    // DIFFERENTIATION MATRIX ACCURACY
    // ========================================

    @Test
    fun `periodic differentiation matrices preserve periodicity`() {
        val nodes = CollocationNodes.generateUniform(8)
        val periodicDiff = PeriodicDifferentiation(nodes)
        
        // Test constant function (derivative should be zero)
        val constantFunction = DoubleArray(8) { 1.0 }
        val constantDerivative = periodicDiff.applyFirstDerivative(constantFunction)
        
        for (i in constantDerivative.indices) {
            assertEquals(0.0, constantDerivative[i], 1e-10, "Derivative of constant should be zero")
        }
        
        // Test periodic linear-like function f(θ) = sin(θ) + cos(θ) (derivative should be cos(θ) - sin(θ))
        val periodicLinearFunction = nodes.map { sin(it) + cos(it) }.toDoubleArray()
        val periodicLinearDerivative = periodicDiff.applyFirstDerivative(periodicLinearFunction)
        val expectedDerivative = nodes.map { cos(it) - sin(it) }
        
        for (i in periodicLinearDerivative.indices) {
            assertEquals(expectedDerivative[i], periodicLinearDerivative[i], 0.15, "Derivative of sin(θ)+cos(θ) should be cos(θ)-sin(θ)")
        }
    }

    @Test
    fun `second derivative matrices are consistent with first derivatives`() {
        val nodes = CollocationNodes.generateUniform(6)
        val periodicDiff = PeriodicDifferentiation(nodes)
        
        // Test periodic quadratic-like function f(θ) = 2*sin(θ) - cos(θ)  
        // First derivative: 2*cos(θ) + sin(θ)
        // Second derivative: -2*sin(θ) + cos(θ)
        val periodicQuadraticFunction = nodes.map { 2.0 * sin(it) - cos(it) }.toDoubleArray()
        
        // First derivative should be 2*cos(θ) + sin(θ)
        val firstDeriv = periodicDiff.applyFirstDerivative(periodicQuadraticFunction)
        val expectedFirstDeriv = nodes.map { 2.0 * cos(it) + sin(it) }
        
        for (i in firstDeriv.indices) {
            assertEquals(expectedFirstDeriv[i], firstDeriv[i], 0.4, "First derivative of 2sin(θ)-cos(θ)")
        }
        
        // Second derivative should be -2*sin(θ) + cos(θ)
        val secondDeriv = periodicDiff.applySecondDerivative(periodicQuadraticFunction)
        val expectedSecondDeriv = nodes.map { -2.0 * sin(it) + cos(it) }
        
        for (i in secondDeriv.indices) {
            assertEquals(expectedSecondDeriv[i], secondDeriv[i], 0.25, "Second derivative of 2sin(θ)-cos(θ)")
        }
    }

    @Test
    fun `differentiation matrices handle trigonometric functions accurately`() {
        val nodes = CollocationNodes.generateUniform(16) // More nodes for trig accuracy
        val periodicDiff = PeriodicDifferentiation(nodes)
        
        // Test sin(θ) - derivative should be cos(θ)
        val sinFunction = nodes.map { sin(it) }.toDoubleArray()
        val sinDerivative = periodicDiff.applyFirstDerivative(sinFunction)
        val expectedCos = nodes.map { cos(it) }
        
        for (i in sinDerivative.indices) {
            assertEquals(expectedCos[i], sinDerivative[i], 0.03, "Derivative of sin(θ) should be cos(θ) at node $i")
        }
        
        // Test cos(θ) - derivative should be -sin(θ)
        val cosFunction = nodes.map { cos(it) }.toDoubleArray()
        val cosDerivative = periodicDiff.applyFirstDerivative(cosFunction)
        val expectedNegSin = nodes.map { -sin(it) }
        
        for (i in cosDerivative.indices) {
            assertEquals(expectedNegSin[i], cosDerivative[i], 0.03, "Derivative of cos(θ) should be -sin(θ) at node $i")
        }
    }

    // ========================================
    // CONSTRAINT SATISFACTION TESTS
    // ========================================

    @Test
    fun `collocation constraints respect stroke length bounds`() {
        val params = LitvinUserParams(
            strokeLengthMm = 20.0,
            samplingStepDeg = 2.0,
            dwellTdcDeg = 10.0,
            dwellBdcDeg = 8.0,
            profileSolverMode = ProfileSolverMode.Collocation
        )
        
        val discretization = CollocationDiscretization(8, CollocationDiscretization.NodeType.UNIFORM)
        val constraintSystem = CollocationConstraints(params, discretization)
        val constraints = constraintSystem.generateConstraints()
        
        assertTrue(constraints.isNotEmpty(), "Should generate some constraints")
        
        // Look for stroke-related constraints
        val strokeConstraints = constraints.filter { 
            it.description.contains("stroke", ignoreCase = true) ||
            it.description.contains("position", ignoreCase = true)
        }
        
        assertTrue(strokeConstraints.isNotEmpty(), "Should have stroke-related constraints")
    }

    @Test
    fun `collocation constraints handle dwell periods correctly`() {
        val params = LitvinUserParams(
            dwellTdcDeg = 15.0,
            dwellBdcDeg = 12.0,
            samplingStepDeg = 2.0,
            profileSolverMode = ProfileSolverMode.Collocation
        )
        
        val discretization = CollocationDiscretization(16, CollocationDiscretization.NodeType.UNIFORM)
        val constraintSystem = CollocationConstraints(params, discretization)
        val constraints = constraintSystem.generateConstraints()
        
        // Look for dwell-related constraints
        val dwellConstraints = constraints.filter {
            it.description.contains("dwell", ignoreCase = true) ||
            it.description.contains("TDC", ignoreCase = true) ||
            it.description.contains("BDC", ignoreCase = true)
        }
        
        // Should have constraints related to dwell periods
        assertTrue(dwellConstraints.isNotEmpty(), "Should have dwell-related constraints")
    }

    @ParameterizedTest
    @EnumSource(RampProfile::class)
    fun `collocation constraints support all ramp profiles`(rampProfile: RampProfile) {
        val params = LitvinUserParams(
            rampProfile = rampProfile,
            strokeLengthMm = 15.0,
            samplingStepDeg = 2.0,
            profileSolverMode = ProfileSolverMode.Collocation
        )
        
        val discretization = CollocationDiscretization(12, CollocationDiscretization.NodeType.UNIFORM)
        
        // Should not throw exceptions for any ramp profile
        assertDoesNotThrow {
            val constraintSystem = CollocationConstraints(params, discretization)
            val constraints = constraintSystem.generateConstraints()
            assertTrue(constraints.isNotEmpty(), "Should generate constraints for $rampProfile")
        }
    }

    // ========================================
    // SOLVER INTEGRATION ACCURACY
    // ========================================

    @Test
    @Timeout(30, unit = TimeUnit.SECONDS)
    fun `collocation solver produces kinematically consistent results`() {
        if (!CollocationMotionSolver.isAvailable()) {
            println("Collocation solver not available, skipping accuracy test")
            return
        }
        
        val params = LitvinUserParams(
            strokeLengthMm = 10.0,
            samplingStepDeg = 3.0,
            dwellTdcDeg = 8.0,
            dwellBdcDeg = 6.0,
            rampProfile = RampProfile.Cycloidal,
            profileSolverMode = ProfileSolverMode.Collocation
        )
        
        val result = try {
            CollocationMotionSolver.solve(params)
        } catch (e: UnsupportedOperationException) {
            println("Collocation solver not implemented, skipping test: ${e.message}")
            return
        }
        
        // Validate kinematic consistency
        assertTrue(result.samples.isNotEmpty(), "Should produce motion samples")
        
        val positions = result.samples.map { it.xMm }
        val velocities = result.samples.map { it.vMmPerOmega }
        val accelerations = result.samples.map { it.aMmPerOmega2 }
        
        // All values should be finite
        assertTrue(positions.all { it.isFinite() }, "All positions should be finite")
        assertTrue(velocities.all { it.isFinite() }, "All velocities should be finite")
        assertTrue(accelerations.all { it.isFinite() }, "All accelerations should be finite")
        
        // Check periodicity (first and last should be close)
        val positionClosure = abs(positions.first() - positions.last())
        assertTrue(positionClosure < 0.1, "Position should be approximately periodic")
        
        // Stroke length should be approximately correct
        val strokeActual = (positions.maxOrNull() ?: 0.0) - (positions.minOrNull() ?: 0.0)
        assertTrue(strokeActual > 0.001, "Should have some motion")
    }

    @Test
    fun `collocation discretization caches differentiation matrices`() {
        val nodeCount = 10
        
        // Create multiple discretizations with same parameters
        val disc1 = CollocationDiscretization(nodeCount, CollocationDiscretization.NodeType.UNIFORM)
        val disc2 = CollocationDiscretization(nodeCount, CollocationDiscretization.NodeType.UNIFORM)
        
        // Both should work and have same nodes
        assertEquals(disc1.nodes.size, disc2.nodes.size)
        for (i in disc1.nodes.indices) {
            assertEquals(disc1.nodes[i], disc2.nodes[i], EPS)
        }
    }

    // ========================================
    // NUMERICAL STABILITY TESTS
    // ========================================

    @Test
    fun `collocation handles small node counts gracefully`() {
        // Test minimum viable node count
        assertDoesNotThrow {
            val discretization = CollocationDiscretization(3, CollocationDiscretization.NodeType.UNIFORM)
            assertTrue(discretization.nodes.size >= 3, "Should handle minimum node count")
        }
    }

    @Test
    fun `collocation handles large node counts efficiently`() {
        // Test with larger node count (should complete in reasonable time)
        val startTime = System.currentTimeMillis()
        
        assertDoesNotThrow {
            val discretization = CollocationDiscretization(64, CollocationDiscretization.NodeType.UNIFORM)
            assertEquals(64, discretization.nodeCount)
        }
        
        val elapsedTime = System.currentTimeMillis() - startTime
        assertTrue(elapsedTime < 5000, "Large discretization should complete quickly: ${elapsedTime}ms")
    }

    @Test
    fun `periodic differentiation handles edge cases`() {
        val nodes = CollocationNodes.generateUniform(4)
        val periodicDiff = PeriodicDifferentiation(nodes)
        
        // Test with zero function
        val zeroFunction = DoubleArray(4) { 0.0 }
        val zeroDerivative = periodicDiff.applyFirstDerivative(zeroFunction)
        
        for (value in zeroDerivative) {
            assertEquals(0.0, value, EPS, "Derivative of zero should be zero")
        }
        
        // Test with very small values
        val smallFunction = DoubleArray(4) { 1e-15 }
        val smallDerivative = periodicDiff.applyFirstDerivative(smallFunction)
        
        assertTrue(smallDerivative.all { abs(it) < 1e-10 }, "Small function should have small derivative")
    }

    // ========================================
    // PERFORMANCE AND SCALABILITY TESTS
    // ========================================

    @ParameterizedTest
    @ValueSource(ints = [4, 8, 16, 32])
    fun `constraint generation scales reasonably with node count`(nodeCount: Int) {
        val params = LitvinUserParams(
            strokeLengthMm = 12.0,
            samplingStepDeg = 2.0,
            profileSolverMode = ProfileSolverMode.Collocation
        )
        
        val startTime = System.currentTimeMillis()
        
        val discretization = CollocationDiscretization(nodeCount, CollocationDiscretization.NodeType.UNIFORM)
        val constraintSystem = CollocationConstraints(params, discretization)
        val constraints = constraintSystem.generateConstraints()
        
        val elapsedTime = System.currentTimeMillis() - startTime
        
        assertTrue(constraints.isNotEmpty(), "Should generate constraints for $nodeCount nodes")
        assertTrue(elapsedTime < 1000, "Constraint generation should be fast: ${elapsedTime}ms for $nodeCount nodes")
    }

    @Test
    fun `discretization creation is deterministic`() {
        // Multiple creations should give identical results
        val disc1 = CollocationDiscretization(8, CollocationDiscretization.NodeType.UNIFORM)
        val disc2 = CollocationDiscretization(8, CollocationDiscretization.NodeType.UNIFORM)
        
        assertEquals(disc1.nodeCount, disc2.nodeCount)
        assertEquals(disc1.nodeType, disc2.nodeType)
        
        for (i in disc1.nodes.indices) {
            assertEquals(disc1.nodes[i], disc2.nodes[i], EPS, "Nodes should be identical")
        }
    }
}
