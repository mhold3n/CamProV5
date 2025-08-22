package com.campro.v5.animation

import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.RampProfile
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.doubles.shouldBeLessThan
import io.kotest.matchers.shouldBe
import io.kotest.property.Arb
import io.kotest.property.RandomSource
import io.kotest.property.arbitrary.*
import io.kotest.property.forAll
import io.kotest.property.PropTestConfig
import io.kotest.property.Gen
import io.kotest.property.PropertyContext
import com.campro.v5.animation.testutil.MotionLawAssertions
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.PI

// Overload bridge to keep existing call sites: allows forAll(ciSeed, gen) style
suspend fun <A> forAll(seed: Long, genA: Gen<A>, property: suspend PropertyContext.(A) -> Boolean) =
    io.kotest.property.forAll(PropTestConfig(seed = seed), genA, property)

/**
 * Property-based tests for MotionLawGenerator.
 * Tests check for:
 * - No NaN/Inf values
 * - Wrap continuity (x(0)=x(360), v(0)=v(360), a(0)=a(360))
 * - C1/C2 continuity based on profile type
 * - Sampling integrity (360/stepDeg is an integer)
 */
class MotionLawGeneratorPropertyTest : FunSpec({
    
    // Fixed seed for deterministic test behavior in CI (SEED_KOTLIN=1729)
    val ciSeed = 1729L
    
    context("Motion Law Properties") {
        
        // Generator for sampling step sizes that divide 360 evenly
        val samplingStepGen = arbitrary { rs ->
            val possibleSteps = listOf(1.0, 1.2, 1.5, 2.0, 2.4, 3.0, 4.0, 5.0, 6.0, 7.5, 8.0, 9.0, 10.0)
            possibleSteps.random(rs.random)
        }
        
        // Generator for ramp profiles
        val rampProfileGen = arbitrary { rs ->
            RampProfile.values().random(rs.random)
        }
        
        // Generator for angle parameters within reasonable ranges
        val angleGen = Arb.double(min = 0.0, max = 45.0)
        
        // Generator for stroke length
        val strokeLengthGen = Arb.double(min = 10.0, max = 200.0)
        
        // Generator for LitvinUserParams
        val paramsGen = arbitrary { rs: RandomSource ->
            val samplingStep = samplingStepGen.sample(rs).value
            val rampProfile = rampProfileGen.sample(rs).value
            val dwellTdc = angleGen.sample(rs).value / 2.0  // Smaller values for dwells
            val dwellBdc = angleGen.sample(rs).value / 2.0
            val rampBeforeTdc = angleGen.sample(rs).value
            val rampAfterTdc = angleGen.sample(rs).value
            val rampBeforeBdc = angleGen.sample(rs).value
            val rampAfterBdc = angleGen.sample(rs).value
            val strokeLength = strokeLengthGen.sample(rs).value
            
            LitvinUserParams(
                samplingStepDeg = samplingStep,
                rampProfile = rampProfile,
                dwellTdcDeg = dwellTdc,
                dwellBdcDeg = dwellBdc,
                rampBeforeTdcDeg = rampBeforeTdc,
                rampAfterTdcDeg = rampAfterTdc,
                rampBeforeBdcDeg = rampBeforeBdc,
                rampAfterBdcDeg = rampAfterBdc,
                strokeLengthMm = strokeLength
            )
        }
        
        test("no NaN or Inf values in generated motion law") {
            forAll(ciSeed, paramsGen) { params ->
                val m = MotionLawGenerator.generateMotion(params)
                val n = m.samples.size
                val x = DoubleArray(n) { m.samples[it].xMm }
                val v = DoubleArray(n) { m.samples[it].vMmPerOmega }
                val a = DoubleArray(n) { m.samples[it].aMmPerOmega2 }
                try {
                    MotionLawAssertions.assertNoNaNInf(x, v, a)
                    true
                } catch (t: Throwable) {
                    println("[DEBUG_LOG] NaN/Inf detected for params=$params: ${'$'}{t.message}")
                    false
                }
            }
        }
        
        test("wrap continuity - centered derivative checks") {
            forAll(ciSeed, paramsGen) { params ->
                val m = MotionLawGenerator.generateMotion(params)
                val n = m.samples.size
                val theta = DoubleArray(n) { m.samples[it].thetaDeg }
                val x = DoubleArray(n) { m.samples[it].xMm }
                val v = DoubleArray(n) { m.samples[it].vMmPerOmega }
                val a = DoubleArray(n) { m.samples[it].aMmPerOmega2 }
                try {
                    val tol = MotionLawAssertions.Tolerances(
                        relX = 1e-9, absX = 1e-10,
                        relV = 1e-9, absV = 1e-10,
                        relA = 1e-9, absA = 1e-9,
                        neighborhood = 3
                    )
                    MotionLawAssertions.assertWrapContinuityExtrapolated360(theta, x, v, a, tol)
                    true
                } catch (t: Throwable) {
                    println("[DEBUG_LOG] wrap continuity (centered) failure for params=$params: ${'$'}{t.message}")
                    false
                }
            }
        }
        
        test("sampling integrity and monotone theta grid") {
            forAll(ciSeed, paramsGen) { params ->
                val m = MotionLawGenerator.generateMotion(params)
                val n = m.samples.size
                val theta = DoubleArray(n) { m.samples[it].thetaDeg }
                try {
                    MotionLawAssertions.assertSamplingIntegrity(theta, m.stepDeg)
                    true
                } catch (t: Throwable) {
                    println("[DEBUG_LOG] sampling integrity failure for params=$params: ${'$'}{t.message}")
                    false
                }
            }
        }
        
        test("C1/C2 continuity at segment boundaries based on profile type") {
            forAll(ciSeed, paramsGen) { params ->
                val motionLaw = MotionLawGenerator.generateMotion(params)
                val samples = motionLaw.samples
                
                // Function to find indices before and after a theta value
                fun findIndicesBefore(theta: Double): Pair<Int, Int> {
                    var idx = samples.indexOfFirst { it.thetaDeg >= theta }
                    if (idx == -1) {
                        // Boundary may be exactly at 360°, wrap to first sample
                        return Pair(samples.size - 1, 0)
                    }
                    val prevIdx = if (idx > 0) idx - 1 else samples.size - 1
                    return Pair(prevIdx, idx)
                }
                
                // Check acceleration continuity at segment boundaries
                // Segment boundaries depend on parameters
                val dwellTdcEnd = params.dwellTdcDeg
                val rampAfterTdcEnd = dwellTdcEnd + params.rampAfterTdcDeg
                val fixedBudget = params.dwellTdcDeg + params.dwellBdcDeg +
                        params.rampAfterTdcDeg + params.rampBeforeBdcDeg +
                        params.rampAfterBdcDeg + params.rampBeforeTdcDeg
                val freeCv = (360.0 - fixedBudget).coerceAtLeast(0.0)
                val upCv = (freeCv * params.upFraction).coerceAtLeast(0.0)
                val dnCv = (freeCv - upCv).coerceAtLeast(0.0)
                val rampBeforeBdcStart = rampAfterTdcEnd + upCv
                val bdcStart = rampBeforeBdcStart + params.rampBeforeBdcDeg
                val bdcEnd = bdcStart + params.dwellBdcDeg
                val rampAfterBdcEnd = bdcEnd + params.rampAfterBdcDeg
                val rampBeforeTdcStart = rampAfterBdcEnd + dnCv
                
                // Key points to check continuity
                val keyPoints = listOf(
                    dwellTdcEnd, 
                    rampAfterTdcEnd, 
                    rampBeforeBdcStart,
                    bdcStart,
                    bdcEnd,
                    rampAfterBdcEnd,
                    rampBeforeTdcStart
                )
                
                // For each key point, check velocity and acceleration continuity
                val result = keyPoints.all { theta ->
                    // Skip points that are too close to each other
                    if (keyPoints.any { other -> other != theta && abs(other - theta) < params.samplingStepDeg * 1.5 }) {
                        return@all true
                    }
                    
                    val (beforeIdx, afterIdx) = findIndicesBefore(theta)
                    if (beforeIdx < 0 || afterIdx >= samples.size) return@all true
                    
                    val before = samples[beforeIdx]
                    val after = samples[afterIdx]
                    
                    // Skip if points are too far from the boundary
                    if (abs(before.thetaDeg - theta) > params.samplingStepDeg * 1.5 || 
                        abs(after.thetaDeg - theta) > params.samplingStepDeg * 1.5) {
                        return@all true
                    }
                    
                    // C1 continuity: velocity should be continuous for all profiles
                    val vPeak = samples.maxOfOrNull { abs(it.vMmPerOmega) } ?: 1.0
                    val vDiff = abs(before.vMmPerOmega - after.vMmPerOmega) / max(1e-6, vPeak)
                    
                    // C2 continuity: acceleration depends on profile
                    val aPeak = samples.maxOfOrNull { abs(it.aMmPerOmega2) } ?: 1.0
                    val aDiff = abs(before.aMmPerOmega2 - after.aMmPerOmega2) / max(1e-6, aPeak)
                    
                    // Continuity thresholds with ramp-shape-aware scaling:
                    // For S5 near a boundary, v deviation scales ~ (Δθ/Δα)^3 and a deviation ~ (Δθ/Δα)^2.
                    // For S7, orders are 4 and 3 respectively. Use actual grid step and local ramp span.
                    val stepDeg = motionLaw.stepDeg
                    val rampSpanDeg = when {
                        abs(theta - dwellTdcEnd) < 1e-9 || abs(theta - rampAfterTdcEnd) < 1e-9 -> params.rampAfterTdcDeg
                        abs(theta - rampBeforeBdcStart) < 1e-9 || abs(theta - bdcStart) < 1e-9 -> params.rampBeforeBdcDeg
                        abs(theta - bdcEnd) < 1e-9 || abs(theta - rampAfterBdcEnd) < 1e-9 -> params.rampAfterBdcDeg
                        abs(theta - rampBeforeTdcStart) < 1e-9 -> params.rampBeforeTdcDeg
                        else -> max(1.0, stepDeg)
                    }.coerceAtLeast(1e-9)
                    val u = (stepDeg / rampSpanDeg).coerceAtMost(1.0)
                    val vOrder = when (params.rampProfile) {
                        RampProfile.Cycloidal -> 2
                        RampProfile.S5 -> 3
                        RampProfile.S7 -> 4
                    }
                    val aOrder = when (params.rampProfile) {
                        RampProfile.Cycloidal -> 1 // not used; see aTolerance below
                        RampProfile.S5 -> 2
                        RampProfile.S7 -> 3
                    }
                    // Sampling-offset multiplier accounts for boundary falling between sample points
                    val distBeforeSteps = abs(before.thetaDeg - theta) / stepDeg
                    val distAfterSteps = abs(after.thetaDeg - theta) / stepDeg
                    val samplingMultiplier = 1.0 + max(distBeforeSteps, distAfterSteps).coerceAtMost(1.5)
                    val vTolerance = max(1e-5, 50.0 * Math.pow(u, vOrder.toDouble())) * samplingMultiplier
                    val aTolerance = when (params.rampProfile) {
                        RampProfile.Cycloidal -> 1.0 // skip strict C2 check
                        else -> max(1e-5, 50.0 * Math.pow(u, aOrder.toDouble())) * samplingMultiplier
                    }
                    
                    val ok = vDiff < vTolerance && aDiff < aTolerance
                    if (!ok) {
                        println("[DEBUG_LOG] continuity fail @theta=$theta profile=${params.rampProfile} step=${motionLaw.stepDeg} rampSpan=$rampSpanDeg u=${u} vDiff=${vDiff} vTol=${vTolerance} aDiff=${aDiff} aTol=${aTolerance} dBefore=${distBeforeSteps} dAfter=${distAfterSteps}")
                        println("[DEBUG_LOG] before(theta=${before.thetaDeg}, v=${before.vMmPerOmega}, a=${before.aMmPerOmega2}); after(theta=${after.thetaDeg}, v=${after.vMmPerOmega}, a=${after.aMmPerOmega2})")
                        println("[DEBUG_LOG] params=$params")
                    }
                    ok
                }
                
                result
            }
        }
        
        test("samples count matches 360/step") {
            forAll(ciSeed, paramsGen) { params ->
                val motionLaw = MotionLawGenerator.generateMotion(params)
                
                // Expected number of samples (rounded to avoid FP jitter)
                val expectedCount = kotlin.math.round(360.0 / motionLaw.stepDeg).toInt()
                
                // Actual number of samples
                val actualCount = motionLaw.samples.size
                
                expectedCount == actualCount
            }
        }
    }
})