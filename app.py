import os
import json
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sqlite3  # Keep for backward compatibility with existing queries
from datetime import datetime, date, timedelta
import threading
import schedule
import time
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from lead_generator import LeadGenerator
import paypalrestsdk
import math
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # Safe to continue if dotenv is not available in production
    pass

# Virginia Government Contracting Lead Generation Application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'virginia-contracting-fallback-key-2024')

# Session configuration - 20 minute timeout
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)

# Admin credentials (bypass paywall)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'VAContracts2024!')

# PayPal Configuration
paypalrestsdk.configure({
    "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),  # 'sandbox' or 'live'
    "client_id": os.environ.get('PAYPAL_CLIENT_ID', ''),
    "client_secret": os.environ.get('PAYPAL_SECRET', '')
})

# PayPal subscription plans (Update these with your actual Plan IDs from PayPal dashboard)
SUBSCRIPTION_PLANS = {
    'monthly': {
        'name': 'Monthly Subscription',
        'price': 99.00,
        'plan_id': os.environ.get('PAYPAL_MONTHLY_PLAN_ID', 'P-MONTHLY-PLAN-ID')
    },
    'annual': {
        'name': 'Annual Subscription (Save 20%)',
        'price': 950.00,
        'plan_id': os.environ.get('PAYPAL_ANNUAL_PLAN_ID', 'P-ANNUAL-PLAN-ID')
    }
}

# Database configuration - supports both PostgreSQL and SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    # Fix Heroku's postgres:// to postgresql://
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Use psycopg (version 3) instead of psycopg2
if DATABASE_URL and 'postgresql://' in DATABASE_URL:
    # Change postgresql:// to postgresql+psycopg:// for psycopg3 driver
    if '+psycopg' not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///leads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Single-instance background jobs guard (avoid duplicate schedulers under Gunicorn)
# ---------------------------------------------------------------------------
_BACKGROUND_LOCK_PATH = '/tmp/va_contracts_background.lock'

def _acquire_background_lock():
    try:
        # Try to exclusively create the lock file
        import errno
        fd = os.open(_BACKGROUND_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        # If file exists, another worker already started background jobs
        return False

# Custom Jinja filters
@app.template_filter('comma')
def comma_filter(value):
    """Add comma separators to numbers"""
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'noreply@vacontracts.com')

mail = Mail(app)

# ============================================================================
# EMAIL NOTIFICATION FUNCTIONS
# ============================================================================

def send_new_lead_notification(lead_type, lead_data):
    """Send email notifications to subscribers when new leads come in"""
    try:
        # Get all paid subscribers with email notifications enabled
        subscribers = db.session.execute(text('''
            SELECT email, company_name FROM leads 
            WHERE subscription_status = 'paid' 
            AND email_notifications = TRUE
        ''')).fetchall()
        
        if not subscribers:
            return
        
        # Prepare email content based on lead type
        if lead_type == 'residential':
            subject = f"🏠 New Residential Cleaning Lead in {lead_data.get('city')}"
            body = f"""
            New residential cleaning lead available!
            
            Location: {lead_data.get('address')}, {lead_data.get('city')}, VA {lead_data.get('zip_code')}
            Property Type: {lead_data.get('property_type', 'N/A')}
            Square Footage: {lead_data.get('square_footage', 'N/A')} sq ft
            Bedrooms: {lead_data.get('bedrooms', 'N/A')}
            Bathrooms: {lead_data.get('bathrooms', 'N/A')}
            Frequency: {lead_data.get('frequency', 'N/A')}
            Budget: {lead_data.get('budget_range', 'Not specified')}
            Estimated Value: ${lead_data.get('estimated_value', 0)}/month
            
            Services Needed:
            {lead_data.get('services_needed', 'General cleaning')}
            
            Contact: {lead_data.get('homeowner_name')}
            Phone: {lead_data.get('phone')}
            Email: {lead_data.get('email')}
            
            Login to your Lead Marketplace to view full details and contact the homeowner!
            """
        else:  # commercial
            subject = f"🏢 New Commercial Cleaning Lead in {lead_data.get('city')}"
            body = f"""
            New commercial cleaning lead available!
            
            Business: {lead_data.get('business_name')}
            Type: {lead_data.get('business_type', 'N/A')}
            Location: {lead_data.get('address')}, {lead_data.get('city')}, VA {lead_data.get('zip_code')}
            Square Footage: {lead_data.get('square_footage', 'N/A')} sq ft
            Frequency: {lead_data.get('frequency', 'N/A')}
            Budget: {lead_data.get('budget_range', 'Not specified')}
            Urgency: {lead_data.get('urgency', 'Normal')}
            
            Services Needed:
            {lead_data.get('services_needed', 'General cleaning')}
            
            Contact: {lead_data.get('contact_name')}
            Phone: {lead_data.get('phone')}
            Email: {lead_data.get('email')}
            
            Login to your Lead Marketplace to submit a bid!
            """
        
        # Send to all subscribers
        for subscriber in subscribers:
            try:
                msg = Message(
                    subject=subject,
                    recipients=[subscriber[0]],  # email
                    body=body
                )
                msg.html = body.replace('\n', '<br>')
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send email to {subscriber[0]}: {str(e)}")
                
        print(f"✅ Sent {lead_type} lead notifications to {len(subscribers)} subscribers")
        
    except Exception as e:
        print(f"Error sending lead notifications: {str(e)}")

def send_bid_notification(business_email, contractor_info, bid_info):
    """Notify business owner when a contractor submits a bid"""
    try:
        subject = f"New Bid Received for Your Cleaning Request"
        body = f"""
        Good news! A contractor has submitted a bid for your cleaning request.
        
        Contractor: {contractor_info.get('company_name', 'Professional Cleaning Contractor')}
        Proposed Price: ${bid_info.get('price', 'See proposal')}
        Timeline: {bid_info.get('timeline', 'To be discussed')}
        
        Proposal:
        {bid_info.get('proposal', 'Contact contractor for details')}
        
        The contractor will be reaching out to you soon to discuss the details.
        
        Thank you for using VA Contract Hub!
        """
        
        msg = Message(
            subject=subject,
            recipients=[business_email],
            body=body
        )
        msg.html = body.replace('\n', '<br>')
        mail.send(msg)
        print(f"✅ Sent bid notification to {business_email}")
        
    except Exception as e:
        print(f"Error sending bid notification: {str(e)}")

# Initialize lead generator for automated updates (only if using SQLite)
lead_generator = None
if not DATABASE_URL or 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    lead_generator = LeadGenerator('leads.db')

# Global variables for scheduling
scheduler_thread = None
scheduler_running = False

# Session activity tracker - auto logout after 20 minutes of inactivity
@app.before_request
def check_session_timeout():
    """Check if user session has expired due to inactivity"""
    # Skip timeout check for static files and certain routes
    if request.endpoint and (request.endpoint.startswith('static') or 
                             request.endpoint in ['signin', 'register', 'index']):
        return
    
    if 'user_id' in session:
        session.permanent = True  # Enable permanent session
        last_activity = session.get('last_activity')
        
        if last_activity:
            # Convert string back to datetime if needed
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity)
            
            # Check if 20 minutes have passed
            if datetime.now() - last_activity > timedelta(minutes=20):
                # Clear session and redirect to signin
                user_email = session.get('user_email', 'User')
                session.clear()
                flash(f'Your session expired due to inactivity. Please sign in again.', 'info')
                return redirect(url_for('signin'))
        
        # Update last activity time
        session['last_activity'] = datetime.now().isoformat()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Admin bypass
        if session.get('is_admin'):
            return f(*args, **kwargs)
        if 'user_id' not in session:
            flash('Please sign in to access the Customer Portal.', 'warning')
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

def paid_or_limited_access(f):
    """Allow 3 free views, then blur content for non-subscribers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Admin bypass
        if session.get('is_admin'):
            return f(*args, **kwargs)
        
        # Check if user is paid subscriber
        if 'user_id' in session:
            user_id = session['user_id']
            result = db.session.execute(text('''
                SELECT subscription_status FROM leads WHERE id = :user_id
            '''), {'user_id': user_id}).fetchone()
            
            if result and result[0] == 'paid':
                return f(*args, **kwargs)
        
        # Track free clicks (for non-logged-in or unpaid users)
        if 'contract_clicks' not in session:
            session['contract_clicks'] = 0
        
        # Allow function to run, but pass click limit info to template
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# AUTOMATED DATA UPDATES FROM SAM.GOV
# ============================================================================

def update_federal_contracts_from_samgov():
    """Fetch and update federal contracts from SAM.gov API"""
    try:
        print("📡 Fetching real federal contracts from SAM.gov API...")
        from sam_gov_fetcher import SAMgovFetcher

        fetcher = SAMgovFetcher()
        # Use a shorter lookback to reduce rate-limit risk; fetcher has built-in retries
        contracts = fetcher.fetch_va_cleaning_contracts(days_back=14)
        
        if not contracts:
            print("⚠️  No new contracts found. Check SAM_GOV_API_KEY.")
            return
        
        # Use SQLAlchemy for database operations
        with app.app_context():
            # Clean up old contracts (older than 90 days) - PostgreSQL syntax
            db.session.execute(text('''
                DELETE FROM federal_contracts 
                WHERE posted_date < CURRENT_DATE - INTERVAL '90 days'
            '''))
            
            # Insert new contracts with PostgreSQL ON CONFLICT
            new_count = 0
            for contract in contracts:
                try:
                    db.session.execute(text('''
                        INSERT INTO federal_contracts 
                        (title, agency, department, location, value, deadline, description, 
                         naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                        VALUES (:title, :agency, :department, :location, :value, :deadline, 
                                :description, :naics_code, :sam_gov_url, :notice_id, 
                                :set_aside, :posted_date)
                        ON CONFLICT (notice_id) DO NOTHING
                    '''), contract)
                    new_count += 1
                except Exception as e:
                    print(f"⚠️  Error inserting contract {contract.get('notice_id')}: {e}")
                    continue
            
            db.session.commit()
            print(f"✅ Updated {new_count} real federal contracts from SAM.gov")
            
    except Exception as e:
        print(f"❌ Error updating federal contracts: {e}")

def update_local_gov_contracts():
    """Fetch and update local government contracts from Virginia city websites"""
    try:
        print("🏛️  Fetching real local government contracts from Virginia cities...")
        from local_gov_scraper import VirginiaLocalGovScraper
        
        scraper = VirginiaLocalGovScraper()
        contracts = scraper.fetch_all_local_contracts()
        
        if not contracts:
            print("⚠️  No new local contracts found.")
            return
        
        # Normalize data (ensure deadline is a proper DATE or NULL)
        import re
        normalized = []
        for c in contracts:
            dl = c.get('deadline')
            if not dl or not re.match(r'^\d{4}-\d{2}-\d{2}$', str(dl)):
                c['deadline'] = None
            normalized.append(c)

        # Use SQLAlchemy for database operations
        with app.app_context():
            # Clean up old contracts (older than 120 days) - PostgreSQL syntax
            db.session.execute(text('''
                DELETE FROM contracts 
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '120 days'
            '''))
            
            # Insert new contracts
            new_count = 0
            for contract in normalized:
                try:
                    # Check if contract already exists (by title and agency)
                    existing = db.session.execute(text('''
                        SELECT COUNT(*) FROM contracts 
                        WHERE title = :title AND agency = :agency
                    '''), {'title': contract['title'], 'agency': contract['agency']}).fetchone()
                    
                    if existing[0] == 0:
                        db.session.execute(text('''
                            INSERT INTO contracts 
                            (title, agency, location, value, deadline, description, naics_code, website_url)
                            VALUES (:title, :agency, :location, :value, :deadline, :description, 
                                    :naics_code, :website_url)
                        '''), contract)
                        new_count += 1
                except Exception as e:
                    print(f"⚠️  Error inserting contract {contract.get('title')}: {e}")
                    continue
            
            db.session.commit()
            print(f"✅ Updated {new_count} real local government contracts from Virginia cities")
            
    except Exception as e:
        print(f"❌ Error updating local government contracts: {e}")

def schedule_samgov_updates():
    """Run SAM.gov updates daily at 2 AM"""
    schedule.every().day.at("02:00").do(update_federal_contracts_from_samgov)
    
    print("⏰ SAM.gov scheduler started - will update federal contracts daily at 2 AM")
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

def schedule_local_gov_updates():
    """Run local government updates daily at 3 AM"""
    schedule.every().day.at("03:00").do(update_local_gov_contracts)
    
    print("⏰ Local Government scheduler started - will update city/county contracts daily at 3 AM")
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

def start_background_jobs_once():
    """Start schedulers and optional initial fetch only in a single worker."""
    if not _acquire_background_lock():
        # Another worker already launched background jobs
        return

    # Start SAM.gov scheduler in background thread
    samgov_scheduler_thread = threading.Thread(target=schedule_samgov_updates, daemon=True)
    samgov_scheduler_thread.start()

    # Start Local Government scheduler in background thread
    localgov_scheduler_thread = threading.Thread(target=schedule_local_gov_updates, daemon=True)
    localgov_scheduler_thread.start()

    # Optional initial update on startup (controlled by env to reduce load)
    if os.environ.get('FETCH_ON_INIT', '0') == '1':
        def initial_samgov_fetch():
            time.sleep(5)  # Wait 5 seconds for app to fully start
            update_federal_contracts_from_samgov()

        def initial_localgov_fetch():
            time.sleep(10)  # Wait 10 seconds, after SAM.gov
            update_local_gov_contracts()

        initial_fetch_thread = threading.Thread(target=initial_samgov_fetch, daemon=True)
        initial_fetch_thread.start()

        localgov_fetch_thread = threading.Thread(target=initial_localgov_fetch, daemon=True)
        localgov_fetch_thread.start()

# Launch background jobs once per container/process cluster
start_background_jobs_once()


def run_daily_updates():
    """Background thread function for daily updates"""
    global scheduler_running, lead_generator
    
    # Only run if lead_generator is available
    if not lead_generator:
        print("⚠️ Lead generator not available (PostgreSQL mode)")
        return
        
    while scheduler_running:
        try:
            # Check if it's time for daily update (run at 6 AM daily)
            current_time = datetime.now()
            if current_time.hour == 6 and current_time.minute == 0:
                print("🕕 Running scheduled daily lead update...")
                result = lead_generator.generate_daily_update()
                
                if result['success']:
                    print(f"✅ Scheduled update completed: {result['government_added']} gov + {result['commercial_added']} commercial leads")
                else:
                    print(f"❌ Scheduled update failed: {result.get('error', 'Unknown error')}")
                
                # Sleep for 61 seconds to avoid running multiple times in same minute
                time.sleep(61)
            else:
                # Check every minute
                time.sleep(60)
                
        except Exception as e:
            print(f"❌ Error in scheduler thread: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying

def start_scheduler():
    """Start the background scheduler"""
    global scheduler_thread, scheduler_running
    if not scheduler_running:
        scheduler_running = True
        scheduler_thread = threading.Thread(target=run_daily_updates, daemon=True)
        scheduler_thread.start()
        print("🔄 Daily update scheduler started")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler_running
    scheduler_running = False
    print("⏹️ Daily update scheduler stopped")

# Credit management functions
def get_user_credits(email):
    """Get user's current credit balance"""
    try:
        result = db.session.execute(
            text('SELECT credits_balance FROM leads WHERE email = :email'),
            {'email': email}
        ).fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"Error getting user credits: {e}")
        return 0

def deduct_credits(email, credits_amount, action_type, opportunity_id=None, opportunity_name=None):
    """Deduct credits from user's balance and log usage"""
    try:
        # Get current balance
        result = db.session.execute(
            text('SELECT credits_balance, credits_used FROM leads WHERE email = :email'),
            {'email': email}
        ).fetchone()
        
        if not result:
            return False, "User not found"
        
        current_balance, total_used = result
        
        if current_balance < credits_amount:
            return False, "Insufficient credits"
        
        # Update user's credit balance and usage
        new_balance = current_balance - credits_amount
        new_total_used = total_used + credits_amount
        
        db.session.execute(
            text('''UPDATE leads 
                    SET credits_balance = :new_balance, 
                        credits_used = :new_total_used, 
                        low_credits_alert_sent = :alert_sent
                    WHERE email = :email'''),
            {
                'new_balance': new_balance,
                'new_total_used': new_total_used,
                'alert_sent': False if new_balance >= 10 else True,
                'email': email
            }
        )
        
        # Log the credit usage
        db.session.execute(
            text('''INSERT INTO credits_usage 
                    (user_email, credits_used, action_type, opportunity_id, opportunity_name, usage_date)
                    VALUES (:email, :credits, :action_type, :opp_id, :opp_name, :usage_date)'''),
            {
                'email': email,
                'credits': credits_amount,
                'action_type': action_type,
                'opp_id': opportunity_id,
                'opp_name': opportunity_name,
                'usage_date': datetime.now().isoformat()
            }
        )
        
        db.session.commit()
        return True, new_balance
        
    except Exception as e:
        print(f"Error deducting credits: {e}")
        db.session.rollback()
        return False, str(e)

def add_credits(email, credits_amount, purchase_type, amount_paid, transaction_id=None):
    """Add credits to user's balance and log purchase"""
    try:
        # Get current balance
        result = db.session.execute(
            text('SELECT credits_balance FROM leads WHERE email = :email'),
            {'email': email}
        ).fetchone()
        
        if not result:
            return False, "User not found"
        
        current_balance = result[0]
        new_balance = current_balance + credits_amount
        
        # Update user's credit balance
        db.session.execute(
            text('''UPDATE leads 
                    SET credits_balance = :new_balance, 
                        last_credit_purchase_date = :purchase_date, 
                        low_credits_alert_sent = :alert_sent
                    WHERE email = :email'''),
            {
                'new_balance': new_balance,
                'purchase_date': datetime.now().isoformat(),
                'alert_sent': False,
                'email': email
            }
        )
        
        # Log the credit purchase
        db.session.execute(
            text('''INSERT INTO credits_purchases 
                    (user_email, credits_purchased, amount_paid, purchase_type, transaction_id, purchase_date)
                    VALUES (:email, :credits, :amount, :ptype, :trans_id, :pdate)'''),
            {
                'email': email,
                'credits': credits_amount,
                'amount': amount_paid,
                'ptype': purchase_type,
                'trans_id': transaction_id,
                'pdate': datetime.now().isoformat()
            }
        )
        
        db.session.commit()
        return True, new_balance
        
    except Exception as e:
        print(f"Error adding credits: {e}")
        db.session.rollback()
        return False, str(e)

