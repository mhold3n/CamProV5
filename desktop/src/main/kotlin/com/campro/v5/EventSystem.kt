package com.campro.v5

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentHashMap

/**
 * A centralized event system for the CamProV5 application.
 * This class provides a way for components to emit and listen for events.
 */
object EventSystem {
    private val scope = CoroutineScope(
        SupervisorJob() + Dispatchers.IO + CoroutineName("EventSystem")
    )
    private val eventFlows = ConcurrentHashMap<String, MutableSharedFlow<Event>>()
    
    /**
     * Emit an event to all listeners of the specified event type.
     *
     * @param event The event to emit
     */
    fun emit(event: Event) {
        // Check testing mode dynamically to ensure it reflects the current state
        val testingMode = System.getProperty("testing.mode") == "true"
        
        // Log event if in testing mode - do this synchronously to ensure it's available immediately
        if (testingMode) {
            val eventJson = event.toJson()
            println("EVENT:$eventJson")
        }
        
        // Get the flow before launching the coroutine to ensure it exists
        val flow = getOrCreateFlow(event.type)
        
        // Try to emit the event synchronously first if possible (for better performance)
        if (flow.tryEmit(event)) {
            return
        }
        
        // If synchronous emission fails (e.g., buffer is full), fall back to asynchronous emission
        scope.launch {
            flow.emit(event)
        }
    }
    
    /**
     * Get a flow of events of the specified type.
     *
     * @param eventType The type of events to listen for
     * @return A flow of events of the specified type
     */
    fun events(eventType: String): SharedFlow<Event> {
        return getOrCreateFlow(eventType).asSharedFlow()
    }
    
    /**
     * Get or create a flow for the specified event type.
     *
     * @param eventType The type of events
     * @return A mutable shared flow for the specified event type
     */
    private fun getOrCreateFlow(eventType: String): MutableSharedFlow<Event> {
        return eventFlows.getOrPut(eventType) {
            // Increase buffer capacity to handle high-volume event processing
            MutableSharedFlow(
                replay = 16,                // Increase replay cache for late subscribers
                extraBufferCapacity = 4000  // Significantly larger buffer for performance tests
            )
        }
    }
    
    /**
     * Emit multiple events efficiently as a batch.
     * This is more efficient than emitting events individually for large numbers of events.
     *
     * @param events The list of events to emit
     */
    fun emitBatch(events: List<Event>) {
        // Group events by type for more efficient processing
        val eventsByType = events.groupBy { it.type }
        
        // Process each group of events
        eventsByType.forEach { (type, eventsOfType) ->
            val flow = getOrCreateFlow(type)
            
            // Log events in testing mode
            val testingMode = System.getProperty("testing.mode") == "true"
            if (testingMode) {
                eventsOfType.forEach { event ->
                    println("EVENT:${event.toJson()}")
                }
            }
            
            // Emit events in a single coroutine for each type
            scope.launch {
                eventsOfType.forEach { event ->
                    // Try synchronous emission first
                    if (!flow.tryEmit(event)) {
                        // Fall back to suspending emission if needed
                        flow.emit(event)
                    }
                }
            }
        }
    }
    
    /**
     * Collect events of the specified type with a callback.
     * This is more efficient than using the flow directly for high-volume event processing.
     *
     * @param eventType The type of events to collect
     * @param callback The callback to invoke for each event
     * @return A job that can be cancelled to stop collection
     */
    fun collectEvents(eventType: String, callback: (Event) -> Unit): Job {
        return scope.launch {
            events(eventType).collect { event ->
                callback(event)
            }
        }
    }
    
    /**
     * Clear all event flows.
     * This is useful for testing and resetting the event system.
     */
    fun clear() {
        eventFlows.clear()
    }
}

/**
 * Base class for all events in the system.
 */
abstract class Event {
    /**
     * The type of the event.
     * This is used to route events to the appropriate listeners.
     */
    abstract val type: String
    
    /**
     * Convert the event to a JSON string.
     * This is used for logging and testing.
     */
    open fun toJson(): String {
        return "{\"type\":\"$type\"}"
    }
}

/**
 * Event emitted when a UI component is clicked.
 *
 * @param component The ID of the component that was clicked
 * @param params Additional parameters for the click event
 */
data class ClickEvent(
    val component: String,
    val params: Map<String, Any> = emptyMap()
) : Event() {
    override val type: String = "click"
    
    override fun toJson(): String {
        val paramsJson = if (params.isNotEmpty()) {
            ", \"params\": ${params.entries.joinToString(", ", "{", "}") { "\"${it.key}\":\"${it.value}\"" }}"
        } else {
            ""
        }
        return "{\"type\":\"$type\",\"component\":\"$component\"$paramsJson}"
    }
}

