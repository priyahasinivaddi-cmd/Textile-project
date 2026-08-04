"""Environmental impact estimates for individual textile waste batches."""

from typing import Any, Mapping

from app.environmental_factors import STATUS_DIVERSION_FACTORS
from app.services.sustainability_common import parse_quantity_kg, weighted_factor


def calculate_environmental_impact(quantity: Any, composition: Mapping[str, float], status: str | None = None) -> dict[str, float]:
    quantity_kg = parse_quantity_kg(quantity)
    co2_rate = weighted_factor(composition, "co2_kg_per_kg")
    water_rate = weighted_factor(composition, "water_l_per_kg")
    recovery_rate = max(0.0, min(weighted_factor(composition, "recovery_rate"), 1.0))
    diversion_factor = STATUS_DIVERSION_FACTORS.get(str(status or "pending").strip().lower(), recovery_rate)
    return {
        "quantity_kg": round(quantity_kg, 2),
        "co2_saved_kg": round(quantity_kg * co2_rate * recovery_rate, 2),
        "water_saved_litres": round(quantity_kg * water_rate * recovery_rate, 2),
        "landfill_reduction_kg": round(quantity_kg * min(recovery_rate, diversion_factor), 2),
        "recoverable_material_kg": round(quantity_kg * recovery_rate, 2),
        "recovery_percentage": round(recovery_rate * 100.0, 2),
        "co2_rate": co2_rate,
        "water_rate": water_rate,
    }
