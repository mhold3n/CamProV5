package com.campro.v5.optimization

import com.campro.v5.models.OptimizationParameters
import com.campro.v5.models.OptimizationResult
import com.campro.v5.models.MotionLawData
import com.campro.v5.models.GearProfileData
import com.campro.v5.models.ToothProfileData
import com.campro.v5.models.FEAAnalysisData
import com.campro.v5.pipeline.UnifiedOptimizationBridge
import io.mockk.*
import kotlinx.coroutines.*
import kotlinx.coroutines.test.*
import org.junit.jupiter.api.*
import org.junit.jupiter.api.Assertions.*
import java.nio.file.Paths
import java.util.concurrent.CompletableFuture

/**
 * Tests for OptimizationStateManager.
 */
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class OptimizationStateManagerTest {

    private lateinit var mockBridge: UnifiedOptimizationBridge
    private lateinit var stateManager: OptimizationStateManager
    private lateinit var testDispatcher: TestDispatcher

    @BeforeEach
    fun setup() {
        mockBridge = mockk()
        testDispatcher = StandardTestDispatcher()
        Dispatchers.setMain(testDispatcher)
        stateManager = OptimizationStateManager(mockBridge)
    }

    @AfterEach
    fun tearDown() {
        Dispatchers.resetMain()
        clearAllMocks()
    }

    @Test
    fun `test initial state is idle`() {
        assertEquals(OptimizationState.Idle, stateManager.getCurrentState())
        assertFalse(stateManager.isRunning())
    }

    @Test
    fun `test successful optimization flow`() = runTest {
        // Given
        val parameters = OptimizationParameters.createDefault()
        val outputDir = Paths.get("./test_output")
        val expectedResult = createTestOptimizationResult()

        val future = CompletableFuture.completedFuture(expectedResult)
        coEvery { mockBridge.runOptimization(any(), any()) } returns future

        // When
        val job = launch {
            stateManager.runOptimization(parameters, outputDir)
        }

        // Then
        advanceUntilIdle()

        assertEquals(OptimizationState.Completed(expectedResult), stateManager.getCurrentState())
        assertFalse(stateManager.isRunning())

        job.cancel()
    }

    @Test
    fun `test failed optimization flow`() = runTest {
        // Given
        val parameters = OptimizationParameters.createDefault()
        val outputDir = Paths.get("./test_output")
        val expectedError = RuntimeException("Test error")

        val future = CompletableFuture.failedFuture<OptimizationResult>(expectedError)
        coEvery { mockBridge.runOptimization(any(), any()) } returns future

        // When
        val job = launch {
            stateManager.runOptimization(parameters, outputDir)
        }

        // Then
        advanceUntilIdle()

        val currentState = stateManager.getCurrentState()
        assertTrue(currentState is OptimizationState.Failed)
        assertEquals(expectedError, (currentState as OptimizationState.Failed).error)
        assertFalse(stateManager.isRunning())

        job.cancel()
    }

    @Test
    fun `test cancel optimization`() = runTest {
        // Given
        val parameters = OptimizationParameters.createDefault()
        val outputDir = Paths.get("./test_output")

        // Mock a long-running operation
        val future = CompletableFuture<OptimizationResult>()
        coEvery { mockBridge.runOptimization(any(), any()) } returns future

        // When
        val job = launch {
            stateManager.runOptimization(parameters, outputDir)
        }

        // Wait for running state
        advanceUntilIdle()
        assertTrue(stateManager.isRunning())

        // Cancel optimization
        stateManager.cancelOptimization()
        advanceUntilIdle()

        // Then
        assertEquals(OptimizationState.Idle, stateManager.getCurrentState())
        assertFalse(stateManager.isRunning())

        job.cancel()
    }

    @Test
    fun `test reset state`() = runTest {
        // Given
        val parameters = OptimizationParameters.createDefault()
        val outputDir = Paths.get("./test_output")
        val expectedResult = createTestOptimizationResult()

        val future = CompletableFuture.completedFuture(expectedResult)
        coEvery { mockBridge.runOptimization(any(), any()) } returns future

        // Run optimization to completion
        val job = launch {
            stateManager.runOptimization(parameters, outputDir)
        }
        advanceUntilIdle()

        // Verify completed state
        assertTrue(stateManager.getCurrentState() is OptimizationState.Completed)

        // When
        stateManager.resetState()

        // Then
        assertEquals(OptimizationState.Idle, stateManager.getCurrentState())
        assertFalse(stateManager.isRunning())

        job.cancel()
    }

    @Test
    fun `test state flow emissions`() = runTest {
        // Given
        val parameters = OptimizationParameters.createDefault()
        val outputDir = Paths.get("./test_output")
        val expectedResult = createTestOptimizationResult()

        val future = CompletableFuture.completedFuture(expectedResult)
        coEvery { mockBridge.runOptimization(any(), any()) } returns future

        val states = mutableListOf<OptimizationState>()
        val stateJob = launch {
            stateManager.optimizationState.collect { state ->
                states.add(state)
            }
        }

        // When
        val job = launch {
            stateManager.runOptimization(parameters, outputDir)
        }
        advanceUntilIdle()

        // Then
        assertTrue(states.contains(OptimizationState.Idle))
        assertTrue(states.any { it is OptimizationState.Running })
        assertTrue(states.any { it is OptimizationState.Completed })

        stateJob.cancel()
        job.cancel()
    }

    private fun createTestOptimizationResult(): OptimizationResult = OptimizationResult(
        status = "success",
        motionLaw = MotionLawData(
            thetaDeg = doubleArrayOf(0.0, 90.0, 180.0),
            displacement = doubleArrayOf(0.0, 50.0, 100.0),
            velocity = doubleArrayOf(100.0, 0.0, -100.0),
            acceleration = doubleArrayOf(0.0, -1000.0, 0.0),
        ),
        optimalProfiles = GearProfileData(
            rSun = doubleArrayOf(110.0, 115.0, 120.0),
            rPlanet = doubleArrayOf(175.0, 180.0, 185.0),
            rRingInner = doubleArrayOf(460.0, 470.0, 480.0),
            gearRatio = 2.0,
            optimalMethod = "litvin",
            efficiencyAnalysis = null,
        ),
        toothProfiles = ToothProfileData(
            sunTeeth = null,
            planetTeeth = null,
            ringTeeth = null,
        ),
        feaAnalysis = FEAAnalysisData(
            maxStress = 150.0,
            naturalFrequencies = doubleArrayOf(100.0, 200.0, 300.0),
            fatigueLife = 1000000.0,
            modeShapes = arrayOf("Mode 1", "Mode 2", "Mode 3"),
            recommendations = arrayOf("Recommendation 1", "Recommendation 2"),
        ),
        executionTime = 1.5,
    )
}
