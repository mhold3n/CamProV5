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
 * Main activity for CamProV5
 * Contains the tabbed interface with Input and Visualization tabs
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
 * Contains tabs for Input and Visualization
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
        
        // Tab content
        when (selectedTab) {
            0 -> InputTab()
            1 -> VisualizationTab()
        }
    }
}

/**
 * App header component
 * Displays the app title and logo
 */
@Composable
fun AppHeader() {
    // Simple header with app name
    MaterialTheme.typography.h4.let { style ->
        Text(
            text = "CamProV5",
            style = style
        )
    }
}

/**
 * Theme for CamProV5
 * Defines colors, typography, and shapes
 */
@Composable
fun CamProV5Theme(content: @Composable () -> Unit) {
    MaterialTheme(
        colors = MaterialTheme.colors.copy(
            primary = androidx.compose.ui.graphics.Color(0xFF1976D2),
            primaryVariant = androidx.compose.ui.graphics.Color(0xFF0D47A1),
            secondary = androidx.compose.ui.graphics.Color(0xFFFF9800)
        ),
        content = content
    )
}

/**
 * Placeholder for InputTab
 * Will be implemented in a separate file
 */
@Composable
fun InputTab() {
    Text("Input Tab - To be implemented")
}

/**
 * Placeholder for VisualizationTab
 * Will be implemented in a separate file
 */
@Composable
fun VisualizationTab() {
    Text("Visualization Tab - To be implemented")
}