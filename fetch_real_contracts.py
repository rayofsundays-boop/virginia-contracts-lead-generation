#!/usr/bin/env python3
"""
Script to fetch real federal contracts from SAM.gov API
and populate the database.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask app and database
from app import app, db
from sqlalchemy import text

def fetch_real_contracts():
    """Fetch real contracts from SAM.gov API"""
    print("🚀 Fetching real federal contracts from SAM.gov API...")
    print(f"📡 API Key: {os.environ.get('SAM_GOV_API_KEY', 'NOT SET')[:20]}...")
    
    try:
        from sam_gov_fetcher import SAMgovFetcher
        
        with app.app_context():
            fetcher = SAMgovFetcher()
            
            # Fetch nationwide cleaning contracts (last 30 days)
            print("🔍 Searching for nationwide cleaning contracts...")
            contracts = fetcher.fetch_us_cleaning_contracts(days_back=30)
            
            if not contracts:
                print("⚠️  No contracts found from SAM.gov API")
                print("   This could mean:")
                print("   1. No cleaning contracts in selected states within the last 30 days")
                print("   2. API key is invalid")
                print("   3. API rate limit reached")
                return False
            
            print(f"✅ Found {len(contracts)} contracts from SAM.gov")
            
            # Insert contracts into database
            inserted = 0
            skipped = 0
            
            for contract in contracts:
                try:
                    db.session.execute(text('''
                        INSERT INTO federal_contracts 
                        (title, agency, department, location, value, deadline, description, 
                         naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                        VALUES (:title, :agency, :department, :location, :value, :deadline, 
                                :description, :naics_code, :sam_gov_url, :notice_id, 
                                :set_aside, :posted_date)
                        ON CONFLICT (notice_id) DO NOTHING
                    '''), contract)
                    inserted += 1
                except Exception as e:
                    print(f"⚠️  Error inserting contract {contract.get('notice_id')}: {e}")
                    skipped += 1
                    continue
            
            db.session.commit()
            
            # Get total count
            total = db.session.execute(text('SELECT COUNT(*) FROM federal_contracts')).scalar()
            
            print(f"\n✅ Successfully fetched real federal contracts!")
            print(f"   Inserted: {inserted} new contracts")
            print(f"   Skipped: {skipped} (duplicates or errors)")
            print(f"   Total in database: {total} contracts")
            print("\n🎉 Database updated with real SAM.gov data!")
            print("   Refresh your federal contracts page to see real opportunities.")
            
            return True
            
    except ImportError as e:
        print(f"❌ Error importing SAMgovFetcher: {e}")
        print("   Make sure sam_gov_fetcher.py exists and has the SAMgovFetcher class")
        return False
    except Exception as e:
        print(f"❌ Error fetching contracts: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    fetch_real_contracts()
