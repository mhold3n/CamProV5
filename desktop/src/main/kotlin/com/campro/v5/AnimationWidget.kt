package com.campro.v5

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.*
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.ZoomIn
import androidx.compose.material.icons.filled.ZoomOut
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import com.campro.v5.animation.*
import com.campro.v5.fea.ComputationManager
import com.campro.v5.fea.ComputationResult
import com.campro.v5.fea.ComputationType
import com.campro.v5.fea.getResultsFile
import kotlinx.coroutines.launch
import java.io.File

/**
 * A widget that displays an animation based on the provided parameters.
 * This widget supports multiple animation types: cycloidal, component-based, and FEA-based.
 * 
 * @param parameters Map of parameter names to values
 * @param testingMode Whether the widget is in testing mode
 */
@Composable
fun AnimationWidget(
    parameters: Map<String, String>,
    testingMode: Boolean = false
) {
    // Create animation manager
    val animationManager = remember { AnimationManager() }
    val coroutineScope = rememberCoroutineScope()
    val computationManager = remember { ComputationManager() }
    
    // Animation state
    var isPlaying by remember { mutableStateOf(true) }
    var animationSpeed by remember { mutableStateOf(1f) }
    var scale by remember { mutableStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }
    var selectedAnimationType by remember { mutableStateOf(AnimationType.COMPONENT_BASED) }
    var feaJobId by remember { mutableStateOf<String?>(null) }
    var feaResultsFile by remember { mutableStateOf<File?>(null) }
    
    // Create the animation engine if not already created
    LaunchedEffect(selectedAnimationType, parameters) {
        try {
            // Create and set the animation engine with proper error handling
            val engine = animationManager.createAndSetEngine(selectedAnimationType, parameters)
            
            // If FEA-based animation, set the results file if available
            if (selectedAnimationType == AnimationType.FEA_BASED && feaResultsFile != null) {
                try {
                    (engine as? FeaBasedAnimationEngine)?.setFeaResults(feaResultsFile!!)
                } catch (e: Exception) {
                    println("WARNING: Failed to set FEA results: ${e.message}")
                }
            }
            
            // Ensure the engine is properly initialized by setting the initial angle to 0
            engine.setAngle(0f)
            
            println("Animation engine initialized successfully: ${selectedAnimationType.name}")
        } catch (e: Exception) {
            println("ERROR: Failed to initialize animation engine: ${e.message}")
            e.printStackTrace()
        }
    }
    
    // Animation value using proper frame timing
    var currentAnimationValue by remember { mutableStateOf(0f) }
    var lastFrameTimeNanos by remember { mutableStateOf(0L) }
    
    // Constants for animation timing
    val baseRpmValue = 60f // 1 rotation per second
    val degreesPerRotation = 360f
    
    // Use withFrameNanos for proper frame timing
    LaunchedEffect(isPlaying, animationSpeed) {
        // Only run the animation loop if playing
        if (!isPlaying) return@LaunchedEffect
        
        // Log animation start
        println("DEBUG: Starting animation loop with speed: $animationSpeed")
        
        // Animation loop with proper frame timing
        while (isPlaying) {
            withFrameNanos { frameTimeNanos ->
                if (lastFrameTimeNanos != 0L) {
                    // Calculate elapsed time in seconds
                    val elapsedSeconds = (frameTimeNanos - lastFrameTimeNanos) / 1_000_000_000.0f
                    
                    // Calculate angle change based on speed and elapsed time
                    // This ensures consistent speed across different devices and frame rates
                    val angleChange = (degreesPerRotation * baseRpmValue * animationSpeed * elapsedSeconds)
                    
                    // Update the animation value
                    currentAnimationValue = (currentAnimationValue + angleChange) % degreesPerRotation
                    
                    // Log frame timing for debugging (uncomment if needed)
                    // println("DEBUG: Frame time: ${elapsedSeconds * 1000}ms, Angle change: $angleChange°")
                    
                    // Set the angle in the animation engine
                    animationManager.getCurrentEngine()?.setAngle(currentAnimationValue)
                }
                
                // Store the current frame time for the next frame
                lastFrameTimeNanos = frameTimeNanos
            }
        }
    }
    
    // Debug information for animation state
    val debugInfo = remember { mutableStateOf("") }
    
    // Update debug info periodically
    LaunchedEffect(Unit) {
        while (true) {
            val engine = animationManager.getCurrentEngine()
            if (engine != null) {
                val angle = engine.getCurrentAngle()
                debugInfo.value = "Angle: ${angle.toInt()}° | Speed: ${animationSpeed}x"
            }
            kotlinx.coroutines.delay(100)
        }
    }
    
    // Observe FEA computation results
    feaJobId?.let { jobId ->
        val result by computationManager.getResult(jobId)?.collectAsState() ?: remember { mutableStateOf<ComputationResult?>(null) }
        
        LaunchedEffect(result) {
            if (result is ComputationResult.Success) {
                feaResultsFile = result.getResultsFile()
                
                // Update the FEA-based animation engine with the results
                if (selectedAnimationType == AnimationType.FEA_BASED) {
                    (animationManager.getCurrentEngine() as? FeaBasedAnimationEngine)?.setFeaResults(feaResultsFile!!)
                }
            }
        }
    }
    
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp)
    ) {
        
        // Animation controls
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Play/Pause button
            IconButton(
                onClick = {
                    isPlaying = !isPlaying
                    if (testingMode) {
                        println("EVENT:{\"type\":\"button_clicked\",\"component\":\"${if (isPlaying) "PlayButton" else "PauseButton"}\"}")
                    }
                }
            ) {
                Icon(
                    imageVector = if (isPlaying) Icons.Filled.Pause else Icons.Filled.PlayArrow,
                    contentDescription = if (isPlaying) "Pause" else "Play"
                )
            }
            
            // Speed control
            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text("Speed: ${animationSpeed}x")
                Slider(
                    value = animationSpeed,
                    onValueChange = { newValue ->
                        try {
                            // Validate the speed value is within a safe range
                            val safeValue = newValue.coerceIn(0.1f, 3f)
                            animationSpeed = safeValue
                            if (testingMode) {
                                println("EVENT:{\"type\":\"slider_changed\",\"component\":\"SpeedSlider\",\"value\":\"$safeValue\"}")
                            }
                        } catch (e: Exception) {
                            // If any error occurs, reset to a safe default value
                            animationSpeed = 1f
                            println("WARNING: Error setting animation speed: ${e.message}. Reset to default value.")
                        }
                    },
                    valueRange = 0.1f..3f,
                    steps = 29,
                    modifier = Modifier.width(200.dp)
                )
            }
            
            // Zoom controls
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(
                    onClick = {
                        scale = (scale * 0.8f).coerceAtLeast(0.1f)
                        if (testingMode) {
                            println("EVENT:{\"type\":\"button_clicked\",\"component\":\"ZoomOutButton\"}")
                        }
                    }
                ) {
                    Icon(
                        imageVector = Icons.Filled.ZoomOut,
                        contentDescription = "Zoom Out"
                    )
                }
                
                Text("${(scale * 100).toInt()}%")
                
                IconButton(
                    onClick = {
                        scale = (scale * 1.2f).coerceAtMost(5f)
                        if (testingMode) {
                            println("EVENT:{\"type\":\"button_clicked\",\"component\":\"ZoomInButton\"}")
                        }
                    }
                ) {
                    Icon(
                        imageVector = Icons.Filled.ZoomIn,
                        contentDescription = "Zoom In"
                    )
                }
            }
            
            // Reset view button
            IconButton(
                onClick = {
                    scale = 1f
                    offset = Offset.Zero
                    if (testingMode) {
                        println("EVENT:{\"type\":\"button_clicked\",\"component\":\"ResetViewButton\"}")
                    }
                }
            ) {
                Icon(
                    imageVector = Icons.Filled.Refresh,
                    contentDescription = "Reset View"
                )
            }
            
            // Export button
            IconButton(
                onClick = {
                    // Export functionality to be implemented
                    if (testingMode) {
                        println("EVENT:{\"type\":\"button_clicked\",\"component\":\"ExportButton\"}")
                    }
                }
            ) {
                Icon(
                    imageVector = Icons.Filled.Save,
                    contentDescription = "Export"
                )
            }
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Animation type selector
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Animation Type: ")
            
            
            // Component-based animation button
            Button(
                onClick = {
                    selectedAnimationType = AnimationType.COMPONENT_BASED
                    if (testingMode) {
                        println("EVENT:{\"type\":\"button_clicked\",\"component\":\"ComponentBasedAnimationButton\"}")
                    }
                },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (selectedAnimationType == AnimationType.COMPONENT_BASED) 
                        MaterialTheme.colorScheme.primary 
                    else 
                        MaterialTheme.colorScheme.secondary
                ),
                modifier = Modifier.padding(horizontal = 4.dp)
            ) {
                Text("Component-Based")
            }
            
            // FEA-based animation button
            Button(
                onClick = {
                    selectedAnimationType = AnimationType.FEA_BASED
                    
                    // Run FEA analysis if not already done
                    if (feaResultsFile == null && feaJobId == null) {
                        coroutineScope.launch {
                            // Create a temporary model file
                            val modelFile = File.createTempFile("fea_model_", ".json")
                            modelFile.deleteOnExit()
                            
                            // Write model data to the file
                            modelFile.writeText("""
                                {
                                    "model": "cam",
                                    "parameters": ${parameters.entries.joinToString(prefix = "{", postfix = "}", transform = { "\"${it.key}\": \"${it.value}\"" })}
                                }
                            """.trimIndent())
                            
                            // Start the computation
                            feaJobId = computationManager.startComputation(
                                modelFile = modelFile,
                                parameters = parameters,
                                type = ComputationType.GENERAL
                            )
                        }
                    }
                    
                    if (testingMode) {
                        println("EVENT:{\"type\":\"button_clicked\",\"component\":\"FeaBasedAnimationButton\"}")
                    }
                },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (selectedAnimationType == AnimationType.FEA_BASED) 
                        MaterialTheme.colorScheme.primary 
                    else 
                        MaterialTheme.colorScheme.secondary
                ),
                modifier = Modifier.padding(horizontal = 4.dp)
            ) {
                Text("FEA-Based")
            }
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Animation canvas
        Box(
            modifier = Modifier
                .weight(1f)  // Use weight instead of fillMaxSize for better layout control
                .clip(MaterialTheme.shapes.medium)
                .background(MaterialTheme.colorScheme.surface)
                .pointerInput(Unit) {
                    detectTransformGestures { _, pan, zoom, _ ->
                        scale = (scale * zoom).coerceIn(0.1f, 5f)
                        offset += pan
                        if (testingMode) {
                            println("EVENT:{\"type\":\"gesture\",\"component\":\"AnimationCanvas\",\"action\":\"pan_zoom\",\"scale\":\"$scale\",\"offset\":\"$offset\"}")
                        }
                    }
                }
        ) {
            // Use BoxWithConstraints to get the actual size of the container
            BoxWithConstraints(modifier = Modifier.matchParentSize()) {
                val boxWidth = constraints.maxWidth.toFloat()
                val boxHeight = constraints.maxHeight.toFloat()
                
                // Log canvas dimensions for debugging
                LaunchedEffect(boxWidth, boxHeight) {
                    println("DEBUG: Canvas container size: ${boxWidth}x${boxHeight}")
                }
                
                Canvas(
                    modifier = Modifier.matchParentSize()
                ) {
                    val canvasWidth = size.width
                    val canvasHeight = size.height
                    
                    // Draw background to ensure the canvas is visible
                    drawRect(
                        color = Color(0xFFF5F5F5), // Light gray background
                        size = size
                    )
                    
                    // Draw a border to clearly define the animation area
                    drawRect(
                        color = Color(0xFF888888), // Medium gray border
                        size = size,
                        style = Stroke(width = 1f)
                    )
                    
                    try {
                        // Get the current engine safely
                        val currentEngine = animationManager.getCurrentEngine()
                        
                        if (currentEngine != null) {
                            // Draw the animation frame
                            currentEngine.drawFrame(
                                drawScope = this,
                                canvasWidth = canvasWidth,
                                canvasHeight = canvasHeight,
                                scale = scale,
                                offset = offset
                            )
                        } else {
                            // Draw a message if no engine is available
                            // Draw a red circle to indicate an error
                            drawCircle(
                                color = Color.Red,
                                radius = 50f,
                                center = Offset(canvasWidth / 2, canvasHeight / 2)
                            )
                        }
                    } catch (e: Exception) {
                        // Draw error indicator if drawing fails
                        // Draw a red X to indicate an error
                        val crossSize = 50f
                        drawLine(
                            color = Color.Red,
                            start = Offset(canvasWidth / 2 - crossSize, canvasHeight / 2 - crossSize),
                            end = Offset(canvasWidth / 2 + crossSize, canvasHeight / 2 + crossSize),
                            strokeWidth = 5f
                        )
                        drawLine(
                            color = Color.Red,
                            start = Offset(canvasWidth / 2 - crossSize, canvasHeight / 2 + crossSize),
                            end = Offset(canvasWidth / 2 + crossSize, canvasHeight / 2 - crossSize),
                            strokeWidth = 5f
                        )
                        println("ERROR: Failed to draw animation frame: ${e.message}")
                        e.printStackTrace()
                    }
                }
            }
            
            // Overlay information - use matchParentSize and Box for proper z-ordering
            Box(modifier = Modifier.matchParentSize()) {
                Column(
                    modifier = Modifier.align(Alignment.TopStart).padding(16.dp),
                    horizontalAlignment = Alignment.Start
                ) {
                Text(
                    "Angle: ${currentAnimationValue.toInt()}°",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                
                // Display parameters based on animation type
                when (selectedAnimationType) {
                    AnimationType.COMPONENT_BASED -> {
                        Text(
                            "Base Circle Radius: ${parameters["base_circle_radius"] ?: "25"} mm",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            "Max Lift: ${parameters["max_lift"] ?: "10"} mm",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            "Cam Duration: ${parameters["cam_duration"] ?: "180"} deg",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            "Rise Duration: ${parameters["rise_duration"] ?: "90"} deg",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            "RPM: ${parameters["rpm"] ?: "3000"}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }
                    AnimationType.FEA_BASED -> {
                        Text(
                            "FEA Analysis: ${if (feaResultsFile != null) "Complete" else if (feaJobId != null) "Running..." else "Not Started"}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            "Base Circle Radius: ${parameters["base_circle_radius"] ?: "25"} mm",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            "Max Lift: ${parameters["max_lift"] ?: "10"} mm",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }
                }
                }
            }
        }
    }
    
    // Clean up resources when the composable is disposed
    DisposableEffect(Unit) {
        onDispose {
            animationManager.dispose()
            computationManager.shutdown()
        }
    }
}