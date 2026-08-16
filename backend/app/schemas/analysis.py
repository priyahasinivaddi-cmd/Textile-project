from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalysisReview(BaseModel):
    decision: Literal["accept", "override"]
    destination: str | None = Field(None, min_length=2, max_length=80)
    reason: str = Field(min_length=2, max_length=1000)


class AnalysisOut(BaseModel):
    analysis_id: str
    image_url: str
    model_name: str
    model_version: str
    ai_destination: str | None
    ai_confidence: float | None
    manual_review_required: bool
    review_status: str
    final_destination: str | None
    reviewer_id: int | None
    review_reason: str | None
    reviewed_at: datetime | None
    created_at: datetime
    result: dict[str, Any]
