"""HTTP endpoints for the production fabric model."""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.services.model_service import model_service
from app.services.multitask_model_service import multitask_model_service
from app.services.destination_model_service import destination_model_service
from app.models.user import User
from app.utils.permissions import get_current_user


router = APIRouter(prefix="/api/model", tags=["Textile composition model"])
logger = logging.getLogger(__name__)
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.get("/status")
def model_status() -> dict:
    """Report artifact loading and output-label compatibility."""
    return model_service.status()


@router.get("/multitask/status")
def multitask_status() -> dict:
    return multitask_model_service.status()


@router.get("/destination/status")
def destination_status(_user: User = Depends(get_current_user)) -> dict:
    return destination_model_service.status()


@router.post("/predict-multitask")
async def predict_multitask(file: UploadFile = File(...), _user: User = Depends(get_current_user)) -> dict:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only PNG, JPG, and JPEG images are supported")
    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller")
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty")
    try:
        return multitask_model_service.predict(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Multitask model unavailable") from exc


@router.post("/predict-composition")
async def predict_composition(file: UploadFile = File(...), _user: User = Depends(get_current_user)) -> dict:
    logger.info("Fabric prediction upload received: filename=%s", file.filename or "unnamed")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PNG, JPG, and JPEG images are supported",
        )

    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be 10 MB or smaller",
        )
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty")

    try:
        prediction = model_service.predict(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Composition prediction request failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Fabric prediction is temporarily unavailable",
        ) from exc

    return {
        "success": True,
        "filename": file.filename or "uploaded-image",
        **prediction,
    }
