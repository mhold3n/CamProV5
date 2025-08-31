# Contributing to CamProV5

Thanks for your interest in contributing!

## Code of Conduct
By participating, you agree to abide by our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Branching Strategy (Trunk-based)
- Mainline: `main` is always releasable.
- Short-lived branches with prefixes:
  - `feature/<short-topic>` for features
  - `fix/<short-topic>` for bug fixes
  - `chore/<short-topic>` for maintenance
  - `docs/<short-topic>` for documentation
- Rebase or squash-merge preferred to keep history linear.

## Commit Messages
- Follow Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Link issues in PRs using “Fixes #123” (auto-closes on merge).

## Local Setup
- JDK 17 with Kotlin 1.9 via Gradle wrapper. Use the wrapper: `./gradlew ...`
- Rust (stable toolchain) if working on native crates.
- Python 3.10+ for scripts/tools.

## Build & Test
- Desktop (Kotlin/Compose):
  - Run: `./gradlew :desktop:run`
  - Test: `./gradlew :desktop:test`
- Android: open in Android Studio or `./gradlew :android:assembleDebug`
- Rust: `cd camprofw/rust/fea-engine && cargo test`
- Python: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pytest`

## Linting (Kotlin)
- Check: `./gradlew :desktop:ktlintCheck`
- Format: `./gradlew :desktop:ktlintFormat`

### Native build flags (Desktop + Rust)
- Include native build steps in Gradle by passing system properties:
  - `-DincludeNative=true` to build/copy Rust libs and enable native-tagged tests
  - `-DnativeClean=true` to force a clean native rebuild (optional)
- Examples:
  - Build desktop with native: `./gradlew :desktop:build -DincludeNative=true`
  - Run tests with native + regenerate goldens: `./gradlew :desktop:test -DincludeNative=true`

## Pull Requests
- Fill out the PR template and keep changes focused/small.
- Ensure CI is green. Run relevant checks locally when possible.
- Add/adjust tests and docs as needed.

## Reviews
- At least one approval is required (CODEOWNERS may be auto-requested).
- Address review feedback promptly; stale approvals may be dismissed on new commits.

## Required checks to merge
To merge into main, the following GitHub checks must be green:
- CI / jvm-desktop
- CI / rust-fea-engine
- CodeQL
- (Optional) PR Title Lint

You can run most checks locally before pushing:
- Desktop build & tests: `./gradlew :desktop:build :desktop:test`
  - With native tests: `./gradlew :desktop:test -DincludeNative=true`
- Rust fea-engine: `cd camprofw/rust/fea-engine && cargo clippy --all-targets -- -D warnings && cargo test --all`

## Release process
- Bump versions in gradle.properties and camprofw/rust/fea-engine/Cargo.toml to X.Y.Z.
- Commit and merge the release PR, then create a Git tag `vX.Y.Z`.
- Publish a GitHub Release for the tag. The release workflow will verify that:
  - `gradle.properties` version matches the tag.
  - `camprofw/rust/fea-engine/Cargo.toml` `[package].version` matches the tag.
- The workflow builds installers and the shadow JAR, plus Rust artifacts, and uploads them to the release.

## Reporting Issues
Use the issue templates under New Issue to report bugs or request features.

## License
By contributing, you agree that your contributions will be licensed under the LICENSE of this repository.


## Troubleshooting Gradle/Shadow/ktlint builds

What’s happening
- If you see an error like: “This version of Shadow supports Gradle 8.0+ only. Please upgrade.” it means your local build used an older Gradle instead of the wrapper. This repo uses the Gradle wrapper 8.9 and JDK 17.

Fix it step by step
1) Verify you are using the Gradle wrapper (8.9)
- macOS/Linux:
  - chmod +x ./gradlew
  - ./gradlew --version
- Windows:
  - gradlew.bat --version
- Expected: Gradle 8.9. If you see 7.x, you ran a system Gradle or have stale wrapper artifacts. Always use ./gradlew or gradlew.bat.

Common commands (always via wrapper):
- ./gradlew :desktop:build :desktop:test
- ./gradlew :desktop:ktlintCheck
- ./gradlew :desktop:ktlintFormat
- ./gradlew :desktop:shadowJar

2) Set IntelliJ IDEA to use the wrapper and JDK 17
- Settings > Build, Execution, Deployment > Build Tools > Gradle:
  - Gradle JVM: 17 (Temurin 17 or JetBrains Runtime 17)
  - Use Gradle from: gradle-wrapper.properties
- Click “Reload All Gradle Projects”.

3) Refresh wrapper artifacts (if they might be stale)
- Even if gradle-wrapper.properties says 8.9, the wrapper JAR/scripts may be stale.
- Run:
  - ./gradlew wrapper --gradle-version 8.9 --distribution-type bin
- Commit any changes:
  - gradle/wrapper/gradle-wrapper.properties
  - gradle/wrapper/gradle-wrapper.jar
  - gradlew, gradlew.bat
- If ./gradlew fails (inconsistent wrapper), temporarily use a modern Gradle just to regenerate the wrapper, then go back to the wrapper:
  - With SDKMAN: sdk install gradle 8.9; gradle wrapper --gradle-version 8.9 --distribution-type bin
  - Or use IntelliJ’s Gradle tool window to run the “wrapper” task with Gradle 8.9.

4) Re-run builds and ktlint
- Build & test: ./gradlew --no-daemon :desktop:build :desktop:test
- Ktlint check: ./gradlew --no-daemon :desktop:ktlintCheck
- Ktlint format (auto-fix): ./gradlew --no-daemon :desktop:ktlintFormat
- Shadow JAR: ./gradlew --no-daemon :desktop:shadowJar
- Sanity run: java -jar desktop/build/libs/CamProV5-desktop-*-all.jar
- Note: If compilation errors persist (e.g., unresolved references) or ktlint parsing issues occur, these are separate code issues. Run ktlintFormat to fix style where possible, then address unresolved references so :desktop:build compiles.

5) Temporary fallback (not recommended)
- If you cannot upgrade your local Gradle immediately, you can temporarily use Shadow 7.1.2 in desktop/build.gradle.kts:
  - id("com.github.johnrengelman.shadow") version "7.1.2"
- However, CI and release use Gradle 8.9 + Shadow 8.1.1. Align your local environment as the proper fix.

Quick validation checklist
- ./gradlew --version shows Gradle 8.9
- IntelliJ uses Gradle wrapper + JDK 17
- ./gradlew :desktop:ktlintCheck runs (format with :desktop:ktlintFormat if needed)
- ./gradlew :desktop:build succeeds; then :desktop:shadowJar builds the fat JAR
