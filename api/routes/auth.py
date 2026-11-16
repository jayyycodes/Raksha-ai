"""
Authentication, RBAC & Workspaces Router — Raksha AI Stage 3 Solid
Owner: Jay (Lead & Platform) | Milestone: M8
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text

from common.auth import (
    get_db,
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from common.audit import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication & Workspaces"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "analyst"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, db=Depends(get_db)):
    """Authenticate user with email and password, returning JWT access token."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    row = db.execute(
        text("SELECT id, email, password_hash, full_name, role, is_active FROM users WHERE email = :email"),
        {"email": req.email.lower().strip()},
    ).fetchone()

    if not row or not verify_password(req.password, row.password_hash):
        log_audit_event(
            db,
            action="auth.login_failed",
            entity_type="user",
            entity_id=req.email,
            ip_address=client_ip,
            user_agent=user_agent,
            details={"reason": "invalid_credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not row.is_active:
        log_audit_event(
            db,
            action="auth.login_blocked",
            user_id=row.id,
            entity_type="user",
            entity_id=str(row.id),
            ip_address=client_ip,
            user_agent=user_agent,
            details={"reason": "account_inactive"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact platform administrator.",
        )

    # Update last login
    db.execute(
        text("UPDATE users SET last_login_at = NOW() WHERE id = :id"),
        {"id": row.id},
    )
    db.commit()

    token = create_access_token(
        data={"sub": str(row.id), "email": row.email, "role": row.role}
    )

    user_info = {
        "id": row.id,
        "email": row.email,
        "full_name": row.full_name,
        "role": row.role,
    }

    log_audit_event(
        db,
        action="auth.login_success",
        user_id=row.id,
        entity_type="user",
        entity_id=str(row.id),
        ip_address=client_ip,
        user_agent=user_agent,
        details={"role": row.role},
    )

    return {"access_token": token, "token_type": "bearer", "user": user_info}


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, request: Request, db=Depends(get_db)):
    """Register a new user account (defaults to analyst role)."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    existing = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": req.email.lower().strip()},
    ).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    role = req.role if req.role in ("admin", "analyst", "viewer") else "analyst"
    # Prevent self-registering as admin unless no users exist
    user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
    if role == "admin" and user_count > 0:
        role = "analyst"

    pwd_hash = get_password_hash(req.password)
    row = db.execute(
        text("""
            INSERT INTO users (email, password_hash, full_name, role, is_active, created_at, last_login_at)
            VALUES (:email, :pwd, :name, :role, TRUE, NOW(), NOW())
            RETURNING id, email, full_name, role
        """),
        {
            "email": req.email.lower().strip(),
            "pwd": pwd_hash,
            "name": req.full_name.strip(),
            "role": role,
        },
    ).fetchone()
    db.commit()

    token = create_access_token(
        data={"sub": str(row.id), "email": row.email, "role": row.role}
    )

    user_info = {
        "id": row.id,
        "email": row.email,
        "full_name": row.full_name,
        "role": row.role,
    }

    log_audit_event(
        db,
        action="auth.register",
        user_id=row.id,
        entity_type="user",
        entity_id=str(row.id),
        ip_address=client_ip,
        user_agent=user_agent,
        details={"role": row.role},
    )

    return {"access_token": token, "token_type": "bearer", "user": user_info}


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Retrieve details and accessible workspaces of the currently signed-in user."""
    workspaces = db.execute(
        text("""
            SELECT id, name, description, is_shared, owner_id
            FROM workspaces
            WHERE is_shared = TRUE OR owner_id = :uid
            ORDER BY is_shared DESC, name ASC
        """),
        {"uid": current_user["id"]},
    ).fetchall()

    return {
        "user": current_user,
        "workspaces": [dict(w._mapping) for w in workspaces],
    }


@router.get("/workspaces")
def list_workspaces(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """All workspaces accessible to the user (both shared organizational and private)."""
    rows = db.execute(
        text("""
            SELECT w.id, w.name, w.description, w.is_shared, w.owner_id,
                   u.full_name AS owner_name
            FROM workspaces w
            LEFT JOIN users u ON u.id = w.owner_id
            WHERE w.is_shared = TRUE OR w.owner_id = :uid
            ORDER BY w.is_shared DESC, w.name ASC
        """),
        {"uid": current_user["id"]},
    ).fetchall()
    return [dict(r._mapping) for r in rows]
