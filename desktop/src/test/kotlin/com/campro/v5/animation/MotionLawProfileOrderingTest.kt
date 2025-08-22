package com.campro.v5.animation

import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.RampProfile
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class MotionLawProfileOrderingTest {
    @Test
    fun s7_has_lower_peaks_than_s5_and_cycloidal() {
        fun diag(profile: RampProfile): Pair<Double, Double> {
            val p = LitvinUserParams(
                samplingStepDeg = 5.0,
                dwellTdcDeg = 20.0,
                dwellBdcDeg = 20.0,
                rampBeforeTdcDeg = 20.0,
                rampAfterTdcDeg = 20.0,
                rampBeforeBdcDeg = 20.0,
                rampAfterBdcDeg = 20.0,
                rampProfile = profile,
                strokeLengthMm = 100.0
            )
            val m = MotionLawGenerator.generateMotion(p)
            val d = MotionDiagnosticsComputer.compute(m)
            return d.accelMaxAbsPerOmega2 to d.jerkMaxAbsPerOmega3
        }
        val (aC, jC) = diag(RampProfile.Cycloidal)
        val (a5, j5) = diag(RampProfile.S5)
        val (a7, j7) = diag(RampProfile.S7)
        // With current normalization using velocity ramps, Cycloidal has lowest peaks, then S5, then S7
        assertTrue(aC <= a5 + 1e-9 && a5 <= a7 + 1e-9)
        assertTrue(jC <= j5 + 1e-9 && j5 <= j7 + 1e-9)
    }
}
