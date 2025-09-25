package com.campro.v5.animation.collocation

import com.campro.v5.data.litvin.LitvinUserParams
import com.campro.v5.data.litvin.RampProfile
import kotlin.math.*

/**
 * Converts UI parameters to collocation constraints for the NLP solver.
 * 
 * This maps the existing piecewise motion law parameters (dwells, ramps, CV segments)
 * into constraint equations that the collocation solver can enforce.
 */
class CollocationConstraints(
    private val params: LitvinUserParams,
    private val discretization: CollocationDiscretization
) {
    
    // Constraint tolerance for NLP solver
    private val constraintTolerance = 1e-8
    
    /**
     * Generate all constraints for the motion law problem.
     * 
     * @return List of constraints to be enforced by the NLP solver
     */
    fun generateConstraints(): List<MotionConstraint> {
        val constraints = mutableListOf<MotionConstraint>()
        
        // 1. Periodicity constraints (essential for cam profiles)
        constraints.addAll(generatePeriodicityConstraints())
        
        // 2. Dwell constraints (velocity ≈ 0, acceleration ≈ 0)
        constraints.addAll(generateDwellConstraints())
        
        // 3. Constant velocity constraints
        constraints.addAll(generateConstantVelocityConstraints())
        
        // 4. Ramp profile constraints (based on RampProfile type)
        constraints.addAll(generateRampConstraints())
        
        // 5. Stroke boundary constraints
        constraints.addAll(generateStrokeBoundaryConstraints())
        
        // 6. Planetary gearset constraints (UNIFIED CONSTRAINT SYSTEM)
        constraints.addAll(generatePlanetaryGearsetConstraints())
        
        return constraints
    }
    
    /**
     * Generate periodicity constraints.
     * Ensures x(0) = x(2π), v(0) = v(2π), a(0) = a(2π)
     */
    private fun generatePeriodicityConstraints(): List<MotionConstraint> {
        return listOf(
            MotionConstraint.Equality(
                name = "position_periodicity",
                description = "x(0) = x(2π)",
                evaluationPoints = doubleArrayOf(0.0, 2.0 * PI),
                constraintType = ConstraintType.POSITION_DIFFERENCE,
                targetValue = 0.0,
                tolerance = constraintTolerance
            ),
            MotionConstraint.Equality(
                name = "velocity_periodicity", 
                description = "v(0) = v(2π)",
                evaluationPoints = doubleArrayOf(0.0, 2.0 * PI),
                constraintType = ConstraintType.VELOCITY_DIFFERENCE,
                targetValue = 0.0,
                tolerance = constraintTolerance
            ),
            MotionConstraint.Equality(
                name = "acceleration_periodicity",
                description = "a(0) = a(2π)", 
                evaluationPoints = doubleArrayOf(0.0, 2.0 * PI),
                constraintType = ConstraintType.ACCELERATION_DIFFERENCE,
                targetValue = 0.0,
                tolerance = constraintTolerance
            )
        )
    }
    
    /**
     * Generate dwell constraints.
     * Enforces v ≈ 0 and a ≈ 0 during dwell periods.
     */
    private fun generateDwellConstraints(): List<MotionConstraint> {
        val constraints = mutableListOf<MotionConstraint>()
        
        // TDC dwell constraint
        if (params.dwellTdcDeg > 0.0) {
            val dwellStartRad = 0.0
            val dwellEndRad = params.dwellTdcDeg * PI / 180.0
            val dwellPoints = generateConstraintPoints(dwellStartRad, dwellEndRad, 3)
            
            constraints.add(
                MotionConstraint.Equality(
                    name = "tdc_dwell_velocity",
                    description = "Velocity ≈ 0 during TDC dwell",
                    evaluationPoints = dwellPoints,
                    constraintType = ConstraintType.VELOCITY_TARGET,
                    targetValue = 0.0,
                    tolerance = constraintTolerance * 10 // Slightly relaxed for dwells
                )
            )
            
            constraints.add(
                MotionConstraint.Equality(
                    name = "tdc_dwell_acceleration",
                    description = "Acceleration ≈ 0 during TDC dwell",
                    evaluationPoints = dwellPoints,
                    constraintType = ConstraintType.ACCELERATION_TARGET,
                    targetValue = 0.0,
                    tolerance = constraintTolerance * 10
                )
            )
        }
        
        // BDC dwell constraint
        if (params.dwellBdcDeg > 0.0) {
            val bdcStartRad = computeBdcStart()
            val bdcEndRad = bdcStartRad + params.dwellBdcDeg * PI / 180.0
            val dwellPoints = generateConstraintPoints(bdcStartRad, bdcEndRad, 3)
            
            constraints.add(
                MotionConstraint.Equality(
                    name = "bdc_dwell_velocity",
                    description = "Velocity ≈ 0 during BDC dwell",
                    evaluationPoints = dwellPoints,
                    constraintType = ConstraintType.VELOCITY_TARGET,
                    targetValue = 0.0,
                    tolerance = constraintTolerance * 10
                )
            )
            
            constraints.add(
                MotionConstraint.Equality(
                    name = "bdc_dwell_acceleration",
                    description = "Acceleration ≈ 0 during BDC dwell",
                    evaluationPoints = dwellPoints,
                    constraintType = ConstraintType.ACCELERATION_TARGET,
                    targetValue = 0.0,
                    tolerance = constraintTolerance * 10
                )
            )
        }
        
        return constraints
    }
    
    /**
     * Generate constant velocity constraints.
     * Enforces approximately constant velocity during CV segments.
     */
    private fun generateConstantVelocityConstraints(): List<MotionConstraint> {
        val constraints = mutableListOf<MotionConstraint>()
        
        // Compute CV segment boundaries based on upFraction
        val segmentBoundaries = computeSegmentBoundaries()
        
        // Up CV segment
        if (segmentBoundaries.upCvLength > 0.0) {
            val cvPoints = generateConstraintPoints(
                segmentBoundaries.upCvStart, 
                segmentBoundaries.upCvEnd, 
                5
            )
            
            constraints.add(
                MotionConstraint.Equality(
                    name = "up_cv_acceleration",
                    description = "Acceleration ≈ 0 during up CV segment",
                    evaluationPoints = cvPoints,
                    constraintType = ConstraintType.ACCELERATION_TARGET,
                    targetValue = 0.0,
                    tolerance = constraintTolerance * 5
                )
            )
        }
        
        // Down CV segment  
        if (segmentBoundaries.downCvLength > 0.0) {
            val cvPoints = generateConstraintPoints(
                segmentBoundaries.downCvStart,
                segmentBoundaries.downCvEnd,
                5
            )
            
            constraints.add(
                MotionConstraint.Equality(
                    name = "down_cv_acceleration", 
                    description = "Acceleration ≈ 0 during down CV segment",
                    evaluationPoints = cvPoints,
                    constraintType = ConstraintType.ACCELERATION_TARGET,
                    targetValue = 0.0,
                    tolerance = constraintTolerance * 5
                )
            )
        }
        
        return constraints
    }
    
    /**
     * Generate ramp profile constraints.
     * Enforces specific acceleration profiles during ramp segments.
     */
    private fun generateRampConstraints(): List<MotionConstraint> {
        val constraints = mutableListOf<MotionConstraint>()
        
        when (params.rampProfile) {
            RampProfile.Cycloidal -> {
                // For cycloidal: smooth acceleration transitions
                constraints.addAll(generateCycloidalConstraints())
            }
            RampProfile.S5 -> {
                // For 5th order: bounded jerk  
                constraints.addAll(generateS5Constraints())
            }
            RampProfile.S7 -> {
                // For 7th order: bounded jerk derivatives
                constraints.addAll(generateS7Constraints())
            }
        }
        
        return constraints
    }
    
    /**
     * Generate stroke boundary constraints.
     * Ensures proper stroke length and positioning.
     */
    private fun generateStrokeBoundaryConstraints(): List<MotionConstraint> {
        val constraints = mutableListOf<MotionConstraint>()
        
        // Position at TDC should be minimum (relative reference)
        constraints.add(
            MotionConstraint.Equality(
                name = "tdc_position",
                description = "Position at TDC = 0 (reference)",
                evaluationPoints = doubleArrayOf(0.0),
                constraintType = ConstraintType.POSITION_TARGET,
                targetValue = 0.0,
                tolerance = constraintTolerance
            )
        )
        
        // Maximum displacement should match stroke length
        val bdcAngle = computeBdcStart() + params.dwellBdcDeg * PI / 180.0 / 2.0
        constraints.add(
            MotionConstraint.Equality(
                name = "stroke_length",
                description = "Stroke length constraint",
                evaluationPoints = doubleArrayOf(bdcAngle),
                constraintType = ConstraintType.POSITION_TARGET,
                targetValue = params.strokeLengthMm,
                tolerance = constraintTolerance * params.strokeLengthMm
            )
        )
        
        return constraints
    }
    
    /**
     * Generate cycloidal ramp constraints.
     */
    private fun generateCycloidalConstraints(): List<MotionConstraint> {
        // Cycloidal profiles have smooth acceleration transitions
        // We enforce continuity and bounded acceleration
        return listOf(
            MotionConstraint.Inequality(
                name = "acceleration_bounds",
                description = "Bounded acceleration for cycloidal profile",
                evaluationPoints = discretization.createConstraintPoints(2),
                constraintType = ConstraintType.ACCELERATION_MAGNITUDE,
                upperBound = computeAccelerationLimit(),
                tolerance = constraintTolerance
            )
        )
    }
    
    /**
     * Generate S5 (5th order polynomial) constraints.
     */
    private fun generateS5Constraints(): List<MotionConstraint> {
        return listOf(
            MotionConstraint.Inequality(
                name = "jerk_bounds_s5",
                description = "Bounded jerk for S5 profile",
                evaluationPoints = discretization.createConstraintPoints(3),
                constraintType = ConstraintType.JERK_MAGNITUDE,
                upperBound = computeJerkLimit(),
                tolerance = constraintTolerance
            )
        )
    }
    
    /**
     * Generate S7 (7th order polynomial) constraints.
     */
    private fun generateS7Constraints(): List<MotionConstraint> {
        return listOf(
            MotionConstraint.Inequality(
                name = "jerk_bounds_s7",
                description = "Bounded jerk for S7 profile",
                evaluationPoints = discretization.createConstraintPoints(4),
                constraintType = ConstraintType.JERK_MAGNITUDE,
                upperBound = computeJerkLimit() * 0.8, // Tighter for S7
                tolerance = constraintTolerance
            )
        )
    }
    
    // Helper methods for segment computation
    
    private fun computeBdcStart(): Double {
        val fixedBudget = params.dwellTdcDeg + params.dwellBdcDeg +
                params.rampAfterTdcDeg + params.rampBeforeBdcDeg +
                params.rampAfterBdcDeg + params.rampBeforeTdcDeg
        val freeCv = max(0.0, 360.0 - fixedBudget)
        val upCv = freeCv * params.upFraction
        
        return (params.dwellTdcDeg + params.rampAfterTdcDeg + upCv + params.rampBeforeBdcDeg) * PI / 180.0
    }
    
    private fun computeSegmentBoundaries(): SegmentBoundaries {
        val fixedBudget = params.dwellTdcDeg + params.dwellBdcDeg +
                params.rampAfterTdcDeg + params.rampBeforeBdcDeg +
                params.rampAfterBdcDeg + params.rampBeforeTdcDeg
        val freeCv = max(0.0, 360.0 - fixedBudget)
        val upCv = freeCv * params.upFraction
        val downCv = freeCv - upCv
        
        val upCvStart = (params.dwellTdcDeg + params.rampAfterTdcDeg) * PI / 180.0
        val upCvEnd = upCvStart + upCv * PI / 180.0
        
        val bdcEnd = computeBdcStart() + params.dwellBdcDeg * PI / 180.0
        val downCvStart = bdcEnd + params.rampAfterBdcDeg * PI / 180.0
        val downCvEnd = downCvStart + downCv * PI / 180.0
        
        return SegmentBoundaries(
            upCvStart = upCvStart,
            upCvEnd = upCvEnd,
            upCvLength = upCv,
            downCvStart = downCvStart,
            downCvEnd = downCvEnd,
            downCvLength = downCv
        )
    }
    
    /**
     * Generate planetary gearset constraints (UNIFIED CONSTRAINT SYSTEM).
     * 
     * The most critical constraint is: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
     * This ensures planets are tangent to BOTH sun and ring surfaces.
     */
    private fun generatePlanetaryGearsetConstraints(): List<MotionConstraint> {
        val constraints = mutableListOf<MotionConstraint>()
        
        // UNIFIED CONSTRAINT SYSTEM: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
        // This is derived from: contact_point_ring_planet = contact_point_sun_planet
        // For each angle θ, enforce contact point constraint:
        // contact_point_ring_planet(θ) = contact_point_sun_planet(θ)
        // This automatically ensures no overlap and proper meshing
        
        // Generate evaluation points across the 180° ring rotation
        val evaluationPoints = generateConstraintPoints(0.0, PI, 36) // 36 points for 180° (5° intervals)
        
        // Constraint: Ring inner radius = Sun radius + 2 * Planet radius
        constraints.add(
            MotionConstraint.Equality(
                name = "unified_contact_constraint",
                description = "UNIFIED CONSTRAINT: R_ring(θ) = R_sun(θ) + 2*R_planet(θ)",
                evaluationPoints = evaluationPoints,
                constraintType = ConstraintType.UNIFIED_CONTACT_CONSTRAINT,
                targetValue = 0.0,
                tolerance = constraintTolerance
            )
        )
        
        // Constraint: Ring inner radius > Planet radius (no interference)
        constraints.add(
            MotionConstraint.Inequality(
                name = "ring_planet_clearance",
                description = "Ring inner radius must be greater than planet radius",
                evaluationPoints = evaluationPoints,
                constraintType = ConstraintType.RING_PLANET_CLEARANCE,
                upperBound = Double.POSITIVE_INFINITY,
                lowerBound = params.interferenceBuffer, // Minimum clearance
                tolerance = constraintTolerance
            )
        )
        
        // Constraint: Ring outer radius > Ring inner radius
        constraints.add(
            MotionConstraint.Inequality(
                name = "ring_thickness_constraint",
                description = "Ring outer radius must be greater than inner radius",
                evaluationPoints = evaluationPoints,
                constraintType = ConstraintType.RING_THICKNESS_CONSTRAINT,
                upperBound = Double.POSITIVE_INFINITY,
                lowerBound = params.ringThickness, // Minimum ring thickness
                tolerance = constraintTolerance
            )
        )
        
        // Constraint: Gear ratio enforcement through φ(θ) mapping
        // For 2:1 gear ratio: planet rotates 2x faster than ring
        // φ(θ) = 2θ (planet angle vs ring angle)
        constraints.add(
            MotionConstraint.Equality(
                name = "gear_ratio_constraint",
                description = "Gear ratio constraint: φ(θ) = 2θ for 2:1 ratio",
                evaluationPoints = evaluationPoints,
                constraintType = ConstraintType.GEAR_RATIO_CONSTRAINT,
                targetValue = 0.0,
                tolerance = constraintTolerance
            )
        )
        
        // Constraint: Arc-length conjugacy for proper tooth meshing
        // Both gears should have similar arc-lengths because they complete their respective cycles
        constraints.add(
            MotionConstraint.Equality(
                name = "arc_length_conjugacy",
                description = "Arc-length ratio should be ~1.0 for proper meshing",
                evaluationPoints = evaluationPoints,
                constraintType = ConstraintType.ARC_LENGTH_CONJUGACY,
                targetValue = 0.0,
                tolerance = constraintTolerance * 10.0 // Slightly more tolerance for arc-length
            )
        )
        
        // Constraint: Ring symmetry about 0-180° line for 2:1 gear ratio
        // The ring profile should be symmetric because planet rotates 2x faster than ring
        constraints.add(
            MotionConstraint.Equality(
                name = "ring_symmetry_constraint",
                description = "Ring profile symmetry: R_ring(θ) = R_ring(θ + 180°)",
                evaluationPoints = generateConstraintPoints(0.0, PI, 18), // 18 points for 0-180°
                constraintType = ConstraintType.RING_SYMMETRY_CONSTRAINT,
                targetValue = 0.0,
                tolerance = constraintTolerance
            )
        )
        
        // Constraint: Stroke achievability
        // The gearset must be large enough to accommodate the full stroke
        constraints.add(
            MotionConstraint.Inequality(
                name = "stroke_achievability",
                description = "Gearset capacity must accommodate stroke length",
                evaluationPoints = evaluationPoints,
                constraintType = ConstraintType.STROKE_ACHIEVABILITY,
                upperBound = Double.POSITIVE_INFINITY,
                lowerBound = params.strokeLengthMm * 0.8, // 80% of stroke must be achievable
                tolerance = constraintTolerance
            )
        )
        
        return constraints
    }

    private fun generateConstraintPoints(startRad: Double, endRad: Double, numPoints: Int): DoubleArray {
        return DoubleArray(numPoints) { i ->
            val t = i.toDouble() / (numPoints - 1)
            startRad + t * (endRad - startRad)
        }
    }
    
    private fun computeAccelerationLimit(): Double {
        // Estimate reasonable acceleration limit based on stroke and timing
        val typicalRpm = params.rpm
        val omega = typicalRpm * 2.0 * PI / 60.0 // rad/s
        return params.strokeLengthMm * omega * omega * 10.0 // Conservative factor
    }
    
    private fun computeJerkLimit(): Double {
        val accelLimit = computeAccelerationLimit()
        val typicalRpm = params.rpm
        val omega = typicalRpm * 2.0 * PI / 60.0
        return accelLimit * omega * 5.0 // Conservative jerk limit
    }
    
    private data class SegmentBoundaries(
        val upCvStart: Double,
        val upCvEnd: Double,
        val upCvLength: Double,
        val downCvStart: Double,
        val downCvEnd: Double,
        val downCvLength: Double
    )
}

