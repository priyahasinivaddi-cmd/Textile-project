import os
import uuid
import shutil
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status

from app.services.image_analysis import analyze_image_file
from app.schemas.pipeline import PipelineResponse

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

UPLOAD_DIR = os.path.join("static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/analyze", response_model=PipelineResponse)
async def analyze_pipeline(
    image: UploadFile = File(..., description="Textile image to analyse (PNG/JPG/JPEG)."),
    sensitivity: Optional[float] = Form(
        0.5,
        ge=0.0,
        le=1.0,
        description="Defect detection sensitivity (0 = lenient, 1 = strict).",
    ),
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
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image (PNG, JPG, JPEG, etc.).",
        )

    # --- Persist to disk ---------------------------------------------------
    file_ext = os.path.splitext(image.filename or "")[1] or ".jpg"
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buf:
            shutil.copyfileobj(image.file, buf)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded image: {exc}",
        )

    # --- Run the analysis pipeline -----------------------------------------
    try:
        result = analyze_image_file(file_path, sensitivity=sensitivity)
    except Exception as exc:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {exc}",
        )

    result["image_url"] = f"/static/uploads/{unique_filename}"
    return result
