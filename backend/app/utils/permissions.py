"""JWT identity resolution and role-aware waste access helpers."""

from fastapi import Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.database import get_db
from app.models.user import InventoryItem, User
from app.utils.auth import oauth2_scheme, verify_access_token

VALID_ROLES = {"admin", "manufacturer", "manager", "operator"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = verify_access_token(token)
    email = payload.get("sub") if payload else None
    user = db.query(User).filter(User.email == email).first() if email else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    if user.role not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your role is not permitted to use sustainability assessments")
    return user


def can_access_batch(user: User, batch: InventoryItem) -> bool:
    if user.role == "admin":
        return True
    if user.role == "manager":
        if user.organization_id is None:
            return True
        return batch.owner is None or batch.owner.organization_id == user.organization_id
    if user.role == "manufacturer":
        return batch.owner_id == user.id
    if user.role == "operator":
        assigned = str(batch.assigned_to or "").strip().lower()
        uploaded = str(batch.uploaded_by or "").strip().lower()
        return assigned in {"recycling facility", user.name.lower(), user.email.lower()} or uploaded == "recycling facility"
    return False


def require_batch_access(user: User, batch: InventoryItem) -> None:
    if not can_access_batch(user, batch):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this waste batch")


def scope_inventory_query(query: Query, user: User) -> Query:
    if user.role == "admin":
        return query
    if user.role == "manager":
        if user.organization_id is None:
            return query
        return query.filter(
            or_(
                InventoryItem.owner_id.is_(None),
                InventoryItem.owner.has(User.organization_id == user.organization_id),
            )
        )
    if user.role == "manufacturer":
        return query.filter(InventoryItem.owner_id == user.id)
    return query.filter(or_(InventoryItem.assigned_to.in_(["Recycling Facility", user.name, user.email]), InventoryItem.uploaded_by == "Recycling Facility"))
