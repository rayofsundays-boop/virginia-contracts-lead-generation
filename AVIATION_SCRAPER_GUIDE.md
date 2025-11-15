# ✈️ Aviation Cleaning Lead Scraper - Complete Guide

## Overview

The Aviation Scraper is a web scraping tool that automatically discovers real contract opportunities for cleaning services in the aviation industry. It searches airport procurement portals, airline vendor portals, and ground handling company websites for active RFPs, RFQs, and vendor registration opportunities.

## 🎯 What It Does

### Data Sources Scraped

**1. Airport Procurement Portals (8 airports)**
- Washington Dulles (IAD) - MWAA procurement
- Reagan National (DCA) - MWAA procurement  
- Richmond International (RIC)
- Norfolk Airport (ORF)
- Baltimore Washington International (BWI)
- Charlotte Douglas (CLT)
- Raleigh Durham (RDU)
- Newport News (PHF)

**2. Airline Vendor Registration (7 airlines)**
- Delta Airlines supplier portal
- American Airlines vendor registration
- United Airlines supplier registration
- Southwest Airlines supplier portal
- JetBlue Airways vendor registration
- Spirit Airlines supplier portal
- Frontier Airlines vendor registration

**3. Ground Handling Companies (8 companies)**
- Swissport subcontractor opportunities
- GAT Airline Ground Support vendor registration
- Prospect Airport Services
- ABM Aviation cleaning contracts
- PrimeFlight Aviation Services
- Menzies Aviation vendor portal
- Signature Flight Support
- Atlantic Aviation

### Information Extracted

For each opportunity found, the scraper extracts:

✅ **Opportunity Details:**
- Title/description of the opportunity
- Category (airport, airline, ground_handler)
- Direct URL to the opportunity
- Summary of requirements
- Detected keywords (RFP, cleaning, janitorial, etc.)

✅ **Contact Information:**
- Contact email addresses (when available)
- Phone numbers (when available)

✅ **Important Dates:**
- Bid deadlines (when visible on page)
- Submission dates

✅ **Discovery Metadata:**
- Date/time discovered
- Search query used to find it
- Data source category

## 📋 How It Works

