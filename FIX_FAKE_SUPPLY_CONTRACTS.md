# Fix for Fake Supply Contracts on Production

## Problem
The `/supply-contracts` page shows:
- **3 Quick Wins** with fake/placeholder website URLs
- Synthetic data that looks real but isn't

## Root Cause
The `populate_supply_contracts()` function inserts synthetic/demo data including:
1. VA Medical Center Hampton - fake vafbo URL
2. Naval Station Norfolk - fake navy URL  
3. Newport News Public Schools - fake NNPS URL
4. 50+ other fake supplier requests

## Solution: Delete ALL Fake Supply Contracts on Render

### Step 1: Access Render PostgreSQL Database

SSH into your Render web service or use Render's database console:

```bash
# Option A: Via Render Dashboard
1. Go to your Render dashboard
2. Click on your PostgreSQL database
3. Click "Connect" → "External Connection"
4. Use psql command provided

# Option B: Via web service shell
# On Render dashboard, go to your web service → Shell tab
```

### Step 2: Run SQL Commands

```sql
-- Check current supply contracts
SELECT COUNT(*) FROM supply_contracts;

-- See examples of fake data
SELECT title, agency, website_url FROM supply_contracts LIMIT 5;

-- CREATE BACKUP FIRST (optional but recommended)
CREATE TABLE supply_contracts_backup_20251105 AS SELECT * FROM supply_contracts;

-- DELETE ALL FAKE SUPPLY CONTRACTS
DELETE FROM supply_contracts;

-- Verify deletion
SELECT COUNT(*) FROM supply_contracts;
-- Should return: 0
```

### Step 3: Prevent Future Auto-Population

The fake data comes from `populate_supply_contracts()` function in app.py (lines 15855-16000+).

**Option A: Quick Fix - Disable Auto-Population on Startup**

Find this code in `app.py` (around line 16026-16040):
```python
# Auto-populate supply contracts only if table is empty
try:
    count_result = db.session.execute(text('SELECT COUNT(*) FROM supply_contracts')).fetchone()
    existing_count = count_result[0] if count_result else 0
    
    if existing_count == 0:
        print("🔍 Supply contracts table is empty - attempting auto-population...")
        try:
            new_count = populate_supply_contracts(force=False)
            print(f"✅ SUCCESS: Auto-populated {new_count} supply contracts on startup!")
        except Exception as e:
            print(f"⚠️  Could not auto-populate supply contracts: {e}")
except Exception as e:
    print(f"⚠️  WARNING: Could not auto-populate supply contracts: {e}")
```

**COMMENT IT OUT:**
```python
# DISABLED: Do not auto-populate fake supply contracts
# Auto-population disabled - only use real SAM.gov data
print("ℹ️  Supply contract auto-population disabled (fake data removed)")
```

**Option B: Better Fix - Only Use Real SAM.gov Data**

Modify `populate_supply_contracts()` to ONLY use real API data:
1. Keep the `fetch_international_cleaning()` call
2. Delete ALL the `supplier_requests = [...]` synthetic data array
3. Return early if no real data found

### Step 4: Update Admin Routes

Update these admin routes to prevent re-population:
- `/admin/repopulate-supply-contracts` - Disable or show warning
- `/admin/populate-if-empty` - Skip supply contracts section

### Step 5: Verify on Production

After changes:
1. Visit: https://virginia-contracts-lead-generation.onrender.com/supply-contracts
2. Should show: **0 Quick Wins** (correct)
3. No fake website links

## Alternative: Show Only Real Federal Contracts

Instead of supply contracts, redirect `/supply-contracts` to show real SAM.gov opportunities:

```python
@app.route('/supply-contracts')
@login_required
def quick_wins():
    # Redirect to real federal contracts instead
    return redirect(url_for('federal_contracts'))
```

## Summary

✅ **DO THIS:**
1. Delete all supply_contracts via PostgreSQL on Render
2. Disable auto-population in app.py
3. Verify production site shows 0 quick wins
4. Only add REAL verified opportunities going forward

❌ **DON'T:**
- Don't re-populate with fake data
- Don't use placeholder websites
- Don't use synthetic supplier requests

## Need Real Supply Opportunities?

If you want real supply/quick win contracts:
1. Use SAM.gov API with proper search filters
2. Manually verify each opportunity
3. Ensure all website URLs are real and working
4. Add data_source field to track where it came from

---

**Created:** November 5, 2025
**Issue:** Fake supply contracts showing on production
**Status:** Ready to implement on Render
