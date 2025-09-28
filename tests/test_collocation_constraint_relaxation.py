import numpy as np
import types
import pytest


def make_fake_casadi(calls):
    class FakeDM:
        def __init__(self, data=None):
            self.data = np.array(data) if data is not None else None
        @staticmethod
        def zeros(n):
            return np.zeros(n)

    class FakeSolver:
        def __init__(self, name, algo, problem, options):
            self.name = name
            self.options = options
            self.problem = problem

        def stats(self):
            return {"return_status": "Solve_Succeeded", "iter_count": 5}

        def __call__(self, x0, lbx, ubx, lbg, ubg):
            # record constraint bounds for inspection per step
            calls.append({"lbg": np.array(lbg), "ubg": np.array(ubg)})
            # synthesize decreasing violation if bounds are relaxed
            width = np.max(np.array(ubg) - np.array(lbg))
            violation = max(0.0, 1.0 - min(1.0, width))
            return {
                "x": np.zeros_like(x0),
                "f": np.array([0.0]),
                "g": np.array([violation]),
            }

    fake = types.SimpleNamespace()
    fake.DM = FakeDM
    fake.nlpsol = lambda name, algo, problem, options: FakeSolver(name, algo, problem, options)
    return fake


class FakeContinuation:
    def generate_continuation_sequence(self):
        return [0.5, 0.8, 1.0]

    def adjust_regularization(self, weight, factor):
        return max(1e-9, weight * factor)


class FakeWarmStart:
    def perturb_solution(self, x, scale):
        return x

    def generate_sinusoidal_start(self, nodes, stroke_length, motion_params):
        return np.zeros_like(nodes)


class FakeNumericalGuards:
    def __init__(self):
        self.continuation = FakeContinuation()
        self.warm_start = FakeWarmStart()

    def setup_robust_solver_options(self, options):
        return dict(options)


class FakeGrid:
    def __init__(self, n=8):
        self.node_count = n
        self.nodes = np.linspace(0, 2 * np.pi, n, endpoint=False)


class FakeNLP:
    def __init__(self):
        self.casadi_problem = {"dummy": True}
        self.grid = FakeGrid(8)
        self.num_variables = 8
        # Tight bounds that benefit from relaxation
        self.variable_bounds = {"lower": -np.ones(8), "upper": np.ones(8)}
        self.constraint_bounds = {"lower": np.zeros(3), "upper": np.zeros(3)}


@pytest.fixture
def solver_with_fakes(monkeypatch):
    from campro.solvers import collocation_solver as cs

    # patch casadi
    calls = []
    fake_ca = make_fake_casadi(calls)
    monkeypatch.setattr(cs, "ca", fake_ca, raising=True)
    monkeypatch.setattr(cs, "CASADI_AVAILABLE", True, raising=True)

    # construct solver
    params = cs.CollocationParameters(use_continuation=True, continuation_steps=3)
    s = cs.CollocationSolver(parameters=params)
    # inject numerical guards and fake nlp
    s.numerical_guards = FakeNumericalGuards()
    nlp = FakeNLP()
    return s, nlp, calls


def test_relaxes_constraints_in_early_steps(solver_with_fakes, monkeypatch):
    s, nlp, calls = solver_with_fakes

    # run continuation directly
    res = s._solve_with_continuation(nlp, {"strokeLengthMm": 10.0}, {"ipopt.tol": 1e-8})

    # Ensure multiple steps executed
    assert len(calls) >= 2
    early_lbg = calls[0]["lbg"]
    early_ubg = calls[0]["ubg"]
    orig_lbg = nlp.constraint_bounds["lower"]
    orig_ubg = nlp.constraint_bounds["upper"]

    # Expect relaxation: early step bounds should be wider than original
    assert np.any(early_lbg < orig_lbg) or np.any(early_ubg > orig_ubg), (
        "Early continuation step should relax constraint bounds"
    )


def test_first_step_infeasible_raises_clear_error(monkeypatch):
    from campro.solvers import collocation_solver as cs

    calls = []
    # Fake solver that always raises at first call
    class RaisingSolver:
        def __init__(self, *a, **k):
            pass
        def stats(self):
            return {"return_status": "Solve_Failed"}
        def __call__(self, *a, **k):
            raise RuntimeError("Infeasible problem")

    fake = make_fake_casadi(calls)
    fake.nlpsol = lambda *a, **k: RaisingSolver()
    monkeypatch.setattr(cs, "ca", fake, raising=True)
    monkeypatch.setattr(cs, "CASADI_AVAILABLE", True, raising=True)

    s = cs.CollocationSolver(parameters=cs.CollocationParameters(use_continuation=True))
    s.numerical_guards = FakeNumericalGuards()
    nlp = FakeNLP()

    with pytest.raises(RuntimeError):
        s._solve_with_continuation(nlp, {"strokeLengthMm": 10.0}, {"ipopt.tol": 1e-8})


