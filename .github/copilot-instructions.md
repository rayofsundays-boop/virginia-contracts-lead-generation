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

## Latest Features (Nov 4, 2025)

### 🤖 Automated URL Population System
**Three-tier automation for ensuring all leads have valid URLs:**

1. **Scheduled Daily Updates** - Runs at 3 AM EST
   - Automatically finds leads without URLs
   - Uses OpenAI GPT-4 to generate appropriate URLs
   - Updates database automatically
   - Processes up to 20 leads per day

2. **Real-Time Population** - Triggers on lead import
   - Generates URLs immediately for new leads
   - Works with Data.gov, SAM.gov, USAspending imports
   - Processes up to 10 leads per batch

3. **Customer Notifications** - Automatic alerts
   - Notifies customers when saved leads get new URLs
   - In-app messages system
   - Only for active subscribers

**Admin Interfaces:**
- `/admin-enhanced?section=populate-urls` - Manual URL generation with preview
- `/admin-enhanced?section=url-automation` - Monitor automation activity
- `/admin-enhanced?section=track-all-urls` - Analyze URL quality

**Documentation:** See `AUTOMATED_URL_SYSTEM.md` for complete guide

## Project Information
This is a Flask web application for government contracting lead generation, specifically focused on cleaning contracts in Virginia cities including Hampton, Suffolk, Virginia Beach, Newport News, and Williamsburg.