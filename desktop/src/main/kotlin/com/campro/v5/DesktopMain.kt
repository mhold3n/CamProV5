@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.campro.v5

import androidx.compose.desktop.ui.tooling.preview.Preview
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.DpSize
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.WindowState
import androidx.compose.ui.window.application
import androidx.compose.ui.window.rememberWindowState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Animation
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.DataArray
import com.campro.v5.layout.LayoutManager
import com.campro.v5.layout.rememberLayoutManager
import com.campro.v5.ui.*
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.toSize
import com.google.gson.Gson
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.BufferedReader
import java.io.InputStreamReader

fun main(args: Array<String>) {
    val testingMode = args.contains("--testing-mode")
    val enableAgent = args.contains("--enable-agent")

    // Basic CLI parser for key runtime config flags
    val argMap = args.filter { it.startsWith("--") && it.contains("=") }
        .associate {
            val idx = it.indexOf('=')
            it.substring(2, idx) to it.substring(idx + 1)
        }
    val sessionId = argMap["session-id"] ?: java.time.format.DateTimeFormatter.ofPattern("yyyyMMddHHmmss").format(java.time.LocalDateTime.now())
    val logLevel = argMap["log-level"] ?: System.getProperty("campro.log.level", "INFO")
    val defaultLogDir = java.nio.file.Paths.get(System.getProperty("user.home"), "CamProV5", "logs", sessionId).toString()
    val logDir = argMap["log-dir"] ?: System.getProperty("campro.log.dir", defaultLogDir)
    try { java.nio.file.Files.createDirectories(java.nio.file.Paths.get(logDir)) } catch (_: Throwable) {}

    // Publish to system properties for downstream components (MotionLawEngine, diagnostics, etc.)
    runCatching { System.setProperty("campro.log.level", logLevel) }
    runCatching { System.setProperty("log.level", logLevel) }
    runCatching { System.setProperty("campro.log.dir", logDir) }

    // Optional RNG seed passthrough for determinism across runs
    argMap["rng-seed"]?.let { System.setProperty("campro.rng.seed", it) }
    // Ensure app version is visible to SessionInfo and diagnostics
    runCatching { System.setProperty("campro.version", System.getProperty("campro.version") ?: "0.9.0-beta") }

    // Initialize Rust logger early (graceful no-op if native unavailable)
    try {
        com.campro.v5.animation.LitvinNativeStubs.initRustLoggerNative(sessionId, logLevel, logDir)
        println("[CamProV5] Rust logger initialized: sessionId=$sessionId level=$logLevel dir=$logDir")
    } catch (e: Throwable) {
        println("[CamProV5] Rust logger init failed (continuing without native logs): ${e.message}")
    }

    // One-click support bundle creation and exit
    if (args.contains("--make-support-bundle")) {
        val jsonDirs = (argMap["json-dirs"] ?: "")
            .split(';', ',')
            .map { it.trim() }
            .filter { it.isNotEmpty() }
        val out = com.campro.v5.support.SupportBundle.createSupportBundle(sessionId, logDir, jsonDirs)
        println("[CamProV5] Support bundle created at: $out")
        return
    }

    // Inform about native availability (do not crash UI)
    if (!com.campro.v5.animation.LitvinNativeStubs.isNativeAvailable()) {
        val envDir = System.getenv("FEA_ENGINE_LIB_DIR") ?: "(unset)"
        val os = System.getProperty("os.name")
        val arch = System.getProperty("os.arch")
        println("[CamProV5] Native engine DLL not loaded. OS=$os ARCH=$arch FEA_ENGINE_LIB_DIR=$envDir")
        println("[CamProV5] The app will run with limited functionality. Ensure fea_engine.dll and dependencies are accessible.")
    }
    
    // Initialize command processor if in testing mode
    val commandProcessor = if (testingMode) CommandProcessor() else null
    commandProcessor?.start()

    // Decide which windows to show at startup for multi-window mode
    val windowsCsv = argMap["windows"]?.lowercase()?.trim()
    val visibleSet: Set<String> = when {
        !windowsCsv.isNullOrBlank() -> windowsCsv.split(',', ';').map { it.trim() }.filter { it.isNotEmpty() }.toSet()
        else -> emptySet()
    }

    val initialVisibility = mapOf(
        "parameters" to (
            argMap["show-parameters"] == "true" ||
            (visibleSet.isNotEmpty() && "parameters" in visibleSet) ||
            visibleSet.isEmpty()
        ),
        "animation" to (argMap["show-animation"] == "true" || "animation" in visibleSet),
        "plots" to (argMap["show-plots"] == "true" || "plots" in visibleSet),
        "data" to (argMap["show-data"] == "true" || "data" in visibleSet),
        "static" to (argMap["show-static"] == "true" || "static" in visibleSet || argMap["static-profiles-window"] == "true")
    )

    // Enable multi-window if explicitly requested, or if any window flags are present
    val multiWindowEnabled = args.contains("--multi-window") ||
        !windowsCsv.isNullOrBlank() ||
        listOf(
            "show-parameters",
            "show-animation",
            "show-plots",
            "show-data",
            "show-static",
            "static-profiles-window"
        ).any { key -> argMap[key] != null }

    if (multiWindowEnabled) {
        // Seed shared visibility and parameters before application starts
        initialVisibility.forEach { (k, v) ->
            com.campro.v5.SharedAppState.windowVisibility[k] = v
        }
        com.campro.v5.SharedAppState.parameters = emptyMap()
    }
    
    application {
        if (multiWindowEnabled) {
            val layoutManager = rememberLayoutManager()
            com.campro.v5.window.WindowsController(
                testingMode = testingMode,
                layoutManager = layoutManager
            )
        }
        val windowState = rememberWindowState(
            size = DpSize(1400.dp, 1000.dp)
        )
        
        if (!multiWindowEnabled) Window(
            onCloseRequest = {
                commandProcessor?.stop()
                exitApplication()
            },
            title = "CamProV5",
            state = windowState
        ) {
            val layoutManager = rememberLayoutManager()
            val density = LocalDensity.current
            
            // Update layout manager when window size changes
            LaunchedEffect(windowState.size) {
                layoutManager.updateWindowSize(
                    windowState.size.width,
                    windowState.size.height
                )
                println("[UI] window size dp=${windowState.size}")
            }
            // React to per-monitor DPI changes and font scale
            LaunchedEffect(density.density, density.fontScale) {
                layoutManager.updateDensityFactor(density.density)
                println("[UI] density=${density.density} fontScale=${density.fontScale}")
            }
            
            CamProV5App(
                testingMode = testingMode, 
                enableAgent = enableAgent,
                layoutManager = layoutManager
            )
            
            // Report UI initialization event if in testing mode
            if (testingMode) {
                println("EVENT:{\"type\":\"ui_initialized\",\"component\":\"MainWindow\"}")
                // Auto-exit shortly after initialization to support automated verification
                LaunchedEffect(Unit) {
                    try {
                        kotlinx.coroutines.delay(1500)
                    } catch (_: Throwable) {}
                    println("EVENT:{\"type\":\"ui_exit\",\"component\":\"MainWindow\"}")
                    exitApplication()
                }
            }
        }
    }
}

