import json
import sqlite3
import sys
from pathlib import Path
from urllib.parse import unquote


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
AI_DB = PROJECT_ROOT / "ai_service" / "ai_service.db"


def configured_backend_db() -> Path:
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.core.config import get_settings

    database_url = get_settings().DATABASE_URL
    if database_url.startswith("sqlite:///"):
        raw_path = unquote(database_url.replace("sqlite:///", "", 1))
        db_path = Path(raw_path)
        if not db_path.is_absolute():
            db_path = BACKEND_ROOT / db_path
        return db_path

    raise RuntimeError(
        "clear_preview_data.py only clears SQLite databases. "
        f"Configured DATABASE_URL is {database_url!r}."
    )

BACKEND_TABLES = [
    "auth_sessions",
    "certificates",
    "assessments",
    "assessment_templates",
    "course_enrollments",
    "course_codes",
    "courses",
    "materials",
    "issuer_keys",
    "institution_keys",
    "learners",
    "issuers",
    "institutions",
    "users",
    "audit_log",
]

AI_TABLES = [
    "assessment_sessions",
    "materials",
]


def clear_tables(db_path: Path, tables: list[str]) -> dict:
    if not db_path.exists():
        return {"database": str(db_path), "exists": False}

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    existing = {
        row[0]
        for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }

    before = {}
    after = {}
    for table in tables:
        if table in existing:
            before[table] = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    cur.execute("PRAGMA foreign_keys=OFF")
    for table in tables:
        if table in existing:
            cur.execute(f"DELETE FROM {table}")

    if "sqlite_sequence" in existing:
        for table in tables:
            cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))

    conn.commit()

    for table in tables:
        if table in existing:
            after[table] = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    conn.close()
    return {
        "database": str(db_path),
        "exists": True,
        "before": before,
        "after": after,
    }


def main():
    backend_db = configured_backend_db()
    result = {
        "backend": clear_tables(backend_db, BACKEND_TABLES),
        "ai_service": clear_tables(AI_DB, AI_TABLES),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
