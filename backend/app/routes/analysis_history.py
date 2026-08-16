import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import AnalysisRecord
from app.models.user import User
from app.schemas.analysis import AnalysisOut, AnalysisReview
from app.utils.permissions import get_current_user

router = APIRouter(prefix="/api/analyses", tags=["analysis history and review"])


def serialize(record: AnalysisRecord) -> dict:
    return {
        "analysis_id": record.analysis_id,
        "image_url": record.image_url,
        "model_name": record.model_name,
        "model_version": record.model_version,
        "ai_destination": record.ai_destination,
        "ai_confidence": record.ai_confidence,
        "manual_review_required": record.manual_review_required,
        "review_status": record.review_status,
        "final_destination": record.final_destination,
        "reviewer_id": record.reviewer_id,
        "review_reason": record.review_reason,
        "reviewed_at": record.reviewed_at,
        "created_at": record.created_at,
        "result": json.loads(record.result_json),
    }


def query_for(db: Session, user: User):
    query = db.query(AnalysisRecord)
    return query if user.role == "admin" else query.filter(AnalysisRecord.user_id == user.id)


def get_record(db: Session, user: User, analysis_id: str) -> AnalysisRecord:
    record = query_for(db, user).filter(AnalysisRecord.analysis_id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return record


@router.get("", response_model=list[AnalysisOut])
def list_analyses(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    limit = min(max(limit, 1), 100)
    rows = query_for(db, user).order_by(AnalysisRecord.created_at.desc()).offset(max(skip, 0)).limit(limit).all()
    return [serialize(row) for row in rows]


@router.get("/feedback.csv")
def export_feedback(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    rows = db.query(AnalysisRecord).filter(AnalysisRecord.review_status.in_(["accepted", "overridden"])).order_by(AnalysisRecord.created_at).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["analysis_id", "image_url", "ai_destination", "ai_confidence", "human_destination", "review_status", "reviewer_id", "reason", "reviewed_at", "model_version"])
    for row in rows:
        writer.writerow([row.analysis_id, row.image_url, row.ai_destination, row.ai_confidence, row.final_destination, row.review_status, row.reviewer_id, row.review_reason, row.reviewed_at, row.model_version])
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=training-feedback.csv"})


@router.get("/feedback")
def list_feedback(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    rows = db.query(AnalysisRecord).filter(AnalysisRecord.review_status.in_(["accepted", "overridden"])).order_by(AnalysisRecord.reviewed_at.desc()).offset(max(skip, 0)).limit(min(max(limit, 1), 100)).all()
    return [serialize(row) for row in rows]


@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return serialize(get_record(db, user, analysis_id))


@router.post("/{analysis_id}/review", response_model=AnalysisOut)
def review_analysis(analysis_id: str, payload: AnalysisReview, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = get_record(db, user, analysis_id)
    if payload.decision == "override" and not payload.destination:
        raise HTTPException(status_code=422, detail="An override destination is required")
    record.review_status = "accepted" if payload.decision == "accept" else "overridden"
    record.final_destination = record.ai_destination if payload.decision == "accept" else payload.destination
    record.reviewer_id = user.id
    record.review_reason = payload.reason
    record.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return serialize(record)
