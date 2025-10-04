"""Utility helpers for unified solver result handling."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Mapping


def extract_mapping_value(source: Mapping[str, Any], *keys: str) -> Any:
    """Return the first non-empty mapping value for the given keys."""

    for key in keys:
        value = source.get(key)
        if value is None:
            continue
        if isinstance(value, dict) and not value:
            continue
        return value
    return None


def extract_kkt(source: Mapping[str, Any]) -> Dict[str, float]:
    """Return KKT residuals using either naming convention."""

    value = extract_mapping_value(source, "kkt", "kkt_residuals")
    return value or {}


def ensure_kkt_aliases(result: Dict[str, Any]) -> None:
    """Populate both KKT keys when data is present."""

    kkt = extract_kkt(result)
    if kkt:
        result["kkt"] = kkt
        result["kkt_residuals"] = kkt


def solution_to_dict(solution: Any) -> Dict[str, Any]:
    """Normalise solver outputs (dataclass, object, dict) into a dict."""

    if solution is None:
        return {}

    if isinstance(solution, dict):
        result = dict(solution)
    elif is_dataclass(solution):
        result = asdict(solution)
    elif hasattr(solution, "to_dict") and callable(solution.to_dict):
        try:
            result = dict(solution.to_dict())
        except Exception:
            result = _public_attribute_dict(solution)
    else:
        result = _public_attribute_dict(solution)

    ensure_kkt_aliases(result)
    return result


def _public_attribute_dict(obj: Any) -> Dict[str, Any]:
    """Collect public, non-callable attributes from an object."""

    data: Dict[str, Any] = {}
    for attr in dir(obj):
        if attr.startswith("_"):
            continue
        try:
            value = getattr(obj, attr)
        except AttributeError:
            continue
        if callable(value):
            continue
        data[attr] = value
    return data
