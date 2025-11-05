#!/usr/bin/env python3
"""
Fix Recreation Centers Network Cleaning Contract URL
Sets broken URL to NULL and displays proper contact information
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def fix_recreation_centers_url():
    """Fix the broken URL for Recreation Centers contract"""
    with app.app_context():
        try:
            print("=" * 80)
            print("🔧 FIXING: Recreation Centers Network Cleaning Contract URL")
            print("=" * 80)
            
            # Check current state
            print("\n📋 BEFORE UPDATE:")
            result = db.session.execute(text("""
                SELECT id, title, website_url
                FROM contracts 
                WHERE title LIKE '%Recreation Centers%'
            """)).fetchone()
            
            if not result:
                print("❌ Contract not found in local database")
                print("   This contract may only exist on Render PostgreSQL")
                print("\n💡 To fix on Render:")
                print("   1. Go to Render Dashboard → Web Service → Shell")
                print("   2. Run: psql $DATABASE_URL")
                print("   3. Run the following SQL:")
                print("\n   UPDATE contracts")
                print("   SET website_url = NULL")
                print("   WHERE title = 'Recreation Centers Network Cleaning Contract';")
                return False
            
            print(f"   ID: {result[0]}")
            print(f"   Title: {result[1]}")
            print(f"   Current URL: {result[2] or 'NULL'}")
            
            # Update the URL to NULL
            print("\n🔄 UPDATING URL TO NULL...")
            db.session.execute(text("""
                UPDATE contracts 
                SET website_url = NULL
                WHERE title LIKE '%Recreation Centers%'
            """))
            db.session.commit()
            
            # Verify the update
            print("\n✅ AFTER UPDATE:")
            result_after = db.session.execute(text("""
                SELECT id, title, website_url
                FROM contracts 
                WHERE title LIKE '%Recreation Centers%'
            """)).fetchone()
            
            print(f"   ID: {result_after[0]}")
            print(f"   Title: {result_after[1]}")
            print(f"   New URL: {result_after[2] or 'NULL (Contact Agency Directly)'}")
            
            print("\n" + "=" * 80)
            print("✅ SUCCESS: URL fixed in local database!")
            print("=" * 80)
            print("\n📝 What happens now:")
            print("   • Broken link removed")
            print("   • Users will see 'Contact Agency Directly' message")
            print("   • Phone number displayed: (757) 385-4621")
            print("   • Email displayed: parks@vbgov.com")
            print("\n⚠️  Remember to run the same fix on Render production database!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = fix_recreation_centers_url()
    
    if success:
        print("\n" + "=" * 80)
        print("📋 NEXT STEPS:")
        print("=" * 80)
        print("1. ✅ Local database updated")
        print("2. 🔄 Test the contract page locally: http://localhost:8080/contracts")
        print("3. 🚀 Run same fix on Render production:")
        print("   • Go to Render Dashboard → Web Service → Shell")
        print("   • Run: psql $DATABASE_URL")
        print("   • Run: UPDATE contracts SET website_url = NULL")
        print("           WHERE title = 'Recreation Centers Network Cleaning Contract';")
        print("4. ✅ Verify on production: https://virginia-contracts-lead-generation.onrender.com/contracts")
        print("=" * 80)
    else:
        print("\n⚠️  Fix could not be applied to local database")
        print("   Apply fix directly on Render production instead")
