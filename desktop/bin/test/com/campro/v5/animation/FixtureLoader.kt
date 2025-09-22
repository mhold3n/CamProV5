package com.campro.v5.animation

import java.nio.file.Files
import java.nio.file.Paths

data class FixtureMotionSample(
    val thetaDeg: Double,
    val xMm: Double,
    val vMmPerOmega: Double,
    val aMmPerOmega2: Double,
)

data class FixtureMotionSamples(
    val stepDeg: Double,
    val samples: List<FixtureMotionSample>,
)

object FixtureLoader {
    fun loadMotionSamples(pathStr: String): FixtureMotionSamples {
        val path = Paths.get(pathStr)
        val text = Files.readString(path)
        val step = Regex("\"stepDeg\"\\s*:\\s*([0-9eE+.-]+)")
            .find(text)?.groupValues?.get(1)?.toDouble()
            ?: error("stepDeg missing in $pathStr")
        val samplesArray = Regex("\"samples\"\\s*:\\s*\\[(.*)]", RegexOption.DOT_MATCHES_ALL)
            .find(text)?.groupValues?.get(1)
            ?: error("samples missing in $pathStr")
        val sampleRegex = Regex("\\{([^}]*)\\}")
        val numRegex = { key: String ->
            Regex("\"$key\"\\s*:\\s*([0-9eE+.-]+)")
        }
        val samples = mutableListOf<FixtureMotionSample>()
        for (m in sampleRegex.findAll(samplesArray)) {
            val obj = m.groupValues[1]
            val th = numRegex("thetaDeg").find(obj)?.groupValues?.get(1)?.toDouble() ?: continue
            val x = numRegex("xMm").find(obj)?.groupValues?.get(1)?.toDouble() ?: 0.0
            val v = numRegex("vMmPerOmega").find(obj)?.groupValues?.get(1)?.toDouble() ?: 0.0
            val a = numRegex("aMmPerOmega2").find(obj)?.groupValues?.get(1)?.toDouble() ?: 0.0
            samples.add(FixtureMotionSample(th, x, v, a))
        }
        return FixtureMotionSamples(step, samples)
    }
}


