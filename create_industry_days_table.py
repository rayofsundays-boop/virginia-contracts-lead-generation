#!/usr/bin/env python3
"""
Create the industry_days table in the local SQLite database (db.sqlite3) if it does not exist.
Schema mirrors the canonical schema used in migrations, adapted for SQLite types.
Safe to run multiple times.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

DDL = {
    "create_table": """
    CREATE TABLE IF NOT EXISTS industry_days (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_title TEXT NOT NULL,
        organizer TEXT NOT NULL,
        organizer_type TEXT,
        event_date TEXT NOT NULL,            -- ISO date string YYYY-MM-DD
        event_time TEXT,
        location TEXT,
        city TEXT,
        state TEXT,
        venue_name TEXT,
        event_type TEXT DEFAULT 'Industry Day',
        description TEXT,
        target_audience TEXT,
        registration_required INTEGER DEFAULT 1,
        registration_deadline TEXT,         -- ISO date string YYYY-MM-DD
        registration_link TEXT,
        contact_name TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        topics TEXT,
        is_virtual INTEGER DEFAULT 0,
        virtual_link TEXT,
        attachments TEXT,
        status TEXT DEFAULT 'upcoming',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    "idx_date": "CREATE INDEX IF NOT EXISTS idx_industry_days_date ON industry_days(event_date)",
    "idx_city": "CREATE INDEX IF NOT EXISTS idx_industry_days_city ON industry_days(city)",
    "idx_status": "CREATE INDEX IF NOT EXISTS idx_industry_days_status ON industry_days(status)",
    "idx_state": "CREATE INDEX IF NOT EXISTS idx_industry_days_state ON industry_days(state)",
}

def ensure_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Create table only; indexes handled after ensuring columns
    cur.execute(DDL["create_table"])
    conn.commit()


def ensure_columns(conn: sqlite3.Connection) -> None:
    """Ensure required columns exist even if table was created previously without them."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(industry_days)")
    cols = {row[1] for row in cur.fetchall()}  # column names
    missing = []
    if 'state' not in cols:
        missing.append(("state", "TEXT"))
    for name, typ in missing:
        cur.execute(f"ALTER TABLE industry_days ADD COLUMN {name} {typ}")
    if missing:
        conn.commit()


def ensure_indexes(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    for key in ("idx_date", "idx_city", "idx_status", "idx_state"):
        cur.execute(DDL[key])
    conn.commit()


def table_exists(conn: sqlite3.Connection) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='industry_days'")
    return cur.fetchone() is not None


def get_row_count(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM industry_days")
    return cur.fetchone()[0]


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    try:
        existed = table_exists(conn)
        ensure_table(conn)
        ensure_columns(conn)
        ensure_indexes(conn)
        now_exists = table_exists(conn)
        print(f"industry_days existed before: {existed}")
        print(f"industry_days exists now:   {now_exists}")
        if now_exists:
            try:
                count = get_row_count(conn)
            except sqlite3.OperationalError:
                # Table exists but empty or columns not yet compatible, treat as 0
                count = 0
            print(f"industry_days row count:  {count}")
        print("✅ Done")
        return 0
    finally:
        conn.close()

if __name__ == "__main__":
    raise SystemExit(main())
