"""
app/services/ipfs.py — IPFS pinning via Pinata API

Functions:
  pin_json(data, name)  → CID string
  pin_file(path, name)  → CID string
"""
import json
import logging
from typing import Union

import httpx

from app.core.config import get_settings

log = logging.getLogger("ipfs")

PINATA_JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
PINATA_FILE_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"


def _headers() -> dict:
    settings = get_settings()
    if settings.PINATA_JWT:
        return {"Authorization": f"Bearer {settings.PINATA_JWT}"}
    return {
        "pinata_api_key":    settings.PINATA_API_KEY,
        "pinata_secret_api_key": settings.PINATA_API_SECRET,
    }


async def pin_json(data: dict, name: str = "skillcert-metadata") -> str:
    """
    Pin a JSON object to IPFS via Pinata.
    Returns the IPFS CID (without ipfs:// prefix).
    """
    settings = get_settings()
    if not settings.PINATA_JWT and not settings.PINATA_API_KEY:
        # Dev fallback — return a deterministic fake CID
        import hashlib
        fake = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        log.warning(f"No Pinata credentials — using mock CID: {fake[:32]}")
        return f"Qm{fake[:44]}"

    payload = {
        "pinataContent": data,
        "pinataMetadata": {"name": name},
        "pinataOptions":  {"cidVersion": 1},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(PINATA_JSON_URL, json=payload, headers=_headers())
        resp.raise_for_status()
        cid = resp.json()["IpfsHash"]
        log.info(f"Pinned JSON to IPFS: {cid}")
        return cid


async def pin_file(file_bytes: bytes, name: str) -> str:
    """
    Pin a file (e.g. PDF attestation) to IPFS via Pinata.
    Returns the IPFS CID.
    """
    settings = get_settings()
    if not settings.PINATA_JWT and not settings.PINATA_API_KEY:
        import hashlib
        fake = hashlib.sha256(file_bytes).hexdigest()
        log.warning(f"No Pinata credentials — using mock CID: {fake[:32]}")
        return f"Qm{fake[:44]}"

    files = {"file": (name, file_bytes, "application/octet-stream")}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(PINATA_FILE_URL, files=files, headers=_headers())
        resp.raise_for_status()
        cid = resp.json()["IpfsHash"]
        log.info(f"Pinned file to IPFS: {cid}")
        return cid