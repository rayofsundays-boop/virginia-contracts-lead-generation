"""
Fix SAM.gov URLs for existing federal contracts
"""
import os
from app import app, db
from sqlalchemy import text

def fix_sam_urls():
    """Update all federal contracts with proper SAM.gov search URLs"""
    with app.app_context():
        print("🔧 Fixing SAM.gov URLs for existing contracts...")
        
        # Get all contracts
        contracts = db.session.execute(text('''
            SELECT id, naics_code FROM federal_contracts
        ''')).fetchall()
        
        print(f"Found {len(contracts)} contracts to update")
        
        updated = 0
        for contract in contracts:
            contract_id = contract[0]
            naics_code = contract[1] if contract[1] else ''
            
            # Create proper SAM.gov URL
            if naics_code and naics_code != 'None' and naics_code.strip():
                sam_url = f'https://sam.gov/search/?index=opp&page=1&naics={naics_code}&sort=-relevance'
            else:
                # Default to general cleaning services
                sam_url = 'https://sam.gov/search/?index=opp&page=1&naics=561720&sort=-relevance'
            
            # Update the contract
            db.session.execute(text('''
                UPDATE federal_contracts 
                SET sam_gov_url = :url 
                WHERE id = :id
            '''), {'url': sam_url, 'id': contract_id})
            
            updated += 1
            if updated % 10 == 0:
                print(f"  Updated {updated} contracts...")
        
        db.session.commit()
        print(f"✅ Successfully updated {updated} contracts with proper SAM.gov URLs")

if __name__ == '__main__':
    fix_sam_urls()
