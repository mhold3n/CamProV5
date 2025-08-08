package com.campro.v5

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp

/**
 * Input tab with parameter forms
 * Contains sections for different parameter categories
 */
@Composable
fun InputTab() {
    val scrollState = rememberScrollState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(scrollState)
    ) {
        Text(
            text = "CamProV5 - Cam Profile Designer",
            style = MaterialTheme.typography.h5,
            fontWeight = FontWeight.Bold
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = "Enter parameters below and click 'Compute' to generate the cam profile",
            style = MaterialTheme.typography.body1
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Geometry parameters section
        ParameterSection(
            title = "Cam Geometry Parameters",
            parameters = listOf(
                ParameterField("Piston Diameter", "mm", 50.0),
                ParameterField("Stroke", "mm", 10.0),
                ParameterField("Chamber CC", "cc", 25.0),
                ParameterField("TDC Angle", "deg", 0.0),
                ParameterField("BDC Dwell", "deg", 45.0),
                ParameterField("TDC Dwell", "deg", 45.0)
            )
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Motion profile parameters section
        ParameterSection(
            title = "Motion Profile Parameters",
            parameters = listOf(
                ParameterField("Profile Type", "", 0.0, isNumeric = false, options = listOf("Cycloidal", "Modified Sine", "Polynomial")),
                ParameterField("Acceleration Factor", "", 1.0),
                ParameterField("Jerk Factor", "", 1.0),
                ParameterField("Smoothing Factor", "", 0.5)
            )
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Material parameters section
        ParameterSection(
            title = "Material Parameters",
            parameters = listOf(
                ParameterField("Cam Material", "", 0.0, isNumeric = false, options = listOf("Steel", "Aluminum", "Titanium")),
                ParameterField("Young's Modulus", "GPa", 200.0),
                ParameterField("Poisson's Ratio", "", 0.3),
                ParameterField("Density", "kg/m³", 7850.0)
            )
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Simulation parameters section
        ParameterSection(
            title = "Simulation Parameters",
            parameters = listOf(
                ParameterField("RPM", "rpm", 1000.0),
                ParameterField("Time Steps", "", 100.0),
                ParameterField("Convergence Tolerance", "", 0.001),
                ParameterField("Max Iterations", "", 100.0)
            )
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Compute button
        Button(
            onClick = { /* Trigger computation */ },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Compute & Update Plots")
        }
    }
}

/**
 * Parameter section component
 * Displays a group of related parameters with a title
 */
@Composable
fun ParameterSection(title: String, parameters: List<ParameterField>) {
    Column {
        Text(
            text = title,
            style = MaterialTheme.typography.h6,
            fontWeight = FontWeight.Bold
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        parameters.forEach { parameter ->
            ParameterInput(parameter)
            Spacer(modifier = Modifier.height(4.dp))
        }
    }
}

/**
 * Parameter input component
 * Displays a single parameter input field with label and unit
 */
@Composable
fun ParameterInput(parameter: ParameterField) {
    var value by remember { mutableStateOf(parameter.defaultValue.toString()) }
    
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = "${parameter.name} ${if (parameter.unit.isNotEmpty()) "(${parameter.unit})" else ""}:",
            modifier = Modifier.weight(1f)
        )
        
        if (parameter.isNumeric) {
            OutlinedTextField(
                value = value,
                onValueChange = { value = it },
                modifier = Modifier.width(120.dp),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true
            )
        } else {
            // Dropdown for non-numeric parameters
            var expanded by remember { mutableStateOf(false) }
            var selectedIndex by remember { mutableStateOf(0) }
            
            Box(modifier = Modifier.width(120.dp)) {
                OutlinedButton(
                    onClick = { expanded = true },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(parameter.options.getOrNull(selectedIndex) ?: "")
                }
                
                DropdownMenu(
                    expanded = expanded,
                    onDismissRequest = { expanded = false }
                ) {
                    parameter.options.forEachIndexed { index, option ->
                        DropdownMenuItem(
                            onClick = {
                                selectedIndex = index
                                expanded = false
                            }
                        ) {
                            Text(option)
                        }
                    }
                }
            }
        }
    }
}

/**
 * Parameter field data class
 * Represents a single parameter with name, unit, and default value
 */
data class ParameterField(
    val name: String,
    val unit: String,
    val defaultValue: Double,
    val isNumeric: Boolean = true,
    val options: List<String> = emptyList()
)