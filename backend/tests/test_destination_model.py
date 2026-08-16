from app.services.destination_model_service import destination_model_service


def test_destination_model_returns_calibrated_six_class_distribution():
    ai = {"predictions": {"condition": {"label": "4"}, "type": {"label": "shirt"}, "usage": {"top_predictions": [{"label": "Reuse", "probability": 0.6}, {"label": "Recycle", "probability": 0.3}]}}}
    result = destination_model_service.predict(
        {"damage_detected": False, "contamination_detected": False, "fabric_pattern": "plain"},
        {"fabric_type": "Cotton", "blend_type": "single"}, ai,
    )
    assert result["calibrated"] is True
    assert len(result["probabilities"]) == 6
    assert abs(sum(item["probability"] for item in result["probabilities"]) - 1) < 1e-5
    assert result["manual_review_required"] is True
