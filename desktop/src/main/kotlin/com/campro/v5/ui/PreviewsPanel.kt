package com.campro.v5.ui

import androidx.compose.runtime.Composable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.ui.Modifier
import androidx.compose.material3.Text
import com.campro.v5.animation.MotionLawEngine

/**
 * Minimal stub for the PreviewsPanel used by AnimationWidget. This can be
 * replaced with the full implementation later. For now, it simply renders
 * a placeholder to keep the desktop module compiling.
 */
@Composable
fun PreviewsPanel(engine: MotionLawEngine, modifier: Modifier = Modifier) {
    Box(modifier = modifier.fillMaxWidth()) {
        Text("Previews are not yet implemented in the desktop UI preview panel.")
    }
}
