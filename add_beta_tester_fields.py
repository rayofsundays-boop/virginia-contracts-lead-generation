"""
Add beta tester fields to leads table
Run this script to add the beta tester functionality
"""
from app import app, db
from sqlalchemy import text

def add_beta_tester_fields():
    with app.app_context():
        try:
            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(leads)")).fetchall()
            existing_columns = [row[1] for row in result]
            
            # Add is_beta_tester column if it doesn't exist
            if 'is_beta_tester' not in existing_columns:
                db.session.execute(text("ALTER TABLE leads ADD COLUMN is_beta_tester BOOLEAN DEFAULT FALSE"))
                print("✅ Added is_beta_tester column")
            else:
                print("ℹ️  is_beta_tester column already exists")
            
            # Add beta_expiry_date column if it doesn't exist
            if 'beta_expiry_date' not in existing_columns:
                db.session.execute(text("ALTER TABLE leads ADD COLUMN beta_expiry_date TIMESTAMP"))
                print("✅ Added beta_expiry_date column")
            else:
                print("ℹ️  beta_expiry_date column already exists")
            
            # Add beta_registered_at column if it doesn't exist
            if 'beta_registered_at' not in existing_columns:
                db.session.execute(text("ALTER TABLE leads ADD COLUMN beta_registered_at TIMESTAMP"))
                print("✅ Added beta_registered_at column")
            else:
                print("ℹ️  beta_registered_at column already exists")
            
            db.session.commit()
            print("✅ Successfully added beta tester fields to leads table")
            
            # Check current beta tester count
            count = db.session.execute(text("SELECT COUNT(*) FROM leads WHERE is_beta_tester = TRUE OR is_beta_tester = 1")).scalar()
            print(f"📊 Current beta testers: {count}/100")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    add_beta_tester_fields()
