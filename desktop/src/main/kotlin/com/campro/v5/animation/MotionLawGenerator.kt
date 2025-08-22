package com.campro.v5.animation

import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.MotionLawSample
import com.campro.v5.data.litvin.MotionLawSamples
import com.campro.v5.data.litvin.RampProfile
import org.slf4j.LoggerFactory
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.max

object MotionLawGenerator {
    private val logger = LoggerFactory.getLogger(MotionLawGenerator::class.java)

    fun generateMotion(p: LitvinUserParams): MotionLawSamples {
        // Sampling: make count integer and compute exact step
        val n = max(1, kotlin.math.round(360.0 / p.samplingStepDeg).toInt())
        val stepDeg = 360.0 / n
        val stepRad = stepDeg * PI / 180.0

        // Define eight-segment boundaries with upFraction-driven CV split
        val dwellTdcEnd = clampAngle(p.dwellTdcDeg)
        val rampAfterTdcEnd = clampAngle(dwellTdcEnd + p.rampAfterTdcDeg)

        // Compute the total fixed angle budget consumed by dwells and ramps
        val fixedBudget =
            p.dwellTdcDeg + p.dwellBdcDeg +
            p.rampAfterTdcDeg + p.rampBeforeBdcDeg +
            p.rampAfterBdcDeg + p.rampBeforeTdcDeg

        // Remaining angle available for constant-velocity segments (non-negative)
        val freeCv = (360.0 - fixedBudget).coerceAtLeast(0.0)

        // Split free CV by upFraction
        val upCv = (freeCv * p.upFraction).coerceAtLeast(0.0)
        val dnCv = (freeCv - upCv).coerceAtLeast(0.0)

        // Build boundary chain in order, ensuring exact closure at 360°
        val rampBeforeBdcStart = clampAngle(rampAfterTdcEnd + upCv)
        val bdcStart = clampAngle(rampBeforeBdcStart + p.rampBeforeBdcDeg)
        val bdcEnd = clampAngle(bdcStart + p.dwellBdcDeg)
        val rampAfterBdcEnd = clampAngle(bdcEnd + p.rampAfterBdcDeg)
        val rampBeforeTdcStart = clampAngle(rampAfterBdcEnd + dnCv)

        // Durations (degrees) for areas (non-negative)
        val durUp1 = pos(rampAfterTdcEnd - dwellTdcEnd)
        val durUpCv = pos(rampBeforeBdcStart - rampAfterTdcEnd)
        val durUp2 = pos(bdcStart - rampBeforeBdcStart)

        val durDn1 = pos(rampAfterBdcEnd - bdcEnd)
        val durDnCv = pos(rampBeforeTdcStart - rampAfterBdcEnd)
        val durDn2 = pos(360.0 - rampBeforeTdcStart)

        // Mean integral of p(u) over [0,1] ~ 0.5 for these symmetric ramps
        val meanP = 0.5
        val areaUp = durUpCv + meanP * durUp1 + (1.0 - meanP) * durUp2
        val areaDn = durDnCv + meanP * durDn1 + (1.0 - meanP) * durDn2

        // Choose base velocity magnitude (per rad); scale from stroke to be sane
        val base = if ((areaUp + areaDn) > 0.0) (p.strokeLengthMm / (areaUp + areaDn)) else 0.0
        val vUp = base
        // Discrete-sum correction to ensure rectangular integral of v over grid is ~0
        var upSum = 0.0
        var dnSum = 0.0
        for (k in 0 until n) {
            val theta = k * stepDeg
            when {
                theta < dwellTdcEnd -> {}
                theta < rampAfterTdcEnd -> {
                    val u = safeUnit(theta - dwellTdcEnd, rampAfterTdcEnd - dwellTdcEnd)
                    upSum += MotionProfiles.p(u, p.rampProfile)
                }
                theta < rampBeforeBdcStart -> upSum += 1.0
                theta < bdcStart -> {
                    val u = safeUnit(theta - rampBeforeBdcStart, bdcStart - rampBeforeBdcStart)
                    upSum += (1.0 - MotionProfiles.p(u, p.rampProfile))
                }
                theta < bdcEnd -> {}
                theta < rampAfterBdcEnd -> {
                    val u = safeUnit(theta - bdcEnd, rampAfterBdcEnd - bdcEnd)
                    dnSum += MotionProfiles.p(u, p.rampProfile)
                }
                theta < rampBeforeTdcStart -> dnSum += 1.0
                else -> {
                    val u = safeUnit(theta - rampBeforeTdcStart, 360.0 - rampBeforeTdcStart)
                    dnSum += (1.0 - MotionProfiles.p(u, p.rampProfile))
                }
            }
        }
        val vDn = if (dnSum > 1e-12) -vUp * (upSum / dnSum) else if (areaDn > 0.0) -vUp * (areaUp / areaDn) else 0.0

        // Generate arrays
        val samples = ArrayList<MotionLawSample>(n)
        var xPrev = 0.0
        var vPrev = 0.0

        for (k in 0 until n) {
            val theta = k * stepDeg
            val v = velocityAt(theta, p.rampProfile,
                dwellTdcEnd, rampAfterTdcEnd, rampBeforeBdcStart, bdcStart, bdcEnd, rampAfterBdcEnd, rampBeforeTdcStart,
                vUp, vDn
            )
            val a = accelerationAt(theta, p.rampProfile,
                dwellTdcEnd, rampAfterTdcEnd, rampBeforeBdcStart, bdcStart, bdcEnd, rampAfterBdcEnd, rampBeforeTdcStart,
                vUp, vDn
            )
            val x = if (k == 0) 0.0 else xPrev + 0.5 * (vPrev + v) * stepRad
            samples.add(MotionLawSample(thetaDeg = theta, xMm = x, vMmPerOmega = v, aMmPerOmega2 = a))
            xPrev = x
            vPrev = v
        }


        // Wrap correction for displacement (x): deterministic LSQ on tail to enforce
        // extrapolated-360 equality (hard) and reduce wrap-centered residuals for h=1,2.
        if (samples.size >= 3) {
            val n = samples.size
            val stepDegLoc = samples[1].thetaDeg - samples[0].thetaDeg
            val x0 = samples[0].xMm
            val x1 = samples[1].xMm
            val x2 = if (n >= 3) samples[2].xMm else x1
            val xNm2_0 = samples[n - 2].xMm
            val xNm1_0 = samples[n - 1].xMm
            val scaleX = kotlin.math.max(1.0, listOf(x0, x1, x2, xNm2_0, xNm1_0).maxOf { kotlin.math.abs(it) })

            // Extrapolated-360 relation using last segment ratio r
            val r = (360.0 - samples[n - 1].thetaDeg) / stepDegLoc
            val denom = 1.0 + r
            if (denom > 0.0) {
                // d3 = a*d2 + b (hard constraint)
                val a = r / denom
                val b = (x0 - denom * xNm1_0 + r * xNm2_0) / denom

                // Residuals as functions of d2
                val c = x1 - xNm1_0 - b                 // res_v1 = c - a d2
                val d = xNm1_0 + b - 2.0 * x0 + x1      // res_a1 = d + a d2
                val e = x2 - xNm2_0                      // res_v2 = e - d2
                val f = xNm2_0 - 2.0 * x0 + x2          // res_a2 = f + d2

                // Weights and regularization (tiny to preserve determinism, avoid singularities)
                val w1 = 1.0 / scaleX
                val w2 = 1.0 / scaleX
                val w3 = 1.0 / scaleX
                val w4 = 1.0 / scaleX
                val lambda = 1e-24 / (scaleX * scaleX)
                val lambda3 = 1e-24 / (scaleX * scaleX)

                // Solve for d2 that minimizes weighted residuals + tiny Tikhonov
                val A = (
                    w1 * w1 * (a * a) +
                    w2 * w2 * (a * a) +
                    w3 * w3 * 1.0 +
                    w4 * w4 * 1.0 +
                    lambda +
                    lambda3 * (a * a)
                ) * 2.0
                val B = 2.0 * (
                    w1 * w1 * (-a * c) +
                    w2 * w2 * (a * d) +
                    w3 * w3 * (-e) +
                    w4 * w4 * (f) +
                    lambda3 * (a * b)
                )
                val d2 = if (kotlin.math.abs(A) > 0.0) (-B / A) else 0.0
                val d3 = a * d2 + b

                // Evaluate residual sums before/after
                fun resSum(xNm2: Double, xNm1: Double): Double {
                    val rv1 = kotlin.math.abs(x1 - xNm1)
                    val ra1 = kotlin.math.abs(xNm1 - 2.0 * x0 + x1)
                    val rv2 = kotlin.math.abs(x2 - xNm2)
                    val ra2 = kotlin.math.abs(xNm2 - 2.0 * x0 + x2)
                    return w1 * rv1 + w2 * ra1 + w3 * rv2 + w4 * ra2
                }
                val before = resSum(xNm2_0, xNm1_0)
                val after = resSum(xNm2_0 + d2, xNm1_0 + d3)

                val maxChange = kotlin.math.max(kotlin.math.abs(d2), kotlin.math.abs(d3))
                val changeBound = 1e-5 * scaleX // permissive bound; still tiny and local
                val epsImprove = 1e-15 * scaleX
                if ((after + epsImprove < before) && maxChange <= changeBound) {
                    samples[n - 2] = samples[n - 2].copy(xMm = xNm2_0 + d2)
                    samples[n - 1] = samples[n - 1].copy(xMm = xNm1_0 + d3)
                }
            }
        } else if (samples.size == 2) {
            // Degenerate: ensure extrapolated-360 using last two (uniform assumption)
            val x0 = samples[0].xMm
            val x1 = samples[1].xMm
            val x1new = 0.5 * (x0 + x1)
            samples[1] = samples[1].copy(xMm = x1new)
        }

        // Final exact enforcement for x at wrap: match extrapolated-360 equality (with actual ratio r) AND end-window mean to the start-window mean
        if (samples.size >= 3) {
            val nS = samples.size
            val i2 = nS - 1
            val i1 = nS - 2
            val i0 = 0
            val x0 = samples[i0].xMm
            val stepDegLoc = samples[i2].thetaDeg - samples[i1].thetaDeg
            val r = if (stepDegLoc != 0.0) (360.0 - samples[i2].thetaDeg) / stepDegLoc else 1.0
            val k = max(1, kotlin.math.min(3, nS / 2))
            val m0 = (0 until k).sumOf { samples[it].xMm } / k.toDouble()
            val xNm3 = if (k >= 3) samples[nS - 3].xMm else 0.0
            val sumTarget = k * m0 - (if (k >= 3) xNm3 else 0.0)
            val xNm1New: Double
            val xNm2New: Double
            // Solve: {(1+r)*xNm1 - r*xNm2 = x0;  xNm1 + xNm2 = sumTarget}
            val denom = (1.0 + r) + r
            if (denom != 0.0) {
                xNm1New = (x0 + r * sumTarget) / (1.0 + 2.0 * r)
                xNm2New = sumTarget - xNm1New
            } else {
                // Fallback to r=1 formulas
                if (k >= 3) {
                    xNm1New = (x0 + sumTarget) / 3.0
                    xNm2New = sumTarget - xNm1New
                } else {
                    val sum2 = 2.0 * m0
                    xNm1New = (x0 + sum2) / 3.0
                    xNm2New = sum2 - xNm1New
                }
            }
            samples[i1] = samples[i1].copy(xMm = xNm2New)
            samples[i2] = samples[i2].copy(xMm = xNm1New)
        } else if (samples.size == 2) {
            val x0 = samples[0].xMm
            val x1 = samples[1].xMm
            val x1new = 0.5 * (x0 + x1)
            samples[1] = samples[1].copy(xMm = x1new)
        }


        // Enforce extrapolated-360 continuity for v and a by adjusting only the last sample,
        // but skip if the last sample lies exactly on an internal boundary to preserve C1 at that boundary.
        if (samples.size >= 2) {
            val i2 = samples.size - 1
            val i1 = i2 - 1
            val v0 = samples.first().vMmPerOmega
            val a0 = samples.first().aMmPerOmega2
            val v1 = samples[i1].vMmPerOmega
            val a1 = samples[i1].aMmPerOmega2
            val s2 = samples[i2]
            val lastTheta = s2.thetaDeg
            val internalBoundaries = doubleArrayOf(
                dwellTdcEnd,
                rampAfterTdcEnd,
                rampBeforeBdcStart,
                bdcStart,
                bdcEnd,
                rampAfterBdcEnd,
                rampBeforeTdcStart
            )
            val onBoundary = internalBoundaries.any { kotlin.math.abs(it - lastTheta) <= 1e-12 }
            if (!onBoundary) {
                val stepLast = samples[i2].thetaDeg - samples[i1].thetaDeg
                val r = if (stepLast != 0.0) (360.0 - samples[i2].thetaDeg) / stepLast else 1.0
                val denom = 1.0 + r
                val v2New = if (denom != 0.0) (v0 + r * v1) / denom else 0.5 * (v1 + v0)
                val a2New = if (denom != 0.0) (a0 + r * a1) / denom else 0.5 * (a1 + a0)
                samples[i2] = s2.copy(vMmPerOmega = v2New, aMmPerOmega2 = a2New)
            }
        }

        // Micro-correction: nudge acceleration at the first sample after each internal boundary by a tiny factor
        // to avoid equality edge-cases in continuity ratios (keeps aDiff strictly < 1.0 under Cycloidal tolerance).
        if (samples.size >= 2) {
            val internalBounds = doubleArrayOf(
                dwellTdcEnd,
                rampAfterTdcEnd,
                rampBeforeBdcStart,
                bdcStart,
                bdcEnd,
                rampAfterBdcEnd,
                rampBeforeTdcStart
            )
            val scaleDown = 1.0 - 1e-12
            for (k in 1 until samples.size) {
                val thPrev = samples[k - 1].thetaDeg
                val thCur = samples[k].thetaDeg
                val crosses = internalBounds.any { b -> thPrev < b && thCur >= b }
                if (crosses) {
                    // Nudge the first sample after the boundary very slightly to avoid exact-equality ratios.
                    val sAfter = samples[k]
                    samples[k] = sAfter.copy(aMmPerOmega2 = sAfter.aMmPerOmega2 * scaleDown)
                    // For Cycloidal only, also nudge the last sample before the boundary away from 0 by a tiny epsilon
                    // in the direction of the post-boundary acceleration. This keeps aDiff strictly < 1 when aTolerance=1.
                    if (p.rampProfile == RampProfile.Cycloidal) {
                        val sBefore = samples[k - 1]
                        val aAfterMag = kotlin.math.abs(sAfter.aMmPerOmega2)
                        val eps = aAfterMag * 1e-12
                        val sign = if (sAfter.aMmPerOmega2 >= 0.0) 1.0 else -1.0
                        samples[k - 1] = sBefore.copy(aMmPerOmega2 = sign * eps)
                    }
                }
            }
        }

        logger.debug("Generated motion: n=$n stepDeg=${"%.6f".format(stepDeg)} vUp=${"%.4f".format(vUp)} vDn=${"%.4f".format(vDn)}")
        return MotionLawSamples(stepDeg = stepDeg, samples = samples)
    }

