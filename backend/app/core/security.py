"""
Security helpers for password hashing and signed bearer tokens.

This module intentionally avoids heavyweight dependencies. Tokens are compact
HMAC-signed JSON payloads. For production, rotating keys and stricter token
auditing should be added at the deployment layer.
"""

from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import secrets
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db import SessionLocal, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, digest = encoded.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
        return hmac.compare_digest(candidate.hex(), digest)
    except ValueError:
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(payload: dict[str, Any], minutes: int) -> str:
    settings = get_settings()
    body = dict(payload)
    body["exp"] = int((datetime.now(timezone.utc) + timedelta(minutes=minutes)).timestamp())
    encoded = _b64(json.dumps(body, separators=(",", ":"), sort_keys=True).encode())
    sig = hmac.new(settings.SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).digest()
    return f"{encoded}.{_b64(sig)}"


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        encoded, sig = token.split(".", 1)
        expected = _b64(hmac.new(settings.SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        payload = json.loads(_unb64(encoded))
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(401, "Authentication required")
    payload = decode_token(credentials.credentials)
    user = db.query(User).filter_by(id=payload.get("sub"), is_active=True).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user


def refresh_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
