from datetime import datetime, timezone
import base64
import hashlib

from app.core.config import get_settings
from app.models.db import IssuerKey, SessionLocal


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt_private_key(private_key: str) -> str:
    key = hashlib.sha256(get_settings().SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(_xor(private_key.encode(), key)).decode()


def decrypt_private_key(encrypted: str) -> str:
    key = hashlib.sha256(get_settings().SECRET_KEY.encode()).digest()
    return _xor(base64.urlsafe_b64decode(encrypted.encode()), key).decode()


class IssuerKeyManager:
    def __init__(self):
        self.keys_cache: dict[int, tuple[str, str]] = {}
        self.load_all_keys()

    def load_all_keys(self):
        db = SessionLocal()
        try:
            records = db.query(IssuerKey).filter(IssuerKey.revoked_at.is_(None)).all()
            self.keys_cache = {
                r.issuer_id: (r.issuer_address, decrypt_private_key(r.private_key_encrypted))
                for r in records
            }
        finally:
            db.close()

    def get_key(self, issuer_id: int) -> tuple[str, str] | None:
        return self.keys_cache.get(issuer_id)

    def add_key(self, issuer_id: int, address: str, private_key: str):
        db = SessionLocal()
        try:
            db.add(IssuerKey(
                issuer_id=issuer_id,
                issuer_address=address,
                private_key_encrypted=encrypt_private_key(private_key),
            ))
            db.commit()
            self.keys_cache[issuer_id] = (address, private_key)
        finally:
            db.close()

    def revoke_key(self, issuer_id: int):
        db = SessionLocal()
        try:
            records = db.query(IssuerKey).filter_by(issuer_id=issuer_id, revoked_at=None).all()
            for record in records:
                record.revoked_at = datetime.now(timezone.utc)
            db.commit()
            self.keys_cache.pop(issuer_id, None)
        finally:
            db.close()


_manager: IssuerKeyManager | None = None


def get_key_manager() -> IssuerKeyManager:
    global _manager
    if _manager is None:
        _manager = IssuerKeyManager()
    return _manager
