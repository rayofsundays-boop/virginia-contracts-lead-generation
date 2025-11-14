#!/usr/bin/env python3
"""
Add 2FA columns to leads table for production database.
Run this after deployment to fix admin2 login issues.
"""

import os
import sys
from sqlalchemy import create_engine, text

def add_twofa_columns():
    """Add twofa_enabled and twofa_secret columns to leads table."""
    
    # Get database URL from environment or use local SQLite
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Local development - use SQLite
        database_url = 'sqlite:///leads.db'
        print("🔧 Using local SQLite database")
    else:
        # Production - ensure postgres:// is replaced with postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print("🌐 Using production PostgreSQL database")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if columns already exist
            if 'postgresql' in database_url:
                # PostgreSQL query
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'leads' 
                    AND column_name IN ('twofa_enabled', 'twofa_secret')
                """))
                existing_cols = [row[0] for row in result]
            else:
                # SQLite query
                result = conn.execute(text("PRAGMA table_info(leads)"))
                existing_cols = [row[1] for row in result]
            
            # Add twofa_enabled if missing
            if 'twofa_enabled' not in existing_cols:
                try:
                    conn.execute(text("ALTER TABLE leads ADD COLUMN twofa_enabled BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                    print("✅ Added twofa_enabled column")
                except Exception as e:
                    print(f"⚠️  Could not add twofa_enabled: {e}")
            else:
                print("✅ twofa_enabled column already exists")
            
            # Add twofa_secret if missing
            if 'twofa_secret' not in existing_cols:
                try:
                    conn.execute(text("ALTER TABLE leads ADD COLUMN twofa_secret TEXT"))
                    conn.commit()
                    print("✅ Added twofa_secret column")
                except Exception as e:
                    print(f"⚠️  Could not add twofa_secret: {e}")
            else:
                print("✅ twofa_secret column already exists")
        
        print("\n✅ Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_twofa_columns()
    sys.exit(0 if success else 1)
