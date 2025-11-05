#!/usr/bin/env python3
"""
Check and fix the website URL for Recreation Centers Network Cleaning Contract
Contract ID: VA-LOCAL-00112
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def check_recreation_centers_contract():
    """Check the Recreation Centers Network Cleaning Contract"""
    with app.app_context():
        try:
            print("=" * 80)
            print("🔍 CHECKING: Recreation Centers Network Cleaning Contract")
            print("=" * 80)
            
            # Search for this contract by title
            result = db.session.execute(text("""
                SELECT id, title, agency, location, value, deadline, description, 
                       naics_code, website_url, created_at
                FROM contracts 
                WHERE title LIKE '%Recreation Centers%'
                OR title LIKE '%VA-LOCAL-00112%'
                LIMIT 5
            """)).fetchall()
            
            if not result:
                print("\n❌ Contract not found in database")
                print("   This might be on Render PostgreSQL only")
                print("\n💡 To check on Render:")
                print("   1. Go to Render Dashboard → Web Service → Shell")
                print("   2. Run: psql $DATABASE_URL")
                print("   3. Run: SELECT title, website_url FROM contracts WHERE title LIKE '%Recreation Centers%';")
                return
            
            print(f"\n✅ Found {len(result)} matching contract(s):\n")
            
            for contract in result:
                print(f"ID: {contract[0]}")
                print(f"Title: {contract[1]}")
                print(f"Agency: {contract[2]}")
                print(f"Location: {contract[3]}")
                print(f"Value: {contract[4]}")
                print(f"Deadline: {contract[5]}")
                print(f"NAICS: {contract[7]}")
                print(f"Website URL: {contract[8] or 'NULL/MISSING'}")
                print(f"Created: {contract[9]}")
                print(f"\nDescription: {contract[6][:200]}...")
                print("\n" + "-" * 80 + "\n")
                
                # Check if URL is missing or invalid
                website_url = contract[8]
                if not website_url or website_url == 'NULL' or website_url.strip() == '':
                    print(f"⚠️  WARNING: Contract ID {contract[0]} has NO website URL")
                    print("   This is correct - local government contracts may not have direct URLs")
                    print("   Users should contact the agency directly using phone/email")
                elif 'vacontractshub.com' in website_url or 'placeholder' in website_url:
                    print(f"❌ FAKE URL DETECTED: {website_url}")
                    print(f"   Contract ID: {contract[0]}")
                    print("   This should be fixed or set to NULL")
                else:
                    print(f"✅ Website URL looks valid: {website_url}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

def suggest_fix():
    """Suggest how to fix missing/broken URLs"""
    print("\n" + "=" * 80)
    print("📝 HOW TO FIX MISSING/BROKEN WEBSITE URLS")
    print("=" * 80)
    
    print("""
    For LOCAL GOVERNMENT CONTRACTS (City/County):
    - These often don't have direct online URLs
    - Users should contact the procurement office directly
    - Phone/email contact info should be provided instead
    - Setting website_url to NULL is acceptable
    
    CORRECT APPROACH:
    - Display: "Contact Agency Directly"
    - Show: Phone number and email
    - Link: Agency's general procurement page (if available)
    
    EXAMPLE FIXES:
    
    1. Virginia Beach Parks & Recreation:
       - Website: https://www.vbgov.com/government/departments/parks-recreation
       - Procurement: https://www.vbgov.com/government/departments/finance/procurement
       - Phone: (757) 385-4621
    
    2. Hampton Parks & Recreation:
       - Website: https://hampton.gov/facilities
       - Procurement: https://www.hampton.gov/bids.aspx
       - Phone: (757) 727-6347
    
    3. Norfolk Parks & Recreation:
       - Website: https://www.norfolk.gov/2764/Parks-Recreation
       - Procurement: https://www.norfolk.gov/bids.aspx
       - Phone: (757) 664-4000
    
    TO UPDATE ON RENDER:
    ```sql
    -- Connect to database
    psql $DATABASE_URL
    
    -- Update Recreation Centers contract
    UPDATE contracts 
    SET website_url = 'https://www.vbgov.com/government/departments/parks-recreation'
    WHERE title LIKE '%Recreation Centers%';
    
    -- Verify update
    SELECT title, website_url FROM contracts WHERE title LIKE '%Recreation Centers%';
    ```
    """)

if __name__ == '__main__':
    check_recreation_centers_contract()
    suggest_fix()
