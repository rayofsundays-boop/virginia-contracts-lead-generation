# 🔗 Fix Broken Website URL - Recreation Centers Network Cleaning Contract

## Issue Identified

**Contract:** Recreation Centers Network Cleaning Contract  
**Agency:** Virginia Beach Parks & Recreation  
**Reference:** VA-LOCAL-00112  
**Current URL:** `https://www.vbgov.com/departments/procurement`  
**Status:** ❌ **URL IS BROKEN/INVALID**

The current URL returns "Invalid URL" and does not work.

## Root Cause

The URL `https://www.vbgov.com/departments/procurement` appears to be either:
1. **Incorrect path** - Wrong department structure
2. **Website changed** - Virginia Beach may have restructured their site
3. **Blocked/Down** - Site may be temporarily unavailable

## Recommended Fixes

### Option 1: Use General Parks & Recreation Page ✅
```sql
UPDATE contracts 
SET website_url = 'https://www.vbgov.com/government/departments/parks-recreation'
WHERE title = 'Recreation Centers Network Cleaning Contract';
```

### Option 2: Use City Procurement Portal ✅
```sql
UPDATE contracts 
SET website_url = 'https://www.vbgov.com/government/departments/finance/procurement/Pages/default.aspx'
WHERE title = 'Recreation Centers Network Cleaning Contract';
```

### Option 3: Set to NULL (Contact Agency Directly) ✅
```sql
UPDATE contracts 
SET website_url = NULL
WHERE title = 'Recreation Centers Network Cleaning Contract';
```

**Recommended:** Option 3 (NULL) + Display "Contact Agency Directly" message

## Why NULL Is Best for Local Government Contracts

Local government contracts often:
- ❌ Don't have individual contract detail pages
- ❌ Require attending pre-bid meetings
- ❌ Need direct contact with procurement office
- ✅ Should show phone/email instead of website link

### Better User Experience:
Instead of a broken link, show:
```
📞 Contact Agency Directly
   Virginia Beach Parks & Recreation
   Phone: (757) 385-4621
   Email: procurement@vbgov.com
   Website: www.vbgov.com/parks-recreation
```

## Implementation Steps

### Step 1: Update Database on Render
```bash
# SSH into Render web service or use Shell
psql $DATABASE_URL

# Option A: Set to NULL (recommended)
UPDATE contracts 
SET website_url = NULL
WHERE title = 'Recreation Centers Network Cleaning Contract';

# Option B: Use valid general page
UPDATE contracts 
SET website_url = 'https://www.vbgov.com/government/departments/parks-recreation/Pages/default.aspx'
WHERE title = 'Recreation Centers Network Cleaning Contract';

# Verify
SELECT id, title, website_url 
FROM contracts 
WHERE title LIKE '%Recreation Centers%';
```

### Step 2: Update Template Logic (contracts.html)

Update the template to handle NULL URLs better:

```html
{% if contract.website_url and contract.website_url != 'NULL' %}
    <a href="{{ contract.website_url }}" target="_blank" class="btn btn-outline-primary btn-sm">
        <i class="fas fa-external-link-alt me-2"></i>View Details
    </a>
{% else %}
    <button class="btn btn-outline-secondary btn-sm" disabled>
        <i class="fas fa-phone me-2"></i>Contact Agency Directly
    </button>
    <small class="text-muted d-block mt-2">
        Call procurement office for bid documents
    </small>
{% endif %}
```

### Step 3: Add Contact Information

Update the contract display to show contact info when URL is missing:

```python
# In app.py - contracts route
# Add contact info to each contract
contact_info = {
    'Virginia Beach Parks & Recreation': {
        'phone': '(757) 385-4621',
        'email': 'parks@vbgov.com',
        'procurement_page': 'https://www.vbgov.com/government/departments/parks-recreation'
    },
    'City of Hampton': {
        'phone': '(757) 727-6000',
        'email': 'procurement@hampton.gov',
        'procurement_page': 'https://www.hampton.gov/bids.aspx'
    },
    # Add more as needed
}
```

## Verification Checklist

After fix:
- [ ] URL is either valid OR set to NULL
- [ ] Template shows appropriate message for NULL URLs
- [ ] Contact information displayed for local contracts
- [ ] No "Invalid URL" or broken link errors
- [ ] Users can easily contact agency

## Related Contracts to Check

Run this query to find other potentially broken URLs:

```sql
-- Check all contracts with vbgov.com URLs
SELECT id, title, website_url 
FROM contracts 
WHERE website_url LIKE '%vbgov.com%';

-- Check all contracts with NULL or empty URLs
SELECT id, title, agency, website_url 
FROM contracts 
WHERE website_url IS NULL OR website_url = '' OR website_url = 'NULL'
LIMIT 20;

-- Check for other placeholder/fake URLs
SELECT id, title, website_url 
FROM contracts 
WHERE website_url LIKE '%placeholder%'
   OR website_url LIKE '%example.com%'
   OR website_url LIKE '%vacontractshub.com%';
```

## Prevention

To prevent future broken URLs:
1. ✅ Validate URLs before insertion (use requests.head())
2. ✅ Set NULL for local contracts without direct links
3. ✅ Provide contact info instead of forcing URL
4. ✅ Regular URL health checks (automated script)
5. ✅ Clear documentation that NULL is acceptable

---

**Created:** November 5, 2025  
**Issue:** Broken website URL for Recreation Centers contract  
**Status:** Documented - Requires database update on Render  
**Priority:** Medium - Affects user experience but workaround available
