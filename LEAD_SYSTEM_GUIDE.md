# Lead Generation System - User Guide

## Overview

Your Virginia Contracts application now includes a comprehensive lead generation system with:

1. **Commercial Lead Requests** - Businesses can request cleaning services
2. **Bidding System** - Paid subscribers can bid on commercial requests
3. **Residential Leads** - High-value homeowner data (integration ready)
4. **Lead Marketplace** - Dashboard for viewing and managing all leads

---

## For Businesses (Requesting Cleaning Services)

### How to Submit a Request

1. Visit `/request-cleaning` or click "Request Cleaning" in the navigation
2. Fill out the form with:
   - Business information
   - Contact details
   - Location
   - Service requirements (frequency, square footage, etc.)
   - Budget range and start date
3. Submit the form
4. Your request will be visible to verified cleaning contractors
5. Review competitive bids and choose the best contractor

**No cost to submit a request!**

---

## For Cleaning Contractors (Subscribers)

### Accessing the Lead Marketplace

1. **Sign in** to your account
2. Ensure you have an **active paid subscription**
3. Navigate to **Lead Marketplace** in the menu

### Viewing Leads

The marketplace has 3 tabs:

#### 1. Commercial Requests
- See all open cleaning requests from businesses
- Filter by location, business type, budget
- View detailed requirements
- Submit competitive bids

#### 2. Residential Leads
- High-value homeowner properties
- Sorted by estimated property value
- Includes address, square footage, beds/baths
- Links to source listings

#### 3. My Bids
- Track all your submitted bids
- See bid status (Pending/Accepted/Rejected)
- View your proposal details
- Monitor which leads you've bid on

### Submitting a Bid

1. Browse commercial requests
2. Click "Submit Bid" on any request
3. Fill out the bid form:
   - **Bid Amount** - Your monthly or one-time price
   - **Proposal** - Why you're the best fit
   - **Start Date** - When you can begin
   - **Contact Phone** - For direct communication
4. Submit and wait for the business to review

### Lead Tracking

- Each lead view is logged
- Bid counts are displayed
- Status updates show when businesses respond
- Requests marked "Complete" when a bid is accepted

---

## System Features

### Database Tables

1. **residential_leads** - Homeowner property data
   - Address, city, property details
   - Estimated value, beds/baths, sq ft
   - Source tracking (Zillow, Realtor.com)

2. **commercial_lead_requests** - Business cleaning requests
   - Business info and contact
   - Service requirements
   - Budget and timeline
   - Bid tracking

3. **bids** - Contractor proposals
   - Linked to requests
   - Bid amount and proposal
   - Status tracking
   - Timestamp logging

4. **lead_access_log** - Analytics
   - Track which leads users view
   - Measure engagement
   - Credit usage tracking

### Automated Features

- **Request Status Updates** - Automatically changes from "Open" → "Bidding" → "Completed"
- **Bid Counting** - Tracks number of bids per request
- **Timestamp Tracking** - All actions are logged
- **Email Notifications** - (Ready to implement)

---

## Residential Lead Scraper

### Current Implementation

The `residential_scraper.py` file generates **sample data** for demonstration.

### Running the Scraper

```bash
python residential_scraper.py
```

This will:
1. Generate 8-15 sample properties per city
2. Save to `residential_leads` table
3. Avoid duplicates
4. Display summary statistics

### Production Implementation

**⚠️ IMPORTANT:** Scraping Zillow/Realtor.com violates their Terms of Service.

**Legal Alternatives:**

1. **Zillow API** - Official partner program
   - Website: https://www.zillow.com/howto/api/APIOverview.htm
   - Requires partnership application

2. **Realtor.com Data Licensing**
   - Contact: data-licensing@move.com
   - Commercial data feeds available

3. **County Property Records** - 100% Legal
   - Virginia tax assessor databases
   - Public record, no restrictions
   - Example: Hampton City Assessor

4. **CoreLogic / Black Knight**
   - Professional real estate data
   - Licensed for commercial use
   - Industry standard

5. **Google Places API** - For business listings
   - $17 per 1,000 searches
   - Legal and compliant
   - Good for commercial leads

### Automating the Scraper

Add to your server's cron jobs:

```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/app && python residential_scraper.py
```

Or use the built-in scheduler in `app.py` (already configured for daily updates).

---

## Revenue Model

### For You (Platform Owner)

1. **Subscription Fees**
   - $50-$100/month for contractor access
   - Unlimited bid submissions
   - Access to all leads

2. **Pay-Per-Lead**
   - $5-$10 per commercial request reveal
   - $2-$5 per residential lead
   - Credit-based system already implemented

3. **Featured Bids**
   - Contractors pay extra to be featured
   - Highlighted in bid lists
   - Premium placement

### For Businesses (Requesting)

- **Free to submit** requests
- No cost until they choose a contractor
- Creates high-quality lead flow

### For Contractors (Subscribers)

- Monthly subscription for marketplace access
- Competitive bidding (best value wins)
- Direct client relationships

---

## Next Steps

### Immediate Tasks

1. ✅ Test the commercial request form
2. ✅ Submit a test bid as a subscriber
3. ⬜ Set up email notifications
4. ⬜ Integrate payment processing (Stripe)
5. ⬜ Add contractor verification system

### Data Integration

1. **County Records** (Week 1)
   - Virginia Beach Assessor API
   - Hampton tax records
   - Public, legal, free data

2. **Google Places** (Week 2)
   - Set up API key
   - Search for businesses
   - Filter by cleaning potential

3. **Licensed Data** (Month 1)
   - Evaluate CoreLogic pricing
   - Consider MLS data feeds
   - Partner with data aggregators

### Feature Enhancements

1. **Contractor Profiles**
   - Ratings and reviews
   - Portfolio photos
   - Certifications display

2. **Automated Matching**
   - AI-suggested contractors
   - Score bid quality
   - Predict win probability

3. **Communication System**
   - In-app messaging
   - Email threading
   - SMS notifications

4. **Analytics Dashboard**
   - Lead conversion rates
   - Average bid amounts
   - Revenue tracking

---

## Support & Maintenance

### Monitoring

- Check bid activity daily
- Review new commercial requests
- Monitor residential lead quality
- Track user engagement

### Database Maintenance

```sql
-- Clean old leads (older than 90 days)
DELETE FROM residential_leads WHERE created_at < NOW() - INTERVAL '90 days' AND status = 'old';

-- Archive completed requests
UPDATE commercial_lead_requests SET status = 'archived' 
WHERE status = 'completed' AND updated_at < NOW() - INTERVAL '60 days';
```

### Performance Tips

- Index frequently queried columns
- Archive old data quarterly
- Monitor database size
- Optimize slow queries

---

## Legal Compliance

### Fair Housing Act
- No discrimination in lead distribution
- Equal access to all contractors
- Transparent bidding process

### Data Privacy
- Secure storage of contact information
- GDPR/CCPA compliance if applicable
- User data deletion on request

### Terms of Service
- Clear contractor agreement
- Business request terms
- Data usage policies

---

## Questions?

**Technical Issues:** Check server logs in Render dashboard
**Feature Requests:** Update the GitHub issues
**Legal Questions:** Consult with attorney before scraping data

**Remember:** Use licensed data sources for production. The current implementation is for demonstration only!

🚀 Happy Lead Generating!
