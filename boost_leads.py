#!/usr/bin/env python3
"""
Quick Lead Boost Script
Manually fetch more federal contracts with expanded parameters
"""

import os
import sys
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import the fetcher
from sam_gov_fetcher import SAMgovFetcher

def boost_federal_leads():
    """Fetch more federal contracts with new expanded settings"""
    
    print("=" * 70)
    print("🚀 QUICK LEAD BOOST - Fetching More Federal Contracts")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv('SAM_GOV_API_KEY', '')
    if not api_key:
        print("\n❌ No SAM_GOV_API_KEY found!")
        print("📝 Get free key at: https://open.gsa.gov/api/sam-gov-entity-api/")
        return
    
    print(f"\n✅ API Key found: {api_key[:15]}...")
    
    # Initialize fetcher
    fetcher = SAMgovFetcher()
    
    print(f"\n📊 Fetcher Configuration:")
    print(f"   • NAICS Codes: {len(fetcher.naics_codes)} categories")
    print(f"   • Lookback Window: 90 days")
    print(f"   • Target States: {len(fetcher.target_states)} states configured")
    print(f"   • Max Retries: 3 attempts before Data.gov fallback")
    print(f"   • Expected: 60-120 new contracts")
    
    print("\n🔍 Fetching contracts from SAM.gov...")
    print("   (May take 2-3 minutes due to API rate limiting)")
    print("   (Will automatically switch to Data.gov if SAM.gov fails)")
    
    try:
        # Fetch contracts nationwide (will auto-fallback to Data.gov if needed)
        contracts = fetcher.fetch_us_cleaning_contracts(days_back=90)
        
        if not contracts:
            print("\n⚠️  No contracts found")
            print("   Possible reasons:")
            print("   1. API key may be invalid")
            print("   2. Rate limit reached")
            print("   3. No contracts in this timeframe")
            return
        
        print(f"\n✅ Found {len(contracts)} contracts from SAM.gov!")
        
        # Connect to database
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        # Check for existing contracts
        cursor.execute("SELECT COUNT(*) FROM federal_contracts")
        before_count = cursor.fetchone()[0]
        
        # Insert contracts
        inserted = 0
        skipped = 0
        
        for contract in contracts:
            try:
                # Check if contract already exists
                cursor.execute(
                    "SELECT id FROM federal_contracts WHERE notice_id = ?",
                    (contract['notice_id'],)
                )
                
                if cursor.fetchone():
                    skipped += 1
                    continue
                
                # Insert new contract
                cursor.execute('''
                    INSERT INTO federal_contracts 
                    (title, agency, department, location, value, deadline, description,
                     naics_code, sam_gov_url, notice_id, set_aside, posted_date, data_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    contract['title'],
                    contract['agency'],
                    contract.get('department', ''),
                    contract['location'],
                    contract['value'],
                    contract['deadline'],
                    contract['description'],
                    contract['naics_code'],
                    contract['sam_gov_url'],
                    contract['notice_id'],
                    contract.get('set_aside', ''),
                    contract['posted_date'],
                    'SAM.gov API'
                ))
                
                inserted += 1
                
            except Exception as e:
                print(f"   ⚠️  Error inserting contract: {e}")
                continue
        
        conn.commit()
        
        # Get final count
        cursor.execute("SELECT COUNT(*) FROM federal_contracts")
        after_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ LEAD BOOST COMPLETE!")
        print("=" * 70)
        print(f"\n📊 Results:")
        print(f"   • Fetched from SAM.gov: {len(contracts)} contracts")
        print(f"   • New contracts added: {inserted}")
        print(f"   • Duplicates skipped: {skipped}")
        print(f"   • Before: {before_count} federal contracts")
        print(f"   • After: {after_count} federal contracts")
        print(f"   • Growth: +{after_count - before_count} contracts ({((after_count - before_count) / before_count * 100) if before_count > 0 else 0:.0f}% increase)")
        
        if inserted > 0:
            print("\n🎉 Success! Your federal contracts page now has more opportunities.")
            print("   View them at: http://localhost:5000/federal-contracts")
        else:
            print("\n✅ Database is up to date - no new contracts found in this timeframe")
        
        print("\n💡 Tips to get even more leads:")
        print("   1. Run this script daily for fresh contracts")
        print("   2. Check LEAD_GENERATION_STRATEGY.md for 10 more tactics")
        print("   3. Consider expanding to Maryland/DC (+300% more contracts)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    boost_federal_leads()
