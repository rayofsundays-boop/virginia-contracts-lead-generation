# 🤖 Automated Daily Federal Contract Fetching

**Status:** ✅ ACTIVE & WORKING  
**Last Updated:** November 5, 2025  
**Data Source:** Data.gov / USAspending.gov API

---

## 📊 Current Performance

```
Total Opportunities:         246
├── Federal Contracts:        92 (88 from Data.gov, 4 from SAM.gov)
├── Local Government:         88
├── Supply Contracts:         31
└── Commercial Opportunities: 35
```

**Latest Fetch Results:**
- ✅ 50 contracts fetched from Data.gov
- ✅ 39 new contracts added to database
- ✅ 11 duplicates automatically skipped
- ✅ 78% success rate

---

## 🎯 How It Works

### Automated Daily Fetching

The system automatically fetches new federal contracts from Data.gov/USAspending.gov **every day at 3:00 AM EST**.

**Key Features:**
- ✅ **No API Key Required** - Data.gov is free and reliable
- ✅ **Automatic Duplicate Detection** - Won't add the same contract twice
- ✅ **Smart Filtering** - Prioritizes cleaning/service contracts (NAICS 56xxxx)
- ✅ **Comprehensive Logging** - All activity logged to `daily_fetch.log`
- ✅ **Error Recovery** - If Data.gov fails, retries automatically
- ✅ **DMV Region Coverage** - Fetches contracts from VA, MD, and DC

### Data Flow

```
Data.gov/USAspending.gov API
            ↓
    auto_fetch_daily.py (runs at 3 AM)
            ↓
    Fetch 100 contracts from last 7 days
            ↓
    Filter for service contracts (NAICS 56xxxx)
            ↓
    Check for duplicates (notice_id + title)
            ↓
    Save new contracts to database
            ↓
    Log results to daily_fetch.log
```

---

## 🚀 Setup Instructions

### Option 1: Automatic Cron Job (Recommended)

Run the setup script to install automated daily fetching:

```bash
cd "/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE"
./setup_auto_fetch.sh
```

This will:
1. Create a cron job to run every day at 3:00 AM EST
2. Automatically fetch new contracts
3. Log all activity to `daily_fetch.log`

**To verify cron job is installed:**
```bash
crontab -l | grep auto_fetch_daily
```

**Expected output:**
```
0 3 * * * cd /Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE && /usr/bin/python3 auto_fetch_daily.py >> daily_fetch.log 2>&1
```

### Option 2: Manual Testing

Test the automated fetch manually anytime:

```bash
cd "/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE"
python3 auto_fetch_daily.py
```

### Option 3: Web Interface (Admin Panel)

Access from Flask admin panel:
```
http://localhost:5000/admin/auto-fetch-datagov
```

**Options:**
- Default: Fetch last 7 days
- `/admin/auto-fetch-datagov?days=14` - Fetch last 14 days
- `/admin/auto-fetch-datagov?days=30` - Fetch last 30 days

---

## 📁 Files Created

### Core Scripts

| File | Purpose | Location |
|------|---------|----------|
| `auto_fetch_daily.py` | Main automated fetching script | Project root |
| `setup_auto_fetch.sh` | Cron job installer | Project root |
| `datagov_bulk_fetcher.py` | Data.gov API integration | Project root |
| `daily_fetch.log` | Activity log (auto-generated) | Project root |

### Flask Routes

| Route | Purpose | Access |
|-------|---------|--------|
| `/admin/auto-fetch-datagov` | Manual trigger from web | Admin only |
| `/admin/check-contracts` | View database stats | Admin only |
| `/federal-contracts` | View all federal contracts | All users |

---

## 📊 Monitoring & Logs

### View Real-Time Logs

```bash
# Watch logs in real-time
tail -f daily_fetch.log

# View last 50 lines
tail -50 daily_fetch.log

# View entire log
cat daily_fetch.log
```

### Check Database Stats

```bash
cd "/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE"
python3 database_analysis.py
```

### Web Dashboard

Visit admin panel to see:
- Total contracts by source
- Recent additions
- Top agencies
- Database health

---

## ⚙️ Configuration

### Adjust Fetch Frequency

Edit the cron schedule in `setup_auto_fetch.sh`:

