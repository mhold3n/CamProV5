package com.campro.v5.models

/**
 * Result from the unified optimization pipeline.
 * 
 * This class contains all the results from the unified optimization
 * pipeline, including motion law data, gear profiles, tooth profiles,
 * and FEA analysis results.
 */
data class OptimizationResult(
    val status: String,
    val motionLaw: MotionLawData,
    val optimalProfiles: GearProfileData,
    val toothProfiles: ToothProfileData,
    val feaAnalysis: FEAAnalysisData,
    val executionTime: Double = 0.0,
    val error: String? = null
) {
    
    /**
     * Check if optimization was successful.
     */
    fun isSuccess(): Boolean = status == "success"
    
    /**
     * Check if optimization failed.
     */
    fun isFailure(): Boolean = status == "failed"
    
    /**
     * Get error message if optimization failed.
     */
    fun getErrorMessage(): String? = if (isFailure()) error else null
}

/**
 * Motion law data from optimization.
 */
data class MotionLawData(
    val thetaDeg: DoubleArray,
    val displacement: DoubleArray,
    val velocity: DoubleArray,
    val acceleration: DoubleArray
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as MotionLawData

        if (!thetaDeg.contentEquals(other.thetaDeg)) return false
        if (!displacement.contentEquals(other.displacement)) return false
        if (!velocity.contentEquals(other.velocity)) return false
        if (!acceleration.contentEquals(other.acceleration)) return false

        return true
    }

    override fun hashCode(): Int {
        var result = thetaDeg.contentHashCode()
        result = 31 * result + displacement.contentHashCode()
        result = 31 * result + velocity.contentHashCode()
        result = 31 * result + acceleration.contentHashCode()
        return result
    }
}

/**
 * Gear profile data from optimization.
 */
data class GearProfileData(
    val rSun: DoubleArray,
    val rPlanet: DoubleArray,
    val rRingInner: DoubleArray,
    val gearRatio: Double,
    val optimalMethod: String,
    val efficiencyAnalysis: Map<String, Any>?
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as GearProfileData

        if (!rSun.contentEquals(other.rSun)) return false
        if (!rPlanet.contentEquals(other.rPlanet)) return false
        if (!rRingInner.contentEquals(other.rRingInner)) return false
        if (gearRatio != other.gearRatio) return false
        if (optimalMethod != other.optimalMethod) return false

        return true
    }

    override fun hashCode(): Int {
        var result = rSun.contentHashCode()
        result = 31 * result + rPlanet.contentHashCode()
        result = 31 * result + rRingInner.contentHashCode()
        result = 31 * result + gearRatio.hashCode()
        result = 31 * result + optimalMethod.hashCode()
        return result
    }
}

/**
 * Tooth profile data from optimization.
 */
data class ToothProfileData(
    val sunTeeth: Array<DoubleArray>?,
    val planetTeeth: Array<DoubleArray>?,
    val ringTeeth: Array<DoubleArray>?
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as ToothProfileData

        if (sunTeeth != null) {
            if (other.sunTeeth == null) return false
            if (!sunTeeth.contentDeepEquals(other.sunTeeth)) return false
        } else if (other.sunTeeth != null) return false
        
        if (planetTeeth != null) {
            if (other.planetTeeth == null) return false
            if (!planetTeeth.contentDeepEquals(other.planetTeeth)) return false
        } else if (other.planetTeeth != null) return false
        
        if (ringTeeth != null) {
            if (other.ringTeeth == null) return false
            if (!ringTeeth.contentDeepEquals(other.ringTeeth)) return false
        } else if (other.ringTeeth != null) return false

        return true
    }

    override fun hashCode(): Int {
        var result = sunTeeth?.contentDeepHashCode() ?: 0
        result = 31 * result + (planetTeeth?.contentDeepHashCode() ?: 0)
        result = 31 * result + (ringTeeth?.contentDeepHashCode() ?: 0)
        return result
    }
}

/**
 * FEA analysis data from optimization.
 */
data class FEAAnalysisData(
    val maxStress: Double,
    val naturalFrequencies: DoubleArray,
    val fatigueLife: Double,
    val modeShapes: Array<String>,
    val recommendations: Array<String>
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as FEAAnalysisData

        if (maxStress != other.maxStress) return false
        if (!naturalFrequencies.contentEquals(other.naturalFrequencies)) return false
        if (fatigueLife != other.fatigueLife) return false
        if (!modeShapes.contentEquals(other.modeShapes)) return false
        if (!recommendations.contentEquals(other.recommendations)) return false

        return true
    }

    override fun hashCode(): Int {
        var result = maxStress.hashCode()
        result = 31 * result + naturalFrequencies.contentHashCode()
        result = 31 * result + fatigueLife.hashCode()
        result = 31 * result + modeShapes.contentHashCode()
        result = 31 * result + recommendations.contentHashCode()
        return result
    }
}
