# Environment Configuration Guide for ContractLink AI
# Complete setup instructions for all production features

## Required Environment Variables

### 🔐 Core Application Settings

```bash
# Flask Secret Key (REQUIRED)
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-secret-key-here

# Application URL (for email links)
APP_URL=https://contractlink.ai

# Admin Email (receives notifications)
ADMIN_EMAIL=admin@contractlink.ai
```

### 📧 Email Configuration (Transactional Emails)

**For Gmail SMTP:**
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # Not your regular password!
EMAIL_FROM=noreply@contractlink.ai
EMAIL_FROM_NAME=ContractLink AI
```

**How to get Gmail App Password:**
1. Go to Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate password for "Mail"
4. Copy 16-character password

**For SendGrid SMTP:**
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USER=apikey
EMAIL_PASSWORD=your-sendgrid-api-key
EMAIL_FROM=verified-sender@yourdomain.com
EMAIL_FROM_NAME=ContractLink AI
```

**For Mailgun SMTP:**
```bash
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USER=postmaster@your-domain.mailgun.org
EMAIL_PASSWORD=your-mailgun-password
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=ContractLink AI
```

### 🤖 OpenAI API (AI Classification & URL Generation)

```bash
# Get API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-api-key-here
```

**Cost Estimates:**
- RFP Classification: ~$0.001 per contract
- URL Generation: ~$0.002 per lead
- Monthly cost (1000 leads): ~$3

### 💳 PayPal Integration (Subscriptions)

```bash
# PayPal API Credentials (get from PayPal Developer Dashboard)
PAYPAL_CLIENT_ID=your-client-id
PAYPAL_CLIENT_SECRET=your-client-secret
PAYPAL_MODE=sandbox  # or 'live' for production

# PayPal Billing Plan IDs (create in PayPal Dashboard)
PAYPAL_MONTHLY_PLAN_ID=P-xxx
PAYPAL_ANNUAL_PLAN_ID=P-yyy

# WIN50 Promotion Discounted Plans
PAYPAL_MONTHLY_WIN50_PLAN_ID=P-aaa
PAYPAL_ANNUAL_WIN50_PLAN_ID=P-bbb
```

**PayPal Setup Steps:**
1. Create PayPal Business Account
2. Go to Dashboard → Apps & Credentials
3. Create REST API app
4. Copy Client ID and Secret
5. Create Billing Plans:
   - Monthly: $99/month
   - Annual: $950/year
   - WIN50 Monthly: $49.50/month
   - WIN50 Annual: $475/year

### 🔒 2FA Configuration (Admin Security)

```bash
# Force 2FA for admins
FORCE_ADMIN_2FA=true

# 2FA Encryption Key (REQUIRED if using 2FA)
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
TWOFA_ENCRYPTION_KEY=your-32-byte-base64-key
```

### 🐛 Debug Settings (Development Only)

```bash
# Enable verbose authentication logging
AUTH_DEBUG=0  # Set to 1 for development

# Flask Debug Mode
FLASK_DEBUG=False  # NEVER enable in production
```

### 📊 Database Configuration

**SQLite (Default for Development):**
```bash
# Automatically created as leads.db
# No configuration needed
```

**PostgreSQL (Production Recommended):**
```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

**Convert SQLite to PostgreSQL:**
```bash
# Export data from SQLite
python export_sqlite_data.py

# Import to PostgreSQL
python import_to_postgres.py
```

---

## Feature-Specific Configuration

### 🌐 SAM.gov API (Federal Contracts)

```bash
# Get API key from: https://sam.gov/data-services
SAM_GOV_API_KEY=your-sam-api-key

# Rate limiting (requests per minute)
SAM_GOV_RATE_LIMIT=10
```

### 🏗️ Construction Scraper

```bash
# Enable/disable scraper
CONSTRUCTION_SCRAPER_ENABLED=true

# Scraping intensity (1-5 leads per state)
CONSTRUCTION_SCRAPER_INTENSITY=2

# Update frequency (hours)
CONSTRUCTION_SCRAPER_INTERVAL=24
```

### 📍 Location-Based Pricing

No configuration needed - state cost-of-living data is built-in.

### 🎨 Branding Materials

No configuration needed - materials are served from static files.

---

## Environment File Templates

### Development (.env.development)

```bash
# Core
SECRET_KEY=dev-secret-key-change-in-production
APP_URL=http://localhost:5000
ADMIN_EMAIL=admin@localhost

# Email (Optional in dev)
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USER=
# EMAIL_PASSWORD=

# OpenAI (Optional - use demo mode if not configured)
# OPENAI_API_KEY=

# PayPal (Use sandbox)
PAYPAL_MODE=sandbox
# PAYPAL_CLIENT_ID=
# PAYPAL_CLIENT_SECRET=

# Debug
AUTH_DEBUG=1
FLASK_DEBUG=True
```

### Production (.env.production)

```bash
# Core (REQUIRED)
SECRET_KEY=<generate-strong-key>
APP_URL=https://contractlink.ai
ADMIN_EMAIL=admin@contractlink.ai

