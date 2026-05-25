from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_token,
    current_user,
    get_db,
    hash_password,
    refresh_token_hash,
    verify_password,
)
from app.models.db import AuthSession, Issuer, Learner, User, UserRoleEnum

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    wallet_address: str = Field(min_length=10, max_length=42)
    full_name: str = Field(min_length=2)
    programme: str = "General"
    role: UserRoleEnum = UserRoleEnum.LEARNER


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)


def issue_tokens(user: User, db: Session) -> dict:
    settings = get_settings()
    access = create_token({"sub": user.id, "role": user.role.value}, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh = secrets.token_urlsafe(48)
    db.add(AuthSession(
        user_id=user.id,
        refresh_token_hash=refresh_token_hash(refresh),
        # SQLite returns naive datetimes even when aware values are inserted.
        # Store UTC-naive values for DB comparisons and keep JWT times timezone-aware.
        expires_at=datetime.utcnow() + timedelta(days=30),
    ))
    db.commit()
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "wallet_address": user.wallet_address,
        "role": user.role.value,
        "learner_id": user.learner_id,
        "issuer_id": user.issuer_id,
    }


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.email == req.email.lower()) | (User.wallet_address == req.wallet_address)
    ).first()
    if existing:
        raise HTTPException(409, "Account already exists")

    learner = None
    issuer= None
    if req.role == UserRoleEnum.LEARNER:
        did = f"did:ethr:arbitrum:{req.wallet_address}"
        learner = Learner(
            did=did,
            hashed_name=hashlib.sha256(req.full_name.encode()).hexdigest(),
            hashed_email=hashlib.sha256(req.email.lower().encode()).hexdigest(),
            wallet_address=req.wallet_address,
            programme=req.programme,
        )
        db.add(learner)
        db.flush()
    elif req.role == UserRoleEnum.issuer:
        issuer= Issuer(
            did=f"did:ethr:arbitrum:{req.wallet_address}",
            name=req.full_name,
            wallet_address=req.wallet_address,
        )
        db.add(issuer)
        db.flush()

    user = User(
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        wallet_address=req.wallet_address,
        role=req.role,
        learner_id=learner.id if learner else None,
        issuer_id=issuer.id if issuer else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    tokens = issue_tokens(user, db)
    return {
        **tokens,
        "user": serialize_user(user),
    }


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=req.email.lower(), is_active=True).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    tokens = issue_tokens(user, db)
    return {
        **tokens,
        "user": serialize_user(user),
    }


@router.get("/me")
async def me(user: User = Depends(current_user)):
    return {"user": serialize_user(user)}


@router.post("/refresh")
async def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    record = db.query(AuthSession).filter_by(
        refresh_token_hash=refresh_token_hash(req.refresh_token),
        revoked_at=None,
    ).first()
    if not record or record.expires_at < datetime.utcnow():
        raise HTTPException(401, "Invalid refresh token")
    user = db.query(User).filter_by(id=record.user_id, is_active=True).first()
    if not user:
        raise HTTPException(401, "User not found")
    return {"access_token": create_token({"sub": user.id, "role": user.role.value}, get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)}


@router.post("/logout")
async def logout(req: RefreshRequest, db: Session = Depends(get_db)):
    record = db.query(AuthSession).filter_by(refresh_token_hash=refresh_token_hash(req.refresh_token)).first()
    if record:
        record.revoked_at = datetime.utcnow()
        db.commit()
    return {"status": "success"}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    return {"status": "accepted", "message": "Password reset delivery is not configured in preview mode."}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    return {"status": "accepted", "message": "Password reset token validation is not configured in preview mode."}
