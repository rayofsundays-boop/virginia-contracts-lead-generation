#!/usr/bin/env python3
"""
Ensure aviation_cleaning_leads table exists on production PostgreSQL
Run this on Render.com to fix the Internal Server Error
"""

from app import app, db
from sqlalchemy import text

def ensure_aviation_table_postgres():
    """Create aviation_cleaning_leads table if it doesn't exist"""
    with app.app_context():
        try:
            print("🔍 Checking if aviation_cleaning_leads table exists...")
            
            # Check if table exists
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'aviation_cleaning_leads'
                )
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ Table already exists")
                
                # Check row count
                result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads'))
                count = result.scalar()
                print(f"📊 Current records: {count}")
                
                return True
            
            print("⚠️  Table does not exist. Creating now...")
            
            # Create table with PostgreSQL syntax
            db.session.execute(text("""
                CREATE TABLE aviation_cleaning_leads (
                    id SERIAL PRIMARY KEY,
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
                    UNIQUE(company_name, city, state)
                )
            """))
            db.session.commit()
            
            print("✅ Table created successfully")
            
            # Verify creation
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'aviation_cleaning_leads'
                )
            """))
            verified = result.scalar()
            
            if verified:
                print("✅ Table creation verified")
                return True
            else:
                print("❌ Table creation failed verification")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("="*60)
    print("🛫 AVIATION TABLE SETUP FOR PRODUCTION")
    print("="*60)
    
    success = ensure_aviation_table_postgres()
    
    if success:
        print("\n✅ Aviation table is ready!")
        print("🌐 Visit /aviation-cleaning-leads to verify")
    else:
        print("\n❌ Setup failed. Check errors above.")
    
    print("="*60)
