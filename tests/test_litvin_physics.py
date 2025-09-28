"""
Litvin non-circular gear physics tests.

These tests validate tooth thickness, contact ratio, and gear radius
calculations on non-circular (Litvin-style) gear geometries.
"""

import numpy as np
import types
import pytest

from campro.solvers.discretization import CollocationGrid
from campro.solvers.litvin_constraints import LitvinConstraintBuilder, LitvinParameters
from campro.solvers.validation import DenseValidator, ValidationLimits
from campro.solvers.robust_gear_design import (
    RobustGearDesign, GearMaterialProperties, GearDesignParameters,
)


def make_litvin_geometry(node_count: int = 64, center_distance: float = 90.0):
    grid = CollocationGrid(node_count=node_count, node_type="LGL")
    theta = grid.nodes
    # Non-circular cam radius: base + first/second harmonics
    cam_base = 40.0
    cam_radius = cam_base + 4.0 * np.cos(theta) + 1.5 * np.cos(2 * theta)
    ring_radius = center_distance - cam_radius
    return grid, theta, cam_radius, ring_radius


def test_litvin_contact_ratio_builder_uses_variable_radii(monkeypatch):
    grid, _, cam_radius, ring_radius = make_litvin_geometry()
    params = LitvinParameters(center_distance=90.0, cam_base_radius=40.0)
    builder = LitvinConstraintBuilder(params, grid)

    # Patch casadi namespace used inside builder to numpy functions
    fake_ca = types.SimpleNamespace(
        cos=np.cos,
        sqrt=np.sqrt,
        sum1=lambda x: np.sum(x),
        fmax=lambda a, b: np.maximum(a, b),
    )
    monkeypatch.setattr("campro.solvers.litvin_constraints.ca", fake_ca, raising=True)

    # Call private helper directly to avoid CASADI_AVAILABLE gate
    cr = builder._build_contact_ratio_constraints(cam_radius, ring_radius)

    assert isinstance(cr, dict)
    assert len(cr["expressions"]) == 1
    assert cr["lower"][0] == params.contact_ratio_min
    assert cr["upper"][0] == float("inf")


def test_robust_contact_ratio_on_litvin_geometry():
    grid, theta, cam_radius, ring_radius = make_litvin_geometry()

    material = GearMaterialProperties()
    design = GearDesignParameters()
    rgd = RobustGearDesign(material, design)

    pressure_angle = np.deg2rad(20.0 + 3.0 * np.sin(theta))
    addendum = np.full_like(theta, 2.5)
    dedendum = np.full_like(theta, 3.0)

    contact_ratio = rgd.calculate_contact_ratio(cam_radius, ring_radius, pressure_angle, addendum, dedendum)

    assert contact_ratio.shape == theta.shape
    assert np.all(np.isfinite(contact_ratio))
    assert np.all(contact_ratio >= 0.0)
    # Should vary with geometry; not constant
    assert np.std(contact_ratio) > 1e-6


def test_robust_tooth_thickness_litvin_load_profile():
    grid, theta, cam_radius, _ = make_litvin_geometry()

    material = GearMaterialProperties()
    design = GearDesignParameters()
    rgd = RobustGearDesign(material, design)

    # Varying contact force over cycle (simulate combustion + inertia)
    contact_force = 1000.0 + 300.0 * (1.0 + np.sin(theta))
    tooth_count = 2.0 * cam_radius / 5.0  # module≈5mm equivalent

    thickness = rgd.calculate_tooth_thickness(cam_radius, contact_force, tooth_count)

    assert thickness.shape == theta.shape
    assert np.all(np.isfinite(thickness))
    assert np.all(thickness > 0.0)
    # Not flat across cycle
    assert np.std(thickness) > 1e-6


def test_robust_gear_radius_under_litvin_conditions():
    grid, theta, *_ = make_litvin_geometry()

    material = GearMaterialProperties()
    design = GearDesignParameters()
    rgd = RobustGearDesign(material, design)

    torque = 150.0 + 50.0 * np.cos(theta)
    rpm = 2000.0 + 500.0 * np.sin(theta)

    radius = rgd.calculate_gear_radius(torque, rpm)

    assert radius.shape == theta.shape
    assert np.all(np.isfinite(radius))
    assert np.all(radius >= 10.0)


def test_litvin_validation_uses_local_geometry():
    grid, theta, cam_radius, ring_radius = make_litvin_geometry()

    # Build a motion law consistent with the geometry
    position = cam_radius - np.min(cam_radius)
    velocity = np.gradient(position, theta)
    acceleration = np.gradient(velocity, theta)

    validator = DenseValidator(ValidationLimits())
    report = validator.validate_solution(theta, position, velocity, acceleration,
                                         {"strokeLengthMm": float(np.ptp(position)), "rpm": 3000.0})

    assert report is not None
    # Ensure it generated pressure angle results reflecting local geometry sampling
    assert hasattr(report, "pressure_angle_results")
    assert len(report.pressure_angle_results) > 0


