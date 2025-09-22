package com.campro.v5.animation

import com.campro.v5.data.litvin.LitvinTablesDTO
import com.campro.v5.data.litvin.PlanetDTO
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.lang.reflect.Field

class RenderingPathSelectionTest {
    private fun setPrivateField(target: Any, name: String, value: Any?) {
        val f: Field = target.javaClass.getDeclaredField(name)
        f.isAccessible = true
        f.set(target, value)
    }

    @Test
    fun `litvin active when tables present`() {
        val engine = MotionLawEngine()
        val planet = PlanetDTO(
            centerX = listOf(1.0),
            centerY = listOf(2.0),
            spinPsiDeg = listOf(0.0),
            journalX = listOf(3.0),
            journalY = listOf(4.0),
            pistonS = listOf(5.0),
        )
        val tables = LitvinTablesDTO(alphaDeg = listOf(0.0), planets = listOf(planet))
        setPrivateField(engine, "litvinTables", tables)
        assertTrue(engine.isLitvinActive())
    }

    @Test
    fun `when litvin selected but tables absent, engine should not fallback-render`() {
        val engine = MotionLawEngine()
        // Ensure no tables present
        setPrivateField(engine, "litvinTables", null)
        // Calling getComponentPositions currently falls back; desired behavior is to avoid legacy visuals.
        val positions = engine.getComponentPositions(0.0)
        // Expect a neutral 'no data' posture (all zeros) rather than SHM-like or cam-at-origin proxy coupling rod=piston
        assertEquals(0f, positions.pistonPosition.y)
        assertEquals(0f, positions.rodPosition.y)
        assertEquals(0f, positions.camPosition.x)
        assertEquals(0f, positions.camPosition.y)
    }
}


