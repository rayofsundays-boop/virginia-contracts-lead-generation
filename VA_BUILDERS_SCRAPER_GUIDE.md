# VA Builders Summit Web Scraper - User Guide

## 🎯 Overview
Automated web scraper that extracts construction and cleaning contract opportunities from **vabuilderssummit.com**. This scraper helps you discover real leads from Virginia's premier construction industry event.

---

## 🚀 Quick Start

### Access the Scraper
1. Log in as admin
2. Navigate to `/admin-enhanced?section=va-builders-scraper`
3. See the **VA Builders Summit Web Scraper** dashboard

### Run Your First Scrape
1. Click "**Run Link Verification**" to test connectivity (optional)
2. Click "**Start Full Scrape**" to extract all opportunities
3. Wait 3-5 minutes for scraper to complete
4. View newly scraped contracts in the table below

---

## 📊 Scraper Dashboard

### Statistics Cards
- **Total Scraped**: Number of opportunities extracted from VA Builders Summit
- **Status**: Current scraper state (Ready, Running, Complete, Error)
- **Links**: Number of accessible URLs found on the website

### Scraper Actions
1. **Verify Links** (Fast - 1 minute)
   - Tests all 79+ links on vabuilderssummit.com
   - Shows accessible/warning/error counts
   - Useful for checking website availability

2. **Full Scrape** (Slow - 3-5 minutes)
   - Extracts opportunities from all accessible pages
   - Saves new leads to database
   - Skips duplicates automatically

---

## 🔍 What Gets Scraped

### Data Extracted
- **Title**: Event/opportunity name
- **Description**: Details about the opportunity (first 500 chars)
- **URL**: Direct link to the source page
- **Date**: Extracted from page content (if available)
- **Location**: Virginia (default) or extracted from page
- **Agency**: "VA Builders Summit"
- **NAICS Code**: 561720 (Janitorial Services)
- **Data Source**: "VA Builders Summit Web Scraper"

### Example Opportunities
- Construction supplier exhibitions
- Industry networking events
- Vendor partnership opportunities
- Building material showcases
- Professional development sessions

---

## 📈 How It Works

### 1. Link Discovery
```python
scraper = VABuildersSummitScraper()
links = scraper.get_all_internal_links()
# Found 79 internal links
```

### 2. Link Verification
```python
results = scraper.verify_all_links(links)
# ✅ Accessible: 79
# ⚠️ Warnings: 0
# ❌ Errors: 0
```

### 3. Data Extraction
```python
opportunities = scraper.scrape_all_opportunities()
# Extracts title, description, date, location from each page
```

### 4. Database Saving
```python
saved = scraper.save_to_database(opportunities, db.session)
# Saves to government_contracts table
# Skips duplicates based on URL
```

---

## 🎨 Admin UI Features

### Real-Time Progress
- Shows "Scraping in Progress..." with animated progress bar
- Updates status automatically
- Reloads page when complete to show new contracts

### Result Messages
- **Success**: "✅ Scraping Complete! 15 opportunities scraped, 10 new saved"
- **Duplicates**: "⏭️ 5 duplicates skipped"
- **Errors**: "❌ Error: Connection timeout"

### Recent Contracts Table
- Displays last 20 scraped opportunities
- Columns: Title, Location, Date, URL, Scraped At
- Click "View" to open source URL in new tab

---

## 🔧 Technical Details

### API Endpoints

#### Run Full Scrape
```http
POST /admin/run-va-builders-scraper
Authorization: Admin login required

Response:
{
  "success": true,
  "message": "Successfully scraped 15 opportunities, saved 10 new leads",
  "total_scraped": 15,
  "saved": 10,
  "duplicates": 5
}
```

#### Verify Links
```http
GET /admin/verify-va-builders-links
Authorization: Admin login required

Response:
{
  "success": true,
  "total_links": 79,
  "accessible": 79,
  "warnings": 0,
  "errors": 0,
  "accessible_urls": [...],
  "warning_urls": [...],
  "error_urls": [...]
}
```

