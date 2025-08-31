/**
 * Build configuration for the CamProV5 desktop module.
 * 
 * This file is a placeholder for the actual implementation.
 * The actual implementation would use the Compose for Desktop plugin
 * to build a desktop version of the Android UI.
 */

import java.util.Locale

plugins {
    kotlin("jvm") version "1.9.21"
    id("org.jetbrains.compose") version "1.8.2"
    id("com.github.johnrengelman.shadow") version "8.1.1"
    id("org.jlleitschuh.gradle.ktlint") version "12.1.1"
}

version = project.version as String

kotlin {
    // Ensure Gradle and IDE use JDK 17 toolchain for Kotlin
    jvmToolchain(17)
}

tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
    kotlinOptions {
        // Target JDK 17 for Compose Desktop and IDE import consistency
        jvmTarget = "17"
        freeCompilerArgs += "-opt-in=org.jetbrains.compose.ExperimentalComposeLibrary"
        freeCompilerArgs += "-opt-in=androidx.compose.material3.ExperimentalMaterial3Api"
        freeCompilerArgs += "-opt-in=androidx.compose.foundation.ExperimentalFoundationApi"
        freeCompilerArgs += "-opt-in=androidx.compose.ui.ExperimentalComposeUiApi"
    }
}

repositories {
    google()
    mavenCentral()
    maven("https://maven.pkg.jetbrains.space/public/p/compose/dev")
}

dependencies {
    // This would reference a shared module containing code common to both Android and desktop
    // implementation(project(":shared"))
    
    // Compose for Desktop dependencies
    implementation(compose.desktop.currentOs)
    implementation("org.jetbrains.compose.material3:material3:1.8.2")
    implementation(compose.material)
    implementation(compose.materialIconsExtended)
    implementation(compose.ui)
    implementation(compose.foundation)
    implementation(compose.runtime)
    
    // JSON
    implementation("com.google.code.gson:gson:2.13.1")
    
    // Logging (quick wins)
    implementation("org.slf4j:slf4j-api:2.0.17")
    runtimeOnly("ch.qos.logback:logback-classic:1.5.18")
    runtimeOnly("net.logstash.logback:logstash-logback-encoder:7.4")
    
    // Testing dependencies
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter-api:5.13.4")
    testImplementation("org.junit.jupiter:junit-jupiter-params:5.13.4")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.13.4")
    
    // Kotest for property-based testing
    testImplementation("io.kotest:kotest-runner-junit5:5.9.1")
    testImplementation("io.kotest:kotest-assertions-core:5.9.1")
    testImplementation("io.kotest:kotest-property:5.9.1")
}


