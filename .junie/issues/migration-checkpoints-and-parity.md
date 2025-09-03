---
title: "[Junie] Migration checkpoints and parity with current UI"
labels: [junie:ready, p1]
intent: docs
---

## Context
Define functional parity checkpoints between the current UI and the new Rust‑native UI. Establish the criteria and KPIs required to switch the default UI, with clear measurement and a rollback plan.

## Acceptance Criteria
- A checklist of parity items exists (playback, scrubbing, selection, overlays, probe plots, export), each with measurable KPIs.
- A decision record documents the gate to "Enable Rust UI as default", including required KPIs (e.g., p95 latency < 50 ms, zero crashes in soak) and rollback plan.
- Links to relevant issues/PRs implementing each checkpoint; progress is trackable.
- Documented procedure for switching defaults (flags/config) and verifying on CI/nightly builds.