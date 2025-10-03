import math
import pytest
import casadi as ca

from campro.models import (
    smooth_valve_lift,
    wiebe_heat_release,
    smooth_friction_stribeck,
)
from campro.models.core import (
    smooth_valve_lift_d2,
    wiebe_heat_release_d2,
    smooth_friction_stribeck_d2,
)


def _is_finite_dm(x: ca.DM) -> bool:
    try:
        xv = float(ca.DM(x))
        return math.isfinite(xv)
    except Exception:
        return False


def test_smooth_valve_basic_continuity() -> None:
    t = ca.MX.sym("t")
    expr = smooth_valve_lift(t, t_open=0.2, t_close=0.8, L_max=1.0, eps=0.05)
    f = ca.Function("f", [t], [expr])

    for tv in [0.0, 0.19, 0.2, 0.21, 0.79, 0.8, 0.81, 1.0]:
        val = f(tv)
        assert _is_finite_dm(val)
        assert float(val) >= -1e-9
        assert float(val) <= 1.0 + 1e-9

    # Check derivative exists near transitions
    dfdt = ca.jacobian(expr, t)
    g = ca.Function("g", [t], [dfdt])
    for tv in [0.2, 0.8]:
        dv = g(tv)
        assert _is_finite_dm(dv)


def test_wiebe_is_monotone_after_start_angle() -> None:
    phi = ca.MX.sym("phi")
    expr = wiebe_heat_release(phi, a=5.0, m=2.0, theta0=0.1, theta_b=0.5)
    f = ca.Function("f", [phi], [expr])
    p1 = float(f(0.6))
    p2 = float(f(0.7))
    assert 0.0 <= p1 <= 1.0
    assert 0.0 <= p2 <= 1.0
    assert p2 >= p1 - 1e-9


def test_stribeck_is_smooth_and_finite() -> None:
    v = ca.MX.sym("v")
    expr = smooth_friction_stribeck(v, fs=100.0, fc=50.0, vs=0.2, k_visc=1.0)
    f = ca.Function("f", [v], [expr])
    df = ca.Function("df", [v], [ca.jacobian(expr, v)])

    for vv in [-1.0, -0.3, 0.0, 0.1, 0.3, 1.0]:
        val = f(vv)
        dval = df(vv)
        assert _is_finite_dm(val)
        assert _is_finite_dm(dval)


def test_second_derivatives_are_finite() -> None:
    # Valve
    d2_val = smooth_valve_lift_d2(0.5, t_open=0.2, t_close=0.8, L_max=1.0, eps=0.05)
    assert _is_finite_dm(d2_val)
    # Wiebe
    d2_w = wiebe_heat_release_d2(0.5, a=5.0, m=2.0, theta0=0.1, theta_b=0.5)
    assert _is_finite_dm(d2_w)
    # Stribeck
    d2_s = smooth_friction_stribeck_d2(0.1, fs=100.0, fc=50.0, vs=0.2, k_visc=1.0)
    assert _is_finite_dm(d2_s)


def test_invalid_parameters_raise() -> None:
    with pytest.raises(ValueError):
        smooth_valve_lift(0.0, t_open=0.8, t_close=0.2, L_max=1.0, eps=0.05)
    with pytest.raises(ValueError):
        wiebe_heat_release(0.0, a=-1.0, m=2.0, theta0=0.1, theta_b=0.5)
    with pytest.raises(ValueError):
        wiebe_heat_release(0.0, a=5.0, m=2.0, theta0=0.1, theta_b=0.0)
    with pytest.raises(ValueError):
        smooth_friction_stribeck(0.0, fs=100.0, fc=50.0, vs=0.0, k_visc=1.0)
