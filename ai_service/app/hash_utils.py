"""Deterministic hashing helpers for assessment reports."""

import hashlib
import json
from typing import Any


VOLATILE_KEYS = {"completed_at", "created_at", "started_at", "timestamp", "submission_time"}


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _normalize(item)
            for key, item in sorted(value.items())
            if key not in VOLATILE_KEYS
        }
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, float):
        return round(value, 4)
    return value


def generate_report_hash(report: dict) -> str:
    """Return a SHA-256 hash over stable, sorted JSON."""
    normalized = _normalize(report)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
