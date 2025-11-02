# URL Fix for Broken Application Links

## Issue
Some leads show broken "Apply Now" links that lead to 404 pages, such as:
- `https://www.hampton.gov/bids/bids.aspx?bidID=1217` (broken)

## Root Cause
Old or dynamically generated URLs in the database that are no longer valid on the agency websites.

## Solution Implemented

### 1. Added Better URL Handling in Template
File: `templates/customer_leads.html`

Added helper text to inform users that the link goes to the agency's procurement page where they can find current bids.

### 2. URL Validation Strategy

For broken links, the system now:
1. Shows a warning message that the specific bid URL may be outdated
2. Provides the agency's main procurement page as fallback
3. Includes contact information for the procurement office

## Recommended Actions for Users

If you encounter a broken "Apply Now" link:

1. **Use the Agency's Main Procurement Page**
   - Hampton: https://www.hampton.gov/bids.aspx
   - Norfolk: https://www.norfolk.gov/procurement
   - Virginia Beach: https://www.vbgov.com/government/departments/purchasing
   - Richmond: https://www.rva.gov/procurement

2. **Search for the RFP Number**
   - Look for "RFP 26-17/AB" or similar on the procurement page
   - Use the site search function
   - Check "Current Opportunities" or "Open Bids" sections

3. **Contact Procurement Directly**
   - Hampton: (757) 727-6392
   - Reference the RFP number when calling

4. **Check SAM.gov for Federal Contracts**
   - https://sam.gov/content/opportunities
   - Search by agency name or contract number

## Future Improvements

To prevent broken links:
1. Implement URL validation before storing in database
2. Add periodic link checker to test stored URLs
3. Automatically update links from agency RSS feeds
4. Cache fallback URLs for each agency

## Quick Fix Script

If you need to update all Hampton URLs in the database:

```python
from app import app, db
from sqlalchemy import text

with app.app_context():
    # Update any broken bidID-specific URLs to general procurement page
    db.session.execute(text('''
        UPDATE contracts 
        SET website_url = 'https://www.hampton.gov/bids.aspx'
        WHERE website_url LIKE '%hampton.gov%bidID%'
    '''))
    db.session.commit()
    print("✅ Updated broken Hampton URLs")
```

## Contact for Issues

If a link is broken:
1. Save the lead to your repository
2. Note the RFP/contract number
3. Visit the agency's main procurement page
4. Report broken link via "Report Issue" button (if available)
