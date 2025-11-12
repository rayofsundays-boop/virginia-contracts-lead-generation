"""
Migration script to add posted_date column to supply_contracts (SQLite/local)
Use this locally if you want to eliminate insert warnings during seed.
"""

import sqlite3

def migrate():
    conn = sqlite3.connect('leads.db')
    cur = conn.cursor()

    # Detect existing columns
    cur.execute("PRAGMA table_info(supply_contracts)")
    cols = [row[1] for row in cur.fetchall()]
    if 'posted_date' in cols:
        print('ℹ️  posted_date already exists on supply_contracts')
        conn.close()
        return True

    try:
        cur.execute("ALTER TABLE supply_contracts ADD COLUMN posted_date TEXT")
        conn.commit()
        print('✅ Added posted_date column to supply_contracts')
    except Exception as e:
        print(f'❌ Failed to add posted_date: {e}')
        conn.rollback()
        conn.close()
        return False

    conn.close()
    return True

if __name__ == '__main__':
    migrate()
