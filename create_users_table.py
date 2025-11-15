#!/usr/bin/env python3
"""
Create a dedicated users table for user management.
This separates user authentication/management from the leads table.

Run: python create_users_table.py
"""

import os
from datetime import datetime
from sqlalchemy import text
from app import app, db

def create_users_table():
    """Create users table with comprehensive user management fields"""
    
    with app.app_context():
        try:
            # Detect database type
            is_postgres = 'postgresql' in str(db.engine.url)
            serial_type = 'SERIAL PRIMARY KEY' if is_postgres else 'INTEGER PRIMARY KEY AUTOINCREMENT'
            bool_type = 'BOOLEAN' if is_postgres else 'INTEGER'
            ts_default = 'CURRENT_TIMESTAMP'
            
            print("=" * 70)
            print("CREATING USERS TABLE FOR USER MANAGEMENT")
            print("=" * 70)
            print(f"Database: {str(db.engine.url)[:80]}...")
            print(f"Type: {'PostgreSQL' if is_postgres else 'SQLite'}")
            print("=" * 70)
            
            # Create users table
            db.session.execute(text(f'''
                CREATE TABLE IF NOT EXISTS users (
                    -- Primary Key
                    id {serial_type},
                    
                    -- Authentication
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    
                    -- Profile Information
                    first_name TEXT,
                    last_name TEXT,
                    full_name TEXT,
                    phone TEXT,
                    company_name TEXT,
                    
                    -- Account Status
                    is_active {bool_type} DEFAULT 1,
                    is_verified {bool_type} DEFAULT 0,
                    is_admin {bool_type} DEFAULT 0,
                    is_superuser {bool_type} DEFAULT 0,
                    
                    -- Subscription & Credits
                    subscription_status TEXT DEFAULT 'free',
                    subscription_tier TEXT DEFAULT 'free',
                    subscription_start_date TIMESTAMP,
                    subscription_end_date TIMESTAMP,
                    credits_balance INTEGER DEFAULT 0,
                    credits_used INTEGER DEFAULT 0,
                    free_credits_remaining INTEGER DEFAULT 3,
                    
                    -- Security
                    twofa_enabled {bool_type} DEFAULT 0,
                    twofa_secret TEXT,
                    last_login TIMESTAMP,
                    last_login_ip TEXT,
                    failed_login_attempts INTEGER DEFAULT 0,
                    account_locked_until TIMESTAMP,
                    password_reset_token TEXT,
                    password_reset_expires TIMESTAMP,
                    email_verification_token TEXT,
                    email_verification_expires TIMESTAMP,
                    
                    -- Preferences
                    email_notifications {bool_type} DEFAULT 1,
                    sms_notifications {bool_type} DEFAULT 0,
                    marketing_emails {bool_type} DEFAULT 0,
                    timezone TEXT DEFAULT 'America/New_York',
                    language TEXT DEFAULT 'en',
                    
                    -- Metadata
                    lead_source TEXT DEFAULT 'website',
                    registration_ip TEXT,
                    user_agent TEXT,
                    referrer TEXT,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT {ts_default},
                    updated_at TIMESTAMP DEFAULT {ts_default},
                    deleted_at TIMESTAMP,
                    
                    -- Soft Delete Flag
                    is_deleted {bool_type} DEFAULT 0
                )
            '''))
            
            db.session.commit()
            print("✅ Users table created successfully!")
            
            # Create indexes for performance
            indexes = [
                ('idx_users_email', 'users', 'email'),
                ('idx_users_username', 'users', 'username'),
                ('idx_users_is_active', 'users', 'is_active'),
                ('idx_users_subscription_status', 'users', 'subscription_status'),
                ('idx_users_created_at', 'users', 'created_at'),
            ]
            
            print("\n🔧 Creating indexes...")
            for idx_name, table, column in indexes:
                try:
                    db.session.execute(text(f'''
                        CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})
                    '''))
                    print(f"   ✅ {idx_name}")
                except Exception as idx_err:
                    print(f"   ⚠️  {idx_name}: {idx_err}")
            
            db.session.commit()
            print("✅ Indexes created successfully!")
            
            # Create user_roles table for role-based access control
            print("\n🔧 Creating user_roles table...")
            db.session.execute(text(f'''
                CREATE TABLE IF NOT EXISTS user_roles (
                    id {serial_type},
                    user_id INTEGER NOT NULL,
                    role_name TEXT NOT NULL,
                    granted_at TIMESTAMP DEFAULT {ts_default},
                    granted_by INTEGER,
                    expires_at TIMESTAMP,
                    is_active {bool_type} DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            '''))
            db.session.commit()
            print("✅ User roles table created!")
            
            # Create user_sessions table for session management
            print("\n🔧 Creating user_sessions table...")
            db.session.execute(text(f'''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id {serial_type},
                    user_id INTEGER NOT NULL,
                    session_token TEXT NOT NULL UNIQUE,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT {ts_default},
                    last_activity TIMESTAMP DEFAULT {ts_default},
                    expires_at TIMESTAMP,
                    is_active {bool_type} DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            '''))
            db.session.commit()
            print("✅ User sessions table created!")
            
            # Create user_activity_log table
            print("\n🔧 Creating user_activity_log table...")
            db.session.execute(text(f'''
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id {serial_type},
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    activity_description TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT {ts_default},
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            '''))
            db.session.commit()
            print("✅ User activity log table created!")
            
            # Show table structure
            print("\n" + "=" * 70)
            print("USERS TABLE STRUCTURE")
            print("=" * 70)
            
            if is_postgres:
                result = db.session.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position
                """)).fetchall()
                for row in result:
                    print(f"  {row[0]:30} {row[1]:15} {row[2]}")
            else:
                result = db.session.execute(text("PRAGMA table_info(users)")).fetchall()
                print(f"  {'Column Name':30} {'Type':15} {'Not Null':10} {'Default'}")
                print(f"  {'-'*30} {'-'*15} {'-'*10} {'-'*20}")
                for row in result:
                    print(f"  {row[1]:30} {row[2]:15} {str(bool(row[3])):10} {str(row[4])[:20]}")
            
            # Check if we should migrate data from leads table
            print("\n" + "=" * 70)
            print("DATA MIGRATION CHECK")
            print("=" * 70)
            
            leads_count = db.session.execute(text("SELECT COUNT(*) FROM leads")).fetchone()[0]
            users_count = db.session.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
            
            print(f"Leads table records: {leads_count}")
            print(f"Users table records: {users_count}")
            
            if leads_count > 0 and users_count == 0:
                print("\n⚠️  WARNING: You have data in 'leads' table but 'users' table is empty.")
                print("Consider running migration script to copy users from leads to users table.")
            
            print("\n" + "=" * 70)
            print("✅ USER MANAGEMENT SYSTEM READY!")
            print("=" * 70)
            print("\nTables created:")
            print("  ✅ users - Main user accounts")
            print("  ✅ user_roles - Role-based access control")
            print("  ✅ user_sessions - Session tracking")
            print("  ✅ user_activity_log - Audit trail")
            print("\nNext steps:")
            print("  1. Run migration script if needed: python migrate_leads_to_users.py")
            print("  2. Update authentication routes to use users table")
            print("  3. Consider deprecating leads table for user management")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    create_users_table()
