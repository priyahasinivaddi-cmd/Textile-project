import uuid
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.analysis import AnalysisRecord
from app.models.operations import AnalysisJob
from app.models.user import User
from app.services.analysis_job_service import execute_analysis_job
from app.services.storage_service import storage_provider
from app.utils.permissions import get_current_user

router = APIRouter(prefix="/api/v1/analysis", tags=["asynchronous analysis"])
ALLOWED = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_BYTES = 10 * 1024 * 1024


def serialize(job):
    return {"job_id": job.id, "status": job.status, "stage": job.stage, "progress": job.progress, "analysis_id": job.analysis_id, "image_url": job.image_url, "error": job.error_message, "created_at": job.created_at, "started_at": job.started_at, "completed_at": job.completed_at}


@router.post("/jobs", status_code=202)
async def create_job(background_tasks: BackgroundTasks, image: UploadFile = File(...), sensitivity: float = Form(0.5, ge=0, le=1), label_text: str | None = Form(None), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if image.content_type not in ALLOWED:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG and WebP garment images are supported")
    payload = await image.read(MAX_BYTES + 1)
    if not payload or len(payload) > MAX_BYTES:
        raise HTTPException(status_code=413 if payload else 400, detail="Image is empty or exceeds the 10 MB limit")
    try:
        with Image.open(BytesIO(payload)) as decoded:
            decoded.verify()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Please upload a valid, non-corrupted garment image") from exc
    job_id = str(uuid.uuid4())
    filename = f"{job_id}{ALLOWED[image.content_type]}"
    job_dir = Path("static/jobs")
    job_dir.mkdir(parents=True, exist_ok=True)
    job_path = job_dir / filename
    job_path.write_bytes(payload)
    image_url = storage_provider.save(filename, payload, image.content_type)
    job = AnalysisJob(id=job_id, user_id=user.id, image_key=str(job_path), image_url=image_url, sensitivity=sensitivity, label_text=label_text, status="queued", stage="Uploading", progress=5)
    db.add(job)
    db.commit()
    if settings.task_mode == "celery":
        from app.worker import celery_app
        celery_app.send_task("analysis.execute", args=[job_id])
    else:
        background_tasks.add_task(execute_analysis_job, job_id)
    return serialize(job)


@router.get("/jobs/{job_id}")
def job_status(job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(AnalysisJob).filter(AnalysisJob.id == job_id)
    if user.role != "admin":
        query = query.filter(AnalysisJob.user_id == user.id)
    job = query.first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    response = serialize(job)
    if job.analysis_id:
        record = db.query(AnalysisRecord).filter(AnalysisRecord.analysis_id == job.analysis_id).first()
        if record:
            import json
            response["result"] = json.loads(record.result_json)
    return response


@router.get("/jobs")
def list_jobs(skip: int = 0, limit: int = 25, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(AnalysisJob)
    if user.role != "admin":
        query = query.filter(AnalysisJob.user_id == user.id)
    return [serialize(job) for job in query.order_by(AnalysisJob.created_at.desc()).offset(max(skip, 0)).limit(min(max(limit, 1), 100)).all()]
