"""
DEPRECATED - Old 50-State Scraper System
=========================================

These scrapers have been replaced by the new National Procurement Engine.

OLD APPROACH (DEPRECATED):
- 50+ individual state scrapers
- Separate scraper for each state portal
- High maintenance burden
- Difficult to keep URLs updated
- Many broken scrapers (404s, 403s)

NEW APPROACH (national_scrapers/):
- 7 unified scrapers covering all states
- Symphony: 28 states
- DemandStar: Thousands of local governments
- BidExpress: Multi-state platform
- COMMBUYS: Massachusetts
- eMaryland: Maryland
- NewHampshire: New Hampshire
- RhodeIsland: Rhode Island

MIGRATION GUIDE:
================

Old import:
    from scrapers.state_portal_scraper_v2 import StatePortalScraperV2

New import:
    from national_scrapers import (
        SymphonyScraper,
        DemandStarScraper,
        BidExpressScraper,
        COMBUYSScraper,
        EMarylandScraper,
        NewHampshireScraper,
        RhodeIslandScraper
    )

Or use the unified engine:
    from national_engine import NationalProcurementScraper
    
    scraper = NationalProcurementScraper()
    contracts = scraper.run_all()

FILES IN THIS FOLDER:
- base_scraper.py (replaced by national_scrapers/base_scraper.py)
- state_portal_scraper.py (old version)
- state_portal_scraper_v2.py (replaced by Symphony/DemandStar/etc)
- eva_virginia_scraper.py (old version)
- eva_virginia_scraper_v2.py (replaced by DemandStar or Symphony)

DO NOT USE THESE FILES.
They are kept for reference only.

Use national_engine.py for all procurement scraping.
"""
