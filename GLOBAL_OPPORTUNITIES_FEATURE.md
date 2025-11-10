# Global Opportunities Feature
## International Contracts for Cleaning Companies

### Overview
The Global Opportunities section provides ContractLink.ai users with access to international cleaning and facility management contracts from organizations worldwide.

### Feature Components

#### 1. Navigation Integration ✅
- **Location**: Main navigation menu under "Leads" dropdown
- **Position**: After "Supply Opportunities" section
- **Icon**: Globe Americas (fa-globe-americas)
- **Route**: `/global-opportunities`

#### 2. Backend Route ✅
**File**: `app.py` (lines ~15920-16000)

**Features**:
- Login required (`@login_required`)
- Subscriber status checking
- Region and country filtering
- Search functionality
- Integration with international data sources

**Query Parameters**:
- `region` - Filter by geographic region (Europe, Asia Pacific, Africa, etc.)
- `country` - Filter by specific country
- `search` - Text search across titles and descriptions

#### 3. Template ✅
**File**: `templates/global_opportunities.html`

**Sections**:
1. **Hero Header**
   - Purple gradient background
   - Statistics display (total contracts, regions, countries)
   - "Go Global" call-to-action

2. **Filters Section**
   - Region dropdown (all available regions)
   - Country dropdown (all available countries)
   - Search text input
   - Apply button

3. **Opportunities Grid**
   - 2-column responsive layout
   - Card design with hover effects
   - Badge system for country, region, contract value
   - Organization and deadline information
   - Contact details (subscriber-only)
   - Application URLs

4. **Subscriber Paywall**
   - Free users: See limited preview
   - Paid subscribers: Full contact details
   - Upgrade CTA for free users

5. **Information Section**
   - About international opportunities
   - Organization types covered
   - Partnership benefits

#### 4. Data Integration ✅
**File**: `integrations/international_sources.py`

**Data Sources**:
- UK Contracts Finder API
- Canada PSPC (Public Services and Procurement Canada)
- EU RSS feeds (configurable)
- Canada RSS feeds (configurable)
- Generic RSS adapters

**Function**: `fetch_international_cleaning(limit_per_source=50)`

**Data Structure**:
```python
{
    'title': str,           # Contract title
    'country': str,         # Country name
    'region': str,          # Geographic region
    'organization': str,    # Issuing organization
    'description': str,     # Contract description
    'value': str,           # Estimated contract value
    'deadline': str,        # Application deadline
    'contract_type': str,   # Type of contract
    'duration': str,        # Contract duration
    'contact_name': str,    # Contact person/department
    'contact_email': str,   # Email address
    'contact_phone': str,   # Phone number
    'application_url': str, # URL to apply
    'source': str,          # Data source name
    'urgent': bool          # Urgency flag
}
```

### Regions Covered
- **North America**: United States, Canada
- **Europe**: UK, France, Belgium, Switzerland, etc.
- **Asia Pacific**: Japan, Thailand, Philippines, etc.
- **Middle East**: UAE, Saudi Arabia, etc.
- **Africa**: Kenya, South Africa, etc.

### Contract Types
- UN Organizations (WHO, UNESCO, UNICEF)
- World Bank and Development Banks
- U.S. Embassies and Consulates
- NATO and International Alliances
- NGOs and Humanitarian Organizations
- Multinational Corporations

### User Experience Flow

#### Free Users
1. View all international opportunities
2. See basic contract information
3. Contact details are locked
4. "Upgrade to Access" button shown
5. Redirects to `/subscription` page

#### Paid Subscribers
1. Full access to all opportunities
2. Complete contact information visible
3. Direct "Apply Now" buttons
4. Can filter by region/country
5. Search across all contracts

### Admin Features
- No special admin interface yet (future enhancement)
- Admins have full access like paid subscribers
- Data sources can be configured via environment variables

### Environment Variables
**Optional RSS Feed Configuration**:
```bash
# Single RSS feed
INTERNATIONAL_RSS_URL=https://example.com/rss

# Multiple RSS feeds (comma-separated)
INTERNATIONAL_RSS_URLS=https://feed1.com/rss,https://feed2.com/rss
```

### Testing the Feature

#### Manual Testing
1. **Access the page**:
   ```
   http://localhost:5000/global-opportunities
   ```

2. **Test filters**:
   - Select region: Europe
   - Select country: United Kingdom
   - Enter search: "embassy"
   - Click Apply

3. **Test subscriber paywall**:
   - Log in as free user → Contact details locked
   - Log in as paid user → Contact details visible

#### Test as Admin
```python
# In Python shell
from app import app, db
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create test admin user
    from sqlalchemy import text
    db.session.execute(text("""
        INSERT INTO leads (email, password, subscription_status, is_admin)
        VALUES ('admin@test.com', :pwd, 'paid', 1)
    """), {'pwd': generate_password_hash('password123')})
    db.session.commit()
```

### Future Enhancements

#### Phase 2
- [ ] Add more data sources (UN Global Marketplace, USAID)
- [ ] Implement real-time API integrations
- [ ] Add contract value sorting
- [ ] Deadline countdown timers
- [ ] Email alerts for new opportunities

#### Phase 3
- [ ] Save favorite contracts
- [ ] Application tracking
- [ ] Contract history
- [ ] Success rate statistics
- [ ] Partnership recommendations

#### Phase 4
- [ ] Admin scraper dashboard
- [ ] Custom RSS feed manager
- [ ] Contract import/export
- [ ] Bulk application tools
- [ ] International vendor directory

### Troubleshooting

#### No Contracts Displayed
**Cause**: Data source API may be down or rate-limited

**Solution**:
1. Check integration logs
2. Verify API endpoints are accessible
3. Check environment variables
4. Test individual source functions

#### Filter Not Working
**Cause**: Data structure mismatch

**Solution**:
1. Verify all contracts have 'region' and 'country' fields
2. Check filter values match data exactly (case-sensitive)
3. Review JavaScript console for errors

#### Subscriber Check Failing
**Cause**: Session or database issue

**Solution**:
1. Verify user is logged in
2. Check subscription_status field in database
3. Clear browser cookies and re-login
4. Check is_admin flag

### Related Files
- `app.py` - Main route handler
- `templates/global_opportunities.html` - Frontend template
- `templates/base.html` - Navigation menu
- `integrations/international_sources.py` - Data fetching
- `database.py` - Database models (if extended)

### Deployment Notes
1. Ensure `integrations/` directory is included in deployment
2. Set environment variables for RSS feeds (optional)
3. Test API rate limits in production
4. Monitor error logs for failed data fetches
5. Consider caching international data (15-30 minutes)

### Marketing Points
- **Global Expansion**: Help cleaning companies expand internationally
- **Exclusive Access**: Contracts not easily found elsewhere
- **Direct Contacts**: Embassy, UN, World Bank contacts
- **High Value**: Multi-million dollar opportunities
- **Credible Sources**: Government and international organization contracts

### Success Metrics
- Page views per day
- Filter usage patterns
- Conversion rate (free → paid)
- Application link clicks
- User engagement time
- Regional interest distribution

---

**Status**: ✅ Fully Implemented
**Version**: 1.0
**Last Updated**: November 5, 2025
**Deployed**: Ready for production