@Composable
@Preview
fun CamProV5App(
    testingMode: Boolean = false, 
    enableAgent: Boolean = false,
    layoutManager: LayoutManager = rememberLayoutManager()
) {
    MaterialTheme {
        var animationStarted by remember { mutableStateOf(false) }
        var allParameters by remember { mutableStateOf(mapOf<String, String>()) }
        
        // Simplified architecture - removed complex management layers
        
        // Use new responsive layout that automatically adapts to screen size
        ResponsiveLayout(
            testingMode = testingMode,
            animationStarted = animationStarted,
            allParameters = allParameters,
            layoutManager = layoutManager,
            onParametersChanged = { parameters ->
                allParameters = parameters
                if (parameters.containsKey("animationStarted") && parameters["animationStarted"] == "true") {
                    animationStarted = true
                }
            }
        )
    }
}


@Composable
private fun ResizablePanelStandardLayout(
    testingMode: Boolean,
    animationStarted: Boolean,
    allParameters: Map<String, String>,
    layoutManager: LayoutManager,
    onParametersChanged: (Map<String, String>) -> Unit
) {
    val spacing = layoutManager.getAppropriateSpacing()
    
    Column(
        modifier = Modifier.fillMaxSize().padding(spacing),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            "CamProV5 - Cycloidal Animation Generator",
            style = MaterialTheme.typography.headlineMedium
        )
        
        Spacer(modifier = Modifier.height(spacing))
        
        // Parameter Input Form with resizable panel
        ResizablePanel(
            panelId = "parameter_panel",
            modifier = Modifier.fillMaxWidth(),
            initialWidth = 400.dp,
            initialHeight = if (layoutManager.shouldUseCompactMode()) 280.dp else 360.dp,
            minWidth = 280.dp,
            minHeight = 200.dp,
            maxWidth = 2000.dp,
            maxHeight = 1400.dp,
            title = "Parameters"
        ) {
            ScrollableParameterInputForm(
                testingMode = testingMode,
                onParametersChanged = onParametersChanged,
                layoutManager = layoutManager
            )
        }
        
        if (animationStarted) {
            Spacer(modifier = Modifier.height(spacing))
            
            // Resizable panels for widgets
            Column(
                modifier = Modifier.fillMaxWidth().weight(1f),
                verticalArrangement = Arrangement.spacedBy(spacing)
            ) {
                // Top row with resizable Animation and Plot panels
                Row(
                    modifier = Modifier.fillMaxWidth().weight(2f),
                    horizontalArrangement = Arrangement.spacedBy(spacing)
                ) {
                    // Animation Widget Panel
                    ResizablePanel(
                        panelId = "animation_panel",
                        modifier = Modifier.weight(1f),
                        initialWidth = 400.dp,
                        initialHeight = if (layoutManager.shouldUseCompactMode()) 280.dp else 360.dp,
                        minWidth = 280.dp,
                        minHeight = 200.dp,
                        maxWidth = 2000.dp,
                        maxHeight = 1400.dp,
                        title = "Animation"
                    ) {
                        ScrollableAnimationWidget(
                            parameters = allParameters,
                            testingMode = testingMode
                        )
                    }
                    
                    // Plot Carousel Widget Panel
                    ResizablePanel(
                        panelId = "plot_panel",
                        modifier = Modifier.weight(1f),
                        initialWidth = 400.dp,
                        initialHeight = if (layoutManager.shouldUseCompactMode()) 280.dp else 360.dp,
                        minWidth = 280.dp,
                        minHeight = 200.dp,
                        maxWidth = 2000.dp,
                        maxHeight = 1400.dp,
                        title = "Plots"
                    ) {
                        ScrollablePlotCarouselWidget(
                            parameters = allParameters,
                            testingMode = testingMode
                        )
                    }
                }
                
                // Bottom row with resizable Data Display panel
                ResizablePanel(
                    panelId = "data_panel",
                    modifier = Modifier.fillMaxWidth().weight(1f),
                    initialWidth = 1200.dp,
                    initialHeight = 300.dp,
                    minWidth = 600.dp,
                    minHeight = 150.dp,
                    maxWidth = 1600.dp,
                    maxHeight = 500.dp,
                    title = "Data Display"
                ) {
                    ScrollableDataDisplayPanel(
                        parameters = allParameters,
                        testingMode = testingMode
                    )
                }
            }
        }
    }
}

