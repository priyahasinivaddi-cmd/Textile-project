from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from app.database import Base


class NotificationReceipt(Base):
    __tablename__ = "notification_receipts"
    __table_args__ = (UniqueConstraint("user_id", "notification_key", name="uq_notification_receipt"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_key = Column(String(255), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
