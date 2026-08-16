from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    ai_destination = Column(String, nullable=True, index=True)
    ai_confidence = Column(Float, nullable=True)
    manual_review_required = Column(Boolean, nullable=False, default=True, index=True)
    result_json = Column(Text, nullable=False)
    review_status = Column(String, nullable=False, default="pending", index=True)
    final_destination = Column(String, nullable=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_reason = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