### Database Schema
Contracts saved to `government_contracts` table:
```sql
CREATE TABLE government_contracts (
    id SERIAL PRIMARY KEY,
    title TEXT,
    agency TEXT,              -- "VA Builders Summit"
    location TEXT,            -- "Virginia"
    url TEXT UNIQUE,          -- Source page URL
    description TEXT,         -- Extracted content
    posted_date DATE,         -- Extracted or current date
    deadline DATE,            -- NULL (not available)
    contract_type TEXT,       -- "Construction/Cleaning"
    naics_code TEXT,          -- "561720"
    data_source TEXT,         -- "VA Builders Summit Web Scraper"
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🛠️ Command Line Usage

### Run Scraper Manually
```bash
cd "/path/to/project"
python3 scrapers/va_builders_summit_scraper.py
```

### Output
```
============================================================
VA BUILDERS SUMMIT LINK VERIFICATION
============================================================
🔍 Verifying 79 links...
✅ [1/79] https://www.vabuilderssummit.com/
✅ [2/79] https://www.vabuilderssummit.com/about/
...
============================================================
SUMMARY
============================================================
✅ Accessible: 79
⚠️ Warnings: 0
❌ Errors: 0
```

### Enable Full Scrape Mode
Edit `scrapers/va_builders_summit_scraper.py` (bottom of file):
```python
# Uncomment these lines:
opportunities = scraper.scrape_all_opportunities()
print(f"\n📊 Total opportunities found: {len(opportunities)}")
```

---

## 🧪 Testing

### Test Link Verification
1. Click "Run Link Verification"
2. Wait ~1 minute
3. Should show "79 accessible links"

### Test Full Scrape
1. Click "Start Full Scrape"
2. Wait 3-5 minutes
3. Check for new contracts in table
4. Verify in database: `/admin-enhanced?section=all-contracts`

### Verify Data Quality
```sql
-- Check scraped contracts
SELECT * FROM government_contracts 
WHERE data_source = 'VA Builders Summit Web Scraper'
ORDER BY created_at DESC;

-- Count by date
SELECT DATE(created_at), COUNT(*) 
FROM government_contracts 
WHERE data_source = 'VA Builders Summit Web Scraper'
GROUP BY DATE(created_at);
```

---

## 📊 Performance Metrics

### Speed
- Link Verification: ~60 seconds (79 links @ 0.5s delay)
- Full Scrape: 3-5 minutes (79 pages @ 1s delay)
- Database Insert: <1 second per contract

### Respectful Scraping
- 0.5s delay between link checks
- 1s delay between page scrapes
- User-Agent header to identify scraper
- HEAD requests for link verification

---

## 🔮 Future Enhancements

### Scheduled Scraping
```python
# Add to app.py background jobs
schedule.every().day.at("03:00").do(run_va_builders_scraper)
# Runs automatically at 3 AM daily
```

### Email Notifications
```python
# Send admin email when new opportunities found
if saved_count > 0:
    send_admin_notification(
        f"🎉 {saved_count} new opportunities from VA Builders Summit"
    )
```

### Advanced Filtering
- Filter by opportunity type (exhibition, session, vendor)
- Extract pricing information if available
- Categorize by industry segment

---

## ❓ Troubleshooting

### "No opportunities found"
- Check if website is accessible: https://www.vabuilderssummit.com/
- Run Link Verification first
- Verify BeautifulSoup is installed: `pip install beautifulsoup4`

### "Connection timeout"
- Increase timeout in scraper.py: `timeout=10` → `timeout=30`
- Check internet connection
- Try again later (website may be temporarily down)

### "Scraper module not found"
- Ensure `scrapers/` directory exists
- Check file name: `va_builders_summit_scraper.py`
- Restart Flask app after creating file

### Duplicates not skipping
- Verify URL uniqueness constraint on database
- Check if URLs match exactly (trailing slash matters)
- Clear old contracts and re-scrape

---

## 📞 Support

### Logs
Check console output for detailed scraping progress:
```
📋 Found 79 internal links
🔍 Extracting data from accessible pages...
📄 [1/79] Scraping https://www.vabuilderssummit.com/about/
   ✅ Extracted: Virginia Builders Summit Overview
...
✅ Scraped 15 opportunities
```

### Debug Mode
Enable verbose logging in `scrapers/va_builders_summit_scraper.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📈 Best Practices

1. **Run Weekly**: Scrape once per week to catch new opportunities
2. **Verify First**: Always run link verification before full scrape
3. **Monitor Quality**: Review scraped contracts for data accuracy
4. **Clean Duplicates**: Use SQL to remove old/outdated entries
5. **Extend Scraper**: Add more construction websites to scraper library

---

**Last Updated**: November 10, 2025  
**Status**: ✅ Live and Operational  
**Test Result**: 79/79 links accessible  
**Commit**: `be21d94`
