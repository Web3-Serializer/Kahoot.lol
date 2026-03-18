import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db, User

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-secret")
ALGORITHM = "HS256"


def create_jwt(user_id: str, is_admin: bool = False):
    payload = {
        "sub": user_id,
        "admin": is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(401, "invalid token")


def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "invalid auth header")
    payload = decode_jwt(authorization[7:])
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(401, "user not found")
    return user


def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "admin required")
    return user
