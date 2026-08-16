from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
from app.services.user_service import create_user
from app.utils.auth import create_access_token, create_refresh_token, verify_access_token, verify_refresh_token, verify_password
from pydantic import BaseModel
from app.utils.permissions import require_admin

router = APIRouter(prefix="/user", tags=["user"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")


class RefreshRequest(BaseModel):
    refresh_token: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    new_user = create_user(db, user.name, user.email, user.password, user.role, user.organization_id)

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return {"msg": "User registered", "role": new_user.role}


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return db.query(User).order_by(User.id.desc()).all()


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if db_user.id == admin.id:
        raise HTTPException(status_code=400, detail="Administrators cannot delete their own active account")

    db.delete(db_user)
    db.commit()


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.email == form_data.username).first()

    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    claims = {"sub": db_user.email, "uid": db_user.id, "role": db_user.role, "organization_id": db_user.organization_id}
    token = create_access_token(claims)

    return {
        "access_token": token,
        "refresh_token": create_refresh_token(claims),
        "token_type": "bearer",
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role,
    }


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    claims = verify_refresh_token(payload.refresh_token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    db_user = db.query(User).filter(User.id == claims.get("uid"), User.email == claims.get("sub")).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User account is no longer available")
    fresh_claims = {"sub": db_user.email, "uid": db_user.id, "role": db_user.role, "organization_id": db_user.organization_id}
    return {"access_token": create_access_token(fresh_claims), "refresh_token": create_refresh_token(fresh_claims), "token_type": "bearer"}


@router.get("/profile")
def get_profile(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return {
        "message": "Protected route accessed",
        "email": payload.get("sub"),
    }
