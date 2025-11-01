# Testing Guide - Client-Side Filtering & Mailbox

## Application Status
✅ **Running**: http://127.0.0.1:8080

## Test Scenarios

### 1. Test Client-Side Filtering (Customer Leads Portal)

#### Access the Portal
1. Open http://127.0.0.1:8080
2. Click "Sign In" (if not signed in)
3. Login with:
   - **Admin**: Username: `admin`, Password: `admin123`
   - **Test User**: Create a new account or use existing credentials
4. Navigate to "Customer Leads" from the menu

#### Test Lead Type Filter
1. Click "Lead Type" dropdown
2. Select "Government Contracts"
3. ✅ **Expected**: Only government leads show instantly (no page reload)
4. Select "Commercial Opportunities"
5. ✅ **Expected**: Only commercial leads show instantly
6. Select "Direct Requests"
7. ✅ **Expected**: Only commercial/residential requests show

#### Test Location Filter
1. Click "Location" dropdown
2. Select "Virginia Beach"
3. ✅ **Expected**: Only Virginia Beach leads show
4. Select "Norfolk"
5. ✅ **Expected**: Only Norfolk leads show
6. Try other cities: Hampton, Newport News, Suffolk, Williamsburg

#### Test Value Range Filter
1. Click "Value Range" dropdown
2. Select "$100K - $250K"
3. ✅ **Expected**: Only leads in that value range show
4. Try other ranges:
   - Under $50K
   - $50K - $100K
   - $250K - $500K
   - $500K - $1M
   - $1M - $3M
   - Over $3M

#### Test Category Filter (Quick Buttons)
1. Click "Universities" quick filter button
2. ✅ **Expected**: Only university-related leads show
3. Click "Schools"
4. ✅ **Expected**: Only school-related leads show
5. Click "Hospitals"
6. ✅ **Expected**: Only hospital-related leads show
7. Try: Hotels, Military, Norfolk, VB, Hampton buttons

#### Test Search Filter
1. In search box, type "cleaning"
2. ✅ **Expected**: Results filter as you type (instant)
3. Clear search, type "janitorial"
4. ✅ **Expected**: Janitorial-related leads show
5. Clear search, type "maintenance"
6. ✅ **Expected**: Maintenance-related leads show

#### Test Combined Filters
1. Select "Government Contracts" as lead type
2. Select "Virginia Beach" as location
3. Select "$100K - $250K" as value range
4. ✅ **Expected**: Only leads matching ALL criteria show
5. Results count should update: "Showing X of Y leads"

#### Test Clear All Filters
1. Apply multiple filters
2. Click "Clear All Filters" button
3. ✅ **Expected**: All filters reset, all leads show again

#### Test Sorting
1. Click "Sort By" dropdown
2. Select "Highest Value"
3. ✅ **Expected**: Leads re-order with highest value first
4. Select "Lowest Value"
5. ✅ **Expected**: Leads re-order with lowest value first
6. Select "By Location"
7. ✅ **Expected**: Leads sort alphabetically by location

#### Test Grid/List View Toggle
1. Click "Grid" button in top right
2. ✅ **Expected**: View changes to list layout (one per row)
3. Click again to toggle back
4. ✅ **Expected**: View changes to grid layout (multiple per row)

#### Verify Results Counter
1. Check top of page for badge: "X leads available"
2. Apply filters
3. ✅ **Expected**: Badge updates to show filtered count
4. Check bottom of page: "Showing X of Y leads"
5. ✅ **Expected**: Both counters match and update together

### 2. Test Mailbox Visibility

#### As Admin
1. Sign in with admin credentials
2. Look at top navigation bar
3. ✅ **Expected**: "Mailbox" link is visible with envelope icon
4. Click "Mailbox"
5. ✅ **Expected**: Mailbox page loads with Inbox/Sent/Admin tabs
6. Check for unread count badge
7. ✅ **Expected**: Badge shows unread message count (if any)

#### As Regular User
1. Sign out of admin account
2. Sign in with regular user account (or create new)
3. Look at top navigation bar
4. ✅ **Expected**: "Mailbox" link is visible
5. Click "Mailbox"
6. ✅ **Expected**: Mailbox page loads with Inbox/Sent tabs (no Admin tab)

#### Test Mailbox Folders
1. In Mailbox, click "Inbox" tab
2. ✅ **Expected**: Shows received messages
3. Click "Sent" tab
4. ✅ **Expected**: Shows sent messages
5. If admin, click "Admin" tab
6. ✅ **Expected**: Shows admin messages

### 3. Test User Profile Visibility

#### Check Profile Dropdown
1. After signing in, look at top right corner
2. ✅ **Expected**: User name or email is displayed
3. Click on username
4. ✅ **Expected**: Dropdown menu shows:
   - Profile link
   - Settings link
   - Credits balance
   - Subscription status
   - Sign out button

#### Check Admin Panel (Admin Only)
1. Sign in as admin
2. Look at navigation or profile dropdown
3. ✅ **Expected**: "Admin Panel" link is visible
4. Click "Admin Panel"
5. ✅ **Expected**: Admin dashboard loads with management tools

### 4. Performance Testing

#### Page Load Speed
1. Navigate to Customer Leads
2. Open browser dev tools (F12)
3. Check Network tab
4. ✅ **Expected**: Single page load with all data
5. Note the total data size
6. ✅ **Expected**: Under 1MB for ~500 leads

#### Filter Response Time
1. Apply a filter
2. ✅ **Expected**: Results update instantly (<100ms)
3. Change filter rapidly
4. ✅ **Expected**: No lag or delay
5. Type in search box
6. ✅ **Expected**: Results filter as you type (real-time)

