import json
import sqlite3
from pathlib import Path


BACKEND_DB = Path("/home/anzicle/project/backend/dev2.db")
AI_DB = Path("/home/anzicle/project/ai_service/ai_service.db")

BACKEND_TABLES = [
    "auth_sessions",
    "certificates",
    "assessments",
    "assessment_templates",
    "course_enrollments",
    "course_codes",
    "courses",
    "materials",
    "institution_keys",
    "learners",
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
    result = {
        "backend": clear_tables(BACKEND_DB, BACKEND_TABLES),
        "ai_service": clear_tables(AI_DB, AI_TABLES),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
