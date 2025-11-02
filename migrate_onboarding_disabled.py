#!/usr/bin/env python3
"""
Migration script to add onboarding_disabled column to user_onboarding table
This allows users to permanently dismiss the onboarding modal
"""

import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    exit(1)

# Fix postgres:// to postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Adding onboarding_disabled column to user_onboarding table...")
        
        # Read and execute the migration SQL
        with open('migrations/add_onboarding_disabled_column.sql', 'r') as f:
            sql = f.read()
        
        # Execute each statement
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
except Exception as e:
    print(f"❌ Migration failed: {e}")
    exit(1)
