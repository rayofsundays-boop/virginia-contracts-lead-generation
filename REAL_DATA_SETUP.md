# Real Data Sources & Monthly Updates

## 🚫 REMOVING SAMPLE DATA

All sample/fake data has been identified and needs to be removed. Real leads will only come from:

### 1. **SAM.gov Federal Contracts** (Auto-Updated)
- **Source**: SAM.gov API (official government contracting portal)
- **Update Frequency**: Real-time via API or daily scraping
- **Setup Required**: SAM.gov API key (free)
- **Data Type**: Real federal cleaning contracts from VA

### 2. **Commercial Lead Requests** (User-Generated)
- **Source**: Businesses filling out `/request-cleaning` form
- **Update Frequency**: Real-time as businesses submit
- **No fake data**: Only actual business requests populate the database

### 3. **Residential Lead Requests** (User-Generated)
- **Source**: Homeowners filling out `/request-residential-cleaning` form
- **Update Frequency**: Real-time as homeowners submit
- **No fake data**: Only actual homeowner requests populate the database

---

## 📊 REAL DATA IMPLEMENTATION PLAN

### Step 1: Remove ALL Sample Data

**Location**: Lines 895-1100+ in `app.py`

Delete these sections:
- `sample_contracts` (local/state contracts)
- `sample_federal_contracts` (federal contracts)
- `sample_commercial` (commercial opportunities)

### Step 2: Implement SAM.gov API Integration

```python
# Add to requirements.txt
requests==2.31.0

# New file: sam_gov_fetcher.py
import requests
import os
from datetime import datetime

class SAMgovFetcher:
    def __init__(self):
        self.api_key = os.environ.get('SAM_GOV_API_KEY')
        self.base_url = 'https://api.sam.gov/opportunities/v2/search'
    
    def fetch_va_cleaning_contracts(self):
        """Fetch real cleaning contracts from Virginia"""
        params = {
            'api_key': self.api_key,
            'postedFrom': '30', # Last 30 days
            'postedTo': '0',
            'ptype': 'o', # Opportunities
            'ncode': '561720', # Janitorial Services NAICS
            'state': 'VA',
            'limit': 100
        }
        
        response = requests.get(self.base_url, params=params)
        
        if response.status_code == 200:
            opportunities = response.json().get('opportunitiesData', [])
            return self.parse_opportunities(opportunities)
        return []
    
    def parse_opportunities(self, opportunities):
        """Convert SAM.gov format to our database format"""
        contracts = []
        for opp in opportunities:
            contract = {
                'title': opp.get('title'),
                'agency': opp.get('departmentName'),
                'department': opp.get('subTier'),
                'location': f"{opp.get('placeOfPerformance', {}).get('city', '')}, VA",
                'value': self.estimate_value(opp),
                'deadline': opp.get('responseDeadLine'),
                'description': opp.get('description', '')[:500],
                'naics_code': opp.get('naics', [{}])[0].get('code'),
                'sam_gov_url': f"https://sam.gov/opp/{opp.get('noticeId')}",
                'notice_id': opp.get('noticeId'),
                'set_aside': opp.get('typeOfSetAside'),
                'posted_date': opp.get('postedDate')
            }
            contracts.append(contract)
        return contracts
    
    def estimate_value(self, opp):
        """Extract or estimate contract value"""
        # Try to get award amount or estimate from description
        award = opp.get('awardAmount') or opp.get('estimatedValue')
        if award:
            return f"${award:,.0f}"
        return "$500,000 - $5,000,000" # Typical range
```

### Step 3: Add Automated Monthly Updates

