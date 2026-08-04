"""Aggregate sustainability analytics."""

from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Iterable

from app.environmental_factors import BENCHMARK_DIVERSION_PERCENT


def aggregate_assessments(assessments: Iterable[object]) -> dict:
    rows = list(assessments)
    total_quantity = sum(float(getattr(row, "quantity_kg", 0) or 0) for row in rows)
    landfill = sum(float(getattr(row, "landfill_reduction_kg", 0) or 0) for row in rows)
    categories = Counter(getattr(row, "circularity_category", None) or "Uncategorized" for row in rows)
    average = sum(float(getattr(row, "circularity_score", 0) or 0) for row in rows) / len(rows) if rows else 0.0
    diversion = landfill / total_quantity * 100.0 if total_quantity else 0.0
    return {
        "total_assessments": len(rows), "total_waste_kg": round(total_quantity, 2),
        "co2_saved_kg": round(sum(float(getattr(row, "co2_saved_kg", 0) or 0) for row in rows), 2),
        "water_saved_litres": round(sum(float(getattr(row, "water_saved_litres", 0) or 0) for row in rows), 2),
        "landfill_reduction_kg": round(landfill, 2),
        "recoverable_material_kg": round(sum(float(getattr(row, "recoverable_material_kg", 0) or 0) for row in rows), 2),
        "waste_diversion_percentage": round(diversion, 2), "average_circularity_score": round(average, 2),
        "benchmark_diversion_percentage": BENCHMARK_DIVERSION_PERCENT,
        "benchmark_status": "meeting" if diversion >= BENCHMARK_DIVERSION_PERCENT else "below",
        "category_distribution": dict(categories),
    }


def monthly_trends(assessments: Iterable[object]) -> list[dict]:
    groups: dict[str, list[object]] = defaultdict(list)
    for row in assessments:
        batch = getattr(row, "waste_batch", None)
        raw_date = getattr(batch, "collection_date", None) or getattr(row, "created_at", None)
        try:
            parsed = raw_date if isinstance(raw_date, (date, datetime)) else datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
            key = parsed.strftime("%Y-%m")
        except (TypeError, ValueError):
            key = "Unknown"
        groups[key].append(row)
    return [{"month": key, **aggregate_assessments(groups[key])} for key in sorted(groups)]
