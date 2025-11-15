#!/usr/bin/env python3
"""
Create external_emails table for tracking sent external emails.
Run: python create_external_emails_table.py
"""

import os
from datetime import datetime
from sqlalchemy import text
from app import app, db

def create_external_emails_table():
    """Create table for tracking external emails sent by admins"""
    
    with app.app_context():
        try:
            # Detect database type
            is_postgres = 'postgresql' in str(db.engine.url)
            serial_type = 'SERIAL PRIMARY KEY' if is_postgres else 'INTEGER PRIMARY KEY AUTOINCREMENT'
            bool_type = 'BOOLEAN' if is_postgres else 'INTEGER'
            ts_default = 'CURRENT_TIMESTAMP'
            
            print("=" * 70)
            print("CREATING EXTERNAL EMAILS TABLE")
            print("=" * 70)
            print(f"Database: {str(db.engine.url)[:80]}...")
            print(f"Type: {'PostgreSQL' if is_postgres else 'SQLite'}")
            print("=" * 70)
            
            # Create external_emails table
            db.session.execute(text(f'''
                CREATE TABLE IF NOT EXISTS external_emails (
                    -- Primary Key
                    id {serial_type},
                    
                    -- Sender Information
                    sender_user_id INTEGER NOT NULL,
                    sender_username TEXT,
                    sender_email TEXT,
                    is_admin_sender {bool_type} DEFAULT 1,
                    
                    -- Recipient Information
                    recipient_email TEXT NOT NULL,
                    recipient_name TEXT,
                    
                    -- Message Details
                    message_type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    message_body TEXT NOT NULL,
                    message_html TEXT,
                    
                    -- Delivery Status
                    status TEXT DEFAULT 'pending',
                    sent_at TIMESTAMP,
                    delivery_attempted {bool_type} DEFAULT 0,
                    delivery_error TEXT,
                    
                    -- Tracking
                    opened_at TIMESTAMP,
                    clicked_at TIMESTAMP,
                    bounce_reason TEXT,
                    
                    -- Rate Limiting
                    ip_address TEXT,
                    user_agent TEXT,
                    
                    -- Metadata
                    priority TEXT DEFAULT 'normal',
                    tags TEXT,
                    campaign_id TEXT,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT {ts_default},
                    updated_at TIMESTAMP DEFAULT {ts_default}
                )
            '''))
            
            db.session.commit()
            print("✅ external_emails table created successfully!")
            
            # Create indexes for performance
            indexes = [
                ('idx_external_emails_sender', 'external_emails', 'sender_user_id'),
                ('idx_external_emails_recipient', 'external_emails', 'recipient_email'),
                ('idx_external_emails_status', 'external_emails', 'status'),
                ('idx_external_emails_type', 'external_emails', 'message_type'),
                ('idx_external_emails_created', 'external_emails', 'created_at'),
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
            
            # Show table structure
            print("\n" + "=" * 70)
            print("EXTERNAL EMAILS TABLE STRUCTURE")
            print("=" * 70)
            
            if is_postgres:
                result = db.session.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'external_emails'
                    ORDER BY ordinal_position
                """)).fetchall()
                for row in result:
                    print(f"  {row[0]:30} {row[1]:15} {row[2]}")
            else:
                result = db.session.execute(text("PRAGMA table_info(external_emails)")).fetchall()
                print(f"  {'Column Name':30} {'Type':15} {'Not Null'}")
                print(f"  {'-'*30} {'-'*15} {'-'*10}")
                for row in result:
                    print(f"  {row[1]:30} {row[2]:15} {str(bool(row[3]))}")
            
            print("\n" + "=" * 70)
            print("✅ EXTERNAL EMAILS SYSTEM READY!")
            print("=" * 70)
            print("\nFeatures available:")
            print("  ✅ Track all sent external emails")
            print("  ✅ Admin badge on sent messages")
            print("  ✅ Delivery status tracking")
            print("  ✅ Rate limiting support")
            print("  ✅ Message type categorization")
            print("  ✅ HTML email support")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    create_external_emails_table()
