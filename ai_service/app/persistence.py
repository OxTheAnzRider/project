"""Small SQLite persistence layer for AI-service recovery/cache.

The backend database remains authoritative. This local store prevents the AI
service from losing generated questions and submitted answers on restart.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB = Path(__file__).resolve().parents[1] / "ai_service.db"


class AIPersistence:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv("AI_SERVICE_DB_PATH", str(DEFAULT_DB))
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS materials (
                    material_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assessment_sessions (
                    session_id TEXT PRIMARY KEY,
                    material_id TEXT NOT NULL,
                    learner_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )

    def save_material(self, material_id: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO materials (material_id, payload_json, created_at)
                VALUES (?, ?, ?)
                """,
                (material_id, json.dumps(payload), payload.get("created_at", "")),
            )

    def load_material(self, material_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM materials WHERE material_id = ?",
                (material_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save_session(self, session_id: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO assessment_sessions
                    (session_id, material_id, learner_id, payload_json, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    payload.get("material_id", ""),
                    payload.get("student_id", ""),
                    json.dumps(payload),
                    payload.get("started_at", ""),
                    payload.get("completed_at"),
                ),
            )

    def load_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM assessment_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None
