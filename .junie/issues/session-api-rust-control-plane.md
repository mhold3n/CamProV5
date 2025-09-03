---
title: "[Junie] Session API in Rust: control plane + frame subscription"
labels: [junie:ready, p0]
intent: implement
---

## Context
Provide a transport‑agnostic Session API to start/stop sessions, update parameters, seek/play/pause/step, subscribe to frames, and query diagnostics/errors. Integrate with existing camprofw/rust/fea-engine crates and the frame_model types. Include a bounded SPSC frame ring with configurable depth and tests under load.

## Acceptance Criteria
- A session module/crate exposes:
  - start/stop, update_parameters, seek, play, pause, step.
  - subscribe_frames(fields_mask, include_contact, include_probes) returning a frame stream handle.
  - diagnostics: latency p50/p95, queue depth, dropped frames, solver_dt, render_dt; last_error.
- Bounded SPSC frame queue implemented with configurable depth; unit tests simulate producer/consumer under load.
- Example CLI: steps the solver, prints diagnostics, and emits frames; build/test passes in CI.