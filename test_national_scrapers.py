"""
Quick Test Script for National Procurement Scrapers
Tests each scraper individually and shows sample results
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from national_scrapers import (
    SymphonyScraper,
    DemandStarScraper,
    BidExpressScraper,
    COMBUYSScraper,
    EMarylandScraper,
    NewHampshireScraper,
    RhodeIslandScraper
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_scraper(name: str, scraper, *args, **kwargs):
    """
    Test a single scraper and display results.
    
    Args:
        name: Scraper name
        scraper: Scraper instance
        *args, **kwargs: Arguments to pass to scraper.scrape()
    """
    print("\n" + "=" * 80)
    print(f"Testing {name} Scraper")
    print("=" * 80)
    
    try:
        contracts = scraper.scrape(*args, **kwargs)
        print(f"✅ {name}: Found {len(contracts)} cleaning-related opportunities")
        
        if contracts:
            print(f"\nFirst 3 results from {name}:")
            for i, contract in enumerate(contracts[:3], 1):
                print(f"\n  #{i}")
                print(f"    State: {contract['state']}")
                print(f"    Title: {contract['title'][:70]}...")
                print(f"    Sol #: {contract['solicitation_number']}")
                print(f"    Due: {contract.get('due_date', 'N/A')}")
                print(f"    Agency: {contract.get('agency', 'N/A')[:50]}")
                print(f"    Link: {contract.get('link', 'N/A')[:70]}...")
        else:
            print(f"⚠️  {name} returned 0 results (may need attention)")
        
        return True, len(contracts)
        
    except Exception as e:
        print(f"❌ {name} FAILED: {e}")
        logger.exception(f"Error in {name}")
        return False, 0


def main():
    """
    Run quick tests on all 7 scrapers.
    """
    print("\n" + "=" * 80)
    print("NATIONAL PROCUREMENT SCRAPER - QUICK TEST")
    print("=" * 80)
    print("\nTesting all 7 scraper sources...\n")
    
    results = {}
    
    # Test 1: Symphony (just a few states for speed)
    results['symphony'] = test_scraper(
        'Symphony',
        SymphonyScraper(),
        states=['CA', 'TX', 'NY']  # Test 3 major states
    )
    
    # Test 2: DemandStar (limited results)
    results['demandstar'] = test_scraper(
        'DemandStar',
        DemandStarScraper(),
        limit=100  # Limit for faster testing
    )
    
    # Test 3: BidExpress
    results['bidexpress'] = test_scraper(
        'BidExpress',
        BidExpressScraper()
    )
    
    # Test 4: COMMBUYS (MA)
    results['commbuys'] = test_scraper(
        'COMMBUYS',
        COMBUYSScraper()
    )
    
    # Test 5: eMaryland
    results['emaryland'] = test_scraper(
        'eMaryland',
        EMarylandScraper()
    )
    
    # Test 6: New Hampshire
    results['newhampshire'] = test_scraper(
        'New Hampshire',
        NewHampshireScraper()
    )
    
    # Test 7: Rhode Island
    results['rhodeisland'] = test_scraper(
        'Rhode Island',
        RhodeIslandScraper()
    )
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_success = sum(1 for success, _ in results.values() if success)
    total_contracts = sum(count for _, count in results.values())
    
    print(f"\nScrapers Tested: {len(results)}")
    print(f"Successful: {total_success}/{len(results)}")
    print(f"Total Contracts Found: {total_contracts}")
    
    print("\nBy Source:")
    for source, (success, count) in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {source:20s}: {count:4d} opportunities")
    
    if total_success == len(results):
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {len(results) - total_success} scraper(s) need attention")
    
    print("=" * 80 + "\n")
    
    return total_contracts > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
