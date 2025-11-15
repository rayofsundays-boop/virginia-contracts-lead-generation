#!/usr/bin/env python3
"""
Auto-import aviation leads on production startup
This runs automatically when the app starts if aviation table is empty
"""

import json
import os
from app import app, db
from sqlalchemy import text

def auto_import_aviation_leads():
    """Import aviation leads if table is empty"""
    with app.app_context():
        try:
            # Check if table exists and has data
            try:
                result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads'))
                count = result.scalar()
                
                if count > 0:
                    print(f"ℹ️  Aviation leads table already has {count} records - skipping import")
                    return
            except Exception:
                # Table doesn't exist, create it
                print("🔧 Creating aviation_cleaning_leads table...")
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
                print("✅ Table created")
            
            # Find JSON export file
            json_files = [f for f in os.listdir('.') if f.startswith('aviation_leads_export_') and f.endswith('.json')]
            
            if not json_files:
                print("⚠️  No aviation leads JSON file found - skipping import")
                return
            
            # Use most recent export
            json_file = sorted(json_files)[-1]
            
            print(f"📂 Importing aviation leads from {json_file}...")
            
            with open(json_file, 'r') as f:
                leads = json.load(f)
            
            inserted = 0
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
                except Exception as e:
                    print(f"  ⚠️  Skipped 1 lead: {str(e)[:50]}")
            
            db.session.commit()
            print(f"✅ Imported {inserted} aviation leads")
            
        except Exception as e:
            print(f"❌ Auto-import error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    auto_import_aviation_leads()