```python
# Add to app.py after initialization

from sam_gov_fetcher import SAMgovFetcher
import schedule
import threading

def update_federal_contracts():
    """Update federal contracts from SAM.gov monthly"""
    print("Fetching real federal contracts from SAM.gov...")
    fetcher = SAMgovFetcher()
    contracts = fetcher.fetch_va_cleaning_contracts()
    
    with app.app_context():
        # Clear old contracts (older than 90 days)
        db.session.execute(text('''
            DELETE FROM federal_contracts 
            WHERE posted_date < DATE('now', '-90 days')
        '''))
        
        # Insert new contracts
        for contract in contracts:
            db.session.execute(text('''
                INSERT OR IGNORE INTO federal_contracts 
                (title, agency, department, location, value, deadline, description, 
                 naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                VALUES (:title, :agency, :department, :location, :value, :deadline, 
                        :description, :naics_code, :sam_gov_url, :notice_id, 
                        :set_aside, :posted_date)
            '''), contract)
        
        db.session.commit()
        print(f"✅ Updated {len(contracts)} federal contracts")

def schedule_updates():
    """Run monthly updates in background thread"""
    schedule.every().month.do(update_federal_contracts)
    # Also run daily check for new contracts
    schedule.every().day.at("02:00").do(update_federal_contracts)
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

# Start scheduler in background
scheduler_thread = threading.Thread(target=schedule_updates, daemon=True)
scheduler_thread.start()
```

---

## 💰 PAYPAL INTEGRATION SETUP

### Step 1: Get Your PayPal Business Account

1. Go to https://www.paypal.com/businessmanagement/
2. Sign up for **PayPal Business** account (free)
3. Verify your business information
4. Get your **Client ID** and **Secret** from Developer Dashboard

### Step 2: PayPal Developer Setup

1. Visit https://developer.paypal.com/dashboard/
2. Go to **Apps & Credentials**
3. Create an app for your website
4. Copy these credentials:
   - **Client ID**: `AXXXXxxxxx...` (Sandbox for testing)
   - **Secret**: `EXXXXxxxxx...` (Keep secret!)
   - **Webhook ID**: (for payment notifications)

### Step 3: Add PayPal to Your App

**Add to requirements.txt:**
```
paypalrestsdk==1.13.1
```

**Add to app.py:**
```python
import paypalrestsdk

# PayPal Configuration
paypalrestsdk.configure({
    "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),  # 'sandbox' or 'live'
    "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
    "client_secret": os.environ.get('PAYPAL_SECRET')
})

# PayPal subscription plans
SUBSCRIPTION_PLANS = {
    'monthly': {
        'name': 'Monthly Subscription',
        'price': 99.00,
        'plan_id': 'P-XXXXXXXXXXXXX'  # Create in PayPal dashboard
    },
    'annual': {
        'name': 'Annual Subscription (Save 20%)',
        'price': 950.00,  # ~$79/month
        'plan_id': 'P-YYYYYYYYYYYYY'
    }
}
```

### Step 4: Create Subscription Route

