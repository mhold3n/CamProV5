# CamProV5

Multi-platform project combining Desktop (Kotlin/Compose), Android, Python tooling, Rust engines, and C++ components.

## Modules Overview
- desktop: Kotlin/Compose Desktop application
- android: Android application module
- camprofw/rust: Rust crates (e.g., fea-engine)
- cpp: Native C++ components
- campro, layouts: Python packages and templates

See [README_CROSS_PLATFORM.md](README_CROSS_PLATFORM.md) for environment setup and cross-platform details.

## Building
- JVM/Desktop: `./gradlew :desktop:build`
- Android (CI/CLI): `./gradlew :android:assembleDebug`
- Rust: `cargo test` inside each crate (e.g., camprofw/rust/fea-engine)
- Python: `pip install -r requirements.txt && pytest`

## Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Support and Security
For help, see [SUPPORT.md](SUPPORT.md). For responsible disclosure, see [SECURITY.md](SECURITY.md).

## License
See [LICENSE](LICENSE).
