package com.campro.v5.animation

import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.MotionLawSample
import com.campro.v5.data.litvin.MotionLawSamples
import com.campro.v5.data.litvin.RampProfile
import org.slf4j.LoggerFactory
import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.max

object MotionLawGenerator {
    private val logger = LoggerFactory.getLogger(MotionLawGenerator::class.java)

    fun generateMotion(p: LitvinUserParams): MotionLawSamples {
        // CORRECTED: Generate motion law for 180° ring rotation (planetary gearset)
        // The motion law should span 180° ring rotation for complete 2-stroke cycle
        val ringRotationDeg = p.ringRotationDeg // 180°
        val n = max(1, kotlin.math.round(ringRotationDeg / p.samplingStepDeg).toInt())
        val stepDeg = ringRotationDeg / n
        val stepRad = stepDeg * PI / 180.0

        logger.info("Generating motion law using piecewise method with proper acceleration profile...")
        logger.info("CORRECTED: Generate motion law for ${ringRotationDeg}° ring rotation (planetary gearset)")

        // Motion law parameters
        val maxLift = p.strokeLengthMm
        val rampBeforeTdc = p.rampBeforeTdcDeg
        val rampAfterTdc = p.rampAfterTdcDeg
        val dwellTdc = p.dwellTdcDeg
        val rampBeforeBdc = p.rampBeforeBdcDeg
        val rampAfterBdc = p.rampAfterBdcDeg
        val dwellBdc = p.dwellBdcDeg

        // Calculate phase boundaries
        var phase1End = rampBeforeTdc // Acceleration to constant velocity
        var phase2End = phase1End + 30.0 // Constant velocity (30°)
        var phase3End = phase2End + rampAfterTdc // Deceleration to dwell
        var phase4End = phase3End + dwellTdc // Dwell at TDC
        var phase5End = phase4End + rampBeforeBdc // Acceleration to constant velocity
        var phase6End = phase5End + 40.0 // Constant velocity (40°)
        var phase7End = phase6End + rampAfterBdc // Deceleration to dwell
        var phase8End = phase7End + dwellBdc // Dwell at BDC

        // Scale phases to fit 180° ring rotation
        val totalPhases = phase8End
        val scaleFactor = ringRotationDeg / totalPhases

        phase1End *= scaleFactor
        phase2End *= scaleFactor
        phase3End *= scaleFactor
        phase4End *= scaleFactor
        phase5End *= scaleFactor
        phase6End *= scaleFactor
        phase7End *= scaleFactor
        phase8End *= scaleFactor

        logger.info("Motion law phases (scaled to ${ringRotationDeg}°):")
        logger.info("  0-${phase1End}°: Acceleration to constant velocity")
        logger.info("  ${phase1End}-${phase2End}°: Constant velocity")
        logger.info("  ${phase2End}-${phase3End}°: Deceleration to dwell")
        logger.info("  ${phase3End}-${phase4End}°: Dwell at TDC")
        logger.info("  ${phase4End}-${phase5End}°: Acceleration to constant velocity")
        logger.info("  ${phase5End}-${phase6End}°: Constant velocity")
        logger.info("  ${phase6End}-${phase7End}°: Deceleration to dwell")
        logger.info("  ${phase7End}-${phase8End}°: Dwell at BDC")

        // Generate motion law using 8-phase corrected profile
        val samples = ArrayList<MotionLawSample>(n)

        for (k in 0 until n) {
            val theta = k * stepDeg
            val (displacement, velocity, acceleration) = calculateMotionLawPhase(
                theta, maxLift, phase1End, phase2End, phase3End, phase4End,
                phase5End, phase6End, phase7End, phase8End, p.rampProfile
            )
            
            samples.add(MotionLawSample(
                thetaDeg = theta, 
                xMm = displacement, 
                vMmPerOmega = velocity, 
                aMmPerOmega2 = acceleration
            ))
        }

        // CORRECTED: Wrap correction for 180° ring rotation motion law
        // Ensure periodicity at 180° boundary (not 360°)
        if (samples.size >= 2) {
            val firstSample = samples.first()
            val lastSample = samples.last()
            
            // Ensure displacement returns to zero at 180° (periodic boundary)
            if (kotlin.math.abs(lastSample.xMm) > 1e-6) {
                logger.debug("Adjusting final displacement for 180° periodicity: ${lastSample.xMm} -> 0.0")
                samples[samples.size - 1] = lastSample.copy(xMm = 0.0)
            }
            
            // Ensure velocity and acceleration are zero at 180° boundary
            if (kotlin.math.abs(lastSample.vMmPerOmega) > 1e-6 || kotlin.math.abs(lastSample.aMmPerOmega2) > 1e-6) {
                logger.debug("Adjusting final velocity/acceleration for 180° periodicity")
                samples[samples.size - 1] = lastSample.copy(vMmPerOmega = 0.0, aMmPerOmega2 = 0.0)
            }
        }

        logger.debug("Generated corrected motion law: n=$n stepDeg=${"%.6f".format(stepDeg)} ringRotation=${ringRotationDeg}°")
        return MotionLawSamples(stepDeg = stepDeg, samples = samples)
    }