```python
@app.route('/subscribe/<plan_type>')
@login_required
def subscribe(plan_type):
    """Initiate PayPal subscription"""
    user_email = session.get('user_email')
    
    if plan_type not in SUBSCRIPTION_PLANS:
        flash('Invalid subscription plan', 'error')
        return redirect(url_for('index'))
    
    plan = SUBSCRIPTION_PLANS[plan_type]
    
    # Create PayPal subscription
    subscription = paypalrestsdk.Subscription({
        "plan_id": plan['plan_id'],
        "subscriber": {
            "name": {
                "given_name": session.get('company_name', '').split()[0],
                "surname": session.get('company_name', '').split()[-1]
            },
            "email_address": user_email
        },
        "application_context": {
            "brand_name": "VA Contract Leads",
            "return_url": url_for('subscription_success', _external=True),
            "cancel_url": url_for('subscription_cancel', _external=True),
            "user_action": "SUBSCRIBE_NOW"
        }
    })
    
    if subscription.create():
        # Redirect to PayPal
        for link in subscription.links:
            if link.rel == "approve":
                return redirect(link.href)
    else:
        flash('Error creating subscription. Please try again.', 'error')
        return redirect(url_for('register'))

@app.route('/subscription-success')
@login_required
def subscription_success():
    """Handle successful PayPal subscription"""
    subscription_id = request.args.get('subscription_id')
    
    if subscription_id:
        # Update user to paid subscriber
        user_email = session.get('user_email')
        db.session.execute(text('''
            UPDATE leads 
            SET subscription_status = 'paid',
                paypal_subscription_id = :sub_id,
                subscription_start_date = :start_date
            WHERE email = :email
        '''), {
            'sub_id': subscription_id,
            'start_date': datetime.now(),
            'email': user_email
        })
        db.session.commit()
        
        flash('🎉 Subscription activated! Welcome to exclusive leads.', 'success')
        return redirect(url_for('lead_marketplace'))
    
    flash('Subscription verification failed. Please contact support.', 'error')
    return redirect(url_for('register'))

@app.route('/subscription-cancel')
def subscription_cancel():
    """Handle cancelled PayPal subscription"""
    flash('Subscription cancelled. You can try again anytime.', 'info')
    return redirect(url_for('register'))

@app.route('/webhook/paypal', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook events (subscription updates, cancellations)"""
    webhook_data = request.json
    event_type = webhook_data.get('event_type')
    
    if event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
        # User cancelled subscription
        subscription_id = webhook_data['resource']['id']
        db.session.execute(text('''
            UPDATE leads 
            SET subscription_status = 'cancelled'
            WHERE paypal_subscription_id = :sub_id
        '''), {'sub_id': subscription_id})
        db.session.commit()
    
    elif event_type == 'PAYMENT.SALE.COMPLETED':
        # Payment received
        subscription_id = webhook_data['resource']['billing_agreement_id']
        db.session.execute(text('''
            UPDATE leads 
            SET subscription_status = 'paid',
                last_payment_date = :payment_date
            WHERE paypal_subscription_id = :sub_id
        '''), {
            'sub_id': subscription_id,
            'payment_date': datetime.now()
        })
        db.session.commit()
    
    return jsonify({'status': 'success'}), 200
```

### Step 5: Update Database Schema

Add PayPal tracking columns to leads table:
```python
# Add to init_db() function
c.execute('''ALTER TABLE leads ADD COLUMN paypal_subscription_id TEXT''')
c.execute('''ALTER TABLE leads ADD COLUMN subscription_start_date DATE''')
c.execute('''ALTER TABLE leads ADD COLUMN last_payment_date DATE''')
```

### Step 6: Update Register Template

**Add to `templates/register.html`** (after form):

```html
<!-- PayPal Subscription Plans -->
<div class="row mt-5">
    <div class="col-12">
        <h3 class="text-center mb-4">Choose Your Subscription Plan</h3>
    </div>
    
    <div class="col-md-6">
        <div class="card shadow-lg">
            <div class="card-header bg-primary text-white">
                <h4>Monthly Plan</h4>
            </div>
            <div class="card-body text-center">
                <h1 class="display-3">$99<small>/month</small></h1>
                <ul class="list-unstyled my-4">
                    <li>✅ Unlimited lead access</li>
                    <li>✅ Email notifications</li>
                    <li>✅ Bidding system</li>
                    <li>✅ Contact details</li>
                    <li>✅ Cancel anytime</li>
                </ul>
                <a href="{{ url_for('subscribe', plan_type='monthly') }}" 
                   class="btn btn-primary btn-lg">
                    Subscribe Monthly
                </a>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card shadow-lg border-success">
            <div class="card-header bg-success text-white">
                <h4>Annual Plan <span class="badge badge-warning">SAVE 20%</span></h4>
            </div>
            <div class="card-body text-center">
                <h1 class="display-3">$950<small>/year</small></h1>
                <p class="text-muted">That's only $79/month!</p>
                <ul class="list-unstyled my-4">
                    <li>✅ Everything in Monthly</li>
                    <li>✅ <strong>Save $238/year</strong></li>
                    <li>✅ Priority support</li>
                    <li>✅ Early access to leads</li>
                    <li>✅ Annual contract bonus</li>
                </ul>
                <a href="{{ url_for('subscribe', plan_type='annual') }}" 
                   class="btn btn-success btn-lg">
                    Subscribe Annually
                </a>
            </div>
        </div>
    </div>
</div>

<!-- PayPal Trust Badge -->
<div class="text-center mt-4">
    <img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_111x69.jpg" 
         alt="PayPal" style="height: 50px;">
    <p class="text-muted">Secure payment processing by PayPal</p>
</div>
```

