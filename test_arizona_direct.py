"""
Test Arizona-specific scraper
"""
import sys
sys.path.insert(0, '/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE')

from national_scrapers.arizona_scraper import ArizonaScraper

print("Testing Arizona State Portal Scraper...")
print("=" * 60)

scraper = ArizonaScraper()
print(f"Base URL: {scraper.BASE_URL}")
print(f"Search URL: {scraper.SEARCH_URL}")

print("\nScraping Arizona state portal...")
try:
    az_contracts = scraper.scrape()
    print(f"✅ Found {len(az_contracts)} opportunities")
    
    if az_contracts:
        print("\nFirst 3 results:")
        for i, contract in enumerate(az_contracts[:3], 1):
            print(f"\n  {i}. {contract['title'][:70]}")
            print(f"     Sol #: {contract['solicitation_number']}")
            print(f"     Agency: {contract.get('agency', 'N/A')}")
            print(f"     Due: {contract.get('due_date', 'N/A')}")
            print(f"     Link: {contract.get('link', 'N/A')[:60]}")
    else:
        print("\n⚠️  No cleaning-related opportunities found")
        print("This could mean:")
        print("  1. No active janitorial/custodial RFPs right now")
        print("  2. Portal structure changed (need to update selectors)")
        print("  3. Portal is blocking requests")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
