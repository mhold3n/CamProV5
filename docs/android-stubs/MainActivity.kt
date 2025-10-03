package com.campro.v5

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.material.MaterialTheme
import androidx.compose.material.Tab
import androidx.compose.material.TabRow
import androidx.compose.material.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier

/**
 * Main activity for CamProV5 Android app
 * This is a stub for future Android implementation
 * 
 * When re-implementing:
 * 1. Adapt desktop UI components for mobile screens
 * 2. Integrate with Python optimization pipeline
 * 3. Handle mobile-specific performance considerations
 * 4. Implement proper navigation and state management
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            CamProV5Theme {
                MainScreen()
            }
        }
    }
}

/**
 * Main screen with tabbed layout
 * Stub implementation - will be replaced with full mobile UI
 */
@Composable
fun MainScreen() {
    var selectedTab by remember { mutableStateOf(0) }
    
    Column {
        // App header
        AppHeader()
        
        // Tab row
        TabRow(selectedTabIndex = selectedTab) {
            Tab(
                selected = selectedTab == 0,
                onClick = { selectedTab = 0 },
                text = { Text("Inputs") }
            )
            Tab(
                selected = selectedTab == 1,
                onClick = { selectedTab = 1 },
                text = { Text("Visualization") }
            )
        }
        
        // Tab content - stubs for future implementation
        when (selectedTab) {
            0 -> InputTab()
            1 -> VisualizationTab()
        }
    }
}

/**
 * App header component
 * Stub implementation
 */
@Composable
fun AppHeader() {
    // Simple header with app name
    Text(
        text = "CamProV5",
        style = MaterialTheme.typography.h4
    )
}

/**
 * Input tab stub
 * Future implementation will include:
 * - Parameter input forms adapted for mobile
 * - Touch-friendly controls
 * - Mobile-optimized validation
 */
@Composable
fun InputTab() {
    Text("Input Tab - Future Implementation")
}

/**
 * Visualization tab stub
 * Future implementation will include:
 * - Mobile-optimized charts and graphs
 * - Touch interactions for zoom/pan
 * - Responsive layout for different screen sizes
 */
@Composable
fun VisualizationTab() {
    Text("Visualization Tab - Future Implementation")
}

/**
 * Theme stub
 * Future implementation will match desktop theme with mobile adaptations
 */
@Composable
fun CamProV5Theme(content: @Composable () -> Unit) {
    MaterialTheme {
        content()
    }
}
