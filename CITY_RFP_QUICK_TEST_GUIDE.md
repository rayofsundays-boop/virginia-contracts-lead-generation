# City RFP Finder - Quick Test Guide 🧪

**Issue Fixed:** "Find City RFPs (AI)" button now works with 4-tier fallback system  
**Deployment Date:** November 12, 2025  
**Test Estimated Time:** 5-10 minutes  

---

## 🚀 Quick Test Instructions

### **Test 1: Database Cache (Instant Results)**
**Time:** 30 seconds  
**Steps:**
1. Go to https://virginia-contracts-lead-generation.onrender.com/state-procurement-portals
2. Select "Virginia" from state dropdown
3. Click "Find City RFPs (AI)" button
4. Wait 10-60 seconds (first search will scrape portals)
5. **Expected Result:** List of RFPs with cities like Richmond, Norfolk, Virginia Beach
6. Click button again immediately
7. **Expected Result:** Instant results (< 1 second) from database cache
8. Check browser console → Should see "✅ Found X cached RFPs (< 7 days old)"

---

### **Test 2: Direct Portal Scraping (Virginia)**
**Time:** 2 minutes  
**Prerequisites:** Clear Virginia RFPs from database OR wait 7 days after Test 1  
**Steps:**
1. Go to `/state-procurement-portals`
2. Select "Virginia"
3. Click "Find City RFPs (AI)"
4. Open browser console (F12)
5. **Expected Console Logs:**
   ```
   🔍 Finding city RFPs for Virginia (VA)...
   📍 Found 8 known portals for Virginia
     🔍 Scraping Richmond, VA...
       ✅ Found keywords: janitorial, custodial, cleaning
     🔍 Scraping Norfolk, VA...
       ✅ Found keywords: janitorial, cleaning
     ...
   ✅ Direct scraping found X RFPs
   ```
6. **Expected Results:**
   - Modal shows "Finding RFPs in Virginia..."
   - After 10-60 seconds, modal shows results
   - RFPs list includes cities: Richmond, Norfolk, Virginia Beach, Chesapeake, Newport News, Hampton, Alexandria, Arlington
   - Each RFP has: title, city, deadline, contact info, URL
7. Click an RFP URL → Should open valid government procurement page

---

### **Test 3: California (Another Hardcoded State)**
**Time:** 2 minutes  
**Steps:**
1. Go to `/state-procurement-portals`
2. Select "California"
3. Click "Find City RFPs (AI)"
4. **Expected Cities Checked:** Los Angeles, San Diego, San Francisco, San Jose
5. Verify results appear (or "no RFPs" message if none currently active)
6. Check console → Should see "📍 Found 4 known portals for California"

---

### **Test 4: Texas (Another Hardcoded State)**
**Time:** 2 minutes  
**Steps:**
1. Go to `/state-procurement-portals`
2. Select "Texas"
3. Click "Find City RFPs (AI)"
4. **Expected Cities Checked:** Houston, Dallas, Austin, San Antonio
5. Verify results or helpful "no RFPs" message
6. Check console → Should see "📍 Found 4 known portals for Texas"

---

### **Test 5: OpenAI Fallback (State NOT in Database)**
**Time:** 3 minutes  
**Prerequisites:** OpenAI API key must be configured  
**Steps:**
1. Go to `/state-procurement-portals`
2. Select "Alabama" or "Montana" (states NOT in hardcoded portal database)
3. Click "Find City RFPs (AI)"
4. Open browser console
5. **Expected Console Logs:**
   ```
   🔍 Finding city RFPs for Alabama (AL)...
   📍 Found 0 known portals for Alabama (skipping direct scraping)
   🤖 Using OpenAI fallback for Alabama...
   ✅ AI identified 8 cities
     🔍 AI analyzing Birmingham...
       ✅ Found 2 RFPs
     🔍 AI analyzing Montgomery...
       ✅ Found 1 RFP
   ```
