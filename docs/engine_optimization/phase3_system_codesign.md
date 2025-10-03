---
title: Phase 3 — System Co-Design
created: 2025-10-03
format: gfm
description: Multiobjective system co-design combining phases with normalized terms and robustness.
---

## Objectives (Normalized)
- Work \(\widehat{W}\) — maximize
- Efficiency \(\widehat{\eta}\) — maximize
- Jerk \(\widehat{J}_{\text{jerk}}\) — minimize
- Stress \(\widehat{\sigma}_{\max}\) — minimize (also constrained to \(\le 1\))
- Loss \(\widehat{P}_{\text{loss}}\) — minimize

Scalarization example: Augmented Tchebyshev with weights \(\lambda_i\). Example weight grids can bias toward work/efficiency, balanced, or durability-focused designs.

## Robustness (Chance Constraints)
- Friction coefficient \(\mu\) ~ Normal(0.08, 0.02): enforce \(P(\sigma_{\max} \le \sigma_{\text{lim}}) \ge 0.95\), truncated to \(\mu \ge 0\).
- Heat release parameters \(a, m\): calibrate from experiments; enforce \(P(\eta \ge \eta_{\min}) \ge 0.95\).
- Clearance \(V_c\) ~ Uniform(\pm 2\%): enforce \(P(p_{\text{peak}} \le p_{\text{lim}}) \ge 0.95\).

## Acceptance Criteria
- KKT/feasibility \(\le 1\times10^{-6}\) at final stage
- No scaled constraint violations > \(1\times10^{-6}\)
- Sensitivity: small \(\Delta\)opt for \(\pm 5\%\) parameter variations
- Grid invariance: objectives stable under refinement

## Notes
- Discrete hardware choices (e.g., bearing type, mesh selection) are handled via scenario enumeration. Optimize the continuous variables per scenario and compare results; avoid embedding discrete variables directly.


