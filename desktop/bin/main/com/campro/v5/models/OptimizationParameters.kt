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
    val rpm: Double = 3000.0,
    val planetCount: Int = 3,
    val carrierOffsetDeg: Double = 120.0,
    
    // Motion law timing parameters
    val rampBeforeTdcDeg: Double = 20.0,
    val rampAfterTdcDeg: Double = 20.0,
    val dwellTdcDeg: Double = 10.0,
    val rampBeforeBdcDeg: Double = 20.0,
    val rampAfterBdcDeg: Double = 20.0,
    val dwellBdcDeg: Double = 10.0,
    val constantVelocityTdcDeg: Double = 30.0,
    val constantVelocityBdcDeg: Double = 40.0,
    
    // Advanced parameters
    val planetRadiusBaseFactor: Double = 0.2,
    val planetRadiusVariationFactor: Double = 0.1,
    val sunRadiusBaseFactor: Double = 0.15,
    val sunRadiusVariationFactor: Double = 0.05,
    val strokeAchievableFactor: Double = 0.9,
    val clearanceSafetyMargin: Double = 0.2,
    val adjustmentSplitFactor: Double = 0.6
) {
    
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
        adjustmentSplitFactor: Double = this.adjustmentSplitFactor
    ): OptimizationParameters {
        return OptimizationParameters(
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
            adjustmentSplitFactor = adjustmentSplitFactor
        )
    }
    
    companion object {
        /**
         * Create default parameters for testing.
         */
        fun createDefault(): OptimizationParameters {
            return OptimizationParameters()
        }
        
        /**
         * Create parameters for high-performance testing.
         */
        fun createHighPerformance(): OptimizationParameters {
            return OptimizationParameters(
                samplingStepDeg = 2.0,
                strokeLengthMm = 15.0,
                gearRatio = 2.5,
                rpm = 5000.0,
                planetCount = 4,
                rodLength = 100.0,
                journalRadius = 8.0,
                ringThickness = 8.0,
                interferenceBuffer = 0.2
            )
        }
        
        /**
         * Create parameters for quick testing.
         */
        fun createQuickTest(): OptimizationParameters {
            return OptimizationParameters(
                samplingStepDeg = 10.0,
                strokeLengthMm = 5.0,
                gearRatio = 2.0,
                rpm = 1000.0,
                planetCount = 2,
                rodLength = 40.0,
                journalRadius = 3.0,
                ringThickness = 3.0
            )
        }
    }
}
