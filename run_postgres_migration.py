"""
Run PostgreSQL migration to create commercial tables on production database
Usage: python run_postgres_migration.py

⚠️  DISABLED: SQL migration file has been disabled to prevent fake data insertion.
This script will not run until migrations/create_commercial_tables_postgres.sql is restored.
"""
import os
import sys
from sqlalchemy import create_engine, text

print("❌ MIGRATION DISABLED")
print("=" * 80)
print("The SQL migration file has been disabled (.DISABLED extension) to prevent")
print("insertion of fake/demo commercial leads into the production database.")
print("")
print("File location: migrations/create_commercial_tables_postgres.sql.DISABLED")
print("")
print("If you need to run this migration:")
print("1. Remove the fake data INSERT statements from the SQL file")
print("2. Rename the file back to .sql (remove .DISABLED)")
print("3. Run this script again")
print("=" * 80)
sys.exit(1)

# Get DATABASE_URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    print("Please set it to your PostgreSQL connection string")
    exit(1)

# Fix for SQLAlchemy 1.4+ which requires postgresql:// instead of postgres://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

print(f"Connecting to database...")
print(f"URL: {DATABASE_URL[:30]}..." if len(DATABASE_URL) > 30 else "URL: [hidden]")

try:
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Read migration SQL - THIS WILL FAIL NOW SINCE FILE IS DISABLED
    with open('migrations/create_commercial_tables_postgres.sql', 'r') as f:
        migration_sql = f.read()
    
    # Split into individual statements (PostgreSQL can handle multiple, but safer this way)
    statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
    
    print(f"\nExecuting {len(statements)} SQL statements...")
    
    with engine.connect() as conn:
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"  [{i}/{len(statements)}] Executing statement...")
                try:
                    result = conn.execute(text(statement))
                    conn.commit()
                    
                    # Try to fetch results if it's a SELECT
                    if statement.strip().upper().startswith('SELECT'):
                        rows = result.fetchall()
                        for row in rows:
                            print(f"    ✓ {row[0]}")
                except Exception as e:
                    print(f"    ⚠ Warning: {str(e)[:100]}")
                    # Continue even if there's an error (table might already exist)
    
    print("\n✅ Migration completed successfully!")
    print("\nVerifying tables exist...")
    
    with engine.connect() as conn:
        # Check if tables exist
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('commercial_lead_requests', 'bids', 'residential_lead_requests')
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print("✓ Found tables:")
            for table in tables:
                print(f"  - {table}")
                
                # Count rows
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                print(f"    ({count} rows)")
        else:
            print("⚠ Warning: Tables not found. Migration may have failed.")
    
    print("\n🎉 Database migration complete!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
