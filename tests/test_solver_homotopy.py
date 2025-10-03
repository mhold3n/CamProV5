import casadi as ca

from campro.solver_config import homotopy_run, homotopy_stages


def _build_quadratic_nlp(smoothing: float):
    # Minimize 0.5*x^T Q x with Q well-scaled; smoothing unused but ensures API compat
    x = ca.MX.sym("x", 3)
    Q = ca.DM.eye(3)
    nlp = {"x": x, "f": 0.5 * ca.dot(x, Q @ x), "g": ca.vertcat()}
    return nlp


def test_homotopy_runs_and_returns_solution():
    res = homotopy_run(_build_quadratic_nlp, smoothing_sequence=[1.0, 0.5, 0.1], initial_guess=ca.DM([10, -5, 2]))
    assert "x" in res
    x_sol = ca.DM(res["x"]).full().ravel()
    # Minimum at zero
    assert (abs(x_sol) < 1e-6).all()


def test_homotopy_stages_with_options():
    opts_seq = [
        {"ipopt": {"tol": 1e-2, "acceptable_tol": 1e-1}},
        {"ipopt": {"tol": 1e-4, "acceptable_tol": 1e-3}},
        {"ipopt": {"tol": 1e-6, "acceptable_tol": 1e-5}},
    ]
    res = homotopy_stages(_build_quadratic_nlp, smoothing_sequence=[1.0, 0.5, 0.1], initial_guess=ca.DM([1, 1, 1]), option_sequence=opts_seq)
    x_sol = ca.DM(res["x"]).full().ravel()
    assert (abs(x_sol) < 1e-6).all()
