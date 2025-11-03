# Data.gov Federal Contracts Integration

This project now integrates with **USAspending.gov** (part of Data.gov) to fetch real federal contract data.

## What is Data.gov?

Data.gov is the U.S. government's open data portal providing access to thousands of federal datasets. For federal contracting, the primary sources are:

1. **USAspending.gov API** - Tracks all federal spending including contracts, grants, and loans
2. **FPDS (Federal Procurement Data System)** - Detailed procurement data
3. **SAM.gov** - Active contract opportunities (already integrated)

## Integration Overview

### Files Created

- **`datagov_bulk_fetcher.py`** - Main fetcher class for USAspending.gov API
- **`update_from_datagov.py`** - Standalone script to fetch and populate contracts
- **`app.py`** (modified) - Added daily scheduler for automatic updates

### How It Works

1. **USAspending.gov API Integration**
   - Searches for contracts awarded in Virginia
   - Filters by NAICS codes (cleaning, janitorial, landscaping services)
   - Searches last 90 days of contract awards
   - Returns up to 100 contracts per request

2. **Automated Scheduling**
   - Runs daily at 1:00 AM (less frequent than SAM.gov due to bulk data size)
   - Initial fetch on application startup (15-second delay)
   - Background daemon thread for non-blocking execution

3. **Database Storage**
   - Stores in `federal_contracts` table
   - Deduplicates using `notice_id` (unique award ID)
   - Updates existing contracts if they change

### Data Sources

#### USAspending.gov
- **URL**: https://api.usaspending.gov
- **Coverage**: All federal contract awards (post-award data)
- **Update Frequency**: Daily
- **Rate Limit**: 100 results per request
- **Data Includes**: 
  - Award amounts
  - Awarding agency
  - Performance location
  - NAICS codes
  - Contract descriptions
  - Award recipients

#### SAM.gov (Existing)
- **Coverage**: Active opportunities (pre-award data)
- **Update Frequency**: Every 15 minutes
- **API Key Required**: Yes (already configured)

## Usage

### Manual Update

Run the standalone script to fetch contracts immediately:

```bash
python3 update_from_datagov.py
```

### Automatic Updates

The Flask app automatically runs Data.gov updates:
- **Every 15 minutes**: SAM.gov opportunities (real-time)
- **Daily at 1 AM**: USAspending.gov awards (bulk data)
- **Daily at 3 AM**: Local government contracts (web scraping)

### Environment Variables

No additional configuration needed! The integration works out of the box.

Optional:
```bash
FETCH_ON_INIT=1  # Fetch on startup (default: enabled)
```

## API Details

### USAspending.gov Endpoints

**Award Search API**:
```
POST https://api.usaspending.gov/api/v2/search/spending_by_award/
```

**Filters Used**:
- Award Types: A, B, C, D (contracts)
- Location: Virginia (VA)
- NAICS: 561720, 561730, 561790 (cleaning/landscaping)
- Time Period: Last 90 days
- Limit: 100 contracts

### Data Mapping

USAspending.gov → Database:
- `Award ID` → `notice_id`
- `Awarding Agency` → `agency`
- `Award Amount` → `value`
- `Description` → `title` and `description`
- `Place of Performance City/State` → `location`
- `Period of Performance End Date` → `deadline`
- `NAICS Code` → `naics_code`

## Troubleshooting

### No Contracts Found

**Possible Reasons**:
1. No new cleaning contracts awarded in VA in last 90 days
2. Contracts use different NAICS codes
3. API rate limiting or downtime

**Solutions**:
- Check logs: `grep "Data.gov" flask.log`
- Test manually: `python3 update_from_datagov.py`
- Verify API is responsive: https://api.usaspending.gov/api/

### Parser Errors

If you see "Error parsing award" messages:
- The USAspending.gov API response structure may have changed
- Check test script: `python3 test_usaspending_api.py`
- Review API documentation: https://api.usaspending.gov/docs/

## Future Enhancements

1. **Pagination** - Fetch more than 100 contracts per request
2. **Historical Data** - Import older contracts (365+ days)
3. **FPDS Integration** - Add Federal Procurement Data System feed
4. **Data.gov Catalog** - Search for additional relevant datasets
5. **Advanced Filtering** - Filter by contract value, set-aside type, etc.

## Resources

- [USAspending.gov API Docs](https://api.usaspending.gov/docs/)
- [Data.gov Catalog](https://catalog.data.gov/)
- [FPDS ATOM Feeds](https://www.fpds.gov/wiki/index.php/ATOM_Feed_Usage)
- [SAM.gov API](https://open.gsa.gov/api/entity-api/)

## Benefits

✅ **More Complete Data** - Combines active opportunities (SAM.gov) with awarded contracts (USAspending.gov)

✅ **Historical Context** - See what contracts were actually awarded

✅ **No API Key Required** - USAspending.gov is fully open

✅ **Government-Verified** - Official federal spending data

✅ **Automatic Updates** - Runs daily without intervention

---

**Note**: This integration is complementary to SAM.gov. Use SAM.gov for active bidding opportunities and USAspending.gov for market research and historical analysis.
