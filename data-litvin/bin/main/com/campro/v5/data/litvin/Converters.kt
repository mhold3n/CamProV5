package com.campro.v5.data.litvin

import com.google.gson.Gson

/** Extension for call-site convenience */
fun LitvinUserParams.validate(): List<String> = validateParams(this)

/** Return list of validation error messages; empty if ok. Minimal implementation for compile. */
fun validateParams(p: LitvinUserParams): List<String> {
    val errs = mutableListOf<String>()
    if (p.samplingStepDeg <= 0.0) errs += "samplingStepDeg must be > 0"
    if (p.upFraction !in 0.0..1.0) errs += "upFraction must be in [0,1]"
    return errs
}

/** Construct params from a generic map; tolerates missing keys with defaults. */
fun litvinParamsFromMap(m: Map<String, Any?>): LitvinUserParams {
    fun num(key: String, def: Double) = (m[key] as? Number)?.toDouble() ?: def
    fun ramp(key: String, def: RampProfile) =
        (m[key] as? String)?.let {
            runCatching { RampProfile.valueOf(it) }.getOrNull()
        } ?: def
    fun solverMode(key: String, def: ProfileSolverMode) =
        (m[key] as? String)?.let {
            runCatching { ProfileSolverMode.valueOf(it) }.getOrNull()
        } ?: def
    return LitvinUserParams(
        strokeLengthMm = num("strokeLengthMm", 10.0),
        samplingStepDeg = num("samplingStepDeg", 1.0),
        profileSolverMode = solverMode("Profile Solver", ProfileSolverMode.Piecewise),
        rampProfile = ramp("rampProfile", RampProfile.Cycloidal),
        dwellTdcDeg = num("dwellTdcDeg", 0.0),
        rampAfterTdcDeg = num("rampAfterTdcDeg", 0.0),
        rampBeforeBdcDeg = num("rampBeforeBdcDeg", 0.0),
        dwellBdcDeg = num("dwellBdcDeg", 0.0),
        rampAfterBdcDeg = num("rampAfterBdcDeg", 0.0),
        rampBeforeTdcDeg = num("rampBeforeTdcDeg", 0.0),
        upFraction = num("upFraction", 0.5)
    )
}

/** Extension for call-site convenience */
fun LitvinUserParams.toJniArgs(): Array<String> = toJniArgsInternal(this)

/** Serialize params for JNI argument passing (string array). Keep stable order. */
fun toJniArgsInternal(p: LitvinUserParams): Array<String> = arrayOf(
    p.strokeLengthMm.toString(),
    p.samplingStepDeg.toString(),
    p.rampProfile.name,
    p.dwellTdcDeg.toString(),
    p.rampAfterTdcDeg.toString(),
    p.rampBeforeBdcDeg.toString(),
    p.dwellBdcDeg.toString(),
    p.rampAfterBdcDeg.toString(),
    p.rampBeforeTdcDeg.toString(),
    p.upFraction.toString()
)

/** Inverse of toJniArgs; best-effort. */
fun jniArgsToMap(args: Array<String>): Map<String, Any?> {
    val keys = listOf(
        "strokeLengthMm","samplingStepDeg","rampProfile","dwellTdcDeg","rampAfterTdcDeg",
        "rampBeforeBdcDeg","dwellBdcDeg","rampAfterBdcDeg","rampBeforeTdcDeg","upFraction"
    )
    val map = mutableMapOf<String, Any?>()
    for ((i, k) in keys.withIndex()) {
        val v = args.getOrNull(i)
        map[k] = when (k) {
            "rampProfile" -> v ?: RampProfile.Cycloidal.name
            else -> v?.toDoubleOrNull() ?: 0.0
        }
    }
    return map
}