/**
 * Event emitted when a value in a UI component is changed.
 *
 * @param component The ID of the component whose value changed
 * @param value The new value
 */
data class ValueChangedEvent(
    val component: String,
    val value: String
) : Event() {
    override val type: String = "value_changed"
    
    override fun toJson(): String {
        return "{\"type\":\"$type\",\"component\":\"$component\",\"value\":\"$value\"}"
    }
}

/**
 * Event emitted when a tab is selected in a tabbed component.
 *
 * @param component The ID of the tabbed component
 * @param tab The ID or name of the selected tab
 */
data class TabSelectedEvent(
    val component: String,
    val tab: String
) : Event() {
    override val type: String = "tab_selected"
    
    override fun toJson(): String {
        return "{\"type\":\"$type\",\"component\":\"$component\",\"tab\":\"$tab\"}"
    }
}

/**
 * Event emitted when a gesture is performed on a UI component.
 *
 * @param component The ID of the component on which the gesture was performed
 * @param action The type of gesture (e.g., "pan", "zoom", "pan_zoom")
 * @param params Additional parameters for the gesture
 */
data class GestureEvent(
    val component: String,
    val action: String,
    val params: Map<String, Any> = emptyMap()
) : Event() {
    override val type: String = "gesture"
    
    override fun toJson(): String {
        val paramsJson = if (params.isNotEmpty()) {
            params.entries.joinToString(", ", ", ", "") { "\"${it.key}\":\"${it.value}\"" }
        } else {
            ""
        }
        return "{\"type\":\"$type\",\"component\":\"$component\",\"action\":\"$action\"$paramsJson}"
    }
}

/**
 * Event emitted when an animation is started.
 *
 * @param component The ID of the animation component
 * @param params Animation parameters
 */
data class AnimationStartedEvent(
    val component: String,
    val params: Map<String, Any> = emptyMap()
) : Event() {
    override val type: String = "animation_started"
    
    override fun toJson(): String {
        val paramsJson = if (params.isNotEmpty()) {
            ", \"params\": ${params.entries.joinToString(", ", "{", "}") { "\"${it.key}\":\"${it.value}\"" }}"
        } else {
            ""
        }
        return "{\"type\":\"$type\",\"component\":\"$component\"$paramsJson}"
    }
}

/**
 * Event emitted when an animation is paused.
 *
 * @param component The ID of the animation component
 */
data class AnimationPausedEvent(
    val component: String
) : Event() {
    override val type: String = "animation_paused"
    
    override fun toJson(): String {
        return "{\"type\":\"$type\",\"component\":\"$component\"}"
    }
}

/**
 * Event emitted when data is exported from a component.
 *
 * @param component The ID of the component from which data was exported
 * @param filePath The path to which the data was exported
 * @param format The format of the exported data
 */
data class ExportEvent(
    val component: String,
    val filePath: String,
    val format: String
) : Event() {
    override val type: String = "export"
    
    override fun toJson(): String {
        return "{\"type\":\"$type\",\"component\":\"$component\",\"file_path\":\"$filePath\",\"format\":\"$format\"}"
    }
}

/**
 * Event emitted when data is imported to a component.
 *
 * @param component The ID of the component to which data was imported
 * @param filePath The path from which the data was imported
 */
data class ImportEvent(
    val component: String,
    val filePath: String
) : Event() {
    override val type: String = "import"
    
    override fun toJson(): String {
        return "{\"type\":\"$type\",\"component\":\"$component\",\"file_path\":\"$filePath\"}"
    }
}

/**
 * Event emitted when a report or other content is generated.
 *
 * @param component The ID of the component that generated the content
 * @param contentType The type of content that was generated
 * @param filePath The path to which the content was saved
 */
data class GenerateEvent(
    val component: String,
    val contentType: String,
    val filePath: String? = null
) : Event() {
    override val type: String = "generate"
    
    override fun toJson(): String {
        val filePathJson = if (filePath != null) {
            ", \"file_path\":\"$filePath\""
        } else {
            ""
        }
        return "{\"type\":\"$type\",\"component\":\"$component\",\"content_type\":\"$contentType\"$filePathJson}"
    }
}

/**
 * Event emitted when an error occurs.
 *
 * @param message The error message
 * @param component The ID of the component where the error occurred (optional)
 */
data class ErrorEvent(
    val message: String,
    val component: String? = null
) : Event() {
    override val type: String = "error"
    
    override fun toJson(): String {
        val componentJson = if (component != null) {
            ", \"component\":\"$component\""
        } else {
            ""
        }
        return "{\"type\":\"$type\",\"message\":\"$message\"$componentJson}"
    }
}

/**
 * Event emitted when a command is executed.
 *
 * @param command The command that was executed
 * @param component The ID of the component on which the command was executed
 * @param params Additional parameters for the command
 */
