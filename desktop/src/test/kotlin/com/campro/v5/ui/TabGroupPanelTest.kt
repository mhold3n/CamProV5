package com.campro.v5.ui

import androidx.compose.ui.unit.DpOffset
import androidx.compose.ui.unit.dp
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

/**
 * Tests for tab group interactions such as adding, menu actions and reordering.
 */
class TabGroupPanelTest {

    @Test
    fun addTabAddsPanelToGroup() {
        val manager = DockingManager()
        manager.registerPanel("p1", "One")
        val groupId = manager.createTabGroup(listOf("p1"), DpOffset.Zero, 100.dp to 100.dp)

        // Simulate add tab handler from TabGroupPanel
        val newId = "tab_add_test"
        manager.registerPanel(newId, "New Tab")
        manager.addToTabGroup(newId, groupId)
        manager.setActiveTabPanel(groupId, newId)

        val group = manager.tabGroups.value[groupId]!!
        assertEquals(2, group.panelIds.size)
        assertEquals(newId, group.activePanel)
    }

    @Test
    fun menuActionCloseAllRemovesGroup() {
        val manager = DockingManager()
        manager.registerPanel("p1", "One")
        manager.registerPanel("p2", "Two")
        val groupId = manager.createTabGroup(listOf("p1", "p2"), DpOffset.Zero, 100.dp to 100.dp)

        // Simulate menu action which closes all tabs
        manager.unregisterPanel("p1")
        manager.unregisterPanel("p2")

        assertFalse(manager.tabGroups.value.containsKey(groupId))
    }

    @Test
    fun reorderTabsChangesOrder() {
        val manager = DockingManager()
        manager.registerPanel("p1", "One")
        manager.registerPanel("p2", "Two")
        manager.registerPanel("p3", "Three")
        val groupId = manager.createTabGroup(listOf("p1", "p2", "p3"), DpOffset.Zero, 100.dp to 100.dp)

        // Move first tab to the right
        manager.moveTab(groupId, "p1", 1)
        var group = manager.tabGroups.value[groupId]!!
        assertEquals(listOf("p2", "p1", "p3"), group.panelIds)

        // Move last tab to the front
        manager.moveTab(groupId, "p3", -2)
        group = manager.tabGroups.value[groupId]!!
        assertEquals(listOf("p3", "p2", "p1"), group.panelIds)
    }
}

