## Full Implementation TDD Guide

This guide defines a strict Test-Driven Development (TDD) workflow to replace all placeholder or simplified implementations with robust, production‑ready solutions. For every item, unit tests are written first and must fail before implementation. Tests should stress physics and simulation components across nominal, edge, and experimental conditions.

### Repository/CI invariants
- All tests live in `tests/` and follow pytest naming `test_*.py`.
- Each commit/PR must pass: `ruff --fix`, `mypy --strict`, `pytest -q`.
- No bare `print(` outside tests; use `campro.logging.get_logger`.
- New public symbols require full type hints (mypy strict).
- Duplicate literals used in ≥2 modules go to `campro.constants`.

### General TDD cycle per item
1. Write failing tests targeting the new behavior and physics correctness.
2. Run CI locally (ruff, mypy, pytest) to confirm failures.
3. Implement the smallest viable solution.
4. Refactor for clarity and performance without changing behavior.
5. Add property-based tests (optional but recommended for physics invariants).
6. Re‑run CI locally; ensure green across lint, types, tests.

### Test design principles (physics & simulation)
- Nominal scenarios reflect expected operating ranges.
- Edge scenarios include boundary values, discontinuities, and numerical‑stability stressors (e.g., near singularities, very small/large magnitudes).
- Experimental scenarios probe beyond standard ranges to validate graceful degradation and defined failure modes.
- Validate invariants: conservation/energy consistency (when applicable), periodicity/continuity, dimension/units sanity, monotonicity or bounds.
- Include tolerance windows and numerical robustness checks (condition numbers, step sensitivity, convergence criteria).

## Item‑by‑item TDD outline

### 1) Periodic LGL nodes in `campro/solvers/discretization.py`
- Tests (write first):
  - Validate node periodicity (first/last equivalence modulo 2π or period).
  - Compare spacing and quadrature weights vs known periodic LGL references.
  - Stress: very low/high node counts; ensure stability and ordering.
- Acceptance: numerical integration error on smooth periodic functions below threshold (e.g., ≤1e‑6 relative for medium N).

### 2) Constraint relaxation strategy in `campro/solvers/collocation_solver.py`
- Tests (write first):
  - Multi‑stage solve reduces violations monotonically.
  - Edge: infeasible constraints trigger clear exception with diagnostics.
  - Stress: tight bounds; verify convergence or proper failure.
- Acceptance: measured constraint residuals fall below tolerance after final stage.

### 3) Piecewise initial guess in `campro/solvers/collocation_solver.py`
- Tests (write first):
  - Construct initial guess from traditional motion phases; continuity at phase joins.
  - Stress: extreme phase durations; still continuous and within bounds.
- Acceptance: collocation residuals from initial guess are finite and within configured pre‑solve thresholds.

### 4) Robust fallback in `scripts/collocation_solver_cli_fixed.py`
- Replace cycloidal placeholder and zero derivatives.
- Tests (write first):
  - Fallback produces position, velocity, acceleration consistent via numerical differentiation identities.
  - Edge: small stroke; large stroke; varying node counts.
- Acceptance: velocity ≈ d(position)/dθ, acceleration ≈ d(velocity)/dθ within tolerance; no zero‑filled derivatives.

### 5) Complete Python CasADi bridge and wire into Kotlin `CollocationMotionSolver`
- Tests (write first):
  - Python bridge round‑trip (JSON IO, correct shapes/units).
  - Kotlin integration chooses Python solution when available; no sinusoidal placeholder.
  - Failure paths provide actionable errors.
- Acceptance: integration test verifies non‑placeholder trajectories and constraint satisfaction.

### 6) Physics‑based energy objective in `campro/models/movement_law.py`
- Replace approximate energy from acceleration‑squared with proper power/energy integration.
- Tests (write first):
  - Power = force × velocity; energy integrates over period.
  - Stress: variable time‑step/angle‑step consistency; near‑zero velocity phases.
- Acceptance: reference scenarios match analytical/benchmark values within tolerance.

### 7) Replace approximate BDC in `campro/solvers/nlp_formulation.py`
- Tests (write first):
  - Detect BDC via data/constraints (max displacement) not fixed 180° assumption.
  - Edge: flat regions or multiple local extrema.
- Acceptance: correct BDC index/angle identified with tie‑break rules and stability to noise.

### 8) Real FEA JNI outputs in `camprofw/rust/fea-engine/src/jni.rs`
- Remove `placeHolder` fields; return real metrics.
- Tests (write first):
  - JNI returns structured, schema‑validated JSON.
  - Edge: empty/degenerate meshes return defined warnings and minimal valid output.
- Acceptance: round‑trip read in Kotlin/Python succeeds; values pass basic physical sanity checks.

### 9) Implement `FeaResultsLoader` in `desktop/.../AnimationEngine.kt`
- Tests (write first):
  - Parse real analysis data; map to in‑app types; handle missing fields gracefully.
  - Stress: large files, partial data; ensure performance and resilience.
- Acceptance: UI components receive complete datasets; placeholder paths removed.

### 10) Real Kotlin invocation in `scripts/generate_gear_profiles.py`
- Replace temporary Python simulation with actual Kotlin bridge.
- Tests (write first):
  - Command/bridge executes deterministically; validates schema and units.
  - Failure: Kotlin unavailable → skip with clear message (not silent fallback).
- Acceptance: generated profiles match Kotlin computation within numeric tolerances.

### 11) Harden Kotlin NLP setup in `CollocationMotionSolver`
- Remove "placeholder for now" path; enforce constraints and solver configuration.
- Tests (write first):
  - Feasibility checks, residual thresholds, convergence diagnostics.
  - Stress: noisy inputs; parameter extremes; ensure bounded outputs or explicit errors.
- Acceptance: no sinusoidal fallback; consistent convergence in nominal cases.

### 12) Implement `desktop/build.gradle.kts`
- Replace placeholder content with working Compose Desktop build config.
- Tests (write first):
  - Gradle build integration test (headless) verifies tasks, artifacts, and dependency graph.
- Acceptance: CI can build and run desktop tests without manual steps.

### 13) Audit tests vs production boundaries
- Tests (write first):
  - Identify and update any tests asserting placeholder behavior.
  - Add boundary tests ensuring production paths are exercised.
- Acceptance: no tests rely on placeholders; all critical paths covered.

### 14) Backfill and CI hardening
- Tests (write first):
  - Property‑based tests for invariants (use Hypothesis where applicable).
  - Performance guards (max solve time for standard cases).
- Acceptance: CI suite executes quickly, deterministically; clear failure messages.

## Execution checklist per item
- Add/extend tests in `tests/` (pytest) and/or Kotlin tests for desktop components.
- Run: `ruff --fix && mypy --strict && pytest -q`.
- Implement feature with full type hints and logging via `campro.logging`.
- Refactor, re‑run CI, and update docs in `docs/` (append API/status where needed).

## Notes on data, fixtures, and metrics
- Prefer small, deterministic fixtures; version them if generated.
- Track numerical tolerances explicitly; document rationale.
- Record key metrics (residuals, iterations, timings) in test assertions where stable.


