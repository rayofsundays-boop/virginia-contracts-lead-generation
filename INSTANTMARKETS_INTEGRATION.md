# Instantmarkets.com Daily Lead Pull Integration

**Date Implemented:** November 10, 2025  
**Commit:** c80655a  
**Status:** ✅ Active

## Overview

Automated daily lead pull system that fetches cleaning and janitorial service opportunities from instantmarkets.com and populates the `supply_contracts` database table with real business opportunities.

## Features

### 1. **Automated Daily Schedule**
- **Trigger Time:** 5:00 AM EST (off-peak hours)
- **Frequency:** Once per day
- **Database:** PostgreSQL `supply_contracts` table
- **Duplicate Prevention:** Checks for existing leads by (title + agency + location)

### 2. **Manual Trigger**
- **Admin-Only Endpoint:** `/api/trigger-instantmarkets-pull`
- **Method:** POST
- **Authentication:** Admin session required
- **Response:** JSON with count of leads added

### 3. **Data Extraction**
The system extracts and stores:
- **Title:** Project/opportunity name
- **Agency:** Company or organization posting the opportunity
- **Location:** Project location (Virginia-focused)
- **Description:** Project details and requirements
- **Estimated Value:** Budget or pricing information
- **Posted Date:** When opportunity was posted
- **Website URL:** Direct link to opportunity
- **Category:** Set to "Cleaning Services"
- **Status:** Marked as "open"

## Technical Implementation

### Function: `fetch_instantmarkets_leads()`
**Location:** app.py (lines ~1450-1550)

**Key Features:**
```python
def fetch_instantmarkets_leads():
    # 1. Sends GET request to instantmarkets.com
    # 2. Parses HTML with BeautifulSoup
    # 3. Extracts opportunity data from DOM
    # 4. Validates and normalizes lead information
    # 5. Checks for duplicates in database
    # 6. Inserts new leads into supply_contracts
    # 7. Returns count of leads added
```

**Processing Flow:**
1. Requests instantmarkets.com search results for cleaning + janitorial services in Virginia
2. Parses HTML response with BeautifulSoup
3. Extracts up to 50 listings per pull (prevents overload)
4. For each listing:
   - Extracts title, agency, location, description, value, URL
   - Formats data to match supply_contracts schema
   - Checks for existing duplicate (by title + agency + location)
   - Inserts if new, skips if duplicate
5. Commits transaction and returns success count

### Scheduler: `schedule_instantmarkets_updates()`
**Location:** app.py (lines ~1620-1630)

Runs in background thread during application startup:
```python
schedule.every().day.at("05:00").do(fetch_instantmarkets_leads)
```

### Admin API Endpoint
**Route:** `/api/trigger-instantmarkets-pull`  
**Method:** POST  
**Auth:** `@admin_required` decorator

**Response Example:**
```json
{
  "success": true,
  "message": "Successfully pulled 12 new leads from instantmarkets.com",
  "leads_added": 12
}
```

## Integration Points

### 1. **Application Startup** (app.py ~line 1670)
```python
# Start Instantmarkets.com scheduler in background thread (runs at 5 AM daily)
instantmarkets_scheduler_thread = threading.Thread(target=schedule_instantmarkets_updates, daemon=True)
instantmarkets_scheduler_thread.start()
print("✅ Instantmarkets.com daily lead pull enabled - will run at 5 AM EST")
```

### 2. **Background Jobs Lock**
- Uses existing single-instance lock mechanism (`_BACKGROUND_LOCK_PATH`)
- Prevents duplicate scheduler threads under Gunicorn multi-worker deployment

### 3. **Database Operations**
- Uses SQLAlchemy ORM with raw SQL text queries
- PostgreSQL CURRENT_TIMESTAMP for `created_at`
- Proper transaction handling with `db.session.commit()`

## Data Schema

### Inserted Fields (supply_contracts table)
```sql
INSERT INTO supply_contracts 
(title, agency, location, product_category, estimated_value, 
 description, website_url, posted_date, status, created_at)
VALUES (...)
```

**Field Mappings:**
| Instantmarkets | Database Column | Example |
|---|---|---|
| Project Title | `title` | "Office Space Cleaning" |
| Company Name | `agency` | "ABC Corporation" |
| Project Location | `location` | "Richmond, VA" |
| Service Type | `product_category` | "Cleaning Services" |
| Budget/Price | `estimated_value` | "$500-1000" |
| Details | `description` | "Weekly office cleaning required..." |
| Listing URL | `website_url` | "https://instantmarkets.com/opportunity/..." |
| Listed Date | `posted_date` | "2025-11-10" |
| Availability | `status` | "open" |
| Import Time | `created_at` | CURRENT_TIMESTAMP |

## Duplicate Prevention

**Uniqueness Check:**
```sql
SELECT COUNT(*) FROM supply_contracts 
WHERE title = :title AND agency = :agency AND location = :location
```

- Prevents duplicate opportunities from appearing multiple times
- Checks all three fields to ensure accurate duplicate detection
- Allows same agency to post similar projects in different locations

## Error Handling

### Network Errors
- Catches `requests.exceptions.RequestException`
- Logs error and returns 0 leads
- Continues normally at next scheduled time

