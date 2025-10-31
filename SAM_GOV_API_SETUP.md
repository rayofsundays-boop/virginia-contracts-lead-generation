# SAM.gov API Setup Guide

## ✅ You've Updated Your SAM.gov API Key!

Now follow these steps to ensure it's working correctly on Render.

---

## 🔑 Step 1: Add API Key to Render

1. **Go to your Render Dashboard**
   - Visit: https://dashboard.render.com
   - Select your service: `virginia-contracts-lead-generation`

2. **Add Environment Variable**
   - Click **"Environment"** in the left sidebar
   - Click **"Add Environment Variable"**
   - Key: `SAM_GOV_API_KEY`
   - Value: `[paste your SAM.gov API key here]`
   - Click **"Save Changes"**

3. **Render will automatically redeploy** (takes 2-3 minutes)

---

## 📊 Step 2: Verify It's Working

After deployment completes (2-3 minutes), visit these URLs:

### Check Database Status
```
https://your-app.onrender.com/db-status
```

Look for:
- ✅ **SAM_GOV_API_KEY: SET** (green)
- ✅ **Federal Contracts: [number > 0]** (green)

### Force Database Initialization (if needed)
```
https://your-app.onrender.com/init-db
```

This will:
- Create all database tables
- Immediately fetch real contracts from SAM.gov
- Scrape Virginia local government websites
- Show success/error messages

---

## 🔍 Step 3: Check Render Logs

1. Go to Render Dashboard → Your Service → **Logs**

2. Look for these **SUCCESS messages**:
```
✅ Database tables initialized successfully
📡 Fetching real federal contracts from SAM.gov API...
Fetching contracts for NAICS 561720...
Fetching contracts for NAICS 561730...
Fetching contracts for NAICS 561790...
✅ Fetched 25 real contracts from SAM.gov
✅ Updated 25 real federal contracts from SAM.gov
⏰ SAM.gov scheduler started - will update federal contracts daily at 2 AM
⏰ Local Government scheduler started - will update city/county contracts daily at 3 AM
```

3. If you see **ERROR messages**:
```
❌ SAM_GOV_API_KEY not set
⚠️ No contracts fetched. Check SAM_GOV_API_KEY environment variable
Error fetching from SAM.gov: 403 Forbidden
```
→ Double-check the API key in Render Environment Variables

---

## 🎯 What Data Gets Fetched?

### Federal Contracts (SAM.gov API)
- **NAICS 561720**: Janitorial Services
- **NAICS 561730**: Landscaping Services  
- **NAICS 561790**: Other Services to Buildings and Dwellings
- **Location**: Virginia only (`placeOfPerformanceState=VA`)
- **Timeframe**: Last 30 days
- **Update Schedule**: Daily at 2:00 AM + on app startup

### Local Government Contracts (Web Scraping)
10 Virginia cities/counties:
- Hampton
- Norfolk
- Virginia Beach
- Newport News
- Chesapeake
- Portsmouth
- Suffolk
- Williamsburg
- James City County
- York County
- **Update Schedule**: Daily at 3:00 AM + on app startup

---

## 🐛 Troubleshooting

### Problem: "No leads are populating"

**Solution 1: Check API Key**
1. Visit `/db-status` on your live site
2. Confirm `SAM_GOV_API_KEY: SET` shows green ✅
3. If red ❌, add the key to Render Environment Variables

**Solution 2: Force Initialization**
1. Visit `/init-db` on your live site
2. Wait for success messages
3. Refresh your dashboard

**Solution 3: Check SAM.gov API Status**
1. Test your API key: https://open.gsa.gov/api/sam-gov-entity-api/
2. Make sure you're using the **v2** API key (not v1)
3. Verify your key hasn't expired

**Solution 4: Wait for Scheduled Updates**
- Initial fetch: 5-10 seconds after app starts
- Federal contracts: Daily at 2:00 AM
- Local government: Daily at 3:00 AM

### Problem: "403 Forbidden" from SAM.gov

**Causes:**
- Invalid API key
- API key not activated yet (takes 5-10 minutes after registration)
- Rate limit exceeded (100 requests/hour for free tier)

**Solutions:**
1. Wait 10 minutes after getting new API key
2. Verify key at: https://open.gsa.gov/api/sam-gov-entity-api/
3. Check if you need to upgrade to paid tier

### Problem: Some contracts missing details

**This is normal!** SAM.gov data varies:
- Some contracts have full details
- Others have minimal information
- Contract values are estimated if not provided
- Deadlines default to 30 days if not specified

---

## 📝 Environment Variables Checklist

Make sure these are ALL set in Render:

- ✅ `SAM_GOV_API_KEY` - Your SAM.gov API key
- ✅ `DATABASE_URL` - Auto-set by Render (PostgreSQL)
- ✅ `SECRET_KEY` - Random string for Flask sessions
- ✅ `MAIL_USERNAME` - Your Gmail address
- ✅ `MAIL_PASSWORD` - Gmail app-specific password
- ✅ `PAYPAL_CLIENT_ID` - PayPal app credentials
- ✅ `PAYPAL_CLIENT_SECRET` - PayPal app credentials
- ✅ `PAYPAL_MODE` - `sandbox` or `live`
- ✅ `PAYPAL_MONTHLY_PLAN_ID` - Monthly subscription plan ID
- ✅ `PAYPAL_ANNUAL_PLAN_ID` - Annual subscription plan ID

---

## 🎉 Success Indicators

You'll know it's working when:

1. **`/db-status` shows:**
   - ✅ SAM_GOV_API_KEY: SET
   - ✅ Federal Contracts: 15-50+ contracts
   - ✅ Local Government Contracts: 10-30+ contracts

2. **Dashboard displays:**
   - Real federal cleaning contracts with SAM.gov links
   - Virginia city/county procurement opportunities
   - Contract details: agency, location, value, deadline

3. **Render logs show:**
   - Successful API fetches every startup
   - Daily updates at 2 AM and 3 AM
   - No API errors or warnings

---

## 🔗 Useful Links

- **SAM.gov API Portal**: https://open.gsa.gov/api/sam-gov-entity-api/
- **SAM.gov Website**: https://sam.gov
- **Render Dashboard**: https://dashboard.render.com
- **Your App Status**: `/db-status`
- **Force Database Init**: `/init-db`

---

## 🆘 Still Having Issues?

1. Check Render logs for specific error messages
2. Visit `/db-status` to see exactly what's missing
3. Verify API key is valid at SAM.gov portal
4. Try visiting `/init-db` to force re-initialization
5. Wait 5-10 minutes after adding API key (activation time)

**The most common issue is simply forgetting to add the API key to Render!** Double-check your Environment Variables. 🔑