6. **Expected Results:**
   - Takes 30-90 seconds (AI is slower)
   - Shows 5-10 cities checked
   - RFPs have `source: 'openai_gpt4_fallback'`

**If OpenAI Key NOT Configured:**
- Should see helpful error message: "No active cleaning RFPs currently available in Alabama. Try checking back in a few days or explore nearby states."
- Message includes suggestion: "Check the state procurement portal page for statewide opportunities, or try a neighboring state."

---

### **Test 6: No Results State**
**Time:** 1 minute  
**Steps:**
1. Select a small state (e.g., Wyoming, Vermont)
2. Click "Find City RFPs (AI)"
3. **Expected Result:**
   ```json
   {
     "success": true,
     "message": "No active cleaning RFPs currently available in Wyoming. Try checking back in a few days or explore nearby states.",
     "rfps": [],
     "cities_checked": ["Unable to access city portals"],
     "cities_searched": 0,
     "state": "Wyoming",
     "source": "none",
     "suggestion": "Check the state procurement portal page for statewide opportunities, or try a neighboring state."
   }
   ```
4. Verify user sees helpful suggestion instead of just "0 RFPs found"

---

### **Test 7: Error Handling (Not Logged In)**
**Time:** 30 seconds  
**Steps:**
1. Log out of the application
2. Navigate directly to `/state-procurement-portals`
3. Try to click "Find City RFPs (AI)" button
4. **Expected Result:** Redirect to login page OR disable button with tooltip "Please login"

---

### **Test 8: Rate Limiting Verification**
**Time:** 2 minutes  
**Steps:**
1. Select Virginia
2. Clear database cache for Virginia (admin tool or SQL: `DELETE FROM city_rfps WHERE state_code = 'VA'`)
3. Click "Find City RFPs (AI)"
4. Open browser console
5. Note timestamps between city scraping logs:
   ```
   [12:00:15] 🔍 Scraping Richmond, VA...
   [12:00:18] 🔍 Scraping Norfolk, VA...  ← 3 seconds later
   [12:00:21] 🔍 Scraping Virginia Beach, VA...  ← 3 seconds later
   ```
6. **Expected:** 3-second delay between each city request
7. **Purpose:** Prevents IP bans from government servers

---

## ✅ Success Criteria

### **Must Pass (Critical)**
- ✅ Virginia returns RFPs (from cache or direct scraping)
- ✅ Cached results load in < 1 second
- ✅ Direct scraping checks 6-8 cities for Virginia
- ✅ Rate limiting enforced (3-second delays visible in console)
- ✅ No "0 RFPs found" generic error (unless truly no RFPs exist)
- ✅ User sees helpful suggestions when no results found

### **Should Pass (Important)**
- ✅ California returns RFPs (4 cities checked)
- ✅ Texas returns RFPs (4 cities checked)
- ✅ Florida returns RFPs (4 cities checked)
- ✅ New York returns RFPs (3 cities checked)
- ✅ RFP URLs are valid (click test)
- ✅ Contact emails/phones included where available

### **Nice to Have (Optional)**
- ✅ OpenAI fallback works for states not in database
- ✅ All 28 hardcoded portals return results
- ✅ Duplicate RFPs are filtered out
- ✅ RFP data includes deadline, estimated value, department

---

## 🐛 What to Check If Tests Fail

### **"No RFPs found" for Virginia**
**Possible Causes:**
1. All Virginia city portals are currently down → Check URLs manually
2. HTML structure changed → Update scraping logic in `scrape_city_portals()`
3. Keywords not matching → Verify "janitorial" or "cleaning" appears on pages
4. Database commit failed → Check console for "❌ Database commit error"

