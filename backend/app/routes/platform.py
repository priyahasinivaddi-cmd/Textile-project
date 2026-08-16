"""Global search, model registry and production administration APIs."""
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.analysis import AnalysisRecord
from app.models.operations import AnalysisJob, ModelVersion
from app.models.user import InventoryItem, User
from app.services.audit_service import record_audit
from app.utils.permissions import get_current_user, require_admin, scope_inventory_query

router = APIRouter(prefix="/api/v1", tags=["production platform"])
ROOT = Path(__file__).resolve().parents[3]


@router.get("/search")
def global_search(q: str = Query(min_length=2, max_length=100), limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pattern = f"%{q.strip()}%"
    garments = scope_inventory_query(db.query(InventoryItem), user).filter(or_(InventoryItem.waste_batch_id.ilike(pattern), InventoryItem.fabric_type.ilike(pattern), InventoryItem.condition.ilike(pattern), InventoryItem.analysis_results.ilike(pattern))).limit(limit).all()
    analyses = db.query(AnalysisRecord)
    if user.role != "admin": analyses = analyses.filter(AnalysisRecord.user_id == user.id)
    analyses = analyses.filter(or_(AnalysisRecord.analysis_id.ilike(pattern), AnalysisRecord.ai_destination.ilike(pattern), AnalysisRecord.final_destination.ilike(pattern), AnalysisRecord.result_json.ilike(pattern))).limit(limit).all()
    results = [{"kind": "garment", "id": item.waste_batch_id, "title": item.waste_batch_id, "subtitle": f"{item.fabric_type} · {item.condition}", "url": "/inventory"} for item in garments]
    results += [{"kind": "analysis", "id": item.analysis_id, "title": item.analysis_id, "subtitle": f"{item.final_destination or item.ai_destination} · {(item.ai_confidence or 0) * 100:.1f}%", "url": f"/analyze?analysis={item.analysis_id}"} for item in analyses]
    return {"query": q, "results": results[:limit]}


def artifact_models():
    entries = []
    definitions = (("garment-multitask-b0", "EfficientNet-B0 multitask", ROOT / "ml/artifacts/multitask/b0/metadata.json"), ("garment-multitask-b2", "EfficientNet-B2 multitask", ROOT / "ml/artifacts/multitask/b2/metadata.json"), ("destination-xgboost", "Calibrated XGBoost + visual fusion", ROOT / "ml/artifacts/destination/metadata.json"))
    for key, architecture, path in definitions:
        if path.exists():
            metadata = json.loads(path.read_text(encoding="utf-8"))
            entries.append({"model_key": key, "version": metadata.get("trained_at", "unknown"), "architecture": architecture, "dataset": "fnauman/fashion-second-hand-front-only-rgb", "metrics": metadata.get("metrics", {}), "quality_gate_passed": bool(metadata.get("quality_gate_passed", False)), "training_date": metadata.get("trained_at"), "artifact_path": str(path.parent)})
    return entries


@router.get("/models/insights")
def model_insights(_user: User = Depends(get_current_user)):
    return {"models": artifact_models(), "disclaimer": "Development artifacts are not approved for autonomous operational decisions."}


@router.get("/models/registry")
def model_registry(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return [{"id": row.id, "model_key": row.model_key, "version": row.version, "architecture": row.architecture, "dataset": row.dataset, "metrics": json.loads(row.metrics_json), "stage": row.stage, "active": row.active, "approved_by": row.approved_by, "approved_at": row.approved_at, "created_at": row.created_at} for row in db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()]


@router.post("/models/registry/sync")
def sync_registry(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    created = 0
    for item in artifact_models():
        if not db.query(ModelVersion).filter(ModelVersion.model_key == item["model_key"], ModelVersion.version == item["version"]).first():
            metrics = {**item["metrics"], "quality_gate_passed": item["quality_gate_passed"]}
            db.add(ModelVersion(model_key=item["model_key"], version=item["version"], architecture=item["architecture"], dataset=item["dataset"], metrics_json=json.dumps(metrics), artifact_path=item["artifact_path"], stage="candidate")); created += 1
    record_audit(db, user_id=admin.id, action="model_registry_sync", entity_type="model_registry", details={"created": created}); db.commit()
    return {"created": created}


@router.post("/models/registry/{model_id}/promote")
def promote_model(model_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    candidate = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not candidate: raise HTTPException(status_code=404, detail="Model candidate not found")
    if not json.loads(candidate.metrics_json).get("quality_gate_passed"): raise HTTPException(status_code=409, detail="This model failed its quality gate and cannot be promoted")
    db.query(ModelVersion).filter(ModelVersion.model_key == candidate.model_key).update({ModelVersion.active: False, ModelVersion.stage: "archived"})
    candidate.active, candidate.stage, candidate.approved_by, candidate.approved_at = True, "production", admin.id, datetime.now(timezone.utc)
    record_audit(db, user_id=admin.id, action="model_promoted", entity_type="model_version", entity_id=candidate.id, request_id=getattr(request.state, "request_id", None)); db.commit()
    return {"id": candidate.id, "stage": candidate.stage, "active": True}


@router.get("/admin/analytics")
def admin_analytics(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    total = db.query(AnalysisRecord).count(); successful = db.query(AnalysisRecord).filter(AnalysisRecord.result_json.isnot(None)).count(); failed = db.query(AnalysisJob).filter(AnalysisJob.status == "failed").count()
    destination = db.query(AnalysisRecord.ai_destination, func.count(AnalysisRecord.id)).group_by(AnalysisRecord.ai_destination).order_by(func.count(AnalysisRecord.id).desc()).first()
    return {"total_users": db.query(User).count(), "total_analyses": total, "successful_analyses": successful, "failed_analyses": failed, "average_confidence": float(db.query(func.avg(AnalysisRecord.ai_confidence)).scalar() or 0), "most_common_destination": destination[0] if destination else None}