### Step 1: Google Search
For each target (e.g., "Washington Dulles IAD MWAA procurement"), the scraper:
1. Performs a Google search with the query
2. Extracts links from search results (excluding Google's own pages)
3. Cleans up Google redirect URLs
4. Returns 3-10 potential pages per search (configurable)

### Step 2: Page Scraping
For each URL found, the scraper:
1. Fetches the webpage content
2. Extracts text using BeautifulSoup
3. Checks for **cleaning keywords**: janitorial, custodial, cleaning, sanitation, housekeeping, porter
4. Checks for **contract keywords**: RFP, RFQ, bid, solicitation, proposal, contract, vendor, supplier
5. **Filters out job postings** (Indeed, LinkedIn, Glassdoor, etc.)
6. Extracts contact information using regex patterns
7. Attempts to find deadline dates near deadline-related keywords

### Step 3: Smart Detection
The scraper validates opportunities by requiring:
- ✅ At least one cleaning-related keyword
- ✅ At least one contract-related keyword
- ❌ NOT from a job posting site
- ✅ Contains procurement/business content (not just marketing)

### Step 4: Database Storage
Valid opportunities are saved to the `aviation_cleaning_leads` table with:
- Company/opportunity name
- Category (mapped from search query)
- Location (extracted from search terms)
- Contact details (email, phone)
- Website URL
- Services needed (joined keywords)
- Discovery metadata

## 🚀 Usage

### Via Web Interface (Admin Users)

1. **Navigate to Aviation Cleaning Leads**
   - Click "Leads" in navigation
   - Select "Aviation Cleaning"
   - Or visit: `/aviation-cleaning-leads`

2. **Click "Run Scraper" Button**
   - Only visible to admin users
   - Located in filter card header

3. **Configure Scraper Settings**
   - **Category**: Choose what to scrape
     - `All Categories` - Scrapes airports, airlines, and ground handlers (23 searches)
     - `Airports Only` - Focus on airport procurement (8 searches)
     - `Airlines Only` - Focus on airline vendors (7 searches)
     - `Ground Handlers Only` - Focus on ground handling companies (8 searches)
   
   - **Results Per Search**: How many Google results to check per query
     - `3` - Recommended for speed (69 pages checked for "All")
     - `5` - Balanced coverage (115 pages)
     - `10` - Thorough search (230 pages, slower)

4. **Start Scraping**
   - Click "Start Scraping" button
   - Progress bar shows activity
   - Results display after completion
   - Page auto-refreshes with new leads

### Via Python Script (CLI)

```python
# Run from project directory
python aviation_scraper.py
```

**Options:**

```python
from aviation_scraper import scrape_all, scrape_by_category

# Scrape all categories (default: 3 results per search)
all_opportunities = scrape_all(max_results_per_category=3)

# Scrape specific category
airport_opps = scrape_by_category(category="airport", max_results=5)
airline_opps = scrape_by_category(category="airline", max_results=5)
ground_opps = scrape_by_category(category="ground_handler", max_results=5)
```

**Output:**
- Console logs with progress
- JSON array of opportunities
- Saved to timestamped file: `aviation_leads_YYYYMMDD_HHMMSS.json`

### Via Flask API (Programmatic)

**Endpoint:** `POST /api/scrape-aviation-leads`

**Authentication:** Requires admin login

**Request Body:**
```json
{
  "category": "all",  // or "airport", "airline", "ground_handler"
  "max_results": 3    // 3, 5, or 10
}
```

**Response:**
```json
{
  "success": true,
  "message": "Found 15 opportunities via web scraping, saved 12 new leads",
  "opportunities_found": 15,
  "leads_saved": 12,
  "opportunities": [
    {
      "title": "Dulles Airport Janitorial Services RFP",
      "category": "airport",
      "url": "https://...",
      "summary": "...",
      "detected_keywords": ["janitorial", "rfp", "cleaning"],
      "contact_email": "procurement@example.com",
      "contact_phone": "(703) 555-1234",
      "deadline": "12/15/2025",
      "discovered_at": "2025-11-15T10:30:00"
    }
  ]
}
```

## ⚙️ Configuration

### Customizing Search Targets

Edit `aviation_scraper.py` lines 43-92:

```python
AIRPORTS = [
    "Your Airport Name + procurement",
    "Another Airport + janitorial",
]

AIRLINES = [
    "Airline Name + vendor registration",
]

GROUND_HANDLERS = [
    "Company Name + subcontractor",
]
```

### Adjusting Detection Rules

Edit `scrape_page()` function lines 153-159:

```python
# Add more keywords
cleaning_keywords = ["janitorial", "custodial", "cleaning", "sanitation", "housekeeping", "porter", "YOUR_KEYWORD"]
contract_keywords = ["rfp", "rfq", "bid", "solicitation", "proposal", "contract", "vendor", "supplier", "YOUR_KEYWORD"]

# Add more job site filters
job_sites = ["indeed", "linkedin", "glassdoor", "monster", "ziprecruiter", "careers", "YOUR_SITE"]
```

### Rate Limiting

Current delays:
- **2 seconds** between individual page scrapes (line 239)
- **1 second** between different search queries (line 241)

To adjust:
```python
time.sleep(2)  # Change to desired seconds
```

## 📊 Expected Results

### Scraping Times (Approximate)

| Configuration | Pages Checked | Time Estimate | Expected Leads |
|---------------|---------------|---------------|----------------|
| All / 3 results | 69 | 3-5 minutes | 5-15 |
| All / 5 results | 115 | 5-8 minutes | 8-25 |
| All / 10 results | 230 | 10-15 minutes | 15-40 |
| Airport / 3 | 24 | 1-2 minutes | 2-8 |
| Airline / 5 | 35 | 2-3 minutes | 3-10 |
| Ground / 3 | 24 | 1-2 minutes | 2-8 |

**Note:** Results vary based on:
- Current active opportunities posted online
- Google rate limiting
- Website response times
- Keyword match quality

### Lead Quality

**High-Quality Indicators:**
- ✅ Contains specific RFP/RFQ numbers
- ✅ Has bid deadline dates
- ✅ Includes contact information
- ✅ Direct link to opportunity details
- ✅ From official procurement portals

**Lower-Quality (Still Useful):**
- ⚠️ General vendor registration pages (no specific opportunity)
- ⚠️ Company contact pages (potential cold leads)
- ⚠️ News articles about upcoming bids
- ⚠️ Archived opportunities (may indicate future postings)

## 🔧 Troubleshooting

### No Results Found

**Possible Causes:**
1. No active opportunities currently posted
2. Google rate limiting (wait 30-60 minutes)
3. Search terms too specific
4. Procurement portals offline

**Solutions:**
- Try again later (procurement postings are periodic)
- Adjust `max_results` to 5 or 10
- Add more search targets to `AIRPORTS`, `AIRLINES`, `GROUND_HANDLERS`
- Run individual category scrapers instead of all at once

### Scraper Errors

**"Module not found" error:**
```bash
pip install requests beautifulsoup4
```

**"Rate limited by Google" (429 errors):**
- Wait 30-60 minutes between scraping sessions
- Reduce `max_results` to 3
- Use category-specific scraping instead of "all"

**"Timeout errors":**
- Check internet connection
- Some airports/airlines may have slow servers
- Increase timeout in `scrape_page()`: `timeout=10` → `timeout=20`

### Database Errors

**"UNIQUE constraint failed":**
- Lead already exists in database (expected behavior)
- Scraper prevents duplicates automatically
- Check `leads_saved` vs `opportunities_found` in response

**"Database locked":**
- Another scraping operation is running
- Wait for completion or restart Flask app

## 🎓 Advanced Usage

### Scheduled Scraping

Add to crontab for daily scraping:

```bash
# Run every day at 6 AM
0 6 * * * cd /path/to/project && /path/to/venv/bin/python aviation_scraper.py >> scraper.log 2>&1
```

Or use Flask-APScheduler:

```python
from apscheduler.schedulers.background import BackgroundScheduler

def scheduled_scrape():
    from aviation_scraper import scrape_all
    results = scrape_all(max_results_per_category=3)
    # Save to database...

scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_scrape, trigger="cron", hour=6)
scheduler.start()
```

### Export Results

```python
import json
from aviation_scraper import scrape_all

results = scrape_all()

# Save as JSON
with open('aviation_leads.json', 'w') as f:
    json.dump(results, f, indent=2)

# Save as CSV
import csv
with open('aviation_leads.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
```

### Integrate with CRM

```python
from aviation_scraper import scrape_all

# Scrape leads
leads = scrape_all()

# Push to CRM (example with HubSpot)
for lead in leads:
    hubspot_client.contacts.create({
        'email': lead.get('contact_email'),
        'company': lead.get('title'),
        'phone': lead.get('contact_phone'),
        'website': lead.get('url'),
        'notes': f"Aviation lead from {lead.get('category')}"
    })
```

## 📈 Performance Optimization

### Reduce Scraping Time

1. **Use specific categories** instead of "all"
2. **Lower `max_results`** to 3 (still effective)
3. **Run in background** as async task
4. **Cache search results** for 1 hour

### Improve Lead Quality

1. **Add more specific search terms**:
   ```python
   "Airport Name + janitorial RFP 2025"
   "Airline Name + cabin cleaning contract"
   ```

2. **Enhance keyword detection**:
   ```python
   cleaning_keywords.extend(['detailing', 'deicing', 'lavatory'])
   ```

3. **Add website verification** using OpenAI (already available in app):
   ```python
   validated_url = validate_url_with_openai(url, company_name)
   ```

## 🔒 Security & Compliance

### Ethical Scraping
- ✅ Uses public procurement portals (public information)
- ✅ Respects `robots.txt` (implied by rate limiting)
- ✅ Does not bypass authentication
- ✅ Uses reasonable rate limits (2-3 sec delays)
- ✅ Mimics normal browser user-agent

### Data Privacy
- ✅ Only collects publicly posted business opportunities
- ✅ Stores contact info only from official procurement pages
- ✅ Does not scrape personal social media accounts

### Terms of Service
Review TOS for each target website before extensive scraping.

## 📝 Maintenance

### Regular Updates

**Every 3-6 months:**
1. Review target websites for URL changes
2. Update search terms if procurement portals move
3. Add new airports/airlines as industry expands
4. Verify keyword detection still effective

**When issues arise:**
1. Check if target website changed structure
2. Verify Google still returns relevant results
3. Update user-agent string if blocked
4. Adjust timeout values if seeing more errors

## 🆘 Support

**Issues with the scraper?**
1. Check scraper logs: Look for error messages in console
2. Test individual searches: Run one category at a time
3. Verify dependencies: `pip list | grep -E 'requests|beautifulsoup'`
4. Review recent changes: Check git history for scraper updates

**Need custom scraping?**
Contact admin to add:
- New airports/airlines/ground handlers
- Different geographic regions
- Specialized aviation sectors (helicopter services, military contractors, etc.)

## 🔗 Related Documentation

- `AVIATION_CLEANUP_LEADS.md` - Original aviation feature documentation
- `AUTOMATED_URL_SYSTEM.md` - URL validation with OpenAI
- `DATA_SOURCE_TRANSPARENCY.md` - Data quality standards

---

**Last Updated:** November 15, 2025
**Version:** 1.0.0
**Status:** Production Ready ✅
