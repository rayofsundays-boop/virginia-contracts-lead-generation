# Instantmarkets.com Daily Lead Pull - Quick Setup Guide

## What's New ✨

Automated daily lead pull system that retrieves cleaning & janitorial service opportunities from **instantmarkets.com** and populates your supply contracts database.

## Key Features

| Feature | Details |
|---------|---------|
| **Schedule** | Daily at 5:00 AM EST (off-peak) |
| **Database** | supply_contracts table (PostgreSQL) |
| **Duplicates** | Automatically prevented via (title + agency + location) check |
| **Manual Trigger** | Admin API endpoint: `/api/trigger-instantmarkets-pull` |
| **Error Handling** | Network errors, parsing errors, and DB errors all handled gracefully |

## System Architecture

```
Application Startup (app.py)
    ↓
Create scheduler thread for instantmarkets.com
    ↓
Every 24 hours at 5 AM EST:
    ├─ Fetch listings from instantmarkets.com
    ├─ Parse HTML with BeautifulSoup
    ├─ Extract: title, agency, location, description, value, URL
    ├─ Check for duplicates in database
    ├─ Insert new leads into supply_contracts
    └─ Return count of leads added
```

## How It Works

### 1. **Automatic Daily Pull**
```
⏰ Runs at 5:00 AM EST every day
📍 Searches for "cleaning janitorial" services in Virginia
🔗 Extracts opportunity data from 50 listings
✅ Checks for duplicates
📊 Adds new leads to database
```

### 2. **Manual Trigger (Admin)**
```bash
POST /api/trigger-instantmarkets-pull

Response:
{
  "success": true,
  "message": "Successfully pulled 12 new leads from instantmarkets.com",
  "leads_added": 12
}
```

### 3. **Data Extracted**
- ✅ Project title
- ✅ Company/agency name
- ✅ Location (Virginia-focused)
- ✅ Project description
- ✅ Estimated budget/value
- ✅ Direct URL to opportunity
- ✅ Posted date
- ✅ Status: "open"

## Implementation Details

### Files Modified
- **app.py**
  - Added `fetch_instantmarkets_leads()` function (~100 lines)
  - Added `schedule_instantmarkets_updates()` scheduler (~10 lines)
  - Added `/api/trigger-instantmarkets-pull` endpoint (~15 lines)
  - Integrated scheduler into startup sequence

### Files Added
- **INSTANTMARKETS_INTEGRATION.md** - Complete technical documentation

### Commits
```
c80655a - Add daily instantmarkets.com lead pull
77bb888 - Add comprehensive documentation
```

## Monitoring & Logs

### Expected Log Output
```
🌐 Fetching leads from instantmarkets.com...
📊 Found 45 listings on instantmarkets.com
✅ Instantmarkets.com update complete: 12 new leads added, 33 duplicates skipped
```

### Watch for These Log Messages

**Success:**
```
⏰ Instantmarkets.com scheduler started - will fetch supply leads daily at 5 AM EST (off-peak)
```

**During Pull:**
```
📊 Found X listings on instantmarkets.com
✅ Instantmarkets.com update complete: Y new leads added, Z duplicates skipped
```

**Errors:**
```
❌ Network error fetching from instantmarkets.com: [error]
❌ Error parsing listing: [error]
❌ Error inserting lead: [error]
```

## Integration with Existing Systems

✅ **Fits into existing schedule:**
- 2 AM: Data.gov bulk updates
- 3 AM: Auto URL population
- 4 AM: USAspending.gov + Local government
- **5 AM: Instantmarkets.com** ← New

✅ **Uses existing infrastructure:**
- PostgreSQL database (supply_contracts table)
- Flask app routing
- Admin authentication
- Background threading
- Error handling patterns

✅ **No new dependencies required:**
- `requests` already installed
- `beautifulsoup4` already installed

## Testing

### Test 1: Verify Scheduler Started
1. Check application logs on startup
2. Look for: `✅ Instantmarkets.com daily lead pull enabled`

### Test 2: Manual Trigger
1. Log in as admin
2. Run: `POST /api/trigger-instantmarkets-pull`
3. Verify response shows leads added
4. Check database: `SELECT COUNT(*) FROM supply_contracts WHERE product_category = 'Cleaning Services'`

### Test 3: Verify Duplicates Prevented
1. Trigger pull twice in quick succession
2. First pull: "X new leads added"
3. Second pull: "0 new leads added, X duplicates skipped"

### Test 4: Check Data Quality
```sql
SELECT title, agency, location, estimated_value, website_url, created_at
FROM supply_contracts
WHERE product_category = 'Cleaning Services'
ORDER BY created_at DESC
LIMIT 10;
```

## Admin Controls

### Trigger Manual Pull
```javascript
// From admin panel, add button that calls:
fetch('/api/trigger-instantmarkets-pull', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'}
}).then(r => r.json()).then(data => {
  console.log(`Added ${data.leads_added} leads`);
});
```

### View Pull History
```sql
-- Check when leads were added
SELECT COUNT(*) as leads_count, DATE(created_at) as pull_date
FROM supply_contracts
WHERE product_category = 'Cleaning Services'
GROUP BY DATE(created_at)
ORDER BY pull_date DESC;
```

## Troubleshooting

### Problem: No leads being added
**Solution:**
1. Check if instantmarkets.com is accessible
2. Verify site HTML structure hasn't changed
3. Run manual trigger and check logs for parsing errors
4. Update CSS selectors if site redesigned

### Problem: Too many duplicates
**Solution:**
1. Check if title/agency/location extraction is correct
2. Review database for typos or inconsistencies
3. Add additional uniqueness criteria if needed

### Problem: Scheduler not running
**Solution:**
1. Check application logs for startup message
2. Verify app doesn't have other errors preventing startup
3. Check if background lock is being held
4. Restart application

## Performance Impact

✅ **Minimal:**
- Runs during off-peak hours (5 AM)
- Processes 50 listings max per pull
- Network request + parsing: ~5-10 seconds
- Database insert: ~100-500ms
- Doesn't block other scheduled tasks
- Uses daemon thread (non-blocking shutdown)

## Security Considerations

✅ **Admin-only endpoint**
- `/api/trigger-instantmarkets-pull` requires admin session

✅ **Input validation**
- All extracted data sanitized before DB insert
- SQL injection prevented via parameterized queries
- HTML parsed safely with BeautifulSoup

✅ **Error handling**
- No sensitive data in error messages
- Exceptions logged, not exposed to users

## Future Enhancements

1. **Multiple sites:** TaskRabbit, Upwork, Thumbtack
2. **Real-time updates:** Switch from daily to hourly
3. **Lead scoring:** AI-powered relevance ranking
4. **Notifications:** Alert users of hot leads
5. **Analytics:** Track conversion by source

## Quick Reference

| Item | Details |
|------|---------|
| Function | `fetch_instantmarkets_leads()` |
| Scheduler | `schedule_instantmarkets_updates()` |
| Endpoint | `POST /api/trigger-instantmarkets-pull` |
| Database Table | `supply_contracts` |
| Run Time | 5:00 AM EST daily |
| Timezone | US Eastern |
| Duplicate Check | (title + agency + location) |
| Max Listings | 50 per pull |
| Error Handling | Graceful - continues on failures |

## Documentation

- **Full Technical Details:** See `INSTANTMARKETS_INTEGRATION.md`
- **Code Location:** app.py lines ~1450-1550
- **Scheduler Location:** app.py lines ~1620-1630
- **Admin Integration:** app.py lines ~8070-8085

---

**Deployed:** November 10, 2025  
**Status:** ✅ Production Ready  
**Last Updated:** November 10, 2025
