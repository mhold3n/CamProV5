package com.campro.v5.visualization

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.campro.v5.models.GearProfileData
import kotlin.math.*

/**
 * Efficiency analysis visualization component.
 * 
 * This component displays efficiency comparisons between different optimization
 * methods and provides detailed efficiency breakdowns.
 */
@Composable
fun EfficiencyAnalysisVisualization(
    gearProfiles: GearProfileData,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxSize(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Header
            Text(
                text = "Efficiency Analysis",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onSurface
            )
            
            // Efficiency comparison chart
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .background(
                        color = MaterialTheme.colorScheme.surfaceVariant,
                        shape = MaterialTheme.shapes.medium
                    )
                    .padding(16.dp)
            ) {
                EfficiencyComparisonChart(
                    gearProfiles = gearProfiles,
                    modifier = Modifier.fillMaxSize()
                )
            }
            
            // Efficiency breakdown
            EfficiencyBreakdown(gearProfiles = gearProfiles)
        }
    }
}

@Composable
private fun EfficiencyComparisonChart(
    gearProfiles: GearProfileData,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val canvasWidth = size.width
        val canvasHeight = size.height
        
        // Calculate margins
        val marginLeft = 80.dp.toPx()
        val marginRight = 20.dp.toPx()
        val marginTop = 20.dp.toPx()
        val marginBottom = 60.dp.toPx()
        
        val chartWidth = canvasWidth - marginLeft - marginRight
        val chartHeight = canvasHeight - marginTop - marginBottom

        // Guard against non-positive drawable area
        if (chartWidth <= 0f || chartHeight <= 0f) {
            return@Canvas
        }
        
        // Draw axes
        drawEfficiencyAxes(
            chartWidth = chartWidth,
            chartHeight = chartHeight,
            marginLeft = marginLeft,
            marginTop = marginTop
        )
        
        // Draw efficiency bars
        drawEfficiencyBars(
            gearProfiles = gearProfiles,
            chartWidth = chartWidth,
            chartHeight = chartHeight,
            marginLeft = marginLeft,
            marginTop = marginTop
        )
    }
}

private fun DrawScope.drawEfficiencyAxes(
    chartWidth: Float,
    chartHeight: Float,
    marginLeft: Float,
    marginTop: Float
) {
    val strokeWidth = 2.dp.toPx()
    val axisColor = Color.Gray
    
    // X-axis
    drawLine(
        start = Offset(marginLeft, marginTop + chartHeight),
        end = Offset(marginLeft + chartWidth, marginTop + chartHeight),
        color = axisColor,
        strokeWidth = strokeWidth
    )
    
    // Y-axis
    drawLine(
        start = Offset(marginLeft, marginTop),
        end = Offset(marginLeft, marginTop + chartHeight),
        color = axisColor,
        strokeWidth = strokeWidth
    )
    
    // Y-axis labels (0% to 100%)
    for (i in 0..10) {
        val y = marginTop + (chartHeight * i / 10)
        val value = (100 - i * 10).toString()
        
        // Note: Text drawing removed - will be handled by Compose Text components
        
        // Grid line
        drawLine(
            start = Offset(marginLeft, y),
            end = Offset(marginLeft + chartWidth, y),
            color = Color.Gray.copy(alpha = 0.3f),
            strokeWidth = 1.dp.toPx()
        )
    }
}

private fun DrawScope.drawEfficiencyBars(
    gearProfiles: GearProfileData,
    chartWidth: Float,
    chartHeight: Float,
    marginLeft: Float,
    marginTop: Float
) {
    // Guard against non-positive drawable area
    if (chartWidth <= 0f || chartHeight <= 0f) {
        return
    }
    // Simulate efficiency data (in real implementation, this would come from the analysis)
    val methods = listOf("Litvin", "Collocation", "Hybrid")
    val efficiencies = listOf(0.85, 0.82, 0.88) // Example values
    val colors = listOf(
        Color(0xFF2196F3), // Blue
        Color(0xFF4CAF50), // Green
        Color(0xFFFF9800)  // Orange
    )
    
    val safeChartWidth = chartWidth.coerceAtLeast(1f)
    val safeChartHeight = chartHeight.coerceAtLeast(1f)
    val barWidth = (safeChartWidth / (methods.size * 2)).coerceAtLeast(1f)
    val barSpacing = (barWidth / 2).coerceAtLeast(1f)
    
    methods.forEachIndexed { index, method ->
        val efficiency = efficiencies[index]
        val color = colors[index]
        
        val barX = marginLeft + (index * (barWidth + barSpacing)) + barSpacing
        val rawHeight = (safeChartHeight * efficiency).toFloat()
        val barHeight = rawHeight.coerceIn(0f, safeChartHeight)
        val barY = marginTop + safeChartHeight - barHeight
        
        // Draw bar
        if (barHeight > 0f) {
            drawRect(
                color = color,
                topLeft = Offset(barX, barY),
                size = androidx.compose.ui.geometry.Size(barWidth, barHeight)
            )
        }
        
        // Draw efficiency value on top of bar
        // Note: Text drawing removed - will be handled by Compose Text components
        
        // Note: Text drawing removed - will be handled by Compose Text components
    }
}

@Composable
private fun EfficiencyBreakdown(gearProfiles: GearProfileData) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Efficiency Breakdown",
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            // Efficiency metrics
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                EfficiencyMetric(
                    label = "Optimal Method",
                    value = gearProfiles.optimalMethod,
                    color = Color(0xFF4CAF50)
                )
                
                EfficiencyMetric(
                    label = "Efficiency",
                    value = "85%", // Example value
                    color = Color(0xFF2196F3)
                )
                
                EfficiencyMetric(
                    label = "Loss Factor",
                    value = "15%", // Example value
                    color = Color(0xFFFF9800)
                )
            }
            
            // Loss breakdown
            LossBreakdownCard()
        }
    }
}

@Composable
private fun EfficiencyMetric(
    label: String,
    value: String,
    color: Color
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = color
        )
    }
}

@Composable
private fun LossBreakdownCard() {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.3f)
        )
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Text(
                text = "Loss Breakdown",
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onErrorContainer
            )
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                LossItem(
                    label = "Friction",
                    value = "8%",
                    color = Color(0xFFFF5722)
                )
                
                LossItem(
                    label = "Deformation",
                    value = "4%",
                    color = Color(0xFFE91E63)
                )
                
                LossItem(
                    label = "Vibration",
                    value = "3%",
                    color = Color(0xFF9C27B0)
                )
            }
        }
    }
}

@Composable
private fun LossItem(
    label: String,
    value: String,
    color: Color
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onErrorContainer
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold,
            color = color
        )
    }
}


