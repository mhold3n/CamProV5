---
title: Phase 2 — Transmission
created: 2025-10-03
format: gfm
description: Mapping linear piston motion to rotational output with smooth, efficient transmission design.
---

## Scope
Phase 2 maps the Phase 1 motion law to a rotational output through a smooth ratio field while respecting stress, efficiency, and manufacturability.

## Mapping and Variables
- Ratio field \(i(x)\): clamped B-spline over \(x \in [0, S]\), monotone if required.
- Smoothness: derivative bounds \(\lVert i'(x) \rVert \le \kappa_1\), \(\lVert i''(x) \rVert \le \kappa_2\).
- Loss model: smooth Stribeck friction \(P_{\text{loss}}\) with bounded parameters.
- Contact constraints: Hertzian stress \(\sigma_H \le \sigma_{\text{lim}}\) with fatigue guardrails.

## Objectives (Normalized)
- Transmission efficiency: \(\widehat{\eta} = \eta/\overline{\eta}\) — maximize.
- Contact stress penalty: \(\widehat{\sigma}_{\max} = \sigma_{\max}/\overline{\sigma}\) — minimize; also constrained.
- Loss power: \(\widehat{P}_{\text{loss}} = P_{\text{loss}}/\overline{P}\) — minimize.

## Coupling and Consistency
- Kinematic coupling: \(\dot{\theta} = i(x)\, \dot{x}\) on the shared grid.
- Power balance: \(\tau_{\text{out}}\, \dot{\theta} = F_p\, \dot{x} - P_{\text{loss}}(x, \dot{x}, i)\).
- Fatigue guardrail: \(\text{SF} = \sigma_{\text{lim}}/\sigma_{\max} \ge 1\) (or life \(\ge L_{\min}\)).

## Notes
- Prefer rolling elements and smooth profiles to reduce slip losses.
- Keep ratio ramps gradual to avoid surge and force peaks.