data class CommandExecutedEvent(
    val command: String,
    val component: String,
    val params: Map<String, Any> = emptyMap()
) : Event() {
    override val type: String = "command_executed"
    
    override fun toJson(): String {
        val paramsJson = if (params.isNotEmpty()) {
            ", \"params\": ${params.entries.joinToString(", ", "{", "}") { "\"${it.key}\":\"${it.value}\"" }}"
        } else {
            ""
        }
        return "{\"type\":\"$type\",\"command\":\"$command\",\"component\":\"$component\"$paramsJson}"
    }
}

/**
 * Extension function to emit a click event.
 *
 * @param component The ID of the component that was clicked
 * @param params Additional parameters for the click event
 */
fun emitClick(component: String, params: Map<String, Any> = emptyMap()) {
    EventSystem.emit(ClickEvent(component, params))
}

/**
 * Extension function to emit a value changed event.
 *
 * @param component The ID of the component whose value changed
 * @param value The new value
 */
fun emitValueChanged(component: String, value: String) {
    EventSystem.emit(ValueChangedEvent(component, value))
}

/**
 * Extension function to emit a tab selected event.
 *
 * @param component The ID of the tabbed component
 * @param tab The ID or name of the selected tab
 */
fun emitTabSelected(component: String, tab: String) {
    EventSystem.emit(TabSelectedEvent(component, tab))
}

/**
 * Extension function to emit a gesture event.
 *
 * @param component The ID of the component on which the gesture was performed
 * @param action The type of gesture (e.g., "pan", "zoom", "pan_zoom")
 * @param params Additional parameters for the gesture
 */
fun emitGesture(component: String, action: String, params: Map<String, Any> = emptyMap()) {
    EventSystem.emit(GestureEvent(component, action, params))
}

/**
 * Extension function to emit an animation started event.
 *
 * @param component The ID of the animation component
 * @param params Animation parameters
 */
fun emitAnimationStarted(component: String, params: Map<String, Any> = emptyMap()) {
    EventSystem.emit(AnimationStartedEvent(component, params))
}

/**
 * Extension function to emit an animation paused event.
 *
 * @param component The ID of the animation component
 */
fun emitAnimationPaused(component: String) {
    EventSystem.emit(AnimationPausedEvent(component))
}

/**
 * Extension function to emit an export event.
 *
 * @param component The ID of the component from which data was exported
 * @param filePath The path to which the data was exported
 * @param format The format of the exported data
 */
fun emitExport(component: String, filePath: String, format: String) {
    EventSystem.emit(ExportEvent(component, filePath, format))
}

/**
 * Extension function to emit an import event.
 *
 * @param component The ID of the component to which data was imported
 * @param filePath The path from which the data was imported
 */
fun emitImport(component: String, filePath: String) {
    EventSystem.emit(ImportEvent(component, filePath))
}

/**
 * Extension function to emit a generate event.
 *
 * @param component The ID of the component that generated the content
 * @param contentType The type of content that was generated
 * @param filePath The path to which the content was saved
 */
fun emitGenerate(component: String, contentType: String, filePath: String? = null) {
    EventSystem.emit(GenerateEvent(component, contentType, filePath))
}

/**
 * Extension function to emit an error event.
 *
 * @param message The error message
 * @param component The ID of the component where the error occurred (optional)
 */
fun emitError(message: String, component: String? = null) {
    EventSystem.emit(ErrorEvent(message, component))
}

/**
 * Extension function to emit a command executed event.
 *
 * @param command The command that was executed
 * @param component The ID of the component on which the command was executed
 * @param params Additional parameters for the command
 */
fun emitCommandExecuted(command: String, component: String, params: Map<String, Any> = emptyMap()) {
    EventSystem.emit(CommandExecutedEvent(command, component, params))
}

/**
 * Event emitted when a layout change occurs.
 *
 * @param action The type of layout change (e.g., "window_size_changed", "template_changed", "density_changed")
 * @param params Additional parameters for the layout change
 */
data class LayoutEvent(
    val action: String,
    val params: Map<String, Any> = emptyMap()
) : Event() {
    override val type: String = "layout"
    
    override fun toJson(): String {
        val paramsJson = if (params.isNotEmpty()) {
            ", \"params\": ${params.entries.joinToString(", ", "{", "}") { "\"${it.key}\":\"${it.value}\"" }}"
        } else {
            ""
        }
        return "{\"type\":\"$type\",\"action\":\"$action\"$paramsJson}"
    }
}

/**
 * Extension function to emit a layout event.
 *
 * @param action The type of layout change (e.g., "window_size_changed", "template_changed", "density_changed")
 * @param params Additional parameters for the layout change
 */
fun emitLayout(action: String, params: Map<String, Any> = emptyMap()) {
    EventSystem.emit(LayoutEvent(action, params))
}