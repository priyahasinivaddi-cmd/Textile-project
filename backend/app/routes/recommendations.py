from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import InventoryItem, User
from app.schemas.assessment import RecommendationOut
from app.utils.permissions import get_current_user, require_batch_access

router = APIRouter(prefix="/api/recommendations", tags=["recycling recommendations"])


@router.get("/{batch_id}", response_model=RecommendationOut)
def get_recommendation(batch_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    batch = db.query(InventoryItem).filter(InventoryItem.waste_batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waste batch not found")
    require_batch_access(user, batch)
    assessment = batch.assessment
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found; calculate the assessment first")
    return {
        "batch_id": batch.waste_batch_id, "recommended_action": assessment.recommended_action,
        "recommended_processing_method": assessment.recommended_processing_method,
        "recommendation_reason": assessment.recommendation_reason,
        "estimated_recovery_percentage": assessment.material_recovery_score,
        "estimated_recoverable_quantity_kg": assessment.recoverable_material_kg,
        "estimated_co2_savings_kg": assessment.co2_saved_kg,
        "estimated_water_savings_litres": assessment.water_saved_litres,
        "circularity_score": assessment.circularity_score, "circularity_category": assessment.circularity_category,
    }