# Email (REQUIRED for transactional emails)
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USER=apikey
EMAIL_PASSWORD=<sendgrid-api-key>
EMAIL_FROM=noreply@contractlink.ai
EMAIL_FROM_NAME=ContractLink AI

# OpenAI (REQUIRED for AI features)
OPENAI_API_KEY=<openai-api-key>

# PayPal (REQUIRED for subscriptions)
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=<live-client-id>
PAYPAL_CLIENT_SECRET=<live-secret>
PAYPAL_MONTHLY_PLAN_ID=<plan-id>
PAYPAL_ANNUAL_PLAN_ID=<plan-id>
PAYPAL_MONTHLY_WIN50_PLAN_ID=<plan-id>
PAYPAL_ANNUAL_WIN50_PLAN_ID=<plan-id>

# 2FA (REQUIRED for admin security)
FORCE_ADMIN_2FA=true
TWOFA_ENCRYPTION_KEY=<generated-key>

# SAM.gov (REQUIRED for federal contracts)
SAM_GOV_API_KEY=<sam-api-key>

# Debug (DISABLE in production)
AUTH_DEBUG=0
FLASK_DEBUG=False

# Database (PostgreSQL recommended)
DATABASE_URL=postgresql://user:pass@host:5432/contractlink
```

---

## Testing Your Configuration

### Test Email Configuration

```bash
python -c "
from email_notifications import send_email
result = send_email(
    'test@example.com',
    'Test Email',
    '<h1>Email works!</h1>',
    'Email works!'
)
print('✅ Email sent!' if result else '❌ Email failed')
"
```

### Test OpenAI API

```bash
python -c "
import os
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': 'Say hello'}],
    max_tokens=10
)
print('✅ OpenAI connected:', response.choices[0].message.content)
"
```

### Test PayPal API

```bash
python -c "
import paypalrestsdk
import os
paypalrestsdk.configure({
    'mode': os.getenv('PAYPAL_MODE', 'sandbox'),
    'client_id': os.getenv('PAYPAL_CLIENT_ID'),
    'client_secret': os.getenv('PAYPAL_CLIENT_SECRET')
})
print('✅ PayPal configured' if paypalrestsdk.Api() else '❌ PayPal failed')
"
```

### Test Database Connection

```bash
python -c "
from app import app, db
with app.app_context():
    try:
        db.session.execute('SELECT 1')
        print('✅ Database connected')
    except Exception as e:
        print(f'❌ Database error: {e}')
"
```

---

## Security Best Practices

### 🔒 Secret Generation

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Generate TWOFA_ENCRYPTION_KEY:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 🛡️ Environment Security

- ✅ Never commit .env files to Git
- ✅ Use different keys for dev/staging/prod
- ✅ Rotate keys every 90 days
- ✅ Store production keys in secure vault (AWS Secrets Manager, etc.)
- ✅ Use environment-specific email addresses
- ✅ Enable 2FA for all admin accounts

### 🚨 Production Checklist

Before deploying to production:

- [ ] SECRET_KEY is unique and strong (64+ characters)
- [ ] FLASK_DEBUG=False
- [ ] AUTH_DEBUG=0
- [ ] Email credentials are for production service
- [ ] PayPal mode is 'live' with live credentials
- [ ] OpenAI API key has spending limits set
- [ ] 2FA is enabled (FORCE_ADMIN_2FA=true)
- [ ] Database is PostgreSQL (not SQLite)
- [ ] All API keys are from production accounts
- [ ] .env file has correct permissions (600)
- [ ] Backup database regularly
- [ ] Monitor API usage and costs

---

## Troubleshooting

### Email Not Sending

1. Check EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD
2. For Gmail: Ensure "Less secure app access" is enabled OR use App Password
3. Check SMTP logs: Enable debug with `EMAIL_DEBUG=True`
4. Verify sender email is verified (SendGrid, Mailgun)

### OpenAI API Errors

1. Check API key is valid: `echo $OPENAI_API_KEY`
2. Verify account has credits: https://platform.openai.com/usage
3. Check rate limits (Tier 1: 3 RPM, 10K TPM)
4. Review error messages in logs

### PayPal Integration Issues

1. Verify mode (sandbox vs live) matches credentials
2. Check billing plans are active in PayPal Dashboard
3. Ensure return URLs are correct
4. Review PayPal API logs in Dashboard

### Database Connection Errors

1. SQLite: Check file permissions on leads.db
2. PostgreSQL: Verify DATABASE_URL format
3. Test connection: `psql $DATABASE_URL -c "SELECT 1"`
4. Check firewall rules for database host

---

## Support

- 📖 Documentation: README.md, QUICKSTART.md
- 🐛 Issues: GitHub Issues
- 💬 Support: support@contractlink.ai
- 🔧 Admin Panel: /admin-enhanced

---

**Last Updated:** 2025-11-16
**Version:** 2.0.0
