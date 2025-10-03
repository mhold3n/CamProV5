---
title: Global — IPOPT & CasADi
created: 2025-10-03
format: gfm
description: Solver options, modeling notes, scaling, and continuation strategy for the engine optimization NLP.
---

## IPOPT Options (Baseline)
- tol: 1e-6 (tighten after homotopy stages)
- acceptable_tol: 1e-4 (for early acceptance during continuation)
- mu_strategy: adaptive
- nlp_scaling_method: user-scaling (we supply variable/objective scaling)
- hessian_approximation: exact (CasADi exact Hessian; consider limited-memory if required)
- linear_solver: mumps (or ma57)
- max_iter: 5000 (allow generous iterations for continuation)

## CasADi Modeling Notes
- Graph type: use MX for NLP; constants as DM; consider Function(..., { 'jit': True }).
- Sparsity: exploit sparsity from collocation/multiple-shooting; avoid dense maps.
- Automatic differentiation: use exact Jacobians/Hessian from CasADi.

## Scaling / Normalization
- Indicated work: \(\widehat{W} = W / \overline{W}\) — unitless.
- Contact stress: \(\widehat{\sigma} = \sigma / \overline{\sigma}\) — keep \(\widehat{\sigma} \le 1\).
- Jerk metric: \(\widehat{J}_{\text{jerk}} = J_{\text{jerk}} / \overline{J}\).
- Valve smoothing: \(\varepsilon_v\) — start large and decrease per stage.

## Continuation (Homotopy) Plan
| Stage | \(\varepsilon_v\) | \(\varepsilon_{\text{fric}}\) | Stress limit factor | Notes |
| --- | --- | --- | --- | --- |
| 1 | 1e-1 | 1e-1 | 0.7×\(\sigma_{\text{lim}}\) | Very smooth, relaxed limits, coarse grid |
| 2 | 5e-2 | 5e-2 | 0.85×\(\sigma_{\text{lim}}\) | Tighten bounds; refine grid |
| 3 | 1e-2 | 1e-2 | 1.00×\(\sigma_{\text{lim}}\) | Final physics-like limits; final grid |

## Diagnostics to Log
- KKT error < 1e-6
- Primal/dual infeasibility < 1e-6 (scaled)
- Mass/energy residuals < 1e-6 (nondimensional)
- Stable active set across weight sweeps


