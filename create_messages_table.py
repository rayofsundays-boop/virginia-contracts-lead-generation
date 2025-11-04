#!/usr/bin/env python3
"""
Create messages table if it doesn't exist.
Run this on Render to fix the missing table error.
"""

from app import app, db
from sqlalchemy import text

def create_messages_table():
    """Create the messages table for in-app messaging"""
    with app.app_context():
        try:
            print("🔧 Creating messages table...")
            
            db.session.execute(text('''
                CREATE TABLE IF NOT EXISTS messages
                (id SERIAL PRIMARY KEY,
                 sender_id INTEGER,
                 recipient_id INTEGER,
                 subject TEXT NOT NULL,
                 body TEXT NOT NULL,
                 is_read BOOLEAN DEFAULT FALSE,
                 is_admin BOOLEAN DEFAULT FALSE,
                 sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 read_at TIMESTAMP,
                 FOREIGN KEY (sender_id) REFERENCES leads(id),
                 FOREIGN KEY (recipient_id) REFERENCES leads(id))
            '''))
            
            # Create indexes for better query performance
            db.session.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_messages_recipient 
                ON messages(recipient_id)
            '''))
            
            db.session.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_messages_sender 
                ON messages(sender_id)
            '''))
            
            db.session.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_messages_is_read 
                ON messages(is_read)
            '''))
            
            db.session.commit()
            print("✅ Table created successfully!")
            
            # Verify it was created
            result = db.session.execute(text('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'messages'
                )
            ''')).scalar()
            
            if result:
                print("✅ Verified: Table exists in database")
            else:
                print("❌ Warning: Table may not have been created properly")
                
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_messages_table()
