---
title: "[Junie] Diagnostics and performance HUD + soak tests"
labels: [junie:ready, p1]
intent: test
---

## Context
Validate latency budgets and long‑run stability for the Rust UI. Expose a HUD with key metrics and add automated soak tests that exercise producer/consumer paths under load, ensuring bounded memory usage and no deadlocks.

## Acceptance Criteria
- HUD displays: p50/p95 latency, queue depth, dropped frames, solver_dt, render_dt.
- Soak test runs for hours on a sample mesh with bounded memory and zero deadlocks.
- CI job executes perf smoke tests; artifacts include metrics JSON for inspection.