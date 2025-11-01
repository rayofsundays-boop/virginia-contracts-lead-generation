# Database Migration Instructions

## Deployment Failed - Fix Applied ✅

### Problem
The deployment failed because the new routes (`/educational-contracts` and `/industry-days`) tried to query tables that don't exist yet in the production database.

### Solution Applied
1. ✅ Added table existence checks to both routes
2. ✅ Routes now gracefully handle missing tables with user-friendly messages
3. ✅ Created comprehensive migration script

### Now Safe to Deploy
The app will now deploy successfully and show "feature is being set up" messages until you run the migration.

---

## How to Run the Migration on Production

### Option 1: Using Render Dashboard (Recommended)
1. Log into your Render dashboard
2. Go to your PostgreSQL database
3. Click on "Connect" and choose "psql" command
4. Run each migration file in order:

**Step 1: Add Educational Contracts & Industry Days**
```sql
-- Copy and paste contents of: migrations/deploy_educational_and_industry_tables.sql
```
Verify: `SELECT COUNT(*) FROM educational_contracts;` (should return 13)
Verify: `SELECT COUNT(*) FROM industry_days;` (should return 12)

**Step 2: Populate Virginia Cleaning Contracts**
```sql
-- Copy and paste contents of: migrations/populate_virginia_contracts.sql
```
Verify: `SELECT COUNT(*) FROM contracts;` (should return 50+)
Verify: `SELECT COUNT(*), location FROM contracts GROUP BY location;` (shows contracts by city)

### Option 2: Using Render Shell
```bash
# Connect to your database using the External Database URL from Render
psql $DATABASE_URL

# Run the migration
\i /path/to/migrations/deploy_educational_and_industry_tables.sql

# Verify
SELECT COUNT(*) FROM educational_contracts;
SELECT COUNT(*) FROM industry_days;
```

### Option 3: Using pgAdmin or DBeaver
1. Connect to your Render PostgreSQL database
2. Open SQL Query window
3. Open `migrations/deploy_educational_and_industry_tables.sql`
4. Execute the script
5. Verify the data loaded correctly

---

## What This Migration Creates

### 1. educational_contracts Table
- **13 Virginia college/university contracts** including:
  - Hampton University ($850K janitorial + $125K floor care)
  - Christopher Newport University ($420K + $95K supplies)
  - Norfolk State University ($680K)
  - Old Dominion University ($520K + $85K windows)
  - William & Mary ($720K historic campus)
  - And 8 more institutions

### 2. industry_days Table
- **12 upcoming events** including:
  - Virginia Procurement Conference (Richmond)
  - Hampton Roads Small Business Expo
  - Military Installation Contractor Day
  - Educational Facilities Management Summit
  - Virtual webinars and workshops
  - City vendor showcases

---

## Features Added in This Deployment

### Educational Contracts Feature
- ✅ Route: `/educational-contracts`
- ✅ Filters: Institution, City, Category
- ✅ Contact info for paid subscribers only
- ✅ Paywall for non-subscribers
- ✅ Added to navigation menu
- ✅ Template: `templates/educational_contracts.html`

### Industry Days Feature
- ✅ Route: `/industry-days`
- ✅ Filters: City, Event Type
- ✅ Virtual and in-person events
- ✅ Registration links for subscribers
- ✅ Added to navigation menu
- ✅ Template: `templates/industry_days.html`

### Error Handling
- ✅ Quick Wins route no longer throws 500 errors
- ✅ Graceful fallbacks when tables don't exist
- ✅ User-friendly error messages

---

## Verification Steps After Migration

1. **Check Tables Exist**
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_name IN ('educational_contracts', 'industry_days');
   ```

2. **Verify Educational Contracts**
   ```sql
   SELECT COUNT(*), city FROM educational_contracts 
   GROUP BY city ORDER BY COUNT(*) DESC;
   ```

3. **Verify Industry Days**
   ```sql
   SELECT event_title, event_date FROM industry_days 
   ORDER BY event_date;
   ```

4. **Test Routes**
   - Visit: https://your-app.onrender.com/educational-contracts
   - Visit: https://your-app.onrender.com/industry-days
   - Both should load without errors

---

## Rollback (If Needed)

If you need to remove these tables:

```sql
DROP TABLE IF EXISTS educational_contracts;
DROP TABLE IF EXISTS industry_days;
```

---

## Git Commits

1. **9552d40** - Initial feature implementation (failed deployment)
2. **f989aa7** - Added table existence checks (deployment now safe)

---

## Next Features to Implement

After this migration is successful:

1. ☐ Complete remaining admin panel sections
2. ☐ Add post-registration survey redirect
3. ☐ Filter all leads to cleaning/janitorial only
4. ☐ Add email notifications for admin actions
5. ☐ Build admin user management interface
6. ☐ Create revenue and profit statement reports

---

## Need Help?

If migration fails or you see errors:
1. Check the PostgreSQL logs in Render dashboard
2. Verify database connection URL is correct
3. Ensure you have write permissions
4. Try running the script in smaller sections

Contact support or check the app logs for specific error messages.
