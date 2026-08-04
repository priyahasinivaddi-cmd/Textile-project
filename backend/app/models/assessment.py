from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WasteAssessment(Base):
    __tablename__ = "waste_assessments"

    id = Column(Integer, primary_key=True, index=True)
    waste_batch_id = Column(Integer, ForeignKey("inventory.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    quantity_kg = Column(Float, nullable=False)
    recyclability_score = Column(Float, nullable=False)
    condition_score = Column(Float, nullable=False)
    reuse_score = Column(Float, nullable=False)
    environmental_benefit_score = Column(Float, nullable=False)
    processing_feasibility_score = Column(Float, nullable=False)
    material_recovery_score = Column(Float, nullable=False)
    sustainability_score = Column(Float, nullable=False)
    circularity_score = Column(Float, nullable=False)
    circularity_category = Column(String, nullable=False, index=True)
    co2_saved_kg = Column(Float, nullable=False)
    water_saved_litres = Column(Float, nullable=False)
    landfill_reduction_kg = Column(Float, nullable=False)
    recoverable_material_kg = Column(Float, nullable=False)
    recommended_action = Column(String, nullable=False)
    recommended_processing_method = Column(String, nullable=False)
    recommendation_reason = Column(Text, nullable=False)
    audit_log = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    waste_batch = relationship("InventoryItem", back_populates="assessment")
