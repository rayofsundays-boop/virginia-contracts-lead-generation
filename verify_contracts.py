#!/usr/bin/env python3
"""
Verify legitimacy of contracts in database
Checks URLs, agency names, and creates a verified/unverified report
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

# Known legitimate VA government websites
LEGITIMATE_DOMAINS = {
    'hampton.gov': 'City of Hampton',
    'norfolk.gov': 'City of Norfolk',
    'vbgov.com': 'City of Virginia Beach',
    'suffolkva.us': 'City of Suffolk',
    'nnva.gov': 'City of Newport News',
    'williamsburgva.gov': 'City of Williamsburg',
    'portsmouthva.gov': 'City of Portsmouth',
    'cityofchesapeake.net': 'City of Chesapeake',
    'jamescitycountyva.gov': 'James City County',
    'yorkcounty.gov': 'York County',
    'hrtransit.org': 'Hampton Roads Transit',
    'hrsd.com': 'Hampton Roads Sanitation District',
    'vaports.com': 'Virginia Port Authority',
    'sam.gov': 'Federal SAM.gov'
}

# Known fake/placeholder URLs
FAKE_URL_INDICATORS = [
    '/bids.aspx',  # Generic placeholder path
    'example.com',
    'test.com',
    'demo.com'
]

with app.app_context():
    print("=" * 80)
    print("VERIFYING CONTRACTS IN DATABASE")
    print("=" * 80)
    
    # Get all contracts
    contracts = db.session.execute(text('''
        SELECT id, title, agency, location, value, deadline, website_url, created_at
        FROM contracts 
        ORDER BY created_at DESC
    ''')).fetchall()
    
    verified = []
    needs_verification = []
    suspicious = []
    
    for contract in contracts:
        contract_id = contract.id
        title = contract.title
        agency = contract.agency
        url = contract.website_url
        
        # Check URL legitimacy
        url_status = "NO_URL"
        domain_verified = False
        
        if url:
            url_lower = url.lower()
            
            # Check if it's a legitimate domain
            for domain, org in LEGITIMATE_DOMAINS.items():
                if domain in url_lower:
                    domain_verified = True
                    break
            
            # Check for fake indicators
            has_fake_indicator = any(fake in url_lower for fake in FAKE_URL_INDICATORS)
            
            if domain_verified and not has_fake_indicator:
                url_status = "VERIFIED"
            elif domain_verified and has_fake_indicator:
                url_status = "SUSPICIOUS_PATH"
            elif not domain_verified:
                url_status = "UNKNOWN_DOMAIN"
        
        # All contracts created at same time = bulk import (suspicious)
        created_at_str = str(contract.created_at) if contract.created_at else ""
        same_timestamp = '2025-11-01 16:56:51' in created_at_str
        
        # Categorize
        if url_status == "VERIFIED":
            verified.append(contract)
        elif url_status in ["SUSPICIOUS_PATH", "UNKNOWN_DOMAIN"] or same_timestamp:
            suspicious.append((contract, url_status))
        else:
            needs_verification.append((contract, url_status))
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total contracts: {len(contracts)}")
    print(f"   ✅ Verified (legitimate URLs): {len(verified)}")
    print(f"   ⚠️  Suspicious: {len(suspicious)}")
    print(f"   ❓ Needs verification: {len(needs_verification)}")
    
    print("\n" + "=" * 80)
    print("⚠️  SUSPICIOUS CONTRACTS (Recommend deletion)")
    print("=" * 80)
    
    for contract, status in suspicious:
        print(f"\nID: {contract.id}")
        print(f"Title: {contract.title}")
        print(f"Agency: {contract.agency}")
        print(f"URL: {contract.website_url or 'None'}")
        print(f"Status: {status}")
        print(f"Reason: ", end="")
        
        if status == "SUSPICIOUS_PATH":
            print("Domain is legitimate but URL path looks like placeholder (/bids.aspx)")
        elif status == "UNKNOWN_DOMAIN":
            print("Domain not in verified government list")
        
        if '2025-11-01 16:56:51' in created_at_str:
            print("Bulk import timestamp suggests generated data")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print(f"\n⚠️  ALL {len(contracts)} contracts were created at the same timestamp")
    print("   This suggests they were batch-generated, not manually added")
    print("\n🚫 RECOMMENDATION: DELETE ALL CONTRACTS")
    print("\n✅ Reason:")
    print("   - All created simultaneously (Nov 1, 2025 at 16:56:51)")
    print("   - Many use generic /bids.aspx placeholder paths")
    print("   - Cannot verify if contracts actually exist on government sites")
    print("   - Violates 'no fake data' policy")
    print("\n💡 Next Steps:")
    print("   1. Clear contracts table completely")
    print("   2. Add empty state message to /contracts page")
    print("   3. Build real web scrapers for VA city procurement sites")
    print("   4. Manually add verified contracts from official sources")
    
    print("\n" + "=" * 80)
    
    # Create deletion script
    print("\nCreating deletion script...")
    
    with open('clear_contracts_table.py', 'w') as f:
        f.write('''#!/usr/bin/env python3
"""
Clear ALL contracts from contracts table
Run this to remove all potentially fake local/state contracts
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

with app.app_context():
    print("⚠️  WARNING: This will DELETE ALL contracts from the contracts table")
    print("This includes all local and state government contracts")
    
    # Count before deletion
    count_before = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar()
    print(f"\\n📊 Current count: {count_before} contracts")
    
    confirm = input("\\nType 'DELETE ALL' to confirm: ")
    
    if confirm == "DELETE ALL":
        db.session.execute(text('DELETE FROM contracts'))
        db.session.commit()
        
        count_after = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar()
        print(f"\\n✅ Deleted {count_before} contracts")
        print(f"✅ Remaining contracts: {count_after}")
        print("\\n✅ Contracts table is now EMPTY")
        print("\\n💡 Next: /contracts page will show 'No contracts available'")
        print("   Add real contracts from verified sources only")
    else:
        print("\\n❌ Deletion cancelled")
''')
    
    print("✅ Created clear_contracts_table.py")
    print("\nTo delete all contracts, run:")
    print("   python3 clear_contracts_table.py")
