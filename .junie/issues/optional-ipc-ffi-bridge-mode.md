---
title: "[Junie] Optional: IPC/FFI layer for hybrid operation (bridge mode)"
labels: [junie:ready, p2]
intent: implement
---

## Context
Enable the legacy UI to subscribe to the same frame/session interface for side‑by‑side validation and A/B comparisons. Provide a shared memory ring or FFI bridge exposing frame_model types to external consumers.

## Acceptance Criteria
- Shared memory ring or FFI bridge exposes frame_model data and Session API controls to an external process.
- Sample: legacy/current UI subscribes and renders frames for A/B comparison with the Rust UI.
- Documentation on setup, performance considerations, and loop‑prevention safeguards.
- Basic integration test verifies data integrity and latency envelope across the bridge.