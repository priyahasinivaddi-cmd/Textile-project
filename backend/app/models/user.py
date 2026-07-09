from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="operator")


class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    waste_batch_id = Column(String, unique=True, index=True)
    fabric_type = Column(String)
    source = Column(String)
    quantity = Column(String)
    color = Column(String)
    condition = Column(String)
    collection_date = Column(String)
    status = Column(String, default="Pending")
    uploaded_by = Column(String, default="Manufacturer")
    assigned_to = Column(String, default="Recycling Facility")
