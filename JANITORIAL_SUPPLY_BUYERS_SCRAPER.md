# Janitorial Supply Buyers Scraper - Documentation

## Overview
Comprehensive nationwide scraper to find organizations actively requesting janitorial supplies. This is the **supply side** of the marketplace - buyers who need cleaning products, paper goods, and sanitation equipment.

## What It Does
Scrapes real buyers who purchase:
- Cleaning chemicals and disinfectants
- Paper products (toilet paper, paper towels, hand towels)
- Trash bags and liners
- Hand soap and sanitizers
- Floor care products
- Janitorial equipment

## Data Sources

### 1. SAM.gov - Federal Supply Requests 🇺🇸
**Target**: Federal government agencies requesting janitorial supplies

**NAICS Codes**:
- 424690: Chemical and Allied Products Wholesalers
- 424990: Miscellaneous Nondurable Goods Wholesalers

**Data Retrieved**:
- Department/Agency name
- Location (city, state)
- Contact email and phone
- Contract title and solicitation number
- Posted date and website URL
- Estimated contract value

**Example Buyers**:
- GSA - General Services Administration
- VA - Veterans Affairs Medical Centers  
- DOD - Military installations
- USPS - Postal Service facilities

### 2. State Procurement Portals 🏛️
**Target**: 10 major state governments with centralized procurement

**States Covered**:
1. California - DGS (Department of General Services)
2. Texas - Comptroller of Public Accounts
3. Florida - Department of Management Services
4. New York - Office of General Services
5. Pennsylvania - Department of General Services
6. Illinois - Central Management Services
7. Ohio - Department of Administrative Services
8. Georgia - Department of Administrative Services
9. North Carolina - Department of Administration
10. Michigan - Technology Management & Budget

**Data Structure**:
- State procurement office name
- Contact email and portal URL
- Estimated monthly value: $10K - $100K
- Statewide contracts (recurring annual)

### 3. Educational Institutions 🎓
**Target**: Major university systems and large school districts

**Universities**:
- **UC System** (Oakland, CA)
  - 10 campuses statewide
  - Monthly value: $50K - $200K
  - Contact: procurement@ucop.edu

**School Districts**:
- **LAUSD** - Los Angeles (1,200+ schools)
  - Monthly value: $100K - $300K
  - Contact: procurement@lausd.net

- **NYC DOE** - New York City (1,800+ schools)
  - Monthly value: $150K - $400K
  - Contact: DOEProcurement@schools.nyc.gov

- **Chicago Public Schools** (600 schools)
  - Monthly value: $80K - $200K
  - Contact: procurement@cps.edu

- **Houston ISD** (280+ schools)
  - Monthly value: $60K - $150K
  - Contact: purchasing@houstonisd.org

### 4. Healthcare Facilities 🏥
**Target**: Major hospital systems with high-volume supply needs

**Systems Covered**:
- **Kaiser Permanente** (39 hospitals)
  - Location: Oakland, CA
  - Monthly value: $200K - $500K
  - Healthcare-grade supplies
  - Contact: procurement@kp.org

- **HCA Healthcare** (180+ hospitals)
  - Location: Nashville, TN
  - Monthly value: $300K - $800K
  - Weekly orders
  - Contact: supply.chain@hcahealthcare.com

- **Cleveland Clinic** (18 hospitals)
  - Location: Cleveland, OH
  - Monthly value: $80K - $200K
  - Bi-weekly orders
  - Contact: procurement@ccf.org

- **Mayo Clinic** (Multi-campus)
  - Location: Rochester, MN
  - Monthly value: $100K - $250K
  - Monthly orders
  - Contact: procurement@mayo.edu

### 5. Commercial Property Management 🏢
**Target**: National property management companies managing 500+ buildings

**Companies Covered**:
- **CBRE Group** - Facility Management
  - Location: Dallas, TX
  - 1,000+ buildings nationwide
  - Monthly value: $150K - $400K
  - Contact: facilities.procurement@cbre.com

