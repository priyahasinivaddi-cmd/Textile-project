from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    users = relationship("User", back_populates="organization")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="operator")
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    organization = relationship("Organization", back_populates="users")
    waste_batches = relationship("InventoryItem", back_populates="owner")


class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    waste_batch_id = Column(String, unique=True, index=True)
    fabric_type = Column(String)
    source = Column(String)
    quantity = Column(String)
    quantity_kg = Column(Float, nullable=True)
    color = Column(String)
    condition = Column(String)
    collection_date = Column(String)
    status = Column(String, default="Pending")
    uploaded_by = Column(String, default="Manufacturer")
    assigned_to = Column(String, default="Recycling Facility")
    image_url = Column(String, nullable=True)
    analysis_results = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    owner = relationship("User", back_populates="waste_batches")
    assessment = relationship("WasteAssessment", back_populates="waste_batch", uselist=False, cascade="all, delete-orphan")

