import numpy as np
import pytest


class FakeGrid:
    def __init__(self, nodes):
        self.nodes = nodes
        self.node_count = len(nodes)


class FakeNLP:
    def __init__(self, nodes):
        self.grid = FakeGrid(nodes)
        self.num_variables = len(nodes)


@pytest.mark.skip(reason="Testing deprecated collocation solver - functionality moved to enhanced optimizers")
@pytest.mark.parametrize("nodes", [
    np.linspace(0, 2*np.pi, 16, endpoint=False),
    np.linspace(0, 2*np.pi, 32, endpoint=False),
])
def test_piecewise_initial_guess_continuity(monkeypatch, nodes):
    from campro.solvers import collocation_solver as cs

    # Build solver and force piecewise guess mode
    params = cs.CollocationParameters(initial_guess_type="piecewise")
    # patch casadi DM to simple wrapper
    class FakeDM:
        def __init__(self, data=None): self.data = data
        @staticmethod
        def zeros(n): return np.zeros(n)
    monkeypatch.setattr(cs, "ca", type("FakeCA", (), {"DM": FakeDM}))

    s = cs.CollocationSolver(parameters=params)
    nlp = FakeNLP(nodes)

    motion_params = {
        "strokeLengthMm": 20.0,
        "linearAccelTdcDeg": 8.0,
        "linearAccelBdcDeg": 6.0,
    }

    guess = s._piecewise_initial_guess(nlp, motion_params)
    pos = np.array(guess)[: len(nodes)] if not isinstance(guess, np.ndarray) else guess

    # Continuity: no large jumps between adjacent nodes
    diffs = np.diff(pos, append=pos[0])
    assert np.all(np.isfinite(diffs))
    assert np.max(np.abs(diffs)) < motion_params["strokeLengthMm"]


@pytest.mark.skip(reason="Testing deprecated collocation solver - functionality moved to enhanced optimizers")
def test_piecewise_initial_guess_bounds(monkeypatch):
    from campro.solvers import collocation_solver as cs
    nodes = np.linspace(0, 2*np.pi, 24, endpoint=False)

    params = cs.CollocationParameters(initial_guess_type="piecewise")
    class FakeDM:
        def __init__(self, data=None): self.data = data
        @staticmethod
        def zeros(n): return np.zeros(n)
    monkeypatch.setattr(cs, "ca", type("FakeCA", (), {"DM": FakeDM}))

    s = cs.CollocationSolver(parameters=params)
    nlp = FakeNLP(nodes)

    motion_params = {
        "strokeLengthMm": 15.0,
        "linearAccelTdcDeg": 10.0,
        "linearAccelBdcDeg": 10.0,
    }

    guess = s._piecewise_initial_guess(nlp, motion_params)
    pos = np.array(guess)[: len(nodes)] if not isinstance(guess, np.ndarray) else guess

    assert np.min(pos) >= -1e-9
    assert np.max(pos) <= motion_params["strokeLengthMm"] + 1e-9


@pytest.mark.skip(reason="Testing deprecated collocation solver - functionality moved to enhanced optimizers")
def test_piecewise_initial_guess_extreme_phase_lengths(monkeypatch):
    from campro.solvers import collocation_solver as cs
    nodes = np.linspace(0, 2*np.pi, 18, endpoint=False)

    params = cs.CollocationParameters(initial_guess_type="piecewise")
    class FakeDM:
        def __init__(self, data=None): self.data = data
        @staticmethod
        def zeros(n): return np.zeros(n)
    monkeypatch.setattr(cs, "ca", type("FakeCA", (), {"DM": FakeDM}))

    s = cs.CollocationSolver(parameters=params)
    nlp = FakeNLP(nodes)

    # Extreme: almost all rise then short fall
    motion_params = {
        "strokeLengthMm": 30.0,
        "linearAccelTdcDeg": 1.0,
        "linearAccelBdcDeg": 1.0,
        "riseDeg": 300.0,
        "dwellDeg": 0.0,
        "returnDeg": 60.0,
    }

    guess = s._piecewise_initial_guess(nlp, motion_params)
    pos = np.array(guess)[: len(nodes)] if not isinstance(guess, np.ndarray) else guess

    # Monotone rise then monotone fall is not strictly required, but we expect no NaNs and bounds respected
    assert np.all(np.isfinite(pos))
    assert 0.0 <= np.min(pos) <= np.max(pos) <= motion_params["strokeLengthMm"]


