"""
Add reset_token and reset_token_expires columns to leads table
Run this once to enable self-service password resets
"""

from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Check if columns already exist
        check = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='leads' AND column_name='reset_token'
        """)).fetchone()
        
        if not check:
            print("Adding reset_token columns to leads table...")
            
            db.session.execute(text("""
                ALTER TABLE leads 
                ADD COLUMN IF NOT EXISTS reset_token TEXT,
                ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP
            """))
            
            db.session.commit()
            print("✅ Successfully added reset_token columns!")
        else:
            print("✅ reset_token columns already exist")
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
