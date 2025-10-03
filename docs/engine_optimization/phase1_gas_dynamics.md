---
title: Phase 1 — Gas Dynamics
created: 2025-10-03
format: gfm
description: Narrative and reference for Phase 1 gas dynamics optimization, with normalized objectives and constraints.
---

## Scope
Phase 1 defines the piston motion law, thermodynamic assumptions, and cycle timing that shape the pressure–volume behavior and set the stage for later phases.

## Key Decisions and Variables
- Motion law \(x(t)\): B-spline (order ≥ 4), clamped at \(t \in [0, T_{\text{cyc}}]\), \(x(0)=0\), \(x(T_{\text{cyc}})=S\), ensuring at least C² continuity.
- Velocity target \(v_{\text{targ}}(t)\): Piecewise-constant plateau with smooth ramps, used in the flatness objective.
- Valve lift \(L(t)\): C¹ sigmoid or polynomial-7 with smoothing \(\varepsilon_v\); bounded by \(0 \le L(t) \le L_{\max}\).
- Heat release \(x_{\text{burn}}(t)\): Wiebe function \(1-\exp[-a((t-t_0)/\Delta t)^{m+1}]\) with parameters \(a, m, t_0, \Delta t\).

## Objectives (Normalized)
- Work output: \(\widehat{W} = W / \overline{W}\) — maximize.
- Velocity flatness: \(\widehat{J}_{\text{flat}} = \int (v - v_{\text{targ}})^2 dt / \overline{J}_{\text{flat}}\) — minimize.
- Jerk regularization: \(\widehat{J}_{\text{jerk}} = \int (x^{\prime\prime\prime})^2 dt / \overline{J}_{\text{jerk}}\) — minimize.
- Exergy loss (optional): \(\widehat{J}_{\text{ex}} = \int T_0 \, \dot S_{\text{gen}} \, dt / \overline{E}\) — minimize.

## Constraints (Differentiable Forms)
- Stroke boundary conditions: \(x(0)=0\), \(x(T_{\text{cyc}})=S\).
- Cycle timing: fixed \(T_{\text{cyc}}\); compression fraction \(\varphi_c = T_{\text{comp}}/T_{\text{cyc}}\) may be fixed or bounded.
- Adiabatic segments: \(pV^{\gamma} = \text{const}\) when valves are closed via a smooth gate \(\sigma_{\text{valve}}(t)\in[0,1]\).
- State evolution: mass and energy balances consistent with \(x_{\text{burn}}(t)\) using collocation defects.
- Valve bounds: \(0 \le L(t) \le L_{\max}\) with C¹ smoothness.

## Transcription and Grid
- Transcription: Radau collocation; shared grid across phases for consistent coupling.
- Grid density: 60–120 points per cycle; cluster near motion reversals.

## Diagnostics
- KKT error: < 1e-6 at final stage.
- Primal/dual infeasibility: < 1e-6 (scaled).
- Mass/energy residuals: < 1e-6 (nondimensional) per segment.
- Active set: stable across weight sweeps without oscillation.

## Notes
- Use smooth parameterizations and gates to avoid non-differentiable kinks.
- Normalize contributions to stabilize scalarization and tuning.


