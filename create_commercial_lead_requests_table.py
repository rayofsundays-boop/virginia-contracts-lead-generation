#!/usr/bin/env python3
"""
Create commercial_lead_requests table if it doesn't exist.
Run this on Render to fix the missing table error.
"""

from app import app, db
from sqlalchemy import text

def create_commercial_lead_requests_table():
    """Create the commercial_lead_requests table"""
    with app.app_context():
        try:
            print("🔧 Creating commercial_lead_requests table...")
            
            db.session.execute(text('''
                CREATE TABLE IF NOT EXISTS commercial_lead_requests
                (id SERIAL PRIMARY KEY,
                 business_name TEXT NOT NULL,
                 contact_name TEXT NOT NULL,
                 email TEXT NOT NULL,
                 phone TEXT NOT NULL,
                 address TEXT NOT NULL,
                 city TEXT NOT NULL,
                 state TEXT DEFAULT 'VA',
                 zip_code TEXT,
                 business_type TEXT NOT NULL,
                 square_footage INTEGER,
                 frequency TEXT NOT NULL,
                 services_needed TEXT NOT NULL,
                 special_requirements TEXT,
                 budget_range TEXT,
                 start_date DATE,
                 urgency TEXT DEFAULT 'normal',
                 status TEXT DEFAULT 'open',
                 bid_count INTEGER DEFAULT 0,
                 winning_bid_id INTEGER,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
            '''))
            
            db.session.commit()
            print("✅ Table created successfully!")
            
            # Verify it was created
            result = db.session.execute(text('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'commercial_lead_requests'
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
    create_commercial_lead_requests_table()
