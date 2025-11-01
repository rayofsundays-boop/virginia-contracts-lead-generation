#!/usr/bin/env python3
"""
Database Update Script
Run this to create/update database tables after schema changes
"""

import os
from app import app, db
from sqlalchemy import text

def run_database_updates():
    """Create or update all database tables"""
    with app.app_context():
        try:
            print("🔄 Starting database updates...\n")
            
            # Test connection
            result = db.session.execute(text("SELECT 1"))
            print("✅ Database connection successful\n")
            
            # Create residential_leads table
            print("📋 Creating/updating residential_leads table...")
            db.session.execute(text('''CREATE TABLE IF NOT EXISTS residential_leads
                         (id SERIAL PRIMARY KEY,
                          homeowner_name TEXT NOT NULL,
                          address TEXT NOT NULL,
                          city TEXT NOT NULL,
                          state TEXT DEFAULT 'VA',
                          zip_code TEXT,
                          property_type TEXT,
                          bedrooms INTEGER,
                          bathrooms DECIMAL(3,1),
                          square_footage INTEGER,
                          contact_email TEXT,
                          contact_phone TEXT,
                          estimated_value DECIMAL(12,2),
                          cleaning_frequency TEXT,
                          services_needed TEXT,
                          special_requirements TEXT,
                          status TEXT DEFAULT 'new',
                          source TEXT,
                          lead_quality TEXT,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
            db.session.commit()
            print("✅ residential_leads table ready\n")
            
            # Create commercial_lead_requests table
            print("📋 Creating/updating commercial_lead_requests table...")
            db.session.execute(text('''CREATE TABLE IF NOT EXISTS commercial_lead_requests
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
                          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
            db.session.commit()
            print("✅ commercial_lead_requests table ready\n")
            
            # Check table counts
            print("📊 Current table status:")
            
            try:
                count = db.session.execute(text("SELECT COUNT(*) FROM residential_leads")).scalar()
                print(f"   • Residential leads: {count}")
            except Exception as e:
                print(f"   • Residential leads: Error - {e}")
            
            try:
                count = db.session.execute(text("SELECT COUNT(*) FROM commercial_lead_requests")).scalar()
                print(f"   • Commercial requests: {count}")
            except Exception as e:
                print(f"   • Commercial requests: Error - {e}")
            
            try:
                count = db.session.execute(text("SELECT COUNT(*) FROM contracts")).scalar()
                print(f"   • Government contracts: {count}")
            except Exception as e:
                print(f"   • Government contracts: Error - {e}")
            
            try:
                count = db.session.execute(text("SELECT COUNT(*) FROM federal_contracts")).scalar()
                print(f"   • Federal contracts: {count}")
            except Exception as e:
                print(f"   • Federal contracts: Error - {e}")
            
            print("\n✅ Database update completed successfully!")
            print("\n🎉 You can now submit residential and commercial cleaning requests!")
            
        except Exception as e:
            print(f"\n❌ Error during database update: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    run_database_updates()
