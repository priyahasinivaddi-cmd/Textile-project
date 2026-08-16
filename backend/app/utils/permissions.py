"""JWT identity resolution and role-aware waste access helpers."""

from fastapi import Depends, HTTPException, status
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


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user


def can_access_batch(user: User, batch: InventoryItem) -> bool:
    # Waste inventory is a shared operational register. Authentication and a
    # valid platform role are sufficient to see any batch, regardless of who
    # uploaded it. The uploader is retained on each record for accountability.
    return user.role in VALID_ROLES


def require_batch_access(user: User, batch: InventoryItem) -> None:
    if not can_access_batch(user, batch):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this waste batch")


def scope_inventory_query(query: Query, user: User) -> Query:
    return query
