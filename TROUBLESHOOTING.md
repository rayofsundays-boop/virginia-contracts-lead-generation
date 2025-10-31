# 🔧 Troubleshooting: "Leads Aren't Generating"

## ⚡ Quick Diagnostic Checklist

Follow these steps **in order** to identify and fix the issue:

---

## Step 1: Check Render Environment Variables ⚙️

**Go to:** Render Dashboard → Your Service → Environment

**Required Variables:**

| Variable | Status | How to Check |
|----------|--------|--------------|
| `SAM_GOV_API_KEY` | ⚠️ **REQUIRED** | Should be 32+ characters |
| `DATABASE_URL` | ✅ Auto-set | Starts with `postgresql://` |
| `SECRET_KEY` | ✅ Required | Any long random string |
| `MAIL_USERNAME` | Optional | Your Gmail address |
| `MAIL_PASSWORD` | Optional | Gmail app password |

**⚠️ If `SAM_GOV_API_KEY` is missing:**
1. Get free key: https://open.gsa.gov/api/sam-gov-entity-api/
2. Add to Render Environment
3. Save (triggers auto-redeploy)
4. Wait 2-3 minutes

---

## Step 2: Visit Diagnostic URLs 🔍

**After deployment completes, visit these URLs on your LIVE site:**

### A. Database Status Check
```
https://YOUR-APP-NAME.onrender.com/db-status
```

**What to look for:**

✅ **GOOD:**
```
SAM_GOV_API_KEY: ✅ SET (32 chars)
Federal Contracts: 15-50+
Local Government Contracts: 10-30+
```

❌ **BAD:**
```
SAM_GOV_API_KEY: ❌ NOT SET
Federal Contracts: 0
Local Government Contracts: 0
```

### B. Force Database Initialization
```
https://YOUR-APP-NAME.onrender.com/init-db
```

**What happens:**
- Creates all database tables
- Fetches real federal contracts from SAM.gov
- Scrapes Virginia local government websites
- Shows success/error messages

**Expected output:**
```
✅ PostgreSQL database tables initialized successfully
📡 Fetching real federal contracts from SAM.gov API...
Fetching contracts for NAICS 561720...
✅ Successfully loaded 25 REAL federal contracts from SAM.gov
```

---

## Step 3: Check Render Logs 📊

**Go to:** Render Dashboard → Your Service → Logs

### Look for SUCCESS messages:

```
✅ PostgreSQL database tables initialized successfully
📡 Fetching real federal contracts from SAM.gov API...
Fetching contracts for NAICS 561720...
Fetching contracts for NAICS 561730...
Fetching contracts for NAICS 561790...
✅ Fetched 25 real contracts from SAM.gov
✅ Successfully loaded 25 REAL federal contracts from SAM.gov
⏰ SAM.gov scheduler started
⏰ Local Government scheduler started
✅ Updated 15 real local government contracts from Virginia cities
```

### Look for ERROR messages:

❌ **Missing API Key:**
```
SAM_GOV_API_KEY not set
⚠️ No contracts fetched. Check SAM_GOV_API_KEY environment variable
```
**FIX:** Add `SAM_GOV_API_KEY` to Render Environment

❌ **API Error:**
```
Error fetching from SAM.gov: 403 Forbidden
Error fetching from SAM.gov: 401 Unauthorized
```
**FIX:** 
- Verify API key is correct
- Wait 10 minutes if just created (activation time)
- Check API status: https://open.gsa.gov/api/sam-gov-entity-api/

❌ **Database Error:**
```
relation "federal_contracts" does not exist
no such table: contracts
```
**FIX:** Visit `/init-db` to create tables

---

## Step 4: Common Issues & Solutions 🛠️

### Issue 1: "SAM_GOV_API_KEY not set"

**Symptoms:**
- `/db-status` shows: ❌ NOT SET
- Federal contracts: 0
- Logs show: "No contracts fetched"

**Solution:**
1. Get API key: https://open.gsa.gov/api/sam-gov-entity-api/
2. Add to Render: Environment → `SAM_GOV_API_KEY` = `your-key`
3. Save (auto-redeploys)
4. Wait 2-3 minutes
5. Visit `/init-db` to force fetch

---

### Issue 2: "API Key is Set But No Data"

**Symptoms:**
- `/db-status` shows: ✅ SET
- Federal contracts: Still 0
- No error messages

**Possible Causes:**
1. **API key just created** (not activated yet)
   - **FIX:** Wait 10 minutes after registration
   
2. **Wrong API version** (using v1 instead of v2)
   - **FIX:** Get new v2 key from portal
   
3. **Rate limit exceeded** (100 requests/hour on free tier)
   - **FIX:** Wait 1 hour or upgrade to paid tier
   
4. **Database not initialized**
   - **FIX:** Visit `/init-db`

5. **Background threads not started**
   - **FIX:** Check Render logs for scheduler messages
   - **FIX:** Restart service in Render dashboard

---

### Issue 3: "Some Contracts But Not Many"

**Symptoms:**
- Federal contracts: 1-5 (expected 15-50+)
- Local contracts: 1-3 (expected 10-30+)

**Possible Causes:**
1. **Limited date range** (only searching recent contracts)
   - **FIX:** Visit `/init-db` (fetches last 90 days)
   
2. **Narrow search criteria** (only specific NAICS codes)
   - This is normal - cleaning contracts are niche
   
