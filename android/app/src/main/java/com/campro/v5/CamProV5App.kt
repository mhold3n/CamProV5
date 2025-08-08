package com.campro.v5

import android.app.Application

/**
 * Main application class for CamProV5
 * Initializes application components including the native library
 */
class CamProV5App : Application() {
    override fun onCreate() {
        super.onCreate()
        // Initialize application components
        NativeLibrary.initialize()
    }
}