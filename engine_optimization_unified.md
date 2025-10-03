>
> **Change markers:** All edits in this revision are tagged with **[UPDATED]** so you can quickly locate them.
>

---
title: Engine Optimization Phases — Unified Tables
created: 2025-10-01
format: gfm
description: Machine-friendly consolidation of all sheets from engine_optimization_phases_UPDATED.xlsx with normalized headers and math columns.
---

# Engine Optimization — Unified Tables
This document consolidates all worksheets into normalized Markdown tables with **snake_case** headers. Equations are wrapped in inline LaTeX where applicable. Empty cells are omitted.

## Contents
- [Phase 1 - Gas Dynamics](#phase-1-gas-dynamics)
- [Phase 2 - Transmission](#phase-2-transmission)
- [Global – IPOPT&CasADi](#global-ipopt-casadi)
- [Phase 1 – Revised](#phase-1-revised)
- [Phase 2 – Revised](#phase-2-revised)
- [Phase 3 – System Co-Design](#phase-3-system-co-design)

## Phase 1 - Gas Dynamics

| category | item | brief_description | representative_per_objective_equation_symbolic | units | primary_inputs | downstream_outputs | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Constraint | Stroke length S | Total linear travel per cycle | $x(0)=0,  x(T_cyc)=S$ | m | S (user), T_cyc | V(t) | Sets boundary conditions on x(t) |
| Constraint | Cycle timing | Total cycle duration and compression fraction | $T_cyc,  φ_c ≔ T_comp/T_cyc$ | s | T_cyc (user), φ_c (user) | Collocation grid & segment lengths | φ_c=0.50 is cranklike; free-piston can vary |
| Constraint | Adiabatic segments | Compression & expansion assumed adiabatic | $p(t) V(t)^γ = const$ | — | γ (gas), initial (p_i,T_i), V(t) | p(t),T(t) | Set per segment (intake/exhaust closed) |
| Constraint | Geometric volume | Chamber volume vs. piston position | $V(t)=V_c + A_p x(t)$ | m³ | V_c (clearance), A_p (area), x(t) | p(t),T(t) | A_p=π D²/4 |
| Constraint | Valve isolation | Valves shut during adiabats | $u_valve(t)=0 (closed)$ | — | Valve schedule | Mass in cylinder | Ideal rotary valves assumed lossless |
| Constraint | Reversal kinematics | Velocity zero at ends; bounded jerk | $v(0)=v(T_cyc)=0; \|j(t)\| ≤ j_max$ | SI | j_max (design), S,T_cyc | Feasible x(t) | Prevents impulsive accelerations |
| Free variable | Motion law x(t) | Spline/collocation representation | $x(t)=Σ b_k ϕ_k(t)$ | m | Basis ϕ_k, coefficients b_k | V(t),p(t),T(t) | Choose C³ splines |
| Free variable | Valve timing | Open/close fractions of cycle | ${θ_io,θ_ic,θ_eo,θ_ec} ∈ [0,1]$ | — | φ_c, combustion model | Mass trapped | Avoid overlap |
| Free variable | Spark timing | Ignition phasing wrt compression end | $Δt_ign before TDC$ | s | Fuel, burn model, φ_c | Peak p,T rise | Basis for indicated work |
| Optimized quantity | Velocity flatness | Hold v(t) near target v̄ | $J_v=∫(v(t)-v̄)² dt$ | m²/s | x(t), φ_c, S,T_cyc | Uniformity of p,T | v̄=S_comp/T_comp |
| Optimized quantity | Jerk regularization | Limit excitation | $J_j=∫ j(t)² dt$ | m²/s⁵ | x(t) | Flow losses proxy | Smoothness vs flatness |
| Optimized quantity | Indicated work | Area of p–V loop | $W_id=∮ p dV$ | J | V(t), p(t) | η_ind | Benchmark metric |
| Optimized quantity | Exergy loss (optional) — e.g., \(\int T_0\, \dot S_{\text{gen}}\, dt\) **[UPDATED]** | Penalize fast compression | $J_S ≈ ∫ (dp/dt)²$ | J | x(t),p,T | Cycle efficiency | Surrogate metric |
| Objective | Phase-1 composite | Balance velocity, jerk, entropy | $J₁= w_vJ_v+w_jJ_j+w_SW_id$ | — | Weights w_* | x*(t),u_valve*,Δt_ign* | Weight tuning |

## Phase 2 - Transmission

| category | item | brief_description | representative_per_objective_equation_symbolic | units | primary_inputs | downstream_outputs | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Constraint | Preserve motion law | Use x₁*(t) as input | $x(t)=x₁*(t), v=ẋ$ | SI | From Phase-1 | All mappings | No retiming |
| Constraint | Kinematic mapping | Linear → rotational | $θ_out=Φ(x); ω=ḟ$ | rad | Eccentric profile, gear geometry | Speed ratio | Define Φ monotone |
| Constraint | Feasible ratio & smoothness | Bound ramps | $i(t)=dθ/dx>0; \|di/dt\| ≤ κ$ | 1/m | Φ(x), bearings | F_p peaks | Avoid surge |
| Constraint | Stress & contact | Limit stresses | $σ_contact ≤ σ_allow$ | Pa | Materials, loads | η_tr | Durability |
| Free variable | Transmission ratio profile | Shape of i(x) | $i(x) param (B-spline)$ | 1/m | Eccentricity, radii | R_eff,τ_out | Controls MA, speeds |
| Free variable | Mesh/bearing selection | Loss model | $η_tr=Π η_i$ | — | Lubrication μ, geometry | W_out, temps | Use rolling |
| Free variable | Output load model | Expected torque | $τ_load(θ_out)$ | N·m | Duty cycle | Required MA | Includes inertia |
| Derived quantity | Effective lever arm | Virtual radius | $R_eff=1/i(x)$ | m | i(x) | τ_out | Energy consistent |
| Derived quantity | Mechanical advantage | Force→torque | $MA=τ_out/F=R_effη_tr$ | m | R_eff,η_tr | F_p,τ_out | Tradeoff piston force |
| Optimized quantity | Output work | Max shaft work | $W_out=∫ τω dt$ | J | η_tr,i,v,F | η_overall | Goal metric |
| Optimized quantity | Force moderation | Limit piston forces | $J_F=∫ (F/F_ref)^q dt$ | — | R_eff,τ_load | F_p peaks | Durability |
| Optimized quantity | Loss minimization | Reduce losses | $J_L=∫ P_loss dt$ | J | μ,v_slip | η_tr | Efficiency |
| Optimized quantity | Ratio smoothness | Avoid rapid changes | $J_i=∫ (di/dt)² dt$ | 1/m²s | i(x),v | Gas forcing | Sync with Phase-1 |
| Objective | Phase-2 composite | Max useful work, penalize losses | $𝒢=W_out-αJ_L-βJ_F-γJ_i$ | J | Weights {α,β,γ} | i*(x),Φ*(x) | Tune weights |

## Global – IPOPT&CasADi

| revision_metadata_2025-10-01_22_36 | unnamed_1 | unnamed_2 | unnamed_3 | unnamed_4 | unnamed_5 |
| --- | --- | --- | --- | --- | --- |
| Field | Value | Notes |  |  |  |
| Revision tag | IPOPT-ready smoothing & scaling | Added sheets and normalized objectives/constraints |  |  |  |
| Source sheets detected | Phase 1 - Gas Dynamics, Phase 2 - Transmission | Original sheets left intact |  |  |  |
| Status | ADDED | New sheet with solver settings and scaling guidance |  |  |  |
|  |  |  |  |  |  |
| IPOPT Options (baseline) |  |  |  |  |  |
| Option | Value | Notes | Status |  |  |
| tol | 1e-6 | Tighten after homotopy stages | ADDED |  |  |
| acceptable_tol | 1e-4 | For early acceptance during continuation | ADDED |  |  |
| mu_strategy | adaptive | Barrier update strategy | ADDED |  |  |
| nlp_scaling_method | user-scaling | We provide variable/objective scaling | ADDED |  |  |
| hessian_approximation | exact | Use CasADi exact Hessian; switch to limited-memory if needed | ADDED |  |  |
| linear_solver | mumps | Or ma57 if available | ADDED |  |  |
| max_iter | 5000 | Allow generous iterations for continuation | ADDED |  |  |
|  |  |  |  |  |  |
| CasADi Modeling Notes |  |  |  |  |  |
| Topic | Recommendation | Status |  |  |  |
| Graph type | Use MX for NLP; constants as DM; set Function(..., {'jit': True}) if possible | ADDED |  |  |  |
| Sparsity | Exploit sparsity from collocation/multiple-shooting; avoid dense maps | ADDED |  |  |  |
| AD | Let CasADi generate exact Jacobians/Hessian for IPOPT | ADDED |  |  |  |
|  |  |  |  |  |  |
| Scaling / Normalization |  |  |  |  |  |
| Quantity | Symbol | Scale (reference) | Normalized variable | Notes | Status |
| Indicated work | W | W̄ (e.g., work@baseline cycle) | Ŵ = W / W̄ | Unitless objective contribution | ADDED |
| Contact stress | σ | σ̄ (e.g., allowable Hertzian stress) | σ̂ = σ / σ̄ | Keep σ̂ ≤ 1 as constraint | ADDED |
| Jerk metric | J_jerk | J̄ (from baseline law) | Ĵ = J_jerk / J̄ | Quadratic regularization | ADDED |
| Valve smoothing | ε_v | ε_v0 (initially large) | — | Continuation: decrease ε_v per stage | ADDED |
|  |  |  |  |  |  |
| Continuation (Homotopy) Plan |  |  |  |  |  |
| Stage | ε_v (valve) | ε_fric (friction) | Stress limit factor | Notes | Status |
| 1 | 1e-1 | 1e-1 | 0.7×σ_lim | Very smooth, relaxed limits, coarse grid | ADDED |
| 2 | 5e-2 | 5e-2 | 0.85×σ_lim | Tighten bounds; refine grid | ADDED |
| 3 | 1e-2 | 1e-2 | 1.00×σ_lim | Final physics-like limits; final grid | ADDED |

## Phase 1 – Revised

| decisions_parameterization | unnamed_1 | unnamed_2 | unnamed_3 | unnamed_4 | unnamed_5 | unnamed_6 | unnamed_7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Category | Item | Symbol | Form | Bounds | Scale | Notes | Status |
| Motion law | Piston position | x(t) | B-spline (order≥4) over t∈[0,T_cyc] | [x_min,x_max]=[0,S] | S | Clamped ends; C² smooth | ADDED |
| Motion law | Velocity target | v_targ(t) | Piecewise-constant plateau w/ smooth ramps | — | max\|v\| | Used only in J_flat | ADDED |
| Valve | Lift profile | L(t) | C¹ sigmoid/poly-7; ε_v smoothing | [0,L_max] | L_max | No hard on/off; parameterized timing | ADDED |
| Combustion | Heat-release fraction | x_burn(t) | Wiebe: 1-exp[-a((t-t0)/Δt)^{m+1}] | [0,1] | 1 | a,m,t0,Δt are decisions | ADDED |
|  |  |  |  |  |  |  |  |
| Objectives (normalized) |  |  |  |  |  |  |  |
| Objective | Expression | Norm | Role | Weight (α_i) | Notes | Status |  |
| Work output | Ŵ = W / W̄ | Unitless | Maximize | α_W | Use negative sign for minimization in NLP | ADDED |  |
| Velocity flatness | Ĵ_flat = ∫ (v-v_targ)^2 dt / J̄_flat | Unitless | Minimize | α_flat | Encourages uniform piston speed segments | ADDED |  |
| Jerk regularization | Ĵ_jerk = ∫ (x‴)^2 dt / J̄_jerk | Unitless | Minimize | α_jerk | NVH & durability | ADDED |  |
| Exergy loss (optional) | Ĵ_ex = ∫ T0 Ṡ_gen dt / Ê̄ | Unitless | Minimize | α_ex | Replace vague Exergy loss (optional) — e.g., \(\int T_0\, \dot S_{\text{gen}}\, dt\) **[UPDATED]** | ADDED |  |
|  |  |  |  |  |  |  |  |
| Constraints (differentiable forms) |  |  |  |  |  |  |  |
| Constraint | Expression | Units | Type | Notes | Status |  |  |
| Stroke BCs | x(0)=0, x(T_cyc)=S | m | Equality | Clamped spline constraints | ADDED |  |  |
| Cycle timing | T_cyc fixed; φ_c=T_comp/T_cyc | s | Equality/Param | φ_c may be fixed or bounded | ADDED |  |  |
| Adiabatic segments | pV^γ = const (when valves closed via smooth gate σ_valve(t)) | — | Path | Use σ_valve∈[0,1] smooth to blend | ADDED |  |  |
| State evolution | Mass/energy balances consistent with x_burn(t) | — | Path | Use collocation defects | ADDED |  |  |
| Valve bounds | 0 ≤ L(t) ≤ L_max | m | Inequality | Sigmoid ensures C¹ | ADDED |  |  |
|  |  |  |  |  |  |  |  |
| Transcription & Grid |  |  |  |  |  |  |  |
| Choice | Value | Notes | Status |  |  |  |  |
| Transcription | Radau collocation | Tight defect control; consistent grid across phases | ADDED |  |  |  |  |
| Grid density | N=60–120 pts per cycle | Refine near reversals with clustering | ADDED |  |  |  |  |
|  |  |  |  |  |  |  |  |
| Diagnostics to Log |  |  |  |  |  |  |  |
| Metric | Target | Notes | Status |  |  |  |  |
| KKT error | < 1e-6 | Final stage | ADDED |  |  |  |  |
| Primal/dual infeasibility | < 1e-6 | Scaled | ADDED |  |  |  |  |
| Mass/energy residuals | < 1e-6 (nondim) | Per segment | ADDED |  |  |  |  |
| Active set | Stable across weight sweeps | No oscillatory activeness | ADDED |  |  |  |  |

## Phase 2 – Revised

| decisions_transmission_mapping | unnamed_1 | unnamed_2 | unnamed_3 | unnamed_4 | unnamed_5 | unnamed_6 | unnamed_7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Category | Item | Symbol | Form | Bounds | Scale | Notes | Status |
| Mapping | Ratio field | i(x) | Clamped B-spline over x∈[0,S] | i_min>0, i_max | — | Monotone if required | ADDED |
| Mapping | Smoothness | i'(x), i''(x) | Spline derivatives | \|i'\|≤κ₁, \|i''\|≤κ₂ | — | Manufacturability & surge control | ADDED |
| Loss model | Friction | P_loss | Smooth Stribeck (C¹) | Params bounded | — | Avoid Coulomb kinks | ADDED |
| Contact | Geometry | — | Hertzian contact calc | σ_H ≤ σ_lim | σ̄ | Use fatigue guardrail | ADDED |
|  |  |  |  |  |  |  |  |
| Objectives (normalized) |  |  |  |  |  |  |  |
| Objective | Expression | Norm | Role | Weight (β_i) | Notes | Status |  |
| Transmission efficiency | η̂ = η/η̄ | Unitless | Maximize | β_η | Negative sign in NLP | ADDED |  |
| Contact stress penalty | σ̂_max = σ_max/σ̄ | Unitless | Minimize | β_σ | Keep ≤ 1 via constraint too | ADDED |  |
| Loss power | P̂_loss = P_loss/P̄ | Unitless | Minimize | β_loss | Derived from Stribeck model | ADDED |  |
|  |  |  |  |  |  |  |  |
| Coupling & Power Consistency |  |  |  |  |  |  |  |
| Constraint | Expression | Units | Type | Notes | Status |  |  |
| Kinematic coupling | θ̇ = i(x)·ẋ | rad/s | Path | Enforce on same grid as Phase 1 | ADDED |  |  |
| Power balance | τ_out·θ̇ = F_p·ẋ − P_loss(x, ẋ, i) | W | Path | Ensures thermodynamic consistency | ADDED |  |  |
| Fatigue guardrail | SF = σ_lim/σ_max ≥ 1 (or life ≥ L_min) | — | Inequality | AGMA/Dang Van surrogate | ADDED |  |  |


- **[UPDATED]** Discrete hardware choices (e.g., bearing type, mesh selection) should be handled via **scenario enumeration** (optimize continuously per scenario), with smooth **surrogates** only for performance prediction—final selection occurs post-optimization.

## Phase 3 – System Co-Design

| composite_multiobjective_normalized | unnamed_1 | unnamed_2 | unnamed_3 | unnamed_4 | unnamed_5 | unnamed_6 | unnamed_7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Component | Normalized term | Role | Scalarization | Weight | Notes | Status |  |
| Work | Ŵ | Maximize | Augmented Tchebyshev | λ_W | Use normalization to avoid tuning fragility | ADDED |  |
| Efficiency | η̂ | Maximize | Augmented Tchebyshev | λ_η | — | ADDED |  |
| Jerk | Ĵ_jerk | Minimize | Augmented Tchebyshev | λ_J | — | ADDED |  |
| Stress | σ̂_max | Minimize | Augmented Tchebyshev | λ_σ | Keep ≤1 also as constraint | ADDED |  |
| Loss | P̂_loss | Minimize | Augmented Tchebyshev | λ_L | — | ADDED |  |
|  |  |  |  |  |  |  |  |
| Pareto Weight Sweep (example grid) |  |  |  |  |  |  |  |
| Case | λ_W | λ_η | λ_J | λ_σ | λ_L | Notes | Status |
| A | 0.4 | 0.3 | 0.1 | 0.1 | 0.1 | Work/efficiency biased | ADDED |
| B | 0.25 | 0.25 | 0.25 | 0.15 | 0.1 | Balanced | ADDED |
| C | 0.15 | 0.25 | 0.2 | 0.25 | 0.15 | Durability-biased | ADDED |
|  |  |  |  |  |  |  |  |
| Robustness (chance constraints) |  |  |  |  |  |  |  |
| Uncertain param | Distribution | Mean | Std/Bounds | Constraint (95%) | Notes | Status |  |
| Friction coeff μ | Normal | 0.08 | 0.02 | P(σ_max ≤ σ_lim) ≥ 0.95 | Truncate to μ≥0 | ADDED |  |
| Heat release a,m | Normal | — | — | P(η ≥ η_min) ≥ 0.95 | Calibrate from experiments | ADDED |  |
| Clearance V_c | Uniform | ±2% | — | P(Peak p ≤ p_lim) ≥ 0.95 | Manufacturing tolerance | ADDED |  |
|  |  |  |  |  |  |  |  |
| Diagnostics & Acceptance |  |  |  |  |  |  |  |
| Metric | Threshold | Notes | Status |  |  |  |  |
| KKT/feasibility | <= 1e-6 | Final stage | ADDED |  |  |  |  |
| Constraint violations | None > 1e-6 | Scaled | ADDED |  |  |  |  |
| Sensitivity | Δopt small for ±5% params | Stability check | ADDED |  |  |  |  |
| Grid invariance | Objectives stable under refinement | Discretization check | ADDED |  |  |  |  |
