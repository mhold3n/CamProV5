package com.campro.v5.data.litvin

data class LitvinUserParams(
    // Core sampling/motion controls
    val samplingStepDeg: Double = 1.0,
    val profileSolverMode: ProfileSolverMode = ProfileSolverMode.Piecewise,
    val rampProfile: RampProfile = RampProfile.S5,
    val dwellTdcDeg: Double = 0.0,
    val dwellBdcDeg: Double = 0.0,
    val rampBeforeTdcDeg: Double = 0.0,
    val rampAfterTdcDeg: Double = 0.0,
    val rampBeforeBdcDeg: Double = 0.0,
    val rampAfterBdcDeg: Double = 0.0,

    // Stroke and CV split
    val strokeLengthMm: Double = 100.0,
    val upFraction: Double = 0.5,

    // Geometry/visualization and tuning (cover names used in tests)
    val rodLength: Double = 100.0,
    val interferenceBuffer: Double = 0.5,
    val planetCount: Int = 2,
    val carrierOffsetDeg: Double = 180.0,
    val ringThicknessVisual: Double = 6.0,
    val arcResidualTolMm: Double = 0.01,

    // Existing with defaults
    val sliderAxisDeg: Double = 0.0,
    val journalPhaseBetaDeg: Double = 0.0,
    val journalRadius: Double = 5.0,
    val camR0: Double = 40.0,
    val camKPerUnit: Double = 1.0,
    val centerDistanceBias: Double = 50.0,
    val centerDistanceScale: Double = 1.0,
    val rpm: Double = 3000.0
)