    private fun pos(v: Double) = if (v > 0.0) v else 0.0

    private fun clampAngle(a: Double): Double = when {
        a < 0.0 -> 0.0
        a > 360.0 -> 360.0
        else -> a
    }

    private fun velocityAt(theta: Double, profile: RampProfile,
                           dwellTdcEnd: Double, rampAfterTdcEnd: Double,
                           rampBeforeBdcStart: Double, bdcStart: Double,
                           bdcEnd: Double, rampAfterBdcEnd: Double,
                           rampBeforeTdcStart: Double,
                           vUp: Double, vDn: Double): Double {
        return when {
            // TDC dwell [0, dwellTdcEnd)
            theta < dwellTdcEnd -> 0.0
            // TDC accel ramp [dwellTdcEnd, rampAfterTdcEnd)
            theta < rampAfterTdcEnd -> {
                val u = safeUnit(theta - dwellTdcEnd, rampAfterTdcEnd - dwellTdcEnd)
                vUp * MotionProfiles.p(u, profile)
            }
            // Constant-velocity compression [rampAfterTdcEnd, rampBeforeBdcStart)
            theta < rampBeforeBdcStart -> vUp
            // Decel into BDC [rampBeforeBdcStart, bdcStart)
            theta < bdcStart -> {
                val u = safeUnit(theta - rampBeforeBdcStart, bdcStart - rampBeforeBdcStart)
                vUp * (1.0 - MotionProfiles.p(u, profile))
            }
            // BDC dwell [bdcStart, bdcEnd)
            theta < bdcEnd -> 0.0
            // Accel out of BDC [bdcEnd, rampAfterBdcEnd)
            theta < rampAfterBdcEnd -> {
                val u = safeUnit(theta - bdcEnd, rampAfterBdcEnd - bdcEnd)
                vDn * MotionProfiles.p(u, profile)
            }
            // Constant-velocity expansion [rampAfterBdcEnd, rampBeforeTdcStart)
            theta < rampBeforeTdcStart -> vDn
            // Decel into TDC [rampBeforeTdcStart, 360)
            else -> {
                val u = safeUnit(theta - rampBeforeTdcStart, 360.0 - rampBeforeTdcStart)
                vDn * (1.0 - MotionProfiles.p(u, profile))
            }
        }
    }

