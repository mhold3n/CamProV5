---
title: "[Junie] Define v0 frame schema and binary descriptors (frame_model)"
labels: [junie:ready, p0]
intent: implement
---

## Context
Implement the minimal per‑frame schema and binary descriptors enabling zero‑copy GPU uploads and interop with the solver. Provide reference encoder/decoder and tests. Include an optional JSON debug sidecar in debug builds.

## Acceptance Criteria
- frame_model crate exposes types and a binary descriptor for:
  - Metadata: time_s, step_index, state_hash, flags.
  - Topology snapshot with versioning: topo_version, parts, index buffer.
  - Nodal SoA arrays: disp_x/y/z and optional rotations/strains/stresses.
  - Optional sections: contact geometry, probes, per‑part aggregates.
- Reference encoder/decoder round‑trip tests using two sample meshes.
- JSON debug sidecar feature (behind cfg(debug_assertions)).
- Benchmarks demonstrate zero‑copy views into contiguous buffers.