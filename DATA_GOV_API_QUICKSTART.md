# Data.gov Integration – Quick Reference

**Status:** ✅ LIVE (Nov 11, 2025) | **Commit:** 945bbb4

---

## New JSON API Endpoints

### 1. Fetch Contracts (POST)
```bash
curl -X POST http://localhost:5000/api/admin/datagov-fetch \
  -H "Content-Type: application/json" \
  -d '{"days_back": 14}' \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "success": true,
  "added": 12,
  "total_federal": 95,
  "datagov_total": 88,
  "recent": [
    {"title": "Janitorial Services...", "agency": "GSA", "value": "$125,000", "created_at": "2025-11-11 14:32:15"}
  ]
}
```

### 2. Status Check (GET)
```bash
curl http://localhost:5000/api/admin/datagov-status \
  --cookie "session=YOUR_SESSION_COOKIE"
```

**Response:**
```json
{
  "success": true,
  "total_federal": 95,
  "datagov_total": 88,
  "sam_total": 7,
  "last_fetch": "2025-11-11 14:32:15"
}
```

---

## NAICS 561720 Prioritization

### 6-Tier Filtering System

1. **NAICS 561720** (Janitorial Services) → Prepended (highest priority)
2. **Other cleaning NAICS** (561730, 561790) → Appended to cleaning list
3. **Strict cleaning keywords** → Description/title match (janitor, custodial, sanitiz, etc.)
4. **Related services** → Landscaping/grounds (limited to 20 contracts)
5. **General service sector** → 56xxxx NAICS (limited to 20 contracts)
6. **VA contracts without NAICS** → Fallback (limited to 10 contracts)

### Cleaning Keywords
- janitor
- cleaning
- custodial
- housekeeping
- sanitiz
- disinfect
- sweeping
- mopping

---

## Testing

### Run All Tests
```bash
cd "/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE"
./.venv/bin/python -m unittest discover -s tests -p "test_*.py" -v
```

### VS Code Task
**Command Palette** → "Tasks: Run Task" → "Run Unit Tests"

### Test Coverage
- **AI Assistant KB:** 6 tests (specificity, role bias, fallback)
- **Data.gov Fetch:** 8 tests (NAICS validation, parsing, prioritization, error handling)
- **Total:** 14 tests, all passing ✅

---

## Manual Admin Triggers

### HTML Interface
```
http://localhost:5000/admin/auto-fetch-datagov?days=30
```
Returns HTML page with stats, logs, recent contracts.

### Automated Schedule
- **Daily at 3:00 AM EST**
- Fetches last 7 days
- Off-peak hours to reduce API load

---

## Monitoring

### Check Logs
```bash
tail -f logs/assistant.log
```

### Database Stats
```bash
./.venv/bin/python -c "
from app import app, db
from sqlalchemy import text
with app.app_context():
    total = db.session.execute(text('SELECT COUNT(*) FROM federal_contracts')).scalar()
    datagov = db.session.execute(text(\"SELECT COUNT(*) FROM federal_contracts WHERE data_source LIKE '%Data.gov%'\")).scalar()
    print(f'Total: {total}, Data.gov: {datagov}')
"
```

---

## Quick Troubleshooting

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| `added: 0` | No new contracts in date range | Increase `days_back` parameter |
| API 500 error | AutoFetcher import failure | Check `auto_fetch_daily.py` exists |
| All contracts generic | NAICS filtering too strict | Verify `cleaning_keywords` in `datagov_bulk_fetcher.py` |
| Tests failing | Module import path issue | Run from project root with venv active |

---

## File Locations

- **Fetcher:** `datagov_bulk_fetcher.py`
- **API Endpoints:** `app.py` (lines ~16038+)
- **Tests:** `tests/test_datagov_fetch.py`
- **Docs:** `AI_ASSISTANT_OVERVIEW.md` (Data.gov section)
- **Logs:** `logs/assistant.log`

---

## Next Steps

1. **Monitor first automated fetch** (3 AM EST tomorrow)
2. **Poll `/api/admin/datagov-status`** for dashboard integration
3. **Review prioritization** after 7 days (check NAICS 561720 percentage)
4. **Add admin analytics view** (optional) for top sources/agencies

---

**Documentation:** See `AI_ASSISTANT_OVERVIEW.md` for comprehensive guide  
**Support:** Check inline code comments in `datagov_bulk_fetcher.py`

