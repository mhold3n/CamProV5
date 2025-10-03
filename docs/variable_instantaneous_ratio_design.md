# Variable Instantaneous Gear Ratio r(θ) – Design Doc

## Overview

This document specifies the discretized instantaneous ratio model r(θ) for the eccentric planetary engine. The prior implementation and some scripts assumed a fixed 2:1 mapping (φ(θ) = 2θ). We replace that with a per-node variable r(θ_i) that adapts to kinematic/dynamic demands while maintaining no slip locally and 2:1 net rotation globally.

## Key Concepts

- Instantaneous ratio r(θ) := dφ/dθ, where θ is ring angle and φ is planet angle.
- No slip at contact with constant ring speed implies:
  r(θ_i) = R_ring(θ_i) / R_planet(θ_i).
- Global 2:1 integral over the ring span Θ:
  Σ_i r(θ_i) Δθ = 2 Θ.
- Geometry linkage (unchanged):
  R_ring(θ_i) = R_sun(θ_i) + 2 R_planet(θ_i).

## Phase 2 Optimization Changes

### Decision Variables (per node)
- R_sun[θ_i], R_planet[θ_i], R_ring[θ_i]
- r[θ_i] (new)

### Constraints
- Geometric linkage: R_ring = R_sun + 2 R_planet (equality per node)
- No-slip: r_i − R_ring_i / R_planet_i = 0 (per node)
- Global 2:1: sum over intervals Σ_{i=0..n−2} r_i Δθ = 2 Θ
- Bounds: r_min ≤ r_i ≤ r_max; gear radii kept within feasible ranges

### Objective
- Smoothness penalties on R_sun, R_planet, R_ring
- Optional smoothness/TV penalty on r(θ) via `rSmoothnessWeight`
- Existing force-transfer/efficiency terms remain

### Mapping φ(θ)
- Remove fixed φ = 2θ. Accumulate from r:
  φ_k = φ_0 + Σ_{i=0..k−1} r_i Δθ

## Profile Generation Updates

- `phi_of_theta_deg` is computed from provided `instantaneous_ratio` when available; else falls back to fixed gearRatio.
- Hard-coded 2:1 symmetry replaced by optional soft prior `enableSymmetryPrior/symmetryWeight` (off by default).
- Diagnostics report effective global ratio from φ(θ).

## Parameters and Defaults

- New inputs:
  - rMin (default 1.5), rMax (default 2.5)
  - rSmoothnessWeight (default 0.0)
  - enableSymmetryPrior (default false), symmetryWeight (default 0.5)

## Backward Compatibility

- Setting rMin = rMax = gearRatio (e.g., 2.0) reproduces the fixed-ratio behavior. Tests confirm r(θ) ≡ 2 and φ accumulation equals 2 Θ.

## Testing

- Unit tests cover:
  - No-slip enforcement r_i = R_ring_i / R_planet_i
  - Global integral 2:1 over intervals
  - Back-compat with r ≡ 2
  - Profile generator using provided r(θ)

## Impact

- Enables ratio adaptation at kinematic transitions without violating global 2:1.
- Minimal API changes: additional arrays exposed in pipeline outputs for diagnostics (`instantaneous_ratio`, `accumulated_planet_angle_deg`).


