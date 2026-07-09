from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import create_user
from app.utils.auth import create_access_token, verify_access_token, verify_password

router = APIRouter(prefix="/user", tags=["user"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    new_user = create_user(db, user.name, user.email, user.password, user.role)

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return {"msg": "User registered"}


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

    token = create_access_token({"sub": db_user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role,
    }


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
