---
title: "[Junie] Scrubbing and seek quality policy (coarse→refine)"
labels: [junie:ready, p1]
intent: implement
---

## Context
Implement responsive scrubbing: during user drag, seek with coarse stepping, then refine near the target time. Keep queue depth bounded and maintain latency budgets. Integrate with the Session API QualityHint and ensure UI remains responsive on large meshes.

## Acceptance Criteria
- Implement QualityHint policy (Coarse during drag, Refine on settle) in session/ui_app.
- During scrubbing on demo meshes, diagnostics show p95 latency < 50 ms; queue depth ≤ 3.
- Unit/integration tests cover scrub behavior and transitions from coarse to refine.
- Document policy in code comments and user docs.