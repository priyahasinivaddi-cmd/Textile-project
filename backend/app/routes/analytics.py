from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import InventoryItem, User
from app.schemas.assessment import MonthlyTrendOut, SustainabilitySummaryOut
from app.services.sustainability_service import aggregate_assessments, monthly_trends
from app.utils.permissions import get_current_user, scope_inventory_query

router = APIRouter(prefix="/api/analytics", tags=["sustainability analytics"])


def _assessments(db: Session, user: User, year: int | None = None, month: int | None = None):
    batches = scope_inventory_query(db.query(InventoryItem), user).filter(InventoryItem.assessment.has()).all()
    rows = []
    for batch in batches:
        if year is not None or month is not None:
            try:
                parsed = datetime.fromisoformat(str(batch.collection_date).replace("Z", "+00:00"))
            except (TypeError, ValueError):
                parsed = batch.assessment.created_at
            if year is not None and parsed.year != year:
                continue
            if month is not None and parsed.month != month:
                continue
        rows.append(batch.assessment)
    return rows


def _summary(db: Session, user: User, year: int | None, month: int | None):
    return aggregate_assessments(_assessments(db, user, year, month))


@router.get("/sustainability-summary", response_model=SustainabilitySummaryOut)
def sustainability_summary(year: int | None = Query(None, ge=2000, le=2100), month: int | None = Query(None, ge=1, le=12), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _summary(db, user, year, month)


@router.get("/environmental-impact", response_model=SustainabilitySummaryOut)
def environmental_impact(year: int | None = Query(None, ge=2000, le=2100), month: int | None = Query(None, ge=1, le=12), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _summary(db, user, year, month)


@router.get("/waste-diversion", response_model=SustainabilitySummaryOut)
def waste_diversion(year: int | None = Query(None, ge=2000, le=2100), month: int | None = Query(None, ge=1, le=12), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _summary(db, user, year, month)


@router.get("/circularity", response_model=SustainabilitySummaryOut)
def circularity(year: int | None = Query(None, ge=2000, le=2100), month: int | None = Query(None, ge=1, le=12), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _summary(db, user, year, month)


@router.get("/monthly-trends", response_model=list[MonthlyTrendOut])
def get_monthly_trends(year: int | None = Query(None, ge=2000, le=2100), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return monthly_trends(_assessments(db, user, year, None))

