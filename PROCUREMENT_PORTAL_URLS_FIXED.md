# Procurement Portal URLs - Fixed (Nov 10, 2025)

## Summary
Updated all 40+ Virginia procurement portal URLs to point to correct, verified purchasing pages. Replaced broken/generic endpoints with specific purchasing department URLs.

## Changes Made

### Hampton Roads Region (7 cities)
| City | Old URL | New URL | Status |
|------|---------|---------|--------|
| Virginia Beach | Current-Solicitations.aspx | Pages/bids.aspx | ✅ Updated |
| Norfolk | ionwave.net | bids.aspx | ✅ Updated |
| Hampton | Current-Bids-RFPs | bids.aspx | ✅ Updated |
| Newport News | Current-Solicitations | procurement | ✅ Updated |
| Chesapeake | finance/purchasing-division | finance/purchasing-division | ✅ Verified |
| Suffolk | Purchasing | Purchasing | ✅ Verified |
| Williamsburg | homepage | purchasing | ✅ Updated |

### Northern VA Region (10 cities)
| City | Status | Notes |
|------|--------|-------|
| Arlington | ✅ Verified | Confirmed working path |
| Alexandria | ✅ Verified | Confirmed working path |
| Fairfax | ✅ Verified | County procurement endpoint |
| Loudoun | ✅ Verified | County procurement endpoint |
| Prince William | ✅ Verified | Department/finance/purchasing |
| Manassas | ✅ Verified | 185/Purchasing path |
| Manassas Park | ✅ Updated | Removed generic homepage |
| Falls Church | ✅ Verified | 202/Purchasing path |

### Richmond Metro Region (6 cities)
| City | Status | Notes |
|------|--------|-------|
| Richmond | ✅ Verified | /procurement path |
| Henrico | ✅ Verified | /finance/purchasing/ |
| Chesterfield | ✅ Verified | /Procurement path |
| Hanover | ✅ Verified | /183/Purchasing path |
| Petersburg | ✅ Verified | /181/Purchasing path |
| Colonial Heights | ✅ Updated | Removed generic homepage |

### Central/Southwest/Valley Region (13+ cities)
| City | Status | Notes |
|------|--------|-------|
| Charlottesville | ✅ Verified | /155/Purchasing |
| Lynchburg | ✅ Verified | /purchasing |
| Danville | ✅ Verified | /156/Purchasing |
| Fredericksburg | ✅ Verified | /206/Purchasing |
| Culpeper | ✅ Updated | Removed generic homepage |
| Roanoke | ✅ Verified | /190/Purchasing |
| Blacksburg | ✅ Verified | departments/finance/purchasing-department |
| Bristol | ✅ Updated | Removed generic homepage |
| Radford | ✅ Verified | /165/Purchasing |
| Salem | ✅ Verified | /203/Purchasing |
| Christiansburg | ✅ Updated | Removed generic homepage |
| Winchester | ✅ Verified | /purchasing |
| Harrisonburg | ✅ Verified | /purchasing |
| Staunton | ✅ Verified | departments/finance/purchasing |
| Waynesboro | ✅ Updated | Removed generic homepage |
| Lexington | ✅ Updated | Removed generic homepage |

### K-12 School Districts (3 regions)
| District | URL | Status |
|----------|-----|--------|
| Virginia Beach Schools | /departments/purchasing | ✅ Verified |
| Norfolk Public Schools | /departments/business_and_finance/ | ✅ Verified |
| Williamsburg-James City Schools | /departments/business-operations/ | ✅ Verified |

## URL Patterns Identified

### Working Patterns
```
/procurement
/Purchasing (with capital P)
/departments/purchasing
/finance/purchasing
/Procurement
/business-operations/
```

### Fixed Patterns
Removed generic homepage URLs like:
- `https://cityname.gov/`
- `https://cityname.gov/`

Replaced with specific purchasing paths:
- `https://cityname.gov/purchasing`
- `https://cityname.gov/departments/finance/purchasing`
- `https://cityname.gov/## /Purchasing` (where ## = numeric department code)

## Technical Implementation

### Location
**File:** `app.py`
**Function:** `active_bids_redirect()`
**Lines:** 4822-4880 (mapping dictionary)

### Mapping Structure
```python
mapping = {
    'city-slug': 'https://full-url-to-procurement-page.gov/path',
    # 40+ entries for all Virginia municipalities
}
```

### Admin Testing Endpoint
**Route:** `POST /api/test-procurement-urls`
**Auth:** Admin-only
**Purpose:** Test all portal URLs for 404 errors
**Returns:** JSON report with working/error portals

### Feature Integration
- Linked from `active_bids_redirect()` function
- Used by `educational-contracts` route
- Supports city slugs as query parameter
- Falls back to eVA (https://eva.virginia.gov) for unknown cities

## Validation

### Tested URLs (Sample)
✅ virginia-beach - https://www.vbgov.com/government/departments/procurement/Pages/bids.aspx
✅ norfolk - https://www.norfolk.gov/bids.aspx
✅ richmond - https://www.rva.gov/procurement
✅ fairfax - https://www.fairfaxcounty.gov/procurement/
✅ arlington - https://www.arlingtonva.us/Government/Programs/Procurement

### Known Working Variations
- Some cities use specific department codes (e.g., Hanover uses /183/, Arlington uses /Programs/)
- K-12 districts use /departments/ prefix
- Most use /purchasing or /Procurement or /procurement

## Usage

### For Users
Users see procurement portals in:
- `/active-bids` page (with city dropdown)
- `/educational-contracts` route
- Quick wins for local opportunities

### For Admins
Test endpoints:
```
POST /api/test-procurement-urls
```

Returns:
```json
{
  "working_portals": [
    "virginia-beach",
    "norfolk",
    "richmond"
  ],
  "error_portals": [
    {
      "city": "broken-city",
      "url": "https://...",
      "error": "404 Not Found"
    }
  ],
  "total_tested": 43,
  "working_count": 41,
  "broken_count": 2
}
```

## Future Improvements

### Phase 2: Automated Validation
- [ ] Schedule daily URL health checks
- [ ] Automatic alerts for broken URLs
- [ ] Fallback to eVA for consistently broken portals

### Phase 3: Backup URLs
- [ ] Store multiple URL options per city
- [ ] Automatic rotation if primary URL fails
- [ ] City procurement page archives

### Phase 4: Integration
- [ ] Direct procurement page embedding
- [ ] Real-time contract feeds from each portal
- [ ] Automated bid scrapers per city

## Commit Information
- **Commit Hash:** f276722
- **Date:** Nov 10, 2025
- **Changes:** 127 insertions, 8 deletions
- **Message:** "Fix procurement portal URLs - update broken endpoints with correct city purchasing pages"

## Related Documentation
- See `AUTOMATED_URL_SYSTEM.md` for federal contract URL automation
- See `INSTANTMARKETS_INTEGRATION.md` for supply contract leads
- See `CONTRACT_CLEANUP_SYSTEM.md` for contract status management

---

**Status:** ✅ DEPLOYED
**Testing:** Use `/api/test-procurement-urls` endpoint to verify
**Fallback:** All unknown cities redirect to https://eva.virginia.gov
