package com.campro.v5.config

import java.util.Properties
import java.io.File

/**
 * Feature flag configuration for CamProV5.
 * 
 * This system allows for gradual rollout of new features, particularly
 * the collocation solver, with safe fallbacks and user control.
 */
object FeatureFlags {
    
    // Default feature flag values
    private val defaultFlags = mapOf(
        "collocation.enabled" to false,
        "collocation.force_fallback" to false,
        "collocation.ui_visible" to true,
        "collocation.python_bridge_enabled" to true,
        "collocation.litvin_constraints_enabled" to false,
        "collocation.numerical_guards_enabled" to true,
        "advanced.dense_validation_enabled" to false,
        "advanced.matrix_caching_enabled" to true,
        "debug.verbose_logging" to false,
        "debug.performance_metrics" to false
    )
    
    // Runtime flag overrides
    private val runtimeFlags = mutableMapOf<String, Boolean>()
    
    // Configuration file path
    private val configFile = File(System.getProperty("user.home"), ".campro/feature_flags.properties")
    
    init {
        loadConfigFile()
    }
    
    /**
     * Check if a feature flag is enabled.
     */
    fun isEnabled(flagName: String): Boolean {
        // Priority: runtime override > config file > default
        return runtimeFlags[flagName] ?: loadFromConfig(flagName) ?: defaultFlags[flagName] ?: false
    }
    
    /**
     * Set a feature flag at runtime (temporary override).
     */
    fun setFlag(flagName: String, enabled: Boolean) {
        runtimeFlags[flagName] = enabled
    }
    
    /**
     * Clear runtime override for a flag.
     */
    fun clearFlag(flagName: String) {
        runtimeFlags.remove(flagName)
    }
    
    /**
     * Get all active flags with their values.
     */
    fun getAllFlags(): Map<String, Boolean> {
        val allFlags = defaultFlags.toMutableMap()
        
        // Apply config file overrides
        loadAllFromConfig().forEach { (key, value) ->
            allFlags[key] = value
        }
        
        // Apply runtime overrides
        runtimeFlags.forEach { (key, value) ->
            allFlags[key] = value
        }
        
        return allFlags
    }
    
    /**
     * Save current flags to config file.
     */
    fun saveConfig() {
        try {
            configFile.parentFile?.mkdirs()
            val properties = Properties()
            
            getAllFlags().forEach { (key, value) ->
                properties.setProperty(key, value.toString())
            }
            
            configFile.outputStream().use { output ->
                properties.store(output, "CamProV5 Feature Flags")
            }
        } catch (e: Exception) {
            println("Warning: Could not save feature flags config: ${e.message}")
        }
    }
    
    private fun loadConfigFile() {
        if (!configFile.exists()) return
        
        try {
            val properties = Properties()
            configFile.inputStream().use { input ->
                properties.load(input)
            }
            
            properties.forEach { (key, value) ->
                val flagName = key.toString()
                val flagValue = value.toString().toBoolean()
                // Don't override runtime flags
                if (!runtimeFlags.containsKey(flagName)) {
                    runtimeFlags[flagName] = flagValue
                }
            }
        } catch (e: Exception) {
            println("Warning: Could not load feature flags config: ${e.message}")
        }
    }
    
    private fun loadFromConfig(flagName: String): Boolean? {
        if (!configFile.exists()) return null
        
        try {
            val properties = Properties()
            configFile.inputStream().use { input ->
                properties.load(input)
            }
            return properties.getProperty(flagName)?.toBoolean()
        } catch (e: Exception) {
            return null
        }
    }
    
    private fun loadAllFromConfig(): Map<String, Boolean> {
        if (!configFile.exists()) return emptyMap()
        
        try {
            val properties = Properties()
            configFile.inputStream().use { input ->
                properties.load(input)
            }
            return properties.map { (key, value) ->
                key.toString() to value.toString().toBoolean()
            }.toMap()
        } catch (e: Exception) {
            return emptyMap()
        }
    }
    
    // Convenience methods for specific features
    object Collocation {
        fun isEnabled(): Boolean = isEnabled("collocation.enabled")
        fun isForceFallback(): Boolean = isEnabled("collocation.force_fallback")
        fun isUIVisible(): Boolean = isEnabled("collocation.ui_visible")
        fun isPythonBridgeEnabled(): Boolean = isEnabled("collocation.python_bridge_enabled")
        fun areLitvinConstraintsEnabled(): Boolean = isEnabled("collocation.litvin_constraints_enabled")
        fun areNumericalGuardsEnabled(): Boolean = isEnabled("collocation.numerical_guards_enabled")
    }
    
    object Advanced {
        fun isDenseValidationEnabled(): Boolean = isEnabled("advanced.dense_validation_enabled")
        fun isMatrixCachingEnabled(): Boolean = isEnabled("advanced.matrix_caching_enabled")
    }
    
    object Debug {
        fun isVerboseLoggingEnabled(): Boolean = isEnabled("debug.verbose_logging")
        fun arePerformanceMetricsEnabled(): Boolean = isEnabled("debug.performance_metrics")
    }
    
    /**
     * Get a description of all feature flags for UI display.
     */
    fun getFeatureDescriptions(): Map<String, String> = mapOf(
        "collocation.enabled" to "Enable collocation solver as primary method",
        "collocation.force_fallback" to "Force fallback to piecewise even if collocation is available",
        "collocation.ui_visible" to "Show collocation option in UI profile solver dropdown",
        "collocation.python_bridge_enabled" to "Enable Python CasADi + IPOPT bridge",
        "collocation.litvin_constraints_enabled" to "Enable Litvin conjugacy constraints in NLP",
        "collocation.numerical_guards_enabled" to "Enable numerical methods and guards",
        "advanced.dense_validation_enabled" to "Enable comprehensive post-solve validation",
        "advanced.matrix_caching_enabled" to "Cache collocation matrices for performance",
        "debug.verbose_logging" to "Enable detailed logging for debugging",
        "debug.performance_metrics" to "Enable performance measurement and reporting"
    )
}