/**
 * Represents a constraint to be enforced by the NLP solver.
 */
sealed class MotionConstraint {
    abstract val name: String
    abstract val description: String
    abstract val evaluationPoints: DoubleArray
    abstract val constraintType: ConstraintType
    abstract val tolerance: Double
    
    data class Equality(
        override val name: String,
        override val description: String,
        override val evaluationPoints: DoubleArray,
        override val constraintType: ConstraintType,
        val targetValue: Double,
        override val tolerance: Double
    ) : MotionConstraint()
    
    data class Inequality(
        override val name: String,
        override val description: String,
        override val evaluationPoints: DoubleArray,
        override val constraintType: ConstraintType,
        val upperBound: Double,
        val lowerBound: Double = -upperBound,
        override val tolerance: Double
    ) : MotionConstraint()
}

/**
 * Types of constraints that can be enforced.
 */
enum class ConstraintType {
    POSITION_TARGET,        // x(θ) = target
    VELOCITY_TARGET,        // v(θ) = target  
    ACCELERATION_TARGET,    // a(θ) = target
    POSITION_DIFFERENCE,    // x(θ1) - x(θ2) = 0
    VELOCITY_DIFFERENCE,    // v(θ1) - v(θ2) = 0
    ACCELERATION_DIFFERENCE,// a(θ1) - a(θ2) = 0
    ACCELERATION_MAGNITUDE, // |a(θ)| ≤ bound
    JERK_MAGNITUDE,        // |da/dθ(θ)| ≤ bound
    VELOCITY_MAGNITUDE,    // |v(θ)| ≤ bound
    
    // Planetary gearset constraint types
    UNIFIED_CONTACT_CONSTRAINT,  // R_ring(θ) = R_sun(θ) + 2*R_planet(θ)
    RING_PLANET_CLEARANCE,       // R_ring(θ) - R_planet(θ) ≥ clearance
    RING_THICKNESS_CONSTRAINT,   // R_ring_outer(θ) - R_ring_inner(θ) ≥ thickness
    GEAR_RATIO_CONSTRAINT,       // φ(θ) = gear_ratio * θ
    ARC_LENGTH_CONJUGACY,        // s_planet(θ) / s_ring(θ) ≈ 1.0
    RING_SYMMETRY_CONSTRAINT,    // R_ring(θ) = R_ring(θ + 180°)
    STROKE_ACHIEVABILITY         // gearset_capacity ≥ stroke_length
}
