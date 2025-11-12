#!/usr/bin/env python3
"""
Fix deadline data in federal_contracts table
Ensures all deadline values are either NULL or valid ISO date strings
"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if not DATABASE_URL:
    print("❌ DATABASE_URL not set. This script is for production use only.")
    print("   Run manually on Render shell or set DATABASE_URL locally.")
    exit(1)

# Connect to database
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # First, check for problematic deadlines
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN deadline = '' THEN 1 ELSE 0 END) as empty_strings,
                   SUM(CASE WHEN deadline IS NULL THEN 1 ELSE 0 END) as nulls,
                   SUM(CASE WHEN deadline ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN 1 ELSE 0 END) as valid_dates
            FROM federal_contracts
        """))
        stats = result.fetchone()
        
        print(f"\n📊 Current deadline data:")
        print(f"   Total contracts: {stats[0]}")
        print(f"   Empty strings: {stats[1]}")
        print(f"   NULL values: {stats[2]}")
        print(f"   Valid ISO dates: {stats[3]}")
        
        # Convert empty strings to NULL
        if stats[1] > 0:
            print(f"\n🔧 Converting {stats[1]} empty strings to NULL...")
            conn.execute(text("""
                UPDATE federal_contracts 
                SET deadline = NULL 
                WHERE deadline = ''
            """))
            conn.commit()
            print("✅ Empty strings converted to NULL")
        else:
            print("\n✅ No empty strings found - data is clean!")
        
        # Verify the fix
        result = conn.execute(text("""
            SELECT COUNT(*) FROM federal_contracts 
            WHERE deadline IS NOT NULL AND deadline != ''
        """))
        valid_count = result.scalar()
        print(f"\n✅ Final count: {valid_count} contracts with valid deadlines")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    engine.dispose()
