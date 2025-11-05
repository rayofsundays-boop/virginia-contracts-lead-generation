#!/usr/bin/env python3
"""
Delete Demo/Fake Local & State Government Contracts
====================================================

This script removes all demo/test/fake contracts from the production database.

Run on Render:
1. Open Render Shell for your web service
2. Run: python delete_demo_contracts.py
3. Verify: Check /contracts page - should only show real contracts

Identifies fake contracts by:
- Placeholder agencies (e.g., "Example Agency", "Test City", "Demo Department")
- Fake websites (test.com, example.com, fake.com, demo.com)
- Sample/demo in title or description
- Placeholder values ($XX,XXX, $TBD, N/A)
"""

import os
from app import app, db
from sqlalchemy import text

def delete_demo_contracts():
    """Delete all demo/fake contracts from the database"""
    
    with app.app_context():
        print("🔍 Searching for demo/fake contracts...")
        
        # Patterns that indicate fake/demo data
        fake_patterns = [
            # Fake agencies
            "agency ILIKE '%example%'",
            "agency ILIKE '%test%'",
            "agency ILIKE '%demo%'",
            "agency ILIKE '%sample%'",
            "agency ILIKE '%placeholder%'",
            
            # Fake titles
            "title ILIKE '%example%'",
            "title ILIKE '%test%'",
            "title ILIKE '%demo%'",
            "title ILIKE '%sample%'",
            
            # Fake websites
            "website_url ILIKE '%example.com%'",
            "website_url ILIKE '%test.com%'",
            "website_url ILIKE '%fake.com%'",
            "website_url ILIKE '%demo.com%'",
            "website_url ILIKE '%placeholder%'",
            
            # Fake descriptions
            "description ILIKE '%lorem ipsum%'",
            "description ILIKE '%sample%'",
            "description ILIKE '%placeholder%'",
            
            # Fake locations
            "location ILIKE '%example%'",
            "location ILIKE '%test city%'",
            "location ILIKE '%demo%'"
        ]
        
        # Build WHERE clause
        where_clause = " OR ".join(fake_patterns)
        
        # First, count how many will be deleted
        count_query = f"SELECT COUNT(*) FROM contracts WHERE {where_clause}"
        count = db.session.execute(text(count_query)).scalar()
        
        if count == 0:
            print("✅ No demo/fake contracts found!")
            return
        
        print(f"⚠️  Found {count} demo/fake contracts")
        
        # Show what will be deleted
        preview_query = f"""
        SELECT id, title, agency, location, website_url 
        FROM contracts 
        WHERE {where_clause}
        LIMIT 10
        """
        
        print("\n📋 Preview of contracts to be deleted:")
        print("-" * 80)
        preview = db.session.execute(text(preview_query)).fetchall()
        for row in preview:
            print(f"ID {row[0]}: {row[1]}")
            print(f"  Agency: {row[2]}")
            print(f"  Location: {row[3]}")
            print(f"  URL: {row[4]}")
            print()
        
        if count > 10:
            print(f"... and {count - 10} more")
        
        print("-" * 80)
        print(f"\n⚠️  About to DELETE {count} contracts")
        
        # In production, we auto-confirm. For manual runs, uncomment the confirmation:
        # confirm = input("Type 'DELETE' to confirm: ")
        # if confirm != 'DELETE':
        #     print("❌ Deletion cancelled")
        #     return
        
        # Delete the fake contracts
        delete_query = f"DELETE FROM contracts WHERE {where_clause}"
        result = db.session.execute(text(delete_query))
        db.session.commit()
        
        deleted = result.rowcount
        print(f"\n✅ Successfully deleted {deleted} demo/fake contracts")
        
        # Show remaining contracts count
        remaining = db.session.execute(text("SELECT COUNT(*) FROM contracts")).scalar()
        print(f"📊 Remaining contracts: {remaining}")
        
        if remaining > 0:
            print("\n📋 Sample of remaining contracts:")
            print("-" * 80)
            sample_query = """
            SELECT id, title, agency, location 
            FROM contracts 
            ORDER BY created_at DESC 
            LIMIT 5
            """
            sample = db.session.execute(text(sample_query)).fetchall()
            for row in sample:
                print(f"ID {row[0]}: {row[1]}")
                print(f"  Agency: {row[2]}, Location: {row[3]}\n")

if __name__ == '__main__':
    print("=" * 80)
    print("DELETE DEMO/FAKE CONTRACTS")
    print("=" * 80)
    print()
    
    delete_demo_contracts()
    
    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print("\n✅ Next: Visit your site and check /contracts page")
    print("   Should only show real Virginia government contracts\n")
