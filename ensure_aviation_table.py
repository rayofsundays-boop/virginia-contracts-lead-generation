#!/usr/bin/env python3
"""
Ensure aviation_cleaning_leads table exists in production database
Run this script to create the table if it doesn't exist
"""

from app import app, db
from sqlalchemy import text

def ensure_aviation_table():
    """Create aviation_cleaning_leads table if it doesn't exist"""
    with app.app_context():
        try:
            print("🔍 Checking if aviation_cleaning_leads table exists...")
            
            # Try to query the table
            try:
                result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads'))
                count = result.scalar()
                print(f"✅ Table exists with {count} records")
                return
            except Exception:
                print("⚠️  Table doesn't exist, creating now...")
            
            # Create the table
            db.session.execute(text('''CREATE TABLE IF NOT EXISTS aviation_cleaning_leads
                     (id SERIAL PRIMARY KEY,
                      company_name TEXT NOT NULL,
                      company_type TEXT NOT NULL,
                      aircraft_types TEXT,
                      fleet_size INTEGER,
                      city TEXT NOT NULL,
                      state TEXT NOT NULL,
                      address TEXT,
                      contact_name TEXT,
                      contact_title TEXT,
                      contact_email TEXT,
                      contact_phone TEXT,
                      website_url TEXT,
                      services_needed TEXT,
                      estimated_monthly_value TEXT,
                      current_contract_status TEXT,
                      notes TEXT,
                      data_source TEXT,
                      discovered_via TEXT DEFAULT 'ai_scraper',
                      discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      last_verified TIMESTAMP,
                      is_active BOOLEAN DEFAULT TRUE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      UNIQUE(company_name, city, state))'''))
            
            # Create indexes
            db.session.execute(text('''CREATE INDEX IF NOT EXISTS idx_aviation_leads_state 
                                       ON aviation_cleaning_leads(state)'''))
            db.session.execute(text('''CREATE INDEX IF NOT EXISTS idx_aviation_leads_city 
                                       ON aviation_cleaning_leads(city)'''))
            db.session.execute(text('''CREATE INDEX IF NOT EXISTS idx_aviation_leads_type 
                                       ON aviation_cleaning_leads(company_type)'''))
            db.session.execute(text('''CREATE INDEX IF NOT EXISTS idx_aviation_leads_active 
                                       ON aviation_cleaning_leads(is_active)'''))
            
            db.session.commit()
            print("✅ Table and indexes created successfully")
            
            # Verify
            result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads'))
            count = result.scalar()
            print(f"✅ Table verified with {count} records")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    ensure_aviation_table()
