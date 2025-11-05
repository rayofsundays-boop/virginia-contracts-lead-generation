This is a Flask web application for government contracting lead generation, specifically focused on cleaning contracts in Virginia cities including Hampton, Suffolk, Virginia Beach, Newport News, and Williamsburg.

## Project Completed ✅

All setup steps have been completed:
- [x] Created copilot-instructions.md file
- [x] Clarified project requirements (Flask web app for VA government contracts)
- [x] Scaffolded the project with proper structure
- [x] Customized the project with HTML templates and VA contract data
- [x] Skipped extensions (none required for basic Flask)
- [x] Compiled the project (Python environment configured, dependencies installed)
- [x] Created VS Code task for running Flask application
- [x] Provided launch instructions
- [x] Created complete documentation
- [x] **Implemented fully automated URL population system** 🤖

## Latest Features (Nov 4, 2025) ✅ COMPLETE

### 📊 Database Cleanup & Data Transparency (Nov 4, 2025) - COMPLETE ✅
**Systematic cleanup to ensure 100% real, verified contract data:**

**Actions Completed:**
1. ✅ **Database Backup**: Created `leads_backup_20251104_195528.db`
2. ✅ **Removed Non-Cleaning Contracts**: Deleted 50 contracts with wrong NAICS codes
3. ✅ **Added Data Source Tracking**: New `data_source` column in federal_contracts table
4. ✅ **Fetched Real SAM.gov Contracts**: 3 cleaning contracts from SAM.gov API
5. ✅ **URL Verification**: All contracts have valid SAM.gov URLs
6. ✅ **Transparency Badges**: Data source labels displayed on all contracts

**Current Database Status:**
- **Total Contracts**: 3 real federal cleaning contracts
- **All Verified**: 100% from SAM.gov API
- **NAICS Codes**: 561720 (Janitorial Services)
- **All URLs Valid**: ✅ SAM.gov format with notice IDs
- **No Demo Data**: ✅ Zero fake/sample/test contracts

**Documentation Created:**
- `DATA_SOURCE_TRANSPARENCY.md` - Complete transparency guide
- `systematic_cleanup_and_fetch.py` - Automated cleanup script

### 🎬 Animated Dashboard Video (Nov 4, 2025) - LIVE ✅
**11-second cinematic dashboard preview embedded on homepage:**

**Features:**
- Brand intro → Dashboard → Stats → Contracts → CTA sequence
- Embedded via iframe at `/dashboard-video-preview`
- Auto-loops continuously when embedded
- Controls hidden in iframe for clean look
- Purple gradient matching brand (#667eea, #764ba2)
- Responsive 16:9 aspect ratio container

**Files:**
- `templates/dashboard_video_preview.html` - Video generator
- `templates/home_cinematic.html` - Embedded on homepage
- **Route**: `/dashboard-video-preview`

### 🤖 Automated URL Population System - LIVE & OPERATIONAL
**Three-tier automation for ensuring all leads have valid URLs:**

1. **Scheduled Daily Updates** - Runs at 3 AM EST ✅
   - Automatically finds leads without URLs
   - Uses OpenAI GPT-4 to generate appropriate URLs
   - Updates database automatically
   - Processes up to 20 leads per day
   - **Function:** `auto_populate_missing_urls_background()` (app.py line ~9750)

2. **Real-Time Population** - Triggers on lead import ✅
   - Generates URLs immediately for new leads
   - Works with Data.gov, SAM.gov, USAspending imports
   - Processes up to 10 leads per batch
   - **Function:** `populate_urls_for_new_leads()` (app.py line ~9890)

3. **Customer Notifications** - Automatic alerts ✅
   - Notifies customers when saved leads get new URLs
   - In-app messages system
   - Only for active subscribers
   - **Function:** `notify_customers_about_new_urls()` (app.py line ~10060)

**Admin Interfaces:**
- `/admin-enhanced?section=populate-urls` - Manual URL generation with preview
- `/admin-enhanced?section=url-automation` - Monitor automation activity
- `/admin-enhanced?section=track-all-urls` - Analyze URL quality

**Notice ID Verification:** ✅
- All SAM.gov leads include notice_id field (unique identifier)
- Database column: `federal_contracts.notice_id TEXT UNIQUE`
- Displayed in templates: federal_contracts.html, admin_all_contracts.html
- Properly extracted from SAM.gov API (`noticeId`) and Data.gov (`award_id`)

**Documentation:** See `AUTOMATED_URL_SYSTEM.md` for complete guide

**Commit:** `2dd5769` - All automated URL features deployed and tested

## Project Information
This is a Flask web application for government contracting lead generation, specifically focused on cleaning contracts in Virginia cities including Hampton, Suffolk, Virginia Beach, Newport News, and Williamsburg.