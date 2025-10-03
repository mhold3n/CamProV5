## Phase 2 Optimization: Constraint Simplification and Stabilization

This document explains the changes applied to the Phase 2 gear optimization routine to improve feasibility and stability while preserving the theoretical goals. The primary shift is from dense hard constraints at every collocation node to a hybrid strategy using sparse hard constraints plus soft penalties, alongside stronger smoothness regularization.

### Rationale

- Dense equality constraints at every node (unified geometry, no-slip, global integral, planet rotation propagation, contact/stress) led to overconstraint, infeasibility, and NaNs.
- CasADi/IPOPT responds better when the problem has: fewer hard equalities, well-conditioned bounds, smooth objectives, and soft penalties that guide rather than strictly force.

### High-level Changes

- Sparse hard constraints at key nodes; soft penalties elsewhere.
- Relax global integral to a soft (or more tolerant) constraint.
- Remove φ(θ) as an optimization decision variable in the target design; derive it post-solve from r(θ) via accumulation. (Interim code path keeps φ present but its constraint is disabled; final step will fully drop it.)
- Strengthen smoothness penalties on `r(θ)` and radii to regularize solutions.
- Temporarily drop contact/stress hard constraints; reintroduce as soft penalties after convergence.

### What’s Enforced as Hard Constraints (current)

- Unified geometry and no-slip are enforced at a sparse subset of nodes (every other node) to anchor feasibility.
- Global integral is kept but with relaxed tolerance (can be moved to soft penalty if needed).
- Planet-rotation propagation constraint is disabled; φ(θ) will be derived post-solve from r(θ).

### What’s Penalized in the Objective (soft)

- Deviation from unified geometry across all nodes (L2 penalty; future step).
- Deviation from no-slip across all nodes (L2 penalty; future step).
- Deviation of global integral from the target 2:1 ratio (already relaxed; move to penalty if needed).
- Smoothness penalties on radii and r(θ) (L2 of first/second difference).

### Implementation Notes (current code)

- File: `campro/optimization/phase2_gear_optimizer.py`
  - Unified constraint and no-slip now enforced at sparse nodes only.
  - Global integral uses relaxed tolerance; will be converted to soft penalty if still infeasible.
  - Planet rotation constraint disabled; φ(θ) will be derived post-solve from r(θ) in a subsequent edit.
  - Contact/stress constraints disabled to avoid NaNs and overconstraint.

#### Example: Sparse hard constraints

```286:296:campro/optimization/phase2_gear_optimizer.py
# 1. SIMPLIFIED Unified constraint system - only enforce at key points
for i in range(0, n, 2):
    g.append(unified_constraint[i])
    lbg.append(0.0)
    ubg.append(0.0)

# 2. SIMPLIFIED No-slip constraint - only enforce at key points
for i in range(0, n, 2):
    g.append(r_inst[i] * planet_radius[i] - ring_radius[i])
    lbg.append(0.0)
    ubg.append(0.0)
```

#### Example: Relaxed global integral

```299:308:campro/optimization/phase2_gear_optimizer.py
ring_rotation_deg = gear_params.get('ringRotationDeg', 180.0)
step_deg = ring_rotation_deg / (n - 1)
integral_r = ca.sum1(r_inst) * step_deg
expected_integral = 2.0 * np.pi  # 2π for 2:1 ratio
g.append(integral_r - expected_integral)
lbg.append(-1.0)
ubg.append(1.0)
```

#### Example: Disabled φ(θ) constraint (to be derived post-solve)

```310:315:campro/optimization/phase2_gear_optimizer.py
# Planet rotation constraint - DISABLED for now
# for i in range(1, n, 2):
#     g.append(phi_planet[i] - phi_planet[i-1] - r_inst[i-1] * step_deg)
#     lbg.append(0.0)
#     ubg.append(0.0)
```

### Planned Next Steps

1. Remove φ(θ) from decision vector; compute post-solve via cumulative sum of r(θ).
2. Add soft penalties for unified and no-slip at all nodes; keep sparse hard anchor nodes.
3. Add smoothness penalties for `r(θ)`, `R_sun(θ)`, `R_planet(θ)`, `R_ring(θ)` (first/second differences).
4. Gradually reintroduce contact/stress as soft penalties with proper scaling.
5. Tighten tolerances (continuation): increase nodes for hard constraints, reduce penalty tolerances.

### Tuning Guidance

- Start with wider bounds and higher smoothness weights; reduce gradually.
- Prefer soft penalties (with weights) for complex coupling constraints; avoid overdetermined equalities.
- Monitor IPOPT statuses: if `Infeasible_Problem_Detected`, relax constraints or convert to penalties.

### Impact

- Improves feasibility and convergence.
- Maintains theoretical structure while enabling progressive tightening.
- Provides a stable base for reintroducing richer physics (contact/stress) as penalties.




