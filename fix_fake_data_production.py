#!/usr/bin/env python3
"""
Fix Fake Data Issue on Production
Identifies and removes all fake/demo/synthetic data that keeps reappearing
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def investigate_fake_data():
    """Check what fake data exists in the database"""
    with app.app_context():
        print("=" * 80)
        print("🔍 INVESTIGATING FAKE DATA IN DATABASE")
        print("=" * 80)
        
        # Check supply_contracts for fake data
        print("\n📦 SUPPLY CONTRACTS:")
        print("-" * 80)
        
        try:
            total = db.session.execute(text('SELECT COUNT(*) FROM supply_contracts')).fetchone()[0]
            print(f"Total supply contracts: {total}")
            
            if total > 0:
                # Check for placeholder URLs
                fake_urls = db.session.execute(text("""
                    SELECT COUNT(*) FROM supply_contracts 
                    WHERE website_url LIKE '%vacontractshub.com%' 
                    OR website_url LIKE '%placeholder%'
                    OR website_url IS NULL
                    OR website_url = ''
                """)).fetchone()[0]
                print(f"Contracts with fake/placeholder URLs: {fake_urls}")
                
                # Check for common fake patterns
                fake_agencies = db.session.execute(text("""
                    SELECT COUNT(*) FROM supply_contracts 
                    WHERE agency LIKE '%Commercial Properties%'
                    OR agency LIKE '%State Facility%'
                    OR title LIKE '%Bulk Supplier Request%'
                """)).fetchone()[0]
                print(f"Contracts with fake agency patterns: {fake_agencies}")
                
                # Show examples
                examples = db.session.execute(text("""
                    SELECT title, agency, website_url, posted_date 
                    FROM supply_contracts 
                    LIMIT 10
                """)).fetchall()
                
                print("\n📋 Sample records:")
                for ex in examples:
                    print(f"\n  Title: {ex[0]}")
                    print(f"  Agency: {ex[1]}")
                    print(f"  URL: {ex[2]}")
                    print(f"  Posted: {ex[3]}")
                    
        except Exception as e:
            print(f"Error checking supply_contracts: {e}")
        
        # Check federal_contracts
        print("\n\n🏛️ FEDERAL CONTRACTS:")
        print("-" * 80)
        
        try:
            total = db.session.execute(text('SELECT COUNT(*) FROM federal_contracts')).fetchone()[0]
            print(f"Total federal contracts: {total}")
            
            if total > 0:
                # Check data source distribution
                sources = db.session.execute(text("""
                    SELECT data_source, COUNT(*) as count 
                    FROM federal_contracts 
                    GROUP BY data_source
                """)).fetchall()
                
                print("\n📊 Data sources:")
                for source, count in sources:
                    print(f"  {source or 'Unknown'}: {count}")
                
                # Check for fake patterns
                no_urls = db.session.execute(text("""
                    SELECT COUNT(*) FROM federal_contracts 
                    WHERE sam_gov_url IS NULL OR sam_gov_url = ''
                """)).fetchone()[0]
                print(f"\nContracts without URLs: {no_urls}")
                
        except Exception as e:
            print(f"Error checking federal_contracts: {e}")
        
        # Check contracts (local)
        print("\n\n🏢 LOCAL CONTRACTS:")
        print("-" * 80)
        
        try:
            total = db.session.execute(text('SELECT COUNT(*) FROM contracts')).fetchone()[0]
            print(f"Total local contracts: {total}")
            
            if total > 0:
                # Check for fake URLs
                fake_urls = db.session.execute(text("""
                    SELECT COUNT(*) FROM contracts 
                    WHERE website_url LIKE '%vacontractshub.com%'
                    OR website_url LIKE '%placeholder%'
                    OR website_url LIKE '%example.com%'
                """)).fetchone()[0]
                print(f"Contracts with fake URLs: {fake_urls}")
                
        except Exception as e:
            print(f"Error checking contracts: {e}")

def delete_all_fake_supply_data():
    """Delete ALL supply contracts (they're being repopulated with fake data)"""
    with app.app_context():
        try:
            count = db.session.execute(text('SELECT COUNT(*) FROM supply_contracts')).fetchone()[0]
            
            if count == 0:
                print("✅ No supply contracts to delete")
                return
            
            print(f"\n⚠️  About to DELETE all {count} supply contracts")
            print("    (They will be repopulated with REAL data from SAM.gov API)")
            confirm = input("    Type 'YES' to confirm: ")
            
            if confirm != 'YES':
                print("❌ Cancelled")
                return
            
            db.session.execute(text('DELETE FROM supply_contracts'))
            db.session.commit()
            
            print(f"✅ Deleted all {count} supply contracts")
            print("\n💡 Next steps:")
            print("   1. Make sure SAM_GOV_API_KEY is set on Render")
            print("   2. Restart the app to trigger auto-population with REAL data")
            print("   3. Or visit /admin/repopulate-supply-contracts")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

def check_startup_auto_populate():
    """Check if the app is auto-populating fake data on startup"""
    print("\n" + "=" * 80)
    print("🔍 CHECKING AUTO-POPULATE BEHAVIOR")
    print("=" * 80)
    
    print("\n📝 Looking for auto-populate code in app.py...")
    
    with open('app.py', 'r') as f:
        content = f.read()
        
        # Check if populate_supply_contracts is being called on startup
        if 'populate_supply_contracts' in content:
            print("✅ Found populate_supply_contracts function")
            
            # Check if it's using SAM.gov API
            if 'SAM_GOV_API_KEY' in content:
                print("✅ Function uses SAM.gov API")
            else:
                print("⚠️  Function might not be using real API")
            
            # Check for synthetic data generation
            if 'supplier_requests = [' in content:
                print("⚠️  WARNING: Found synthetic data array in code!")
                print("    This is generating fake data!")
            else:
                print("✅ No synthetic data array found")
    
    # Check for other scripts that might add fake data
    print("\n📝 Checking for other data generation scripts...")
    
    scripts_to_check = [
        'add_supplier_requests.py',
        'populate_federal_contracts.py',
        'quick_populate.py',
        'remove_demo_data.py'
    ]
    
    for script in scripts_to_check:
        if os.path.exists(script):
            print(f"  ⚠️  Found: {script}")
            print(f"      This script might be adding fake data!")
        else:
            print(f"  ✅ Not found: {script}")

if __name__ == '__main__':
    print("\n🔧 VA CONTRACTS - FAKE DATA INVESTIGATION & FIX")
    print("=" * 80)
    
    # Run investigation
    investigate_fake_data()
    
    # Check startup behavior
    check_startup_auto_populate()
    
    print("\n" + "=" * 80)
    print("🛠️  RECOMMENDED ACTIONS:")
    print("=" * 80)
    print("1. Delete ALL supply contracts (they're fake)")
    print("2. Rename/delete add_supplier_requests.py (generates fake data)")
    print("3. Set SAM_GOV_API_KEY on Render")
    print("4. Restart app to fetch REAL data from SAM.gov")
    print("=" * 80)
    
    # Offer to delete
    print("\n❓ Would you like to delete all supply contracts now? (y/n): ", end='')
    response = input().lower()
    
    if response == 'y':
        delete_all_fake_supply_data()
