#!/usr/bin/env python3
"""
Check contracts table for fake/demo data
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

with app.app_context():
    print("=" * 80)
    print("CHECKING CONTRACTS TABLE (Local/State Government Contracts)")
    print("=" * 80)
    
    # Count total contracts
    total = db.session.execute(text('''
        SELECT COUNT(*) FROM contracts
    ''')).scalar() or 0
    
    print(f"\n📊 Total contracts in database: {total}")
    
    if total > 0:
        print("\n📋 First 10 contracts:")
        print("-" * 80)
        
        contracts = db.session.execute(text('''
            SELECT id, title, agency, location, value, deadline, website_url, created_at
            FROM contracts 
            ORDER BY created_at DESC
            LIMIT 10
        ''')).fetchall()
        
        for i, contract in enumerate(contracts, 1):
            print(f"\n{i}. {contract.title}")
            print(f"   Agency: {contract.agency}")
            print(f"   Location: {contract.location}")
            print(f"   Value: ${contract.value:,}" if contract.value else "   Value: N/A")
            print(f"   Deadline: {contract.deadline}" if contract.deadline else "   Deadline: N/A")
            print(f"   URL: {contract.website_url}" if contract.website_url else "   URL: None")
            print(f"   Created: {contract.created_at}")
        
        # Check for potential fake indicators
        print("\n" + "=" * 80)
        print("CHECKING FOR FAKE DATA INDICATORS")
        print("=" * 80)
        
        # Check for demo/test/fake in titles
        fake_titles = db.session.execute(text('''
            SELECT COUNT(*) FROM contracts 
            WHERE LOWER(title) LIKE '%demo%' 
               OR LOWER(title) LIKE '%test%' 
               OR LOWER(title) LIKE '%fake%'
               OR LOWER(title) LIKE '%sample%'
        ''')).scalar() or 0
        
        print(f"\n⚠️  Contracts with demo/test/fake/sample in title: {fake_titles}")
        
        # Check for Norfolk Scope (known fake)
        norfolk = db.session.execute(text('''
            SELECT COUNT(*) FROM contracts 
            WHERE LOWER(title) LIKE '%norfolk scope%'
        ''')).scalar() or 0
        
        print(f"⚠️  Norfolk Scope contracts: {norfolk}")
        
        # Check for Recreation Centers (had broken URL)
        recreation = db.session.execute(text('''
            SELECT COUNT(*) FROM contracts 
            WHERE LOWER(title) LIKE '%recreation center%'
        ''')).scalar() or 0
        
        print(f"⚠️  Recreation center contracts: {recreation}")
        
        # Show all unique agencies
        print("\n📍 All agencies in database:")
        agencies = db.session.execute(text('''
            SELECT DISTINCT agency FROM contracts 
            WHERE agency IS NOT NULL 
            ORDER BY agency
        ''')).fetchall()
        
        for agency in agencies:
            print(f"   - {agency[0]}")
    
    else:
        print("\n✅ Table is EMPTY - no fake data!")
        print("\nTo populate with REAL data:")
        print("1. Use web scrapers for VA city procurement sites")
        print("2. Import from SAM.gov API (federal only)")
        print("3. Manual entry from verified sources")
    
    print("\n" + "=" * 80)
