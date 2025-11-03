"""
Check what's actually in the sam_gov_url column
"""
from app import app, db
from sqlalchemy import text

with app.app_context():
    contracts = db.session.execute(text("""
        SELECT id, notice_id, naics_code, sam_gov_url 
        FROM federal_contracts 
        ORDER BY id
        LIMIT 10
    """)).fetchall()
    
    print("Current SAM.gov URLs in database:")
    print("-" * 100)
    for contract in contracts:
        print(f"ID: {contract[0]:<5} | Notice: {contract[1]:<20} | NAICS: {contract[2]:<10} | URL: {contract[3]}")
