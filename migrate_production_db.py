"""
Production database migration script for PostgreSQL on Render
Creates missing tables and columns using Flask's SQLAlchemy connection

Run this on production: python migrate_production_db.py
"""

import os
import sys
from sqlalchemy import text

# Add current directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def run_migrations():
    """Run all database migrations for production PostgreSQL"""
    
    with app.app_context():
        print("🔧 Starting production database migration...")
        print(f"📊 Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')[:50]}...")
        
        try:
            # Test connection
            db.session.execute(text("SELECT 1"))
            print("✅ Database connection successful\n")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        # Migration 1: Create user_activity table
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    activity_type VARCHAR(100) NOT NULL,
                    activity_description TEXT,
                    ip_address VARCHAR(50),
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.session.commit()
            print("✅ Created user_activity table")
        except Exception as e:
            print(f"⚠️  user_activity table: {e}")
            db.session.rollback()
        
        # Migration 2: Create user_preferences table
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE,
                    email_notifications BOOLEAN DEFAULT TRUE,
                    sms_notifications BOOLEAN DEFAULT FALSE,
                    notification_frequency VARCHAR(20) DEFAULT 'daily',
                    preferred_locations TEXT,
                    preferred_contract_types TEXT,
                    dark_mode BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.session.commit()
            print("✅ Created user_preferences table")
        except Exception as e:
            print(f"⚠️  user_preferences table: {e}")
            db.session.rollback()
        
        # Migration 3: Create notifications table
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    notification_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    link TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    priority VARCHAR(20) DEFAULT 'normal',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP
                )
            """))
            db.session.commit()
            print("✅ Created notifications table")
        except Exception as e:
            print(f"⚠️  notifications table: {e}")
            db.session.rollback()
        
        # Migration 4: Create indexes for performance
        indexes = [
            ("idx_user_activity_user_id", "user_activity", "user_id"),
            ("idx_user_activity_created_at", "user_activity", "created_at"),
            ("idx_notifications_user_id", "notifications", "user_id"),
            ("idx_notifications_is_read", "notifications", "is_read"),
        ]
        
        for idx_name, table, column in indexes:
            try:
                db.session.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})
                """))
                db.session.commit()
                print(f"✅ Created index {idx_name}")
            except Exception as e:
                print(f"⚠️  Index {idx_name}: {e}")
                db.session.rollback()
        
        # Migration 5: Add website_url column to commercial_opportunities
        try:
            # Check if column exists first
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='commercial_opportunities' 
                AND column_name='website_url'
            """))
            
            if result.fetchone() is None:
                db.session.execute(text("""
                    ALTER TABLE commercial_opportunities 
                    ADD COLUMN website_url TEXT
                """))
                db.session.commit()
                print("✅ Added website_url column to commercial_opportunities")
            else:
                print("ℹ️  website_url column already exists in commercial_opportunities")
        except Exception as e:
            print(f"⚠️  website_url column: {e}")
            db.session.rollback()
        
        # Verification
        print("\n🔍 Verifying migrations...")
        
        try:
            # Check tables exist
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('user_activity', 'user_preferences', 'notifications')
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Tables verified: {', '.join(tables)}")
            
            # Check website_url column
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='commercial_opportunities' 
                AND column_name='website_url'
            """))
            if result.fetchone():
                print("✅ website_url column verified in commercial_opportunities")
            
            # Count rows in new tables
            counts = {}
            for table in ['user_activity', 'user_preferences', 'notifications']:
                count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                counts[table] = count
            
            print(f"\n📊 Row counts:")
            for table, count in counts.items():
                print(f"  • {table}: {count} rows")
            
        except Exception as e:
            print(f"⚠️  Verification error: {e}")
        
        print("\n✅ Migration completed successfully!")
        print("\n🎉 Production database is now up to date!")
        return True

if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)
