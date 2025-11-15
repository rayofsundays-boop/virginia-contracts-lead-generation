#!/usr/bin/env python3
"""
Production Error Diagnostic Tool
Run this on Render.com shell to diagnose aviation leads issues
"""

def diagnose_aviation_production():
    """Comprehensive diagnostic check for aviation leads"""
    print("="*70)
    print("🔍 AVIATION LEADS PRODUCTION DIAGNOSTIC")
    print("="*70)
    
    # Import inside function
    from app import app, db, DATABASE_URL
    from sqlalchemy import text
    import sys
    
    # Check database type
    def is_postgres():
        return DATABASE_URL and 'postgresql' in DATABASE_URL
    
    with app.app_context():
        print(f"\n1️⃣  Environment Check")
        print(f"   Python version: {sys.version}")
        print(f"   Database type: {'PostgreSQL' if is_postgres() else 'SQLite'}")
        print(f"   DATABASE_URL set: {'Yes' if DATABASE_URL else 'No'}")
        if DATABASE_URL:
            # Mask password in URL
            safe_url = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else '...'
            print(f"   Database host: {safe_url[:50]}")
        
        print(f"\n2️⃣  Table Existence Check")
        try:
            if is_postgres():
                result = db.session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'aviation_cleaning_leads'
                    )
                """))
                exists = result.scalar()
            else:
                result = db.session.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='aviation_cleaning_leads'
                """))
                exists = result.fetchone() is not None
            
            print(f"   ✅ aviation_cleaning_leads table exists: {exists}")
        except Exception as e:
            print(f"   ❌ Error checking table: {e}")
            exists = False
        
        if not exists:
            print("\n⚠️  TABLE MISSING - Run auto_import_aviation.py")
            return
        
        print(f"\n3️⃣  Data Count Check")
        try:
            result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads'))
            total = result.scalar()
            print(f"   Total records: {total}")
            
            result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads WHERE is_active = 1'))
            active = result.scalar()
            print(f"   Active records: {active}")
        except Exception as e:
            print(f"   ❌ Error counting records: {e}")
            return
        
        print(f"\n4️⃣  Sample Data Check")
        try:
            result = db.session.execute(text("""
                SELECT company_name, company_type, city, state 
                FROM aviation_cleaning_leads 
                WHERE is_active = 1 
                LIMIT 3
            """))
            
            print("   Sample leads:")
            for i, row in enumerate(result, 1):
                print(f"   {i}. {row[0][:40]} ({row[1]}) - {row[2]}, {row[3]}")
        except Exception as e:
            print(f"   ❌ Error fetching sample data: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print(f"\n5️⃣  Column Structure Check")
        try:
            if is_postgres():
                result = db.session.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'aviation_cleaning_leads'
                    ORDER BY ordinal_position
                """))
                print("   Table columns:")
                for row in result:
                    print(f"   - {row[0]}: {row[1]}")
            else:
                result = db.session.execute(text("PRAGMA table_info(aviation_cleaning_leads)"))
                print("   Table columns:")
                for row in result:
                    print(f"   - {row[1]}: {row[2]}")
        except Exception as e:
            print(f"   ⚠️  Could not check column structure: {e}")
        
        print(f"\n6️⃣  Route Test")
        try:
            # Simulate the route query
            query = "SELECT * FROM aviation_cleaning_leads WHERE is_active = 1 ORDER BY state, city, company_name"
            result = db.session.execute(text(query))
            rows = result.fetchall()
            print(f"   ✅ Query executed successfully")
            print(f"   Rows returned: {len(rows)}")
            
            if rows:
                row = rows[0]
                print(f"   First row columns: {len(row)}")
        except Exception as e:
            print(f"   ❌ Route query error: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n" + "="*70)
        print("✅ DIAGNOSTIC COMPLETE")
        print("="*70)
        
        if total > 0:
            print("\n✅ Aviation leads system appears healthy!")
            print("   If you're still seeing errors, check:")
            print("   1. Browser console for JavaScript errors")
            print("   2. Template file exists: templates/aviation_cleaning_leads.html")
            print("   3. User authentication is working")
            print("   4. Render logs for runtime errors")
        else:
            print("\n⚠️  Table exists but has no data")
            print("   Run: python run_real_aviation_scrapers.py")

if __name__ == '__main__':
    try:
        diagnose_aviation_production()
    except Exception as e:
        print(f"\n❌ DIAGNOSTIC FAILED: {e}")
        import traceback
        traceback.print_exc()
