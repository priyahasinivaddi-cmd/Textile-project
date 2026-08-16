import os
import uuid
import json
import tempfile
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status

from app.services.image_analysis import analyze_image_file
from app.schemas.pipeline import PipelineResponse
from app.models.user import User
from app.models.analysis import AnalysisRecord
from app.database import get_db
from app.utils.permissions import get_current_user
from sqlalchemy.orm import Session
from app.services.storage_service import storage_provider

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

UPLOAD_DIR = os.path.join("static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
ALLOWED_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@router.post("/analyze", response_model=PipelineResponse)
async def analyze_pipeline(
    image: UploadFile = File(..., description="Textile image to analyse (PNG/JPG/JPEG)."),
    sensitivity: Optional[float] = Form(
        0.5,
        ge=0.0,
        le=1.0,
        description="Defect detection sensitivity (0 = lenient, 1 = strict).",
    ),
    label_text: Optional[str] = Form(
        None,
        description="Optional care-label text, for example: 80% Cotton, 20% Polyester.",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Textile Waste Intelligence Pipeline**

    Upload a textile image and receive a structured analysis containing:

    - Extracted visual features (colour, texture, pattern, damage, contamination)
    - Material classification (fabric type, fiber composition, quality)
    - Waste category & disposal recommendation
    - Ranked circular-economy recycling suggestions

    The pipeline runs five internal stages:
    1. Image Upload & Validation
    2. Pixel-level Feature Extraction
    3. Material Classification
    4. Waste Classification
    5. Recycling Recommendation Generation
    """
    # --- Validate content type -------------------------------------------
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WebP images are supported.",
        )

    payload = await image.read(MAX_UPLOAD_BYTES + 1)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Image exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    file_ext = ALLOWED_CONTENT_TYPES[image.content_type]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temporary:
            temporary.write(payload)
            temp_path = temporary.name
        image_url = storage_provider.save(unique_filename, payload, image.content_type)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store the uploaded image.",
        )

    # --- Run the analysis pipeline -----------------------------------------
    try:
        result = analyze_image_file(temp_path, sensitivity=sensitivity, label_text=label_text)
    except ValueError as exc:
        storage_provider.delete(image_url)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        storage_provider.delete(image_url)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis is temporarily unavailable. The failure was recorded; please try again.",
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    result["image_url"] = image_url
    ai = result.get("ai_predictions") or {}
    usage = (ai.get("predictions") or {}).get("usage") or {}
    destination = result.get("destination_intelligence") or {}
    analysis_id = f"AN-{uuid.uuid4().hex[:16].upper()}"
    record = AnalysisRecord(
        analysis_id=analysis_id,
        user_id=user.id,
        image_url=result["image_url"],
        model_name="EfficientNet-B0 + calibrated XGBoost" if destination else ai.get("model", "Deterministic fallback"),
        model_version=destination.get("model_version") or ai.get("model_version", "unversioned"),
        ai_destination=destination.get("destination") or usage.get("label") or result["waste_classification"].get("category"),
        ai_confidence=destination.get("confidence", usage.get("confidence")),
        manual_review_required=bool(destination.get("manual_review_required", ai.get("manual_review_required", True))),
        result_json=json.dumps(result),
        review_status="pending",
    )
    db.add(record)
    db.commit()
    result["analysis_id"] = analysis_id
    result["review_status"] = "pending"
    return result
