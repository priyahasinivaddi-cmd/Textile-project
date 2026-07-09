import os
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-development")
ALGORITHM = "HS256"


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
