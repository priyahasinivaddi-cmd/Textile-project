from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import InventoryItem
from app.schemas.user import InventoryCreate, InventoryOut

router = APIRouter(prefix="/inventory", tags=["inventory"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[InventoryOut])
def list_inventory(db: Session = Depends(get_db)):
    return db.query(InventoryItem).order_by(InventoryItem.id.desc()).all()


@router.post("", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
def create_inventory_item(item: InventoryCreate, db: Session = Depends(get_db)):
    existing_item = (
        db.query(InventoryItem)
        .filter(InventoryItem.batch_id == item.batch_id)
        .first()
    )

    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch ID already exists",
        )

    new_item = InventoryItem(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item
