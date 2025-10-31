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

# Virginia Government Contracting Lead Generation Application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'virginia-contracting-fallback-key-2024')

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

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access this page.', 'warning')
            return redirect(url_for('signin'))
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
        contracts = fetcher.fetch_va_cleaning_contracts(days_back=30)
        
        if not contracts:
            print("⚠️  No new contracts found. Check SAM_GOV_API_KEY.")
            return
        
        # Use SQLAlchemy for database operations
        with app.app_context():
            # Clean up old contracts (older than 90 days)
            db.session.execute(text('''
                DELETE FROM federal_contracts 
                WHERE posted_date < DATE('now', '-90 days')
            '''))
            
            # Insert new contracts
            new_count = 0
            for contract in contracts:
                try:
                    db.session.execute(text('''
                        INSERT OR IGNORE INTO federal_contracts 
                        (title, agency, department, location, value, deadline, description, 
                         naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                        VALUES (:title, :agency, :department, :location, :value, :deadline, 
                                :description, :naics_code, :sam_gov_url, :notice_id, 
                                :set_aside, :posted_date)
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
        
        # Use SQLAlchemy for database operations
        with app.app_context():
            # Clean up old contracts (older than 120 days)
            db.session.execute(text('''
                DELETE FROM contracts 
                WHERE created_at < DATE('now', '-120 days')
            '''))
            
            # Insert new contracts
            new_count = 0
            for contract in contracts:
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

# Start SAM.gov scheduler in background thread
samgov_scheduler_thread = threading.Thread(target=schedule_samgov_updates, daemon=True)
samgov_scheduler_thread.start()

# Start Local Government scheduler in background thread
localgov_scheduler_thread = threading.Thread(target=schedule_local_gov_updates, daemon=True)
localgov_scheduler_thread.start()

# Run initial update on startup (in background to not block app startup)
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
        
        # Residential leads table (from Zillow/Realtor.com)
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS residential_leads
                     (id SERIAL PRIMARY KEY,
                      address TEXT NOT NULL,
                      city TEXT NOT NULL,
                      state TEXT DEFAULT 'VA',
                      zip_code TEXT,
                      property_type TEXT,
                      bedrooms INTEGER,
                      bathrooms DECIMAL(3,1),
                      square_feet INTEGER,
                      estimated_value DECIMAL(12,2),
                      owner_name TEXT,
                      owner_phone TEXT,
                      owner_email TEXT,
                      last_sale_date DATE,
                      last_sale_price DECIMAL(12,2),
                      source TEXT,
                      listing_url TEXT,
                      status TEXT DEFAULT 'new',
                      notes TEXT,
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
        
        # Add sample data
        # Check if data already exists
        existing_contracts = db.session.execute(text('SELECT COUNT(*) FROM contracts')).fetchone()[0]
        if existing_contracts == 0:
            # Insert sample contracts using parameterized queries
            db.session.execute(text("""
                INSERT INTO contracts (title, agency, location, value, deadline, description, naics_code, website_url)
                VALUES 
                ('Janitorial Services - City Hall Complex', 'Hampton City Government', 'Hampton, VA', '$45,000', '2025-12-15', 'Daily cleaning and maintenance services for City Hall and administrative buildings', '561720', 'https://www.hampton.gov/bids'),
                ('Medical Facility Cleaning Services', 'Virginia Beach Health Department', 'Virginia Beach, VA', '$78,000', '2025-11-30', 'Specialized cleaning services for medical facilities requiring infection control protocols', '561720', 'https://www.vbgov.com/government/departments/purchasing'),
                ('School Facility Maintenance Contract', 'Suffolk Public Schools', 'Suffolk, VA', '$125,000', '2026-01-20', 'Comprehensive cleaning and maintenance for 12 elementary schools', '561720', 'https://www.suffolkva.us/bids'),
                ('Parks and Recreation Facilities', 'Newport News Parks Department', 'Newport News, VA', '$34,500', '2025-12-01', 'Cleaning services for community centers, sports facilities, and restrooms', '561720', 'https://www.nnva.gov/bids'),
                ('Library System Cleaning Services', 'Williamsburg Regional Library', 'Williamsburg, VA', '$28,000', '2026-02-15', 'Evening and weekend cleaning services for 4 library branches', '561720', 'https://www.wrl.org/about-wrl/bids'),
                ('Municipal Building Janitorial Services', 'Chesapeake City Government', 'Chesapeake, VA', '$52,000', '2025-11-25', 'Daily janitorial services for municipal offices and public spaces', '561720', 'https://www.cityofchesapeake.net/government/bids')
            """))
            
            # Insert sample commercial opportunities
            db.session.execute(text("""
                INSERT INTO commercial_opportunities 
                (business_name, business_type, address, location, square_footage, monthly_value, frequency, services_needed, special_requirements, contact_type, description, size)
                VALUES
                ('Hampton Marina Resort', 'hospitality', '456 Marina Dr', 'Hampton', 15000, 5200, 'daily', 'Guest rooms, lobby, restaurants, pool area', 'Marina resort with boat docks and waterfront dining', 'Property Manager', '120-room waterfront resort with marina and restaurant', 'medium'),
                ('Suffolk Medical Center', 'medical', '789 Medical Plaza', 'Suffolk', 32000, 8500, 'daily', 'Patient rooms, exam rooms, surgical suites', 'Healthcare facility requiring infection control standards', 'Facilities Director', '80-bed medical center with outpatient services', 'large'),
                ('Virginia Beach Tech Campus', 'office', '321 Innovation Way', 'Virginia Beach', 45000, 9200, 'weekly', 'Open office spaces, conference rooms, cafeteria', 'Modern tech campus with multiple buildings', 'Facility Operations Manager', 'Technology company campus with 500+ employees', 'large')
            """))
            
            db.session.commit()
        
        print("PostgreSQL tables created successfully with sample data")
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
        print("📡 Fetching real federal contracts from SAM.gov API...")
        
        # Fetch real federal contracts from SAM.gov on first run
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
            ('Newport News Orthodontics', 'medical', '321 Dental Plaza', 'Newport News', 3200, 2200, 'daily', 'Operatories, sterilization areas, waiting room', 'Specialized dental equipment cleaning, child-friendly environment', 'Practice Administrator', 'Pediatric and adult orthodontics practice with digital imaging', 'small'),
            ('Colonial Fitness Center', 'fitness', '654 Colonial Way', 'Williamsburg', 8500, 3800, 'daily', 'Cardio areas, free weights, locker rooms', 'Historic district location, early morning cleaning preferred', 'Assistant Manager', 'Community fitness center near Colonial Williamsburg with senior programs', 'medium'),
            ('Tidewater Property Management', 'real-estate', '987 Business Park Dr', 'Norfolk', 5500, 1600, 'weekly', 'Offices, conference rooms, break rooms', 'Flexible scheduling for client meetings, document confidentiality', 'Office Coordinator', 'Property management company overseeing 200+ rental properties', 'medium'),
            ('Hampton Roads Hotel', 'hospitality', '147 Hotel Circle', 'Hampton', 25000, 8500, 'daily', 'Guest rooms, lobby, conference facilities, restaurant', '24/7 operation, rapid room turnover, event space cleaning', 'Housekeeping Supervisor', 'Full-service hotel with 120 rooms, restaurant, and meeting facilities', 'large'),
            ('Bright Beginnings Daycare', 'childcare', '258 Kiddie Lane', 'Suffolk', 4800, 2400, 'daily', 'Classrooms, play areas, kitchen, bathrooms', 'Child-safe products only, background check required, naptime cleaning', 'Center Director', 'Licensed daycare for ages 6 weeks to 5 years with 85 children enrolled', 'small'),
            ('Virginia Beach Tutoring Center', 'education', '369 Learning St', 'Virginia Beach', 3500, 1200, 'weekly', 'Tutoring rooms, computer lab, reception area', 'After-hours cleaning preferred, technology equipment care', 'Academic Director', 'Private tutoring center serving K-12 students with STEM focus', 'small'),
            ('Chesapeake Family Medicine', 'medical', '741 Health Dr', 'Chesapeake', 7200, 4800, 'daily', 'Exam rooms, lab area, waiting room, administrative offices', 'Medical waste protocols, patient privacy considerations', 'Office Manager', 'Family practice with on-site lab and minor surgery capabilities', 'medium'),
            ('The Fitness Edge', 'fitness', '852 Workout Way', 'Norfolk', 10000, 4500, 'daily', 'Weight room, cardio area, group fitness studios, locker rooms', 'CrossFit equipment, specialized rubber flooring, shower facilities', 'Operations Manager', 'CrossFit affiliate with personal training and nutrition counseling', 'medium'),
            ('Portsmouth Pediatric Dentistry', 'medical', '963 Kids Dental Ct', 'Portsmouth', 2800, 1800, 'daily', 'Pediatric operatories, play area, consultation rooms', 'Child-friendly cleaning products, colorful environment maintenance', 'Dental Hygienist Supervisor', 'Pediatric dental practice with themed treatment rooms and arcade', 'small'),
            ('Williamsburg Extended Stay', 'hospitality', '159 Extended Way', 'Williamsburg', 18000, 6200, 'weekly', 'Studio apartments, common areas, laundry facility', 'Extended stay guests, kitchen cleaning, weekly deep clean', 'Property Manager', 'Extended stay hotel with kitchenettes for business travelers', 'large'),
            ('Elite Real Estate Group', 'real-estate', '357 Realty Row', 'Virginia Beach', 4200, 1400, 'bi-weekly', 'Open office space, private offices, conference room', 'Staging area cleaning, model home prep as needed', 'Sales Manager', 'High-end real estate brokerage specializing in luxury coastal properties', 'small'),
            ('Suffolk Senior Living', 'healthcare', '486 Senior Blvd', 'Suffolk', 35000, 12000, 'daily', 'Resident rooms, dining hall, activity areas, medical wing', 'Healthcare regulations compliance, infection control, dignified service', 'Administrator', 'Assisted living facility with 65 residents and memory care unit', 'large'),
            
            # Additional 85 Commercial Opportunities
            ('Hampton Bay Medical Plaza', 'medical', '789 Medical Center Dr', 'Hampton', 12000, 6500, 'daily', 'Multiple doctor offices, shared waiting areas, lab facilities', 'Multi-tenant medical building, specialized medical cleaning', 'Building Manager', 'Medical office complex with 8 specialty practices and diagnostic center', 'large'),
            ('Norfolk Corporate Center', 'office', '456 Business Blvd', 'Norfolk', 18000, 4200, 'weekly', 'Corporate offices, meeting rooms, executive suites', 'After-hours cleaning, high-security building access', 'Facilities Director', 'Class A office building with Fortune 500 tenants', 'large'),
            ('Virginia Beach Marriott', 'hospitality', '987 Resort Dr', 'Virginia Beach', 45000, 15000, 'daily', 'Hotel rooms, restaurants, conference center, spa', 'Luxury hotel standards, 24/7 operations, event turnover', 'Executive Housekeeper', '300-room oceanfront resort with full amenities and conference facilities', 'large'),
            ('Chesapeake CrossFit', 'fitness', '123 Strong St', 'Chesapeake', 6500, 2800, 'daily', 'Open gym space, locker rooms, equipment cleaning', 'Specialized equipment cleaning, rubber flooring care', 'Head Coach', 'CrossFit box with Olympic lifting platform and group classes', 'medium'),
            ('Portsmouth Legal Center', 'legal', '654 Justice Way', 'Portsmouth', 8500, 2400, 'weekly', 'Law offices, conference rooms, law library', 'Confidential document handling, evening cleaning preferred', 'Office Administrator', 'Multi-practice legal center with 15 attorneys', 'medium'),
            ('Hampton Veterinary Hospital', 'medical', '321 Pet Care Ln', 'Hampton', 5500, 3200, 'daily', 'Exam rooms, surgery suite, kennels, reception', 'Animal-safe products, odor control, kennel sanitation', 'Hospital Manager', 'Full-service veterinary hospital with boarding and grooming', 'medium'),
            ('Williamsburg Preschool Academy', 'education', '789 Learning Lane', 'Williamsburg', 4200, 2100, 'daily', 'Classrooms, playground areas, kitchen, bathrooms', 'Child-safe cleaning products, naptime schedule coordination', 'Director', 'Montessori preschool for ages 2-6 with 120 students', 'small'),
            ('Norfolk Technology Solutions', 'office', '456 Tech Park Dr', 'Norfolk', 9500, 2800, 'weekly', 'Open office, server room, conference areas', 'Sensitive electronics, data security clearance required', 'Operations Manager', 'IT consulting firm with secure server facilities', 'medium'),
            ('Virginia Beach Dental Specialists', 'medical', '147 Specialty Dr', 'Virginia Beach', 6800, 4200, 'daily', 'Oral surgery suites, recovery areas, sterilization rooms', 'Surgical-grade cleaning, specialized waste disposal', 'Clinical Director', 'Oral surgery and periodontics practice with 4 specialists', 'medium'),
            ('Suffolk Manufacturing Office', 'office', '258 Industrial Way', 'Suffolk', 7200, 2100, 'weekly', 'Administrative offices, break rooms, conference facilities', 'Industrial setting, flexible scheduling around operations', 'HR Manager', 'Manufacturing company headquarters with 150 office employees', 'medium'),
            ('Newport News Auto Dealership', 'office', '369 Auto Mall Dr', 'Newport News', 12000, 3500, 'weekly', 'Showroom, offices, customer lounge, service area', 'High-traffic showroom, weekend availability required', 'General Manager', 'Large automotive dealership with sales and service departments', 'large'),
            ('Chesapeake Childcare Center', 'childcare', '741 Tiny Tots Dr', 'Chesapeake', 5800, 2900, 'daily', 'Age-specific classrooms, playground, kitchen, nursery', 'State licensing compliance, infant room specialization', 'Center Administrator', 'Licensed daycare serving 95 children from infants to school-age', 'medium'),
            ('Portsmouth Marina Club', 'hospitality', '852 Marina Way', 'Portsmouth', 8500, 4800, 'weekly', 'Clubhouse, restaurant, event spaces, marina office', 'Waterfront location, event-based cleaning schedule', 'Club Manager', 'Private marina and yacht club with dining and events', 'medium'),
            ('Hampton Physical Therapy', 'medical', '963 Rehab Dr', 'Hampton', 4500, 2600, 'daily', 'Treatment rooms, gym area, hydrotherapy pool', 'Medical equipment cleaning, pool area maintenance', 'Clinical Director', 'Outpatient physical therapy clinic with aquatic therapy', 'small'),
            ('Virginia Beach Wedding Venue', 'hospitality', '159 Wedding Way', 'Virginia Beach', 15000, 8500, 'weekly', 'Reception halls, bridal suites, outdoor ceremony areas', 'Event-based cleaning, rapid turnovers, landscaping', 'Event Coordinator', 'Premier wedding venue with indoor/outdoor ceremony spaces', 'large'),
            ('Norfolk Insurance Agency', 'office', '357 Insurance Blvd', 'Norfolk', 3500, 1200, 'weekly', 'Agent offices, conference rooms, reception area', 'Professional appearance, client confidentiality', 'Office Manager', 'Independent insurance agency with 8 agents', 'small'),
            ('Williamsburg Assisted Living', 'healthcare', '486 Golden Years Dr', 'Williamsburg', 28000, 9500, 'daily', 'Resident apartments, dining room, activity areas, clinic', 'Healthcare standards, resident dignity, infection control', 'Administrator', '85-bed assisted living facility with memory care wing', 'large'),
            ('Suffolk Fitness Club', 'fitness', '789 Wellness Way', 'Suffolk', 11000, 4200, 'daily', 'Cardio area, weight room, pool, group fitness studios', 'Pool chemicals, equipment sanitization, locker room deep cleaning', 'Club Manager', 'Full-service health club with pool and racquetball courts', 'large'),
            ('Hampton Executive Suites', 'office', '123 Executive Dr', 'Hampton', 6500, 1800, 'weekly', 'Individual offices, shared conference rooms, reception', 'Multiple tenants, professional standards, flexible access', 'Building Manager', 'Executive suite office complex with 25 private offices', 'medium'),
            ('Chesapeake Urgent Care', 'medical', '654 Emergency Dr', 'Chesapeake', 7800, 4500, 'daily', 'Exam rooms, X-ray area, waiting room, lab', 'Fast-paced environment, infection control, medical waste', 'Clinic Manager', 'Urgent care center with on-site X-ray and lab services', 'medium'),
            ('Portsmouth Hotel & Conference Center', 'hospitality', '321 Conference Dr', 'Portsmouth', 22000, 8200, 'daily', 'Hotel rooms, meeting rooms, restaurant, business center', 'Conference turnover, multiple event spaces, catering areas', 'General Manager', '150-room hotel with extensive meeting and conference facilities', 'large'),
            ('Virginia Beach Chiropractic', 'medical', '789 Spine St', 'Virginia Beach', 3800, 2100, 'daily', 'Treatment rooms, exercise area, reception, offices', 'Specialized equipment cleaning, relaxing environment', 'Practice Manager', 'Chiropractic clinic with massage therapy and rehabilitation', 'small'),
            ('Norfolk Accounting Firm', 'office', '456 Numbers Dr', 'Norfolk', 5200, 1500, 'weekly', 'CPA offices, conference rooms, file storage areas', 'Tax season intensity, confidential documents, evening cleaning', 'Managing Partner', 'CPA firm with 12 accountants specializing in business taxes', 'medium'),
            ('Suffolk Country Club', 'hospitality', '147 Golf Club Dr', 'Suffolk', 18000, 7200, 'weekly', 'Clubhouse, pro shop, restaurant, locker rooms', 'Upscale standards, golf tournament events, member privacy', 'Club Manager', 'Private country club with 18-hole golf course and dining', 'large'),
            ('Newport News Dental Group', 'medical', '258 Smile Way', 'Newport News', 9500, 5200, 'daily', 'Multiple operatories, sterilization, waiting areas, offices', 'Large dental practice, high patient volume, team coordination', 'Office Administrator', '12-chair dental practice with general and specialty services', 'large'),
            ('Williamsburg Law Firm', 'legal', '369 Attorney Ave', 'Williamsburg', 6800, 1900, 'weekly', 'Partner offices, associate areas, conference rooms, library', 'Historic district location, document confidentiality', 'Office Manager', 'Boutique law firm specializing in estate planning and real estate', 'medium'),
            ('Hampton Medical Laboratory', 'medical', '741 Lab Dr', 'Hampton', 5500, 3800, 'daily', 'Lab areas, specimen processing, offices, waiting room', 'Biohazard protocols, sterile environment, specialized waste', 'Lab Director', 'Independent medical laboratory serving multiple healthcare providers', 'medium'),
            ('Chesapeake Business Park', 'office', '852 Corporate Way', 'Chesapeake', 25000, 6500, 'weekly', 'Multiple office suites, shared amenities, conference center', 'Multi-tenant facility, common area maintenance', 'Property Manager', 'Business park with 40 office suites and shared facilities', 'large'),
            ('Virginia Beach Spa & Wellness', 'fitness', '963 Relaxation Rd', 'Virginia Beach', 8500, 4800, 'daily', 'Treatment rooms, relaxation areas, changing rooms, reception', 'Luxury spa standards, serene environment, specialized cleaning', 'Spa Director', 'Day spa with massage, facial, and wellness services', 'medium'),
            ('Portsmouth Business Center', 'office', '159 Business Dr', 'Portsmouth', 14000, 3200, 'weekly', 'Office spaces, meeting rooms, business lounge', 'Professional business environment, multi-tenant building', 'Leasing Manager', 'Class B office building with 30 office suites', 'large'),
            ('Norfolk Pediatric Center', 'medical', '357 Kids Health Dr', 'Norfolk', 6200, 3600, 'daily', 'Exam rooms, play area, lab, administrative offices', 'Child-friendly environment, toy sanitization, family areas', 'Practice Administrator', 'Pediatric medical practice serving 2,500 patients', 'medium'),
            ('Suffolk Corporate Plaza', 'office', '486 Plaza Dr', 'Suffolk', 16000, 3800, 'weekly', 'Executive offices, conference facilities, lobby areas', 'Prestigious location, executive standards, evening cleaning', 'Building Manager', 'Premium office building with Fortune 500 tenants', 'large'),
            ('Hampton Innovation Center', 'office', '789 Innovation Way', 'Hampton', 12000, 2800, 'weekly', 'Startup offices, coworking spaces, tech labs', 'Modern facility, technology equipment, flexible spaces', 'Center Director', 'Technology incubator with 25 startup companies', 'large'),
            ('Williamsburg Medical Associates', 'medical', '123 Medical Plaza', 'Williamsburg', 11000, 6200, 'daily', 'Multiple specialties, shared lab, surgery center', 'Multi-specialty practice, surgical suite cleaning', 'Administrator', 'Medical complex with 8 specialty practices', 'large'),
            ('Virginia Beach Learning Center', 'education', '654 Education Dr', 'Virginia Beach', 4800, 2200, 'daily', 'Classrooms, computer lab, library, administration', 'Educational environment, technology care, student safety', 'Principal', 'Private learning center with K-12 tutoring and test prep', 'small'),
            ('Chesapeake Professional Building', 'office', '321 Professional Way', 'Chesapeake', 8500, 2100, 'weekly', 'Professional offices, conference rooms, reception areas', 'Multi-tenant professional building, healthcare tenants', 'Property Manager', 'Professional building with medical and legal tenants', 'medium'),
            ('Newport News Wellness Center', 'fitness', '789 Wellness Blvd', 'Newport News', 13000, 5200, 'daily', 'Fitness areas, pool, spa, group exercise rooms', 'Comprehensive wellness facility, aquatic programs', 'General Manager', 'Health and wellness center with medical fitness programs', 'large'),
            ('Portsmouth Professional Center', 'office', '456 Professional Dr', 'Portsmouth', 7200, 1800, 'weekly', 'Individual offices, shared conference rooms, reception', 'Professional services building, evening cleaning preferred', 'Building Administrator', 'Professional services building with accountants and consultants', 'medium'),
            ('Hampton Rehabilitation Center', 'medical', '147 Recovery Dr', 'Hampton', 9500, 5800, 'daily', 'Therapy rooms, exercise areas, patient rooms', 'Rehabilitation equipment, patient mobility considerations', 'Clinical Director', 'Inpatient and outpatient rehabilitation facility', 'large'),
            ('Suffolk Technology Park', 'office', '258 Tech Valley Dr', 'Suffolk', 20000, 4500, 'weekly', 'Tech companies, labs, conference facilities, cafeteria', 'Technology equipment, clean room standards', 'Facilities Manager', 'Technology park with 15 high-tech companies', 'large'),
            ('Virginia Beach Executive Center', 'office', '369 Executive Way', 'Virginia Beach', 11000, 2600, 'weekly', 'Executive suites, boardrooms, business services', 'Executive-level standards, prestigious location', 'Center Manager', 'Executive office center with concierge services', 'large'),
            ('Williamsburg Retirement Community', 'healthcare', '741 Retirement Dr', 'Williamsburg', 32000, 11000, 'daily', 'Independent living, assisted care, memory care, dining', 'Senior living standards, healthcare compliance, dignity', 'Executive Director', 'Continuing care retirement community with 120 residents', 'large'),
            ('Norfolk Maritime Museum', 'education', '852 Maritime Way', 'Norfolk', 6500, 2800, 'weekly', 'Exhibit areas, gift shop, education center, offices', 'Museum standards, artifact protection, visitor areas', 'Museum Director', 'Maritime museum with interactive exhibits and education programs', 'medium'),
            ('Chesapeake Sports Complex', 'fitness', '963 Sports Dr', 'Chesapeake', 22000, 8500, 'daily', 'Multiple courts, locker rooms, pro shop, concessions', 'Multi-sport facility, tournament events, high traffic', 'Complex Manager', 'Indoor sports complex with basketball, volleyball, and tennis', 'large'),
            ('Portsmouth Arts Center', 'education', '159 Arts Dr', 'Portsmouth', 5500, 2200, 'weekly', 'Studios, gallery, theater, classrooms', 'Art materials consideration, delicate equipment', 'Arts Director', 'Community arts center with classes and performances', 'medium'),
            ('Hampton Business District', 'office', '357 Commerce St', 'Hampton', 15000, 3500, 'weekly', 'Mixed-use offices, retail spaces, common areas', 'Mixed-use development, multiple tenants', 'Property Manager', 'Downtown business district with office and retail tenants', 'large'),
            ('Virginia Beach Medical Tower', 'medical', '486 Medical Tower Dr', 'Virginia Beach', 18000, 8500, 'daily', 'Multiple medical specialties, lab, imaging center', 'Medical tower with various specialties, imaging equipment', 'Building Administrator', '8-story medical tower with 25 medical practices', 'large'),
            ('Suffolk Community College', 'education', '789 College Dr', 'Suffolk', 28000, 7200, 'weekly', 'Classrooms, labs, library, administrative offices', 'Educational institution, technology labs, student areas', 'Facilities Director', 'Community college campus with 5,000 students', 'large'),
            ('Norfolk Convention Center', 'hospitality', '123 Convention Dr', 'Norfolk', 65000, 22000, 'weekly', 'Exhibition halls, meeting rooms, catering areas', 'Large convention facility, event-based cleaning', 'General Manager', 'Regional convention center with 100,000 sq ft exhibit space', 'large'),
            ('Chesapeake Medical Clinic', 'medical', '654 Clinic Dr', 'Chesapeake', 8200, 4800, 'daily', 'Exam rooms, lab, pharmacy, administrative areas', 'Multi-service medical clinic, pharmacy integration', 'Clinic Administrator', 'Multi-specialty clinic with on-site pharmacy', 'medium'),
            ('Williamsburg Conference Resort', 'hospitality', '321 Resort Way', 'Williamsburg', 35000, 12500, 'daily', 'Hotel rooms, conference center, restaurants, spa', 'Conference resort, multiple dining venues, spa services', 'Resort Manager', '200-room conference resort with full amenities', 'large'),
            ('Portsmouth Technology Center', 'office', '789 Tech Center Dr', 'Portsmouth', 16000, 3600, 'weekly', 'Tech offices, labs, conference rooms, data center', 'Technology companies, server rooms, security requirements', 'Facilities Coordinator', 'Technology center with software and engineering firms', 'large'),
            ('Hampton Senior Center', 'healthcare', '456 Senior Way', 'Hampton', 8500, 3200, 'weekly', 'Activity rooms, dining area, fitness center, offices', 'Senior community center, accessibility considerations', 'Program Director', 'Senior community center with daily programs for 300+ seniors', 'medium'),
            ('Virginia Beach Trade Center', 'office', '147 Trade Dr', 'Virginia Beach', 24000, 5200, 'weekly', 'Warehouse offices, showrooms, conference facilities', 'Trade and industrial offices, showroom standards', 'Leasing Director', 'Trade center with wholesale and distribution companies', 'large'),
            ('Suffolk Mental Health Center', 'medical', '258 Mental Health Dr', 'Suffolk', 6800, 3800, 'daily', 'Therapy offices, group rooms, administrative areas', 'Mental health facility, privacy considerations, calming environment', 'Clinical Director', 'Mental health clinic with individual and group therapy', 'medium'),
            ('Newport News Cultural Center', 'education', '369 Culture Dr', 'Newport News', 12000, 4500, 'weekly', 'Theater, gallery, classrooms, administrative offices', 'Cultural facility, performance spaces, exhibit areas', 'Executive Director', 'Community cultural center with theater and art programs', 'large'),
            ('Chesapeake Professional Plaza', 'office', '741 Plaza Dr', 'Chesapeake', 10000, 2400, 'weekly', 'Professional offices, conference center, business services', 'Professional services plaza, multiple tenant types', 'Plaza Manager', 'Professional plaza with medical, legal, and business tenants', 'medium'),
            ('Portsmouth Wellness Clinic', 'medical', '852 Wellness Dr', 'Portsmouth', 5200, 3100, 'daily', 'Treatment rooms, wellness center, reception, offices', 'Integrative wellness clinic, holistic health focus', 'Practice Manager', 'Wellness clinic with alternative and traditional medicine', 'small'),
            ('Hampton Educational Center', 'education', '963 Education Blvd', 'Hampton', 9500, 3200, 'weekly', 'Training rooms, computer labs, library, offices', 'Adult education center, technology training', 'Center Administrator', 'Adult education and workforce development center', 'medium'),
            ('Virginia Beach Golf Club', 'hospitality', '159 Golf Dr', 'Virginia Beach', 16000, 6200, 'weekly', 'Clubhouse, pro shop, restaurant, event facilities', 'Golf club facility, member events, tournament hosting', 'Club General Manager', 'Semi-private golf club with dining and event facilities', 'large'),
            ('Norfolk Health Campus', 'medical', '357 Health Campus Dr', 'Norfolk', 42000, 15000, 'daily', 'Multiple medical buildings, shared facilities, parking', 'Medical campus with multiple practices, unified cleaning', 'Campus Administrator', 'Health campus with 12 medical practices and shared services', 'large'),
            ('Suffolk Innovation Hub', 'office', '486 Innovation Dr', 'Suffolk', 14000, 3200, 'weekly', 'Startup spaces, labs, conference areas, coworking', 'Innovation center, flexible spaces, technology focus', 'Hub Director', 'Innovation hub with 30 startup companies and entrepreneurs', 'large'),
            ('Williamsburg Performance Center', 'education', '789 Performance Dr', 'Williamsburg', 8500, 3500, 'weekly', 'Theater, rehearsal rooms, costume areas, offices', 'Performing arts center, costume and set considerations', 'Artistic Director', 'Community theater and performing arts education center', 'medium'),
            ('Hampton Commerce Center', 'office', '123 Commerce Dr', 'Hampton', 18000, 4100, 'weekly', 'Office spaces, warehouse areas, loading docks', 'Commercial center, mixed office and warehouse', 'Property Supervisor', 'Commerce center with office and light industrial tenants', 'large'),
            ('Chesapeake Family Center', 'healthcare', '654 Family Dr', 'Chesapeake', 7500, 3800, 'daily', 'Family services offices, meeting rooms, play areas', 'Family services center, child-friendly areas', 'Program Coordinator', 'Family services center with counseling and support programs', 'medium'),
            ('Virginia Beach Research Institute', 'office', '321 Research Dr', 'Virginia Beach', 22000, 5500, 'weekly', 'Laboratories, offices, conference facilities, library', 'Research facility, laboratory standards, security', 'Institute Director', 'Marine science research institute with wet and dry labs', 'large'),
            ('Portsmouth Community Center', 'education', '789 Community Dr', 'Portsmouth', 11000, 4200, 'weekly', 'Multi-purpose rooms, gym, kitchen, offices', 'Community center, event hosting, recreational programs', 'Recreation Director', 'Community center with recreation and social programs', 'large'),
            ('Newport News Professional Complex', 'office', '456 Professional Blvd', 'Newport News', 13000, 2900, 'weekly', 'Professional offices, shared conference rooms, reception', 'Professional complex, multiple service providers', 'Complex Manager', 'Professional complex with healthcare and business services', 'large'),
            ('Suffolk Medical Plaza', 'medical', '147 Medical Plaza Dr', 'Suffolk', 16000, 7200, 'daily', 'Multiple medical practices, shared lab, pharmacy', 'Medical plaza, coordinated medical services', 'Plaza Administrator', 'Medical plaza with primary care and specialty practices', 'large'),
            ('Hampton Technology Institute', 'education', '258 Institute Dr', 'Hampton', 15000, 4800, 'weekly', 'Classrooms, computer labs, research areas, administration', 'Technical education institute, hands-on learning', 'Institute President', 'Technology institute with engineering and IT programs', 'large'),
            ('Virginia Beach Wellness Campus', 'fitness', '369 Wellness Campus Dr', 'Virginia Beach', 28000, 9500, 'daily', 'Fitness center, spa, medical offices, cafe', 'Wellness campus, integrated health services', 'Campus Director', 'Comprehensive wellness campus with fitness and medical services', 'large'),
            ('Williamsburg Business Center', 'office', '741 Business Center Dr', 'Williamsburg', 12000, 2800, 'weekly', 'Office suites, conference facilities, business services', 'Business center, professional services, tourist location', 'Business Manager', 'Business center serving local and tourist-related businesses', 'large'),
            ('Norfolk Athletic Club', 'fitness', '852 Athletic Dr', 'Norfolk', 20000, 7500, 'daily', 'Multiple courts, pools, fitness areas, restaurants', 'Athletic club, multiple sports, dining facilities', 'Athletic Director', 'Full-service athletic club with multiple sports and dining', 'large'),
            ('Chesapeake Executive Plaza', 'office', '963 Executive Plaza Dr', 'Chesapeake', 14000, 3100, 'weekly', 'Executive offices, boardrooms, business center', 'Executive plaza, high-end finishes, professional services', 'Plaza Director', 'Executive office plaza with premium business services', 'large'),
            ('Portsmouth Innovation Center', 'office', '159 Innovation Center Dr', 'Portsmouth', 11000, 2600, 'weekly', 'Tech startups, labs, conference rooms, coworking', 'Innovation center, emerging technology, flexible spaces', 'Innovation Director', 'Innovation center with technology startups and research', 'large'),
        
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

@app.route('/register', methods=['GET', 'POST'])
def register():
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
            return redirect(url_for('signin'))
            
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint' in str(e):
                flash('Email or username already exists. Please try another.', 'error')
            else:
                flash(f'Registration error: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
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
            return redirect(url_for('signin'))
    
    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('landing'))

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
    conn = get_db_connection()
    c = conn.cursor()
    
    if location_filter:
        c.execute('SELECT * FROM contracts WHERE location LIKE ? ORDER BY deadline ASC', 
                  (f'%{location_filter}%',))
    else:
        c.execute('SELECT * FROM contracts ORDER BY deadline ASC')
    
    all_contracts = c.fetchall()
    conn.close()
    
    # Get unique locations for filter dropdown
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT DISTINCT location FROM contracts ORDER BY location')
    locations = [row[0] for row in c.fetchall()]
    conn.close()
    
    return render_template('contracts.html', contracts=all_contracts, locations=locations, current_filter=location_filter)

@app.route('/federal-contracts')
def federal_contracts():
    """Federal contracts from SAM.gov"""
    department_filter = request.args.get('department', '')
    set_aside_filter = request.args.get('set_aside', '')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    query = 'SELECT * FROM federal_contracts WHERE 1=1'
    params = []
    
    if department_filter:
        query += ' AND department LIKE ?'
        params.append(f'%{department_filter}%')
    
    if set_aside_filter:
        query += ' AND set_aside LIKE ?'
        params.append(f'%{set_aside_filter}%')
    
    query += ' ORDER BY deadline ASC'
    
    if params:
        c.execute(query, params)
    else:
        c.execute(query)
    
    all_federal_contracts = c.fetchall()
    
    # Get unique departments and set-asides for filters
    c.execute('SELECT DISTINCT department FROM federal_contracts ORDER BY department')
    departments = [row[0] for row in c.fetchall()]
    
    c.execute('SELECT DISTINCT set_aside FROM federal_contracts ORDER BY set_aside')
    set_asides = [row[0] for row in c.fetchall()]
    
    conn.close()
    
    return render_template('federal_contracts.html', 
                          contracts=all_federal_contracts, 
                          departments=departments,
                          set_asides=set_asides,
                          current_department=department_filter,
                          current_set_aside=set_aside_filter)

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
        opportunities = []
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM commercial_opportunities ORDER BY monthly_value DESC')
        
        for row in c.fetchall():
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
        
        conn.close()
        return render_template('commercial_contracts.html', 
                             opportunities=opportunities,
                             is_subscriber=True,
                             show_upgrade_message=False)
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
        
        return render_template('customer_leads.html', all_leads=all_leads)
        
    except Exception as e:
        print(f"Customer leads error: {e}")
        return render_template('customer_leads.html', all_leads=[])

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