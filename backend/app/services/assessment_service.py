"""Orchestrate and persist idempotent waste sustainability assessments."""

import json

from sqlalchemy.orm import Session

from app.models.assessment import WasteAssessment, utc_now
from app.models.user import InventoryItem
from app.services.environmental_impact_service import calculate_environmental_impact
from app.services.scoring_service import calculate_scores
from app.services.sustainability_common import composition_from_analysis
from app.services.sustainability_recommendation_service import generate_sustainability_recommendation


def _reuse_potential(analysis_results: str | None) -> str | None:
    if not analysis_results:
        return None
    try:
        value = json.loads(analysis_results)
        return value.get("waste_classification", {}).get("reuse_potential")
    except (TypeError, ValueError, json.JSONDecodeError, AttributeError):
        return None


def calculate_and_save_assessment(db: Session, batch: InventoryItem) -> WasteAssessment:
    composition = composition_from_analysis(batch.analysis_results, batch.fabric_type)
    impact = calculate_environmental_impact(batch.quantity, composition, batch.status)
    scores = calculate_scores(composition, batch.condition, _reuse_potential(batch.analysis_results), impact["co2_rate"], impact["water_rate"])
    recommendation = generate_sustainability_recommendation(
        condition=batch.condition, quantity_kg=impact["quantity_kg"],
        recyclability_score=scores["recyclability_score"], reuse_score=scores["reuse_score"],
        material_recovery_score=scores["material_recovery_score"],
        processing_feasibility_score=scores["processing_feasibility_score"],
        circularity_category=scores["circularity_category"],
        recoverable_material_kg=impact["recoverable_material_kg"], co2_saved_kg=impact["co2_saved_kg"],
        water_saved_litres=impact["water_saved_litres"],
    )
    assessment = db.query(WasteAssessment).filter(WasteAssessment.waste_batch_id == batch.id).first()
    if assessment is None:
        assessment = WasteAssessment(waste_batch_id=batch.id)
        db.add(assessment)
    try:
        history = json.loads(assessment.audit_log or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        history = []
    history.append({"calculated_at": utc_now().isoformat(), "circularity_score": scores["circularity_score"], "category": scores["circularity_category"]})
    values = {
        "quantity_kg": impact["quantity_kg"], **scores,
        "co2_saved_kg": impact["co2_saved_kg"], "water_saved_litres": impact["water_saved_litres"],
        "landfill_reduction_kg": impact["landfill_reduction_kg"], "recoverable_material_kg": impact["recoverable_material_kg"],
        "recommended_action": recommendation["recommended_action"],
        "recommended_processing_method": recommendation["recommended_processing_method"],
        "recommendation_reason": recommendation["recommendation_reason"], "updated_at": utc_now(),
        "audit_log": json.dumps(history[-25:]),
    }
    for key, value in values.items():
        setattr(assessment, key, value)
    db.commit()
    db.refresh(assessment)
    return assessment


def assessment_to_dict(assessment: WasteAssessment) -> dict:
    try:
        audit_history = json.loads(assessment.audit_log or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        audit_history = []
    return {
        "id": assessment.id, "batch_id": assessment.waste_batch.waste_batch_id,
        "quantity_kg": assessment.quantity_kg, "recyclability_score": assessment.recyclability_score,
        "condition_score": assessment.condition_score, "reuse_score": assessment.reuse_score,
        "environmental_benefit_score": assessment.environmental_benefit_score,
        "processing_feasibility_score": assessment.processing_feasibility_score,
        "material_recovery_score": assessment.material_recovery_score, "sustainability_score": assessment.sustainability_score,
        "circularity_score": assessment.circularity_score, "circularity_category": assessment.circularity_category,
        "co2_saved_kg": assessment.co2_saved_kg, "water_saved_litres": assessment.water_saved_litres,
        "landfill_reduction_kg": assessment.landfill_reduction_kg, "recoverable_material_kg": assessment.recoverable_material_kg,
        "recommended_action": assessment.recommended_action, "recommended_processing_method": assessment.recommended_processing_method,
        "recommendation_reason": assessment.recommendation_reason, "audit_history": audit_history,
        "created_at": assessment.created_at, "updated_at": assessment.updated_at,
    }