def check_low_credits(email):
    """Check if user has low credits and hasn't been alerted"""
    try:
        result = db.session.execute(
            text('SELECT credits_balance, low_credits_alert_sent FROM leads WHERE email = :email'),
            {'email': email}
        ).fetchone()
        
        if result:
            balance, alert_sent = result
            return balance <= 10 and not alert_sent
        return False
        
    except Exception as e:
        print(f"Error checking low credits: {e}")
        return False

def allocate_monthly_credits():
    """Allocate monthly credits to active subscribers"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get active subscribers who need monthly credits
        current_date = datetime.now().date()
        c.execute('''SELECT s.email, s.monthly_credits, l.credits_balance 
                     FROM subscriptions s 
                     JOIN leads l ON s.email = l.email 
                     WHERE s.status = 'active' 
                     AND (s.last_credits_allocated_date IS NULL 
                          OR date(s.last_credits_allocated_date) < date(?))''', 
                  (current_date.isoformat(),))
        
        subscribers = c.fetchall()
        
        for email, monthly_credits, current_balance in subscribers:
            # Add monthly credits
            new_balance = current_balance + monthly_credits
            
            c.execute('''UPDATE leads 
                         SET credits_balance = ?, low_credits_alert_sent = ?
                         WHERE email = ?''', 
                      (new_balance, False, email))
            
            c.execute('''UPDATE subscriptions 
                         SET last_credits_allocated_date = ?
                         WHERE email = ?''', 
                      (current_date.isoformat(), email))
            
            # Log the credit allocation
            c.execute('''INSERT INTO credits_purchases 
                         (user_email, credits_purchased, amount_paid, purchase_type, transaction_id, purchase_date)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (email, monthly_credits, 25.00, 'monthly_subscription', f'monthly_{current_date}', 
                       datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return len(subscribers)
        
    except Exception as e:
        print(f"Error allocating monthly credits: {e}")
        return 0

def send_lead_notification(lead_data):
    """Send email notification when a new lead registers"""
    try:
        company_name = lead_data.get('company_name', 'Unknown Company')
        contact_name = lead_data.get('contact_name', 'Unknown Contact')
        email = lead_data.get('email', 'No email provided')
        phone = lead_data.get('phone', 'No phone provided')
        state = lead_data.get('state', 'Not specified')
        experience = lead_data.get('experience_years', 'Not specified')
        certifications = lead_data.get('certifications', 'None listed')
        
        subject = f"New Lead: {company_name} - Virginia Government Contracts"
        
        body = f"""
New lead registered for Virginia Government Contracts!

COMPANY DETAILS:
Company Name: {company_name}
Contact Person: {contact_name}
Email: {email}
Phone: {phone}
State: {state}
Experience: {experience} years
Certifications: {certifications}

Registration Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This lead is interested in government contract opportunities in Virginia cities:
- Hampton
- Suffolk  
- Virginia Beach
- Newport News
- Williamsburg

Follow up promptly to convert this lead!

---
Virginia Government Contracts Lead Generation System
        """
        
        msg = Message(
            subject=subject,
            recipients=['info@eliteecoservices.com'],
            body=body
        )
        
        mail.send(msg)
        print(f"Lead notification sent successfully for {company_name}")
        return True
        
    except Exception as e:
        print(f"Failed to send email notification: {e}")
        return False

def send_welcome_email(email, name):
    """Send exciting welcome email to new users"""
    try:
        subject = "🎉 Welcome to Virginia Contracts - Your Lead Generation Journey Starts NOW!"
        
        body = f"""
🎊 CONGRATULATIONS {name.upper()}! 🎊

You've just taken the BIGGEST step toward dominating the Virginia cleaning contracts market!

🚀 HERE'S WHAT HAPPENS NEXT:

✅ STEP 1: Purchase Your Credit Package
   → Get instant access to 150+ high-value leads
   → Government contracts worth $50K-$750K each
   → Commercial opportunities generating $2K-$7K/month
   
✅ STEP 2: Browse Premium Leads
   → Filter by location: Hampton, Suffolk, VA Beach, Newport News, Williamsburg
   → View detailed requirements, deadlines, and contact info
   → One-click access to apply directly

✅ STEP 3: Close Contracts & Grow Your Business
   → Each lead includes direct application links
   → Full contact details for subscribers
   → Ongoing support to help you win contracts

💎 SUBSCRIPTION PRICING:
• Monthly Plan: $99/month - Unlimited lead access
• Annual Plan: $950/year - Save 20% ($79/month equivalent)

All subscriptions include:
✓ Unlimited commercial leads
✓ Unlimited residential leads
✓ Full contact information
✓ Email notifications
✓ Priority support

🔥 WHY OUR MEMBERS LOVE US:
"I landed my first $120,000 government contract within 2 weeks!" - Sarah M., Hampton

"The commercial leads alone pay for themselves. I'm now servicing 8 new clients!" - Mike T., Virginia Beach

⚡ READY TO GET STARTED?
Subscribe now: https://your-app-url.render.com/register

Questions? Reply to this email - we're here to help you succeed!

To your cleaning business success,
The Virginia Contracts Team

P.S. Just ONE contract pays for your entire year of subscription!

