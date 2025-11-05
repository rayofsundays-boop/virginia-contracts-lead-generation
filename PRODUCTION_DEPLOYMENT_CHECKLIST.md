# 🚀 PRODUCTION DEPLOYMENT - QUICK REFERENCE

## ✅ What Was Fixed

### 1. Hero Video
- **Before**: 8 cities
- **After**: 12 cities (Hampton, Suffolk, Virginia Beach, Newport News, Williamsburg, Richmond, Norfolk, Chesapeake, Arlington, Alexandria, Fairfax, Washington DC)

### 2. Fake Data Scripts
**DISABLED** (renamed to .DISABLED):
- `add_supplier_requests.py` - Generated 288+ fake supplier requests
- `populate_federal_contracts.py` - May add sample contracts
- `quick_populate.py` - Quick population script

## 🎯 REQUIRED ACTIONS ON RENDER

### Step 1: Delete Fake Supply Contracts
```bash
# Go to: Render Dashboard → Web Service → Shell
psql $DATABASE_URL

# Run this SQL:
DELETE FROM supply_contracts;

# Verify:
SELECT COUNT(*) FROM supply_contracts;
-- Should return: 0

# Exit:
\q
```

### Step 2: Set API Key
1. Go to: Render Dashboard → Web Service → Environment
2. Add variable:
   - **Key**: `SAM_GOV_API_KEY`
   - **Value**: `[Get from https://open.gsa.gov/api/sam-api/]`
3. Click "Save Changes"
4. App will auto-restart

### Step 3: Verify Success
Visit: `https://virginia-contracts-lead-generation.onrender.com/quick-wins`

**Should see:**
- ✅ ~100 real supplier opportunities
- ✅ URLs: `https://sam.gov/opp/.../view`
- ✅ Real agency names (not "Commercial Properties")
- ✅ Legitimate phone numbers (not 555-xxxx)

**Should NOT see:**
- ❌ URLs with `vacontractshub.com/supplier-requests`
- ❌ "Bulk Supplier Request" titles
- ❌ Fake agencies or synthetic data

## 📊 Expected App Logs After Restart

```
🔍 Checking supply_contracts table...
📦 Supply contracts table is empty - auto-populating now...
🔍 Fetching REAL nationwide supplier opportunities from SAM.gov...
  Found 25 opportunities for NAICS 325612
  Found 27 opportunities for NAICS 424690
  Found 23 opportunities for NAICS 561720
  Found 26 opportunities for NAICS 337127
✅ Successfully populated 101 REAL nationwide supplier opportunities from SAM.gov
```

## 🆘 If Something Goes Wrong

### No opportunities after restart?
1. Check logs: Render Dashboard → Web Service → Logs
2. Verify `SAM_GOV_API_KEY` is set: Shell → `echo $SAM_GOV_API_KEY`
3. Manual trigger: Visit `/admin/repopulate-supply-contracts`

### Fake data still appears?
1. Verify latest commit deployed: Check "Deploy Logs"
2. Clear build cache: Manual Deploy → "Clear build cache & deploy"
3. Double-check supply_contracts table is empty

### API key issues?
1. Verify key is valid at: https://open.gsa.gov/api/sam-api/
2. Check key permissions (should allow opportunities API access)
3. Try regenerating key if needed

## ✅ Success Checklist

- [ ] Deleted all supply_contracts on Render PostgreSQL
- [ ] Set `SAM_GOV_API_KEY` environment variable
- [ ] App restarted successfully
- [ ] Logs show "Successfully populated X REAL nationwide opportunities"
- [ ] Quick Wins page shows ~100 opportunities
- [ ] All URLs are sam.gov links (not fake)
- [ ] No synthetic agency names or 555 phone numbers
- [ ] Hero video shows 12 cities correctly

---

**Deployment Date**: _____________
**Deployed By**: _____________
**Status**: ⬜ Complete ⬜ In Progress ⬜ Issues

---

For detailed instructions, see: `COMPLETE_FIX_FAKE_DATA.md`
