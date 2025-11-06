# URL Manager - Quick Reference Guide

## ✅ Deployment Status
**Latest Deployment:** Commit `0d7f5a9` (Nov 6, 2025)  
**Status:** ✅ Live and working  
- Homepage: https://virginia-contracts-lead-generation.onrender.com/ ✅ HTTP 200
- Local Procurement: https://virginia-contracts-lead-generation.onrender.com/local-procurement ✅ HTTP 200

## 🔧 URL Correction Dashboard

### Access URL Manager
**Direct Link:** https://virginia-contracts-lead-generation.onrender.com/admin/url-manager

**Alternative Routes:**
1. Login to admin account
2. Go to Admin Enhanced dashboard
3. Click "URL Manager" or navigate to `/admin/url-manager`

---

## 📊 Features Available

### 1. **Statistics Dashboard**
View real-time URL health across three contract types:
- **Federal Contracts** (SAM.gov URLs)
- **Supply Contracts** (Website URLs)
- **Local Contracts** (Website URLs)

**Metrics:**
- Total count
- Contracts with URLs
- Broken/invalid URLs
- Success percentage with visual progress bar

---

### 2. **Quick Actions**

#### 🗑️ Remove Broken URLs
**Button:** "Remove Broken URLs"
- Finds all invalid URLs (example.com, non-http, NULL)
- Sets them to NULL for AI regeneration
- Works across all three contract tables
- Shows count of removed URLs

#### ✨ AI Generate URLs
**Button:** "AI Generate URLs"
- Links to existing `/admin-enhanced?section=populate-urls`
- Uses OpenAI GPT-4 to create appropriate URLs
- Processes up to 20 contracts per request
- Based on contract title, agency, location, NAICS code

#### 🔍 Verify All URLs
**Button:** "Verify All URLs"
- Links to `/admin/track-all-urls`
- Checks URL accessibility
- Analyzes URL quality and type
- Provides recommendations

#### 📋 View All URLs
**Button:** "View All URLs"
- Links to `/admin-enhanced?section=manage-urls`
- Browse paginated list of all contracts
- Filter by contract type
- Search functionality

---

### 3. **Tabbed Browse & Edit**

Three tabs show broken/missing URLs:
1. **Federal Tab** - Up to 10 broken federal contracts
2. **Supply Tab** - Up to 10 broken supply contracts  
3. **Local Tab** - Up to 10 broken local contracts

**Each Row Shows:**
- Contract ID
- Title (first 50 characters)
- Agency name
- Current URL status (broken/missing indicator)
- Edit button

---

### 4. **Individual URL Editing**

**How to Edit:**
1. Click "Edit" button on any contract
2. Modal opens showing contract details
3. Enter new URL or leave blank (sets to NULL)
4. Click "Save URL"

**URL Validation:**
- Must be valid http/https URL
- Can be left blank to set NULL (for AI regeneration)
- Saves immediately to database

---

## 🎯 Common Workflows

### Workflow 1: Clean All Broken URLs
1. Go to URL Manager
2. Click "Remove Broken URLs"
3. Confirm action
4. Click "AI Generate URLs"
5. Select contract types and quantity
6. Wait for AI to populate URLs

### Workflow 2: Fix Single Contract
1. Navigate to broken contract in tabs
2. Click "Edit" button
3. Enter correct URL
4. Save

### Workflow 3: Bulk Verification
1. Click "Verify All URLs"
2. Select contract types to verify
3. Review AI analysis results
4. Export or view tracking data

---

## 🔗 Existing URL Tools Integration

Your URL Manager integrates with these existing tools:

1. **Admin Enhanced - Manage URLs**  
   `/admin-enhanced?section=manage-urls`
   - Paginated list with search
   - Dynamic filtering

2. **Populate Missing URLs**  
   `/admin-enhanced?section=populate-urls`
   - Manual trigger for AI URL generation
   - Preview before applying

3. **Track All URLs**  
   `/admin/track-all-urls`
   - AI-powered URL verification
   - Accessibility checks
   - Quality scoring

4. **Track Supply URLs**  
   `/admin/track-supply-urls`
   - Specific to supply contracts
   - Quick Win prioritization

5. **Fix SAM URLs**  
   `/admin/fix-sam-urls`
   - Bulk federal contract URL regeneration
   - NAICS-based SAM.gov URL builder

---

## 📈 URL Health Indicators

**Color Codes:**
- 🟢 **Green:** Valid http/https URL
- 🔴 **Red:** Broken (example.com, invalid format)
- ⚪ **Gray:** Missing (NULL or empty)

**Progress Bars:**
Shows percentage of contracts with valid URLs:
- Calculates: (Total - Broken) / Total × 100%
- Updates in real-time

---

## 🚀 Best Practices

### Regular Maintenance
1. **Weekly:** Check URL Manager dashboard
2. **After imports:** Run "Remove Broken URLs" then "AI Generate"
3. **Monthly:** Full verification with "Verify All URLs"

### Quality Control
1. Always verify AI-generated URLs manually for critical contracts
2. Set broken URLs to NULL instead of keeping placeholder URLs
3. Use bulk operations for efficiency

### Emergency Fixes
If all URLs break:
1. Click "Remove Broken URLs" (sets to NULL)
2. Click "AI Generate URLs" (repopulates)
3. Run "Verify All URLs" (confirms quality)

---

## 🛠️ Technical Details

**Database Tables:**
- `federal_contracts.sam_gov_url`
- `supply_contracts.website_url`
- `contracts.website_url`

**Broken URL Detection:**
- Contains "example"
- Does not start with "http"
- Is NULL or empty string

**URL Setting Options:**
- Valid URL: Updates to new URL
- Blank/NULL: Allows AI regeneration
- Invalid: Rejected by browser validation

---

## 📞 Support

**Issue:** Can't access URL Manager  
**Solution:** Must be logged in as admin

**Issue:** Changes not saving  
**Solution:** Check browser console for errors, verify admin session

**Issue:** AI generate not working  
**Solution:** Check OpenAI API key in environment variables

---

## 🎉 Ready to Use!

Your URL Manager is now live at:
**https://virginia-contracts-lead-generation.onrender.com/admin/url-manager**

Wait ~5 minutes for the latest deployment (commit `0d7f5a9`) to complete, then:
1. Log in as admin
2. Navigate to `/admin/url-manager`
3. Start correcting URLs!

---

*Last Updated: November 6, 2025*
*Deployment: Commit 0d7f5a9*
