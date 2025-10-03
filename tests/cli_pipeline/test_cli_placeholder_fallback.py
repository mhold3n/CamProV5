import importlib
import numpy as np


def test_placeholder_fallback_derivatives_nonzero_and_consistent(monkeypatch):
    # Import module to patch
    mod = importlib.import_module("scripts.collocation_solver_cli_fixed")

    # Force dependencies unavailable to trigger placeholder path
    monkeypatch.setattr(mod, "DEPENDENCIES_AVAILABLE", False, raising=True)

    motion_params = {
        "strokeLengthMm": 20.0,
        "samplingStepDeg": 1.0,
    }

    # Solver params value is irrelevant in placeholder path
    result = mod.solve_motion_law(
        {
            "stroke_length_mm": motion_params["strokeLengthMm"],
            "sampling_step_deg": motion_params["samplingStepDeg"],
        },
        solver_params=None,
    )

    assert result["success"] is True
    theta = np.array(result["theta_grid"])  # radians
    pos = np.array(result["position"], dtype=float)
    vel = np.array(result["velocity"], dtype=float)
    acc = np.array(result["acceleration"], dtype=float)

    # Non-zero derivatives expected for cycloidal motion
    assert np.any(np.abs(vel) > 0.0)
    assert np.any(np.abs(acc) > 0.0)

    # Consistency: vel ≈ d(pos)/dθ, acc ≈ d(vel)/dθ using central differences
    def deriv(y, x):
        dy = np.roll(y, -1) - np.roll(y, 1)
        dx = np.roll(x, -1) - np.roll(x, 1)
        return dy / np.where(dx == 0, 1.0, dx)

    vel_num = deriv(pos, theta)
    acc_num = deriv(vel, theta)

    # Tolerances allow coarse node count in placeholder
    assert np.mean(np.abs(vel - vel_num)) < 1e-1
    assert np.mean(np.abs(acc - acc_num)) < 5e-1


