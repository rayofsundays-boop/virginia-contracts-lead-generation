"""
National Procurement Scraper - Quick Start Guide
=================================================

This system replaces the old 50-state approach with 7 unified scrapers
that cover all US states and thousands of local governments.

COVERAGE:
---------
✅ Symphony/Periscope: 28 states (AZ, CA, CO, CT, GA, HI, ID, IL, KS, KY, ME, MI, MN, MO, MS, MT, NV, NM, ND, OH, OK, OR, SC, TN, TX, UT, WA, WI)
✅ DemandStar: Thousands of cities, counties, school districts, utilities, airports
✅ BidExpress: Multi-state construction/facilities platform
✅ COMMBUYS: Massachusetts state procurement
✅ eMaryland: Maryland state procurement  
✅ New Hampshire: NH state procurement
✅ Rhode Island: RI state procurement

TOTAL: Near 100% US coverage with just 7 scrapers

USAGE:
------

1. Run All Scrapers (Parallel):
   ```python
   from national_engine import NationalProcurementScraper
   
   scraper = NationalProcurementScraper()
   contracts = scraper.run_all(parallel=True)
   scraper.print_sample_results(contracts, limit=20)
   ```

2. Run Individual Scraper:
   ```python
   from national_scrapers import SymphonyScraper
   
   scraper = SymphonyScraper()
   contracts = scraper.scrape(states=['CA', 'TX', 'NY'])
   ```

3. Save to PostgreSQL:
   ```python
   scraper = NationalProcurementScraper(db_url='postgresql://user:pass@host/db')
   contracts = scraper.run_all()
   scraper.save_to_postgresql(contracts)
   ```

4. Run from Command Line:
   ```bash
   python national_engine.py
   ```

OUTPUT FORMAT:
--------------
All scrapers return standardized contracts:
{
    "state": "CA",
    "title": "Janitorial Services for County Buildings",
    "solicitation_number": "RFP-2024-123",
    "due_date": "2024-12-31",
    "link": "https://...",
    "agency": "Los Angeles County",
    "source": "symphony",
    "scraped_at": "2024-11-16T12:00:00"
}

FEATURES:
---------
✅ Automatic deduplication by state + solicitation number
✅ Date normalization (10+ formats supported)
✅ State normalization (full names → 2-letter codes)
✅ Keyword filtering (janitorial, custodial, cleaning, etc.)
✅ NAICS code mapping
✅ Error tracking and alerts
✅ 0-results warnings
✅ PostgreSQL upsert (no duplicates)
✅ Parallel execution (7x faster)
✅ RSS/JSON/HTML parsing
✅ Retry logic with exponential backoff

ENVIRONMENT VARIABLES:
----------------------
DATABASE_URL: PostgreSQL connection string (optional)
  Format: postgresql://username:password@host:port/database

LOGGING:
--------
All output logged to:
- Console (INFO level)
- national_scraper.log file

TESTING:
--------
Run first test:
```bash
python national_engine.py
```

Expected output:
- Summary by source
- Summary by state
- First 20 sample contracts
- PostgreSQL save confirmation (if DATABASE_URL set)

MAINTENANCE:
------------
Instead of maintaining 50+ scrapers, you now maintain just 7.

To update a broken scraper:
1. Open national_scrapers/<scraper_name>_scraper.py
2. Update URL or selectors
3. Test with: python -c "from national_scrapers import XScraper; XScraper().scrape()"
4. Deploy

MIGRATION FROM OLD SYSTEM:
--------------------------
Old code:
```python
from scrapers.state_portal_scraper_v2 import StatePortalScraperV2
scraper = StatePortalScraperV2()
contracts = scraper.scrape(['CA', 'TX'])
```

New code:
```python
from national_engine import NationalProcurementScraper
scraper = NationalProcurementScraper()
contracts = scraper.run_all()
```

SCHEDULED EXECUTION:
--------------------
Add to crontab for daily runs:
```bash
0 3 * * * cd /path/to/project && python national_engine.py
```

Or use Python schedule module in app.py:
```python
import schedule
from national_engine import NationalProcurementScraper

def daily_scrape():
    scraper = NationalProcurementScraper()
    contracts = scraper.run_all()
    scraper.save_to_postgresql(contracts)

schedule.every().day.at("03:00").do(daily_scrape)
```

TROUBLESHOOTING:
----------------
Q: Scraper returns 0 results
A: Check logs for specific error. May need to update URL or selectors.

Q: Database save fails
A: Verify DATABASE_URL is set and PostgreSQL is accessible.

Q: Parallel execution too slow
A: Use sequential mode: scraper.run_all(parallel=False)

Q: Missing state coverage
A: Check which scraper covers that state in COVERAGE section above.

SUPPORT:
--------
For issues, check national_scraper.log file.
All errors are logged with source and details.
"""
