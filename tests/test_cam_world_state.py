from math import cos, sin, radians
import pytest

def transform(points, phi, r_center):
    phi_rad = radians(phi)
    c = cos(phi_rad)
    s = sin(phi_rad)
    cx = r_center * c
    cy = r_center * s
    out = []
    for x, y in points:
        wx = c * x - s * y + cx
        wy = s * x + c * y + cy
        out.append((wx, wy))
    return out

def assert_pairs_close(result, expected):
    assert len(result) == len(expected)
    for (rx, ry), (ex, ey) in zip(result, expected):
        assert rx == pytest.approx(ex)
        assert ry == pytest.approx(ey)

def test_rotation_only():
    base = [(1.0, 0.0), (0.0, 1.0)]
    result = transform(base, 90.0, 0.0)
    expected = [(0.0, 1.0), (-1.0, 0.0)]
    assert_pairs_close(result, expected)

def test_rotation_and_translation():
    base = [(1.0, 0.0)]
    result = transform(base, 0.0, 2.0)
    expected = [(3.0, 0.0)]
    assert_pairs_close(result, expected)
