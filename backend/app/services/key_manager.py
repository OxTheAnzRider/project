from datetime import datetime, timezone
import base64
import hashlib

from app.core.config import get_settings
from app.models.db import InstitutionKey, SessionLocal


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt_private_key(private_key: str) -> str:
    key = hashlib.sha256(get_settings().SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(_xor(private_key.encode(), key)).decode()


def decrypt_private_key(encrypted: str) -> str:
    key = hashlib.sha256(get_settings().SECRET_KEY.encode()).digest()
    return _xor(base64.urlsafe_b64decode(encrypted.encode()), key).decode()


class InstitutionKeyManager:
    def __init__(self):
        self.keys_cache: dict[int, tuple[str, str]] = {}
        self.load_all_keys()

    def load_all_keys(self):
        db = SessionLocal()
        try:
            records = db.query(InstitutionKey).filter(InstitutionKey.revoked_at.is_(None)).all()
            self.keys_cache = {
                r.institution_id: (r.institution_address, decrypt_private_key(r.private_key_encrypted))
                for r in records
            }
        finally:
            db.close()

    def get_key(self, institution_id: int) -> tuple[str, str] | None:
        return self.keys_cache.get(institution_id)

    def add_key(self, institution_id: int, address: str, private_key: str):
        db = SessionLocal()
        try:
            db.add(InstitutionKey(
                institution_id=institution_id,
                institution_address=address,
                private_key_encrypted=encrypt_private_key(private_key),
            ))
            db.commit()
            self.keys_cache[institution_id] = (address, private_key)
        finally:
            db.close()

    def revoke_key(self, institution_id: int):
        db = SessionLocal()
        try:
            records = db.query(InstitutionKey).filter_by(institution_id=institution_id, revoked_at=None).all()
            for record in records:
                record.revoked_at = datetime.now(timezone.utc)
            db.commit()
            self.keys_cache.pop(institution_id, None)
        finally:
            db.close()


_manager: InstitutionKeyManager | None = None


def get_key_manager() -> InstitutionKeyManager:
    global _manager
    if _manager is None:
        _manager = InstitutionKeyManager()
    return _manager
