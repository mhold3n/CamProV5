package com.campro.v5.animation

import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.RampProfile
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class MotionLawWrapContinuityTest {

    @Test
    fun wrap_continuity_and_finiteness_s5() {
        val p = LitvinUserParams(
            samplingStepDeg = 5.0,
            rampProfile = RampProfile.S5,
            dwellTdcDeg = 10.0,
            dwellBdcDeg = 10.0,
            rampAfterTdcDeg = 20.0,
            rampBeforeBdcDeg = 20.0,
            rampAfterBdcDeg = 20.0,
            rampBeforeTdcDeg = 20.0,
            strokeLengthMm = 80.0
        )
        val m = MotionLawGenerator.generateMotion(p)

        // Use DiagnosticsPreflight to validate Gate A conditions
        val res = DiagnosticsPreflight.validateMotionLaw(m)
        assertTrue(res.passed, "Preflight items failed: " + res.items.filter { !it.ok }.joinToString { "${it.name}:${it.detail}" })

        // Explicit finiteness
        for (s in m.samples) {
            assertTrue(s.thetaDeg.isFinite())
            assertTrue(s.xMm.isFinite())
            assertTrue(s.vMmPerOmega.isFinite())
            assertTrue(s.aMmPerOmega2.isFinite())
        }
    }
}