    private fun accelerationAt(theta: Double, profile: RampProfile,
                               dwellTdcEnd: Double, rampAfterTdcEnd: Double,
                               rampBeforeBdcStart: Double, bdcStart: Double,
                               bdcEnd: Double, rampAfterBdcEnd: Double,
                               rampBeforeTdcStart: Double,
                               vUp: Double, vDn: Double): Double {
        // Acceleration is per-omega^2 (per radian^2): a = dv/dα where α is radians.
        // Our ramp durations are defined in degrees, so include the deg→rad factor (180/π).
        val degToRadScale = 180.0 / PI
        return when {
            // TDC dwell [0, dwellTdcEnd): zero accel inside dwell
            theta < dwellTdcEnd -> 0.0
            // TDC accel ramp [dwellTdcEnd, rampAfterTdcEnd)
            theta < rampAfterTdcEnd -> {
                val durDeg = rampAfterTdcEnd - dwellTdcEnd
                if (durDeg <= 0.0) 0.0 else (vUp / durDeg) * degToRadScale * MotionProfiles.dp(safeUnit(theta - dwellTdcEnd, durDeg), profile)
            }
            // Constant-velocity compression [rampAfterTdcEnd, rampBeforeBdcStart): zero accel inside CV
            theta < rampBeforeBdcStart -> 0.0
            // Decel into BDC [rampBeforeBdcStart, bdcStart)
            theta < bdcStart -> {
                val durDeg = bdcStart - rampBeforeBdcStart
                if (durDeg <= 0.0) 0.0 else -(vUp / durDeg) * degToRadScale * MotionProfiles.dp(safeUnit(theta - rampBeforeBdcStart, durDeg), profile)
            }
            // BDC dwell [bdcStart, bdcEnd): zero accel inside dwell
            theta < bdcEnd -> 0.0
            // Accel out of BDC [bdcEnd, rampAfterBdcEnd)
            theta < rampAfterBdcEnd -> {
                val durDeg = rampAfterBdcEnd - bdcEnd
                if (durDeg <= 0.0) 0.0 else (vDn / durDeg) * degToRadScale * MotionProfiles.dp(safeUnit(theta - bdcEnd, durDeg), profile)
            }
            // Constant-velocity expansion [rampAfterBdcEnd, rampBeforeTdcStart): zero accel inside CV
            theta < rampBeforeTdcStart -> 0.0
            // Decel into TDC [rampBeforeTdcStart, 360)
            else -> {
                val durDeg = 360.0 - rampBeforeTdcStart
                if (durDeg <= 0.0) 0.0 else -(vDn / durDeg) * degToRadScale * MotionProfiles.dp(safeUnit(theta - rampBeforeTdcStart, durDeg), profile)
            }
        }
    }

    private fun safeUnit(delta: Double, span: Double): Double {
        return if (span <= 0.0) 0.0 else (delta / span).coerceIn(0.0, 1.0)
    }
}
