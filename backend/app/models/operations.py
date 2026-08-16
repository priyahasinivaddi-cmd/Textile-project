from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


def now():
    return datetime.now(timezone.utc)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="queued", index=True)
    stage = Column(String(80), nullable=False, default="Uploading")
    progress = Column(Integer, nullable=False, default=0)
    image_key = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    sensitivity = Column(Float, nullable=False, default=0.5)
    label_text = Column(Text, nullable=True)
    analysis_id = Column(String, nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class NotificationEvent(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    category = Column(String(50), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="info")
    action_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(String(100), nullable=True)
    details_json = Column(Text, nullable=False, default="{}")
    request_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now, index=True)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True)
    model_key = Column(String(100), nullable=False, index=True)
    version = Column(String(120), nullable=False)
    architecture = Column(String(120), nullable=False)
    dataset = Column(String(255), nullable=False)
    metrics_json = Column(Text, nullable=False, default="{}")
    artifact_path = Column(String, nullable=False)
    stage = Column(String(30), nullable=False, default="candidate", index=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now, index=True)
