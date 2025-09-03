---
title: "[Junie] RFC: Rust‑native UI architecture and migration plan (Option B)"
labels: [junie:ready, p0]
intent: docs
---

## Context
We are choosing Option B: a Rust‑native front end running in‑process with the FEA solver. This RFC will define crate boundaries, shared frame/session API, rendering stack (wgpu), and the migration strategy from the current UI. It must align with the Junie Project Guidelines: issues as source of truth; clear acceptance criteria; minimal viable increments; and two‑way mirroring.

## Acceptance Criteria
- An ADR/RFC document exists at docs/adr/00X-rust-ui-option-b.md covering:
  - Crate layout, responsibilities, and inter‑crate interfaces.
  - Chosen UI shell (egui) and renderer (wgpu) rationale.
  - Session API reuse/adjustments; SoA memory layout for GPU.
  - Dependency graph and milestones; de‑risking plan.
  - Rollback plan and risks with mitigations.
- README updated to point to the ADR.
- Issues cross‑linked to this RFC where dependencies exist.