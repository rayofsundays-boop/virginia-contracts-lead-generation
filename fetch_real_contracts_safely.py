"""
Fetch real SAM.gov contracts with careful rate limiting
Stays well under API limits with delays between requests
"""
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

# Import app context
from app import app, db
from sqlalchemy import text

# Import SAM.gov fetcher
from sam_gov_fetcher import SAMgovFetcher

def fetch_real_contracts_safely():
    """Fetch real contracts with extra safety margins on rate limits"""
    print("🔐 Checking SAM.gov API key...")
    api_key = os.environ.get('SAM_GOV_API_KEY', '').strip()
    
    if not api_key:
        print("❌ No SAM_GOV_API_KEY found in environment")
        return
    
    print(f"✅ API key found: {api_key[:20]}...")
    print("\n🛡️  RATE LIMIT PROTECTION ENABLED:")
    print("   - Max 2 pages per NAICS code (reduced from default)")
    print("   - 2-3 second delays between requests")
    print("   - Exponential backoff on errors (capped at 60s)")
    print("   - Total: ~3 NAICS codes × 2 pages = 6 API calls max")
    print()
    
    # Set environment variable to limit pages
    os.environ['SAM_MAX_PAGES_PER_NAICS'] = '2'
    
    with app.app_context():
        try:
            print("📡 Starting SAM.gov fetch with rate limit protection...\n")
            
            # Initialize fetcher
            fetcher = SAMgovFetcher()
            
            # Fetch with reduced lookback (less data = fewer pages)
            print("🔍 Searching last 14 days only (minimal data)...")
            contracts = fetcher.fetch_us_cleaning_contracts(days_back=14)
            
            if not contracts:
                print("\n⚠️  No contracts found in last 14 days")
                print("   This could mean:")
                print("   - No new VA cleaning contracts posted recently")
                print("   - API key issues")
                print("   - Rate limiting (though we have protections)")
                return
            
            print(f"\n✅ Successfully fetched {len(contracts)} contracts!")
            print("\n💾 Inserting into database...")
            
            # Clear sample data first
            deleted = db.session.execute(text('''
                DELETE FROM federal_contracts WHERE notice_id LIKE 'SAMPLE-%'
            ''')).rowcount
            
            if deleted > 0:
                print(f"   Removed {deleted} sample contracts")
            
            # Insert real contracts
            new_count = 0
            updated_count = 0
            
            for contract in contracts:
                try:
                    # Check if exists
                    existing = db.session.execute(text('''
                        SELECT id FROM federal_contracts WHERE notice_id = :notice_id
                    '''), {'notice_id': contract['notice_id']}).fetchone()
                    
                    if existing:
                        # Update existing
                        db.session.execute(text('''
                            UPDATE federal_contracts SET
                                title = :title,
                                agency = :agency,
                                location = :location,
                                value = :value,
                                deadline = :deadline,
                                description = :description
                            WHERE notice_id = :notice_id
                        '''), contract)
                        updated_count += 1
                    else:
                        # Insert new
                        db.session.execute(text('''
                            INSERT INTO federal_contracts 
                            (title, agency, department, location, value, deadline, description, 
                             naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                            VALUES (:title, :agency, :department, :location, :value, :deadline, 
                                    :description, :naics_code, :sam_gov_url, :notice_id, 
                                    :set_aside, :posted_date)
                        '''), contract)
                        new_count += 1
                        
                except Exception as e:
                    print(f"   ⚠️  Error with contract {contract.get('notice_id')}: {e}")
                    continue
            
            db.session.commit()
            
            print(f"\n✅ Database updated successfully!")
            print(f"   - New contracts: {new_count}")
            print(f"   - Updated contracts: {updated_count}")
            print(f"   - Total contracts now: {new_count + updated_count}")
            
            # Show sample
            if new_count > 0:
                print("\n📋 Sample of new contracts:")
                for i, contract in enumerate(contracts[:3], 1):
                    print(f"   {i}. {contract['title'][:60]}...")
                    print(f"      Agency: {contract['agency']}")
                    print(f"      Location: {contract['location']}")
                    print(f"      Value: {contract.get('value', 'Not specified')}")
                    print()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("=" * 70)
    print("SAM.GOV REAL CONTRACT FETCHER (RATE-LIMITED)")
    print("=" * 70)
    print()
    
    fetch_real_contracts_safely()
    
    print("\n" + "=" * 70)
    print("✅ Done! Refresh your federal contracts page to see real data.")
    print("=" * 70)
