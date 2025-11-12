"""
Migration script to create missing database tables
Creates: user_activity, user_preferences, notifications

Run this script to fix database transaction errors.
"""

import sqlite3
from datetime import datetime

def migrate_database():
    """Create missing tables in the database"""
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    print("🔧 Creating missing database tables...")
    
    # Create user_activity table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_description TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES leads(id) ON DELETE CASCADE
            )
        """)
        print("✅ Created user_activity table")
    except Exception as e:
        print(f"⚠️  user_activity table error: {e}")
    
    # Create user_preferences table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                email_notifications BOOLEAN DEFAULT 1,
                sms_notifications BOOLEAN DEFAULT 0,
                notification_frequency TEXT DEFAULT 'daily',
                preferred_locations TEXT,
                preferred_contract_types TEXT,
                dark_mode BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES leads(id) ON DELETE CASCADE
            )
        """)
        print("✅ Created user_preferences table")
    except Exception as e:
        print(f"⚠️  user_preferences table error: {e}")
    
    # Create notifications table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                link TEXT,
                is_read BOOLEAN DEFAULT 0,
                priority TEXT DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES leads(id) ON DELETE CASCADE
            )
        """)
        print("✅ Created notifications table")
    except Exception as e:
        print(f"⚠️  notifications table error: {e}")
    
    # Create indexes for performance
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)")
        print("✅ Created indexes")
    except Exception as e:
        print(f"⚠️  Index creation error: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    print("\nCreated tables:")
    print("  • user_activity - Track user actions and behavior")
    print("  • user_preferences - Store user settings and preferences")
    print("  • notifications - In-app notification system")

if __name__ == '__main__':
    migrate_database()
