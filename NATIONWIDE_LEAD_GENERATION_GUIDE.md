# 🇺🇸 Nationwide Lead Generation Guide

## Overview
Automated Google API lead generation system covering all 50 US states + Washington DC.

## Coverage

### States: 51 (all 50 + DC)
### Cities: 153 total (3 per state average)
### Lead Types: 3 categories
- 🏢 Commercial properties (offices, hospitals, malls, schools, hotels, gyms, restaurants, warehouses, airports)
- 🏘️ Property management companies
- ✈️ Aviation facilities (airports, FBOs, hangars, airlines)

## Expected Results

### Total Leads: 3,000-5,000+
- Commercial properties: 2,000-3,000
- Property managers: 700-1,200
- Aviation facilities: 300-800

### Coverage by Region:
- **Northeast** (9 states): 600-900 leads
- **Southeast** (12 states): 800-1,200 leads
- **Midwest** (12 states): 700-1,000 leads
- **Southwest** (4 states): 400-600 leads
- **West** (13 states): 700-1,100 leads
- **Alaska/Hawaii** (2 states): 100-200 leads

## Usage

### Run on Render Shell:
```bash
python run_nationwide_lead_generation.py
```

### Runtime:
- **Estimated time**: 2-4 hours
- **Per state**: 5-10 minutes (3 cities each)
- **API calls**: ~1,500-2,000 total

### Requirements:
1. ✅ GOOGLE_API_KEY environment variable set
2. ✅ Places API enabled
3. ✅ Geocoding API enabled
4. ✅ Sufficient API quota (2,500 requests/day free tier)

## Progress Tracking

The script shows:
- State-by-state progress with percentages
- Per-city breakdown by category
- Running totals after each state
- Sample leads by category
- Final nationwide statistics

## Output Format

```
🇺🇸 NATIONWIDE GOOGLE API LEAD GENERATION
====================================================================
📍 Searching 51 states/territories
🏙️  Total cities: 153
====================================================================

====================================================================
📍 STATE: AL (3 cities)
====================================================================

🔍 [1/3] Birmingham, AL (radius: 12 miles)
   ✅ Commercial properties: 45
   ✅ Property managers: 8
   ✅ Aviation facilities: 3

✅ AL COMPLETE: 56 leads
📊 Progress: 1/51 states (2.0%)

... [continues for all states] ...

====================================================================
📊 NATIONWIDE TOTALS
====================================================================
🏢 Commercial properties: 2,456
🏘️  Property managers: 892
✈️  Aviation facilities: 437
📍 States covered: 51/51
🎯 TOTAL LEADS FOUND: 3,785
====================================================================
```

## Database Integration

### Table: `commercial_lead_requests`

Leads are automatically saved with:
- `business_name`: Company/facility name
- `city`, `state`: Location
- `phone`, `address`: Contact info
- `business_type`: Category (office, hospital, etc.)
- `special_requirements`: Google rating, website, place ID
- `status`: 'open' (ready for bidding)

## API Quota Management

### Free Tier Limits:
- **Places API**: 2,500 requests/day
- **Geocoding API**: 2,500 requests/day

### Full Run Usage:
- Places API: ~1,500 requests
- Geocoding API: ~160 requests

**Note**: One full run uses ~60% of daily quota. Can run 1-2x per day.

## Major Cities Included

### Top 20 Metros:
1. New York City, NY
2. Los Angeles, CA
3. Chicago, IL
4. Houston, TX
5. Phoenix, AZ
6. Philadelphia, PA
7. San Antonio, TX (via Austin)
8. San Diego, CA
9. Dallas, TX
10. San Francisco, CA
11. Seattle, WA
12. Boston, MA
13. Denver, CO
14. Washington, DC
15. Miami, FL
16. Atlanta, GA
17. Nashville, TN
18. Detroit, MI
19. Portland, OR
20. Las Vegas, NV

### Plus 133 additional cities across all states

## State Codes Reference

AL, AK, AZ, AR, CA, CO, CT, DE, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NY, NC, ND, OH, OK, OR, PA, RI, SC, SD, TN, TX, UT, VT, VA, WA, WV, WI, WY, DC

## Troubleshooting

### "API key not authorized"
→ Enable Places API and Geocoding API in Google Cloud Console

### "Quota exceeded"
→ Wait 24 hours or upgrade to paid tier ($5/1,000 requests)

### "No leads found"
→ Check internet connection, verify API key is correct

### Database errors
→ Ensure PostgreSQL is running, check connection string

## Next Steps

After generation completes:
1. View leads at `/commercial-cleaning-leads` route
2. Filter by state in admin dashboard
3. Export to CSV for sales team
4. Set up automated weekly/monthly runs
5. Add email notifications for new leads

## Comparison: Virginia Only vs Nationwide

| Metric | Virginia Only | Nationwide |
|--------|--------------|------------|
| States | 1 | 51 |
| Cities | 24 | 153 |
| Expected Leads | 700-1,000 | 3,000-5,000 |
| Runtime | 25-35 min | 2-4 hours |
| API Calls | ~250 | ~1,500 |
| Coverage | Hampton Roads, NoVA, Richmond | All major US metros |

## Cost Analysis (If Upgrading from Free Tier)

### Paid Pricing:
- $5 per 1,000 API requests
- Full nationwide run: ~$7.50
- Weekly runs (4x/month): ~$30/month
- Leads per dollar: 400-650 leads/$1

**ROI**: If 1% of leads convert at $500/month contract = $150-250/month revenue vs $30 cost
