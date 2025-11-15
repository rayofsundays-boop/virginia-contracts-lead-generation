# ✈️ Aviation Scraper Quick Start Card

## 🎯 What It Does
Automatically discovers **real aviation cleaning contracts** from 23 sources:
- 🏢 8 Airport procurement portals
- ✈️ 7 Airline vendor portals  
- 🔧 8 Ground handling companies

## 🚀 How to Use (Web Interface)

### Step 1: Navigate to Aviation Leads
```
Navbar → Leads → Aviation Cleaning
```
Or visit: `/aviation-cleaning-leads`

### Step 2: Click "Run Scraper" Button
**Location:** Top-right of filter card header  
**Requires:** Admin login

### Step 3: Configure Scraper
**Category Options:**
- `All Categories` - 23 searches (recommended)
- `Airports Only` - 8 searches (IAD, DCA, RIC, ORF, BWI, CLT, RDU, PHF)
- `Airlines Only` - 7 searches (Delta, American, United, Southwest, etc.)
- `Ground Handlers Only` - 8 searches (Swissport, GAT, ABM, PrimeFlight, etc.)

**Results Per Search:**
- `3` - Fast (69 pages checked for "All") ⚡
- `5` - Balanced (115 pages)
- `10` - Thorough (230 pages, slower) 🐌

### Step 4: Start Scraping
- Click "Start Scraping" button
- Watch progress bar
- View results when complete
- Page auto-refreshes with new leads

## ⏱️ Expected Results

| Category | Time | Leads |
|----------|------|-------|
| All / 3 results | 3-5 min | 5-15 |
| All / 5 results | 5-8 min | 8-25 |
| Airports / 3 | 1-2 min | 2-8 |
| Airlines / 5 | 2-3 min | 3-10 |
| Ground / 3 | 1-2 min | 2-8 |

## 📋 What Gets Extracted

✅ **Opportunity Details:**
- Title/description
- Category (airport/airline/ground_handler)
- Direct URL to opportunity
- Summary of requirements
- Keywords (RFP, cleaning, janitorial, etc.)

✅ **Contact Information:**
- Email addresses
- Phone numbers
- Location (state/city)

✅ **Important Dates:**
- Bid deadlines (when visible)

## 🎓 CLI Usage (Developers)

```bash
# Run full scraper
python aviation_scraper.py

# Scrape specific category
python -c "from aviation_scraper import scrape_by_category; scrape_by_category('airport', 5)"
```

**Output:** JSON file saved as `aviation_leads_YYYYMMDD_HHMMSS.json`

## 🔧 API Usage (Programmatic)

```bash
POST /api/scrape-aviation-leads
{
  "category": "all",
  "max_results": 3
}
```

**Authentication:** Requires admin session

**Response:**
```json
{
  "success": true,
  "opportunities_found": 15,
  "leads_saved": 12,
  "opportunities": [...]
}
```

## ⚠️ Troubleshooting

### No Results Found
**Causes:**
- No active opportunities currently posted
- Google rate limiting (wait 30-60 minutes)
- Search terms too specific

**Solutions:**
- Try again later
- Increase max_results to 5 or 10
- Run category-specific scraping

### Google Rate Limiting
**Symptoms:** 429 errors, 0 links found

**Solutions:**
- Wait 30-60 minutes between runs
- Use category-specific scraping (fewer searches)
- Reduce max_results to 3

### Scraper Running Slowly
**Normal Behavior:**
- 2 seconds per page (rate limiting)
- 1 second between searches
- Large configurations take longer

**To Speed Up:**
- Use specific category instead of "all"
- Reduce max_results to 3
- Run during off-peak hours

## 💡 Pro Tips

### Maximize Lead Quality
1. **Run daily** - Catch opportunities as they're posted
2. **Use "All" category** - Broader coverage
3. **Check results immediately** - Early bird gets the contract

### Optimize Performance
1. **Start with Airports** - Highest value contracts
2. **Use max_results=3** - Best speed/coverage ratio
3. **Schedule off-hours** - Avoid peak traffic times

### Best Practices
1. **Review leads within 24 hours** - Respond quickly
2. **Verify contact info** - Call or email to confirm
3. **Track win rates** - Optimize search targets

## 📊 Data Quality

### High-Quality Indicators
- ✅ Contains RFP/RFQ numbers
- ✅ Has bid deadlines
- ✅ Includes contact information
- ✅ Direct link to opportunity
- ✅ From official procurement portals

### Lower Quality (Still Useful)
- ⚠️ General vendor registration pages
- ⚠️ Company contact pages (cold leads)
- ⚠️ News about upcoming bids

## 🔗 Full Documentation

**Complete Guide:** `AVIATION_SCRAPER_GUIDE.md`
- Detailed usage instructions
- Configuration options
- Advanced features
- Troubleshooting guide
- Performance optimization

**Implementation Summary:** `AVIATION_SCRAPER_SUMMARY.md`
- Technical details
- Business impact
- Testing checklist
- Deployment notes

## 💰 Business Impact

**Revenue Opportunities:**
- Airport terminals: $50K-$500K+/year
- Airline cabin cleaning: $100K-$2M+/year (per hub)
- FBO hangars: $10K-$100K+/year
- Ground handler facilities: $25K-$250K+/year

**Volume Potential:**
- 5-15 leads per session
- Run daily = 150-450 leads/month
- 1-5% conversion = 1-22 contracts/month

## 🎯 Next Steps

1. **Run First Scrape:** Test with "All / 3 results"
2. **Review Leads:** Check quality and relevance
3. **Adjust Settings:** Optimize category/results based on needs
4. **Schedule Regular Runs:** Weekly or daily scraping
5. **Track Results:** Monitor win rates and contract values

---

**Status:** ✅ Production Ready  
**Last Updated:** November 15, 2025  
**Version:** 1.0.0