// Add Rust build tasks (conditional on -DincludeNative=true)
val includeNative = (System.getProperty("includeNative") ?: "false").toBoolean()
if (includeNative) {
    val nativeClean = System.getProperty("nativeClean") == "true"

    tasks.register<Exec>("buildRustLibraries") {
        group = "build"
        description = "Builds the Rust native libraries"

        val crateDir = file("${project.rootDir}/CamProV5/camprofw/rust/fea-engine")
        workingDir = crateDir

        // Use appropriate command based on OS
        val isWindows = System.getProperty("os.name").lowercase(Locale.ROOT).contains("win")
        commandLine = if (isWindows) {
            listOf("cmd", "/c", "cargo", "build", "--release")
        } else {
            listOf("cargo", "build", "--release")
        }

        // Break cache when toolchain changes (cargo/rustc version)
        val cargoVersionProvider = providers.exec {
            commandLine("cargo", "--version")
        }.standardOutput.asText
        val rustcVersionProvider = providers.exec {
            commandLine("rustc", "--version")
        }.standardOutput.asText

        // Only run if Rust code or toolchain has changed
        inputs.dir(file("${project.rootDir}/CamProV5/camprofw/rust/fea-engine/src"))
        inputs.file(file("${project.rootDir}/CamProV5/camprofw/rust/fea-engine/Cargo.toml"))
        inputs.property("cargoVersion", cargoVersionProvider)
        inputs.property("rustcVersion", rustcVersionProvider)
        outputs.dir(file("${project.rootDir}/CamProV5/camprofw/rust/fea-engine/target/release"))

        // Optional clean to avoid stale artifacts
        doFirst {
            if (nativeClean) {
                if (isWindows) {
                    project.exec {
                        workingDir = crateDir
                        commandLine("cmd", "/c", "cargo", "clean", "-p", "fea-engine")
                    }
                } else {
                    project.exec {
                        workingDir = crateDir
                        commandLine("cargo", "clean", "-p", "fea-engine")
                    }
                }
            }
        }
    }

    tasks.register<Copy>("copyRustLibraries") {
        group = "build"
        description = "Copies the built Rust libraries to the resources directory"

        dependsOn("buildRustLibraries")

        // Determine OS-specific paths and file names
        val osName = System.getProperty("os.name").lowercase(Locale.ROOT)
        val isWindows = osName.contains("win")
        val isMac = osName.contains("mac")
        
        val libExtension = when {
            isWindows -> "dll"
            isMac -> "dylib"
            else -> "so"
        }

        val osDir = when {
            isWindows -> "windows"
            isMac -> "mac"
            else -> "linux"
        }

        val archDir = "x86_64"

        val crateDir = file("${project.rootDir}/CamProV5/camprofw/rust/fea-engine")
        // Cargo artifact name differs by platform: Windows has no 'lib' prefix, Unix-like do.
        val cargoArtifactBaseName = if (isWindows) "fea_engine" else "libfea_engine"
        val builtArtifact = file("${crateDir.path}/target/release/${cargoArtifactBaseName}.${libExtension}")

        val resourcesOsArchDir = file("${project.projectDir}/src/main/resources/native/${osDir}/${archDir}")

        // Declare inputs/outputs for up-to-date checks
        inputs.file(builtArtifact)
        outputs.files(
            file("${resourcesOsArchDir.path}/${if (isWindows) "" else "lib"}campro_motion.${libExtension}"),
            file("${resourcesOsArchDir.path}/${if (isWindows) "" else "lib"}campro_fea.${libExtension}"),
            file("${resourcesOsArchDir.path}/${cargoArtifactBaseName}.${libExtension}")
        )

        // Create resource directories if they don't exist and verify artifact exists
        doFirst {
            mkdir(resourcesOsArchDir)
            if (!builtArtifact.exists()) {
                throw GradleException("Rust artifact not found: ${builtArtifact}. Ensure cargo build --release produced the cdylib. Expected crate name 'fea_engine'.")
            }
        }

        // Copy and rename to the names the JVM loader expects
        from(builtArtifact)
        into(resourcesOsArchDir)
        rename("${cargoArtifactBaseName}.${libExtension}", "${if (isWindows) "" else "lib"}campro_motion.${libExtension}")

        doLast {
            // Also copy a second copy as campro_fea for FEA entry points (same library for now)
            copy {
                from(builtArtifact)
                into(resourcesOsArchDir)
                rename("${cargoArtifactBaseName}.${libExtension}", "${if (isWindows) "" else "lib"}campro_fea.${libExtension}")
            }
            // Keep original cargo artifact name for deterministic loading (fea_engine/libfea_engine)
            copy {
                from(builtArtifact)
                into(resourcesOsArchDir)
                rename("${cargoArtifactBaseName}.${libExtension}", "${cargoArtifactBaseName}.${libExtension}")
            }
        }
    }

    // Ensure resources include the native libs before processing and testing
    tasks.named("processResources") {
        dependsOn("copyRustLibraries")
    }

    // Task to generate the Litvin golden JSON into build/generated when native is available
    tasks.register<JavaExec>("generateLitvinGolden") {
        group = "verification"
        description = "Generates Litvin kinematics tables golden into build/generated/goldens"

        // Ensure native libs are present in resources for the test runtime to load
        dependsOn("copyRustLibraries")
        dependsOn("processResources")

        // Use the test runtime classpath because the generator lives under src/test/kotlin
        classpath = sourceSets["test"].runtimeClasspath
        mainClass.set("com.campro.v5.animation.LitvinGoldenGenerator")

        // Match the environment setup used by the tests for consistent JNI loading
        val osName = System.getProperty("os.name").lowercase(Locale.ROOT)
        val osDir = when {
            osName.contains("win") -> "windows"
            osName.contains("mac") -> "mac"
            else -> "linux"
        }
        val archDir = "x86_64"
        val resolvedDir = layout.buildDirectory
            .dir("resources/main/native/${osDir}/${archDir}")
            .get()
            .asFile
        environment("FEA_ENGINE_LIB_DIR", resolvedDir.absolutePath)
        doFirst {
            println("[Gradle][generateLitvinGolden] FEA_ENGINE_LIB_DIR=" + resolvedDir.absolutePath)
        }
    }

}