### Parsing Errors
- Try/except for each listing extraction
- Individual failed listings don't stop entire pull
- Logs parse errors and continues with next item

### Database Errors
- Transaction rollback on insert failure
- Individual failed inserts don't stop batch
- Logs error with lead title for debugging

## Scheduling Details

### Off-Peak Hours Strategy
- **Runs at 5 AM EST** to avoid peak traffic hours
- **Sequence:**
  - 2 AM: Data.gov bulk updates
  - 3 AM: Auto URL population
  - 4 AM: USAspending.gov + Local government contracts
  - 5 AM: **Instantmarkets.com leads** ← New
  
### Thread Safety
- Daemon thread = stops when app stops
- Uses `schedule` library for timing
- Sleeps 3600 seconds (1 hour) between checks
- Single-instance lock prevents duplicates

## Usage

### Automatic (Daily at 5 AM EST)
System automatically pulls leads every morning. No action required.

### Manual (Admin Trigger)
**For Quick Testing:**
1. Log in as admin
2. Open browser console or use curl:
```bash
curl -X POST http://localhost:5000/api/trigger-instantmarkets-pull \
  -H "Content-Type: application/json" \
  -b "session_cookie_value"
```

**From Admin Panel:**
- Add button to `/admin-enhanced` template to trigger endpoint
- Display success/error messages
- Show count of leads added

## Monitoring

### Log Output
Watch for these messages in application logs:

**Successful Pull:**
```
🌐 Fetching leads from instantmarkets.com...
📊 Found 45 listings on instantmarkets.com
✅ Instantmarkets.com update complete: 12 new leads added, 33 duplicates skipped
```

**Error During Pull:**
```
❌ Network error fetching from instantmarkets.com: [error details]
❌ Error parsing listing: [parse error]
❌ Error inserting lead 'Office Cleaning': [db error]
```

**Scheduler Started:**
```
⏰ Instantmarkets.com scheduler started - will fetch supply leads daily at 5 AM EST (off-peak)
```

## Troubleshooting

### No Leads Being Added
1. **Check if scheduler is running:** Look for startup log message
2. **Verify site still exists:** Visit instantmarkets.com in browser
3. **Check DOM structure:** Site HTML/CSS may have changed
4. **Test manually:** Trigger `/api/trigger-instantmarkets-pull` and check logs

### Duplicate Leads Appearing
1. Check if uniqueness columns (title, agency, location) are matching properly
2. Update duplicate detection logic if site data format changed
3. Consider cleaning old duplicates from database

### Network Timeouts
1. Increase timeout from 15 seconds if needed (line in function)
2. Check internet connectivity
3. Verify instantmarkets.com is accessible from deployment server

### Parser Not Finding Data
1. HTML selectors may have changed (class names, element types)
2. Update CSS selectors in `listings = soup.find_all(...)` calls
3. Use browser DevTools to inspect current HTML structure
4. Test parsing with sample HTML

## Future Enhancements

### 1. **Enhanced Data Extraction**
- Extract contact information (email, phone)
- Parse project timelines and deadlines
- Identify service categories automatically (janitorial, office, retail, etc.)

### 2. **AI-Powered Relevance Scoring**
- Use GPT-4 to score lead relevance to user profiles
- Auto-tag high-probability leads
- Predict conversion likelihood

### 3. **Multiple Site Integration**
- Add TaskRabbit business opportunities
- Integrate Upwork projects
- Connect Thumbtack leads
- Expand to regional B2B marketplaces

### 4. **Real-Time Updates**
- Switch from daily to hourly pulls
- Implement webhook listeners if instantmarkets provides them
- Push notifications for hot leads

### 5. **Lead Quality Metrics**
- Track conversion rates by source
- Calculate average deal value
- Monitor completion rates
- Display analytics in admin dashboard

## Related Documentation

- **Scheduling System:** See `DATA FETCHING SCHEDULE` (app.py lines ~55-60)
- **Database Schema:** `supply_contracts` table definition (app.py lines ~2413)
- **Admin Functions:** `/admin-enhanced` route (app.py lines ~9101)
- **Background Jobs:** `_start_background_jobs()` (app.py lines ~1640)

## Deployment Notes

### Requirements
- `requests` library (already installed)
- `beautifulsoup4` library (already installed)
- PostgreSQL database with `supply_contracts` table
- Working network connection to instantmarkets.com

### Environment Variables
- **No new env vars required**
- Uses existing `OPENAI_API_KEY` for optional future enhancements
- All configuration hardcoded in function (can be parameterized later)

### Production Considerations
- ✅ Single-instance lock prevents duplicate threads
- ✅ Daemon thread doesn't block app shutdown
- ✅ Error handling prevents crashes
- ✅ Off-peak scheduling reduces load
- ⚠️ May need rate limiting if instantmarkets.com blocks rapid requests
- ⚠️ HTML parsing breaks if site structure changes significantly

## Commit History

| Commit | Changes |
|--------|---------|
| c80655a | Initial implementation - Add daily instantmarkets.com lead pull system |

---

**Last Updated:** November 10, 2025  
**Maintainer:** Development Team  
**Status:** Production Ready ✅
