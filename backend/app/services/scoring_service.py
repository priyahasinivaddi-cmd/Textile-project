"""Reusable, side-effect-free waste scoring functions."""

from typing import Mapping

from app.environmental_factors import CONDITION_SCORES, REUSE_SCORES
from app.services.sustainability_common import clamp, weighted_factor


def material_recyclability_score(composition: Mapping[str, float]) -> float:
    return round(clamp(weighted_factor(composition, "recyclability")), 2)


def material_condition_score(condition: str | None) -> float:
    return round(clamp(CONDITION_SCORES.get(str(condition or "").strip().lower(), 50.0)), 2)


def reuse_potential_score(condition: str | None, reuse_potential: str | None = None) -> float:
    if reuse_potential:
        return round(clamp(REUSE_SCORES.get(reuse_potential.strip().lower(), 50.0)), 2)
    return round(clamp(material_condition_score(condition) * 0.95), 2)


def environmental_benefit_score(co2_per_kg: float, water_per_kg: float) -> float:
    return round(clamp(min(co2_per_kg / 4.0, 1.0) * 60.0 + min(water_per_kg / 5000.0, 1.0) * 40.0), 2)


def processing_feasibility_score(composition: Mapping[str, float]) -> float:
    return round(clamp(weighted_factor(composition, "processing_feasibility")), 2)


def material_recovery_score(composition: Mapping[str, float]) -> float:
    return round(clamp(weighted_factor(composition, "recovery_rate") * 100.0), 2)


def sustainability_score(recyclability: float, environmental_benefit: float, recovery: float) -> float:
    return round(clamp(recyclability * 0.35 + environmental_benefit * 0.35 + recovery * 0.30), 2)


def circularity_score(recyclability: float, condition: float, reuse: float, environmental_benefit: float, processing_feasibility: float) -> float:
    value = recyclability * 0.35 + condition * 0.20 + reuse * 0.20 + environmental_benefit * 0.15 + processing_feasibility * 0.10
    return round(clamp(value), 2)


def circularity_category(score: float) -> str:
    bounded = clamp(score)
    if bounded >= 90:
        return "Excellent Recovery Potential"
    if bounded >= 75:
        return "High Recovery Potential"
    if bounded >= 60:
        return "Moderate Recovery Potential"
    if bounded >= 40:
        return "Limited Recovery Potential"
    return "Disposal Recommended"


def calculate_scores(composition: Mapping[str, float], condition: str | None, reuse_potential: str | None, co2_per_kg: float, water_per_kg: float) -> dict[str, float | str]:
    recyclability = material_recyclability_score(composition)
    condition_value = material_condition_score(condition)
    reuse = reuse_potential_score(condition, reuse_potential)
    benefit = environmental_benefit_score(co2_per_kg, water_per_kg)
    feasibility = processing_feasibility_score(composition)
    recovery = material_recovery_score(composition)
    sustainability = sustainability_score(recyclability, benefit, recovery)
    circularity = circularity_score(recyclability, condition_value, reuse, benefit, feasibility)
    return {"recyclability_score": recyclability, "condition_score": condition_value, "reuse_score": reuse, "environmental_benefit_score": benefit, "processing_feasibility_score": feasibility, "material_recovery_score": recovery, "sustainability_score": sustainability, "circularity_score": circularity, "circularity_category": circularity_category(circularity)}
