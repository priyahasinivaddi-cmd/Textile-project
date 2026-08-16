from types import SimpleNamespace

import pytest

from app.services.environmental_impact_service import calculate_environmental_impact
from app.services.scoring_service import circularity_category, circularity_score
from app.services.sustainability_common import parse_composition, parse_quantity_kg
from app.services.sustainability_recommendation_service import generate_sustainability_recommendation
from app.services.sustainability_service import aggregate_assessments


def test_circularity_weighted_formula():
    assert circularity_score(80, 70, 60, 50, 40) == 65.5


@pytest.mark.parametrize(("score", "expected"), [
    (100, "Excellent Recovery Potential"), (90, "Excellent Recovery Potential"),
    (89.99, "High Recovery Potential"), (75, "High Recovery Potential"),
    (74.99, "Moderate Recovery Potential"), (50, "Moderate Recovery Potential"),
    (49.99, "Limited Recovery Potential"), (25, "Limited Recovery Potential"),
    (24.99, "Disposal Recommended"), (0, "Disposal Recommended"),
])
def test_category_boundaries(score, expected):
    assert circularity_category(score) == expected


def test_scores_are_clamped():
    assert circularity_score(200, 200, 200, 200, 200) == 100
    assert circularity_score(-20, -20, -20, -20, -20) == 0


@pytest.mark.parametrize("value", [None, "", "unknown", 0, -1, "-5 kg"])
def test_invalid_quantity_is_rejected(value):
    with pytest.raises(ValueError):
        parse_quantity_kg(value)


def test_environmental_calculation_for_cotton():
    result = calculate_environmental_impact("100kg", {"cotton": 1.0}, "Recycled")
    assert result["co2_saved_kg"] == 123
    assert result["water_saved_litres"] == 410000
    assert result["landfill_reduction_kg"] == 82
    assert result["recoverable_material_kg"] == 82


def test_composition_is_normalized():
    assert parse_composition("60% Cotton / 40% Polyester") == {"cotton": 0.6, "polyester": 0.4}


def recommendation(**overrides):
    values = {"condition": "Recyclable", "quantity_kg": 100, "recyclability_score": 85, "reuse_score": 40, "material_recovery_score": 80, "processing_feasibility_score": 80, "circularity_category": "High Recovery Potential", "recoverable_material_kg": 80, "co2_saved_kg": 100, "water_saved_litres": 1000}
    values.update(overrides)
    return generate_sustainability_recommendation(**values)


def test_direct_reuse_rule_has_priority():
    assert recommendation(condition="Reusable", reuse_score=90)["recommended_action"] == "Direct reuse"


def test_mechanical_recycling_rule():
    assert recommendation()["recommended_action"] == "Mechanical recycling"


def test_safe_disposal_rule():
    result = recommendation(recyclability_score=10, material_recovery_score=10, processing_feasibility_score=10, circularity_category="Disposal Recommended")
    assert result["recommended_action"] == "Safe disposal"


def test_analytics_aggregation_handles_empty_data():
    assert aggregate_assessments([])["waste_diversion_percentage"] == 0


def test_analytics_aggregation():
    rows = [
        SimpleNamespace(quantity_kg=100, co2_saved_kg=50, water_saved_litres=500, landfill_reduction_kg=80, recoverable_material_kg=85, circularity_score=80, circularity_category="High Recovery Potential"),
        SimpleNamespace(quantity_kg=50, co2_saved_kg=20, water_saved_litres=200, landfill_reduction_kg=25, recoverable_material_kg=30, circularity_score=60, circularity_category="Moderate Recovery Potential"),
    ]
    summary = aggregate_assessments(rows)
    assert summary["total_waste_kg"] == 150
    assert summary["co2_saved_kg"] == 70
    assert summary["average_circularity_score"] == 70
    assert summary["waste_diversion_percentage"] == 70