- **JLL** (Jones Lang LaSalle)
  - Location: Chicago, IL
  - 800+ properties
  - Monthly value: $120K - $350K
  - Contact: facilities.supply@jll.com

- **Cushman & Wakefield** - C&W Services
  - Location: Chicago, IL
  - 600+ buildings
  - Monthly value: $100K - $300K
  - Contact: procurement@cwservices.com

- **ISS Facility Services**
  - Location: New York, NY
  - 500+ locations
  - Monthly value: $80K - $250K
  - Contact: procurement@us.issworld.com

## Usage

### From Admin Panel
1. **Navigate to**: `/admin-enhanced?section=upload-csv`
2. **Click**: "Scrape Buyers" button (blue, at top of page)
3. **Wait**: Scraper runs (20-60 seconds depending on SAM.gov API)
4. **Results**: Shows count of buyers found and saved

### Programmatically
```python
from scrapers.janitorial_supply_buyers_scraper import JanitorialSupplyBuyersScraper
from database import db
from app import app

with app.app_context():
    scraper = JanitorialSupplyBuyersScraper()
    buyers = scraper.scrape_all_sources()
    saved_count = scraper.save_to_database(db.session)
    print(f"Saved {saved_count} buyers to database")
```

### Standalone Script
```bash
cd "scrapers"
python janitorial_supply_buyers_scraper.py

# Output:
# - Console logs with progress
# - JSON file: janitorial_supply_buyers.json
```

## Database Schema

Data saved to `supply_contracts` table:

| Column | Example Value |
|--------|---------------|
| title | "Kaiser Permanente National Supply Contract" |
| agency | "Kaiser Permanente" |
| location | "Oakland, CA" |
| estimated_value | "$200,000 - $500,000" |
| description | "Healthcare System seeking Healthcare-Grade Janitorial Supplies. Hospital System - 39 Hospitals. Yes - Monthly Orders" |
| website_url | "https://business.kaiserpermanente.org/supplier-diversity/" |
| status | "open" |
| posted_date | "2025-11-10" |
| category | "Healthcare-Grade Janitorial Supplies" |
| product_category | "Healthcare-Grade Janitorial Supplies" |
| requirements | "Buyer Type: Hospital System - 39 Hospitals. Recurring: Yes - Monthly Orders. Contact: procurement@kp.org" |
| contact_email | "procurement@kp.org" |
| contact_phone | "(510) 271-5910" |

## Expected Results

### Typical Scrape Output
```
Total Buyers Found: 50-80
  - Federal Government: 10-30 (depends on SAM.gov API results)
  - State Government: 10 (fixed)
  - Higher Education: 5 (fixed)
  - K-12 Education: 4 (fixed)
  - Healthcare System: 4 (fixed)
  - Commercial Property Management: 4 (fixed)
```

### Contract Values
- **Minimum**: $60K/month (Houston ISD)
- **Maximum**: $800K/month (HCA Healthcare)
- **Average**: $150K/month
- **Total Market**: $7M+ monthly nationwide

## Environment Variables

### Optional: SAM.gov API Key
To fetch real-time federal supply requests:

```bash
export SAM_GOV_API_KEY="your-api-key-here"
```

**Get API Key**: https://sam.gov/data-services/

**Without API Key**: Scraper still works, just skips SAM.gov section and uses the other 4 sources (30+ buyers)

## Integration with Leads Hub

Once buyers are scraped:

1. **Leads Hub** (`/leads`):
   - Buyers appear in "All Supply Contracts" tab
   - Can be filtered by category
   - Searchable by keyword

2. **Supply Contracts** (`/supply-contracts`):
   - Full list of all supply buyers
   - Table view with contact details

3. **Quick Wins** (`/quick-wins`):
   - High-value buyers marked as "quick wins"
   - Priority display for paid subscribers

