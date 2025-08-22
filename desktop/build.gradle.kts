/**
 * Build configuration for the CamProV5 desktop module.
 * 
 * This file is a placeholder for the actual implementation.
 * The actual implementation would use the Compose for Desktop plugin
 * to build a desktop version of the Android UI.
 */

plugins {
    kotlin("jvm")
    id("org.jetbrains.compose")
}

version = "0.9.0-beta"

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
    implementation("org.jetbrains.compose.material3:material3:1.2.0")
    implementation(compose.material)
    implementation(compose.materialIconsExtended)
    implementation(compose.ui)
    implementation(compose.foundation)
    implementation(compose.runtime)
    
    // JSON
    implementation("com.google.code.gson:gson:2.10")
    
    // Logging (quick wins)
    implementation("org.slf4j:slf4j-api:2.0.13")
    runtimeOnly("ch.qos.logback:logback-classic:1.5.6")
    runtimeOnly("net.logstash.logback:logstash-logback-encoder:7.4")
    
    // Testing dependencies
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter-api:5.9.2")
    testImplementation("org.junit.jupiter:junit-jupiter-engine:5.9.2")
    testImplementation("org.junit.jupiter:junit-jupiter-params:5.9.2")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.9.2")
    
    // Kotest for property-based testing
    testImplementation("io.kotest:kotest-runner-junit5:5.6.2")
    testImplementation("io.kotest:kotest-assertions-core:5.6.2")
    testImplementation("io.kotest:kotest-property:5.6.2")
}

// Configure test task to use JUnit Platform with native tag control
tasks.test {
    useJUnitPlatform {
        if (System.getProperty("includeNative") == "true") {
            includeTags("native")
        } else {
            excludeTags("native")
        }
    }
    // Provide DLL discovery for Gate B in CI/dev
    environment("FEA_ENGINE_LIB_DIR", "${rootProject.projectDir}\\CamProV5\\camprofw\\rust\\fea-engine\\target\\release")
    systemProperty("debug", "true")
}

// Add Rust build tasks (conditional on -DincludeNative=true)
val includeNative = System.getProperty("includeNative") == "true"
if (includeNative) {
    val nativeClean = System.getProperty("nativeClean") == "true"

    tasks.register<Exec>("buildRustLibraries") {
        group = "build"
        description = "Builds the Rust native libraries"

        val crateDir = file("${project.rootDir}/CamProV5/camprofw/rust/fea-engine")
        workingDir = crateDir

        // Use appropriate command based on OS
        val isWindows = System.getProperty("os.name").lowercase().contains("win")
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
        val isWindows = System.getProperty("os.name").lowercase().contains("win")
        val isMac = System.getProperty("os.name").lowercase().contains("mac")

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
        val isWindows = System.getProperty("os.name").lowercase().contains("win")
        val isMac = System.getProperty("os.name").lowercase().contains("mac")
        val osDir = when {
            isWindows -> "windows"
            isMac -> "mac"
            else -> "linux"
        }
        val archDir = "x86_64"
        val resolvedDir = file("${project.buildDir}/resources/main/native/${osDir}/${archDir}")
        environment("FEA_ENGINE_LIB_DIR", resolvedDir.absolutePath)
        doFirst {
            println("[Gradle][generateLitvinGolden] FEA_ENGINE_LIB_DIR=" + resolvedDir.absolutePath)
        }
    }

    tasks.named<org.gradle.api.tasks.testing.Test>("test") {
        dependsOn("copyRustLibraries")
        dependsOn("processResources")
        // Prefer the freshly copied resources directory for JNI loading
        val isWindows = System.getProperty("os.name").lowercase().contains("win")
        val isMac = System.getProperty("os.name").lowercase().contains("mac")
        val osDir = when {
            isWindows -> "windows"
            isMac -> "mac"
            else -> "linux"
        }
        val archDir = "x86_64"
        val resolvedDir = file("${project.buildDir}/resources/main/native/${osDir}/${archDir}")
        environment("FEA_ENGINE_LIB_DIR", resolvedDir.absolutePath)
        doFirst {
            println("[Gradle][test] FEA_ENGINE_LIB_DIR=" + resolvedDir.absolutePath)
        }

        // Optionally pre-generate the golden if native is included
        if ((System.getProperty("includeNative") ?: "false").toBoolean()) {
            dependsOn("generateLitvinGolden")
        }
    }
}

// Set the JAR file name to match what the bridge.py file is looking for
// Also configure the manifest to include the Main-Class attribute
// Create a fat JAR that includes all dependencies
tasks.withType<Jar> {
    archiveBaseName.set("CamProV5-desktop")
    manifest {
        attributes(
            mapOf(
                "Main-Class" to "com.campro.v5.DesktopMainKt"
            )
        )
    }
    
    // Include all dependencies in the JAR
    from(configurations.runtimeClasspath.get().map { if (it.isDirectory) it else fileTree(it).apply {
        include("**/*.class")
        include("**/*.properties")
        include("**/*.xml")
        include("**/*.json")
        include("**/*.kotlin_module")
    } })
    
    // Exclude META-INF files from dependencies to avoid conflicts
    exclude("META-INF/*.SF", "META-INF/*.DSA", "META-INF/*.RSA")
    
    // Ensure duplicates are handled properly
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
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
            targetFormats(org.jetbrains.compose.desktop.application.dsl.TargetFormat.Dmg, org.jetbrains.compose.desktop.application.dsl.TargetFormat.Msi, org.jetbrains.compose.desktop.application.dsl.TargetFormat.Deb)
            packageName = "CamProV5"
            packageVersion = "1.0.0"
            
            windows {
                menuGroup = "CamProV5"
                // Generates a Windows Installer
                upgradeUuid = "E8CF9489-0D37-4661-A1BB-3F9D73D958A7"
            }
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
        val isWindows = System.getProperty("os.name").lowercase().contains("win")
        val isMac = System.getProperty("os.name").lowercase().contains("mac")
        val osDir = when {
            isWindows -> "windows"
            isMac -> "mac"
            else -> "linux"
        }
        val archDir = "x86_64"
        val resolvedDir = file("${project.buildDir}/resources/main/native/${osDir}/${archDir}")
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
