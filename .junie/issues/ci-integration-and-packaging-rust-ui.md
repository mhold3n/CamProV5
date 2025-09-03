---
title: "[Junie] CI integration and packaging for Rust UI"
labels: [junie:ready, p0]
intent: refactor
---

## Context
Ensure CI builds/tests new Rust UI crates and, optionally, produces preview artifacts for review. Headless environments should mock or disable GPU features appropriately. Keep CI changes scoped to new crates.

## Acceptance Criteria
- CI builds/tests camprofw/rust/frame_model, camprofw/rust/render_core, camprofw/rust/ui_app.
- Optional: release job uploads platform‑specific preview artifacts for ui_app (Linux/macOS) on tagged builds or PRs.
- Matrix/headless tests configured for GPU features; renderer code guarded for headless.
- Documentation added to README/CONTRIBUTING on how CI runs and how to fetch artifacts.