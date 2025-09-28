import json
from pathlib import Path
import tempfile
import importlib
import numpy as np


def test_cli_json_roundtrip_schema_and_units(monkeypatch):
    mod = importlib.import_module("scripts.collocation_solver_cli_fixed")

    # Force placeholder path to avoid external deps; we validate schema/units not solver internals
    monkeypatch.setattr(mod, "DEPENDENCIES_AVAILABLE", False, raising=True)

    # Create synthetic input params JSON (angles in degrees, stroke in mm)
    params = {
        "strokeLengthMm": 12.5,
        "samplingStepDeg": 5.0,
        "collocation_params": {
            "node_count": 16,
            "node_type": "LGL"
        }
    }

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        input_path = td / "input.json"
        output_path = td / "output.json"
        log_path = td / "solver.log"

        input_path.write_text(json.dumps(params))

        # Load and create param dicts
        loaded = mod.load_input_parameters(input_path)
        motion = mod.create_motion_parameters(loaded)

        # Solve
        result = mod.solve_motion_law(motion, solver_params=None)

        # Save output and read back
        mod.save_solution(result, output_path)
        out = json.loads(output_path.read_text())

        # Schema checks
        assert out.get("success") is True
        for key in ["theta_grid", "position", "velocity", "acceleration"]:
            assert key in out and isinstance(out[key], list) and len(out[key]) > 0

        # Units/shape checks
        theta = np.array(out["theta_grid"], dtype=float)
        assert np.all(theta >= 0.0) and np.all(theta < 2 * np.pi), "theta should be radians in [0, 2π)"

        pos = np.array(out["position"], dtype=float)
        assert np.min(pos) >= -1e-9 and np.max(pos) <= params["strokeLengthMm"] + 1e-9

        # Derivatives present and finite
        vel = np.array(out["velocity"], dtype=float)
        acc = np.array(out["acceleration"], dtype=float)
        assert np.all(np.isfinite(vel)) and np.all(np.isfinite(acc))


