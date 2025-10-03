package com.campro.v5.models

/**
 * Optimization parameters for the unified optimization pipeline.
 *
 * This class contains all the parameters needed to run the unified
 * optimization pipeline, including motion law parameters, gear design
 * parameters, and analysis parameters.
 */
data class OptimizationParameters(
    // Motion law parameters
    val samplingStepDeg: Double = 5.0,
    val ringRotationDeg: Double = 180.0,

    // Gear design parameters
    val gearRatio: Double = 2.0,
    val strokeLengthMm: Double = 10.0,
    val rodLength: Double = 80.0,
    val journalRadius: Double = 5.0,
    val interferenceBuffer: Double = 0.5,
    val ringThickness: Double = 5.0,

    // Operating parameters
    // TODO: FUTURE ENHANCEMENT - GUI INPUT CHANGE REQUIRED:
    // Instead of user inputting a static RPM value (e.g., 3000), the user will input an RPM step interval
    // (e.g., 500) and the system will automatically sweep from 500 to 10000 RPM in 500 RPM steps.
    // This enables comprehensive analysis across multiple operating speeds for resonant frequency
    // detection and optimal speed identification.
    val rpm: Double = 3000.0,
    // Fixed planetary configuration: always 2 planets with 180° offset
    val planetCount: Int = 2,
    val carrierOffsetDeg: Double = 180.0,

    // Motion law timing parameters
    val rampBeforeTdcDeg: Double = 20.0,
    val rampAfterTdcDeg: Double = 20.0,
    val dwellTdcDeg: Double = 10.0,
    val rampBeforeBdcDeg: Double = 20.0,
    val rampAfterBdcDeg: Double = 20.0,
    val dwellBdcDeg: Double = 10.0,
    val constantVelocityTdcDeg: Double = 30.0,
    val constantVelocityBdcDeg: Double = 40.0,

    // Compression stroke control
    val compressionDurationPercent: Double = 70.0, // Compression duration as % of planet duration

    // Advanced parameters
    val planetRadiusBaseFactor: Double = 0.2,
    val planetRadiusVariationFactor: Double = 0.1,
    val sunRadiusBaseFactor: Double = 0.15,
    val sunRadiusVariationFactor: Double = 0.05,
    val strokeAchievableFactor: Double = 0.9,
    val clearanceSafetyMargin: Double = 0.2,
    val adjustmentSplitFactor: Double = 0.6,
    // Instantaneous ratio model (new)
    val rMin: Double = 2.0, // Must be >= 2.0 for geometric consistency
    val rMax: Double = 2.5,
    val rSmoothnessWeight: Double = 0.0,
    val motionVariationWeight: Double = 0.1, // Weight for motion-dependent r(θ) variation
    // Journal offset optimization (critical for variable ratios)
    val journalOffsetMin: Double = -2.0, // Minimum journal offset from planet COM
    val journalOffsetMax: Double = 2.0, // Maximum journal offset from planet COM
    // User-driven bounds (derived from design constraints)
    val maxGearRatioVariation: Double = 0.5, // Maximum deviation from nominal gear ratio
    val maxJournalOffsetPercent: Double = 0.1, // Maximum journal offset as % of planet radius
    // Symmetry prior (optional)
    val enableSymmetryPrior: Boolean = false,
    val symmetryWeight: Double = 0.5,
) {

    /**
     * Calculate gear ratio bounds based on user inputs and design constraints.
     */
    fun calculateGearRatioBounds(): Pair<Double, Double> {
        val nominalRatio = gearRatio
        val variation = maxGearRatioVariation
        val minRatio = maxOf(2.0, nominalRatio - variation) // Ensure geometric consistency
        val maxRatio = nominalRatio + variation
        return Pair(minRatio, maxRatio)
    }
    
    /**
     * Calculate journal offset bounds based on user inputs and design constraints.
     */
    fun calculateJournalOffsetBounds(planetRadius: Double): Pair<Double, Double> {
        val maxOffset = planetRadius * maxJournalOffsetPercent
        return Pair(-maxOffset, maxOffset)
    }
    
    /**
     * Validate parameters for reasonable ranges.
     */
    fun validate(): List<String> {
        val errors = mutableListOf<String>()

        if (samplingStepDeg <= 0 || samplingStepDeg > 180) {
            errors.add("Sampling step must be between 0 and 180 degrees")
        }

        if (strokeLengthMm <= 0 || strokeLengthMm > 100) {
            errors.add("Stroke length must be between 0 and 100 mm")
        }

        if (gearRatio <= 0 || gearRatio > 10) {
            errors.add("Gear ratio must be between 0 and 10")
        }

        if (rpm <= 0 || rpm > 20000) {
            errors.add("RPM must be between 0 and 20000")
        }

        if (planetCount < 2 || planetCount > 8) {
            errors.add("Planet count must be between 2 and 8")
        }

        if (rodLength <= 0 || rodLength > 500) {
            errors.add("Rod length must be between 0 and 500 mm")
        }
        
        if (maxGearRatioVariation <= 0 || maxGearRatioVariation > 2.0) {
            errors.add("Max gear ratio variation must be between 0 and 2.0")
        }
        
        if (maxJournalOffsetPercent <= 0 || maxJournalOffsetPercent > 0.5) {
            errors.add("Max journal offset percent must be between 0 and 50%")
        }

        if (journalRadius <= 0 || journalRadius > 50) {
            errors.add("Journal radius must be between 0 and 50 mm")
        }

        if (ringThickness <= 0 || ringThickness > 50) {
            errors.add("Ring thickness must be between 0 and 50 mm")
        }

        if (interferenceBuffer < 0 || interferenceBuffer > 10) {
            errors.add("Interference buffer must be between 0 and 10 mm")
        }

        return errors
    }

    /**
     * Create a copy with updated parameters.
     */
    fun copyWith(
        samplingStepDeg: Double = this.samplingStepDeg,
        ringRotationDeg: Double = this.ringRotationDeg,
        gearRatio: Double = this.gearRatio,
        strokeLengthMm: Double = this.strokeLengthMm,
        rodLength: Double = this.rodLength,
        journalRadius: Double = this.journalRadius,
        interferenceBuffer: Double = this.interferenceBuffer,
        ringThickness: Double = this.ringThickness,
        rpm: Double = this.rpm,
        planetCount: Int = this.planetCount,
        carrierOffsetDeg: Double = this.carrierOffsetDeg,
        rampBeforeTdcDeg: Double = this.rampBeforeTdcDeg,
        rampAfterTdcDeg: Double = this.rampAfterTdcDeg,
        dwellTdcDeg: Double = this.dwellTdcDeg,
        rampBeforeBdcDeg: Double = this.rampBeforeBdcDeg,
        rampAfterBdcDeg: Double = this.rampAfterBdcDeg,
        dwellBdcDeg: Double = this.dwellBdcDeg,
        constantVelocityTdcDeg: Double = this.constantVelocityTdcDeg,
        constantVelocityBdcDeg: Double = this.constantVelocityBdcDeg,
        planetRadiusBaseFactor: Double = this.planetRadiusBaseFactor,
        planetRadiusVariationFactor: Double = this.planetRadiusVariationFactor,
        sunRadiusBaseFactor: Double = this.sunRadiusBaseFactor,
        sunRadiusVariationFactor: Double = this.sunRadiusVariationFactor,
        strokeAchievableFactor: Double = this.strokeAchievableFactor,
        clearanceSafetyMargin: Double = this.clearanceSafetyMargin,
        adjustmentSplitFactor: Double = this.adjustmentSplitFactor,
        rMin: Double = this.rMin,
        rMax: Double = this.rMax,
        rSmoothnessWeight: Double = this.rSmoothnessWeight,
        motionVariationWeight: Double = this.motionVariationWeight,
        journalOffsetMin: Double = this.journalOffsetMin,
        journalOffsetMax: Double = this.journalOffsetMax,
        maxGearRatioVariation: Double = this.maxGearRatioVariation,
        maxJournalOffsetPercent: Double = this.maxJournalOffsetPercent,
        enableSymmetryPrior: Boolean = this.enableSymmetryPrior,
        symmetryWeight: Double = this.symmetryWeight,
    ): OptimizationParameters = OptimizationParameters(
        samplingStepDeg = samplingStepDeg,
        ringRotationDeg = ringRotationDeg,
        gearRatio = gearRatio,
        strokeLengthMm = strokeLengthMm,
        rodLength = rodLength,
        journalRadius = journalRadius,
        interferenceBuffer = interferenceBuffer,
        ringThickness = ringThickness,
        rpm = rpm,
        planetCount = planetCount,
        carrierOffsetDeg = carrierOffsetDeg,
        rampBeforeTdcDeg = rampBeforeTdcDeg,
        rampAfterTdcDeg = rampAfterTdcDeg,
        dwellTdcDeg = dwellTdcDeg,
        rampBeforeBdcDeg = rampBeforeBdcDeg,
        rampAfterBdcDeg = rampAfterBdcDeg,
        dwellBdcDeg = dwellBdcDeg,
        constantVelocityTdcDeg = constantVelocityTdcDeg,
        constantVelocityBdcDeg = constantVelocityBdcDeg,
        planetRadiusBaseFactor = planetRadiusBaseFactor,
        planetRadiusVariationFactor = planetRadiusVariationFactor,
        sunRadiusBaseFactor = sunRadiusBaseFactor,
        sunRadiusVariationFactor = sunRadiusVariationFactor,
        strokeAchievableFactor = strokeAchievableFactor,
        clearanceSafetyMargin = clearanceSafetyMargin,
        adjustmentSplitFactor = adjustmentSplitFactor,
            rMin = rMin,
            rMax = rMax,
            rSmoothnessWeight = rSmoothnessWeight,
            motionVariationWeight = motionVariationWeight,
            journalOffsetMin = journalOffsetMin,
            journalOffsetMax = journalOffsetMax,
            maxGearRatioVariation = maxGearRatioVariation,
            maxJournalOffsetPercent = maxJournalOffsetPercent,
            enableSymmetryPrior = enableSymmetryPrior,
            symmetryWeight = symmetryWeight,
    )

    companion object {
        /**
         * Create default parameters for testing.
         */
        fun createDefault(): OptimizationParameters = OptimizationParameters()

        /**
         * Create parameters for high-performance testing.
         */
        fun createHighPerformance(): OptimizationParameters = OptimizationParameters(
            samplingStepDeg = 2.0,
            strokeLengthMm = 15.0,
            gearRatio = 2.5,
            rpm = 5000.0,
            planetCount = 4,
            rodLength = 100.0,
            journalRadius = 8.0,
            ringThickness = 8.0,
            interferenceBuffer = 0.2,
        )

        /**
         * Create parameters for quick testing.
         */
        fun createQuickTest(): OptimizationParameters = OptimizationParameters(
            samplingStepDeg = 10.0,
            strokeLengthMm = 5.0,
            gearRatio = 2.0,
            rpm = 1000.0,
            planetCount = 2,
            rodLength = 40.0,
            journalRadius = 3.0,
            ringThickness = 3.0,
        )
    }
}
