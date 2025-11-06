#!/usr/bin/env python3
"""
Fix broken contract URLs - Remove contracts with NULL or invalid URLs
This script connects to the production database and removes contracts with broken URLs
"""

import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment or use local
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("⚠️  DATABASE_URL not set - using local database")
    DATABASE_URL = 'sqlite:///leads.db'
else:
    print(f"✅ Using production database")
    # Fix postgres:// to postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create engine
engine = create_engine(DATABASE_URL)

def check_contracts():
    """Check all contracts for broken URLs"""
    with engine.connect() as conn:
        # Get all contracts
        result = conn.execute(text('''
            SELECT id, title, agency, location, website_url 
            FROM contracts 
            ORDER BY id
        '''))
        
        contracts = result.fetchall()
        
        print(f"\n📊 Total contracts in database: {len(contracts)}")
        print("=" * 80)
        
        if len(contracts) == 0:
            print("✅ No contracts found - database is clean")
            return
        
        broken_urls = []
        null_urls = []
        valid_urls = []
        
        for contract in contracts:
            contract_id, title, agency, location, url = contract
            
            print(f"\nID: {contract_id}")
            print(f"Title: {title}")
            print(f"Agency: {agency}")
            print(f"Location: {location}")
            print(f"URL: {url}")
            
            if url is None or url == '':
                print("❌ Status: NULL/EMPTY URL")
                null_urls.append(contract_id)
            elif 'http' not in url.lower():
                print("❌ Status: INVALID URL (no http)")
                broken_urls.append(contract_id)
            elif url.startswith('http://example.com') or url.startswith('https://example.com'):
                print("❌ Status: PLACEHOLDER URL (example.com)")
                broken_urls.append(contract_id)
            else:
                print("✅ Status: APPEARS VALID")
                valid_urls.append(contract_id)
            
            print("-" * 80)
        
        print(f"\n📈 SUMMARY:")
        print(f"Valid URLs: {len(valid_urls)}")
        print(f"NULL/Empty URLs: {len(null_urls)}")
        print(f"Broken/Invalid URLs: {len(broken_urls)}")
        
        return null_urls, broken_urls

def remove_broken_contracts(null_urls, broken_urls):
    """Remove contracts with NULL or broken URLs"""
    all_broken = null_urls + broken_urls
    
    if len(all_broken) == 0:
        print("\n✅ No broken contracts to remove")
        return
    
    print(f"\n⚠️  Found {len(all_broken)} contracts with broken/NULL URLs")
    print(f"IDs to remove: {all_broken}")
    
    confirm = input("\n❓ Remove these contracts? Type 'DELETE' to confirm: ")
    
    if confirm != 'DELETE':
        print("❌ Deletion cancelled")
        return
    
    with engine.connect() as conn:
        # Begin transaction
        trans = conn.begin()
        try:
            for contract_id in all_broken:
                result = conn.execute(text('''
                    DELETE FROM contracts WHERE id = :id
                '''), {'id': contract_id})
                print(f"✅ Deleted contract ID {contract_id}")
            
            trans.commit()
            print(f"\n✅ Successfully deleted {len(all_broken)} contracts")
            
            # Check remaining count
            result = conn.execute(text('SELECT COUNT(*) FROM contracts'))
            remaining = result.scalar()
            print(f"📊 Remaining contracts: {remaining}")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error during deletion: {e}")
            raise

if __name__ == '__main__':
    print("🔍 Checking contracts for broken URLs...")
    
    result = check_contracts()
    
    if result:
        null_urls, broken_urls = result
        remove_broken_contracts(null_urls, broken_urls)
    
    print("\n✅ Script complete!")
