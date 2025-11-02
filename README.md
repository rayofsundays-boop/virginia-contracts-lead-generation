# Virginia Government Contracts - Lead Generation Platform

A Flask web application for government contracting lead generation, specifically focused on cleaning and maintenance contracts in Virginia cities including Hampton, Suffolk, Virginia Beach, Newport News, and Williamsburg.

## Features

- **Contract Listings**: Browse government contract opportunities across 5 Virginia cities
- **Company Registration**: Register cleaning companies to receive contract notifications
- **Location Filtering**: Filter contracts by specific Virginia cities
- **Lead Management**: Track registered companies and their capabilities
- **Responsive Design**: Mobile-friendly interface with Bootstrap styling

## Virginia Cities Covered

- **Hampton, VA** - City Hall, municipal buildings, transit facilities
- **Suffolk, VA** - Municipal buildings, public schools, various facilities  
- **Virginia Beach, VA** - Convention center, police department, large-scale projects
- **Newport News, VA** - Library system, shipyard facilities, various contracts
- **Williamsburg, VA** - Historic area, courthouse, preservation-sensitive projects

## Installation & Setup

### Prerequisites
- Python 3.8+ 
- pip (Python package manager)

### 1. Clone or Download Project
```bash
# If using git:
git clone <repository-url>
cd "Lead Generartion for Cleaning Contracts (VA) ELITE"

# Or download and extract the project files
```

### 2. Set Up Virtual Environment (Recommended)
```bash
python -m venv .venv

# Activate virtual environment:
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional but Recommended)
Copy `.env.example` to `.env` and fill in values as needed:
```bash
cp .env.example .env
```

Key variables:
- `INTERNATIONAL_RSS_URL` – public procurement RSS feed for international quick wins (cleaning-related)
- `CRON_SECRET` – token for hitting `/cron/supply-daily`
- `PAYPAL_*` – subscription and payment configuration

### 5. Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000`

## VS Code Setup

This project includes VS Code configuration:

### Running with VS Code Tasks
1. Open project in VS Code
2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
3. Type "Tasks: Run Task"
4. Select "Run Flask App"

### Alternative: Run from Terminal
```bash
# Using the configured virtual environment:
"/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE/.venv/bin/python" app.py
```

## Project Structure

```
Lead Generartion for Cleaning Contracts (VA) ELITE/
├── .github/
│   └── copilot-instructions.md    # GitHub Copilot configuration
├── .venv/                         # Python virtual environment
├── .vscode/
│   └── tasks.json                 # VS Code task configuration
├── static/
│   └── style.css                  # Custom CSS styles
├── templates/                     # HTML templates
│   ├── base.html                  # Base template with navigation
│   ├── index.html                 # Homepage with featured contracts
│   ├── contracts.html             # All contracts listing with filters
│   ├── register.html              # Company registration form
│   └── leads.html                 # Registered companies dashboard
├── app.py                         # Main Flask application
├── requirements.txt               # Python dependencies
├── leads.db                       # SQLite database (created on first run)
└── README.md                      # This file
```

## Database Schema

### Contracts Table
- **id**: Primary key
- **title**: Contract title/name
- **agency**: Government agency/department
- **location**: City, State
- **value**: Contract value (as string)
- **deadline**: Application deadline
- **description**: Contract description
- **naics_code**: NAICS classification code
- **created_at**: Record creation timestamp

### Leads Table
- **id**: Primary key
- **company_name**: Company name
- **contact_name**: Primary contact person
- **email**: Contact email address
- **phone**: Contact phone number
- **state**: Company state location
- **experience_years**: Years of experience
- **certifications**: Certifications and licenses
- **created_at**: Registration timestamp

## Sample Contracts Included

The application comes pre-loaded with 10 sample government contracts:

1. **Hampton City Hall Cleaning Services** - $125,000
2. **Suffolk Municipal Building Janitorial** - $95,000
3. **Virginia Beach Convention Center Cleaning** - $350,000
4. **Newport News Library System Maintenance** - $75,000
5. **Williamsburg Historic Area Grounds Keeping** - $180,000
6. **Hampton Roads Transit Facility Cleaning** - $220,000
7. **Suffolk Public Schools Custodial Services** - $450,000
8. **Virginia Beach Police Department Cleaning** - $85,000
9. **Newport News Shipyard Office Cleaning** - $275,000
10. **Williamsburg Court House Maintenance** - $65,000

## Usage

### For Contractors
1. Visit the homepage to see latest contract opportunities
2. Browse all contracts with location filtering
3. Register your company to receive notifications
4. View contract details including deadlines and requirements

### For Administrators
1. View registered companies in the "Leads" section
2. Track company capabilities and experience levels
3. Monitor registration trends and statistics
4. Populate/refresh supply contracts:
	- `GET /admin/populate-if-empty` – populate if empty
	- `GET /admin/repopulate-supply-contracts` – force repopulation
	- `GET /admin/fetch-international-quick-wins` – fetch UK + RSS (deduped)
	- `GET /admin/db-stats` – view DB stats
	- `GET /cron/supply-daily?token=CRON_SECRET` – cron-safe refresh

### International Sources (Quick Wins)
- UK Contracts Finder via OCDS Search API (cleaning keyword)
- Generic RSS adapter (set `INTERNATIONAL_RSS_URL`)

All inbound values and deadlines are normalized with guards; missing/ambiguous fields are logged with warnings.

## Development

### Adding New Contracts
Contracts can be added directly to the database or by modifying the sample data in `app.py` in the `init_db()` function.

### Customizing Design
- Modify `static/style.css` for styling changes
- Update templates in the `templates/` folder
- Bootstrap 5.1.3 is included via CDN

### Database Management
The SQLite database (`leads.db`) is created automatically on first run. For production use, consider upgrading to PostgreSQL or MySQL.

### Testing International Ingestion (Optional)
Use the included script for a quick smoke test:
```bash
export TEST_LIMIT=10
export INTERNATIONAL_RSS_URL="https://your-procurement-feed.example/rss"
"/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE/.venv/bin/python" scripts/test_international_sources.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is intended for educational and business use in government contracting lead generation.

## Support

For issues or questions about this Virginia government contracting platform, please refer to the documentation or create an issue in the project repository.