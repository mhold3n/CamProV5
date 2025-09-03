---
title: "[Junie] Crate scaffolding for frame_model, render_core, and ui_app"
labels: [junie:ready, p0]
intent: implement
---

## Context
Establish minimal Rust crates to host the Rust‑native UI stack. This includes creating lib crates for frame schema/types, renderer core (wgpu), and the egui app shell. Configure workspace membership and CI to build/test these crates. No heavy logic yet—just scaffolding and a blank window example.

## Acceptance Criteria
- New crates present with lib targets:
  - camprofw/rust/frame_model
  - camprofw/rust/render_core
  - camprofw/rust/ui_app
- cargo build && cargo test pass in workspace; CI updated to include these crates.
- Each crate has a README describing scope and initial public API surface placeholder.
- Example binaries for ui_app start a window and render a blank wgpu surface at ~60 FPS.