---

## 🔧 ENVIRONMENT VARIABLES NEEDED

Add these to your Render.com dashboard:

```bash
# SAM.gov API
SAM_GOV_API_KEY=your_sam_gov_api_key_here

# PayPal Configuration
PAYPAL_MODE=sandbox  # Change to 'live' when ready for production
PAYPAL_CLIENT_ID=your_client_id_here
PAYPAL_SECRET=your_secret_here

# Email (already configured)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

---

## 📝 STEP-BY-STEP DEPLOYMENT

### 1. Get SAM.gov API Key (FREE)
- Visit: https://open.gsa.gov/api/sam-gov-entity-api/
- Click "Get API Key" (requires free account)
- Verify email and copy API key
- Add to Render environment variables

### 2. Set Up PayPal Business
- Go to: https://www.paypal.com/business
- Sign up (free business account)
- Complete business verification
- Link bank account for payouts

### 3. Create PayPal Subscription Plans
- Login to: https://www.paypal.com/businessmanagement/
- Go to **Products & Services** → **Subscriptions**
- Create two plans:
  * **Monthly**: $99/month
  * **Annual**: $950/year
- Copy Plan IDs (format: `P-XXXXXXXXXXXXX`)
- Update `SUBSCRIPTION_PLANS` in app.py

### 4. Configure PayPal Webhooks
- Go to: https://developer.paypal.com/dashboard/
- **Apps & Credentials** → Your App → **Webhooks**
- Add webhook URL: `https://your-app.onrender.com/webhook/paypal`
- Select events:
  * `BILLING.SUBSCRIPTION.CANCELLED`
  * `BILLING.SUBSCRIPTION.CREATED`
  * `PAYMENT.SALE.COMPLETED`
- Save Webhook ID to environment variables

### 5. Remove Sample Data & Deploy
```bash
# Remove sample data from app.py (lines 895-1100+)
# Add new files: sam_gov_fetcher.py
# Update requirements.txt
# Commit and push

git add -A
git commit -m "Remove sample data, add SAM.gov API integration, add PayPal payments"
git push
```

---

## 🎯 RESULT: 100% REAL DATA

After implementation:
- ✅ No fake/sample data
- ✅ Real federal contracts from SAM.gov (updated daily)
- ✅ Real commercial leads from business submissions
- ✅ Real residential leads from homeowner submissions
- ✅ PayPal subscription payments
- ✅ Automatic monthly updates
- ✅ Professional payment processing

---

## 📞 YOUR PAYPAL INFORMATION

**Where your money goes:**
- Monthly subscriptions: $99 → Your PayPal business account
- Annual subscriptions: $950 → Your PayPal business account
- PayPal fee: ~2.9% + $0.30 per transaction
- **Your net per monthly subscription**: ~$96
- **Your net per annual subscription**: ~$922

**Payout Schedule:**
- PayPal transfers to your bank account automatically
- Default: Daily (for balances over $1)
- You can change to weekly or monthly in PayPal settings

**To Withdraw Funds:**
1. Login to PayPal
2. Go to **Wallet** → **Transfer Money**
3. Select your linked bank account
4. Enter amount and transfer (1-3 business days)

---

## 🚀 NEXT STEPS

1. **Get SAM.gov API key** (5 minutes)
2. **Create PayPal business account** (10 minutes)
3. **Create subscription plans in PayPal** (15 minutes)
4. **Remove sample data from app.py** (5 minutes)
5. **Add new code and deploy** (30 minutes)

**Total setup time: ~1 hour**

Then your platform will have:
- ✅ Real government contracts (auto-updated)
- ✅ Real business leads (user-submitted)
- ✅ PayPal payment processing
- ✅ Monthly recurring revenue
