"""Utility helpers for working with angular units.

The historical implementation of the planetary gear optimisation pipeline mixed
degrees and radians in a number of places.  This frequently resulted in hidden
unit-conversion bugs whenever caller provided data in a different unit system.

The project now standardises on **percent of ring rotation** as the canonical
representation for user supplied data (where an entire 2π rotation corresponds
to ``100%``).  This module provides a small collection of helpers that make it
easy to convert to and from that representation while still supporting the
legacy degree and radian inputs that appear throughout older scripts and
tests.

All conversion functions work with either scalar floats or :mod:`numpy`
arrays.  Consumers should call :func:`resolve_cycle_percent` to obtain a
normalised percentage for a particular parameter before performing additional
unit conversions.
"""

from __future__ import annotations

from typing import Mapping, Any, Optional, TypeVar, overload

import numpy as np

FULL_CYCLE_RADIANS = 2.0 * np.pi
FULL_CYCLE_DEGREES = 360.0
FULL_CYCLE_PERCENT = 100.0

T = TypeVar("T", float, np.ndarray)


def _as_array(value: T) -> np.ndarray:
    """Return ``value`` as a :class:`numpy.ndarray` without copying when possible."""

    if isinstance(value, np.ndarray):
        return value
    return np.asarray(value, dtype=float)


def percent_to_radians(value: T) -> T:
    """Convert a percentage of the cycle to radians."""

    array = _as_array(value) * (FULL_CYCLE_RADIANS / FULL_CYCLE_PERCENT)
    return array if isinstance(value, np.ndarray) else float(array)


def percent_to_degrees(value: T) -> T:
    """Convert a percentage of the cycle to degrees."""

    array = _as_array(value) * (FULL_CYCLE_DEGREES / FULL_CYCLE_PERCENT)
    return array if isinstance(value, np.ndarray) else float(array)


def degrees_to_percent(value: T) -> T:
    """Convert degrees of rotation to percent of the cycle."""

    array = _as_array(value) * (FULL_CYCLE_PERCENT / FULL_CYCLE_DEGREES)
    return array if isinstance(value, np.ndarray) else float(array)


def radians_to_percent(value: T) -> T:
    """Convert radians of rotation to percent of the cycle."""

    array = _as_array(value) * (FULL_CYCLE_PERCENT / FULL_CYCLE_RADIANS)
    return array if isinstance(value, np.ndarray) else float(array)


@overload
def resolve_cycle_percent(params: Mapping[str, Any], base_key: str) -> float:
    ...


@overload
def resolve_cycle_percent(
    params: Mapping[str, Any], base_key: str, default_percent: float
) -> float:
    ...


def resolve_cycle_percent(
    params: Mapping[str, Any], base_key: str, default_percent: Optional[float] = None
) -> float:
    """Return ``base_key`` expressed as a percentage of the cycle.

    The helper first looks for ``"{base_key}Percent"`` in ``params``.  If that
    entry does not exist it attempts to resolve ``"{base_key}Deg"`` and
    ``"{base_key}Rad"`` respectively.  When none of the keys are present the
    supplied ``default_percent`` is returned.  If no default is provided a
    :class:`KeyError` is raised to signal the missing configuration.
    """

    percent_key = f"{base_key}Percent"
    if percent_key in params:
        return float(params[percent_key])

    deg_key = f"{base_key}Deg"
    if deg_key in params:
        return float(degrees_to_percent(params[deg_key]))

    rad_key = f"{base_key}Rad"
    if rad_key in params:
        return float(radians_to_percent(params[rad_key]))

    if default_percent is not None:
        return default_percent

    raise KeyError(
        f"Unable to resolve '{base_key}' – expected percent/degree/radian entry"
    )


def ensure_percent_grid(step_percent: float) -> float:
    """Normalise percentage step sizes.

    ``numpy.arange`` is sensitive to floating-point rounding which can leave the
    final value just shy of the expected end point.  Normalising the step value
    through this helper ensures a consistent dtype which in turn keeps the grid
    construction stable.
    """

    return float(step_percent)

