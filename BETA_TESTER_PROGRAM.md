# Beta Tester Program Documentation

## Overview
Limited beta tester program offering 100 users 1 year of FREE Premium access in exchange for feedback and early adoption.

## Features Implemented

### 1. Database Schema
**New columns in `leads` table:**
- `is_beta_tester` (BOOLEAN) - Flag to identify beta testers
- `beta_registered_at` (TIMESTAMP) - When user signed up as beta tester
- `beta_expiry_date` (TIMESTAMP) - When beta access expires (1 year from registration)

### 2. Registration Form (`/auth`)
**Visual Beta Tester Card:**
- Prominent yellow/warning-colored card with star icon
- Lists all benefits (1 year free, unlimited leads, priority support, feedback opportunity)
- Real-time spot counter showing remaining slots (0-100)
- Auto-disables when 100 beta testers reached
- Changes to warning color when <10 spots remain

**Benefits Displayed:**
- Full platform access for 12 months
- Unlimited contract leads and downloads
- Priority customer support
- Ability to provide feedback and shape features

### 3. API Endpoint
**Route:** `/api/beta-tester-count`
**Method:** GET
**Response:**
```json
{
  "success": true,
  "total": 15,
  "remaining": 85,
  "limit": 100
}
```

**Behavior:**
- Returns current beta tester count
- Calculates spots remaining (100 - total)
- JavaScript checks this on page load
- Disables checkbox and grays out section when full

### 4. Registration Logic
**When user checks beta tester box:**
1. Checks current count against 100 limit
2. If full, shows warning and registers as regular user
3. If available:
   - Sets `is_beta_tester = TRUE`
   - Sets `subscription_status = 'paid'`
   - Calculates `beta_expiry_date = today + 365 days`
   - Records `beta_registered_at = now()`

**Success Messages:**
- Beta Tester: "🎉🌟 Welcome, Beta Tester! Your account has been created with 1 YEAR FREE Premium access."
- Regular User: "🎉 Welcome! Your account has been created successfully."

### 5. Login Logic
**On each login, system checks:**
1. Is user a beta tester?
2. If yes, has expiry date passed?
3. If expired:
   - Updates `subscription_status = 'unpaid'`
   - Shows warning: "Your 1-year Beta Tester period has expired. Please subscribe to continue."
4. If active:
   - Grants `subscription_status = 'paid'`
   - Shows: "🌟 Beta Tester - X days of Premium access remaining"

### 6. Renewal Reminder System
**Script:** `beta_tester_renewal_reminder.py`
**Schedule:** Run daily via cron job

**Functionality:**
- Checks for beta testers expiring in 30 days
- Sends professional email reminder with:
  - Days remaining countdown
  - Expiry date
  - Benefits recap
  - Subscribe now button
  - Thank you message for early adoption

**Cron Setup:**
```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/app && .venv/bin/python beta_tester_renewal_reminder.py
```

## User Experience Flow

### Registration
1. User visits `/auth` (registration page)
2. JavaScript loads and checks `/api/beta-tester-count`
3. If spots available:
   - Shows green badge: "85 spots remaining"
   - Checkbox enabled
4. If <10 spots:
   - Shows warning badge: "9 spots remaining"
5. If full:
   - Shows gray badge: "Program Full - No spots available"
   - Checkbox disabled and section grayed out

### During Beta Period
- User logs in
- System checks expiry date
- If valid: "🌟 Beta Tester - 245 days of Premium access remaining"
- Full paid subscription features available
- Can access all contract leads, downloads, premium tools

### 30 Days Before Expiry
- Automated email sent with renewal reminder
- Details expiry date
- Provides subscription link
- Thanks user for beta participation

### On Expiry
- User logs in after expiry date
- System automatically updates status to 'unpaid'
- Message: "Your 1-year Beta Tester period has expired. Please subscribe to continue Premium access."
- User can still log in but has free tier limitations

### Post-Expiry
- User can subscribe at any time
- Subscription page: `/subscription`
- Monthly ($99) or Annual ($950) plans
- Can apply WIN50 promo code for 50% off

## Admin Functions

### Check Beta Tester Count
```python
from app import app, db
from sqlalchemy import text

with app.app_context():
    count = db.session.execute(
        text("SELECT COUNT(*) FROM leads WHERE is_beta_tester = TRUE OR is_beta_tester = 1")
    ).scalar()
    print(f"Beta testers: {count}/100")
```

### View All Beta Testers
```python
from app import app, db
from sqlalchemy import text
from datetime import datetime

with app.app_context():
    results = db.session.execute(
        text("""SELECT email, contact_name, beta_registered_at, beta_expiry_date 
                FROM leads WHERE is_beta_tester = TRUE 
                ORDER BY beta_registered_at ASC""")
    ).fetchall()
    
    for row in results:
        email, name, registered, expiry = row
        days_left = (expiry - datetime.utcnow()).days if expiry else 0
        print(f"{name} ({email}) - {days_left} days remaining")
```

### Manually Add Beta Tester
```python
from app import app, db
from sqlalchemy import text
from datetime import datetime, timedelta

with app.app_context():
    email = "user@example.com"
    
    # Check limit first
    count = db.session.execute(
        text("SELECT COUNT(*) FROM leads WHERE is_beta_tester = TRUE")
    ).scalar()
    
    if count >= 100:
        print("Beta tester program is full!")
    else:
        now = datetime.utcnow()
        expiry = now + timedelta(days=365)
        
        db.session.execute(text("""
            UPDATE leads 
            SET is_beta_tester = TRUE,
                beta_registered_at = :reg_date,
                beta_expiry_date = :exp_date,
                subscription_status = 'paid'
            WHERE email = :email
        """), {'email': email, 'reg_date': now, 'exp_date': expiry})
        
        db.session.commit()
        print(f"✅ Added {email} as beta tester")
```

## Migration Files
- `add_beta_tester_fields.py` - Adds columns to existing database
- Run once to upgrade database schema

## Security & Limits
- Hard limit of 100 beta testers enforced at:
  1. Registration form (checkbox disabled)
  2. Backend validation (double-check before insert)
- No way to exceed 100 without admin manual override
- Expiry dates stored in UTC timezone
- Automatic status downgrade on expiry (no manual intervention needed)

## Benefits to Business
1. **Early Adopters:** Build loyal user base
2. **Feedback:** Get real-world testing and feature requests
3. **Marketing:** 100 advocates spreading word
4. **Conversion:** Higher likelihood to convert after 1 year investment
5. **Testimonials:** Request reviews from satisfied beta users

## Monitoring
**Key Metrics to Track:**
- Beta tester signup rate
- Days to hit 100 limit
- Beta tester engagement (login frequency, leads viewed)
- Conversion rate (beta → paid after 1 year)
- Feedback quality and quantity
- Support ticket volume from beta users

## Future Enhancements
- Dashboard badge showing "Beta Tester" status
- Exclusive beta tester community forum
- Monthly beta tester surveys
- Special beta tester pricing after expiry (loyalty discount)
- Beta tester leaderboard (most engaged users)
