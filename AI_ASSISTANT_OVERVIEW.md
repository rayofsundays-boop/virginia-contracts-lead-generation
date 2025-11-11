# AI Assistant & Knowledge Base Overview

**Status:** Live (November 11, 2025)

This document explains the internal AI Assistant architecture: deterministic knowledge base (KB), role-aware scoring, API contract, extensibility, and testing.

## Summary
The assistant delivers fast, reliable answers for proposal support, pricing, navigation, compliance, and strategic guidance. It uses a curated in-repo KB (`chatbot_kb.py`) instead of external AI calls for low latency and predictability.

## Components
- `chatbot_kb.py`: Stores KBArticle objects (id, intent_tags, keywords, answer, followups) and matcher logic.
- `/api/ai-assistant-reply`: Flask endpoint returning structured JSON responses.
- `templates/ai_assistant.html`: UI with role selector, message stream, and KB source badge.

## API Contract
POST `/api/ai-assistant-reply`
Request JSON:
```
{ "message": "technical approach outline?", "role": "proposal manager" }
```
Response JSON:
```
{
  "success": true,
  "answer": "<p>...structured guidance...</p>
  ",
  "followups": "pricing strategy | compliance matrix | proposal templates",
  "source": "proposal_structure"
}
```
Errors:
- 400: Empty message
- 500: KB import failure or unexpected server error

## Scoring Logic
1. Exact intent tag containment (longer tags first for specificity)
2. Keyword frequency aggregation
3. Role bias (+2) if role substring appears in any article's intent tags
4. Fallback answer when no score produced

## Roles
| Role | Purpose | Example Query |
|------|---------|---------------|
| Research Assistant | Gap analysis, benchmarking | "research assistant: compare labor rates" |
| Economist | Cost sensitivity, market risk | "economist: impact of 20% wage increase" |
| Proposal Manager | Workflow, schedule, compliance | "proposal manager rush schedule" |
| IT Support | Troubleshooting, platform guidance | "it: upload failed pdf size?" |

Role strings are free-form but UI restricts to known options. Matching is substring-based on intent tags.

## Adding Articles
1. Open `chatbot_kb.py`.
2. Add a new `KBArticle(` block with:
   - `id`: unique string
   - `intent_tags`: list of phrases for direct matching
   - `keywords`: supplemental triggers
   - `answer`: HTML-capable string (avoid script tags)
   - `followups`: short related prompts
3. Keep answers concise but actionable (bullets, numbered steps, metrics).
4. Ensure new intent tags don't shadow existing specifics; prefer multi-word tags.

## Edge Cases & Safeguards
- Empty messages blocked at API layer.
- Logging is non-blocking; failures ignored.
- Long user messages: only length logged (no content) for privacy.
- Fallback answer guides user toward clarifying categories.

## Source Transparency
UI displays a "KB" badge for AI messages. Future enhancement: include article id tooltip or embed source id in DOM for analytics.

## Analytics
`logs/assistant.log` (rotating) format:
```
TIMESTAMP LEVEL reply role=<role> source=<article_id> len=<length>
```
Add external aggregation or admin view as needed.

## Testing
Create file `tests/test_chatbot_kb.py`:
- Specific role disambiguation
- Generic vs specific tag precedence
- Role bias scoring path
- Fallback scenario when nothing matches

Run tests:
```
python -m unittest -q
```

## Future Enhancements
- Return explicit `score` & `confidence` fields
- Persist interaction metadata in database for trend analysis
- Admin dashboard for top queries & unanswered intents
- Multi-language support (Spanish)
- Hybrid mode: deterministic first, optional external LLM expansion

## Troubleshooting
| Issue | Cause | Fix |
|-------|-------|-----|
| 500 response | Import failure / syntax error | Validate `chatbot_kb.py` syntax; run tests |
| Always fallback | Missing keywords or trimmed input | Add intent tags or improve keywords |
| Wrong article matched | Overlapping tag phrases | Introduce longer specific tag; re-order or rename |
| Log file missing | Directory not writable | Ensure `logs/` exists and permissions ok |

## Security Notes
- No user PII persisted (only role + source + length).
- Answers are internal guidance; user must verify against official RFP docs.
- Avoid embedding dynamic user input directly into HTML without escaping.

---

## Data.gov Integration

### Overview
The platform fetches federal cleaning contracts from Data.gov/USAspending.gov via automated daily jobs and manual admin triggers. NAICS code 561720 (Janitorial Services) is prioritized.

### Key Endpoints

**Manual Fetch (HTML)**
```
GET /admin/auto-fetch-datagov?days=<N>
```
Returns HTML page with stats, logs, and recent contracts.

**Programmatic Fetch (JSON)**
```
POST /api/admin/datagov-fetch
Content-Type: application/json

{ "days_back": 7 }
```
Response:
```json
{
  "success": true,
  "added": 12,
  "total_federal": 95,
  "datagov_total": 88,
  "recent": [
    {"title": "...", "agency": "...", "value": "...", "created_at": "..."}
  ]
}
```

**Status Check (JSON)**
```
GET /api/admin/datagov-status
```
Response:
```json
{
  "success": true,
  "total_federal": 95,
  "datagov_total": 88,
  "sam_total": 7,
  "last_fetch": "2025-11-11 14:32:15"
}
```

### Filtering Logic

**Priority Order (DataGovBulkFetcher)**
1. NAICS 561720 (Janitorial Services) – prepended for highest priority
2. Other cleaning NAICS (561730, 561790)
3. Strict cleaning keywords in description (janitor, cleaning, custodial, etc.)
4. Related services (landscaping/grounds)
5. General service sector (56xxxx) – limited to 20 contracts
6. VA contracts without NAICS – limited to 10 contracts

**Keyword Enforcement**
`cleaning_keywords` attribute includes: janitor, cleaning, custodial, housekeeping, sanitiz, disinfect, sweeping, mopping.

### Testing Data.gov Fetch

**Unit Tests** (`tests/test_datagov_fetch.py`):
- NAICS 561720 validation
- Cleaning keywords configuration
- Award parsing with complete vs minimal data
- Zero/missing value handling
- API error response handling
- Priority ordering (561720 appears first)

Run tests:
```bash
python -m unittest tests.test_datagov_fetch -v
```

### Automated Schedule
- **Daily at 3:00 AM EST**: `AutoFetcher.fetch_and_save()` pulls last 7 days
- **Off-peak hours**: Reduces API load, avoids rate limits

### Monitoring
- View fetch logs via `/admin/auto-fetch-datagov`
- Poll `/api/admin/datagov-status` for dashboard integration
- Check `logs/assistant.log` for any KB queries related to federal contracts

---

## Complete Test Suite

### Run All Tests
```bash
# AI Assistant KB tests
python -m unittest tests.test_chatbot_kb -q

# Data.gov fetch tests
python -m unittest tests.test_datagov_fetch -q

# All tests combined
python -m unittest -q
```

### VS Code Task
**Command Palette** → "Tasks: Run Task" → "Run Unit Tests"

---

Maintainers: Update this doc when adding new roles, altering scoring, introducing persistence, or modifying Data.gov filtering logic.
