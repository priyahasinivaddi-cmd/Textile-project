from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.assessment import WasteAssessment
from app.models.user import InventoryItem, User
from app.schemas.assessment import AssessmentOut, BulkAssessmentOut
from app.services.assessment_service import assessment_to_dict, calculate_and_save_assessment
from app.utils.permissions import get_current_user, require_batch_access, scope_inventory_query

router = APIRouter(prefix="/api/assessments", tags=["sustainability assessments"])


def _calculate_in_background(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        batches = scope_inventory_query(db.query(InventoryItem), user).all()
        for batch in batches:
            try:
                calculate_and_save_assessment(db, batch)
            except (ValueError, SQLAlchemyError):
                db.rollback()
    finally:
        db.close()


@router.post("/bulk/calculate", response_model=BulkAssessmentOut, status_code=status.HTTP_202_ACCEPTED)
def bulk_calculate(background_tasks: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = scope_inventory_query(db.query(InventoryItem), user).count()
    background_tasks.add_task(_calculate_in_background, user.id)
    return {"queued": count, "message": "Sustainability assessments are being calculated in the background"}


def _get_batch_or_404(db: Session, batch_id: str) -> InventoryItem:
    batch = db.query(InventoryItem).filter(InventoryItem.waste_batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waste batch not found")
    return batch


@router.post("/{batch_id}/calculate", response_model=AssessmentOut)
def calculate_assessment(batch_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    batch = _get_batch_or_404(db, batch_id)
    require_batch_access(user, batch)
    try:
        return assessment_to_dict(calculate_and_save_assessment(db, batch))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="The assessment could not be saved") from exc


@router.get("/{batch_id}", response_model=AssessmentOut)
def get_assessment(batch_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    batch = _get_batch_or_404(db, batch_id)
    require_batch_access(user, batch)
    if not batch.assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return assessment_to_dict(batch.assessment)


@router.get("", response_model=list[AssessmentOut])
def list_assessments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    batches = scope_inventory_query(db.query(InventoryItem), user).filter(InventoryItem.assessment.has()).order_by(InventoryItem.id.desc()).all()
    return [assessment_to_dict(batch.assessment) for batch in batches]