compose.desktop {
    application {
        mainClass = "com.campro.v5.DesktopMainKt"
        
        // Allow passing args via -PappArgs / -PappArgsJson when using the standard ':desktop:run' task
        val appArgsProp = (project.findProperty("appArgs") as String?)?.trim()
        val appArgsJsonProp = (project.findProperty("appArgsJson") as String?)?.trim()
        if (!appArgsProp.isNullOrBlank() || !appArgsJsonProp.isNullOrBlank()) {
            fun parseJsonArray(input: String): List<String> {
                val regex = Regex("\"([^\"]*)\"")
                return regex.findAll(input).map { it.groupValues[1] }.toList()
            }
            val argsList: List<String> = when {
                !appArgsJsonProp.isNullOrBlank() -> parseJsonArray(appArgsJsonProp)
                !appArgsProp.isNullOrBlank() -> appArgsProp.split(Regex("\\s+")).filter { it.isNotBlank() }
                else -> emptyList()
            }
            if (argsList.isNotEmpty()) {
                args += argsList
            }
        }
        
        nativeDistributions {
            targetFormats(
                org.jetbrains.compose.desktop.application.dsl.TargetFormat.Dmg,
                org.jetbrains.compose.desktop.application.dsl.TargetFormat.Msi,
                org.jetbrains.compose.desktop.application.dsl.TargetFormat.Deb
            )
            packageName = "CamProV5"

            // Sanitize version for installer requirements (numeric only; MAJOR >= 1)
            val raw = project.version.toString()
            val match = Regex("""(\d+)\.(\d+)\.(\d+)""").find(raw)
            val major0 = match?.groupValues?.get(1)?.toIntOrNull() ?: 1
            val minor = match?.groupValues?.get(2)?.toIntOrNull() ?: 0
            val patch = match?.groupValues?.get(3)?.toIntOrNull() ?: 0
            val major = if (major0 < 1) 1 else major0
            val pkgVer = "$major.$minor.$patch"
            packageVersion = pkgVer

            windows {
                menuGroup = "CamProV5"
                // Generates a Windows Installer
                upgradeUuid = "E8CF9489-0D37-4661-A1BB-3F9D73D958A7"
                msiPackageVersion = pkgVer
            }
            macOS {
                dmgPackageVersion = pkgVer
            }
            vendor = "Your Org"
        }
    }
}


// Fast, non-interactive subset test task for Junie/CI to avoid long-running suites
// Does not modify the default 'test' task behavior.
tasks.register<org.gradle.api.tasks.testing.Test>("junieTest") {
    group = "verification"
    description = "Fast, non-interactive subset of tests for Junie terminal (excludes slow/long-running suites)."

    // Only depend on native-copy workflow if includeNative=true
    if (includeNative) {
        dependsOn("copyRustLibraries")
        dependsOn("processResources")
    }

    useJUnitPlatform()

    // Prefer the freshly copied resources directory for JNI loading (same as 'test') when native is included
    if (includeNative) {
        val osName = System.getProperty("os.name").lowercase(Locale.ROOT)
        val osDir = when {
            osName.contains("win") -> "windows"
            osName.contains("mac") -> "mac"
            else -> "linux"
        }
        val archDir = "x86_64"
        val resolvedDir = layout.buildDirectory
            .dir("resources/main/native/${osDir}/${archDir}")
            .get()
            .asFile
        environment("FEA_ENGINE_LIB_DIR", resolvedDir.absolutePath)
        doFirst {
            println("[Gradle][junieTest] FEA_ENGINE_LIB_DIR=" + resolvedDir.absolutePath)
        }
    }

    // Keep runtime deterministic and short
    maxParallelForks = 1
    failFast = true

    // Include core/gate A–C tests; exclude known long-running/interactive suites
    filter {
        includeTestsMatching("com.campro.v5.animation.MotionLaw*")
        includeTestsMatching("com.campro.v5.data.litvin.DiagnosticsMetricsTest")
        includeTestsMatching("com.campro.v5.animation.MotionLawContinuityTest")
        includeTestsMatching("com.campro.v5.animation.MotionLawGeneratorTest")
        includeTestsMatching("com.campro.v5.animation.MotionLawGeneratorPropertyTest")

        // Exclusions: optimization runs, UI/collaboration heavy tests
        excludeTestsMatching("com.campro.v5.animation.Optimization*")
        excludeTestsMatching("com.campro.v5.ui.*")
        excludeTestsMatching("com.campro.v5.collaboration.*")
    }

    testLogging {
        events("failed", "passed", "skipped")
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.SHORT
        showExceptions = true
        showStandardStreams = false
        showStackTraces = true
    }
}


