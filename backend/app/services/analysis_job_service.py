"""Persistent background analysis execution shared by local and Celery workers."""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.database import SessionLocal
from app.models.user import User as _User  # register users table before resolving worker foreign keys
from app.models.assessment import WasteAssessment as _WasteAssessment  # register InventoryItem relationship target
from app.models.analysis import AnalysisRecord
from app.models.operations import AnalysisJob, NotificationEvent
from app.services.image_analysis import analyze_image_file
from app.services.storage_service import storage_provider

logger = logging.getLogger(__name__)


def _update(db, job, stage, progress):
    job.stage, job.progress = stage, progress
    db.commit()


def execute_analysis_job(job_id: str) -> None:
    db = SessionLocal()
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        db.close()
        return
    image_key = job.image_key
    user_id = job.user_id
    started = time.perf_counter()
    try:
        job.status, job.started_at = "running", datetime.now(timezone.utc)
        _update(db, job, "Preprocessing", 15)
        path = Path(job.image_key)
        _update(db, job, "Analyzing garment", 35)
        result = analyze_image_file(str(path), sensitivity=job.sensitivity, label_text=job.label_text)
        _update(db, job, "Predicting destination", 70)
        result["image_url"] = job.image_url
        ai = result.get("ai_predictions") or {}
        destination = result.get("destination_intelligence") or {}
        usage = (ai.get("predictions") or {}).get("usage") or {}
        analysis_id = f"AN-{uuid.uuid4().hex[:16].upper()}"
        result["analysis_id"] = analysis_id
        result["review_status"] = "pending"
        record = AnalysisRecord(
            analysis_id=analysis_id, user_id=job.user_id, image_url=job.image_url,
            model_name="EfficientNet-B0 + calibrated XGBoost" if destination else ai.get("model", "Deterministic fallback"),
            model_version=destination.get("model_version") or ai.get("model_version", "unversioned"),
            ai_destination=destination.get("destination") or usage.get("label") or result["waste_classification"].get("category"),
            ai_confidence=destination.get("confidence", usage.get("confidence")),
            manual_review_required=bool(destination.get("manual_review_required", ai.get("manual_review_required", True))),
            result_json=json.dumps(result), review_status="pending",
        )
        db.add(record)
        _update(db, job, "Calculating sustainability", 90)
        job.analysis_id, job.status, job.stage, job.progress = analysis_id, "complete", "Complete", 100
        job.completed_at = datetime.now(timezone.utc)
        if record.manual_review_required:
            db.add(NotificationEvent(user_id=job.user_id, category="low-confidence", title="Manual review required", message=f"Analysis {analysis_id} requires confirmation before operational use.", severity="warning", action_url=f"/analyze?analysis={analysis_id}"))
        db.commit()
        logger.info(json.dumps({"event": "analysis_complete", "job_id": job.id, "analysis_id": analysis_id, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "model_version": record.model_version}))
    except Exception:
        logger.exception("Analysis job %s failed", job_id)
        db.rollback()
        failed_job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if failed_job:
            failed_job.status, failed_job.stage, failed_job.error_message = "failed", "Failed", "Unable to analyze image. Please upload a valid garment image or try again."
            failed_job.completed_at = datetime.now(timezone.utc)
            db.add(NotificationEvent(user_id=user_id, category="failed-analysis", title="Analysis failed", message=f"Job {job_id} could not be completed. Please try again.", severity="danger", action_url="/analyze"))
            db.commit()
    finally:
        try:
            Path(image_key).unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove temporary job input %s", image_key)
        db.close()
