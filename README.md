# Virginia Government Contracts - Lead Generation Platform

A Flask web application for government contracting lead generation, specifically focused on cleaning and maintenance contracts in Virginia cities including Hampton, Suffolk, Virginia Beach, Newport News, and Williamsburg.

## Features

- **Contract Listings**: Browse government contract opportunities across 5 Virginia cities
- **Company Registration**: Register cleaning companies to receive contract notifications
- **Location Filtering**: Filter contracts by specific Virginia cities
- **Lead Management**: Track registered companies and their capabilities
- **Responsive Design**: Mobile-friendly interface with Bootstrap styling

### AI Assistant (KB + Roles)
- Role-aware proposal/chat assistant at `/ai-assistant`
- Deterministic in-repo Knowledge Base (no external API calls)
- API: `POST /api/ai-assistant-reply` with `{ message, role? }`
- Transparent sources and suggested follow-ups
- See `AI_ASSISTANT_OVERVIEW.md` for full details

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
- `INTERNATIONAL_RSS_URL` – primary public procurement RSS feed (we filter entries containing "clean")
- `INTERNATIONAL_RSS_URLS` – optional comma-separated list of additional feeds to aggregate
- `EU_RSS_URL` – optional EU procurement RSS feed for cleaning (e.g., TED search)
- `CANADA_RSS_URL` – optional Canada procurement RSS feed for cleaning
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

### Run Unit Tests
```bash
"/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE/.venv/bin/python" -m unittest -q
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
### Authentication Debugging & Secure Credentials

The application purposely avoids shipping hard‑coded admin or demo user credentials.

Environment variables control authentication behavior:

| Variable | Purpose | Default | Notes |
|----------|---------|---------|-------|
| `ADMIN_USERNAME` | Admin login username | (unset) | Admin login disabled unless BOTH username & password are set |
| `ADMIN_PASSWORD` | Admin login password | (unset) | Choose a strong secret; rotate regularly |
| `AUTH_DEBUG` | Verbose signin logging | `0` | Set to `1` (or `true`) temporarily during debugging; prints form keys & validation path |
| `SEED_TEST_USER` | Seed a development sample user | `0` | If `1`, creates user `devsample` with password from `SEED_TEST_PASSWORD` |
| `SEED_TEST_PASSWORD` | Password for seeded dev user | `ChangeMe123!` | Only read when `SEED_TEST_USER=1`; change before enabling |

Example (temporary) development export:
```bash
export ADMIN_USERNAME="admin@example.com"
export ADMIN_PASSWORD="$(openssl rand -base64 24)"
export AUTH_DEBUG=1
export SEED_TEST_USER=1
export SEED_TEST_PASSWORD="DevOnly!Pass123"
```
Disable debug & test seeding before production:
```bash
unset AUTH_DEBUG
unset SEED_TEST_USER SEED_TEST_PASSWORD
```

Security recommendations:
- Never commit real credentials to the repository.
- Keep `AUTH_DEBUG` off in production to avoid leaking request patterns.
- Use a password manager or secret manager (e.g. AWS Secrets Manager) for `ADMIN_*` values.
- Enforce TLS (reverse proxy / load balancer) for deployment.

If admin credentials are not provided, admin login paths automatically redirect to the standard auth flow.

Use the included script for a quick smoke test:
```bash
export TEST_LIMIT=10
export INTERNATIONAL_RSS_URL="https://your-procurement-feed.example/rss"
# Optional additional feeds
export INTERNATIONAL_RSS_URLS="https://feed-one.example/rss,https://feed-two.example/rss"
export EU_RSS_URL="https://eu-procurement.example/rss"
export CANADA_RSS_URL="https://canada-procurement.example/rss"
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

---

Note on Chatbot Docs: `CHATBOT_QUICK_START.md` documents the earlier client-side-only chatbot. The live AI Assistant uses the role-aware KB + API described in `AI_ASSISTANT_OVERVIEW.md`.

## Two-Factor Authentication (2FA)

The platform now supports optional Time-based One-Time Password (TOTP) 2FA for user accounts.

### Overview
2FA adds a second verification step after the password. Supported by common authenticator apps:
- Google Authenticator
- Microsoft Authenticator
- 1Password / Bitwarden
- Authy

### Enabling 2FA
1. Sign in normally with username/email + password.
2. Visit `/enable-2fa` (linked from account/security sections if exposed) or manually navigate.
3. Scan the displayed secret (or copy manually) into your authenticator app.
4. Enter the 6-digit code and submit.
5. On success you will see a confirmation banner.

### Signing In with 2FA
1. Enter username/email + password as usual.
2. You are redirected to `/verify-2fa` (session is staged, not fully authenticated yet).
3. Enter the current 6‑digit code from your app. After success the full session is established.

### Disabling 2FA
POST to `/disable-2fa` while logged in (a button is shown on the enable page if already active). This clears the stored secret. Disabling reduces account security—recommend only for troubleshooting.

### Recovery Codes
If you lose access to your authenticator device you can use a one-time recovery code:
1. After enabling 2FA visit `/2fa-recovery-codes`.
2. Click Generate New Codes (this invalidates any previous unused codes).
3. Store the displayed codes securely (password manager or offline file). They are shown only once.
4. On the 2FA verification screen you may enter a recovery code instead of the 6-digit TOTP.

Recovery codes are hashed at rest; used codes are marked and cannot be reused.

### Forced Admin 2FA
Set `FORCE_ADMIN_2FA=1` to require any admin user to enable 2FA before accessing the platform beyond the enable screen.

### Secret Encryption
Provide `TWOFA_ENCRYPTION_KEY` (a 32-byte url-safe base64 Fernet key) to encrypt the stored TOTP secret. Example:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
export TWOFA_ENCRYPTION_KEY="<output>"
```
If absent or invalid, secrets are stored plaintext (a warning is printed). Existing plaintext secrets continue to work after adding a key; they will be re-encrypted upon regeneration.

### Rate Limiting
`/verify-2fa` enforces a simple in-memory limit: 5 failed attempts per user within 10 minutes → temporary block (requires re-login). Adjust logic in `record_twofa_attempt` / `too_many_twofa_attempts` if deploying multi-instance (for production, use a shared store like Redis).

### Environment / Dependencies
- Library: `pyotp` (added to `requirements.txt`).
- No external API dependency; all codes generated/validated locally.

### Database Additions
Columns added to `leads` table (auto-migrated on app start):
| Column | Type | Purpose |
|--------|------|---------|
| `twofa_enabled` | BOOLEAN/INTEGER | Flag indicating whether 2FA is active |
| `twofa_secret` | TEXT | Base32 TOTP secret (stored in plain form; consider encrypting at rest in future) |

### Security Notes & Roadmap
- Recovery codes implemented (hashed, one-time use).
- Secret encryption supported via Fernet key environment variable.
- Basic in-memory rate limiting implemented (augment with distributed store in clustered deployments).
- Admin 2FA enforcement available via `FORCE_ADMIN_2FA`.
- Future: UI for viewing last 2FA usage, email notification on new 2FA enabling, WebAuthn/FIDO2 support, distributed rate limit backend.

### Testing
Automated tests in `tests/test_2fa.py` cover enablement, login challenge, valid & invalid code flows.

If `pyotp` is not installed the feature gracefully degrades and informs the user.