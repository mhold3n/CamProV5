package com.campro.v5.animation

import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.RampProfile
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import kotlin.math.abs
import kotlin.math.max

class TransmissionPredictorTest {

    @Test
    fun transmission_is_periodic_mean_normalized_and_finite() {
        val profiles = listOf(RampProfile.Cycloidal, RampProfile.S5, RampProfile.S7)
        for (profile in profiles) {
            val p = LitvinUserParams(
                rampProfile = profile,
                samplingStepDeg = 2.0,
                camKPerUnit = 1.0
            )
            val motion = MotionLawGenerator.generateMotion(p)
            val trans = TransmissionSynthesis.computeTransmissionAndPitch(motion, p)

            // Size matches motion sample count
            assertEquals(motion.samples.size, trans.iOfTheta.size)

            // No NaN or Inf
            for ((th, iv) in trans.iOfTheta) {
                assertTrue(th.isFinite(), "theta should be finite")
                assertTrue(iv.isFinite(), "i(theta) should be finite")
            }

            // Periodicity: first and last agree (θ=0 vs θ=360-step)
            val first = trans.iOfTheta.first()
            val last = trans.iOfTheta.last()
            val scale = max(1.0, max(abs(first.second), abs(last.second)))
            assertTrue(abs(first.first - 0.0) < 1e-9)
            assertTrue(abs(last.first - (360.0 - motion.stepDeg)) < 1e-9)
            assertTrue(abs(first.second - last.second) <= 1e-3 * scale, "i wrap mismatch: ${first.second} vs ${last.second}")

            // Mean normalized to exactly ~1.0 (within numeric tolerance)
            val mean = trans.iOfTheta.map { it.second }.average()
            assertEquals(1.0, mean, 1e-12, "mean(i) must be 1.0 after normalization; profile=$profile")

            // Residual smoothness below preview tolerance
            assertTrue(trans.residualArcLenRms.isFinite())
            assertTrue(trans.residualArcLenRms <= 0.25, "Preview residual too high: ${trans.residualArcLenRms} (profile=$profile)")

            // Pitch previews: monotonically increasing s in [0,1] and finite radii
            fun checkPitch(rps: List<Pair<Double, Double>>) {
                if (rps.isEmpty()) return
                var prevS = -1.0
                for ((s, r) in rps) {
                    assertTrue(s in 0.0..1.0, "s out of [0,1]")
                    assertTrue(s >= prevS - 1e-12, "s not monotone: $s < $prevS")
                    assertTrue(r.isFinite(), "radius not finite")
                    prevS = s
                }
            }
            checkPitch(trans.pitchRing)
            checkPitch(trans.pitchPlanet)
        }
    }
}
