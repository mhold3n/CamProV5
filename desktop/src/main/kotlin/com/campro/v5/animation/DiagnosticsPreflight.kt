package com.campro.v5.animation

import com.campro.v5.data.litvin.MotionLawSamples
import kotlin.math.abs

/** Simple preflight checks to gate native diagnostics per ADR Gate A/B. */
object DiagnosticsPreflight {
    data class Item(val name: String, val ok: Boolean, val detail: String = "")
    data class Result(val items: List<Item>) {
        val passed: Boolean get() = items.all { it.ok }
    }

    fun validateMotionLaw(m: MotionLawSamples?): Result {
        if (m == null) return Result(listOf(Item("samples_present", false, "No motion-law samples available")))
        val items = mutableListOf<Item>()
        val n = m.samples.size
        items += Item("count>=3", n >= 3, "n=$n")

        // Monotonic theta and last <= 360
        var mono = true
        var last = Double.NEGATIVE_INFINITY
        var lastStep = 0.0
        for (s in m.samples) {
            if (!(s.thetaDeg >= last)) { mono = false; break }
            lastStep = s.thetaDeg - last
            last = s.thetaDeg
        }
        items += Item("theta_monotonic", mono)
        items += Item("theta_last<=360", last <= 360.0 + 1e-9, "last=$last")

        // Integer 360/stepDeg within tolerance
        val step = m.stepDeg
        val k = 360.0 / step
        val kRound = kotlin.math.round(k)
        val stepOk = abs(k - kRound) <= 1e-9 && step > 0.0
        items += Item("grid_integral", stepOk, "360/step=$k")

        // No NaN/Inf
        fun finite(x: Double) = x.isFinite()
        val hasBad = m.samples.any { s ->
            !(finite(s.thetaDeg) && finite(s.xMm) && finite(s.vMmPerOmega) && finite(s.aMmPerOmega2))
        }
        items += Item("no_nan_inf", !hasBad)

        // Wrap continuity via extrapolated-360 for x/v/a (aligns with MotionLawAssertions)
        var wrapOk = true
        if (n >= 2) {
            val last = m.samples[n - 1]
            val prev = m.samples[n - 2]
            val stepDeg = last.thetaDeg - prev.thetaDeg
            if (stepDeg > 0.0) {
                val ratio = (360.0 - last.thetaDeg) / stepDeg
                val x360 = last.xMm + ratio * (last.xMm - prev.xMm)
                val v360 = last.vMmPerOmega + ratio * (last.vMmPerOmega - prev.vMmPerOmega)
                val a360 = last.aMmPerOmega2 + ratio * (last.aMmPerOmega2 - prev.aMmPerOmega2)

                val first = m.samples[0]
                val maxX = m.samples.maxOf { abs(it.xMm) }.coerceAtLeast(1.0)
                val maxV = m.samples.maxOf { abs(it.vMmPerOmega) }.coerceAtLeast(1.0)
                val maxA = m.samples.maxOf { abs(it.aMmPerOmega2) }.coerceAtLeast(1.0)
                val tx = kotlin.math.max(1e-11, 1e-9 * maxX)
                val tv = kotlin.math.max(1e-10, 1e-9 * maxV)
                val ta = kotlin.math.max(1e-9, 1e-8 * maxA)

                wrapOk = (abs(first.xMm - x360) <= tx) &&
                        (abs(first.vMmPerOmega - v360) <= tv) &&
                        (abs(first.aMmPerOmega2 - a360) <= ta)
            }
        }
        // Provide details for debug/observability of wrap mismatches
        val dx = if (n >= 2) kotlin.run {
            val last = m.samples[n - 1]; val prev = m.samples[n - 2]; val stepDeg2 = last.thetaDeg - prev.thetaDeg
            if (stepDeg2 > 0.0) {
                val ratio2 = (360.0 - last.thetaDeg) / stepDeg2
                val x360_2 = last.xMm + ratio2 * (last.xMm - prev.xMm)
                abs(m.samples[0].xMm - x360_2)
            } else 0.0
        } else 0.0
        val dv = if (n >= 2) kotlin.run {
            val last = m.samples[n - 1]; val prev = m.samples[n - 2]; val stepDeg2 = last.thetaDeg - prev.thetaDeg
            if (stepDeg2 > 0.0) {
                val ratio2 = (360.0 - last.thetaDeg) / stepDeg2
                val v360_2 = last.vMmPerOmega + ratio2 * (last.vMmPerOmega - prev.vMmPerOmega)
                abs(m.samples[0].vMmPerOmega - v360_2)
            } else 0.0
        } else 0.0
        val da = if (n >= 2) kotlin.run {
            val last = m.samples[n - 1]; val prev = m.samples[n - 2]; val stepDeg2 = last.thetaDeg - prev.thetaDeg
            if (stepDeg2 > 0.0) {
                val ratio2 = (360.0 - last.thetaDeg) / stepDeg2
                val a360_2 = last.aMmPerOmega2 + ratio2 * (last.aMmPerOmega2 - prev.aMmPerOmega2)
                abs(m.samples[0].aMmPerOmega2 - a360_2)
            } else 0.0
        } else 0.0
        items += Item("wrap_continuity", wrapOk, "dx=${dx}, dv=${dv}, da=${da}")

        return Result(items)
    }
}
