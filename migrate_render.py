"""
Migrate Render PostgreSQL database to add password reset columns
Run this with: python3 migrate_render.py
"""

import os
import psycopg

# Get DATABASE_URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set")
    print("Please set it with:")
    print('export DATABASE_URL="your-render-postgresql-url"')
    exit(1)

# Convert postgres:// to postgresql:// if needed
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

print(f"🔗 Connecting to database...")

try:
    # Connect to PostgreSQL
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check if columns already exist
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='leads' 
        AND column_name IN ('reset_token', 'reset_token_expires')
    """)
    
    existing_columns = [row[0] for row in cur.fetchall()]
    
    if 'reset_token' in existing_columns and 'reset_token_expires' in existing_columns:
        print("✅ Columns already exist - no migration needed")
    else:
        print("📝 Adding reset_token columns to leads table...")
        
        # Add columns if they don't exist
        cur.execute("""
            ALTER TABLE leads 
            ADD COLUMN IF NOT EXISTS reset_token TEXT,
            ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP
        """)
        
        conn.commit()
        print("✅ Successfully added reset_token columns!")
        print("   - reset_token (TEXT)")
        print("   - reset_token_expires (TIMESTAMP)")
    
    cur.close()
    conn.close()
    print("✅ Migration complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
