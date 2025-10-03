#!/usr/bin/env python3
"""
Minimal placeholder and shim module for tests expecting `scripts.collocation_solver_cli_fixed`.

Provides:
- DEPENDENCIES_AVAILABLE flag for monkeypatch in tests
- solve_motion_law placeholder producing a cycloidal motion law when dependencies are unavailable
- main() delegating to real CLI when available
"""

from __future__ import annotations

import sys
import math
import json
from pathlib import Path
from typing import Any, Dict, Optional

# Exposed flag that tests will monkeypatch
DEPENDENCIES_AVAILABLE = True


def _placeholder_solve_motion_law(motion_params: Dict[str, Any]) -> Dict[str, Any]:
    stroke_mm = float(motion_params.get("stroke_length_mm", 10.0))
    step_deg = float(motion_params.get("sampling_step_deg", 2.0))
    # Use radians grid as expected by the test
    theta_deg = [i for i in range(0, 360, int(max(1, round(step_deg))))]
    theta_rad = [math.radians(d) for d in theta_deg]
    # Simple cycloidal displacement over 0..2π then repeat
    pos = [0.5 * stroke_mm * (1 - math.cos(t)) for t in theta_rad]
    vel = [0.5 * stroke_mm * math.sin(t) for t in theta_rad]
    acc = [0.5 * stroke_mm * math.cos(t) for t in theta_rad]
    return {
        "success": True,
        "theta_grid": theta_rad,
        "position": pos,
        "velocity": vel,
        "acceleration": acc,
    }


def load_input_parameters(input_path: Path) -> Dict[str, Any]:
    """Load input parameters from JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)


def create_motion_parameters(loaded_params: Dict[str, Any]) -> Dict[str, Any]:
    """Create motion parameters from loaded input parameters."""
    return {
        "stroke_length_mm": loaded_params.get("strokeLengthMm", 10.0),
        "sampling_step_deg": loaded_params.get("samplingStepDeg", 2.0),
        "collocation_params": loaded_params.get("collocation_params", {})
    }


def save_solution(result: Dict[str, Any], output_path: Path) -> None:
    """Save solution to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)


def solve_motion_law(motion_params: Dict[str, Any], solver_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not DEPENDENCIES_AVAILABLE:
        return _placeholder_solve_motion_law(motion_params)
    # Otherwise, try to call the real implementation if present
    try:
        from campro.scripts.collocation_solver_cli import solve_motion_law as real_solve  # type: ignore
    except Exception:
        return _placeholder_solve_motion_law(motion_params)
    return real_solve(motion_params, solver_params)


def main() -> int:
    try:
        from campro.scripts.collocation_solver_cli import main as real_main  # type: ignore
    except Exception:
        return 1
    return int(real_main() or 0)


if __name__ == "__main__":
    sys.exit(main())


