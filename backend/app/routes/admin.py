"""Live platform monitoring and usage analytics for administrators."""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import WasteAssessment
from app.models.user import InventoryItem, User
from app.utils.permissions import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])
STARTED_AT = time.time()


@router.get("/system-status")
def system_status(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    database_status = "online"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "offline"
    total_batches = db.query(InventoryItem).count() if database_status == "online" else 0
    assessed_batches = db.query(WasteAssessment).count() if database_status == "online" else 0
    return {
        "api_status": "online",
        "database_status": database_status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - STARTED_AT),
        "total_users": db.query(User).count() if database_status == "online" else 0,
        "total_batches": total_batches,
        "assessed_batches": assessed_batches,
        "assessment_coverage_percentage": round(assessed_batches / total_batches * 100, 1) if total_batches else 0,
    }
