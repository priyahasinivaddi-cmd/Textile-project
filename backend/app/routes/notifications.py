from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.announcement import PlatformAnnouncement
from app.models.user import InventoryItem, User
from app.services.sustainability_service import aggregate_assessments
from app.utils.permissions import get_current_user, scope_inventory_query

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    message: str = Field(min_length=2, max_length=1000)
    severity: str = "info"
    audience: str = "all"


def _days_until(value):
    try:
        return (datetime.fromisoformat(str(value).replace("Z", "+00:00")).date() - date.today()).days
    except (TypeError, ValueError):
        return None


def _item(identifier, category, title, message, severity="info", action_url=None, created_at=None):
    return {"id": identifier, "category": category, "title": title, "message": message, "severity": severity, "action_url": action_url, "created_at": created_at}


@router.get("")
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    batches = scope_inventory_query(db.query(InventoryItem), user).order_by(InventoryItem.id.desc()).all()
    alerts = []

    if user.role in {"admin", "operator", "manufacturer"}:
        for batch in batches:
            days = _days_until(batch.collection_date)
            if batch.status in {"Pickup Requested", "Accepted"} or (days is not None and 0 <= days <= 3 and batch.status not in {"Recycled", "Disposed"}):
                alerts.append(_item(f"collection-{batch.id}-{batch.status}", "collection", "Waste collection alert", f"{batch.waste_batch_id} ({batch.fabric_type}) is scheduled for collection{f' in {days} day(s)' if days is not None and days >= 0 else ''}. Current status: {batch.status}.", "warning", "/inventory"))

    if user.role in {"admin", "operator"}:
        opportunities = sorted((batch for batch in batches if batch.assessment and batch.assessment.recyclability_score >= 70 and batch.status != "Recycled"), key=lambda batch: batch.assessment.recoverable_material_kg, reverse=True)
        for batch in opportunities[:5]:
            assessment = batch.assessment
            alerts.append(_item(f"opportunity-{batch.id}-{int(assessment.recyclability_score)}", "opportunity", "Recycling opportunity", f"{batch.waste_batch_id} has {assessment.recyclability_score:.0f}% recyclability and {assessment.recoverable_material_kg:.1f} kg recoverable. Recommended: {assessment.recommended_action}.", "success", "/dashboard"))

    if user.role in {"admin", "manager"}:
        assessments = [batch.assessment for batch in batches if batch.assessment]
        summary = aggregate_assessments(assessments)
        milestones = [(summary["waste_diversion_percentage"], 75, "Waste diversion", "%"), (summary["average_circularity_score"], 70, "Average circularity", "/100"), (summary["co2_saved_kg"], 1000, "Carbon reduction", " kg CO₂")]
        for current, target, label, unit in milestones:
            severity = "success" if current >= target else "info"
            alerts.append(_item(f"milestone-{label.lower().replace(' ', '-')}-{int(current)}", "milestone", f"{label} milestone", f"Current performance is {current:.1f}{unit}; target is {target}{unit}. {'Milestone achieved.' if current >= target else 'Continue recovery activity to reach the milestone.'}", severity, "/dashboard"))

    if user.role in {"admin", "operator", "manufacturer"}:
        stale_statuses = {"Pending", "Pickup Requested", "Accepted", "Collected", "Processing"}
        for batch in batches:
            days = _days_until(batch.collection_date)
            if days is not None and days < -7 and batch.status in stale_statuses:
                alerts.append(_item(f"inventory-stale-{batch.id}-{batch.status}", "inventory", "Inventory warning", f"{batch.waste_batch_id} has remained {batch.status.lower()} since {batch.collection_date}. Review or update this batch.", "danger", "/inventory"))
            if not batch.quantity_kg or not batch.assessment:
                reason = "missing a valid quantity" if not batch.quantity_kg else "not yet sustainability-assessed"
                alerts.append(_item(f"inventory-data-{batch.id}-{reason}", "inventory", "Inventory data warning", f"{batch.waste_batch_id} is {reason}.", "warning", "/inventory"))

    announcements = db.query(PlatformAnnouncement).filter(PlatformAnnouncement.active.is_(True), PlatformAnnouncement.audience.in_(["all", user.role])).order_by(PlatformAnnouncement.id.desc()).all()
    for announcement in announcements:
        alerts.append(_item(f"announcement-{announcement.id}", "announcement", announcement.title, announcement.message, announcement.severity, None, announcement.created_at))
    return alerts


@router.post("/announcements", status_code=status.HTTP_201_CREATED)
def create_announcement(payload: AnnouncementCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can publish platform announcements")
    if payload.severity not in {"info", "success", "warning", "danger"} or payload.audience not in {"all", "admin", "manager", "manufacturer", "operator"}:
        raise HTTPException(status_code=422, detail="Invalid announcement severity or audience")
    announcement = PlatformAnnouncement(**payload.model_dump())
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_announcement(announcement_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can manage platform announcements")
    announcement = db.query(PlatformAnnouncement).filter(PlatformAnnouncement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    announcement.active = False
    db.commit()
