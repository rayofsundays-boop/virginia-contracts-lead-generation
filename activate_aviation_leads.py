"""
Activate all aviation leads in the database
Ensures is_active is set to TRUE for all leads
"""
from app import app, db
from sqlalchemy import text

def activate_all_aviation_leads():
    with app.app_context():
        try:
            # Check current status
            result = db.session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN is_active = FALSE OR is_active IS NULL THEN 1 ELSE 0 END) as inactive
                FROM aviation_cleaning_leads
            """)).fetchone()
            
            print(f"\n📊 Current Status:")
            print(f"   Total leads: {result[0]}")
            print(f"   Active: {result[1]}")
            print(f"   Inactive: {result[2]}")
            
            # Activate all leads
            update_result = db.session.execute(text("""
                UPDATE aviation_cleaning_leads 
                SET is_active = TRUE 
                WHERE is_active = FALSE OR is_active IS NULL
            """))
            db.session.commit()
            
            updated_count = update_result.rowcount
            print(f"\n✅ Updated {updated_count} leads to active status")
            
            # Verify
            active_count = db.session.execute(text("""
                SELECT COUNT(*) FROM aviation_cleaning_leads WHERE is_active = TRUE
            """)).scalar()
            
            print(f"✅ Total active leads now: {active_count}")
            
            # Show sample
            print(f"\n📋 Sample leads:")
            samples = db.session.execute(text("""
                SELECT company_name, city, state, is_active 
                FROM aviation_cleaning_leads 
                LIMIT 5
            """)).fetchall()
            
            for s in samples:
                print(f"   • {s[0]} - {s[1]}, {s[2]} (Active: {s[3]})")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    activate_all_aviation_leads()
