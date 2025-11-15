#!/usr/bin/env python3
"""
Auto-import aviation leads on production startup
This runs automatically when the app starts if aviation table is empty
"""

import json
import os

def auto_import_aviation_leads():
    """Import aviation leads if table is empty"""
    # Import inside function to avoid circular import
    from app import app, db, DATABASE_URL
    from sqlalchemy import text
    
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
                
                # Detect database type for correct PRIMARY KEY syntax
                if DATABASE_URL and 'postgresql' in DATABASE_URL:
                    pk_syntax = 'id SERIAL PRIMARY KEY'
                else:
                    pk_syntax = 'id INTEGER PRIMARY KEY AUTOINCREMENT'
                
                create_sql = f"""
                    CREATE TABLE IF NOT EXISTS aviation_cleaning_leads (
                        {pk_syntax},
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
                """
                db.session.execute(text(create_sql))
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
                    # Convert is_active from integer (0/1) to boolean for PostgreSQL
                    lead_data = lead.copy()
                    if 'is_active' in lead_data:
                        lead_data['is_active'] = bool(lead_data['is_active'])
                    
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
                    """), lead_data)
                    db.session.commit()  # Commit each lead individually to avoid transaction rollback
                    inserted += 1
                except Exception as e:
                    db.session.rollback()  # Rollback failed insert
                    print(f"  ⚠️  Skipped 1 lead: {str(e)[:80]}")
            
            print(f"✅ Imported {inserted} aviation leads")
            
        except Exception as e:
            print(f"❌ Auto-import error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    auto_import_aviation_leads()
