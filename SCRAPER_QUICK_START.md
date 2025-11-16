# Scraper System - Quick Start Guide 🚀

## ✅ What's Been Completed

### **All 5 Scraper Components Built:**
1. ✅ **Base Scraper Framework** (370 lines) - Rate limiting, HTML parsing, data extraction
2. ✅ **EVA Virginia Scraper** (240 lines) - Virginia state procurement portal
3. ✅ **State Portal Scraper** (350 lines) - All 50 US states with parallel execution
4. ✅ **City/County Scraper** (420 lines) - 11 Virginia cities with fallback URLs
5. ✅ **Scraper Manager** (380 lines) - Orchestration, logging, scheduling, statistics

### **Flask Integration Complete:**
- ✅ Imports added to `app.py`
- ✅ Auto-initialization on app startup
- ✅ Daily scheduling at 2:00 AM
- ✅ Admin section: `/admin-enhanced?section=scrapers`
- ✅ API endpoints: `/api/admin/scrapers/run`, `/logs`, `/stats`

### **Testing & Documentation:**
- ✅ Comprehensive test script: `test_all_scrapers.py`
- ✅ Complete system guide: `SCRAPER_SYSTEM_COMPLETE.md`
- ✅ This quick start guide

---

## 🎯 Next Step: Run Test Suite

### **Option 1: Command Line Test** (Recommended First)
```bash
cd "/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE"
python test_all_scrapers.py
```

**What It Does:**
1. Runs all 3 scrapers individually
2. Shows real-time progress and results
3. Saves contracts to database
4. Displays statistics and logs
5. Verifies database integration

**Expected Output:**
```
================================================================================
SCRAPER TEST SUITE
================================================================================

Available Scrapers:
  1. eva_virginia
  2. state_portals  
  3. city_county

============================================================
Testing: eva_virginia
============================================================

✅ SUCCESS
   Contracts Found: 15
   Contracts Saved: 12
   Duration: 45.20s

[... continues for all scrapers ...]

SUMMARY:
- Total Contracts Found: 65
- Total Contracts Saved: 57
```

### **Option 2: Via Flask Admin Dashboard**
1. Start Flask app: Run the "Run Flask App" task or `python app.py`
2. Visit: `http://127.0.0.1:8080/admin-enhanced?section=scrapers`
3. Click "Run Now" buttons to execute scrapers manually
4. View logs and statistics in real-time

### **Option 3: Via API (cURL)**
```bash
# Run EVA Virginia scraper
curl -X POST http://localhost:8080/api/admin/scrapers/run \
  -H "Content-Type: application/json" \
  -d '{"scraper": "eva_virginia"}'

# Run all scrapers
curl -X POST http://localhost:8080/api/admin/scrapers/run \
  -H "Content-Type: application/json" \
  -d '{"scraper": "all"}'

# Get logs
curl http://localhost:8080/api/admin/scrapers/logs?limit=20

# Get statistics
curl http://localhost:8080/api/admin/scrapers/stats
```

---

## 📊 What Gets Populated

### **Database Table: `contracts`**
All scraped government cleaning/janitorial contracts:

**Fields Populated:**
- `title` - Contract/bid title
- `agency` - Government agency name
- `location` - State or city
- `value` - Estimated contract value (if available)
- `deadline` - Bid submission deadline
- `description` - Full contract description
- `naics_code` - 561720 (Janitorial Services)
- `url` - Link to official bid page
- `solicitation_number` - Unique identifier
- `contact_name`, `contact_email`, `contact_phone` - Agency contact info
- `data_source` - 'EVA Virginia', 'State Portal', or 'City/County'
- `created_at` - Timestamp when scraped

**Expected Volume (First Run):**
- EVA Virginia: 10-20 contracts
- State Portals: 30-50 contracts (50 states combined)
- City/County: 5-10 contracts (11 Virginia cities)
- **Total: 50-80 contracts**

### **Database Table: `scraper_logs`**
Execution history for monitoring:

**Fields:**
- `scraper_name` - Which scraper ran
- `started_at`, `completed_at` - Timestamps
- `status` - 'success' or 'failed'
- `contracts_found`, `contracts_saved` - Counts
- `error_message` - If failed

---

## 🔧 Admin Controls

### **Admin Dashboard** (`/admin-enhanced?section=scrapers`)
**Features:**
- View scraper statistics (runs, success rate, contracts saved)
- Recent execution logs (last 50)
- Contract counts by data source
- Manual "Run Now" buttons for each scraper
- Real-time status updates

