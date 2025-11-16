"""
Quick test to verify Arizona scraping works
"""
import sys
sys.path.insert(0, '/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE')

from national_scrapers import SymphonyScraper

print("Testing Arizona (AZ) scraping...")
print("=" * 60)

scraper = SymphonyScraper()
print(f"Symphony states: {list(scraper.SYMPHONY_STATES.keys())}")
print(f"AZ in list: {'AZ' in scraper.SYMPHONY_STATES}")

# Test Arizona specifically
print("\nScraping Arizona opportunities...")
try:
    az_contracts = scraper.scrape(states=['AZ'])
    print(f"✅ Found {len(az_contracts)} opportunities for Arizona")
    
    if az_contracts:
        print("\nFirst 3 results:")
        for i, contract in enumerate(az_contracts[:3], 1):
            print(f"\n  {i}. {contract['title'][:70]}")
            print(f"     State: {contract['state']}")
            print(f"     Agency: {contract.get('agency', 'N/A')}")
            print(f"     Link: {contract.get('link', 'N/A')[:60]}")
    else:
        print("⚠️  No results found - this is why users see 'No RFPs' message")
        print("Possible reasons:")
        print("  1. Symphony portal is down")
        print("  2. No active cleaning RFPs right now")
        print("  3. HTML structure changed (selectors need update)")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
