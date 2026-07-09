from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "operator"


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str = "operator"

    class Config:
        from_attributes = True


class InventoryCreate(BaseModel):
    waste_batch_id: Optional[str] = None
    fabric_type: str
    source: str
    quantity: str
    color: str
    condition: str
    collection_date: str
    status: str = "Pending"
    uploaded_by: str = "Manufacturer"
    assigned_to: str = "Recycling Facility"


class InventoryUpdate(BaseModel):
    fabric_type: Optional[str] = None
    source: Optional[str] = None
    quantity: Optional[str] = None
    color: Optional[str] = None
    condition: Optional[str] = None
    collection_date: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None


class InventoryOut(BaseModel):
    id: int
    waste_batch_id: str
    fabric_type: str
    source: str
    quantity: str
    color: str
    condition: str
    collection_date: str
    status: str
    uploaded_by: str
    assigned_to: str

    class Config:
        from_attributes = True
