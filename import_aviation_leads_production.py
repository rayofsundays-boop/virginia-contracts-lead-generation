#!/usr/bin/env python3
"""
Import aviation leads to production database
Run this on Render.com
"""

import json
from app import app, db
from sqlalchemy import text

def import_aviation_leads():
    with app.app_context():
        # 1. Ensure table exists
        print("🔍 Creating table if not exists...")
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS aviation_cleaning_leads (
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
            print("✅ Table ready")
        except Exception as e:
            print(f"⚠️  Table check: {e}")
            db.session.rollback()
        
        # 2. Load JSON data
        print("📂 Loading aviation leads from JSON...")
        with open('aviation_leads_export_20251115_085502.json', 'r') as f:
            leads = json.load(f)
        
        print(f"📊 Found {len(leads)} leads to import")
        
        # 3. Insert leads
        inserted = 0
        skipped = 0
        
        for lead in leads:
            try:
                db.session.execute(text("""
                    INSERT INTO aviation_cleaning_leads
                    (company_name, company_type, aircraft_types, fleet_size,
                     city, state, address, contact_name, contact_title,
                     contact_email, contact_phone, website_url, services_needed,
                     estimated_monthly_value, current_contract_status, notes,
                     data_source, is_active)
                    VALUES
                    (:company_name, :company_type, :aircraft_types, :fleet_size,
                     :city, :state, :address, :contact_name, :contact_title,
                     :contact_email, :contact_phone, :website_url, :services_needed,
                     :estimated_monthly_value, :current_contract_status, :notes,
                     :data_source, :is_active)
                    ON CONFLICT (company_name, city, state) DO NOTHING
                """), lead)
                inserted += 1
                if inserted % 10 == 0:
                    print(f"  ✅ Imported {inserted} leads...")
            except Exception as e:
                skipped += 1
                print(f"  ⚠️  Skipped 1 lead: {e}")
        
        db.session.commit()
        
        print(f"\n✅ Import complete!")
        print(f"   Inserted: {inserted}")
        print(f"   Skipped: {skipped}")
        
        # 4. Verify
        result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads'))
        total = result.scalar()
        print(f"   Total in database: {total}")

if __name__ == '__main__':
    import_aviation_leads()