    /**
     * Calculate motion law phase using the corrected 8-phase profile from Python script.
     * This implements the proper acceleration profile with constant velocity zones.
     */
    private fun calculateMotionLawPhase(
        theta: Double,
        maxLift: Double,
        phase1End: Double,
        phase2End: Double,
        phase3End: Double,
        phase4End: Double,
        phase5End: Double,
        phase6End: Double,
        phase7End: Double,
        phase8End: Double,
        rampProfile: RampProfile
    ): Triple<Double, Double, Double> {
        val degToRadScale = 180.0 / PI
        
        return when {
            theta <= phase1End -> {
                // Phase 1: Acceleration to constant velocity
                val beta = theta / phase1End
                val displacement = maxLift * 0.5 * (beta - kotlin.math.sin(2 * PI * beta) / (2 * PI))
                val velocity = maxLift * 0.5 * (1 - kotlin.math.cos(2 * PI * beta)) / (2 * PI * phase1End * PI / 180)
                val acceleration = maxLift * 0.5 * kotlin.math.sin(2 * PI * beta) / (phase1End * PI / 180).pow(2)
                Triple(displacement, velocity, acceleration)
            }
            
            theta <= phase2End -> {
                // Phase 2: Constant velocity
                val displacement = maxLift * 0.5 + maxLift * 0.5 * (theta - phase1End) / (phase2End - phase1End)
                val velocity = maxLift * 0.5 / (phase2End - phase1End) * PI / 180
                val acceleration = 0.0
                Triple(displacement, velocity, acceleration)
            }
            
            theta <= phase3End -> {
                // Phase 3: Deceleration to dwell (stay at max_lift, decelerate to zero velocity)
                val beta = (theta - phase2End) / (phase3End - phase2End)
                val displacement = maxLift // Stay at maximum displacement during deceleration to dwell
                val velocity = maxLift * 0.5 * (1 - beta) / (phase2End - phase1End) * PI / 180
                val acceleration = -maxLift * 0.5 / (phase2End - phase1End) / (phase3End - phase2End) * PI / 180
                Triple(displacement, velocity, acceleration)
            }
            
            theta <= phase4End -> {
                // Phase 4: Dwell at TDC
                val displacement = maxLift
                val velocity = 0.0
                val acceleration = 0.0
                Triple(displacement, velocity, acceleration)
            }
            
            theta <= phase5End -> {
                // Phase 5: Acceleration to constant velocity
                val beta = (theta - phase4End) / (phase5End - phase4End)
                val displacement = maxLift * (1 - 0.5 * (beta - kotlin.math.sin(2 * PI * beta) / (2 * PI)))
                val velocity = -maxLift * 0.5 * (1 - kotlin.math.cos(2 * PI * beta)) / (2 * PI * (phase5End - phase4End) * PI / 180)
                val acceleration = -maxLift * 0.5 * kotlin.math.sin(2 * PI * beta) / ((phase5End - phase4End) * PI / 180).pow(2)
                Triple(displacement, velocity, acceleration)
            }
            
            theta <= phase6End -> {
                // Phase 6: Constant velocity
                val displacement = maxLift * 0.5 - maxLift * 0.5 * (theta - phase5End) / (phase6End - phase5End)
                val velocity = -maxLift * 0.5 / (phase6End - phase5End) * PI / 180
                val acceleration = 0.0
                Triple(displacement, velocity, acceleration)
            }
            
            theta <= phase7End -> {
                // Phase 7: Deceleration to dwell (stay at zero displacement, decelerate to zero velocity)
                val beta = (theta - phase6End) / (phase7End - phase6End)
                val displacement = 0.0 // Stay at zero displacement during deceleration to dwell at BDC
                val velocity = -maxLift * 0.5 * (1 - beta) / (phase6End - phase5End) * PI / 180
                val acceleration = maxLift * 0.5 / (phase6End - phase5End) / (phase7End - phase6End) * PI / 180
                Triple(displacement, velocity, acceleration)
            }
            
            theta <= phase8End -> {
                // Phase 8: Dwell at BDC
                val displacement = 0.0
                val velocity = 0.0
                val acceleration = 0.0
                Triple(displacement, velocity, acceleration)
            }
            
            else -> {
                // Beyond defined phases - should not happen
                Triple(0.0, 0.0, 0.0)
            }
        }
    }
}