**Debug Steps:**
1. Open browser console
2. Look for error messages
3. Check which tier was used (cache, scraping, OpenAI, none)
4. Manually visit portal URLs (e.g., https://www.rva.gov/procurement-services/bids-rfps)
5. Check database: `SELECT * FROM city_rfps WHERE state_code = 'VA'`

### **"Timeout" or "Connection Error"**
**Possible Causes:**
1. Server firewall blocking requests
2. Portal website is down
3. Timeout too short (20 seconds)

**Debug Steps:**
1. Check console for "⏱️ Timeout for [City]" messages
2. Try accessing portal URL from browser directly
3. Increase timeout in code if needed (currently 20 seconds)

### **"OpenAI Fallback Not Working"**
**Possible Causes:**
1. `OPENAI_API_KEY` not set in environment variables
2. API rate limit exceeded
3. OpenAI API is down

**Debug Steps:**
1. Check console for "❌ AI city discovery error"
2. Verify API key: Terminal → `printenv | grep OPENAI`
3. Check OpenAI status: https://status.openai.com/

### **"Duplicate RFPs Appearing"**
**Possible Causes:**
1. Database insert logic not checking for existing RFPs
2. RFP number not unique

**Debug Steps:**
1. Check `rfp_number` values in database
2. Verify INSERT query uses ON CONFLICT clause (if implemented)
3. Manually deduplicate: `DELETE FROM city_rfps WHERE id NOT IN (SELECT MIN(id) FROM city_rfps GROUP BY rfp_number)`

---

## 📊 Expected Performance

| Test | Expected Time | Success Rate |
|------|---------------|--------------|
| Cached Results | < 1 second | 100% |
| Direct Scraping (VA) | 10-60 seconds | 85-95% |
| Direct Scraping (CA/TX/FL/NY) | 10-40 seconds | 80-90% |
| OpenAI Fallback | 30-90 seconds | 70-85% |
| No Results State | 5-20 seconds | 100% (with helpful message) |

---

## 📝 Test Results Template

```
CITY RFP FINDER TEST RESULTS
Date: [Date]
Tester: [Name]

Test 1 - Database Cache (Virginia):
[ ] PASS  [ ] FAIL
Notes: _______________________________________________

Test 2 - Direct Scraping (Virginia):
[ ] PASS  [ ] FAIL
Notes: _______________________________________________

Test 3 - California:
[ ] PASS  [ ] FAIL
Notes: _______________________________________________

Test 4 - Texas:
[ ] PASS  [ ] FAIL
Notes: _______________________________________________

Test 5 - OpenAI Fallback:
[ ] PASS  [ ] FAIL  [ ] SKIP (no API key)
Notes: _______________________________________________

Test 6 - No Results State:
[ ] PASS  [ ] FAIL
Notes: _______________________________________________

Test 7 - Error Handling:
[ ] PASS  [ ] FAIL
Notes: _______________________________________________

Test 8 - Rate Limiting:
[ ] PASS  [ ] FAIL
Notes: _______________________________________________

Overall Assessment:
[ ] READY FOR PRODUCTION
[ ] NEEDS FIXES
[ ] CRITICAL ISSUES FOUND

Critical Issues (if any):
_______________________________________________
_______________________________________________
_______________________________________________
```

---

## 🎉 Next Steps After Testing

### **If All Tests Pass:**
1. ✅ Mark CITY_RFP_REPAIR_COMPLETE.md as "DEPLOYED ✅"
2. ✅ Update copilot-instructions.md with new feature
3. ✅ Add to CHANGELOG.md
4. ✅ Consider expanding portal database (next 10 states)
5. ✅ Schedule daily background scraping (optional)

### **If Tests Fail:**
1. Document specific failures in test results template
2. Check console logs for error messages
3. Review CITY_RFP_DIAGNOSIS.md for troubleshooting
4. Contact developer with test results + console logs
5. Do NOT mark as deployed until fixed

---

**Quick Test Time:** 5-10 minutes  
**Full Test Time:** 20-30 minutes  
**Priority:** HIGH - Critical feature repair  
**User Impact:** HIGH - Main lead discovery tool  
