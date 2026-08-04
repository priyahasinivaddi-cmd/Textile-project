"""Shared parsing and normalization helpers for sustainability services."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from app.environmental_factors import DEFAULT_FABRIC, FABRIC_FACTORS


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(float(value), maximum))


def parse_quantity_kg(value: Any) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError("Quantity is required")
    if isinstance(value, (int, float)):
        quantity = float(value)
    else:
        match = re.fullmatch(r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:kg|kgs|kilograms?)?\s*", str(value), re.IGNORECASE)
        if not match:
            raise ValueError("Quantity must be a number in kilograms")
        quantity = float(match.group(1))
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")
    return quantity


def normalize_fabric_name(value: Any) -> str:
    name = re.sub(r"[^a-z]+", " ", str(value or "").lower()).strip()
    if "polyamide" in name:
        return "nylon"
    for fabric in FABRIC_FACTORS:
        if fabric != DEFAULT_FABRIC and fabric in name:
            return fabric
    return name or DEFAULT_FABRIC


def parse_composition(value: Any, fabric_type: Any = None) -> dict[str, float]:
    raw: dict[str, float] = {}
    if isinstance(value, Mapping):
        for key, item in value.items():
            try:
                number = float(item)
            except (TypeError, ValueError):
                continue
            if number > 0:
                name = normalize_fabric_name(re.sub(r"_pct$", "", str(key)))
                raw[name] = raw.get(name, 0.0) + number
    elif isinstance(value, str):
        for percentage, name in re.findall(r"(\d+(?:\.\d+)?)\s*%\s*([A-Za-z]+)", value):
            normalized = normalize_fabric_name(name)
            raw[normalized] = raw.get(normalized, 0.0) + float(percentage)
    if not raw:
        raw[normalize_fabric_name(fabric_type)] = 100.0
    total = sum(raw.values())
    return {key: number / total for key, number in raw.items()} if total > 0 else {DEFAULT_FABRIC: 1.0}


def composition_from_analysis(value: str | None, fabric_type: Any = None) -> dict[str, float]:
    if not value:
        return parse_composition(None, fabric_type)
    try:
        result = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return parse_composition(value, fabric_type)
    material = result.get("material", {}) if isinstance(result, dict) else {}
    prediction = result.get("composition_prediction", {}) if isinstance(result, dict) else {}
    composition = prediction.get("predicted_composition") or material.get("fiber_composition")
    return parse_composition(composition, material.get("fabric_type") or fabric_type)


def weighted_factor(composition: Mapping[str, float], key: str) -> float:
    default = FABRIC_FACTORS[DEFAULT_FABRIC][key]
    return sum(share * FABRIC_FACTORS.get(name, FABRIC_FACTORS[DEFAULT_FABRIC]).get(key, default) for name, share in composition.items())