@Composable
private fun StandardLayout(
    testingMode: Boolean,
    animationStarted: Boolean,
    allParameters: Map<String, String>,
    layoutManager: LayoutManager,
    onParametersChanged: (Map<String, String>) -> Unit
) {
    val spacing = layoutManager.getAppropriateSpacing()
    
    Column(
        modifier = Modifier.fillMaxSize().padding(spacing),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            "CamProV5 - Cycloidal Animation Generator",
            style = MaterialTheme.typography.headlineMedium
        )
        
        Spacer(modifier = Modifier.height(spacing))
        
        // Parameter Input Form with dynamic sizing
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(0.3f)
        ) {
            ParameterInputForm(
                testingMode = testingMode,
                onParametersChanged = onParametersChanged,
                layoutManager = layoutManager
            )
        }
        
        Spacer(modifier = Modifier.height(spacing))
        
        Column(
            modifier = Modifier.fillMaxWidth().weight(0.7f),
            verticalArrangement = Arrangement.spacedBy(spacing)
        ) {
            // Responsive widget layout - always visible
            if (layoutManager.shouldUseCompactMode()) {
                // Stacked layout for compact mode
                if (!animationStarted) {
                    // Empty state for compact mode
                    Card(modifier = Modifier.fillMaxWidth().weight(1f)) {
                        EmptyStateWidget(
                            message = "Visualizations will appear here after parameters are set",
                            icon = Icons.Default.Animation
                        )
                    }
                } else {
                    // Stacked layout for compact mode with data
                    CompactWidgetLayout(testingMode, allParameters, spacing, animationStarted)
                }
            } else {
                // Side-by-side layout for standard mode
                if (!animationStarted) {
                    // Empty state for standard mode
                    Card(modifier = Modifier.fillMaxWidth().weight(1f)) {
                        EmptyStateWidget(
                            message = "Visualizations will appear here after parameters are set",
                            icon = Icons.Default.Animation
                        )
                    }
                } else {
                    // Side-by-side layout for standard mode with data
                    StandardWidgetLayout(testingMode, allParameters, spacing, animationStarted)
                }
            }
        }
    }
}


