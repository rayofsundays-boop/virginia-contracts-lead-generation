"""
Direct SQL update to fix SAM.gov URLs for test contracts
"""
from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Updating SAM.gov URLs...")
    
    # Update all contracts to have the default cleaning services search URL
    result = db.session.execute(text("""
        UPDATE federal_contracts 
        SET sam_gov_url = 'https://sam.gov/search/?index=opp&page=1&naics=561720&sort=-relevance'
    """))
    
    db.session.commit()
    
    print(f"✅ Updated all contracts with proper SAM.gov search URLs")
    
    # Verify the update
    contracts = db.session.execute(text("""
        SELECT notice_id, sam_gov_url FROM federal_contracts LIMIT 5
    """)).fetchall()
    
    print("\nSample URLs:")
    for contract in contracts:
        print(f"  {contract[0]}: {contract[1][:80]}...")
