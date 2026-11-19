"""
Authentication & RBAC utilities — Raksha AI Stage 3 Solid
Handles password hashing, JWT token lifecycle, and role-based FastAPI dependencies.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text

from common.config import settings
from common.db import get_db as _get_db

import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_db():
    with _get_db() as db:
        yield db


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify raw password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash raw password with bcrypt."""
    try:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")
    except Exception:
        return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate signed JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db=Depends(get_db),
) -> Optional[dict]:
    """Retrieve current authenticated user if token present; returns None if guest."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            return None
        try:
            row = db.execute(
                text("SELECT id, email, full_name, role, is_active FROM users WHERE id = :id AND is_active = TRUE"),
                {"id": int(user_id)},
            ).fetchone()
            if row:
                return dict(row._mapping)
        except Exception:
            pass

        # Fallback to verified JWT payload claims if DB row is unreachable or offline
        return {
            "id": int(user_id),
            "email": payload.get("email", ""),
            "full_name": payload.get("full_name", payload.get("email", "")),
            "role": payload.get("role", "viewer"),
            "is_active": True,
            "workspace_id": payload.get("workspace_id", 1),
        }
    except Exception:
        return None


def get_current_user(user: Optional[dict] = Depends(get_current_user_optional)) -> dict:
    """Strict authentication dependency — rejects unauthenticated requests."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this resource",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: List[str]):
    """Role-based authorization dependency factory (e.g. ['admin', 'analyst'])."""
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "viewer")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {allowed_roles}, your role is '{user_role}'",
            )
        return current_user
    return role_checker


require_admin = require_role(["admin"])
require_analyst_or_admin = require_role(["admin", "analyst"])