// Convenience run task that accepts application arguments via -PappArgs or -PappArgsJson
// Usage examples (PowerShell):
//   .\gradlew :CamProV5:desktop:runDesktop -PappArgs="--testing-mode --session-id=beta --log-level=INFO"
//   .\gradlew :CamProV5:desktop:runDesktop -PappArgsJson="[\"--session-id=beta\",\"--log-level=INFO\"]"
// This avoids the Gradle CLI --args quoting pitfalls and works consistently across shells.
tasks.register<JavaExec>("runDesktop") {
    group = "application"
    description = "Run CamProV5 Desktop with optional args via -PappArgs or -PappArgsJson (JSON array)."

    classpath = sourceSets["main"].runtimeClasspath
    mainClass.set("com.campro.v5.DesktopMainKt")

    doFirst {
        fun parseJsonArray(input: String): List<String> {
            // Minimal JSON array parser for ["arg1","arg2 with spaces"].
            // It extracts quoted items without unescaping; keep args simple.
            val regex = Regex("\"([^\"]*)\"")
            return regex.findAll(input).map { it.groupValues[1] }.toList()
        }
        val appArgsProp = (project.findProperty("appArgs") as String?)?.trim()
        val appArgsJsonProp = (project.findProperty("appArgsJson") as String?)?.trim()
        val argsList: List<String> = when {
            !appArgsJsonProp.isNullOrBlank() -> parseJsonArray(appArgsJsonProp)
            !appArgsProp.isNullOrBlank() -> appArgsProp.split(Regex("\\s+")).filter { it.isNotBlank() }
            else -> emptyList()
        }
        if (argsList.isNotEmpty()) {
            args = argsList
        }
        println("[Gradle][runDesktop] args=" + (if (argsList.isEmpty()) "<none>" else argsList.joinToString(" ")))
    }
}


// Shadow fat JAR configuration (Shadow 8.x)
tasks.named<com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar>("shadowJar") {
    archiveBaseName.set("CamProV5-desktop")
    manifest {
        attributes["Main-Class"] = "com.campro.v5.DesktopMainKt"
    }
    // Consider enabling if you have META-INF/services providers across deps
    mergeServiceFiles()
    // minimize() // optional after runtime verification
}

// Ensure ktlint runs as part of check
tasks.named("check") {
    dependsOn("ktlintCheck")
}

// Unified test task configuration with optional native enablement via -DincludeNative=true
tasks.test {
    useJUnitPlatform {
        if (includeNative) includeTags("native") else excludeTags("native")
    }
    if (includeNative) {
        // Ensure native libs are copied into resources
        dependsOn("copyRustLibraries", "processResources")
        // Prefer the freshly copied resources directory for JNI loading
        val osName = System.getProperty("os.name").lowercase(Locale.ROOT)
        val osDir = when {
            osName.contains("win") -> "windows"
            osName.contains("mac") -> "mac"
            else -> "linux"
        }
        val archDir = "x86_64"
        val resolvedDir = layout.buildDirectory
            .dir("resources/main/native/${osDir}/${archDir}")
            .get()
            .asFile
        environment("FEA_ENGINE_LIB_DIR", resolvedDir.absolutePath)
        doFirst {
            println("[Gradle][test] FEA_ENGINE_LIB_DIR=" + resolvedDir.absolutePath)
        }
        // If the generator task exists (only when includeNative=true), run it before tests
        dependsOn("generateLitvinGolden")
    }
}
