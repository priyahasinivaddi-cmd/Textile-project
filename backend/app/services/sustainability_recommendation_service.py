"""Replaceable rule-based sustainability recommendation engine."""


def generate_sustainability_recommendation(*, condition: str | None, quantity_kg: float, recyclability_score: float, reuse_score: float, material_recovery_score: float, processing_feasibility_score: float, circularity_category: str, recoverable_material_kg: float, co2_saved_kg: float, water_saved_litres: float) -> dict:
    condition_key = str(condition or "").lower()
    if reuse_score >= 80 and condition_key in {"reusable", "excellent", "good"}:
        action, method, reason = "Direct reuse", "Cleaning and redistribution", "Strong condition and reuse scores favor retaining the textile in its current form."
    elif reuse_score >= 55 and condition_key in {"repairable", "damaged", "fair"}:
        action, method, reason = "Repair and reuse", "Inspection, repair and redistribution", "Repair is feasible and avoids premature fibre processing."
    elif recyclability_score >= 80 and processing_feasibility_score >= 70:
        action, method, reason = "Mechanical recycling", "Sorting, shredding and fibre recovery", "High recyclability and processing feasibility support mechanical fibre recovery."
    elif recyclability_score >= 65 and material_recovery_score >= 60:
        action, method, reason = "Chemical recycling", "Material separation and chemical recycling", "Useful recovery potential remains, but material separation may be required."
    elif material_recovery_score >= 55:
        action, method, reason = "Fibre recovery", "Fibre opening and secondary-product processing", "A meaningful material share can be recovered despite limited reuse value."
    elif processing_feasibility_score >= 40:
        action, method, reason = "Downcycling", "Convert to insulation, filling or composite material", "Lower-grade processing remains feasible for a secondary application."
    elif circularity_category != "Disposal Recommended":
        action, method, reason = "Energy recovery", "Certified waste-to-energy processing", "Controlled energy recovery may avoid direct landfill when recycling is constrained."
    else:
        action, method, reason = "Safe disposal", "Licensed disposal following local regulations", "Recovery and processing scores are too low for a reliable recycling route."
    return {
        "recommended_action": action, "recommended_processing_method": method, "recommendation_reason": reason,
        "estimated_recovery_percentage": round(material_recovery_score, 2),
        "estimated_recoverable_quantity_kg": round(recoverable_material_kg, 2),
        "estimated_co2_savings_kg": round(co2_saved_kg, 2),
        "estimated_water_savings_litres": round(water_saved_litres, 2),
        "circularity_category": circularity_category, "quantity_kg": round(quantity_kg, 2),
    }