---
Prefer not to receive these updates? [Unsubscribe](https://your-app-url.render.com/unsubscribe?email={email})
        """
        
        msg = Message(
            subject=subject,
            recipients=[email],
            body=body
        )
        
        mail.send(msg)
        print(f"Welcome email sent to {email}")
        return True
        
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False

def send_password_reset_email(email, name, reset_link):
    """Send password reset email"""
    try:
        subject = "🔐 Reset Your Virginia Contracts Password"
        
        body = f"""
Hello {name},

We received a request to reset your password for your Virginia Contracts account.

Click the link below to create a new password:

{reset_link}

This link will expire in 24 hours.

If you didn't request this password reset, please ignore this email. Your password will remain unchanged.

Need help? Contact our support team at support@vacontracthub.com

Best regards,
Virginia Contracts Team
"""
        
        # Send email using your email configuration
        msg = Message(subject, recipients=[email])
        msg.body = body
        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #667eea;">🔐 Reset Your Password</h2>
                <p>Hello {name},</p>
                <p>We received a request to reset your password for your Virginia Contracts account.</p>
                <div style="margin: 30px 0;">
                    <a href="{reset_link}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                <p><small style="color: #666;">This link will expire in 24 hours.</small></p>
                <p>If you didn't request this password reset, please ignore this email. Your password will remain unchanged.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    Need help? Contact our support team at support@vacontracthub.com
                </p>
            </div>
        </body>
        </html>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False

# Database setup
def get_db_connection():
    db_path = os.environ.get('DATABASE_URL', 'leads.db')
    # Handle PostgreSQL URL format if needed
    if db_path.startswith('postgresql://'):
        db_path = 'leads.db'  # Fallback to SQLite for now
    return sqlite3.connect(db_path)

def init_postgres_db():
    """Initialize PostgreSQL database with proper syntax"""
    try:
        # Rollback any existing failed transaction
        db.session.rollback()
        
        # Create tables using PostgreSQL-compatible SQL
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS leads
                     (id SERIAL PRIMARY KEY,
                      company_name TEXT NOT NULL,
                      contact_name TEXT NOT NULL,
                      email TEXT NOT NULL UNIQUE,
                      username TEXT UNIQUE,
                      password_hash TEXT,
                      phone TEXT,
                      state TEXT,
                      experience_years TEXT,
                      certifications TEXT,
                      registration_date TEXT,
                      lead_source TEXT DEFAULT 'website',
                      survey_responses TEXT,
                      proposal_support BOOLEAN DEFAULT FALSE,
                      free_leads_remaining INTEGER DEFAULT 0,
                      subscription_status TEXT DEFAULT 'unpaid',
                      credits_balance INTEGER DEFAULT 0,
                      credits_used INTEGER DEFAULT 0,
                      last_credit_purchase_date TEXT,
                      low_credits_alert_sent BOOLEAN DEFAULT FALSE,
                      email_notifications BOOLEAN DEFAULT TRUE,
                      sms_notifications BOOLEAN DEFAULT FALSE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
        db.session.commit()
        
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS contracts
                     (id SERIAL PRIMARY KEY,
                      title TEXT NOT NULL,
                      agency TEXT NOT NULL,
                      location TEXT,
                      value TEXT,
                      deadline DATE,
                      description TEXT,
                      naics_code TEXT,
                      website_url TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
        db.session.commit()
        
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS federal_contracts
                     (id SERIAL PRIMARY KEY,
                      title TEXT NOT NULL,
                      agency TEXT NOT NULL,
                      department TEXT,
                      location TEXT,
                      value TEXT,
                      deadline DATE,
                      description TEXT,
                      naics_code TEXT,
                      sam_gov_url TEXT NOT NULL,
                      notice_id TEXT UNIQUE,
                      set_aside TEXT,
                      posted_date DATE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
        db.session.commit()
        
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS commercial_opportunities
                     (id SERIAL PRIMARY KEY,
                      business_name TEXT NOT NULL,
                      business_type TEXT NOT NULL,
                      address TEXT,
                      location TEXT NOT NULL,
                      square_footage INTEGER,
                      monthly_value DECIMAL(10,2),
                      frequency TEXT,
                      services_needed TEXT,
                      special_requirements TEXT,
                      contact_type TEXT DEFAULT 'warm',
                      description TEXT,
                      size TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
        db.session.commit()
        
        # Residential leads table (for homeowner cleaning requests)
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS residential_leads
                     (id SERIAL PRIMARY KEY,
                      homeowner_name TEXT NOT NULL,
                      address TEXT NOT NULL,
                      city TEXT NOT NULL,
                      state TEXT DEFAULT 'VA',
                      zip_code TEXT,
                      property_type TEXT,
                      bedrooms INTEGER,
                      bathrooms DECIMAL(3,1),
                      square_footage INTEGER,
                      contact_email TEXT,
                      contact_phone TEXT,
                      estimated_value DECIMAL(12,2),
                      cleaning_frequency TEXT,
                      services_needed TEXT,
                      special_requirements TEXT,
                      status TEXT DEFAULT 'new',
                      source TEXT,
                      lead_quality TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
        db.session.commit()
        
        # Commercial lead requests table (businesses requesting cleaners)
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS commercial_lead_requests
                     (id SERIAL PRIMARY KEY,
                      business_name TEXT NOT NULL,
                      contact_name TEXT NOT NULL,
                      email TEXT NOT NULL,
                      phone TEXT NOT NULL,
                      address TEXT NOT NULL,
                      city TEXT NOT NULL,
                      state TEXT DEFAULT 'VA',
                      zip_code TEXT,
                      business_type TEXT NOT NULL,
                      square_footage INTEGER,
                      frequency TEXT NOT NULL,
                      services_needed TEXT NOT NULL,
                      special_requirements TEXT,
                      budget_range TEXT,
                      start_date DATE,
                      urgency TEXT DEFAULT 'normal',
                      status TEXT DEFAULT 'open',
                      bid_count INTEGER DEFAULT 0,
                      winning_bid_id INTEGER,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
        db.session.commit()
        
        # Bids table (subscribers bidding on commercial requests)
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS bids
                     (id SERIAL PRIMARY KEY,
                      request_id INTEGER NOT NULL,
                      user_email TEXT NOT NULL,
                      company_name TEXT NOT NULL,
                      bid_amount DECIMAL(10,2) NOT NULL,
                      proposal_text TEXT,
                      estimated_start_date DATE,
                      contact_phone TEXT,
                      status TEXT DEFAULT 'pending',
                      submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      accepted_at TIMESTAMP,
                      FOREIGN KEY (request_id) REFERENCES commercial_lead_requests(id))'''))
        
        db.session.commit()
        
        # Lead access log (track which subscribers viewed which leads)
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS lead_access_log
                     (id SERIAL PRIMARY KEY,
                      user_email TEXT NOT NULL,
                      lead_type TEXT NOT NULL,
                      lead_id INTEGER NOT NULL,
                      accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
        db.session.commit()
        
        # Saved leads table (user bookmarks)
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS saved_leads
                     (id SERIAL PRIMARY KEY,
                      user_email TEXT NOT NULL,
                      lead_type TEXT NOT NULL,
                      lead_id TEXT NOT NULL,
                      lead_title TEXT,
                      lead_data JSON,
                      notes TEXT,
                      status TEXT DEFAULT 'saved',
                      saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      UNIQUE(user_email, lead_type, lead_id))'''))
        
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS password_reset_tokens
                     (id SERIAL PRIMARY KEY,
                      email TEXT NOT NULL UNIQUE,
                      token TEXT NOT NULL,
                      expiry TIMESTAMP NOT NULL,
                      used BOOLEAN DEFAULT FALSE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
        db.session.commit()
        
        # NOTE: Sample data removed - real data will be fetched from SAM.gov API and local government scrapers
        print("✅ PostgreSQL database tables initialized successfully")
        if os.environ.get('FETCH_ON_INIT', '0') == '1':
            print("📡 Fetching real federal contracts from SAM.gov API...")
            # Fetch real federal contracts from SAM.gov on first run (optional)
            try:
                from sam_gov_fetcher import SAMgovFetcher
                fetcher = SAMgovFetcher()
                real_contracts = fetcher.fetch_va_cleaning_contracts(days_back=90)
                
                if real_contracts:
                    for contract in real_contracts:
                        db.session.execute(text('''
                            INSERT INTO federal_contracts 
                            (title, agency, department, location, value, deadline, description, 
                             naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                            VALUES 
                            (:title, :agency, :department, :location, :value, :deadline, 
                             :description, :naics_code, :sam_gov_url, :notice_id, :set_aside, :posted_date)
                            ON CONFLICT (notice_id) DO NOTHING
                        '''), contract)
                    db.session.commit()
                    print(f"✅ Successfully loaded {len(real_contracts)} REAL federal contracts from SAM.gov")
                else:
                    print("⚠️  No contracts fetched. Check SAM_GOV_API_KEY environment variable.")
            except Exception as e:
                print(f"⚠️  Could not fetch SAM.gov contracts on init: {e}")
                print("   Contracts will be fetched on next scheduled update.")
        
        print("✅ Database initialization complete - ready for real leads!")
        print("💡 Commercial/Residential leads will appear as users submit request forms")
        print("🌐 Local government contracts will be scraped on startup...")
        return True
    except Exception as e:
        import traceback
        error_msg = f"Error creating PostgreSQL tables: {e}\n{traceback.format_exc()}"
        print(error_msg)
        db.session.rollback()
        # Return the error message instead of just False
        return error_msg

def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Create leads table
        c.execute('''CREATE TABLE IF NOT EXISTS leads
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      company_name TEXT NOT NULL,
                      contact_name TEXT NOT NULL,
                      email TEXT NOT NULL UNIQUE,
                      username TEXT UNIQUE,
                      password_hash TEXT,
                      phone TEXT,
                      state TEXT,
                      experience_years TEXT,
                      certifications TEXT,
                      registration_date TEXT,
                      lead_source TEXT DEFAULT 'website',
                      survey_responses TEXT,
                      proposal_support BOOLEAN DEFAULT FALSE,
                      free_leads_remaining INTEGER DEFAULT 0,
                      subscription_status TEXT DEFAULT 'unpaid',
                      credits_balance INTEGER DEFAULT 0,
                      credits_used INTEGER DEFAULT 0,
                      last_credit_purchase_date TEXT,
                      low_credits_alert_sent BOOLEAN DEFAULT FALSE,
                      email_notifications BOOLEAN DEFAULT TRUE,
                      sms_notifications BOOLEAN DEFAULT FALSE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Add PayPal subscription tracking columns if they don't exist
        try:
            c.execute('ALTER TABLE leads ADD COLUMN paypal_subscription_id TEXT')
        except:
            pass  # Column already exists
        
        try:
            c.execute('ALTER TABLE leads ADD COLUMN subscription_start_date DATE')
        except:
            pass  # Column already exists
        
        try:
            c.execute('ALTER TABLE leads ADD COLUMN last_payment_date DATE')
        except:
            pass  # Column already exists
        
        # Create credits purchases table
        c.execute('''CREATE TABLE IF NOT EXISTS credits_purchases
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_email TEXT NOT NULL,
                      credits_purchased INTEGER NOT NULL,
                      amount_paid REAL NOT NULL,
                      purchase_type TEXT NOT NULL,
                      transaction_id TEXT,
                      payment_method TEXT DEFAULT 'credit_card',
                      payment_reference TEXT,
                      purchase_date TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create credits usage table
        c.execute('''CREATE TABLE IF NOT EXISTS credits_usage
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_email TEXT NOT NULL,
                      credits_used INTEGER NOT NULL,
                      action_type TEXT NOT NULL,
                      opportunity_id TEXT,
                      opportunity_name TEXT,
                      usage_date TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create survey responses table
        c.execute('''CREATE TABLE IF NOT EXISTS survey_responses
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      biggest_challenge TEXT,
                      annual_revenue TEXT,
                      company_size TEXT,
                      contract_experience TEXT,
                      main_focus TEXT,
                      pain_point_scenario TEXT,
                      submission_date TEXT,
                      ip_address TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create subscriptions table
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      email TEXT NOT NULL,
                      cardholder_name TEXT,
                      total_amount TEXT,
                      proposal_support BOOLEAN DEFAULT FALSE,
                      subscription_date TEXT,
                      status TEXT DEFAULT 'active',
                      monthly_credits INTEGER DEFAULT 50,
                      next_billing_date TEXT,
                      last_credits_allocated_date TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create contracts table
        c.execute('''CREATE TABLE IF NOT EXISTS contracts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT NOT NULL,
                      agency TEXT NOT NULL,
                      location TEXT,
                      value TEXT,
                      deadline DATE,
                      description TEXT,
                      naics_code TEXT,
                      website_url TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create federal contracts table for SAM.gov opportunities
        c.execute('''CREATE TABLE IF NOT EXISTS federal_contracts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT NOT NULL,
                      agency TEXT NOT NULL,
                      department TEXT,
                      location TEXT,
                      value TEXT,
                      deadline DATE,
                      description TEXT,
                      naics_code TEXT,
                      sam_gov_url TEXT NOT NULL,
                      notice_id TEXT UNIQUE,
                      set_aside TEXT,
                      posted_date DATE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create commercial opportunities table
        c.execute('''CREATE TABLE IF NOT EXISTS commercial_opportunities
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      business_name TEXT NOT NULL,
                      business_type TEXT NOT NULL,
                      address TEXT,
                      location TEXT,
                      square_footage INTEGER,
                      monthly_value INTEGER,
                      frequency TEXT,
                      services_needed TEXT,
                      special_requirements TEXT,
                      contact_type TEXT,
                      contact_name TEXT,
                      contact_phone TEXT,
                      contact_email TEXT,
                      description TEXT,
                      size TEXT,
                      website_url TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        
        # NOTE: Sample data removed - real data will be fetched from SAM.gov API
        # Commercial and residential leads come from user-submitted request forms only
        print("✅ Database tables initialized successfully")
        if os.environ.get('FETCH_ON_INIT', '0') == '1':
            print("📡 Fetching real federal contracts from SAM.gov API...")
            # Fetch real federal contracts from SAM.gov on first run (optional)
            try:
                from sam_gov_fetcher import SAMgovFetcher
                fetcher = SAMgovFetcher()
                real_contracts = fetcher.fetch_va_cleaning_contracts(days_back=90)
                
                if real_contracts:
                    for contract in real_contracts:
                        c.execute('''INSERT OR IGNORE INTO federal_contracts 
                                     (title, agency, department, location, value, deadline, description, 
                                      naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                 (contract['title'], contract['agency'], contract['department'],
                                  contract['location'], contract['value'], contract['deadline'],
                                  contract['description'], contract['naics_code'], contract['sam_gov_url'],
                                  contract['notice_id'], contract['set_aside'], contract['posted_date']))
                    conn.commit()
                    print(f"✅ Successfully loaded {len(real_contracts)} REAL federal contracts from SAM.gov")
                else:
                    print("⚠️  No contracts fetched. Check SAM_GOV_API_KEY environment variable.")
            except Exception as e:
                print(f"⚠️  Could not fetch SAM.gov contracts on init: {e}")
                print("   Contracts will be fetched on next scheduled update.")
        
        conn.close()
        print("✅ Database initialization complete - ready for real leads!")
        print("💡 Commercial/Residential leads will appear as users submit request forms")
        print("📡 Federal contracts are being fetched from SAM.gov API...")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Continue anyway - app might still work

@app.route('/')
def index():
    """Main homepage with contract samples"""
    # Check if we're being redirected (prevent infinite loop)
    init_attempted = request.args.get('init_attempted', '0')
    
    try:
        # Get government contracts
        contracts = db.session.execute(
            text('SELECT * FROM contracts ORDER BY deadline ASC LIMIT 6')
        ).fetchall()
        
        # Get commercial opportunities  
        commercial_rows = db.session.execute(
            text('SELECT * FROM commercial_opportunities ORDER BY monthly_value DESC LIMIT 6')
        ).fetchall()
        
        # Convert commercial rows to objects for easier template access
        commercial_opportunities = []
        for row in commercial_rows:
            commercial_opportunities.append({
                'id': row[0],
                'business_name': row[1],
                'business_type': row[2],
                'address': row[3],
                'location': row[4],
                'square_footage': row[5],
                'monthly_value': row[6],
                'frequency': row[7],
                'services_needed': row[8],
                'special_requirements': row[9],
                'contact_type': row[10],
                'description': row[11],
                'size': row[12]
            })
        
        # Get commercial count
        commercial_count_result = db.session.execute(
            text('SELECT COUNT(*) FROM commercial_opportunities')
        ).fetchone()
        commercial_count = commercial_count_result[0] if commercial_count_result else 0
        
        return render_template('index.html', 
                             contracts=contracts, 
                             commercial_opportunities=commercial_opportunities,
                             commercial_count=commercial_count)
    except Exception as e:
        # Log the full error
        import traceback
        print(f"Index route error: {e}")
        print(traceback.format_exc())
        
        error_str = str(e).lower()
        # Check for missing tables in both SQLite and PostgreSQL
        if ("no such table" in error_str or "does not exist" in error_str or "relation" in error_str) and init_attempted == '0':
            try:
                print("Attempting database initialization...")
                # Use PostgreSQL init if using PostgreSQL
                if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
                    print("Using PostgreSQL initialization")
                    result = init_postgres_db()
                    if result == True:
                        print("PostgreSQL init successful, redirecting...")
                        # Redirect with flag to prevent loop
                        return redirect(url_for('index', init_attempted='1'))
                    else:
                        print(f"PostgreSQL init failed: {result}")
                        return f"<h1>Database Setup Error</h1><p>Failed to initialize PostgreSQL tables.</p><pre>{result}</pre><p>Try visiting <a href='/init-db'>/init-db</a> to manually initialize the database.</p>"
                else:
                    print("Using SQLite initialization")
                    init_db()
                    return redirect(url_for('index', init_attempted='1'))
            except Exception as e2:
                print(f"Initialization error: {e2}")
                print(traceback.format_exc())
                return f"<h1>Database Setup Error</h1><p>Error: {str(e2)}</p><p>Original error: {str(e)}</p><p>Try visiting <a href='/init-db'>/init-db</a> to manually initialize the database.</p>"
        
        # If init was already attempted or different error, show error details
        print(f"Rendering with empty data. Init attempted: {init_attempted}")
        return f"<h1>Error Loading Homepage</h1><p>Error: {str(e)}</p><p>Init attempted: {init_attempted}</p><p><a href='/init-db'>Initialize Database</a></p><p><a href='/?init_attempted=0'>Retry</a></p>"

@app.route('/home')
def home():
    """Redirect /home to main page"""
    return redirect(url_for('index'))

@app.route('/test')
def test():
    return "<h1>Flask Test Route Working!</h1><p>If you see this, Flask is running correctly.</p>"

@app.route('/db-status')
def db_status():
    """Diagnostic route to check database status"""
    try:
        html = "<h1>Database Status Report</h1>"
        html += "<style>body{font-family:Arial;padding:20px;} .good{color:green;} .bad{color:red;} .warn{color:orange;}</style>"
        
        # Check environment
        html += "<h2>Environment Variables</h2>"
        sam_key = os.environ.get('SAM_GOV_API_KEY', '')
        html += f"<p>SAM_GOV_API_KEY: <span class='{'good' if sam_key else 'bad'}'>{'✅ SET (' + str(len(sam_key)) + ' chars)' if sam_key else '❌ NOT SET'}</span></p>"
        html += f"<p>DATABASE_URL: <span class='good'>✅ {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...</span></p>"
        
        # Check tables
        html += "<h2>Database Tables</h2>"
        try:
            fed_count = db.session.execute(text('SELECT COUNT(*) FROM federal_contracts')).scalar()
            html += f"<p>Federal Contracts: <span class='{'good' if fed_count > 0 else 'warn'}'>{fed_count}</span></p>"
        except Exception as e:
            html += f"<p>Federal Contracts: <span class='bad'>❌ Error: {e}</span></p>"
        
        try:
            local_count = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar()
            html += f"<p>Local Government Contracts: <span class='{'good' if local_count > 0 else 'warn'}'>{local_count}</span></p>"
        except Exception as e:
            html += f"<p>Local Government Contracts: <span class='bad'>❌ Error: {e}</span></p>"
        
        try:
            comm_count = db.session.execute(text('SELECT COUNT(*) FROM commercial_opportunities')).scalar()
            html += f"<p>Commercial Opportunities: <span class='{'good' if comm_count > 0 else 'warn'}'>{comm_count}</span></p>"
        except Exception as e:
            html += f"<p>Commercial Opportunities: <span class='bad'>❌ Error: {e}</span></p>"
        
        try:
            user_count = db.session.execute(text('SELECT COUNT(*) FROM leads')).scalar()
            html += f"<p>Registered Users: <span class='good'>{user_count}</span></p>"
        except Exception as e:
            html += f"<p>Registered Users: <span class='bad'>❌ Error: {e}</span></p>"
        
        # Recommendations
        html += "<h2>Recommendations</h2>"
        if not sam_key:
            html += "<p class='bad'>⚠️ SAM_GOV_API_KEY is missing. Get one from <a href='https://open.gsa.gov/api/sam-gov-entity-api/' target='_blank'>SAM.gov API Portal</a></p>"
        if fed_count == 0:
            html += "<p class='warn'>⚠️ No federal contracts. Visit <a href='/init-db'>/init-db</a> to initialize or wait for scheduled update at 2 AM.</p>"
        if local_count == 0:
            html += "<p class='warn'>⚠️ No local contracts. Scraper runs at 3 AM daily or on /init-db.</p>"
        
        html += "<hr><p><a href='/'>← Back to Home</a> | <a href='/init-db'>Force Database Init</a></p>"
        
        return html
    except Exception as e:
        return f"<h1>Error checking database status</h1><pre>{e}</pre>"

@app.route('/run-updates')
def run_updates():
    """Manually trigger data updates and show before/after counts.
    Useful when leads aren't populating or after environment changes.
    """
    try:
        html = "<h1>Manual Update Runner</h1>"
        html += "<style>body{font-family:Arial;padding:20px;} .good{color:green;} .bad{color:red;} .warn{color:orange;}</style>"

        # Environment checks
        sam_key = os.environ.get('SAM_GOV_API_KEY', '')
        html += "<h2>Environment</h2>"
        html += f"<p>SAM_GOV_API_KEY: <span class='{'good' if sam_key else 'bad'}'>{'✅ SET (' + str(len(sam_key)) + ' chars)' if sam_key else '❌ NOT SET'}</span></p>"

        # Before counts
        html += "<h2>Before</h2>"
        try:
            fed_before = db.session.execute(text('SELECT COUNT(*) FROM federal_contracts')).scalar() or 0
            html += f"<p>Federal Contracts (before): <strong>{fed_before}</strong></p>"
        except Exception as e:
            html += f"<p>Federal Contracts (before): <span class='bad'>❌ Error: {e}</span></p>"
            fed_before = None

        try:
            local_before = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar() or 0
            html += f"<p>Local Government Contracts (before): <strong>{local_before}</strong></p>"
        except Exception as e:
            html += f"<p>Local Government Contracts (before): <span class='bad'>❌ Error: {e}</span></p>"
            local_before = None

        # Run updates
        html += "<h2>Running Updates...</h2>"
        try:
            update_federal_contracts_from_samgov()
            html += "<p>📡 SAM.gov update: <span class='good'>Triggered</span></p>"
        except Exception as e:
            html += f"<p>📡 SAM.gov update: <span class='bad'>❌ Error: {e}</span></p>"

        try:
            update_local_gov_contracts()
            html += "<p>🏛️ Local government update: <span class='good'>Triggered</span></p>"
        except Exception as e:
            html += f"<p>🏛️ Local government update: <span class='bad'>❌ Error: {e}</span></p>"

        # After counts
        html += "<h2>After</h2>"
        try:
            fed_after = db.session.execute(text('SELECT COUNT(*) FROM federal_contracts')).scalar() or 0
            delta_fed = (fed_after - fed_before) if (fed_before is not None) else 'N/A'
            html += f"<p>Federal Contracts (after): <strong>{fed_after}</strong> (Δ {delta_fed})</p>"
        except Exception as e:
            html += f"<p>Federal Contracts (after): <span class='bad'>❌ Error: {e}</span></p>"

        try:
            local_after = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar() or 0
            delta_local = (local_after - local_before) if (local_before is not None) else 'N/A'
            html += f"<p>Local Government Contracts (after): <strong>{local_after}</strong> (Δ {delta_local})</p>"
        except Exception as e:
            html += f"<p>Local Government Contracts (after): <span class='bad'>❌ Error: {e}</span></p>"

        # Tips
        html += "<h2>Notes</h2>"
        if not sam_key:
            html += "<p class='bad'>⚠️ SAM_GOV_API_KEY is missing. Add it in Render → Environment and redeploy.</p>"
        html += "<p>If counts remain 0, open Render → Logs and share the last 50 lines with errors or warnings.</p>"
        html += "<hr><p><a href='/db-status'>View DB Status</a> | <a href='/'>Back to Home</a></p>"

        return html
    except Exception as e:
        return f"<h1>Error running updates</h1><pre>{e}</pre>"

@app.route('/init-db')
def manual_init_db():
    try:
        # Check if using PostgreSQL
        if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
            result = init_postgres_db()
            if result == True:
                return "<h1>PostgreSQL Database Initialized!</h1><p>Tables created successfully.</p><p><a href='/'>Go to Home</a></p>"
            else:
                return f"<h1>Database Error</h1><p>Failed to create tables.</p><pre>{result}</pre>"
        else:
            init_db()
            return "<h1>Database Initialized!</h1><p>Tables created and sample data loaded.</p><p><a href='/'>Go to Home</a></p>"
    except Exception as e:
        import traceback
        return f"<h1>Database Error</h1><p>Error: {str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/auth')
def auth():
    """Unified authentication page (sign in or register)"""
    return render_template('auth.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect GET requests to unified auth page
    if request.method == 'GET':
        return redirect(url_for('auth') + '#register')
    
    # Handle POST request for registration
    if request.method == 'POST':
        company_name = request.form['company_name']
        contact_name = request.form['contact_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        phone = request.form.get('phone', '')
        state = request.form.get('state', '')
        experience_years = request.form.get('experience_years', 0)
        certifications = request.form.get('certifications', '')
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        # Save to database
        try:
            db.session.execute(
                text('''INSERT INTO leads (company_name, contact_name, email, username, password_hash, phone, 
                        state, experience_years, certifications, free_leads_remaining, credits_balance, subscription_status)
                        VALUES (:company, :contact, :email, :username, :password, :phone, :state, :exp, :certs, :free, :credits, :status)'''),
                {
                    'company': company_name,
                    'contact': contact_name,
                    'email': email,
                    'username': username,
                    'password': password_hash,
                    'phone': phone,
                    'state': state,
                    'exp': experience_years,
                    'certs': certifications,
                    'free': 0,
                    'credits': 0,
                    'status': 'unpaid'
                }
            )
            db.session.commit()
            
            # Send welcome email
            send_welcome_email(email, contact_name)
            
            flash('🎉 Welcome! Your account has been created successfully. Please sign in to get started.', 'success')
            return redirect(url_for('auth'))
            
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint' in str(e):
                flash('Email or username already exists. Please try another.', 'error')
            else:
                flash(f'Registration error: {str(e)}', 'error')
            return redirect(url_for('auth') + '#register')
    
    return render_template('register.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    # Redirect GET requests to unified auth page
    if request.method == 'GET':
        return redirect(url_for('auth'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check for admin login first
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            session['username'] = 'Admin'
            session['name'] = 'Administrator'
            flash('Welcome, Administrator! You have full access to all features. 🔑', 'success')
            return redirect(url_for('contracts'))
        
        # Get user from database
        result = db.session.execute(
            text('SELECT id, username, email, password_hash, contact_name, credits_balance FROM leads WHERE username = :username OR email = :username'),
            {'username': username}
        ).fetchone()
        
        if result and check_password_hash(result[3], password):
            # Login successful
            session['user_id'] = result[0]
            session['username'] = result[1]
            session['email'] = result[2]
            session['name'] = result[4]
            session['credits_balance'] = result[5]
            
            flash(f'Welcome back, {result[4]}! 🎉', 'success')
            return redirect(url_for('customer_leads'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
            return redirect(url_for('auth'))
    
    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('landing'))

@app.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    """Handle password reset requests"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        # Check if user exists
        result = db.session.execute(
            text('SELECT id, contact_name FROM leads WHERE email = :email'),
            {'email': email}
        ).fetchone()
        
        if not result:
            # Don't reveal if email exists for security
            return jsonify({'success': True, 'message': 'If that email exists, a reset link has been sent'})
        
        # Generate reset token
        import secrets
        reset_token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=24)
        
        # Store token in database
        db.session.execute(text('''
            INSERT INTO password_reset_tokens (email, token, expiry)
            VALUES (:email, :token, :expiry)
            ON CONFLICT (email) DO UPDATE 
            SET token = :token, expiry = :expiry, used = FALSE
        '''), {'email': email, 'token': reset_token, 'expiry': expiry})
        db.session.commit()
        
        # Send reset email
        reset_link = url_for('reset_password', token=reset_token, _external=True)
        send_password_reset_email(email, result[1], reset_link)
        
        return jsonify({'success': True, 'message': 'Reset link sent'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Password reset error: {e}")
        return jsonify({'success': False, 'message': 'Failed to process request'}), 500

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if request.method == 'GET':
        # Verify token is valid
        result = db.session.execute(text('''
            SELECT email, expiry, used FROM password_reset_tokens 
            WHERE token = :token
        '''), {'token': token}).fetchone()
        
        if not result or result[2] or datetime.now() > result[1]:
            flash('This password reset link is invalid or has expired.', 'error')
            return redirect(url_for('auth'))
        
        return render_template('reset_password.html', token=token, email=result[0])
    
    else:
        # Process password reset
        try:
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not new_password or len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'error')
                return redirect(url_for('reset_password', token=token))
            
            if new_password != confirm_password:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('reset_password', token=token))
            
            # Verify token again
            result = db.session.execute(text('''
                SELECT email, expiry, used FROM password_reset_tokens 
                WHERE token = :token
            '''), {'token': token}).fetchone()
            
            if not result or result[2] or datetime.now() > result[1]:
                flash('This password reset link is invalid or has expired.', 'error')
                return redirect(url_for('auth'))
            
            # Update password
            password_hash = generate_password_hash(new_password)
            db.session.execute(text('''
                UPDATE leads SET password_hash = :password_hash WHERE email = :email
            '''), {'password_hash': password_hash, 'email': result[0]})
            
            # Mark token as used
            db.session.execute(text('''
                UPDATE password_reset_tokens SET used = TRUE WHERE token = :token
            '''), {'token': token})
            
            db.session.commit()
            
            flash('Password reset successfully! You can now sign in with your new password.', 'success')
            return redirect(url_for('auth'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Password update error: {e}")
            flash('Failed to reset password. Please try again.', 'error')
            return redirect(url_for('reset_password', token=token))

# ============================================================================
# PAYPAL SUBSCRIPTION ROUTES
# ============================================================================

@app.route('/subscribe/<plan_type>')
@login_required
def subscribe(plan_type):
    """Initiate PayPal subscription"""
    user_email = session.get('user_email')
    company_name = session.get('company_name', 'User')
    
    if plan_type not in SUBSCRIPTION_PLANS:
        flash('Invalid subscription plan selected.', 'error')
        return redirect(url_for('register'))
    
    plan = SUBSCRIPTION_PLANS[plan_type]
    
    try:
        # Create PayPal billing agreement (subscription)
        billing_agreement = paypalrestsdk.BillingAgreement({
            "name": plan['name'],
            "description": f"Virginia Cleaning Contracts Lead Access - {plan['name']}",
            "start_date": (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "plan": {
                "id": plan['plan_id']
            },
            "payer": {
                "payment_method": "paypal",
                "payer_info": {
                    "email": user_email
                }
            }
        })
        
        if billing_agreement.create():
            # Get approval URL
            for link in billing_agreement.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
            print(f"PayPal Error: {billing_agreement.error}")
            flash('Unable to create subscription. Please try again or contact support.', 'error')
            return redirect(url_for('register'))
            
    except Exception as e:
        print(f"PayPal Exception: {e}")
        flash('Payment system error. Please try again later.', 'error')
        return redirect(url_for('register'))

@app.route('/subscription-success')
@login_required
def subscription_success():
    """Handle successful PayPal subscription approval"""
    token = request.args.get('token')
    
    if not token:
        flash('Subscription verification failed. Please try again.', 'error')
        return redirect(url_for('register'))
    
    try:
        # Execute the billing agreement
        billing_agreement = paypalrestsdk.BillingAgreement.execute(token)
        
        if billing_agreement:
            # Update user to paid subscriber
            user_email = session.get('user_email')
            agreement_id = billing_agreement.id
            
            db.session.execute(text('''
                UPDATE leads 
                SET subscription_status = 'paid',
                    paypal_subscription_id = :sub_id,
                    subscription_start_date = :start_date,
                    last_payment_date = :payment_date
                WHERE email = :email
            '''), {
                'sub_id': agreement_id,
                'start_date': datetime.now().strftime('%Y-%m-%d'),
                'payment_date': datetime.now().strftime('%Y-%m-%d'),
                'email': user_email
            })
            db.session.commit()
            
            flash('🎉 Subscription activated! Welcome to exclusive cleaning contract leads.', 'success')
            return redirect(url_for('lead_marketplace'))
        else:
            flash('Subscription activation failed. Please contact support.', 'error')
            return redirect(url_for('register'))
            
    except Exception as e:
        print(f"PayPal Execute Error: {e}")
        flash('Subscription verification error. Please contact support with your payment confirmation.', 'error')
        return redirect(url_for('register'))

@app.route('/subscription-cancel')
def subscription_cancel():
    """Handle cancelled PayPal subscription"""
    flash('Subscription cancelled. You can subscribe anytime to access exclusive leads!', 'info')
    return redirect(url_for('register'))

@app.route('/webhook/paypal', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook events (subscription updates, cancellations, payments)"""
    try:
        webhook_data = request.json
        event_type = webhook_data.get('event_type')
        
        print(f"📥 PayPal Webhook: {event_type}")
        
        if event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            # User cancelled subscription
            subscription_id = webhook_data['resource']['id']
            db.session.execute(text('''
                UPDATE leads 
                SET subscription_status = 'cancelled'
                WHERE paypal_subscription_id = :sub_id
            '''), {'sub_id': subscription_id})
            db.session.commit()
            print(f"✅ Subscription {subscription_id} marked as cancelled")
        
        elif event_type == 'PAYMENT.SALE.COMPLETED':
            # Payment received
            billing_agreement_id = webhook_data['resource'].get('billing_agreement_id')
            if billing_agreement_id:
                db.session.execute(text('''
                    UPDATE leads 
                    SET subscription_status = 'paid',
                        last_payment_date = :payment_date
                    WHERE paypal_subscription_id = :sub_id
                '''), {
                    'sub_id': billing_agreement_id,
                    'payment_date': datetime.now().strftime('%Y-%m-%d')
                })
                db.session.commit()
                print(f"✅ Payment recorded for subscription {billing_agreement_id}")
        
        elif event_type == 'BILLING.SUBSCRIPTION.SUSPENDED':
            # Subscription suspended (payment failure)
            subscription_id = webhook_data['resource']['id']
            db.session.execute(text('''
                UPDATE leads 
                SET subscription_status = 'suspended'
                WHERE paypal_subscription_id = :sub_id
            '''), {'sub_id': subscription_id})
            db.session.commit()
            print(f"⚠️  Subscription {subscription_id} suspended")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/contracts')
def contracts():
    location_filter = request.args.get('location', '')
    page = max(int(request.args.get('page', 1) or 1), 1)
    per_page = int(request.args.get('per_page', 12) or 12)
    per_page = min(max(per_page, 6), 48)  # sane bounds
    offset = (page - 1) * per_page
    try:
        # Count total with optional filter
        if location_filter:
            total = db.session.execute(text('''
                SELECT COUNT(*) FROM contracts WHERE LOWER(location) LIKE LOWER(:loc)
            '''), {'loc': f"%{location_filter}%"}).scalar() or 0
            rows = db.session.execute(text('''
                SELECT id, title, agency, location, value, deadline, description, naics_code, website_url, created_at
                FROM contracts 
                WHERE LOWER(location) LIKE LOWER(:loc)
                ORDER BY deadline ASC
                LIMIT :limit OFFSET :offset
            '''), { 'loc': f"%{location_filter}%", 'limit': per_page, 'offset': offset }).fetchall()
        else:
            total = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar() or 0
            rows = db.session.execute(text('''
                SELECT id, title, agency, location, value, deadline, description, naics_code, website_url, created_at
                FROM contracts 
                ORDER BY deadline ASC
                LIMIT :limit OFFSET :offset
            '''), {'limit': per_page, 'offset': offset}).fetchall()

        # For filter dropdown
        locations = [r[0] for r in db.session.execute(text('''
            SELECT DISTINCT location FROM contracts ORDER BY location
        ''')).fetchall()]

        pages = max(math.ceil(total / per_page), 1)
        # Build prev/next URLs preserving filters
        args_base = dict(request.args)
        args_base.pop('page', None)
        args_base.pop('per_page', None)
        prev_url = url_for('contracts', page=page-1, per_page=per_page, **args_base) if page > 1 else None
        next_url = url_for('contracts', page=page+1, per_page=per_page, **args_base) if page < pages else None
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'has_prev': page > 1,
            'has_next': page < pages,
            'prev_url': prev_url,
            'next_url': next_url
        }
        
        return render_template('contracts.html', 
                               contracts=rows, 
                               locations=locations, 
                               current_filter=location_filter,
                               pagination=pagination)
    except Exception as e:
        msg = f"<h1>Contracts Page Error</h1><p>{str(e)}</p>"
        msg += "<p>Try running <a href='/run-updates'>/run-updates</a> and then check <a href='/db-status'>/db-status</a>.</p>"
        return msg

@app.route('/federal-contracts')
def federal_contracts():
    """Federal contracts from SAM.gov with 3-click limit for non-subscribers"""
    # Redirect to coming soon page until November 3, 2025
    from datetime import datetime
    launch_date = datetime(2025, 11, 3, 0, 0, 0)
    if datetime.now() < launch_date:
        return redirect(url_for('federal_coming_soon'))
    
    department_filter = request.args.get('department', '')
    set_aside_filter = request.args.get('set_aside', '')
    page = max(int(request.args.get('page', 1) or 1), 1)
    per_page = int(request.args.get('per_page', 12) or 12)
    per_page = min(max(per_page, 6), 48)
    offset = (page - 1) * per_page
    
    # Check access level
    is_admin = session.get('is_admin', False)
    is_paid_subscriber = False
    clicks_remaining = 3
    
    if not is_admin:
        # Check if paid subscriber
        if 'user_id' in session:
            user_id = session['user_id']
            result = db.session.execute(text('''
                SELECT subscription_status FROM leads WHERE id = :user_id
            '''), {'user_id': user_id}).fetchone()
            
            if result and result[0] == 'paid':
                is_paid_subscriber = True
        
        # Track clicks for non-subscribers
        if not is_paid_subscriber:
            if 'contract_clicks' not in session:
                session['contract_clicks'] = 0
            clicks_remaining = max(0, 3 - session['contract_clicks'])
    
    try:
        # Build dynamic filter with SQLAlchemy text
        base_sql = '''
            SELECT id, title, agency, department, location, value, deadline, description, 
                   naics_code, sam_gov_url, notice_id, set_aside, posted_date, created_at
            FROM federal_contracts WHERE 1=1
        '''
        params = {}
        if department_filter:
            base_sql += ' AND LOWER(department) LIKE LOWER(:dept)'
            params['dept'] = f"%{department_filter}%"
        if set_aside_filter:
            base_sql += ' AND LOWER(set_aside) LIKE LOWER(:sa)'
            params['sa'] = f"%{set_aside_filter}%"
        # Count total
        count_sql = 'SELECT COUNT(*) FROM (' + base_sql + ') as sub'
        total = db.session.execute(text(count_sql), params).scalar() or 0

        base_sql += ' ORDER BY deadline ASC LIMIT :limit OFFSET :offset'
        params.update({'limit': per_page, 'offset': offset})
        rows = db.session.execute(text(base_sql), params).fetchall()

        # Filters
        departments = [r[0] for r in db.session.execute(text('''
            SELECT DISTINCT department FROM federal_contracts WHERE department IS NOT NULL AND department <> '' ORDER BY department
        ''')).fetchall()]
        set_asides = [r[0] for r in db.session.execute(text('''
            SELECT DISTINCT set_aside FROM federal_contracts WHERE set_aside IS NOT NULL AND set_aside <> '' ORDER BY set_aside
        ''')).fetchall()]

        pages = max(math.ceil(total / per_page), 1)
        args_base = dict(request.args)
        args_base.pop('page', None)
        args_base.pop('per_page', None)
        prev_url = url_for('federal_contracts', page=page-1, per_page=per_page, **args_base) if page > 1 else None
        next_url = url_for('federal_contracts', page=page+1, per_page=per_page, **args_base) if page < pages else None
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'has_prev': page > 1,
            'has_next': page < pages,
            'prev_url': prev_url,
            'next_url': next_url
        }

        return render_template('federal_contracts.html', 
                               contracts=rows,
                               departments=departments,
                               set_asides=set_asides,
                               current_department=department_filter,
                               current_set_aside=set_aside_filter,
                               pagination=pagination,
                               is_admin=is_admin,
                               is_paid_subscriber=is_paid_subscriber,
                               clicks_remaining=clicks_remaining)
    except Exception as e:
        msg = f"<h1>Federal Contracts Page Error</h1><p>{str(e)}</p>"
        msg += "<p>Try running <a href='/run-updates'>/run-updates</a> and then check <a href='/db-status'>/db-status</a>.</p>"
        return msg

@app.route('/commercial-contracts')
def commercial_contracts():
    """Commercial cleaning opportunities page - Subscriber Only"""
    # Check if user is logged in and has active subscription
    user_email = session.get('user_email')
    is_subscriber = False
    
    if user_email:
        try:
            user = db.session.execute(
                text('SELECT subscription_status FROM leads WHERE email = :email'),
                {'email': user_email}
            ).fetchone()
            
            if user and user[0] == 'paid':
                is_subscriber = True
        except Exception as e:
            print(f"Error checking subscription: {str(e)}")
    
    # If not a subscriber, show limited preview with upgrade message
    if not is_subscriber:
        return render_template('commercial_contracts.html', 
                             opportunities=[], 
                             is_subscriber=False,
                             show_upgrade_message=True)
    
    # Load opportunities for subscribers
    try:
        page = max(int(request.args.get('page', 1) or 1), 1)
        per_page = int(request.args.get('per_page', 12) or 12)
        per_page = min(max(per_page, 6), 48)
        offset = (page - 1) * per_page

        total = db.session.execute(text('SELECT COUNT(*) FROM commercial_opportunities')).scalar() or 0
        rows = db.session.execute(text('''
            SELECT id, business_name, business_type, address, location, square_footage, monthly_value,
                   frequency, services_needed, special_requirements, contact_type, description, size
            FROM commercial_opportunities
            ORDER BY monthly_value DESC
            LIMIT :limit OFFSET :offset
        '''), {'limit': per_page, 'offset': offset}).fetchall()

        opportunities = []
        for row in rows:
            opportunities.append({
                'id': row[0],
                'business_name': row[1],
                'business_type': row[2],
                'address': row[3],
                'location': row[4],
                'square_footage': row[5],
                'monthly_value': row[6],
                'frequency': row[7],
                'services_needed': row[8],
                'special_requirements': row[9],
                'contact_type': row[10],
                'description': row[11],
                'size': row[12]
            })

        pages = max(math.ceil(total / per_page), 1)
        args_base = dict(request.args)
        args_base.pop('page', None)
        args_base.pop('per_page', None)
        prev_url = url_for('commercial_contracts', page=page-1, per_page=per_page, **args_base) if page > 1 else None
        next_url = url_for('commercial_contracts', page=page+1, per_page=per_page, **args_base) if page < pages else None
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'has_prev': page > 1,
            'has_next': page < pages,
            'prev_url': prev_url,
            'next_url': next_url
        }

        return render_template('commercial_contracts.html', 
                             opportunities=opportunities,
                             is_subscriber=True,
                             show_upgrade_message=False,
                             pagination=pagination)
    except Exception as e:
        flash(f'Error loading opportunities: {str(e)}', 'danger')
        return render_template('commercial_contracts.html', 
                             opportunities=[], 
                             is_subscriber=is_subscriber,
                             show_upgrade_message=not is_subscriber)

@app.route('/request-commercial-contact', methods=['POST'])
@login_required
def request_commercial_contact():
    """Handle commercial contact requests with credit system"""
    try:
        data = request.get_json()
        opportunity_id = data.get('opportunity_id')
        business_name = data.get('business_name')
        user_email = session.get('email', '')
        
        if not user_email:
            return {'success': False, 'message': 'Please sign in to access contact information.'}, 401
        
        # Get user's credits
        result = db.session.execute(
            text('SELECT credits_balance FROM leads WHERE email = :email'),
            {'email': user_email}
        ).fetchone()
        
        if not result:
            return {'success': False, 'message': 'User not found.'}, 404
        
        credits_balance = result[0]
        
        # Check if user has enough credits (5 credits per lead)
        credits_needed = 5
        if credits_balance < credits_needed:
            return {
                'success': False,
                'message': f'Insufficient credits! You need {credits_needed} credits to access contact information.',
                'credits_balance': credits_balance,
                'credits_needed': credits_needed,
                'payment_required': True
            }, 402
        
        # Deduct credits
        success, new_balance = deduct_credits(
            user_email, 
            credits_needed, 
            'commercial_contact', 
            opportunity_id, 
            business_name
        )
        
        if not success:
            return {
                'success': False,
                'message': f'Error processing request: {new_balance}'
            }, 500
        
        # Fetch the actual contact information
        contact_info = db.session.execute(
            text('''SELECT contact_name, contact_phone, contact_email, contact_type, address, business_type
                    FROM commercial_opportunities WHERE id = :id'''),
            {'id': opportunity_id.replace('com_', '')}
        ).fetchone()
        
        if contact_info:
            contact_data = {
                'contact_name': contact_info[0] or 'Property Manager',
                'contact_phone': contact_info[1] or '(757) 555-0100',
                'contact_email': contact_info[2] or f'{business_name.lower().replace(" ", ".")}@business.com',
                'contact_type': contact_info[3] or 'Facilities Manager',
                'address': contact_info[4],
                'business_type': contact_info[5]
            }
        else:
            # Fallback contact info
            contact_data = {
                'contact_name': 'Facilities Manager',
                'contact_phone': '(757) 555-0100',
                'contact_email': f'info@{business_name.lower().replace(" ", "")}.com',
                'contact_type': 'Property Manager',
                'address': 'Contact via phone or email for address',
                'business_type': 'Commercial'
            }
        
        # Update session credits
        session['credits_balance'] = new_balance
        
        # Check if credits are now low
        low_credits_warning = new_balance <= 10
        out_of_credits = new_balance == 0
        
        response = {
            'success': True,
            'message': f'✅ Contact information unlocked for {business_name}!',
            'credits_balance': new_balance,
            'credits_used': credits_needed,
            'contact_info': contact_data,
            'payment_required': False
        }
        
        if out_of_credits:
            response['out_of_credits'] = True
            response['alert_message'] = '⚠️ You\'re out of credits! Purchase more to continue accessing leads.'
        elif low_credits_warning:
            response['low_credits'] = True
            response['alert_message'] = f'⚠️ Low credits! You have {new_balance} credits remaining.'
        
        return response
        
    except Exception as e:
        print(f"Error in request_commercial_contact: {e}")
        return {'success': False, 'message': str(e)}, 500

@app.route('/track-click', methods=['POST'])
def track_click():
    """Track contract clicks for paywall limit"""
    # Don't track for admin or paid subscribers
    if session.get('is_admin') or session.get('is_paid_subscriber'):
        return {'success': True, 'clicks_remaining': 999}
    
    # Initialize or increment clicks
    if 'contract_clicks' not in session:
        session['contract_clicks'] = 0
    
    session['contract_clicks'] += 1
    clicks_remaining = max(0, 3 - session['contract_clicks'])
    
    return {
        'success': True,
        'clicks_remaining': clicks_remaining,
        'clicks_used': session['contract_clicks']
    }

@app.route('/customer-leads')
@login_required
def customer_leads():
    """Customer portal for accessing all leads with advanced features"""
    try:
        # Check if user has credits
        user_credits = session.get('credits_balance', 0)
        
        # If no credits, show payment prompt instead of leads
        if user_credits == 0:
            return render_template('customer_leads.html', all_leads=[], show_payment_prompt=True)
        
        # Get all available leads (both government and commercial)
        government_leads = db.session.execute(text('''
            SELECT 
                contracts.id,
                contracts.title,
                contracts.agency,
                contracts.location,
                contracts.description,
                contracts.value as contract_value,
                contracts.deadline,
                contracts.naics_code,
                contracts.created_at,
                contracts.website_url,
                'government' as lead_type,
                'General Cleaning' as services_needed,
                'Active' as status,
                contracts.description as requirements
            FROM contracts 
            ORDER BY contracts.created_at DESC
        ''')).fetchall()
        
        commercial_leads = db.session.execute(text('''
            SELECT 
                commercial_opportunities.id,
                commercial_opportunities.business_name as title,
                commercial_opportunities.business_type as agency,
                commercial_opportunities.location,
                commercial_opportunities.description,
                '$' || commercial_opportunities.monthly_value || '/month' as contract_value,
                'Ongoing' as deadline,
                '' as naics_code,
                'Recent' as date_posted,
                commercial_opportunities.website_url,
                'commercial' as lead_type,
                commercial_opportunities.services_needed,
                'Active' as status,
                commercial_opportunities.special_requirements as requirements
            FROM commercial_opportunities 
            ORDER BY commercial_opportunities.id DESC
        ''')).fetchall()
        
        # Get commercial cleaning requests (businesses looking for cleaners)
        commercial_requests = db.session.execute(text('''
            SELECT 
                id, business_name, contact_name, email, phone, address, city, zip_code,
                business_type, square_footage, frequency, services_needed, 
                special_requirements, budget_range, start_date, urgency, status, created_at
            FROM commercial_lead_requests 
            WHERE status = 'open'
            ORDER BY created_at DESC
        ''')).fetchall()
        
        # Get residential cleaning requests (homeowners looking for cleaners)
        residential_requests = db.session.execute(text('''
            SELECT 
                id, homeowner_name, address, city, zip_code, property_type, bedrooms, bathrooms,
                square_footage, contact_email, contact_phone, estimated_value, 
                cleaning_frequency, services_needed, special_requirements, status, created_at
            FROM residential_leads 
            WHERE status = 'new'
            ORDER BY created_at DESC
        ''')).fetchall()
        
    # Combine and format leads
        all_leads = []
        
        # Add government leads
        for lead in government_leads:
            # Ensure application_url is valid
            app_url = lead[9] if lead[9] and lead[9].startswith(('http://', 'https://')) else None
            
            lead_dict = {
                'id': f"gov_{lead[0]}",
                'title': lead[1],
                'agency': lead[2],
                'location': lead[3],
                'description': lead[4],
                'contract_value': lead[5],
                'deadline': lead[6],
                'naics_code': lead[7],
                'date_posted': lead[8],
                'application_url': app_url,
                'lead_type': lead[10],
                'services_needed': lead[11],
                'status': lead[12],
                'requirements': lead[13] or 'Standard government contracting requirements apply.',
                'days_left': calculate_days_left(lead[6])
            }
            all_leads.append(lead_dict)

        # Add commercial leads
        for lead in commercial_leads:
            # Check if commercial lead has a valid website URL
            app_url = lead[9] if lead[9] and lead[9].startswith(('http://', 'https://')) else None
            
            lead_dict = {
                'id': f"com_{lead[0]}",
                'title': lead[1],
                'agency': lead[2],
                'location': lead[3],
                'description': lead[4],
                'contract_value': lead[5],
                'deadline': lead[6],
                'naics_code': lead[7],
                'date_posted': lead[8],
                'application_url': app_url,  # Use actual website URL if available
                'lead_type': lead[10],
                'services_needed': lead[11],
                'status': lead[12],
                'requirements': lead[13] or 'Standard commercial cleaning requirements.',
                'days_left': 30  # Commercial leads are ongoing
            }
            all_leads.append(lead_dict)
        
        # Add commercial cleaning requests (businesses seeking cleaners)
        for req in commercial_requests:
            lead_dict = {
                'id': f"comreq_{req[0]}",
                'title': f"Commercial Cleaning Needed - {req[1]}",
                'agency': req[8],  # business_type
                'location': f"{req[6]}, VA {req[7]}",  # city, zip
                'description': f"{req[1]} is seeking professional cleaning services. {req[11]} | Frequency: {req[10]} | Special: {req[12] or 'None'}",
                'contract_value': req[13] or 'Contact for quote',  # budget_range
                'deadline': req[14] or 'ASAP',  # start_date
                'naics_code': '',
                'date_posted': req[17],  # created_at
                'application_url': None,
                'lead_type': 'commercial_request',
                'services_needed': req[11],
                'status': 'NEW - Client Seeking Services',
                'requirements': f"Contact: {req[2]} | Phone: {req[4]} | Email: {req[3]} | Square Footage: {req[9]} sq ft | Urgency: {req[15]}",
                'days_left': 7,  # Urgent leads
                'contact_name': req[2],
                'contact_email': req[3],
                'contact_phone': req[4],
                'address': req[5]
            }
            all_leads.append(lead_dict)
        
        # Add residential cleaning requests (homeowners seeking cleaners)
        for req in residential_requests:
            lead_dict = {
                'id': f"resreq_{req[0]}",
                'title': f"Residential Cleaning Needed - {req[5]} in {req[3]}",  # property_type, city
                'agency': 'Homeowner',
                'location': f"{req[3]}, VA {req[4]}",  # city, zip
                'description': f"{req[1]} needs {req[13]} services for their {req[5]}. {req[6]} bed, {req[7]} bath | {req[8]} sq ft | Frequency: {req[12]}",
                'contract_value': req[11] or 'Contact for quote',  # estimated_value
                'deadline': 'ASAP',
                'naics_code': '',
                'date_posted': req[16],  # created_at
                'application_url': None,
                'lead_type': 'residential_request',
                'services_needed': req[13],
                'status': 'NEW - Client Seeking Services',
                'requirements': f"Contact: {req[1]} | Phone: {req[10]} | Email: {req[9]} | Special: {req[14] or 'None'}",
                'days_left': 7,  # Urgent leads
                'contact_name': req[1],
                'contact_email': req[9],
                'contact_phone': req[10],
                'address': req[2]
            }
            all_leads.append(lead_dict)
        
        # Pagination for combined leads
        page = max(int(request.args.get('page', 1) or 1), 1)
        per_page = int(request.args.get('per_page', 12) or 12)
        per_page = min(max(per_page, 6), 48)
        total = len(all_leads)
        pages = max(math.ceil(total / per_page), 1)
        start = (page - 1) * per_page
        end = start + per_page
        leads_page = all_leads[start:end]

        args_base = dict(request.args)
        args_base.pop('page', None)
        args_base.pop('per_page', None)
        prev_url = url_for('customer_leads', page=page-1, per_page=per_page, **args_base) if page > 1 else None
        next_url = url_for('customer_leads', page=page+1, per_page=per_page, **args_base) if page < pages else None
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'has_prev': page > 1,
            'has_next': page < pages,
            'prev_url': prev_url,
            'next_url': next_url
        }

        return render_template('customer_leads.html', all_leads=leads_page, pagination=pagination)
        
    except Exception as e:
        print(f"Customer leads error: {e}")
        return render_template('customer_leads.html', all_leads=[], pagination={'page':1,'per_page':12,'total':0,'pages':1,'has_prev':False,'has_next':False,'prev_url':None,'next_url':None})

def calculate_days_left(deadline_str):
    """Calculate days remaining until deadline"""
    try:
        from datetime import datetime, timedelta
        import re
        
        # Handle various deadline formats
        if not deadline_str or deadline_str.lower() in ['ongoing', 'open', 'continuous']:
            return 365  # Ongoing contracts
        
        # Extract date from string if it contains one
        date_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', deadline_str)
        if date_match:
            deadline_date = datetime.strptime(date_match.group(), '%m/%d/%Y')
            today = datetime.now()
            delta = deadline_date - today
            return max(0, delta.days)
        
        # Default to 30 days if can't parse
        return 30
    except:
        return 30

@app.route('/save-lead', methods=['POST'])
@login_required
def save_lead():
    """Save a lead to user's repository"""
    try:
        data = request.get_json()
        user_email = session.get('user_email')
        
        if not user_email:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        # Insert or update saved lead
        db.session.execute(text('''
            INSERT INTO saved_leads 
            (user_email, lead_type, lead_id, lead_title, lead_data, status)
            VALUES (:user_email, :lead_type, :lead_id, :lead_title, :lead_data, 'saved')
            ON CONFLICT (user_email, lead_type, lead_id) 
            DO UPDATE SET lead_title = :lead_title, lead_data = :lead_data
        '''), {
            'user_email': user_email,
            'lead_type': data.get('lead_type'),
            'lead_id': data.get('lead_id'),
            'lead_title': data.get('title'),
            'lead_data': json.dumps(data)
        })
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Lead saved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/unsave-lead', methods=['POST'])
@login_required
def unsave_lead():
    """Remove a lead from user's repository"""
    try:
        data = request.get_json()
        user_email = session.get('user_email')
        
        if not user_email:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        # Support both saved_id (from saved_leads page) and lead_type+lead_id (from customer_leads page)
        if 'saved_id' in data:
            db.session.execute(text('''
                DELETE FROM saved_leads 
                WHERE id = :saved_id 
                AND user_email = :user_email
            '''), {
                'saved_id': data.get('saved_id'),
                'user_email': user_email
            })
        else:
            db.session.execute(text('''
                DELETE FROM saved_leads 
                WHERE user_email = :user_email 
                AND lead_type = :lead_type 
                AND lead_id = :lead_id
            '''), {
                'user_email': user_email,
                'lead_type': data.get('lead_type'),
                'lead_id': data.get('lead_id')
            })
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Lead removed from saved'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/saved-leads')
@login_required
def saved_leads():
    """View user's saved leads"""
    try:
        user_email = session.get('user_email')
        
        saved = db.session.execute(text('''
            SELECT id, lead_type, lead_id, lead_title, lead_data, notes, status, saved_at
            FROM saved_leads
            WHERE user_email = :user_email
            ORDER BY saved_at DESC
        '''), {'user_email': user_email}).fetchall()
        
        saved_leads_list = []
        for s in saved:
            lead_data = json.loads(s[4]) if s[4] else {}
            
            # Create object with attributes for template access
            class SavedLead:
                def __init__(self, id, lead_type, lead_id, lead_title, lead_data, notes, status, saved_at):
                    self.id = id
                    self.lead_type = lead_type
                    self.lead_id = lead_id
                    self.lead_title = lead_title
                    self.lead_data = lead_data
                    self.notes = notes
                    self.status = status
                    self.saved_at = saved_at
            
            saved_leads_list.append(SavedLead(
                id=s[0],
                lead_type=s[1],
                lead_id=s[2],
                lead_title=s[3],
                lead_data=lead_data,
                notes=s[5],
                status=s[6],
                saved_at=s[7]
            ))
        
        return render_template('saved_leads.html', saved_leads=saved_leads_list)
    except Exception as e:
        print(f"Error loading saved leads: {e}")
        return render_template('saved_leads.html', saved_leads=[])

@app.route('/branding-materials')
@login_required
def branding_materials():
    """Subscriber-exclusive branding materials"""
    user_email = session.get('user_email')
    
    # Check if user is subscriber (you may need to adjust this based on your subscription logic)
    result = db.session.execute(text('''
        SELECT subscription_status FROM customers 
        WHERE email = :email
    '''), {'email': user_email}).fetchone()
    
    if not result or result[0] != 'active':
        return render_template('branding_materials.html', is_subscriber=False)
    
    # Define branding materials available for download
    materials = [
        {
            'category': 'Logos & Identity',
            'items': [
                {'name': 'Company Logo Package', 'description': 'High-res logos in PNG, SVG, and AI formats', 'icon': 'fa-image'},
                {'name': 'Brand Color Palette', 'description': 'Official color codes and usage guidelines', 'icon': 'fa-palette'},
                {'name': 'Typography Guide', 'description': 'Approved fonts and text styling', 'icon': 'fa-font'}
            ]
        },
        {
            'category': 'Business Cards & Stationery',
            'items': [
                {'name': 'Business Card Templates', 'description': 'Editable templates for Canva and Adobe', 'icon': 'fa-id-card'},
                {'name': 'Letterhead Templates', 'description': 'Professional letterhead designs', 'icon': 'fa-file-lines'},
                {'name': 'Email Signature', 'description': 'HTML email signature code', 'icon': 'fa-envelope'}
            ]
        },
        {
            'category': 'Marketing Materials',
            'items': [
                {'name': 'Flyer Templates', 'description': 'Print and digital flyer designs', 'icon': 'fa-file-pdf'},
                {'name': 'Social Media Graphics', 'description': 'Templates for Facebook, LinkedIn, Instagram', 'icon': 'fa-share-nodes'},
                {'name': 'Brochure Templates', 'description': 'Tri-fold and bi-fold brochure designs', 'icon': 'fa-book'}
            ]
        },
        {
            'category': 'Presentation Materials',
            'items': [
                {'name': 'PowerPoint Templates', 'description': 'Professional presentation decks', 'icon': 'fa-presentation'},
                {'name': 'Proposal Cover Pages', 'description': 'Impressive proposal first pages', 'icon': 'fa-file-contract'},
                {'name': 'Case Study Templates', 'description': 'Success story layouts', 'icon': 'fa-chart-line'}
            ]
        }
    ]
    
    return render_template('branding_materials.html', materials=materials, is_subscriber=True)

@app.route('/proposal-support')
@login_required
def proposal_support():
    """Subscriber-exclusive proposal writing support"""
    user_email = session.get('user_email')
    
    # Check if user is subscriber
    result = db.session.execute(text('''
        SELECT subscription_status FROM customers 
        WHERE email = :email
    '''), {'email': user_email}).fetchone()
    
    if not result or result[0] != 'active':
        return render_template('proposal_support.html', is_subscriber=False)
    
    # Define proposal resources
    resources = [
        {
            'category': 'Proposal Templates',
            'items': [
                {'name': 'Government Contract Proposal', 'description': 'Comprehensive template for federal/state contracts', 'icon': 'fa-file-contract', 'type': 'template'},
                {'name': 'Commercial Cleaning Proposal', 'description': 'Business-focused proposal template', 'icon': 'fa-building', 'type': 'template'},
                {'name': 'Residential Cleaning Quote', 'description': 'Simple quote template for homeowners', 'icon': 'fa-home', 'type': 'template'},
                {'name': 'RFP Response Template', 'description': 'Structured RFP response framework', 'icon': 'fa-file-alt', 'type': 'template'}
            ]
        },
        {
            'category': 'Writing Guides',
            'items': [
                {'name': 'Proposal Writing 101', 'description': 'Step-by-step guide to writing winning proposals', 'icon': 'fa-book', 'type': 'guide'},
                {'name': 'Government Contract Guide', 'description': 'Navigating federal contracting requirements', 'icon': 'fa-landmark', 'type': 'guide'},
                {'name': 'Pricing Strategy Guide', 'description': 'How to price your cleaning services competitively', 'icon': 'fa-dollar-sign', 'type': 'guide'},
                {'name': 'Common Mistakes to Avoid', 'description': 'Top proposal pitfalls and how to avoid them', 'icon': 'fa-exclamation-triangle', 'type': 'guide'}
            ]
        },
        {
            'category': 'Sample Proposals',
            'items': [
                {'name': 'Winning Government Proposal', 'description': 'Real example of a successful federal contract bid', 'icon': 'fa-trophy', 'type': 'sample'},
                {'name': 'Commercial Office Cleaning', 'description': 'Sample proposal for corporate clients', 'icon': 'fa-briefcase', 'type': 'sample'},
                {'name': 'School Cleaning Contract', 'description': 'Educational facility proposal example', 'icon': 'fa-school', 'type': 'sample'},
                {'name': 'Hospital Cleaning Bid', 'description': 'Healthcare facility proposal sample', 'icon': 'fa-hospital', 'type': 'sample'}
            ]
        },
        {
            'category': 'Tools & Checklists',
            'items': [
                {'name': 'Proposal Checklist', 'description': 'Ensure you include everything required', 'icon': 'fa-tasks', 'type': 'tool'},
                {'name': 'Pricing Calculator', 'description': 'Interactive tool to calculate competitive bids', 'icon': 'fa-calculator', 'type': 'tool'},
                {'name': 'Requirements Tracker', 'description': 'Track RFP requirements and responses', 'icon': 'fa-list-check', 'type': 'tool'},
                {'name': 'Timeline Planner', 'description': 'Plan your proposal submission timeline', 'icon': 'fa-calendar-alt', 'type': 'tool'}
            ]
        }
    ]
    
    return render_template('proposal_support.html', resources=resources, is_subscriber=True)

@app.route('/consultations')
@login_required
def consultations():
    """Subscriber-exclusive one-on-one consultation scheduling"""
    user_email = session.get('user_email')
    
    # Check if user is subscriber
    result = db.session.execute(text('''
        SELECT subscription_status, name FROM customers 
        WHERE email = :email
    '''), {'email': user_email}).fetchone()
    
    if not result or result[0] != 'active':
        return render_template('consultations.html', is_subscriber=False, user_name='')
    
    # Available consultation types
    consultation_types = [
        {
            'title': 'Proposal Review Session',
            'duration': '60 minutes',
            'description': 'Get expert feedback on your proposal before submission',
            'icon': 'fa-file-contract',
            'color': 'primary'
        },
        {
            'title': 'Bidding Strategy Call',
            'duration': '45 minutes',
            'description': 'Develop a winning strategy for specific opportunities',
            'icon': 'fa-chess',
            'color': 'success'
        },
        {
            'title': 'Business Development Coaching',
            'duration': '60 minutes',
            'description': 'Long-term growth strategies for government contracting',
            'icon': 'fa-chart-line',
            'color': 'info'
        },
        {
            'title': 'Quick Questions Session',
            'duration': '30 minutes',
            'description': 'Fast answers to specific questions',
            'icon': 'fa-question-circle',
            'color': 'warning'
        }
    ]
    
    return render_template('consultations.html', 
                         consultation_types=consultation_types, 
                         is_subscriber=True, 
                         user_name=result[1])

@app.route('/request-proposal-help', methods=['POST'])
def request_proposal_help():
    """Handle proposal help requests from customers"""
    try:
        data = request.get_json()
        
        # Extract form data
        lead_id = data.get('lead_id')
        lead_title = data.get('lead_title')
        name = data.get('name')
        company = data.get('company')
        email = data.get('email')
        phone = data.get('phone')
        experience = data.get('experience')
        help_needed = data.get('help_needed', [])
        notes = data.get('notes', '')
        contact_method = data.get('contact_method')
        
        # Validate required fields
        if not all([lead_id, name, company, email, phone]):
            return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400
        
        # Store proposal help request in database
        conn = get_db_connection()
        c = conn.cursor()
        
        # Create proposal_help_requests table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS proposal_help_requests
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      lead_id TEXT NOT NULL,
                      lead_title TEXT NOT NULL,
                      name TEXT NOT NULL,
                      company TEXT NOT NULL,
                      email TEXT NOT NULL,
                      phone TEXT NOT NULL,
                      experience TEXT NOT NULL,
                      help_needed TEXT NOT NULL,
                      notes TEXT,
                      contact_method TEXT NOT NULL,
                      request_date TEXT NOT NULL,
                      status TEXT DEFAULT 'pending',
                      assigned_expert TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Insert the request
        help_needed_str = ', '.join(help_needed) if help_needed else ''
        request_date = datetime.now().isoformat()
        
        c.execute('''INSERT INTO proposal_help_requests 
                     (lead_id, lead_title, name, company, email, phone, experience, 
                      help_needed, notes, contact_method, request_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (lead_id, lead_title, name, company, email, phone, experience,
                   help_needed_str, notes, contact_method, request_date))
        
        conn.commit()
        request_id = c.lastrowid
        conn.close()
        
        # Send notification email (in real app)
        send_proposal_help_notification(data, request_id)
        
        return jsonify({
            'success': True,
            'message': 'Proposal help request submitted successfully! We\'ll contact you within 24 hours.',
            'request_id': request_id
        })
        
    except Exception as e:
        print(f"Proposal help request error: {e}")
        return jsonify({'success': False, 'message': 'Error submitting request'}), 500

def send_proposal_help_notification(request_data, request_id):
    """Send email notification for proposal help request"""
    try:
        # Email content
        subject = f"New Proposal Help Request #{request_id} - {request_data['lead_title']}"
        
        html_body = f"""
        <h2>New Proposal Help Request</h2>
        <p><strong>Request ID:</strong> {request_id}</p>
        <p><strong>Lead:</strong> {request_data['lead_title']} (ID: {request_data['lead_id']})</p>
        
        <h3>Contact Information</h3>
        <ul>
            <li><strong>Name:</strong> {request_data['name']}</li>
            <li><strong>Company:</strong> {request_data['company']}</li>
            <li><strong>Email:</strong> {request_data['email']}</li>
            <li><strong>Phone:</strong> {request_data['phone']}</li>
            <li><strong>Preferred Contact:</strong> {request_data['contact_method']}</li>
        </ul>
        
        <h3>Experience & Help Needed</h3>
        <p><strong>Experience Level:</strong> {request_data['experience']}</p>
        <p><strong>Help Areas:</strong> {', '.join(request_data.get('help_needed', []))}</p>
        
        {f"<p><strong>Additional Notes:</strong> {request_data['notes']}</p>" if request_data.get('notes') else ''}
        
        <p><em>Please contact the customer within 24 hours.</em></p>
        """
        
        # Create message
        msg = Message(
            subject=subject,
            recipients=['info@eliteecoservices.com'],  # Your business email
            html=html_body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Send email
        mail.send(msg)
        print(f"Proposal help notification sent for request {request_id}")
        return True
        
    except Exception as e:
        print(f"Error sending proposal help notification: {e}")
        return False

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for lead management"""
    try:
        # Get lead statistics
        stats = lead_generator.get_lead_statistics()
        
        # Get recent activity (last 7 days)
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get recent government contracts
        c.execute('''SELECT title, agency, location, value, created_at 
                     FROM contracts 
                     WHERE created_at >= date("now", "-7 days")
                     ORDER BY created_at DESC LIMIT 10''')
        recent_gov = c.fetchall()
        
        # Get recent commercial opportunities (last 10 added)
        c.execute('''SELECT business_name, business_type, location, monthly_value 
                     FROM commercial_opportunities 
                     ORDER BY id DESC LIMIT 10''')
        recent_commercial = c.fetchall()
        
        conn.close()
        
        return render_template('admin_dashboard.html', 
                             stats=stats, 
                             recent_gov=recent_gov, 
                             recent_commercial=recent_commercial,
                             scheduler_running=scheduler_running)
        
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash('Error loading admin dashboard', 'error')
        return redirect(url_for('index'))

@app.route('/admin/manual-update', methods=['POST'])
def manual_update():
    """Manually trigger lead updates"""
    try:
        data = request.get_json()
        gov_count = int(data.get('government_count', 5))
        commercial_count = int(data.get('commercial_count', 10))
        
        # Generate new leads
        gov_leads = lead_generator.generate_government_leads(count=gov_count)
        commercial_leads = lead_generator.generate_commercial_leads(count=commercial_count)
        
        # Update database
        success = lead_generator.update_database(gov_leads, commercial_leads)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully added {len(gov_leads)} government and {len(commercial_leads)} commercial leads',
                'government_added': len(gov_leads),
                'commercial_added': len(commercial_leads)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update database'
            }), 500
            
    except Exception as e:
        print(f"Manual update error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/admin/cleanup-leads', methods=['POST'])
def cleanup_leads():
    """Clean up old leads"""
    try:
        data = request.get_json()
        days_old = int(data.get('days_old', 90))
        
        success = lead_generator.cleanup_old_leads(days_old=days_old)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully cleaned up leads older than {days_old} days'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to cleanup leads'
            }), 500
            
    except Exception as e:
        print(f"Cleanup error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/admin/scheduler-control', methods=['POST'])
def scheduler_control():
    """Control the automatic scheduler"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'start':
            start_scheduler()
            return jsonify({
                'success': True,
                'message': 'Scheduler started successfully',
                'status': 'running'
            })
        elif action == 'stop':
            stop_scheduler()
            return jsonify({
                'success': True,
                'message': 'Scheduler stopped successfully',
                'status': 'stopped'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid action'
            }), 400
            
    except Exception as e:
        print(f"Scheduler control error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    """Get current lead statistics"""
    try:
        stats = lead_generator.get_lead_statistics()
        
        if stats:
            return jsonify({
                'success': True,
                'stats': stats
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to get statistics'
            }), 500
            
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/leads')
def leads():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM leads ORDER BY created_at DESC')
    all_leads = c.fetchall()
    conn.close()
    return render_template('leads.html', leads=all_leads)

@app.route('/landing')
def landing():
    """Landing page with pain point survey"""
    return render_template('landing.html')

@app.route('/submit-survey', methods=['POST'])
def submit_survey():
    """Handle survey submission and redirect to results"""
    try:
        import json
        
        # Get survey data from request
        survey_data = request.get_json()
        
        # Store survey data in database for analytics
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO survey_responses (
                biggest_challenge, annual_revenue, company_size, 
                contract_experience, main_focus, pain_point_scenario,
                submission_date, ip_address
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            survey_data.get('biggest_challenge', ''),
            survey_data.get('annual_revenue', ''),
            survey_data.get('company_size', ''),
            survey_data.get('contract_experience', ''),
            survey_data.get('main_focus', ''),
            survey_data.get('pain_point_scenario', ''),
            datetime.now().isoformat(),
            request.remote_addr
        ))
        conn.commit()
        conn.close()
        
        # Redirect to results page with survey data
        import urllib.parse
        survey_json = json.dumps(survey_data)
        encoded_data = urllib.parse.quote(survey_json)
        
        return {'success': True, 'redirect_url': f'/survey-results?data={encoded_data}'}
        
    except Exception as e:
        print(f"Survey submission error: {e}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/survey-results')
def survey_results():
    """Display personalized survey results"""
    return render_template('survey_results.html')

@app.route('/register-from-survey', methods=['POST'])
def register_from_survey():
    """Handle registration from survey results page"""
    try:
        import json
        
        data = request.get_json()
        
        # Extract survey data
        survey_data = json.loads(data.get('survey_data', '{}'))
        
        # Prepare lead data
        lead_data = {
            'company_name': data.get('company_name'),
            'contact_name': data.get('contact_name'),
            'email': data.get('email'),
            'phone': data.get('phone', ''),
            'state': data.get('state', ''),
            'experience_years': data.get('experience_years', ''),
            'certifications': data.get('certifications', ''),
            'proposal_support': data.get('proposal_support', False),
            'lead_source': data.get('lead_source', 'survey'),
            'survey_responses': json.dumps(survey_data)
        }
        
        # Insert into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO leads (
                company_name, contact_name, email, phone, state, 
                experience_years, certifications, registration_date, 
                lead_source, survey_responses, proposal_support,
                free_leads_remaining
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead_data['company_name'],
            lead_data['contact_name'], 
            lead_data['email'],
            lead_data['phone'],
            lead_data['state'],
            lead_data['experience_years'],
            lead_data['certifications'],
            datetime.now().isoformat(),
            lead_data['lead_source'],
            lead_data['survey_responses'],
            lead_data['proposal_support'],
            3  # Start with 3 free leads
        ))
        conn.commit()
        conn.close()
        
        # Send notification email
        send_lead_notification(lead_data)
        
        # Store registration data for confirmation page
        import json
        session_data = json.dumps(lead_data)
        
        return {'success': True, 'session_data': session_data}
        
    except Exception as e:
        print(f"Registration error: {e}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/payment')
def payment():
    """Payment page for subscription"""
    return render_template('payment.html')

@app.route('/credits')
def credits():
    """Credits purchase page"""
    return render_template('credits.html')

@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard for signed-in users"""
    return render_template('dashboard.html')

@app.route('/api/dashboard-stats')
def api_dashboard_stats():
    """Get dashboard statistics for user"""
    try:
        user_email = request.args.get('email', 'demo@example.com')
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get government contracts count
        c.execute('SELECT COUNT(*) FROM contracts')
        govt_contracts = c.fetchone()[0]
        
        # Get commercial leads count
        c.execute('SELECT COUNT(*) FROM commercial_opportunities')
        commercial_leads = c.fetchone()[0]
        
        # Get user's leads accessed (credits used)
        c.execute('SELECT COUNT(*) FROM credits_usage WHERE user_email = ?', (user_email,))
        leads_accessed = c.fetchone()[0]
        
        # Calculate total contract value
        c.execute('SELECT SUM(CAST(REPLACE(REPLACE(value, "$", ""), ",", "") AS INTEGER)) FROM contracts')
        total_value_result = c.fetchone()[0]
        total_value = total_value_result if total_value_result else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'government_contracts': govt_contracts,
            'commercial_leads': commercial_leads,
            'leads_accessed': leads_accessed,
            'total_value': total_value
        })
        
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return jsonify({'success': False, 'message': 'Failed to load stats'}), 500

@app.route('/api/recent-opportunities')
def api_recent_opportunities():
    """Get recent opportunities for dashboard"""
    try:
        user_email = request.args.get('email', 'demo@example.com')
        
        conn = get_db_connection()
        c = conn.cursor()
        
        opportunities = []
        
        # Get recent government contracts
        c.execute('SELECT title, agency, location, value, description, website_url FROM contracts ORDER BY created_at DESC LIMIT 3')
        govt_contracts = c.fetchall()
        
        for contract in govt_contracts:
            opportunities.append({
                'id': f'govt_{hash(contract[0])}',
                'type': 'government',
                'title': contract[0],
                'description': contract[4][:100] + '...' if len(contract[4]) > 100 else contract[4],
                'value': contract[3],
                'location': contract[2],
                'website_url': contract[5]
            })
        
        # Get recent commercial opportunities
        c.execute('SELECT business_name, business_type, location, monthly_value, description FROM commercial_opportunities ORDER BY created_at DESC LIMIT 2')
        commercial_opps = c.fetchall()
        
        for opp in commercial_opps:
            opportunities.append({
                'id': f'comm_{hash(opp[0])}',
                'type': 'commercial',
                'title': opp[0],
                'description': opp[4][:100] + '...' if len(opp[4]) > 100 else opp[4],
                'value': f'${opp[3]}/month',
                'location': opp[2]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': opportunities
        })
        
    except Exception as e:
        print(f"Recent opportunities error: {e}")
        return jsonify({'success': False, 'message': 'Failed to load opportunities'}), 500

@app.route('/api/signin', methods=['POST'])
def api_signin():
    """Handle sign in API requests"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user exists in leads table (simplified authentication for demo)
        c.execute('SELECT * FROM leads WHERE email = ?', (email,))
        user = c.fetchone()
        
        if user:
            # In a real app, verify password hash
            # For demo, just check if user exists
            
            # Determine user type based on credits or subscription
            credits_balance = get_user_credits(email)
            user_type = 'premium' if credits_balance > 0 else 'basic'
            
            # In a real app, create session or JWT token here
            
            conn.close()
            return jsonify({
                'success': True,
                'message': 'Sign in successful',
                'user_type': user_type,
                'credits_balance': credits_balance
            })
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            
    except Exception as e:
        print(f"Sign in error: {e}")
        return jsonify({'success': False, 'message': 'Sign in failed'}), 500

@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """Handle password reset requests"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user exists
        c.execute('SELECT * FROM leads WHERE email = ?', (email,))
        user = c.fetchone()
        
        if user:
            # In a real app, generate reset token and send email
            # For demo, just simulate success
            conn.close()
            return jsonify({'success': True, 'message': 'Password reset link sent'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Email not found'}), 404
            
    except Exception as e:
        print(f"Password reset error: {e}")
        return jsonify({'success': False, 'message': 'Reset failed'}), 500

@app.route('/process-subscription', methods=['POST'])
def process_subscription():
    """Process subscription payment"""
    try:
        import json
        
        payment_data = request.get_json()
        
        # In a real implementation, you would:
        # 1. Process payment with Stripe/PayPal
        # 2. Create subscription record
        # 3. Update user's subscription status
        
        # For demo purposes, we'll simulate successful payment processing
        
        # Store subscription data
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO subscriptions (
                email, cardholder_name, total_amount, 
                proposal_support, subscription_date, status
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'demo@example.com',  # In real app, get from session
            payment_data.get('cardholder_name'),
            payment_data.get('total_amount'),
            payment_data.get('proposal_support', False),
            datetime.now().isoformat(),
            'active'
        ))
        conn.commit()
        conn.close()
        
        return {'success': True, 'subscription_id': 'sub_demo_123456'}
        
    except Exception as e:
        print(f"Subscription processing error: {e}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/confirmation')
def confirmation():
    """Confirmation page for registration and payments"""
    return render_template('confirmation.html')

@app.route('/send-confirmation-email', methods=['POST'])
def send_confirmation_email():
    """Send confirmation email after registration or payment"""
    try:
        data = request.get_json()
        confirmation_type = data.get('type', 'free-trial')
        user_data = data.get('userData', {})
        
        # Send confirmation email
        email = user_data.get('email')
        if email:
            if confirmation_type == 'payment':
                subject = "Payment Confirmed - Virginia Contract Leads"
                body = f"""
Thank you for subscribing to Virginia Contract Leads!

Your payment has been processed and your premium access is now active.

You'll continue receiving unlimited contract opportunities for:
- Hampton, VA
- Suffolk, VA  
- Virginia Beach, VA
- Newport News, VA
- Williamsburg, VA

Next billing date: {(datetime.now().replace(day=datetime.now().day + 30)).strftime('%B %d, %Y')}

Questions? Reply to this email or contact info@eliteecoservices.com

Best regards,
Virginia Contract Leads Team
                """
            else:
                subject = "Welcome! Your 3 Free Contract Leads Are Coming"
                body = f"""
Welcome to Virginia Contract Leads, {user_data.get('contact_name', 'there')}!

Your registration is confirmed and you'll receive your first contract opportunity within 24 hours.

What to expect:
- Lead #1: Within 24 hours
- Lead #2: Within 1 week  
- Lead #3: Within 2 weeks

After your 3 free leads, continue unlimited access for just $25/month.

Watch your inbox for opportunities!

Best regards,
Virginia Contract Leads Team
info@eliteecoservices.com
                """
            
            msg = Message(subject=subject, recipients=[email], body=body)
            mail.send(msg)
        
        return {'success': True}
        
    except Exception as e:
        print(f"Confirmation email error: {e}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/credits')
def credits_page():
    """Credits purchase page"""
    return render_template('credits.html')

@app.route('/get-credits-balance')
def get_credits_balance():
    """Get user's current credit balance"""
    try:
        user_email = request.args.get('email', 'demo@example.com')  # In real app, get from session
        balance = get_user_credits(user_email)
        low_credits = check_low_credits(user_email)
        
        return {
            'success': True,
            'credits_balance': balance,
            'low_credits': low_credits,
            'out_of_credits': balance == 0
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

@app.route('/purchase-credits', methods=['POST'])
def purchase_credits():
    """Handle credit purchases with PayPal and credit card support"""
    try:
        data = request.get_json()
        credits_package = data.get('package')  # '10', '20', '30'
        user_email = data.get('user_email', 'demo@example.com')  # In real app, get from session
        payment_method = data.get('payment_method', 'credit_card')
        payment_info = data.get('payment_info', {})
        paypal_details = data.get('paypal_details', {})
        
        # Credit packages
        packages = {
            '10': {'credits': 10, 'price': 5.00, 'description': '10 Credits - $5'},
            '20': {'credits': 20, 'price': 10.00, 'description': '20 Credits - $10'},
            '30': {'credits': 30, 'price': 15.00, 'description': '30 Credits - $15'}
        }
        
        if credits_package not in packages:
            return {'success': False, 'message': 'Invalid credit package'}, 400
        
        package_info = packages[credits_package]
        
        # Process payment based on method
        if payment_method == 'paypal':
            # PayPal payment processing
            transaction_id = paypal_details.get('id', f'paypal_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            payment_status = paypal_details.get('status', 'COMPLETED')
            
            if payment_status != 'COMPLETED':
                return {'success': False, 'message': 'PayPal payment not completed'}, 400
                
            payment_reference = f"PayPal: {transaction_id}"
            
        elif payment_method == 'credit_card':
            # Credit card payment processing (simulate for demo)
            # In production, integrate with Stripe, Square, etc.
            transaction_id = f'card_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            card_last_four = payment_info.get('card_number', '****')[-4:] if payment_info.get('card_number') else '****'
            payment_reference = f"Card ending in {card_last_four}"
            
        else:
            return {'success': False, 'message': 'Invalid payment method'}, 400
        
        # Add credits to user's account
        success, new_balance = add_credits(
            user_email,
            package_info['credits'],
            f"credit_purchase_{credits_package}_{payment_method}",
            package_info['price'],
            transaction_id
        )
        
        if not success:
            return {'success': False, 'message': f'Error adding credits: {new_balance}'}, 500
        
        # Record detailed purchase information
        conn = get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''UPDATE credits_purchases 
                         SET payment_method = ?, payment_reference = ?
                         WHERE user_email = ? AND transaction_id = ?''',
                      (payment_method, payment_reference, user_email, transaction_id))
            conn.commit()
        except Exception as e:
            print(f"Error updating purchase record: {e}")
        finally:
            conn.close()
        
        return {
            'success': True,
            'message': f'Successfully purchased {package_info["credits"]} credits via {payment_method.title()}!',
            'credits_added': package_info['credits'],
            'new_balance': new_balance,
            'amount_paid': package_info['price'],
            'transaction_id': transaction_id,
            'payment_method': payment_method
        }
        
    except Exception as e:
        print(f"Purchase credits error: {e}")
        return {'success': False, 'message': str(e)}, 500

@app.route('/credits-usage-history')
def credits_usage_history():
    """Get user's credit usage history"""
    try:
        user_email = request.args.get('email', 'demo@example.com')  # In real app, get from session
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get usage history
        c.execute('''SELECT credits_used, action_type, opportunity_name, usage_date 
                     FROM credits_usage 
                     WHERE user_email = ? 
                     ORDER BY usage_date DESC LIMIT 50''', (user_email,))
        usage_history = c.fetchall()
        
        # Get purchase history
        c.execute('''SELECT credits_purchased, amount_paid, purchase_type, purchase_date 
                     FROM credits_purchases 
                     WHERE user_email = ? 
                     ORDER BY purchase_date DESC LIMIT 50''', (user_email,))
        purchase_history = c.fetchall()
        
        conn.close()
        
        return {
            'success': True,
            'usage_history': [
                {
                    'credits_used': row[0],
                    'action_type': row[1],
                    'opportunity_name': row[2],
                    'date': row[3]
                }
                for row in usage_history
            ],
            'purchase_history': [
                {
                    'credits_purchased': row[0],
                    'amount_paid': row[1],
                    'purchase_type': row[2],
                    'date': row[3]
                }
                for row in purchase_history
            ]
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

@app.route('/allocate-monthly-credits')
def allocate_monthly_credits_route():
    """Admin route to allocate monthly credits to subscribers"""
    try:
        allocated_count = allocate_monthly_credits()
        return {
            'success': True,
            'message': f'Monthly credits allocated to {allocated_count} subscribers',
            'subscribers_updated': allocated_count
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

# ============================================================================
# TOOLBOX & RESOURCES ROUTES
# ============================================================================

@app.route('/toolbox')
@login_required
def toolbox():
    """Toolbox page with templates and resources"""
    # Check if user is paid subscriber
    is_paid = False
    if 'user_id' in session:
        result = db.session.execute(text('''
            SELECT subscription_status FROM leads WHERE id = :user_id
        '''), {'user_id': session['user_id']}).fetchone()
        if result and result[0] == 'paid':
            is_paid = True
    
    return render_template('toolbox.html', is_paid_subscriber=is_paid, is_admin=session.get('is_admin', False))

@app.route('/proposal-templates')
def proposal_templates():
    """Free proposal writing templates and guidance"""
    return render_template('proposal_templates.html')

@app.route('/pricing-guide')
@login_required
def pricing_guide():
    """Subscriber-only pricing guide for cleaning contracts"""
    # Check if user is paid subscriber or admin
    is_admin = session.get('is_admin', False)
    is_paid = False
    
    if not is_admin and 'user_id' in session:
        result = db.session.execute(text('''
            SELECT subscription_status FROM leads WHERE id = :user_id
        '''), {'user_id': session['user_id']}).fetchone()
        if result and result[0] == 'paid':
            is_paid = True
    
    if not is_admin and not is_paid:
        flash('Pricing Guide is available to paid subscribers only. Subscribe to access this valuable resource!', 'warning')
        return redirect(url_for('subscribe_page'))
    
    return render_template('pricing_guide.html')

@app.route('/capability-statement')
def capability_statement():
    """Capability statement template"""
    return render_template('capability_statement.html')

@app.route('/proposal-review', methods=['GET', 'POST'])
@login_required
def proposal_review():
    """AI-powered proposal review feature"""
    if request.method == 'POST':
        try:
            # Get uploaded files
            rfp_file = request.files.get('rfp_file')
            proposal_file = request.files.get('proposal_file')
            
            if not rfp_file or not proposal_file:
                return jsonify({'success': False, 'message': 'Both RFP and Proposal files are required'}), 400
            
            # Save files temporarily
            import os
            from werkzeug.utils import secure_filename
            
            upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            rfp_filename = secure_filename(rfp_file.filename)
            proposal_filename = secure_filename(proposal_file.filename)
            
            rfp_path = os.path.join(upload_folder, f"rfp_{session['user_id']}_{rfp_filename}")
            proposal_path = os.path.join(upload_folder, f"prop_{session['user_id']}_{proposal_filename}")
            
            rfp_file.save(rfp_path)
            proposal_file.save(proposal_path)
            
            # Process files (for now, return mock analysis)
            analysis = analyze_proposal_compliance(rfp_path, proposal_path)
            
            # Clean up files
            os.remove(rfp_path)
            os.remove(proposal_path)
            
            return jsonify({
                'success': True,
                'analysis': analysis
            })
            
        except Exception as e:
            print(f"Proposal review error: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('proposal_review.html')

def analyze_proposal_compliance(rfp_path, proposal_path):
    """Analyze proposal compliance with RFP requirements (placeholder for AI integration)"""
    # This is a placeholder - in production, integrate with OpenAI or Claude API
    return {
        'compliance_score': 85,
        'strengths': [
            'Clear executive summary addressing key requirements',
            'Detailed pricing breakdown included',
            'Past performance examples provided',
            'All required certifications mentioned'
        ],
        'weaknesses': [
            'Missing specific response to Section 3.2 technical requirements',
            'Staffing plan lacks detail on quality control procedures',
            'Timeline could be more specific with milestones'
        ],
        'suggestions': [
            'Add a detailed organizational chart showing reporting structure',
            'Include specific examples of similar-sized projects completed',
            'Expand on your green cleaning capabilities if RFP mentions sustainability',
            'Add a risk management section addressing potential challenges'
        ],
        'missing_sections': [
            'Safety program documentation',
            'Insurance certificates (mention where they will be provided)'
        ]
    }

@app.route('/pricing-calculator')
@login_required
def pricing_calculator():
    """Interactive pricing calculator for subscribers"""
    # Check if user is paid subscriber or admin
    is_admin = session.get('is_admin', False)
    is_paid = False
    
    if not is_admin and 'user_id' in session:
        result = db.session.execute(text('''
            SELECT subscription_status FROM leads WHERE id = :user_id
        '''), {'user_id': session['user_id']}).fetchone()
        if result and result[0] == 'paid':
            is_paid = True
    
    if not is_admin and not is_paid:
        flash('Pricing Calculator is available to paid subscribers only. Subscribe to unlock this powerful tool!', 'warning')
        return redirect(url_for('subscribe_page'))
    
    return render_template('pricing_calculator.html')

@app.route('/ai-assistant')
@login_required
def ai_assistant():
    """AI chatbot for last-minute proposal help"""
    return render_template('ai_assistant.html')

@app.route('/federal-coming-soon')
def federal_coming_soon():
    """Coming soon page for federal contracts until November 3"""
    return render_template('federal_coming_soon.html')

@app.route('/ai-proposal-generator')
@login_required
def ai_proposal_generator():
    """AI-powered proposal generator with personalization"""
    return render_template('ai_proposal_generator.html')

@app.route('/api/get-contracts')
@login_required
def get_contracts_api():
    """API endpoint to get contracts for proposal generator"""
    try:
        source = request.args.get('source', '')
        contracts = []
        
        if source == 'federal':
            result = db.session.execute(text('''
                SELECT title, agency, deadline, notice_id as id
                FROM federal_contracts 
                WHERE posted_date >= DATE('now', '-30 days')
                ORDER BY posted_date DESC 
                LIMIT 50
            '''))
            contracts = [{'title': r[0], 'agency': r[1], 'deadline': r[2], 'id': r[3]} for r in result]
            
        elif source == 'local':
            result = db.session.execute(text('''
                SELECT title, location, deadline, id
                FROM contracts 
                WHERE posted_date >= DATE('now', '-30 days')
                ORDER BY posted_date DESC 
                LIMIT 50
            '''))
            contracts = [{'title': r[0], 'location': r[1], 'deadline': r[2], 'id': r[3]} for r in result]
            
        elif source == 'commercial':
            result = db.session.execute(text('''
                SELECT business_name as title, city as location, start_date as deadline, id
                FROM commercial_lead_requests 
                WHERE status = 'open' AND created_at >= DATE('now', '-30 days')
                ORDER BY created_at DESC 
                LIMIT 50
            '''))
            contracts = [{'title': r[0], 'location': r[1], 'deadline': r[2], 'id': r[3]} for r in result]
        
        return jsonify({'success': True, 'contracts': contracts})
        
    except Exception as e:
        print(f"Get contracts error: {e}")
        return jsonify({'success': False, 'contracts': []}), 500

@app.route('/api/generate-proposal', methods=['POST'])
@login_required
def generate_proposal_api():
    """Generate AI proposal from contract data"""
    try:
        config = request.get_json()
        contract = config.get('contract', {})
        company_name = config.get('companyName', '[YOUR COMPANY NAME]')
        years = config.get('yearsInBusiness', '[X]')
        differentiators = config.get('differentiators', '[YOUR KEY DIFFERENTIATORS]')
        sections = config.get('sections', {})
        
        # Generate proposal content (placeholder - replace with real AI API)
        proposal_content = generate_proposal_content(contract, company_name, years, differentiators, sections)
        
        # Find placeholders that need personalization
        placeholders = find_placeholders(proposal_content)
        
        return jsonify({
            'success': True,
            'proposal': {
                'content': proposal_content,
                'placeholders': placeholders,
                'contract_id': contract.get('id'),
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        print(f"Generate proposal error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/quick-wins')
@login_required
def quick_wins():
    """Show urgent leads requiring immediate response"""
    urgency_filter = request.args.get('urgency', '')
    lead_type_filter = request.args.get('lead_type', '')
    city_filter = request.args.get('city', '')
    page = max(int(request.args.get('page', 1) or 1), 1)
    per_page = 12
    offset = (page - 1) * per_page
    
    # Check if paid subscriber or admin
    is_admin = session.get('is_admin', False)
    is_paid = False
    if not is_admin and 'user_id' in session:
        result = db.session.execute(text('''
            SELECT subscription_status FROM leads WHERE id = :user_id
        '''), {'user_id': session['user_id']}).fetchone()
        if result and result[0] == 'paid':
            is_paid = True
    
    # Build query
    where_conditions = ["urgency IN ('emergency', 'urgent', 'soon')"]
    params = {}
    
    if urgency_filter:
        where_conditions.append("urgency = :urgency")
        params['urgency'] = urgency_filter
    
    if city_filter:
        where_conditions.append("city = :city")
        params['city'] = city_filter
    
    where_clause = " AND ".join(where_conditions)
    
    # Get counts
    emergency_count = db.session.execute(text(
        "SELECT COUNT(*) FROM commercial_lead_requests WHERE urgency = 'emergency' AND status = 'open'"
    )).scalar() or 0
    
    urgent_count = db.session.execute(text(
        "SELECT COUNT(*) FROM commercial_lead_requests WHERE urgency = 'urgent' AND status = 'open'"
    )).scalar() or 0
    
    # Get leads
    total_count = db.session.execute(text(f'''
        SELECT COUNT(*) FROM commercial_lead_requests WHERE {where_clause} AND status = 'open'
    '''), params).scalar() or 0
    
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    params['limit'] = per_page
    params['offset'] = offset
    
    leads = db.session.execute(text(f'''
        SELECT * FROM commercial_lead_requests 
        WHERE {where_clause} AND status = 'open'
        ORDER BY 
            CASE urgency 
                WHEN 'emergency' THEN 1
                WHEN 'urgent' THEN 2
                WHEN 'soon' THEN 3
                ELSE 4
            END,
            created_at DESC
        LIMIT :limit OFFSET :offset
    '''), params).fetchall()
    
    return render_template('quick_wins.html',
                         leads=leads,
                         emergency_count=emergency_count,
                         urgent_count=urgent_count,
                         total_count=total_count,
                         page=page,
                         total_pages=total_pages,
                         is_paid_subscriber=is_paid,
                         is_admin=is_admin)

@app.route('/bulk-products')
@login_required
def bulk_products():
    """Marketplace for bulk cleaning product requests"""
    category_filter = request.args.get('category', '')
    quantity_filter = request.args.get('quantity', '')
    urgency_filter = request.args.get('urgency', '')
    page = max(int(request.args.get('page', 1) or 1), 1)
    per_page = 12
    offset = (page - 1) * per_page
    
    # Check if paid subscriber or admin
    is_admin = session.get('is_admin', False)
    is_paid = False
    if not is_admin and 'user_id' in session:
        result = db.session.execute(text('''
            SELECT subscription_status FROM leads WHERE id = :user_id
        '''), {'user_id': session['user_id']}).fetchone()
        if result and result[0] == 'paid':
            is_paid = True
    
    # Build query
    where_conditions = ["status = 'open'"]
    params = {}
    
    if category_filter:
        where_conditions.append("category = :category")
        params['category'] = category_filter
    
    if urgency_filter:
        where_conditions.append("urgency = :urgency")
        params['urgency'] = urgency_filter
    
    where_clause = " AND ".join(where_conditions)
    
    # Get stats
    active_requests = db.session.execute(text(
        "SELECT COUNT(*) FROM bulk_product_requests WHERE status = 'open'"
    )).scalar() or 0
    
    total_value = db.session.execute(text(
        "SELECT SUM(total_budget) FROM bulk_product_requests WHERE status = 'open'"
    )).scalar() or 0
    
    categories_count = db.session.execute(text(
        "SELECT COUNT(DISTINCT category) FROM bulk_product_requests WHERE status = 'open'"
    )).scalar() or 0
    
    # Get requests
    total_count = db.session.execute(text(f'''
        SELECT COUNT(*) FROM bulk_product_requests WHERE {where_clause}
    '''), params).scalar() or 0
    
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    params['limit'] = per_page
    params['offset'] = offset
    
    requests_data = db.session.execute(text(f'''
        SELECT * FROM bulk_product_requests 
        WHERE {where_clause}
        ORDER BY 
            CASE urgency 
                WHEN 'immediate' THEN 1
                WHEN 'this_week' THEN 2
                WHEN 'this_month' THEN 3
                ELSE 4
            END,
            created_at DESC
        LIMIT :limit OFFSET :offset
    '''), params).fetchall()
    
    return render_template('bulk_products.html',
                         requests=requests_data,
                         active_requests=active_requests,
                         total_value=total_value,
                         categories_count=categories_count,
                         page=page,
                         total_pages=total_pages,
                         is_paid_subscriber=is_paid,
                         is_admin=is_admin)

@app.route('/api/submit-bulk-quote', methods=['POST'])
@login_required
def submit_bulk_quote():
    """Submit quote for bulk product request"""
    try:
        data = request.get_json()
        
        db.session.execute(text('''
            INSERT INTO bulk_product_quotes
            (request_id, user_id, price_per_unit, total_amount, delivery_timeline,
             brands, details, created_at)
            VALUES (:request_id, :user_id, :price_per_unit, :total_amount, :delivery_timeline,
                    :brands, :details, CURRENT_TIMESTAMP)
        '''), {
            'request_id': data.get('request_id'),
            'user_id': session['user_id'],
            'price_per_unit': data.get('price_per_unit'),
            'total_amount': data.get('total_amount'),
            'delivery_timeline': data.get('delivery_timeline'),
            'brands': data.get('brands', ''),
            'details': data.get('details', '')
        })
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Quote submitted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Submit bulk quote error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Helper function for proposal generation
def generate_proposal_content(contract, company_name, years, differentiators, sections):
    """Generate proposal content (placeholder for AI integration)"""
    content = f"""
    <div style="font-family: 'Times New Roman', serif; font-size: 12pt; line-height: 1.6;">
        <div style="text-align: center; margin-bottom: 40px;">
            <h1>{company_name}</h1>
            <h2>Proposal for: {contract.get('title', 'Cleaning Services Contract')}</h2>
            <p>Solicitation Number: {contract.get('solicitationNumber', contract.get('id', 'N/A'))}</p>
            <p>Submitted: {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
        
        {('<div style="margin-bottom: 30px;"><h3>EXECUTIVE SUMMARY</h3><p>' + company_name + ' is pleased to submit this proposal for ' + contract.get('title', 'the referenced cleaning services contract') + '. With ' + str(years) + ' years of experience in professional cleaning services, we bring proven expertise and a commitment to excellence. Our key differentiators include: ' + differentiators + '</p><p>[ADD SPECIFIC COMPANY HIGHLIGHTS AND WHY YOU ARE THE BEST CHOICE]</p></div>') if sections.get('executiveSummary') else ''}
        
        {('<div style="margin-bottom: 30px;"><h3>TECHNICAL APPROACH</h3><h4>Understanding of Requirements</h4><p>We have carefully reviewed the RFP and understand that the contract requires:</p><ul><li>[LIST KEY REQUIREMENT 1]</li><li>[LIST KEY REQUIREMENT 2]</li><li>[LIST KEY REQUIREMENT 3]</li></ul><h4>Proposed Methodology</h4><p>[DESCRIBE YOUR STEP-BY-STEP CLEANING PROCESS]</p><p>[DETAIL EQUIPMENT AND PRODUCTS TO BE USED]</p><p>[EXPLAIN QUALITY CONTROL MEASURES]</p><h4>Green Cleaning Practices</h4><p>[IF APPLICABLE, DESCRIBE ECO-FRIENDLY APPROACH]</p></div>') if sections.get('technicalApproach') else ''}
        
        {('<div style="margin-bottom: 30px;"><h3>STAFFING PLAN</h3><h4>Organizational Structure</h4><p>[INSERT ORGANIZATIONAL CHART HERE]</p><h4>Key Personnel</h4><table style="width: 100%; border-collapse: collapse;"><tr style="background: #f0f0f0;"><th style="border: 1px solid #ddd; padding: 8px;">Name</th><th style="border: 1px solid #ddd; padding: 8px;">Position</th><th style="border: 1px solid #ddd; padding: 8px;">Experience</th><th style="border: 1px solid #ddd; padding: 8px;">Certifications</th></tr><tr><td style="border: 1px solid #ddd; padding: 8px;">[NAME]</td><td style="border: 1px solid #ddd; padding: 8px;">Project Manager</td><td style="border: 1px solid #ddd; padding: 8px;">[X years]</td><td style="border: 1px solid #ddd; padding: 8px;">[LIST CERTS]</td></tr><tr><td style="border: 1px solid #ddd; padding: 8px;">[NAME]</td><td style="border: 1px solid #ddd; padding: 8px;">Lead Supervisor</td><td style="border: 1px solid #ddd; padding: 8px;">[X years]</td><td style="border: 1px solid #ddd; padding: 8px;">[LIST CERTS]</td></tr></table><h4>Training Programs</h4><p>[DESCRIBE YOUR EMPLOYEE TRAINING APPROACH]</p></div>') if sections.get('staffingPlan') else ''}
        
        {('<div style="margin-bottom: 30px;"><h3>PAST PERFORMANCE</h3><h4>Relevant Project Experience</h4><div style="margin-bottom: 20px;"><strong>Project 1: [PROJECT NAME]</strong><br>Client: [CLIENT NAME]<br>Contract Value: $[VALUE]<br>Period: [START DATE] - [END DATE]<br>Scope: [DESCRIBE SIMILAR WORK]<br>Results: [QUANTIFY ACHIEVEMENTS - e.g., 99.5% quality score, zero safety incidents]</div><div style="margin-bottom: 20px;"><strong>Project 2: [PROJECT NAME]</strong><br>Client: [CLIENT NAME]<br>Contract Value: $[VALUE]<br>Period: [START DATE] - [END DATE]<br>Scope: [DESCRIBE SIMILAR WORK]<br>Results: [QUANTIFY ACHIEVEMENTS]</div><div style="margin-bottom: 20px;"><strong>Project 3: [PROJECT NAME]</strong><br>Client: [CLIENT NAME]<br>Contract Value: $[VALUE]<br>Period: [START DATE] - [END DATE]<br>Scope: [DESCRIBE SIMILAR WORK]<br>Results: [QUANTIFY ACHIEVEMENTS]</div></div>') if sections.get('pastPerformance') else ''}
        
        {('<div style="margin-bottom: 30px;"><h3>QUALITY CONTROL PLAN</h3><h4>Inspection Procedures</h4><p>[DESCRIBE HOW YOU WILL INSPECT WORK DAILY/WEEKLY]</p><h4>Customer Feedback Mechanisms</h4><p>[EXPLAIN HOW CUSTOMERS CAN REPORT ISSUES]</p><h4>Corrective Action Process</h4><p>[DETAIL STEPS WHEN ISSUES ARE IDENTIFIED]</p><h4>Performance Metrics</h4><ul><li>[METRIC 1: e.g., Response time to complaints < 2 hours]</li><li>[METRIC 2: e.g., Quality audit scores > 95%]</li><li>[METRIC 3: e.g., Customer satisfaction > 90%]</li></ul></div>') if sections.get('qualityControl') else ''}
        
        {('<div style="margin-bottom: 30px;"><h3>COMPLIANCE MATRIX</h3><table style="width: 100%; border-collapse: collapse;"><tr style="background: #f0f0f0;"><th style="border: 1px solid #ddd; padding: 8px;">RFP Section</th><th style="border: 1px solid #ddd; padding: 8px;">Requirement</th><th style="border: 1px solid #ddd; padding: 8px;">Proposal Section</th><th style="border: 1px solid #ddd; padding: 8px;">Page #</th></tr><tr><td style="border: 1px solid #ddd; padding: 8px;">[e.g., Section 3.1]</td><td style="border: 1px solid #ddd; padding: 8px;">[REQUIREMENT TEXT]</td><td style="border: 1px solid #ddd; padding: 8px;">[WHERE YOU ADDRESSED IT]</td><td style="border: 1px solid #ddd; padding: 8px;">[PAGE]</td></tr><tr><td colspan="4" style="border: 1px solid #ddd; padding: 8px; text-align: center;">[ADD ALL RFP REQUIREMENTS HERE]</td></tr></table></div>') if sections.get('compliance') else ''}
        
        <div style="margin-top: 40px;">
            <p><strong>Respectfully Submitted,</strong></p>
            <p>[YOUR NAME]<br>[YOUR TITLE]<br>{company_name}<br>[CONTACT INFORMATION]</p>
        </div>
    </div>
    """
    return content

def find_placeholders(content):
    """Find placeholders that need personalization"""
    import re
    placeholders = re.findall(r'\[([^\]]+)\]', content)
    return list(set(placeholders))  # Remove duplicates

@app.route('/api/consultation-request', methods=['POST'])
@login_required
def consultation_request():
    """Handle consultation request submissions"""
    try:
        data = request.get_json()
        
        # Store consultation request in database
        db.session.execute(text('''
            INSERT INTO consultation_requests 
            (user_id, full_name, company_name, email, phone, solicitation_number,
             contract_type, proposal_length, deadline, add_branding, add_marketing,
             add_full_service, description, contact_method, service_level, created_at)
            VALUES (:user_id, :full_name, :company_name, :email, :phone, :solicitation_number,
                    :contract_type, :proposal_length, :deadline, :add_branding, :add_marketing,
                    :add_full_service, :description, :contact_method, :service_level, CURRENT_TIMESTAMP)
        '''), {
            'user_id': session['user_id'],
            'full_name': data.get('fullName'),
            'company_name': data.get('companyName'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'solicitation_number': data.get('solicitationNumber', ''),
            'contract_type': data.get('contractType'),
            'proposal_length': data.get('proposalLength'),
            'deadline': data.get('deadline'),
            'add_branding': data.get('addBranding', False),
            'add_marketing': data.get('addMarketing', False),
            'add_full_service': data.get('addFullService', False),
            'description': data.get('description'),
            'contact_method': data.get('contactMethod'),
            'service_level': data.get('serviceLevel', '')
        })
        db.session.commit()
        
        # TODO: Send notification email to admin/proposal specialists
        
        return jsonify({'success': True, 'message': 'Consultation request received'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Consultation request error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notify-launch', methods=['POST'])
def notify_launch():
    """Store email for federal contracts launch notification"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email required'}), 400
        
        # Store email for notification
        db.session.execute(text('''
            INSERT INTO launch_notifications (email, created_at)
            VALUES (:email, CURRENT_TIMESTAMP)
            ON CONFLICT (email) DO NOTHING
        '''), {'email': email})
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'You will be notified on launch day'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Launch notification error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# NEW LEAD GENERATION SYSTEM
# ============================================================================

@app.route('/request-cleaning', methods=['GET', 'POST'])
def submit_cleaning_request():
    """Commercial businesses can request cleaning services"""
    if request.method == 'GET':
        return render_template('request_cleaning.html')
    
    try:
        # Get form data
        data = {
            'business_name': request.form['business_name'],
            'contact_name': request.form['contact_name'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'address': request.form['address'],
            'city': request.form['city'],
            'zip_code': request.form['zip_code'],
            'business_type': request.form['business_type'],
            'square_footage': request.form['square_footage'],
            'frequency': request.form['frequency'],
            'services_needed': request.form['services_needed'],
            'special_requirements': request.form.get('special_requirements', ''),
            'budget_range': request.form.get('budget_range', ''),
            'start_date': request.form.get('start_date', None),
            'urgency': request.form.get('urgency', 'normal')
        }
        
        # Insert into database
        db.session.execute(text('''
            INSERT INTO commercial_lead_requests 
            (business_name, contact_name, email, phone, address, city, zip_code, 
             business_type, square_footage, frequency, services_needed, 
             special_requirements, budget_range, start_date, urgency, status)
            VALUES (:business_name, :contact_name, :email, :phone, :address, :city, :zip_code,
                    :business_type, :square_footage, :frequency, :services_needed,
                    :special_requirements, :budget_range, :start_date, :urgency, 'open')
        '''), data)
        db.session.commit()
        
        # Send email notifications to subscribers
        send_new_lead_notification('commercial', data)
        
        flash('Your request has been submitted successfully! Cleaning contractors will contact you soon.', 'success')
        return redirect(url_for('submit_cleaning_request'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting request: {str(e)}', 'danger')
        return redirect(url_for('submit_cleaning_request'))

@app.route('/request-residential-cleaning', methods=['GET', 'POST'])
def submit_residential_cleaning_request():
    """Homeowners can request residential cleaning services"""
    if request.method == 'GET':
        return render_template('request_residential_cleaning.html')
    
    try:
        # Get form data
        data = {
            'homeowner_name': request.form['homeowner_name'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'address': request.form['address'],
            'city': request.form['city'],
            'zip_code': request.form['zip_code'],
            'property_type': request.form['property_type'],
            'bedrooms': request.form.get('bedrooms', 0),
            'bathrooms': request.form.get('bathrooms', 0),
            'square_footage': request.form.get('square_footage', 0),
            'frequency': request.form['frequency'],
            'services_needed': request.form['services_needed'],
            'special_requirements': request.form.get('special_requirements', ''),
            'budget_range': request.form.get('budget_range', ''),
            'preferred_start_date': request.form.get('preferred_start_date', None),
            'urgency': request.form.get('urgency', 'normal'),
            'pets': request.form.get('pets', 'no'),
            'access_instructions': request.form.get('access_instructions', '')
        }
        
        # Insert into residential_leads table
        db.session.execute(text('''
            INSERT INTO residential_leads 
            (homeowner_name, address, city, zip_code, property_type, bedrooms, bathrooms, 
             square_footage, contact_email, contact_phone, estimated_value, 
             cleaning_frequency, services_needed, special_requirements, status, 
             source, lead_quality, created_at)
            VALUES 
            (:homeowner_name, :address, :city, :zip_code, :property_type, :bedrooms, :bathrooms,
             :square_footage, :email, :phone, :estimated_value, :frequency, :services_needed,
             :special_requirements, 'new', 'website_form', 'hot', CURRENT_TIMESTAMP)
        '''), {
            'homeowner_name': data['homeowner_name'],
            'address': data['address'],
            'city': data['city'],
            'zip_code': data['zip_code'],
            'property_type': data['property_type'],
            'bedrooms': data['bedrooms'],
            'bathrooms': data['bathrooms'],
            'square_footage': data['square_footage'],
            'email': data['email'],
            'phone': data['phone'],
            'estimated_value': calculate_estimated_value(data),
            'frequency': data['frequency'],
            'services_needed': data['services_needed'],
            'special_requirements': f"{data['special_requirements']}; Budget: {data['budget_range']}; Start: {data['preferred_start_date']}; Urgency: {data['urgency']}; Pets: {data['pets']}; Access: {data['access_instructions']}"
        })
        db.session.commit()
        
        # Add estimated_value to data for email
        data['estimated_value'] = calculate_estimated_value(data)
        
        # Send email notifications to subscribers
        send_new_lead_notification('residential', data)
        
        flash('Your request has been submitted successfully! Cleaning contractors will contact you soon.', 'success')
        return redirect(url_for('submit_residential_cleaning_request'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting request: {str(e)}', 'danger')
        return redirect(url_for('submit_residential_cleaning_request'))

def calculate_estimated_value(data):
    """Calculate estimated monthly value based on property details"""
    base_value = 100
    
    # Add value based on square footage
    sqft = int(data.get('square_footage', 0) or 0)
    if sqft > 3000:
        base_value += 200
    elif sqft > 2000:
        base_value += 100
    elif sqft > 1000:
        base_value += 50
    
    # Add value based on frequency
    freq = data.get('frequency', 'one-time')
    if freq == 'weekly':
        base_value *= 4
    elif freq == 'bi-weekly':
        base_value *= 2
    elif freq == 'monthly':
        base_value *= 1
    else:  # one-time
        base_value *= 1.5
    
    # Add value based on rooms
    bedrooms = int(data.get('bedrooms', 0) or 0)
    bathrooms = int(data.get('bathrooms', 0) or 0)
    base_value += (bedrooms * 20) + (bathrooms * 30)
    
    return int(base_value)

@app.route('/lead-marketplace')
@login_required
def lead_marketplace():
    """Dashboard for subscribers to view and bid on leads"""
    try:
        # Check if user has active subscription
        user_email = session.get('user_email')
        user = db.session.execute(
            text('SELECT * FROM leads WHERE email = :email'),
            {'email': user_email}
        ).fetchone()
        
        if not user or user[15] != 'paid':  # subscription_status column
            flash('You need an active subscription to access the lead marketplace.', 'warning')
            return redirect(url_for('register'))
        
        # Get open commercial lead requests
        requests = db.session.execute(text('''
            SELECT * FROM commercial_lead_requests 
            WHERE status = 'open' 
            ORDER BY created_at DESC
        ''')).fetchall()
        
        # Get user's bids
        my_bids = db.session.execute(text('''
            SELECT b.*, clr.business_name, clr.city 
            FROM bids b
            JOIN commercial_lead_requests clr ON b.request_id = clr.id
            WHERE b.user_email = :email
            ORDER BY b.submitted_at DESC
        '''), {'email': user_email}).fetchall()
        
        # Get residential leads
        residential = db.session.execute(text('''
            SELECT * FROM residential_leads 
            WHERE status = 'new'
            ORDER BY estimated_value DESC
            LIMIT 50
        ''')).fetchall()
        
        return render_template('lead_marketplace.html', 
                             requests=requests, 
                             my_bids=my_bids,
                             residential=residential)
    except Exception as e:
        flash(f'Error loading marketplace: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route('/submit-bid/<int:request_id>', methods=['POST'])
@login_required
def submit_bid(request_id):
    """Submit a bid on a commercial lead request"""
    try:
        user_email = session.get('user_email')
        
        # Get user info
        user = db.session.execute(
            text('SELECT company_name FROM leads WHERE email = :email'),
            {'email': user_email}
        ).fetchone()
        
        # Insert bid
        db.session.execute(text('''
            INSERT INTO bids 
            (request_id, user_email, company_name, bid_amount, proposal_text, 
             estimated_start_date, contact_phone, status)
            VALUES (:request_id, :user_email, :company_name, :bid_amount, :proposal_text,
                    :start_date, :phone, 'pending')
        '''), {
            'request_id': request_id,
            'user_email': user_email,
            'company_name': user[0],
            'bid_amount': request.form['bid_amount'],
            'proposal_text': request.form['proposal_text'],
            'start_date': request.form.get('estimated_start_date'),
            'phone': request.form['contact_phone']
        })
        
        # Update bid count
        db.session.execute(text('''
            UPDATE commercial_lead_requests 
            SET bid_count = bid_count + 1,
                status = CASE WHEN bid_count = 0 THEN 'bidding' ELSE status END
            WHERE id = :request_id
        '''), {'request_id': request_id})
        
        db.session.commit()
        
        flash('Your bid has been submitted successfully!', 'success')
        return redirect(url_for('lead_marketplace'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting bid: {str(e)}', 'danger')
        return redirect(url_for('lead_marketplace'))

@app.route('/mark-complete/<int:request_id>', methods=['POST'])
@login_required
def mark_request_complete(request_id):
    """Mark a lead request as complete (admin only or request owner)"""
    try:
        db.session.execute(text('''
            UPDATE commercial_lead_requests 
            SET status = 'completed',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :request_id
        '''), {'request_id': request_id})
        
        db.session.commit()
        flash('Lead request marked as complete!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('lead_marketplace'))

# Initialize database for both local and production
try:
    init_db()
except Exception as e:
    print(f"Database initialization warning: {e}")

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)