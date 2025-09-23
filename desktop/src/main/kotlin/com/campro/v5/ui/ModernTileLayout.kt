package com.campro.v5.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.campro.v5.layout.LayoutManager

/**
 * Modern tile-based layout for CamProV5
 * 
 * This replaces the old resizable panel system with a modern, responsive
 * tile environment that provides better UX and scaling behavior.
 */

@Composable
fun ModernTileLayout(
    testingMode: Boolean,
    animationStarted: Boolean,
    allParameters: Map<String, String>,
    layoutManager: LayoutManager,
    onParametersChanged: (Map<String, String>) -> Unit,
    modifier: Modifier = Modifier
) {
    var tileStates by remember { mutableStateOf<Map<String, TileState>>(emptyMap()) }
    
    val tiles = createCamProTiles(
        testingMode = testingMode,
        animationStarted = animationStarted,
        allParameters = allParameters,
        onParametersChanged = onParametersChanged,
        layoutManager = layoutManager
    )
    
    Column(
        modifier = modifier.fillMaxSize()
    ) {
        // App header
        AppHeader(
            testingMode = testingMode,
            animationStarted = animationStarted
        )
        
        // Main tile environment
        TileEnvironment(
            tiles = tiles,
            modifier = Modifier.weight(1f),
            onTileStateChanged = { tileId, newState ->
                tileStates = tileStates.toMutableMap().apply {
                    put(tileId, newState)
                }
            }
        )
    }
}

@Composable
private fun AppHeader(
    testingMode: Boolean,
    animationStarted: Boolean
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "CamProV5 - Cycloidal Animation Generator",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Text(
                    text = "Modern Tile Environment",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
            ) {
                StatusChip(
                    label = "Mode",
                    value = if (testingMode) "Testing" else "Production",
                    isActive = testingMode
                )
                
                StatusChip(
                    label = "Animation",
                    value = if (animationStarted) "Running" else "Stopped",
                    isActive = animationStarted
                )
            }
        }
    }
}

@Composable
private fun StatusChip(
    label: String,
    value: String,
    isActive: Boolean
) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (isActive) 
                MaterialTheme.colorScheme.primaryContainer 
            else 
                MaterialTheme.colorScheme.surfaceVariant
        ),
        modifier = Modifier.padding(4.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = value,
                style = MaterialTheme.typography.bodySmall,
                color = if (isActive) 
                    MaterialTheme.colorScheme.onPrimaryContainer 
                else 
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
