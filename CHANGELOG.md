# Changelog

All notable changes to this project will be documented in this file.

## 2025-11-11

### AI Assistant Enhancements
- Added role-aware KB endpoint `/api/ai-assistant-reply` wiring to UI with role selector.
- KB Matching: Prioritize longer, more specific intent tags over generic ones to avoid overshadowing (e.g., "proposal manager" over "proposal").
- Analytics: Introduced optional rotating file logger at `logs/assistant.log` (role, source, length only; no PII).
- Docs: Extended `AI_ASSISTANT_OVERVIEW.md` with complete API contract, testing guide, and Data.gov integration details.
- Updated `README.md` with assistant usage and unit test instructions.
- UI: AI Assistant now displays a subtle "KB" source badge on assistant messages.

### Data.gov Integration Enhancements
- **New Endpoints:**
  - `POST /api/admin/datagov-fetch` – JSON API for programmatic contract fetch with `days_back` parameter
  - `GET /api/admin/datagov-status` – Real-time DB stats (total_federal, datagov_total, sam_total, last_fetch)
- **NAICS 561720 Prioritization:** Updated `DataGovBulkFetcher` to prepend NAICS 561720 (Janitorial Services) contracts for highest priority.
- **Strict Cleaning Keywords:** Added `cleaning_keywords` attribute (janitor, cleaning, custodial, housekeeping, sanitiz, disinfect, sweeping, mopping).
- **Enhanced Filtering:** 6-tier priority system ensures cleaning contracts appear first, limits general service/fallback contracts.
- **Unit Tests:** Created `tests/test_datagov_fetch.py` with 8 test cases validating parsing, prioritization, error handling.
- **Logging Improvements:** Detailed contract breakdown logging (cleaning vs related services vs general).

## 2025-11-10
- Enhanced chatbot quick start guide for the legacy client-only chatbot (`CHATBOT_QUICK_START.md`).