#### Memory Usage
1. Open dev tools > Performance Monitor
2. Load Customer Leads page
3. ✅ **Expected**: Memory usage is reasonable
4. Apply filters multiple times
5. ✅ **Expected**: No memory leaks (memory stays stable)

### 5. Mobile Responsiveness

#### Test on Mobile View
1. Open dev tools (F12)
2. Toggle device toolbar (Ctrl+Shift+M or Cmd+Shift+M)
3. Select "iPhone 12 Pro" or similar
4. ✅ **Expected**: Filters collapse into mobile menu
5. ✅ **Expected**: Lead cards stack vertically
6. ✅ **Expected**: Mailbox link accessible in mobile nav

### 6. Browser Console Check

#### Verify No JavaScript Errors
1. Open browser console (F12 > Console tab)
2. Navigate to Customer Leads
3. ✅ **Expected**: No red error messages
4. Apply filters
5. ✅ **Expected**: No errors when filtering
6. Check warnings (yellow)
7. ✅ **Expected**: Only minor/expected warnings

#### Verify Data Loaded
1. In console, type: `leadsData.length`
2. ✅ **Expected**: Shows number like 200, 300, 500 (total leads)
3. Apply a filter
4. In console, type: `document.querySelectorAll('.lead-card:not([style*="display: none"])').length`
5. ✅ **Expected**: Shows filtered count matching badge

## Known Issues & Workarounds

### Issue: Mailbox Not Visible After Login
**Workaround**: 
1. Sign out completely
2. Clear browser cookies/cache
3. Sign back in
4. ✅ Should now see mailbox

### Issue: Filters Not Clearing
**Workaround**:
1. Refresh the page
2. ✅ All filters reset to default

### Issue: Leads Not Showing
**Possible Causes**:
- Database is empty (run scrapers to populate)
- Filter combination too restrictive (clear all filters)
- JavaScript error (check console)

**Solution**:
1. Check backend logs for database query results
2. Clear all filters
3. Refresh page

## Success Criteria

### ✅ All Tests Pass If:
1. **Filtering**: All filter types work instantly without page reload
2. **Mailbox**: Link visible after login for all user types
3. **Results Count**: Updates correctly with filters
4. **Sorting**: Re-orders leads as expected
5. **Search**: Filters results as you type
6. **Performance**: No lag or delay when applying filters
7. **Console**: No critical JavaScript errors
8. **Mobile**: Works on mobile viewport sizes
9. **Profile**: User info displays correctly
10. **Admin Panel**: Accessible for admin users

## Report Issues

If any tests fail, note:
1. **Test number** that failed
2. **Expected result** vs **actual result**
3. **Browser** and version
4. **Console errors** (if any)
5. **Network errors** (if any)

Example:
```
❌ Test 1.3 Failed
Expected: Only government leads show
Actual: All leads still visible
Browser: Chrome 120
Console Error: "Uncaught TypeError: Cannot read property 'value' of null"
```

## Next Steps After Testing

### If All Tests Pass ✅
1. Commit changes to git
2. Push to GitHub
3. Deploy to Render
4. Test on production URL
5. Announce feature to users

### If Tests Fail ❌
1. Document failures
2. Check browser console for errors
3. Review code changes
4. Fix issues
5. Re-test
6. Repeat until all pass

## Quick Commands

### Start Application
```bash
cd "/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE"
source .venv/bin/activate
python app.py
```

### Stop Application
Press `Ctrl+C` in terminal

### View Logs
- Terminal output shows Flask logs
- Browser console shows JavaScript errors

### Reset Database (if needed)
```bash
rm leads.db
python app.py  # Will recreate database
```

## Test Results Template

Copy and fill this out:

```
# Test Results - [Date]

## Environment
- Browser: [Chrome/Firefox/Safari] [Version]
- Device: [Desktop/Mobile]
- OS: [macOS/Windows/Linux]

## Test 1: Client-Side Filtering
- [ ] Lead type filter: PASS/FAIL
- [ ] Location filter: PASS/FAIL
- [ ] Value range filter: PASS/FAIL
- [ ] Category filter: PASS/FAIL
- [ ] Search filter: PASS/FAIL
- [ ] Combined filters: PASS/FAIL
- [ ] Clear all filters: PASS/FAIL
- [ ] Sorting: PASS/FAIL
- [ ] Grid/List toggle: PASS/FAIL
- [ ] Results counter: PASS/FAIL

## Test 2: Mailbox Visibility
- [ ] Admin mailbox: PASS/FAIL
- [ ] User mailbox: PASS/FAIL
- [ ] Inbox folder: PASS/FAIL
- [ ] Sent folder: PASS/FAIL
- [ ] Admin folder: PASS/FAIL
- [ ] Unread badge: PASS/FAIL

## Test 3: User Profile
- [ ] Profile dropdown: PASS/FAIL
- [ ] Admin panel: PASS/FAIL
- [ ] Credits display: PASS/FAIL
- [ ] Subscription badge: PASS/FAIL

## Test 4: Performance
- [ ] Page load speed: PASS/FAIL
- [ ] Filter response time: PASS/FAIL
- [ ] Memory usage: PASS/FAIL

## Test 5: Mobile
- [ ] Mobile responsive: PASS/FAIL
- [ ] Touch interactions: PASS/FAIL

## Test 6: Console
- [ ] No JS errors: PASS/FAIL
- [ ] Data loaded: PASS/FAIL

## Overall Status: PASS/FAIL

Notes:
[Any additional observations or issues]
```
