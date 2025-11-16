#!/usr/bin/env python3
"""
Test All Scrapers
Comprehensive testing of all procurement scrapers
"""

import sys
import time
from scrapers.scraper_manager import get_scraper_manager

def test_scrapers():
    """Test all scrapers and save results to database"""
    
    print("=" * 80)
    print("SCRAPER TEST SUITE")
    print("=" * 80)
    print()
    
    manager = get_scraper_manager()
    
    print("Available Scrapers:")
    for i, name in enumerate(manager.scrapers.keys(), 1):
        print(f"  {i}. {name}")
    print()
    
    # Test individual scrapers
    print("=" * 80)
    print("TESTING INDIVIDUAL SCRAPERS")
    print("=" * 80)
    print()
    
    results = {}
    
    for scraper_name in manager.scrapers.keys():
        print(f"\n{'='*60}")
        print(f"Testing: {scraper_name}")
        print(f"{'='*60}\n")
        
        result = manager.run_scraper(scraper_name, save_to_db=True)
        results[scraper_name] = result
        
        if result.get('success'):
            print(f"✅ SUCCESS")
            print(f"   Contracts Found: {result.get('contracts_found', 0)}")
            print(f"   Contracts Saved: {result.get('contracts_saved', 0)}")
            print(f"   Duration: {result.get('duration_seconds', 0):.2f}s")
        else:
            print(f"❌ FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Brief pause between scrapers
        time.sleep(2)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    total_found = sum(r.get('contracts_found', 0) for r in results.values() if r.get('success'))
    total_saved = sum(r.get('contracts_saved', 0) for r in results.values() if r.get('success'))
    successful = sum(1 for r in results.values() if r.get('success'))
    failed = len(results) - successful
    
    print(f"Scrapers Run: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total Contracts Found: {total_found}")
    print(f"Total Contracts Saved: {total_saved}")
    print()
    
    # Get scraper stats
    print("=" * 80)
    print("SCRAPER STATISTICS")
    print("=" * 80)
    print()
    
    stats = manager.get_scraper_stats()
    
    for scraper_name, stat in stats.items():
        print(f"\n{scraper_name}:")
        print(f"  Total Runs: {stat.get('total_runs', 0)}")
        print(f"  Successful: {stat.get('successful_runs', 0)}")
        print(f"  Failed: {stat.get('failed_runs', 0)}")
        print(f"  Total Contracts Saved: {stat.get('total_contracts_saved', 0)}")
        print(f"  Last Run: {stat.get('last_run_at', 'Never')}")
    
    # Check database
    print("\n" + "=" * 80)
    print("DATABASE CHECK")
    print("=" * 80)
    print()
    
    import sqlite3
    
    try:
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM contracts")
        contract_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contracts WHERE data_source IS NOT NULL")
        contracts_with_source = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT data_source, COUNT(*) as count
            FROM contracts
            WHERE data_source IS NOT NULL
            GROUP BY data_source
        """)
        by_source = cursor.fetchall()
        
        conn.close()
        
        print(f"Total Contracts in Database: {contract_count}")
        print(f"Contracts with Data Source: {contracts_with_source}")
        print()
        
        if by_source:
            print("Contracts by Source:")
            for source, count in by_source:
                print(f"  {source}: {count}")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    
    return total_saved > 0


def main():
    """Main entry point"""
    try:
        success = test_scrapers()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