@Composable
private fun CompactWidgetLayout(
    testingMode: Boolean,
    allParameters: Map<String, String>,
    spacing: androidx.compose.ui.unit.Dp,
    animationStarted: Boolean = true
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(spacing)
    ) {
        Card(
            modifier = Modifier.fillMaxWidth().weight(0.35f)
        ) {
            if (!animationStarted) {
                EmptyStateWidget(
                    message = "Animation will appear here after parameters are set",
                    icon = Icons.Default.Animation
                )
            } else {
                AnimationWidget(
                    parameters = allParameters,
                    testingMode = testingMode
                )
            }
        }
        
        Card(
            modifier = Modifier.fillMaxWidth().weight(0.35f)
        ) {
            if (!animationStarted) {
                EmptyStateWidget(
                    message = "Plots will appear here after parameters are set",
                    icon = Icons.Default.BarChart
                )
            } else {
                PlotCarouselWidget(
                    parameters = allParameters,
                    testingMode = testingMode
                )
            }
        }
        
        Card(
            modifier = Modifier.fillMaxWidth().weight(0.3f)
        ) {
            if (!animationStarted) {
                EmptyStateWidget(
                    message = "Data will appear here after parameters are set",
                    icon = Icons.Default.DataArray
                )
            } else {
                DataDisplayPanel(
                    parameters = allParameters,
                    testingMode = testingMode
                )
            }
        }
    }
}

