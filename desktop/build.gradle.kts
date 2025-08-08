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

tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
    kotlinOptions {
        freeCompilerArgs += "-opt-in=org.jetbrains.compose.ExperimentalComposeLibrary"
        freeCompilerArgs += "-opt-in=androidx.compose.material3.ExperimentalMaterial3Api"
        freeCompilerArgs += "-opt-in=androidx.compose.foundation.ExperimentalFoundationApi"
        freeCompilerArgs += "-opt-in=androidx.compose.ui.ExperimentalComposeUiApi"
    }
}

repositories {
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
    
    // Add dependencies for communication with Python
    implementation("com.google.code.gson:gson:2.10")
    
    // Testing dependencies
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter-api:5.9.2")
    testImplementation("org.junit.jupiter:junit-jupiter-engine:5.9.2")
    testImplementation("org.junit.jupiter:junit-jupiter-params:5.9.2")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.9.2")
}

// Configure test task to use JUnit Platform
tasks.test {
    useJUnitPlatform()
}

// Add Rust build tasks
tasks.register<Exec>("buildRustLibraries") {
    group = "build"
    description = "Builds the Rust native libraries"
    
    workingDir = file("${project.rootDir}/camprofw/rust/fea-engine")
    
    // Use appropriate command based on OS
    val isWindows = System.getProperty("os.name").toLowerCase().contains("win")
    commandLine = if (isWindows) {
        listOf("cmd", "/c", "cargo", "build", "--release")
    } else {
        listOf("cargo", "build", "--release")
    }
    
    // Only run if Rust code has changed
    inputs.dir(file("${project.rootDir}/camprofw/rust/fea-engine/src"))
    inputs.file(file("${project.rootDir}/camprofw/rust/fea-engine/Cargo.toml"))
    outputs.dir(file("${project.rootDir}/camprofw/rust/fea-engine/target/release"))
}

tasks.register<Copy>("copyRustLibraries") {
    group = "build"
    description = "Copies the built Rust libraries to the resources directory"
    
    dependsOn("buildRustLibraries")
    
    // Determine OS-specific paths and file names
    val isWindows = System.getProperty("os.name").toLowerCase().contains("win")
    val isMac = System.getProperty("os.name").toLowerCase().contains("mac")
    
    val libPrefix = if (isWindows) "" else "lib"
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
    
    // Create resource directories if they don't exist
    doFirst {
        mkdir("${project.projectDir}/src/main/resources/native/$osDir/$archDir")
    }
    
    // Copy motion library
    from(file("${project.rootDir}/camprofw/rust/fea-engine/target/release/fea_engine.$libExtension"))
    into(file("${project.projectDir}/src/main/resources/native/$osDir/$archDir"))
    rename("fea_engine.$libExtension", "${libPrefix}campro_motion.$libExtension")
    
    // Copy FEA library
    doLast {
        copy {
            from(file("${project.rootDir}/camprofw/rust/fea-engine/target/release/fea_engine.$libExtension"))
            into(file("${project.projectDir}/src/main/resources/native/$osDir/$archDir"))
            rename("fea_engine.$libExtension", "${libPrefix}campro_fea.$libExtension")
        }
    }
}

// Make the main build depend on copying the libraries
tasks.named("processResources") {
    dependsOn("copyRustLibraries")
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