3. **Local government websites changed** (scraper can't parse)
   - Some cities may have 0 current opportunities
   - This is normal - procurement cycles vary

---

### Issue 4: "No Commercial/Residential Leads"

**Symptoms:**
- Commercial opportunities: 0
- Residential leads: 0

**This is NORMAL!**

These leads come from **user submissions only**:
- Users fill out "Request Commercial Lead" form
- Users fill out "Request Residential Service" form
- Property owners contact you directly

**They do NOT auto-populate like government contracts.**

---

### Issue 5: "Data Was There, Now Gone"

**Symptoms:**
- Had contracts before
- Now showing 0
- Recent deployment

**Possible Causes:**
1. **Database was reset** (new deployment with clean DB)
   - **FIX:** Visit `/init-db` to repopulate
   
2. **Old contracts expired** (auto-cleanup runs daily)
   - Federal: Deleted after 90 days
   - Local: Deleted after 120 days
   - **FIX:** This is normal, new contracts fetch daily

3. **Using different database** (switched from SQLite to PostgreSQL)
   - **FIX:** Visit `/init-db` on new database

---

## Step 5: Manual Testing 🧪

If still having issues, test the scrapers locally:

```bash
cd "/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE"

# Test SAM.gov fetcher
python3 test_scrapers.py

# Or test directly
python3 -c "
from sam_gov_fetcher import SAMgovFetcher
fetcher = SAMgovFetcher()
contracts = fetcher.fetch_va_cleaning_contracts(30)
print(f'Fetched {len(contracts)} contracts')
for c in contracts[:3]:
    print(f'- {c[\"title\"][:60]}...')
"
```

**Expected output:**
```
Fetched 25 contracts
- Janitorial Services - VA Medical Center Norfolk
- Custodial Services - Joint Base Langley-Eustis  
- Building Maintenance - Federal Courthouse Hampton
```

**If 0 contracts:**
- Check if `SAM_GOV_API_KEY` is set in your environment
- Verify API key works at: https://api.sam.gov/opportunities/v2/search?api_key=YOUR_KEY

---

## Step 6: Database Health Check 🏥

**If you have PostgreSQL database issues:**

1. **Check database connection:**
   ```
   Visit: /db-status
   Look for: DATABASE_URL should start with postgresql://
   ```

2. **Verify tables exist:**
   - federal_contracts
   - contracts (local government)
   - commercial_opportunities
   - residential_leads
   - leads (users)

3. **If tables missing:**
   - Visit `/init-db` 
   - Check Render logs for errors

4. **If connection errors:**
   - Render may have restarted database
   - Visit Render Dashboard → Database → Check status
   - May need to update `DATABASE_URL` if changed

---

## Step 7: Timeline Expectations ⏰

**Understanding when data appears:**

| Data Type | Update Schedule | Initial Fetch |
|-----------|----------------|---------------|
| Federal Contracts | Daily at 2:00 AM | 5 sec after startup |
| Local Government | Daily at 3:00 AM | 10 sec after startup |
| Commercial Leads | User-submitted | Manual entry |
| Residential Leads | User-submitted | Manual entry |

**After deployment:**
- 0-10 seconds: App starts
- 5 seconds: Federal contracts start fetching (30-60 seconds)
- 10 seconds: Local scraper starts (60-120 seconds)
- 2-3 minutes: All data should be populated

**If waiting 5+ minutes and still no data:**
- Check Render logs for errors
- Visit `/db-status` to see what's missing
- Visit `/init-db` to force re-fetch

---

## Step 8: Last Resort 🆘

**If NOTHING works:**

1. **Check Render Service Status**
   - Is service running? (should show green checkmark)
   - Recent failed deployments? (check Deploy tab)
   - Build errors? (check build logs)

2. **Check PostgreSQL Database**
   - Database online? (Render Dashboard → Database)
   - Disk space? (should have available space)
   - Connection limits? (max 100 connections)

3. **Manual Database Reset**
   ```
   Render Dashboard → Your Service → Manual Deploy
   Clear cache and redeploy
   Visit /init-db immediately after
   ```

4. **Contact Support**
   - Provide Render logs (last 100 lines)
   - Screenshots of `/db-status`
   - Error messages from `/init-db`

---

## ✅ Success Indicators

**You'll know it's working when:**

1. **`/db-status` shows:**
   ```
   ✅ SAM_GOV_API_KEY: SET (32 chars)
   ✅ Federal Contracts: 25
   ✅ Local Government Contracts: 18
   ✅ Registered Users: 0 (or more)
   ```

2. **Dashboard displays real contracts:**
   - Federal agencies (VA Medical Centers, military bases)
   - Virginia cities (Hampton, Norfolk, VA Beach, etc.)
   - Real deadlines and values
   - Working SAM.gov links

3. **Render logs show:**
   ```
   ✅ Successfully loaded 25 REAL federal contracts
   ✅ Updated 18 real local government contracts
   ⏰ SAM.gov scheduler started
   ⏰ Local Government scheduler started
   ```

---

## 📞 Quick Reference

| Issue | Solution URL |
|-------|-------------|
| Check database status | `/db-status` |
| Force data refresh | `/init-db` |
| View logs | Render Dashboard → Logs |
| Add API key | Render Dashboard → Environment |
| Get SAM.gov key | https://open.gsa.gov/api/sam-gov-entity-api/ |
| Test locally | `python3 test_scrapers.py` |

---

## 🎯 Most Common Fix

**90% of "no leads generating" issues are:**

**Missing SAM_GOV_API_KEY in Render environment variables!**

1. Go to: https://open.gsa.gov/api/sam-gov-entity-api/
2. Get free API key (2 minutes)
3. Add to Render Environment: `SAM_GOV_API_KEY` = `your-key`
4. Save (auto-redeploys)
5. Wait 3 minutes
6. Visit `/db-status` - should see contracts!

**That's it!** 🎉