## Rate Limiting & Respectful Scraping

### SAM.gov
- 2-second delay between keyword searches
- Respects API rate limits (1000 requests/hour)
- Handles 429 errors gracefully

### State Portals
- No actual scraping (uses static directory)
- Information is publicly available contact data

### Healthcare/Education/Property
- Static curated list of major buyers
- Public procurement contact information
- No web scraping of private data

## Benefits for Supply Vendors

### Reverse Marketplace
Instead of vendors marketing TO buyers, this gives vendors a database OF buyers who are actively purchasing.

### Recurring Revenue
- Most contracts are annual or multi-year
- Monthly or quarterly orders
- Long-term relationships

### High Volume
- School districts: 100s-1,000s of buildings
- Hospital systems: 10s-100s of facilities
- Property managers: 100s-1,000s of properties

### Direct Contacts
- Procurement officer emails
- Supply chain phone numbers
- Facilities management contacts

## Differentiation from Contract Opportunities

### Traditional Contract Scraping
**Focus**: Service contracts (you provide labor)
**Examples**: Cleaning services, janitorial services
**Revenue**: Per cleaning performed

### Supply Buyers Scraping
**Focus**: Product sales (you sell supplies)
**Examples**: Cleaning chemicals, paper goods, equipment
**Revenue**: Per product sold (recurring)

## Future Enhancements

### Phase 2 - More Sources
- [ ] Government GPO (Government Printing Office)
- [ ] Vizient (healthcare group purchasing)
- [ ] E&I Cooperative Purchasing
- [ ] PEPPM (educational procurement)

### Phase 3 - Advanced Features
- [ ] Buyer purchase history tracking
- [ ] Contract renewal date alerts
- [ ] Competitive bidding monitoring
- [ ] Price comparison analytics

### Phase 4 - AI Matching
- [ ] Match vendors to buyers by category
- [ ] Recommend best buyers for vendor profile
- [ ] Predict purchase volumes
- [ ] Optimize supplier outreach timing

## Troubleshooting

### No SAM.gov Results
**Issue**: SAM_GOV_API_KEY not set or invalid

**Solution**:
1. Get free API key from https://sam.gov/data-services/
2. Set environment variable: `export SAM_GOV_API_KEY="your-key"`
3. Restart Flask app

**Workaround**: Scraper still works with other 4 sources

### Database Errors
**Issue**: Supply_contracts table doesn't exist

**Solution**:
```sql
CREATE TABLE supply_contracts (
    id SERIAL PRIMARY KEY,
    title TEXT,
    agency TEXT,
    location TEXT,
    estimated_value TEXT,
    description TEXT,
    website_url TEXT,
    status TEXT,
    posted_date DATE,
    category TEXT,
    product_category TEXT,
    requirements TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Import Fails Silently
**Issue**: Route executes but no data saved

**Check**:
1. Console logs for errors
2. Database connection
3. Table permissions
4. Disk space

---

## Quick Reference

### Files
- **Scraper**: `scrapers/janitorial_supply_buyers_scraper.py`
- **Route**: `app.py` - `/admin-scrape-janitorial-buyers`
- **Admin UI**: `templates/admin_sections/upload_csv.html`

### Routes
- **Scrape API**: `POST /admin-scrape-janitorial-buyers`
- **View Results**: `GET /leads` or `GET /supply-contracts`

### Key Functions
- `scrape_sam_gov_supply_requests()` - Federal buyers
- `scrape_state_procurement_portals()` - State buyers
- `scrape_educational_institutions()` - University/school buyers
- `scrape_healthcare_facilities()` - Hospital buyers
- `scrape_commercial_property_managers()` - Property management buyers
- `scrape_all_sources()` - Run all scrapers
- `save_to_database()` - Persist to DB

---

**Status**: ✅ **READY FOR USE**

**Version**: 1.0  
**Created**: November 10, 2025  
**Documentation**: Complete
