#!/usr/bin/env python3
"""
Deploy Aviation Leads to Production
1. Export local aviation leads to JSON
2. Instructions for uploading to production
"""

import json
from app import app, db
from sqlalchemy import text
from datetime import datetime

def export_aviation_leads():
    """Export aviation leads from local database to JSON"""
    with app.app_context():
        try:
            print("📤 Exporting aviation leads from local database...")
            
            result = db.session.execute(text("""
                SELECT company_name, company_type, aircraft_types, fleet_size,
                       city, state, address, contact_name, contact_title,
                       contact_email, contact_phone, website_url, services_needed,
                       estimated_monthly_value, current_contract_status, notes,
                       data_source, is_active
                FROM aviation_cleaning_leads
                WHERE is_active = 1
                ORDER BY company_name
            """))
            
            leads = []
            for row in result:
                leads.append({
                    'company_name': row[0],
                    'company_type': row[1],
                    'aircraft_types': row[2],
                    'fleet_size': row[3],
                    'city': row[4],
                    'state': row[5],
                    'address': row[6],
                    'contact_name': row[7],
                    'contact_title': row[8],
                    'contact_email': row[9],
                    'contact_phone': row[10],
                    'website_url': row[11],
                    'services_needed': row[12],
                    'estimated_monthly_value': row[13],
                    'current_contract_status': row[14],
                    'notes': row[15],
                    'data_source': row[16],
                    'is_active': row[17]
                })
            
            # Save to JSON
            filename = f'aviation_leads_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w') as f:
                json.dump(leads, f, indent=2)
            
            print(f"✅ Exported {len(leads)} leads to {filename}")
            print(f"\n📊 Summary:")
            print(f"   Total leads: {len(leads)}")
            
            # Count by type
            types = {}
            for lead in leads:
                comp_type = lead['company_type']
                types[comp_type] = types.get(comp_type, 0) + 1
            
            print(f"\n   By type:")
            for comp_type, count in types.items():
                print(f"   - {comp_type}: {count}")
            
            return filename
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            import traceback
            traceback.print_exc()
            return None

def generate_import_script(json_filename):
    """Generate Python script to import on production"""
    import_script = f'''#!/usr/bin/env python3
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
            print(f"⚠️  Table check: {{e}}")
            db.session.rollback()
        
        # 2. Load JSON data
        print("📂 Loading aviation leads from JSON...")
        with open('{json_filename}', 'r') as f:
            leads = json.load(f)
        
        print(f"📊 Found {{len(leads)}} leads to import")
        
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
                    print(f"  ✅ Imported {{inserted}} leads...")
            except Exception as e:
                skipped += 1
                print(f"  ⚠️  Skipped 1 lead: {{e}}")
        
        db.session.commit()
        
        print(f"\\n✅ Import complete!")
        print(f"   Inserted: {{inserted}}")
        print(f"   Skipped: {{skipped}}")
        
        # 4. Verify
        result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads'))
        total = result.scalar()
        print(f"   Total in database: {{total}}")

if __name__ == '__main__':
    import_aviation_leads()
'''
    
    script_filename = 'import_aviation_leads_production.py'
    with open(script_filename, 'w') as f:
        f.write(import_script)
    
    print(f"\n✅ Generated import script: {script_filename}")
    return script_filename

def main():
    print("="*70)
    print("🛫 AVIATION LEADS - PRODUCTION DEPLOYMENT")
    print("="*70)
    
    # Step 1: Export local data
    json_file = export_aviation_leads()
    
    if not json_file:
        print("\n❌ Export failed. Cannot proceed.")
        return
    
    # Step 2: Generate import script
    import_script = generate_import_script(json_file)
    
    # Step 3: Instructions
    print("\n" + "="*70)
    print("📝 DEPLOYMENT INSTRUCTIONS")
    print("="*70)
    print("\n1. Upload files to Render.com:")
    print(f"   - {json_file}")
    print(f"   - {import_script}")
    
    print("\n2. On Render.com Shell, run:")
    print(f"   python {import_script}")
    
    print("\n3. Verify at:")
    print("   https://virginia-contracts-lead-generation.onrender.com/aviation-cleaning-leads")
    
    print("\n" + "="*70)
    print("✅ READY FOR DEPLOYMENT")
    print("="*70)

if __name__ == '__main__':
    main()
