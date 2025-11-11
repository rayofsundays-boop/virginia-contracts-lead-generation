"""
Test script to verify SAM.gov API and Local Government scrapers
Run this to test if data fetching works
"""
import os

print("=" * 60)
print("🧪 TESTING DATA SCRAPERS")
print("=" * 60)

# Test 1: Check environment variables
print("\n1️⃣ Checking Environment Variables...")
sam_api_key = os.environ.get('SAM_GOV_API_KEY', '')
if sam_api_key:
    print(f"   ✅ SAM_GOV_API_KEY is set ({len(sam_api_key)} chars)")
else:
    print("   ❌ SAM_GOV_API_KEY is NOT set")
    print("   📝 Get free key from: https://open.gsa.gov/api/sam-gov-entity-api/")

# Test 2: Test SAM.gov fetcher
print("\n2️⃣ Testing SAM.gov Federal Contracts Fetcher...")
try:
    from sam_gov_fetcher import SAMgovFetcher
    
    fetcher = SAMgovFetcher()
    contracts = fetcher.fetch_us_cleaning_contracts(days_back=30)
    
    if contracts:
        print(f"   ✅ Successfully fetched {len(contracts)} federal contracts")
        print(f"   📄 Sample contract: {contracts[0]['title'][:60]}...")
    else:
        print("   ⚠️  No contracts returned. Check API key or API status.")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Test local government scraper
print("\n3️⃣ Testing Virginia Local Government Scraper...")
try:
    from local_gov_scraper import VirginiaLocalGovScraper
    
    scraper = VirginiaLocalGovScraper()
    local_contracts = scraper.fetch_all_local_contracts()
    
    if local_contracts:
        print(f"   ✅ Successfully scraped {len(local_contracts)} local contracts")
        print(f"   📄 Sample contract: {local_contracts[0]['title'][:60]}...")
    else:
        print("   ⚠️  No local contracts found. Websites may have changed.")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ TESTING COMPLETE")
print("=" * 60)
print("\n💡 Next Steps:")
print("   1. If SAM_GOV_API_KEY is missing, add it to Render environment")
print("   2. If scrapers work locally, check Render deployment logs")
print("   3. Visit /init-db on your live site to manually initialize")