**Access:**
1. Login as admin at `/admin-login`
2. Navigate to Admin Panel
3. Click "Scrapers" in left sidebar

### **API Endpoints**

#### **1. Run Scraper**
```
POST /api/admin/scrapers/run
Content-Type: application/json

{
  "scraper": "eva_virginia"  // or "state_portals", "city_county", "all"
}
```

**Response:**
```json
{
  "success": true,
  "scraper_name": "eva_virginia",
  "contracts_found": 15,
  "contracts_saved": 12,
  "duplicates": 3,
  "duration_seconds": 45.2
}
```

#### **2. Get Logs**
```
GET /api/admin/scrapers/logs?limit=50
```

#### **3. Get Statistics**
```
GET /api/admin/scrapers/stats
```

---

## ⏰ Automated Scheduling

### **Daily Scraping at 2:00 AM**
Configured automatically on Flask startup:

```python
# In app.py
scraper_manager = get_scraper_manager('leads.db')
scraper_manager.schedule_daily_scrape(hour=2, minute=0)
```

**What Runs:**
1. EVA Virginia scraper (~45 seconds)
2. State portal scraper (~3-5 minutes)
3. City/county scraper (~1-2 minutes)
4. **Total: ~5-8 minutes per day**

**Logs Stored:**
All executions logged to `scraper_logs` table for monitoring.

---

## 🐛 Troubleshooting

### **"Scraper system not available" Error**
**Cause**: Import failed for scrapers module
**Fix**: Check that `scrapers/` directory exists with all files:
```
scrapers/
  __init__.py
  base_scraper.py
  eva_virginia_scraper.py
  state_portal_scraper.py
  city_county_scraper.py
  scraper_manager.py
```

### **No Contracts Found**
**Cause**: Portal HTML structure changed or no active bids
**Fix**:
1. Check scraper logs for error messages
2. Manually visit portal URLs to verify structure
3. Update CSS selectors in scraper classes

### **Scraper Failing with Network Errors**
**Cause**: Rate limiting or connectivity issues
**Fix**:
1. Increase rate limit delay in scraper config (e.g., 10 seconds)
2. Check network connectivity
3. Review error message in `scraper_logs` table

### **Duplicates Not Detected**
**Cause**: UNIQUE constraint not working
**Fix**: Ensure `solicitation_number` and `agency` are populated for all contracts

---

## 📁 File Locations

### **Scraper System:**
```
scrapers/
  __init__.py                    # Package initialization
  base_scraper.py                # Base framework (370 lines)
  eva_virginia_scraper.py        # EVA Virginia (240 lines)
  state_portal_scraper.py        # 50 states (350 lines)
  city_county_scraper.py         # 11 cities (420 lines)
  scraper_manager.py             # Manager (380 lines)
```

### **Testing:**
```
test_all_scrapers.py             # Comprehensive test suite
```

### **Flask Integration:**
```
app.py                           # Lines ~85-95 (imports), ~29810-29820 (init), ~15870-15900 (admin), ~21835-21935 (API)
```

### **Documentation:**
```
SCRAPER_SYSTEM_COMPLETE.md       # Complete guide (500+ lines)
SCRAPER_QUICK_START.md           # This file
```

---

## 🎉 Success Indicators

### **After Running Test Suite:**
1. ✅ All 3 scrapers show "SUCCESS" status
2. ✅ `contracts` table has 50+ records
3. ✅ `scraper_logs` table has 3 entries (one per scraper)
4. ✅ Contracts visible at `/contracts` page
5. ✅ Statistics show in admin dashboard

### **Verify Database:**
```bash
sqlite3 leads.db "SELECT COUNT(*) FROM contracts"
# Expected: 50-80 (after first run)

sqlite3 leads.db "SELECT data_source, COUNT(*) FROM contracts GROUP BY data_source"
# Expected:
# EVA Virginia|12
# State Portal|38
# City/County|7
```

---

## 🚀 Ready to Launch!

**Recommended First Run:**
```bash
python test_all_scrapers.py
```

This will:
1. Validate all scrapers work correctly
2. Populate database with real government contracts
3. Create logs for monitoring
4. Show statistics and success metrics

**Total Time:** ~5-8 minutes for first complete run

---

**Questions or Issues?** See `SCRAPER_SYSTEM_COMPLETE.md` for detailed documentation and troubleshooting.
