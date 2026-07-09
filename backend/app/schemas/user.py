from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "operator"

class UserLogin(BaseModel):
    email: str
    password: str


class InventoryCreate(BaseModel):
    batch_id: str
    fabric_type: str
    source: str
    quantity: str
    color: str
    condition: str


class InventoryOut(InventoryCreate):
    id: int

    class Config:
        from_attributes = True
