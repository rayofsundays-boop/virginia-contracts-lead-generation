# Procurement Scraper System

Automated system for scraping and managing Virginia procurement opportunities from federal (SAM.gov) and local government sources.

## Components

### 1. SAM.gov Federal Contracts (`sam_gov_fetcher.py`)
- Fetches federal cleaning contracts from SAM.gov API
- NAICS Codes: 561720 (Janitorial), 561730 (Landscaping), 561790 (Other Building Services)
- Filters for Virginia locations only
- Respects API rate limits

### 2. Local Government Scraper (`local_gov_scraper.py`)
- Scrapes 10 Virginia city/county procurement websites
- Cities: Hampton, Norfolk, Virginia Beach, Newport News, Chesapeake, Portsmouth, Suffolk, Williamsburg, James City County, York County
- Keyword-based filtering for cleaning-related contracts

### 3. Automated Scheduler (`scraper_scheduler.py`)
- Runs scrapers on automated schedule
- Federal: Daily at 2:00 AM + every 6 hours
- Local: Daily at 3:00 AM + every 6 hours
- Prevents duplicate entries
- Handles errors gracefully

## Setup

### 1. SAM.gov API Key (Required for Federal Contracts)
```bash
# Get free API key from https://open.gsa.gov/api/sam-gov-entity-api/
export SAM_GOV_API_KEY='your-api-key-here'
```

### 2. Install Dependencies
```bash
pip install requests beautifulsoup4 schedule sqlalchemy
```

### 3. Run Manual Scrape
```bash
# Test federal scraper
python sam_gov_fetcher.py

# Test local scraper
python local_gov_scraper.py

# Test both
python test_scrapers.py
```

### 4. Run Automated Scheduler
```bash
# Start background scheduler (runs continuously)
python scraper_scheduler.py
```

### 5. Manual Trigger via Admin Panel
- Login as admin
- Navigate to admin panel
- Click "Scrape Procurement Data" button
- View results in real-time

## Database Tables

### `contracts` (Local/State Government)
- title, agency, location, description
- value, deadline, naics_code
- category (Municipal, School District, etc.)
- website_url, created_at

### `federal_contracts` (Federal Opportunities)
- title, agency, location, description
- value, deadline, naics_code
- notice_id, sam_gov_url, posted_date

### `commercial_opportunities` (Private Sector)
- business_name, business_type, location
- description, monthly_value, services_needed
- website_url

## City-Specific Pages

Access procurement by city:
- `/city/hampton`
- `/city/norfolk`
- `/city/virginia-beach`
- `/city/newport-news`
- `/city/williamsburg`
- `/city/suffolk`
- `/city/chesapeake`
- `/city/portsmouth`

## Quick Wins Feature

**Subscriber Exclusive**: Access to urgent procurement opportunities
- Emergency: Response needed within 24 hours
- Urgent: Response needed within 48 hours
- 75% higher win rate due to less competition
- Advertised throughout platform

## Search & Filtering

All procurement opportunities are searchable by:
- City/Location
- Category (Universities, Schools, Municipal, etc.)
- Lead Type (Government, Commercial, Federal)
- Value Range ($50K - $3M+)
- Services Needed
- Full-text search

## Deployment

### On Render (Production)

1. **Environment Variables**
   ```
   SAM_GOV_API_KEY=your-key
   DATABASE_URL=postgresql://...
   ```

2. **Background Worker** (Optional)
   - Add separate service for `scraper_scheduler.py`
   - Or run via cron/scheduled task

3. **Manual Updates**
   - Use admin panel `/scrape-procurement` endpoint
   - Triggered via POST request (admin only)

## Monitoring

Check scraper logs:
```bash
# View scheduler output
tail -f scraper_scheduler.log

# Check database counts
psql $DATABASE_URL -c "SELECT COUNT(*) FROM contracts;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM federal_contracts;"
```

## Troubleshooting

### SAM.gov API Issues
- Verify API key is set: `echo $SAM_GOV_API_KEY`
- Check rate limits (default: 1000 requests/hour)
- Review API docs: https://open.gsa.gov/api/sam-gov-entity-api/

### Local Scraper Issues
- Government websites may change structure
- Check `local_gov_scraper.py` URL patterns
- Update selectors if pages redesigned

### Database Issues
- Ensure tables exist: Run `init_db()` in app.py
- Check for duplicate entries
- Verify foreign key constraints

## Future Enhancements

- [ ] Email notifications for new opportunities
- [ ] Machine learning for relevancy scoring
- [ ] Automated bid recommendation system
- [ ] Integration with more procurement platforms
- [ ] Mobile app for instant notifications
- [ ] API for third-party integrations

## Support

For issues or questions:
- Email: support@vacontracthub.com
- Admin Panel: Use scraper test buttons
- Logs: Check application logs for errors