```bash
# Current: Daily at 3:00 AM EST
CRON_SCHEDULE="0 3 * * *"

# Every 6 hours at 12 AM, 6 AM, 12 PM, 6 PM
CRON_SCHEDULE="0 */6 * * *"

# Twice daily at 3 AM and 3 PM
CRON_SCHEDULE="0 3,15 * * *"

# Every Monday at 3 AM
CRON_SCHEDULE="0 3 * * 1"
```

Then reinstall:
```bash
./setup_auto_fetch.sh
```

### Adjust Lookback Period

Default is 7 days. To change:

**In cron job:**
```bash
export FETCH_DAYS_BACK=14
```

**In manual run:**
```bash
FETCH_DAYS_BACK=30 python3 auto_fetch_daily.py
```

**In web interface:**
```
/admin/auto-fetch-datagov?days=30
```

---

## 🔍 Top Federal Agencies

Based on current Data.gov contracts:

| Rank | Agency | Contracts |
|------|--------|-----------|
| 1 | General Services Administration | 18 |
| 2 | Department of Veterans Affairs | 6 |
| 3 | Department of Transportation | 4 |
| 4 | Department of State | 4 |
| 5 | Department of Homeland Security | 4 |
| 6 | Department of Health and Human Services | 3 |
| 7 | NASA | 2 |
| 8 | Department of Education | 2 |

---

## 🐛 Troubleshooting

### Issue: Cron job not running

**Check if cron job exists:**
```bash
crontab -l
```

**Reinstall:**
```bash
./setup_auto_fetch.sh
```

**Check logs:**
```bash
tail -50 daily_fetch.log
```

### Issue: No new contracts added

**Possible reasons:**
1. All contracts are duplicates (normal after first fetch)
2. No new contracts published in lookback period
3. Data.gov API temporarily down

**Solutions:**
1. Increase lookback period: `/admin/auto-fetch-datagov?days=30`
2. Check log for errors: `tail daily_fetch.log`
3. Try manual fetch: `python3 auto_fetch_daily.py`

### Issue: Database errors

**Check database health:**
```bash
sqlite3 leads.db "SELECT COUNT(*) FROM federal_contracts;"
```

**Verify table structure:**
```bash
sqlite3 leads.db "PRAGMA table_info(federal_contracts);"
```

### Issue: Import errors

**Install missing dependencies:**
```bash
pip install -r requirements.txt
```

---

## 📈 Growth Tracking

### Before Automation
- Federal Contracts: 4 (all from SAM.gov API)
- Data Source: SAM.gov only (requires API key, unreliable)

### After Automation
- Federal Contracts: 92 (88 from Data.gov, 4 from SAM.gov)
- Growth: **2,200% increase** in federal contracts
- Data Source: Data.gov (no API key, very reliable)
- Update Frequency: Daily at 3 AM EST

### Monthly Projection
- Current: ~40 new contracts per week
- Monthly: ~160 new federal contracts
- Annual: ~1,920 new federal contracts

---

## 🎯 Next Steps

### Immediate Actions
1. ✅ **Automated fetching is LIVE** - Runs daily at 3 AM EST
2. ✅ **Database has 92 federal contracts** - Up from 4 originally
3. ✅ **No SAM.gov API key needed** - Data.gov is more reliable

### Future Enhancements
1. **Email Notifications** - Alert when new high-value contracts are found
2. **Advanced Filtering** - AI-powered relevance scoring for cleaning contracts
3. **Multi-State Expansion** - Add more states beyond VA/MD/DC
4. **Historical Data** - Backfill contracts from past 12 months
5. **Competitor Tracking** - Monitor which companies are winning contracts

---

## 📞 Support

### View Status
- **Web Dashboard:** http://localhost:5000/admin-enhanced
- **Federal Contracts:** http://localhost:5000/federal-contracts
- **Manual Fetch:** http://localhost:5000/admin/auto-fetch-datagov

### Files
- **Main Script:** `auto_fetch_daily.py`
- **Cron Setup:** `setup_auto_fetch.sh`
- **Activity Log:** `daily_fetch.log`
- **Database:** `leads.db`

### Useful Commands
```bash
# Test fetch
python3 auto_fetch_daily.py

# View logs
tail -f daily_fetch.log

# Check database
python3 database_analysis.py

# Install cron job
./setup_auto_fetch.sh

# View cron jobs
crontab -l
```

---

**Status:** ✅ System operational and fetching daily  
**Last Manual Test:** November 5, 2025 at 6:34 AM  
**Result:** 39 new contracts added successfully