@Composable
private fun StandardWidgetLayout(
    testingMode: Boolean,
    allParameters: Map<String, String>,
    spacing: androidx.compose.ui.unit.Dp,
    animationStarted: Boolean = true
) {
    Column(
        modifier = Modifier.fillMaxSize()
    ) {
        // Top row with Animation and Plot Widgets
        Row(
            modifier = Modifier.fillMaxWidth().weight(0.65f),
            horizontalArrangement = Arrangement.spacedBy(spacing)
        ) {
            // Animation Widget
            Card(
                modifier = Modifier.weight(1f).fillMaxHeight()
            ) {
                if (!animationStarted) {
                    EmptyStateWidget(
                        message = "Animation will appear here after parameters are set",
                        icon = Icons.Default.Animation
                    )
                } else {
                    AnimationWidget(
                        parameters = allParameters,
                        testingMode = testingMode
                    )
                }
            }
            
            // Plot Carousel Widget
            Card(
                modifier = Modifier.weight(1f).fillMaxHeight()
            ) {
                if (!animationStarted) {
                    EmptyStateWidget(
                        message = "Plots will appear here after parameters are set",
                        icon = Icons.Default.BarChart
                    )
                } else {
                    PlotCarouselWidget(
                        parameters = allParameters,
                        testingMode = testingMode
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(spacing))
        
        // Bottom row with Data Display Panel
        Card(
            modifier = Modifier.fillMaxWidth().weight(0.35f)
        ) {
            if (!animationStarted) {
                EmptyStateWidget(
                    message = "Data will appear here after parameters are set",
                    icon = Icons.Default.DataArray
                )
            } else {
                DataDisplayPanel(
                    parameters = allParameters,
                    testingMode = testingMode
                )
            }
        }
    }
}

// Validate input parameters
fun validateInput(baseCircleRadius: String, rollingCircleRadius: String, tracingPointDistance: String): String? {
    try {
        val baseRadius = baseCircleRadius.toDouble()
        if (baseRadius <= 0) {
            return "Base circle radius must be positive"
        }
        
        val rollingRadius = rollingCircleRadius.toDouble()
        if (rollingRadius <= 0) {
            return "Rolling circle radius must be positive"
        }
        
        val tracingDistance = tracingPointDistance.toDouble()
        if (tracingDistance < 0) {
            return "Tracing point distance must be non-negative"
        }
        
        return null
    } catch (e: NumberFormatException) {
        return "All parameters must be valid numbers"
    }
}

/**
 * Command processor for handling commands from the testing bridge.
 * This class processes commands sent from the KotlinUIBridge and routes them to the appropriate components.
 */
class CommandProcessor {
    private var isRunning = false
    private var inputThread: Thread? = null
    
    fun start() {
        if (isRunning) return
        
        isRunning = true
        inputThread = Thread {
            val reader = BufferedReader(InputStreamReader(System.`in`))
            
            while (isRunning) {
                try {
                    val line = reader.readLine()
                    if (line != null) {
                        processCommand(line)
                    }
                } catch (e: Exception) {
                    if (isRunning) {
                        println("ERROR:{\"type\":\"command_processing_error\",\"message\":\"${e.message}\"}")
                    }
                }
            }
        }
        inputThread?.start()
    }
    
    fun stop() {
        isRunning = false
        inputThread?.interrupt()
    }
    
    private fun processCommand(command: String) {
        try {
            // Check if the command starts with COMMAND: prefix and extract the JSON part
            val jsonPart = if (command.startsWith("COMMAND:")) {
                command.substring("COMMAND:".length)
            } else {
                command
            }
            
            val gson = Gson()
            val commandData = gson.fromJson(jsonPart, Map::class.java)
            
            when (commandData["command"]) {
                "click" -> {
                    val component = commandData["params"]?.let { (it as? Map<*, *>)?.get("component") as? String } ?: ""
                    
                    // Process click command
                    println("EVENT:{\"type\":\"command_executed\",\"command\":\"click\",\"component\":\"$component\"}")
                }
                "set_value" -> {
                    val params = commandData["params"] as? Map<*, *>
                    val component = params?.get("component") as? String ?: ""
                    val value = params?.get("value") as? String ?: ""
                    
                    // Process set value command
                    println("EVENT:{\"type\":\"command_executed\",\"command\":\"set_value\",\"component\":\"$component\",\"value\":\"$value\"}")
                }
                "select_tab" -> {
                    val params = commandData["params"] as? Map<*, *>
                    val component = params?.get("component") as? String ?: ""
                    val value = params?.get("value") as? String ?: ""
                    
                    // Process tab selection command
                    println("EVENT:{\"type\":\"command_executed\",\"command\":\"select_tab\",\"component\":\"$component\",\"value\":\"$value\"}")
                }
                "gesture" -> {
                    val params = commandData["params"] as? Map<*, *>
                    val component = params?.get("component") as? String ?: ""
                    val action = params?.get("action") as? String ?: ""
                    val offsetX = params?.get("offset_x") as? String ?: ""
                    val offsetY = params?.get("offset_y") as? String ?: ""
                    
                    // Process gesture command
                    println("EVENT:{\"type\":\"command_executed\",\"command\":\"gesture\",\"component\":\"$component\",\"action\":\"$action\",\"offset_x\":\"$offsetX\",\"offset_y\":\"$offsetY\"}")
                }
                "get_state" -> {
                    val params = commandData["params"] as? Map<*, *>
                    val component = params?.get("component") as? String ?: ""
                    
                    // Return component state
                    println("EVENT:{\"type\":\"command_executed\",\"command\":\"get_state\",\"component\":\"$component\",\"state\":{}}")
                }
                "reset" -> {
                    val params = commandData["params"] as? Map<*, *>
                    val component = params?.get("component") as? String ?: ""
                    
                    // Process reset command
                    println("EVENT:{\"type\":\"command_executed\",\"command\":\"reset\",\"component\":\"$component\"}")
                }
                "export" -> {
                    val params = commandData["params"] as? Map<*, *>
                    val component = params?.get("component") as? String ?: ""
                    val format = params?.get("format") as? String ?: ""
                    val filePath = params?.get("file_path") as? String ?: ""
                    
                    // Process export command
                    println("EVENT:{\"type\":\"command_executed\",\"command\":\"export\",\"component\":\"$component\",\"format\":\"$format\",\"file_path\":\"$filePath\"}")
                }
                "import" -> {
                    val params = commandData["params"] as? Map<*, *>
                    val component = params?.get("component") as? String ?: ""
                    val filePath = params?.get("file_path") as? String ?: ""
                    
                    // Process import command
                    println("EVENT:{\"type\":\"command_executed\",\"command\":\"import\",\"component\":\"$component\",\"file_path\":\"$filePath\"}")
                }
                "generate" -> {
                    val params = commandData["params"] as? Map<*, *>
                    val component = params?.get("component") as? String ?: ""
                    val type = params?.get("type") as? String ?: ""
                    
                    // Process generate command
                    println("EVENT:{\"type\":\"command_executed\",\"command\":\"generate\",\"component\":\"$component\",\"type\":\"$type\"}")
                }
                else -> {
                    println("EVENT:{\"type\":\"error\",\"message\":\"Unknown command: ${commandData["command"]}\"}")
                }
            }
        } catch (e: Exception) {
            println("EVENT:{\"type\":\"error\",\"message\":\"Error processing command: ${e.message}\"}")
        }
    }
}
