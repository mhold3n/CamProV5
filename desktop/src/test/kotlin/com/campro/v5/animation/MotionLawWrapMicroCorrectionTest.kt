package com.campro.v5.animation

import com.campro.v5.animation.testutil.MotionLawAssertions
import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.RampProfile
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import kotlin.math.abs
import kotlin.math.max

class MotionLawWrapMicroCorrectionTest {

    @Test
    fun centered_wrap_witnesses_and_means_are_within_tolerance() {
        val profiles = listOf(RampProfile.Cycloidal, RampProfile.S5, RampProfile.S7)
        val steps = listOf(2.0, 3.0, 5.0)
        for (profile in profiles) {
            for (step in steps) {
                val p = LitvinUserParams(
                    rampProfile = profile,
                    samplingStepDeg = step,
                    dwellTdcDeg = 30.0,
                    dwellBdcDeg = 30.0,
                    rampAfterTdcDeg = 20.0,
                    rampBeforeBdcDeg = 20.0,
                    rampAfterBdcDeg = 20.0,
                    rampBeforeTdcDeg = 20.0,
                )
                val m = MotionLawGenerator.generateMotion(p)
                val n = m.samples.size
                assertTrue(n >= 3)
                val theta = DoubleArray(n) { m.samples[it].thetaDeg }
                val xs = DoubleArray(n) { m.samples[it].xMm }
                val vs = DoubleArray(n) { m.samples[it].vMmPerOmega }
                val as_ = DoubleArray(n) { m.samples[it].aMmPerOmega2 }

                // Centered witnesses at wrap (h=1)
                MotionLawAssertions.assertWrapContinuityExtrapolated360(
                    theta, xs, vs, as_,
                    MotionLawAssertions.Tolerances(
                        relX = 1e-9, absX = 1e-10,
                        relV = 1e-9, absV = 1e-10,
                        relA = 1e-9, absA = 1e-9,
                        neighborhood = 3
                    )
                )

                // x end-window means should be within tight tolerance
                val k = max(1, kotlin.math.min(3, n / 2))
                var sx0 = 0.0; var sx1 = 0.0
                for (i in 0 until k) { sx0 += xs[i]; sx1 += xs[n - 1 - i] }
                val x0 = sx0 / k; val x1 = sx1 / k
                val maxX = xs.maxOf { kotlin.math.abs(it) }.coerceAtLeast(1.0)
                val tx = kotlin.math.max(1e-11, 1e-9 * maxX)
                assertTrue(abs(x0 - x1) <= tx, "Wrap position mismatch (avg x): |$x0 - $x1| = ${abs(x0 - x1)} > $tx")

                // v/a extrapolated-360 consistency for the first sample
                val i2 = n - 1; val i1 = n - 2
                val stepDeg = theta[i2] - theta[i1]
                assertTrue(stepDeg > 0)
                val ratio = (360.0 - theta[i2]) / stepDeg
                val v360 = vs[i2] + ratio * (vs[i2] - vs[i1])
                val a360 = as_[i2] + ratio * (as_[i2] - as_[i1])
                val vMax = vs.maxOf { kotlin.math.abs(it) }.coerceAtLeast(1.0)
                val aMax = as_.maxOf { kotlin.math.abs(it) }.coerceAtLeast(1.0)
                val tv = kotlin.math.max(1e-9, 1e-5 * vMax)
                val ta = kotlin.math.max(1e-9, 1e-8 * aMax)
                assertEquals(v360, vs[0], tv, "Wrap velocity mismatch (extrapolated v)")
                assertEquals(a360, as_[0], ta, "Wrap accel mismatch (extrapolated a)")
            }
        }
    }
}
