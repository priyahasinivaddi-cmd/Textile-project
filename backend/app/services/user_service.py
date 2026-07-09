from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.auth import create_access_token, hash_password, verify_password


def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password):
        return None

    return create_access_token({"sub": user.email})


def create_user(db, name, email, password, role="operator"):
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        return None

    new_user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role=role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
