from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import InventoryItem
from app.schemas.user import InventoryCreate, InventoryOut, InventoryUpdate
from app.services.pdf_report import build_waste_report
from app.services.sustainability_common import parse_quantity_kg

router = APIRouter(prefix="/inventory", tags=["inventory"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_batch_id():
    return f"WB{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


@router.get("", response_model=list[InventoryOut])
def list_inventory(db: Session = Depends(get_db)):
    return db.query(InventoryItem).order_by(InventoryItem.id.desc()).all()


@router.get("/report/pdf")
def download_waste_report(db: Session = Depends(get_db)):
    items = db.query(InventoryItem).order_by(InventoryItem.id.desc()).all()
    pdf = build_waste_report(items)
    filename = f"textile-waste-report-{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{item_id}/report/pdf")
def download_waste_item_report(item_id: int, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste batch not found",
        )

    pdf = build_waste_report([item])
    safe_batch_id = "".join(
        character
        for character in (item.waste_batch_id or f"waste-{item.id}")
        if character.isalnum() or character in ("-", "_")
    )
    filename = f"{safe_batch_id or f'waste-{item.id}'}-report.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
def create_inventory_item(item: InventoryCreate, db: Session = Depends(get_db)):
    batch_id = item.waste_batch_id or generate_batch_id()
    existing_item = (
        db.query(InventoryItem)
        .filter(InventoryItem.waste_batch_id == batch_id)
        .first()
    )

    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Waste Batch ID already exists",
        )

    item_data = item.model_dump()
    try:
        item_data["quantity_kg"] = parse_quantity_kg(item.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    item_data["waste_batch_id"] = batch_id
    new_item = InventoryItem(**item_data)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


@router.put("/{item_id}", response_model=InventoryOut)
def update_inventory_item(
    item_id: int,
    item: InventoryUpdate,
    db: Session = Depends(get_db),
):
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste batch not found",
        )

    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    if item.quantity is not None:
        try:
            db_item.quantity_kg = parse_quantity_kg(item.quantity)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste batch not found",
        )

    db.delete(db_item)
    db.commit()
