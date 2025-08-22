package com.campro.v5.animation

import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.RampProfile
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import com.campro.v5.animation.testutil.MotionLawAssertions
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

class MotionLawContinuityTest {

    @Test
    fun periodicity_wrap_and_dwell_zeros_for_all_profiles() {
        val profiles = listOf(RampProfile.Cycloidal, RampProfile.S5, RampProfile.S7)
        for (profile in profiles) {
            val p = LitvinUserParams(
                rampProfile = profile,
                samplingStepDeg = 2.0, // reasonably fine for boundary checks
                dwellTdcDeg = 30.0,
                dwellBdcDeg = 30.0,
                rampAfterTdcDeg = 20.0,
                rampBeforeBdcDeg = 20.0,
                rampAfterBdcDeg = 20.0,
                rampBeforeTdcDeg = 20.0,
            )
            val motion = MotionLawGenerator.generateMotion(p)
            val n = motion.samples.size
            assertTrue(n > 0)
            val step = motion.stepDeg
            // Deterministic sampling: 360/step is integer within tolerance
            val stepsDouble = 360.0 / step
            assertEquals(stepsDouble.roundToInt().toDouble(), stepsDouble, 1e-9)

            fun at(i: Int) = ((i % n) + n) % n
            val xs = DoubleArray(n) { motion.samples[it].xMm }
            val vs = DoubleArray(n) { motion.samples[it].vMmPerOmega }
            val as_ = DoubleArray(n) { motion.samples[it].aMmPerOmega2 }
            val theta = DoubleArray(n) { motion.samples[it].thetaDeg }


            // Dwell zero enforcement within dwell spans (allow small numeric epsilon)
            // Compute dwell boundaries using upFraction-driven boundary chain
            val dwellTdcEnd = p.dwellTdcDeg
            val rampAfterTdcEnd = dwellTdcEnd + p.rampAfterTdcDeg
            val fixedBudget = p.dwellTdcDeg + p.dwellBdcDeg +
                    p.rampAfterTdcDeg + p.rampBeforeBdcDeg +
                    p.rampAfterBdcDeg + p.rampBeforeTdcDeg
            val freeCv = (360.0 - fixedBudget).coerceAtLeast(0.0)
            val upCv = (freeCv * p.upFraction).coerceAtLeast(0.0)
            val rampBeforeBdcStart = rampAfterTdcEnd + upCv
            val bdcStart = rampBeforeBdcStart + p.rampBeforeBdcDeg
            val bdcEnd = bdcStart + p.dwellBdcDeg
            fun inRange(th: Double, start: Double, end: Double): Boolean = th >= start - 1e-9 && th < end - 1e-9
            for (i in 0 until n) {
                val th = motion.samples[i].thetaDeg
                if (inRange(th, 0.0, p.dwellTdcDeg) || inRange(th, bdcStart, bdcEnd)) {
                    assertEquals(0.0, vs[i], 1e-9, "v should be ~zero in dwells @θ=$th (profile=$profile)")
                    assertEquals(0.0, as_[i], 1e-6, "a should be ~zero in dwells @θ=$th (profile=$profile)")
                }
            }

            // Boundary smoothness at segment joins: ensure no spikes (jerk proxy bounded)
            // Approximate jerk via central differences of acceleration over θ
            val deg2rad = Math.PI / 180.0
            val jerk = DoubleArray(n) {
                val im1 = at(it - 1)
                val ip1 = at(it + 1)
                val da_ddeg = (as_[ip1] - as_[im1]) / (2.0 * step)
                da_ddeg * deg2rad // per-omega^3
            }
            // Heuristic: jerk should not spike more than 1000x median absolute jerk (more tolerant)
            val medAbs = jerk.map { abs(it) }.sorted().let { arr -> arr[if (arr.isNotEmpty()) arr.size / 2 else 0] }
            val cap = kotlin.math.max(1e-2, if (medAbs > 0.0) 1000.0 * medAbs else 1e6)
            for (j in jerk) {
                assertTrue(abs(j) <= cap, "Excessive jerk spike detected (profile=$profile): $j > $cap")
            }

            // Wrap continuity: centered, symmetric checks across 360° with tight tolerances (optimal method)
            run {
                val tol = MotionLawAssertions.Tolerances(
                    relX = 1e-9, absX = 1e-10,
                    relV = 1e-9, absV = 1e-10,
                    relA = 1e-9, absA = 1e-9,
                    neighborhood = 3
                )
                MotionLawAssertions.assertWrapContinuityExtrapolated360(theta, xs, vs, as_, tol)
            }
        }
    }

    @Test
    fun sampling_adjustment_is_deterministic_and_monotone_theta() {
        // Request a step that doesn’t divide 360 exactly; generator should adjust deterministically
        val p = LitvinUserParams(samplingStepDeg = 7.0, rampProfile = RampProfile.S5)
        val motion = MotionLawGenerator.generateMotion(p)
        val n = motion.samples.size
        assertTrue(n > 0)
        // Monotone theta in [0, 360)
        var prev = -1.0
        for (s in motion.samples) {
            assertTrue(s.thetaDeg in 0.0..360.0)
            assertTrue(s.thetaDeg >= prev)
            prev = s.thetaDeg
        }
        // Implied step should be 360/n
        val implied = 360.0 / n
        assertEquals(implied, motion.stepDeg, 1e-12)
    }
}
