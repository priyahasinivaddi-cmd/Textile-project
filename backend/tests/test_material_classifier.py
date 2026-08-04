"""Tests for composition-aware material classification."""

from app.services import material_classifier


def sample_features():
    return {
        "color_name": "Blue", "is_rough": True, "is_printed": False,
        "color_variance": 10.0, "damage_detected": False,
        "contamination_detected": False, "std_dev": 30.0,
        "damage_score": 0.0, "contamination_score": 0.0,
        "red": 20, "green": 40, "blue": 120,
    }


def test_composition_model_overrides_colour_rule(monkeypatch):
    monkeypatch.setattr(material_classifier, "FABRIC_CLASSIFIER", None)
    monkeypatch.setattr(material_classifier, "QUALITY_CLASSIFIER", None)
    prediction = {"predicted_composition": {
        "wool": 72.0, "polyamide": 23.0, "other": 5.0,
    }}

    result = material_classifier.classify_material(sample_features(), prediction)

    assert result["fabric_type"] == "Wool"
    assert result["confidence"] == 0.72
    assert result["blend_type"] == "mixed"
    assert result["fiber_composition"] == "72.0% Wool / 23.0% Nylon / 5.0% Other fibres"


def test_small_trace_fibres_do_not_mark_material_as_blend(monkeypatch):
    monkeypatch.setattr(material_classifier, "FABRIC_CLASSIFIER", None)
    monkeypatch.setattr(material_classifier, "QUALITY_CLASSIFIER", None)
    prediction = {"predicted_composition": {
        "cotton": 98.0, "elastane": 2.0,
    }}

    result = material_classifier.classify_material(sample_features(), prediction)

    assert result["fabric_type"] == "Cotton"
    assert result["blend_type"] == "single"
    assert result["fiber_composition"] == "98.0% Cotton / 2.0% Elastane"


def test_low_confidence_image_prediction_remains_uncertain(monkeypatch):
    monkeypatch.setattr(material_classifier, "FABRIC_CLASSIFIER", None)
    monkeypatch.setattr(material_classifier, "QUALITY_CLASSIFIER", None)

    result = material_classifier.classify_material(
        sample_features(),
        {
            "predicted_fabric": "Uncertain",
            "confidence": 10.0,
            "low_confidence": True,
            "top_predictions": [{"fabric": "Cotton", "confidence": 10.0}],
        },
    )

    assert result["fabric_type"] == "Uncertain"
    assert result["confidence"] == 0.1
    assert result["fiber_composition"] == "10.0% Cotton"
