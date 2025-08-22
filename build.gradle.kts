/**
 * Aggregator build script for the parent Gradle project ':CamProV5'.
 * This exists to satisfy IDE/Gradle multi-project discovery when including ':CamProV5:desktop'.
 * No build logic is required here; all configuration lives in subprojects.
 */

plugins {
    base
}

description = "CamProV5 aggregator module (no build logic)"

// Intentionally empty: subprojects (e.g., :CamProV5:desktop) configure their own plugins and repositories.