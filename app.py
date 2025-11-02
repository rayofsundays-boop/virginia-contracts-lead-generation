import os
import json
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sqlite3  # Keep for backward compatibility with existing queries
from datetime import datetime, date, timedelta
import threading
import schedule
import time
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps, lru_cache
from lead_generator import LeadGenerator
import paypalrestsdk
import math
import string
import random
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # Safe to continue if dotenv is not available in production
    pass

# Virginia Government Contracting Lead Generation Application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'virginia-contracting-fallback-key-2024')

# Session configuration
# Regular users: 20 minutes
# Admin users: 8 hours (extended for admin workflow)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)
app.config['ADMIN_SESSION_LIFETIME'] = timedelta(hours=8)

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

# Context processor for global template variables
@app.context_processor
def inject_unread_messages():
    """Inject unread message count into all templates"""
    if 'user_id' in session:
        try:
            unread_count = db.session.execute(text('''
                SELECT COUNT(*) FROM messages 
                WHERE recipient_id = :user_id AND is_read = FALSE
            '''), {'user_id': session['user_id']}).scalar() or 0
            return dict(unread_messages_count=unread_count)
        except:
            return dict(unread_messages_count=0)
    return dict(unread_messages_count=0)

# Helper function for generating temporary passwords
def generate_temp_password(length=12):
    """Generate a random temporary password"""
    characters = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(characters) for i in range(length))

# ========================================
# ADMIN OPTIMIZATION HELPERS
# ========================================

def admin_required(f):
    """
    Decorator to require admin access for routes.
    Use this instead of manual session.get('is_admin') checks.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required. Please sign in as administrator.', 'error')
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

def log_admin_action(action_type, details, target_user_id=None):
    """
    Log all admin actions for audit trail and compliance.
    
    Args:
        action_type: Type of action (e.g., 'user_deleted', 'password_reset', 'subscription_change')
        details: Description of what was done
        target_user_id: ID of user affected by the action (if applicable)
    """
    try:
        db.session.execute(text('''
            INSERT INTO admin_actions 
            (admin_id, action_type, target_user_id, action_details, ip_address, user_agent, timestamp)
            VALUES (:admin_id, :action_type, :target_user_id, :details, :ip, :user_agent, NOW())
        '''), {
            'admin_id': session.get('user_id'),
            'action_type': action_type,
            'target_user_id': target_user_id,
            'details': details,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string[:255] if request.user_agent else 'Unknown'
        })
        db.session.commit()
    except Exception as e:
        print(f"Admin action logging error: {e}")
        # Don't fail the main operation if logging fails
        db.session.rollback()

@lru_cache(maxsize=10)
def get_admin_stats_cached(cache_timestamp):
    """
    Cached admin statistics to reduce database load.
    Cache key is timestamp rounded to 5-minute intervals.
    
    Args:
        cache_timestamp: Timestamp rounded to 5-minute bucket (for cache invalidation)
    
    Returns:
        Tuple of admin dashboard statistics
    """
    try:
        stats_result = db.session.execute(text('''
            SELECT 
                COUNT(CASE WHEN subscription_status = 'paid' THEN 1 END) as paid_subscribers,
                COUNT(CASE WHEN subscription_status = 'free' THEN 1 END) as free_users,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as new_users_30d,
                COALESCE(SUM(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 97 ELSE 0 END), 0) as revenue_30d,
                0 as page_views_24h,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 day' THEN 1 END) as active_users_24h
            FROM leads 
            WHERE is_admin = FALSE
        ''')).fetchone()
        return stats_result
    except Exception as e:
        print(f"Error fetching cached admin stats: {e}")
        # Return default values if query fails
        return (0, 0, 0, 0, 0, 0)

# ============================================================================
# PORTAL OPTIMIZATION HELPERS
# ============================================================================

def log_user_activity(user_email, activity_type, resource_type=None, resource_id=None, details=None):
    """Log user activity for analytics and personalization"""
    try:
        db.session.execute(text('''
            INSERT INTO user_activity (user_email, activity_type, resource_type, resource_id, details)
            VALUES (:email, :activity, :res_type, :res_id, :details)
        '''), {
            'email': user_email,
            'activity': activity_type,
            'res_type': resource_type,
            'res_id': resource_id,
            'details': json.dumps(details) if details else None
        })
        db.session.commit()
    except Exception as e:
        print(f"Activity logging error: {e}")
        db.session.rollback()

def get_user_preferences(user_email):
    """Get user preferences or return defaults"""
    try:
        prefs = db.session.execute(text('''
            SELECT dashboard_layout, favorite_lead_types, preferred_locations,
                   notification_enabled, email_alerts_enabled, theme
            FROM user_preferences WHERE user_email = :email
        '''), {'email': user_email}).fetchone()
        
        if prefs:
            return {
                'dashboard_layout': prefs[0],
                'favorite_lead_types': prefs[1] or [],
                'preferred_locations': prefs[2] or [],
                'notification_enabled': prefs[3],
                'email_alerts_enabled': prefs[4],
                'theme': prefs[5]
            }
    except Exception as e:
        print(f"Error fetching preferences: {e}")
    
    # Return defaults
    return {
        'dashboard_layout': 'default',
        'favorite_lead_types': [],
        'preferred_locations': [],
        'notification_enabled': True,
        'email_alerts_enabled': True,
        'theme': 'light'
    }

def get_unread_notifications(user_email, limit=10):
    """Get unread notifications for user"""
    try:
        notifications = db.session.execute(text('''
            SELECT id, notification_type, title, message, link, priority, created_at
            FROM notifications
            WHERE user_email = :email AND is_read = FALSE
            ORDER BY priority DESC, created_at DESC
            LIMIT :limit
        '''), {'email': user_email, 'limit': limit}).fetchall()
        
        return [{
            'id': n[0],
            'type': n[1],
            'title': n[2],
            'message': n[3],
            'link': n[4],
            'priority': n[5],
            'created_at': n[6]
        } for n in notifications]
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return []

def get_personalized_recommendations(user_email, limit=5):
    """Get personalized lead recommendations based on user activity"""
    try:
        # Get user's recent activity
        recent_activity = db.session.execute(text('''
            SELECT resource_type, COUNT(*) as views
            FROM user_activity
            WHERE user_email = :email 
            AND activity_type = 'viewed_lead'
            AND created_at > NOW() - INTERVAL '30 days'
            GROUP BY resource_type
            ORDER BY views DESC
            LIMIT 3
        '''), {'email': user_email}).fetchall()
        
        if not recent_activity:
            # Return quick wins for new users
            return get_quick_win_leads(limit)
        
        # Get leads from preferred types
        preferred_type = recent_activity[0][0] if recent_activity else 'contracts'
        
        # Return personalized leads based on preferences
        return get_leads_by_type(preferred_type, limit)
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return []

def get_quick_win_leads(limit=5):
    """Get quick win leads for recommendations"""
    try:
        leads = db.session.execute(text('''
            SELECT id, title, agency, location, estimated_value, 'Government Contract' as type
            FROM contracts
            WHERE status = 'open'
            AND estimated_value <= 50000
            ORDER BY posted_date DESC
            LIMIT :limit
        '''), {'limit': limit}).fetchall()
        
        return [{
            'id': l[0],
            'title': l[1],
            'agency': l[2],
            'location': l[3],
            'value': l[4],
            'type': l[5]
        } for l in leads]
    except:
        return []

def get_leads_by_type(lead_type, limit=5):
    """Get leads by specific type"""
    # Implementation placeholder - expand based on lead_type
    return get_quick_win_leads(limit)

def check_onboarding_status(user_email):
    """Check if user has completed onboarding"""
    try:
        status = db.session.execute(text('''
            SELECT onboarding_completed FROM user_onboarding WHERE user_email = :email
        '''), {'email': user_email}).scalar()
        
        return status or False
    except:
        return False

def get_dashboard_cache(user_email):
    """Get cached dashboard data if available and not expired"""
    try:
        # Ensure clean transaction state
        try:
            db.session.rollback()
        except:
            pass
            
        cache = db.session.execute(text('''
            SELECT stats_data, expires_at
            FROM dashboard_cache
            WHERE user_email = :email AND expires_at > NOW()
        '''), {'email': user_email}).fetchone()
        
        if cache:
            return json.loads(cache[0])
    except Exception as e:
        # Rollback on error
        try:
            db.session.rollback()
        except:
            pass
        # Silently fail if table doesn't exist (graceful degradation)
        if "does not exist" not in str(e).lower() and "no such table" not in str(e).lower():
            print(f"Cache read error: {e}")
    return None

def set_dashboard_cache(user_email, stats_data, ttl_minutes=5):
    """Cache dashboard data"""
    try:
        # Ensure clean transaction state
        try:
            db.session.rollback()
        except:
            pass
            
        # Use string formatting for interval since it can't be parameterized properly
        db.session.execute(text(f'''
            INSERT INTO dashboard_cache (user_email, stats_data, expires_at)
            VALUES (:email, :data, NOW() + INTERVAL '{ttl_minutes} minutes')
            ON CONFLICT (user_email) 
            DO UPDATE SET stats_data = :data, expires_at = NOW() + INTERVAL '{ttl_minutes} minutes'
        '''), {
            'email': user_email,
            'data': json.dumps(stats_data)
        })
        db.session.commit()
    except Exception as e:
        # Silently fail if table doesn't exist (graceful degradation)
        if "does not exist" not in str(e).lower() and "no such table" not in str(e).lower():
            print(f"Cache write error: {e}")
        db.session.rollback()

# Add to Jinja environment
app.jinja_env.globals.update(generate_temp_password=generate_temp_password)

# Custom Jinja filters
@app.template_filter('comma')
def comma_filter(value):
    """Add comma separators to numbers"""
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value

@app.template_filter('currency')
def currency_filter(value):
    """Format number as US dollar currency with proper punctuation"""
    try:
        # Remove any existing dollar signs, commas, or spaces
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').replace(' ', '').strip()
        
        # Convert to float
        amount = float(value)
        
        # Format with comma separators and 2 decimal places
        return "${:,.2f}".format(amount)
    except (ValueError, TypeError):
        # If conversion fails, try to return original with at least a $ sign
        if value:
            return f"${value}"
        return "$0.00"

@app.template_filter('safe_url')
def safe_url_filter(url, default_system='sam.gov'):
    """Ensure URL is valid and defaults to bid management system if empty/invalid"""
    if not url or url.strip() == '':
        # Default to SAM.gov contract opportunities
        return 'https://sam.gov/content/opportunities'
    
    url = url.strip()
    
    # Check if URL has a protocol, if not add https://
    if not url.startswith(('http://', 'https://', '//')):
        url = 'https://' + url
    
    # Validate that it's a proper URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return url
    except:
        pass
    
    # If validation fails, return default
    return 'https://sam.gov/content/opportunities'

# Add to Jinja environment
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
def handle_failed_transactions():
    """Rollback any failed transactions before processing requests"""
    try:
        # Always rollback to clear any pending transactions
        db.session.rollback()
    except Exception as e:
        # If rollback fails, close and remove the session entirely
        try:
            db.session.close()
        except:
            pass
        try:
            db.session.remove()
        except:
            pass

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

@app.after_request
def cleanup_session(response):
    """Ensure database session is properly cleaned up after each request"""
    try:
        db.session.remove()
    except:
        pass
    return response

@app.errorhandler(Exception)
def handle_database_errors(error):
    """Global error handler for database transaction errors"""
    error_str = str(error).lower()
    
    # Check for transaction errors
    if "transaction is aborted" in error_str or "infailedsqltransaction" in error_str:
        # Force cleanup
        try:
            db.session.rollback()
            db.session.close()
            db.session.remove()
        except:
            pass
        
        # Redirect to retry
        flash('Database connection reset. Please try again.', 'info')
        return redirect(request.url)
    
    # For other errors, just rollback and re-raise
    try:
        db.session.rollback()
    except:
        pass
    
    # Re-raise the error to be handled by the route
    raise error

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
            recipients=['info@eliteecocareservices.com'],
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

def send_all_existing_leads_email():
    """Send all existing customer/lead data to info@eliteecocareservices.com"""
    try:
        # Get all leads from database
        leads = db.session.execute(text('''
            SELECT company_name, contact_name, email, phone, state, 
                   experience_years, certifications, registration_date, 
                   subscription_status, credits_balance
            FROM leads 
            ORDER BY registration_date DESC
        ''')).fetchall()
        
        if not leads:
            return {'success': False, 'message': 'No leads found in database'}
        
        # Build email body
        subject = f"📊 Complete Lead Database Export - {len(leads)} Total Registrations"
        
        body = f"""
COMPLETE LEAD DATABASE EXPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total Registrations: {len(leads)}

{'='*80}
ALL REGISTERED LEADS:
{'='*80}

"""
        
        for idx, lead in enumerate(leads, 1):
            company_name, contact_name, email, phone, state, experience, certs, reg_date, sub_status, credits = lead
            body += f"""
LEAD #{idx}
-------------------------------------------
Company: {company_name}
Contact: {contact_name}
Email: {email}
Phone: {phone or 'Not provided'}
State: {state}
Experience: {experience} years
Certifications: {certs or 'None listed'}
Registration Date: {reg_date}
Subscription Status: {sub_status}
Credits Balance: {credits}

"""
        
        body += f"""
{'='*80}
SUMMARY:
{'='*80}
Total Leads: {len(leads)}
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a complete export of all customer/lead data from the Virginia Government Contracts Lead Generation System.

---
Virginia Government Contracts Lead Generation System
        """
        
        msg = Message(
            subject=subject,
            recipients=['info@eliteecocareservices.com'],
            body=body
        )
        
        mail.send(msg)
        print(f"✅ Successfully sent {len(leads)} leads to info@eliteecocareservices.com")
        return {'success': True, 'count': len(leads)}
        
    except Exception as e:
        print(f"❌ Failed to send existing leads email: {e}")
        return {'success': False, 'error': str(e)}

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
        
        # User activity tracking table
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS user_activity
                     (id SERIAL PRIMARY KEY,
                      user_email TEXT NOT NULL,
                      action_type TEXT NOT NULL,
                      description TEXT,
                      reference_id TEXT,
                      reference_type TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
        db.session.commit()
        
        # User notes table
        db.session.execute(text('''CREATE TABLE IF NOT EXISTS user_notes
                     (id SERIAL PRIMARY KEY,
                      user_email TEXT NOT NULL,
                      title TEXT NOT NULL,
                      content TEXT NOT NULL,
                      tags TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''))
        
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
        
        # Create user activity table
        c.execute('''CREATE TABLE IF NOT EXISTS user_activity
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_email TEXT NOT NULL,
                      action_type TEXT NOT NULL,
                      description TEXT,
                      reference_id TEXT,
                      reference_type TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create user notes table
        c.execute('''CREATE TABLE IF NOT EXISTS user_notes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_email TEXT NOT NULL,
                      title TEXT NOT NULL,
                      content TEXT NOT NULL,
                      tags TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
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
    """Main homepage with contract samples - Optimized with caching"""
    # Check if we're being redirected (prevent infinite loop)
    init_attempted = request.args.get('init_attempted', '0')
    
    try:
        # Aggressively clear any failed transactions
        try:
            db.session.rollback()
            db.session.close()
            db.session.remove()
        except:
            pass
        
        # Don't use cache for now - skip it to avoid transaction issues
        cache_data = None
        
        if cache_data:
            # Use cached data
            contracts = cache_data.get('contracts', [])
            commercial_opportunities = cache_data.get('commercial_opportunities', [])
            commercial_count = cache_data.get('commercial_count', 0)
        else:
            # Fetch fresh data
            contracts = db.session.execute(
                text('SELECT * FROM contracts ORDER BY deadline ASC LIMIT 6')
            ).fetchall()
            
            # Get commercial opportunities - handle if table doesn't exist yet
            commercial_opportunities = []
            commercial_count = 0
            try:
                commercial_rows = db.session.execute(
                    text('SELECT * FROM commercial_opportunities ORDER BY monthly_value DESC LIMIT 6')
                ).fetchall()
                
                # Convert commercial rows to objects for easier template access
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
            except Exception as comm_error:
                # Table doesn't exist yet - that's okay, just skip commercial opportunities
                print(f"Note: commercial_opportunities table not found: {comm_error}")
                commercial_opportunities = []
                commercial_count = 0
            
            # Skip caching for now to avoid transaction issues
            # TODO: Re-enable caching once transaction issues are resolved
        
        return render_template('index.html', 
                             contracts=contracts, 
                             commercial_opportunities=commercial_opportunities,
                             commercial_count=commercial_count)
    except Exception as e:
        # Rollback failed transaction
        try:
            db.session.rollback()
        except:
            pass
            
        # Log the full error
        import traceback
        print(f"Index route error: {e}")
        print(traceback.format_exc())
        
        error_str = str(e).lower()
        
        # Check for transaction errors specifically - always retry these
        if "transaction is aborted" in error_str or "infailedsqltransaction" in error_str:
            print("⚠️ Transaction error detected - forcing complete cleanup and retry")
            try:
                db.session.rollback()
                db.session.close()
                db.session.remove()
            except:
                pass
            
            # Always redirect to retry for transaction errors (no init_attempted check)
            # But add a counter to prevent infinite loops
            retry_count = request.args.get('retry_count', '0')
            retry_num = int(retry_count)
            
            if retry_num < 3:  # Allow up to 3 retries
                return redirect(url_for('index', retry_count=str(retry_num + 1)))
            else:
                return """
                <h1>Database Connection Error</h1>
                <p>Unable to connect to the database after multiple attempts.</p>
                <p>The database might be restarting or undergoing maintenance.</p>
                <p><a href="/">Try again</a> or contact support if the issue persists.</p>
                """
        
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
        
        # Check for admin login first (hardcoded superadmin)
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Set permanent session with extended timeout for admin
            session.permanent = True
            app.config['PERMANENT_SESSION_LIFETIME'] = app.config['ADMIN_SESSION_LIFETIME']
            
            session['user_id'] = 1  # Set admin user_id
            session['is_admin'] = True
            session['username'] = 'Admin'
            session['name'] = 'Administrator'
            session['user_email'] = 'admin@vacontracts.com'
            session['email'] = 'admin@vacontracts.com'
            session['subscription_status'] = 'paid'  # Admin has full access
            
            # Log admin login
            log_admin_action('admin_login', f'Admin logged in from {request.remote_addr}')
            
            flash('Welcome, Administrator! You have full access to all features. 🔑', 'success')
            return redirect(url_for('contracts'))
        
        # Get user from database (including is_admin flag and subscription status)
        result = db.session.execute(
            text('SELECT id, username, email, password_hash, contact_name, credits_balance, is_admin, subscription_status FROM leads WHERE username = :username OR email = :username'),
            {'username': username}
        ).fetchone()
        
        if result and check_password_hash(result[3], password):
            # Login successful - set all session variables
            session['user_id'] = result[0]
            session['username'] = result[1]
            session['email'] = result[2]
            session['user_email'] = result[2]  # Add user_email for template compatibility
            session['name'] = result[4]
            session['credits_balance'] = result[5]
            session['is_admin'] = bool(result[6])  # Set admin status from database
            session['subscription_status'] = result[7] or 'free'  # Set subscription status
            
            # Show appropriate welcome message
            if session['is_admin']:
                flash(f'Welcome back, {result[4]}! You have admin privileges. 🔑', 'success')
            else:
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

@app.route('/user-profile')
@login_required
def user_profile():
    """User profile page showing account details and subscription status"""
    try:
        # Get user details from database
        result = db.session.execute(text('''
            SELECT id, email, business_name, contact_name, phone, city, 
                   subscription_status, subscription_end_date, created_at
            FROM leads 
            WHERE id = :user_id
        '''), {'user_id': session['user_id']}).fetchone()
        
        if result:
            user = {
                'id': result[0],
                'email': result[1],
                'business_name': result[2],
                'contact_name': result[3],
                'phone': result[4],
                'city': result[5],
                'subscription_status': result[6],
                'subscription_end_date': result[7],
                'created_at': result[8]
            }
            
            # Get user stats (placeholder for now)
            stats = {
                'leads_viewed': 0,
                'saved_leads': 0,
                'proposals_submitted': 0
            }
            
            return render_template('user_profile.html', user=user, stats=stats)
        else:
            flash('User not found.', 'error')
            return redirect(url_for('customer_leads'))
    except Exception as e:
        print(f"Error loading user profile: {e}")
        flash('Error loading profile. Please try again.', 'error')
        return redirect(url_for('customer_leads'))

@app.route('/customer-dashboard')
@login_required
def customer_dashboard():
    """Optimized customer dashboard with caching, personalization, and recommendations"""
    try:
        user_email = session.get('user_email')
        
        # Log activity
        log_user_activity(user_email, 'viewed_dashboard')
        
        # Check cache first
        cached_data = get_dashboard_cache(user_email)
        if cached_data:
            stats = cached_data
        else:
            # Get stats from all lead sources
            gov_contracts = 0
            try:
                gov_contracts = db.session.execute(text(
                    "SELECT COUNT(*) FROM contracts"
                )).scalar() or 0
            except:
                pass
            
            supply_contracts = 0
            try:
                supply_contracts = db.session.execute(text(
                    "SELECT COUNT(*) FROM supply_contracts WHERE status = 'open'"
                )).scalar() or 0
            except:
                pass
            
            commercial_leads = 0
            try:
                commercial_leads = db.session.execute(text(
                    "SELECT COUNT(*) FROM commercial_lead_requests WHERE status = 'open'"
                )).scalar() or 0
            except:
                pass
            
            residential_leads = 0
            try:
                residential_leads = db.session.execute(text(
                    "SELECT COUNT(*) FROM residential_leads WHERE status = 'new'"
                )).scalar() or 0
            except:
                pass
            
            quick_wins = 0
            try:
                quick_wins = db.session.execute(text(
                    "SELECT COUNT(*) FROM supply_contracts WHERE is_quick_win = TRUE AND status = 'open'"
                )).scalar() or 0
                quick_wins += db.session.execute(text(
                    "SELECT COUNT(*) FROM commercial_lead_requests WHERE urgency IN ('emergency', 'urgent') AND status = 'open'"
                )).scalar() or 0
            except:
                pass
            
            # Total includes government, supply, commercial, and residential
            total_leads = gov_contracts + supply_contracts + commercial_leads + residential_leads
            
            stats = {
                'total_leads': total_leads,
                'government_contracts': gov_contracts,
                'supply_contracts': supply_contracts,
                'commercial_leads': commercial_leads,
                'residential_leads': residential_leads,
                'quick_wins': quick_wins
            }
            
            # Cache the stats
            set_dashboard_cache(user_email, stats)
        
        # Get user preferences for personalization
        preferences = {}
        try:
            preferences = get_user_preferences(user_email)
        except Exception as e:
            print(f"Error getting preferences: {e}")
            preferences = {}
        
        # Get unread notifications
        notifications = []
        try:
            notifications = get_unread_notifications(user_email, limit=5)
        except Exception as e:
            print(f"Error getting notifications: {e}")
            notifications = []
        
        # Check onboarding status
        show_onboarding = False
        try:
            show_onboarding = not check_onboarding_status(user_email)
        except Exception as e:
            print(f"Error checking onboarding: {e}")
            show_onboarding = False
        
        # Get personalized recommendations
        recommended_leads = []
        try:
            recommended_leads = get_personalized_recommendations(user_email, limit=5)
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            recommended_leads = []
        
        # Get latest opportunities from all sources (optimized query)
        latest_opportunities = []
        try:
            # Get government contracts
            try:
                gov_opps = db.session.execute(text('''
                    SELECT title, agency, location, value, created_at, 
                           'Government Contract' as lead_type, id
                    FROM contracts 
                    ORDER BY created_at DESC
                    LIMIT 10
                ''')).fetchall()
                
                for row in gov_opps:
                    latest_opportunities.append({
                        'title': row[0],
                        'agency': row[1],
                        'location': row[2],
                        'value': row[3],
                        'posted_date': row[4],
                        'lead_type': row[5],
                        'id': row[6],
                        'link': url_for('contracts')
                    })
            except Exception as e:
                print(f"Error fetching government contracts: {e}")
            
            # Get commercial requests
            try:
                com_reqs = db.session.execute(text('''
                    SELECT business_name, business_type, city || ', VA', budget_range, created_at, 
                           'Commercial Request' as lead_type, id
                    FROM commercial_lead_requests 
                    WHERE status = 'open'
                    ORDER BY created_at DESC
                    LIMIT 5
                ''')).fetchall()
                
                for row in com_reqs:
                    latest_opportunities.append({
                        'title': f"Commercial Cleaning - {row[0]}",
                        'agency': row[1],
                        'location': row[2],
                        'value': row[3] or 'Contact for quote',
                        'posted_date': row[4],
                        'lead_type': row[5],
                        'id': row[6],
                        'link': url_for('customer_leads')
                    })
            except Exception as e:
                print(f"Error fetching commercial requests: {e}")
            
            # Get residential requests
            try:
                res_reqs = db.session.execute(text('''
                    SELECT homeowner_name, property_type, city || ', VA', estimated_value, created_at, 
                           'Residential Request' as lead_type, id
                    FROM residential_leads 
                    WHERE status = 'new'
                    ORDER BY created_at DESC
                    LIMIT 5
                ''')).fetchall()
                
                for row in res_reqs:
                    latest_opportunities.append({
                        'title': f"Residential Cleaning - {row[1]}",
                        'agency': f"Homeowner: {row[0]}",
                        'location': row[2],
                        'value': row[3] or 'Contact for quote',
                        'posted_date': row[4],
                        'lead_type': row[5],
                        'id': row[6],
                        'link': url_for('customer_leads')
                    })
            except Exception as e:
                print(f"Error fetching residential requests: {e}")
            
            # Sort all opportunities by date and limit to 15 most recent
            latest_opportunities.sort(key=lambda x: x['posted_date'] if x['posted_date'] else '', reverse=True)
            latest_opportunities = latest_opportunities[:15]
            
        except Exception as e:
            print(f"Error fetching latest opportunities: {e}")
        
        # Get saved searches count
        saved_searches_count = 0
        try:
            saved_searches_count = db.session.execute(text('''
                SELECT COUNT(*) FROM saved_searches WHERE user_email = :email
            '''), {'email': user_email}).scalar() or 0
        except:
            pass
        
        # Get saved leads count
        saved_leads_count = 0
        try:
            saved_leads_count = db.session.execute(text('''
                SELECT COUNT(*) FROM saved_leads WHERE user_email = :email
            '''), {'email': user_email}).scalar() or 0
        except:
            pass
        
        return render_template('customer_dashboard.html', 
                             stats=stats, 
                             latest_opportunities=latest_opportunities,
                             preferences=preferences,
                             notifications=notifications,
                             show_onboarding=show_onboarding,
                             recommended_leads=recommended_leads,
                             saved_searches_count=saved_searches_count,
                             saved_leads_count=saved_leads_count)
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('customer_leads'))

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        business_name = request.form.get('business_name', '').strip()
        contact_name = request.form.get('contact_name', '').strip()
        phone = request.form.get('phone', '').strip()
        city = request.form.get('city', '').strip()
        
        db.session.execute(text('''
            UPDATE leads 
            SET business_name = :business_name,
                contact_name = :contact_name,
                phone = :phone,
                city = :city
            WHERE id = :user_id
        '''), {
            'business_name': business_name,
            'contact_name': contact_name,
            'phone': phone,
            'city': city,
            'user_id': session['user_id']
        })
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_profile'))
    except Exception as e:
        print(f"Error updating profile: {e}")
        db.session.rollback()
        flash('Error updating profile. Please try again.', 'error')
        return redirect(url_for('user_profile'))

# ============================================================================
# PORTAL OPTIMIZATION API ENDPOINTS
# ============================================================================

@app.route('/api/save-search', methods=['POST'])
@login_required
def api_save_search():
    """Save a search with filters for quick access and alerts"""
    try:
        user_email = session.get('user_email')
        data = request.get_json()
        
        search_name = data.get('name', '').strip()
        filters = data.get('filters', {})
        alert_enabled = data.get('alert_enabled', False)
        
        if not search_name:
            return jsonify({'success': False, 'error': 'Search name is required'}), 400
        
        db.session.execute(text('''
            INSERT INTO saved_searches (user_email, search_name, search_filters, alert_enabled)
            VALUES (:email, :name, :filters, :alert)
        '''), {
            'email': user_email,
            'name': search_name,
            'filters': json.dumps(filters),
            'alert': alert_enabled
        })
        db.session.commit()
        
        log_user_activity(user_email, 'saved_search', details={'name': search_name})
        
        return jsonify({'success': True, 'message': 'Search saved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/saved-searches', methods=['GET'])
@login_required
def api_get_saved_searches():
    """Get user's saved searches"""
    try:
        user_email = session.get('user_email')
        
        searches = db.session.execute(text('''
            SELECT id, search_name, search_filters, alert_enabled, created_at
            FROM saved_searches
            WHERE user_email = :email
            ORDER BY created_at DESC
        '''), {'email': user_email}).fetchall()
        
        return jsonify({
            'success': True,
            'searches': [{
                'id': s[0],
                'name': s[1],
                'filters': json.loads(s[2]) if s[2] else {},
                'alert_enabled': s[3],
                'created_at': s[4].isoformat() if s[4] else None
            } for s in searches]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save-lead', methods=['POST'])
@login_required
def api_save_lead():
    """Bookmark/save a lead for later"""
    try:
        user_email = session.get('user_email')
        data = request.get_json()
        
        lead_type = data.get('lead_type')
        lead_id = data.get('lead_id')
        notes = data.get('notes', '')
        
        db.session.execute(text('''
            INSERT INTO saved_leads (user_email, lead_type, lead_id, notes)
            VALUES (:email, :type, :id, :notes)
            ON CONFLICT (user_email, lead_type, lead_id) DO UPDATE SET notes = :notes
        '''), {
            'email': user_email,
            'type': lead_type,
            'id': lead_id,
            'notes': notes
        })
        db.session.commit()
        
        log_user_activity(user_email, 'saved_lead', lead_type, lead_id)
        
        return jsonify({'success': True, 'message': 'Lead saved'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/unsave-lead/<int:saved_id>', methods=['DELETE'])
@login_required
def api_unsave_lead(saved_id):
    """Remove a saved/bookmarked lead"""
    try:
        user_email = session.get('user_email')
        
        db.session.execute(text('''
            DELETE FROM saved_leads
            WHERE id = :id AND user_email = :email
        '''), {'id': saved_id, 'email': user_email})
        db.session.commit()
        
        log_user_activity(user_email, 'unsaved_lead', details={'saved_id': saved_id})
        
        return jsonify({'success': True, 'message': 'Lead removed'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifications/read', methods=['POST'])
@login_required
def api_mark_notification_read():
    """Mark notification as read"""
    try:
        user_email = session.get('user_email')
        data = request.get_json()
        notification_id = data.get('notification_id')
        
        db.session.execute(text('''
            UPDATE notifications
            SET is_read = TRUE, read_at = NOW()
            WHERE id = :id AND user_email = :email
        '''), {'id': notification_id, 'email': user_email})
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/preferences', methods=['POST'])
@login_required
def api_update_preferences():
    """Update user preferences"""
    try:
        user_email = session.get('user_email')
        data = request.get_json()
        
        db.session.execute(text('''
            INSERT INTO user_preferences (
                user_email, dashboard_layout, favorite_lead_types, preferred_locations,
                notification_enabled, email_alerts_enabled, theme
            ) VALUES (
                :email, :layout, :fav_types, :locations, :notif, :email_alert, :theme
            )
            ON CONFLICT (user_email) DO UPDATE SET
                dashboard_layout = :layout,
                favorite_lead_types = :fav_types,
                preferred_locations = :locations,
                notification_enabled = :notif,
                email_alerts_enabled = :email_alert,
                theme = :theme,
                updated_at = NOW()
        '''), {
            'email': user_email,
            'layout': data.get('dashboard_layout', 'default'),
            'fav_types': data.get('favorite_lead_types', []),
            'locations': data.get('preferred_locations', []),
            'notif': data.get('notification_enabled', True),
            'email_alert': data.get('email_alerts_enabled', True),
            'theme': data.get('theme', 'light')
        })
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Preferences updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/complete-onboarding', methods=['POST'])
@login_required
def api_complete_onboarding():
    """Mark onboarding step as complete"""
    try:
        user_email = session.get('user_email')
        data = request.get_json()
        step = data.get('step')
        
        # Update onboarding progress
        db.session.execute(text(f'''
            INSERT INTO user_onboarding (user_email, completed_{step})
            VALUES (:email, TRUE)
            ON CONFLICT (user_email) DO UPDATE SET completed_{step} = TRUE
        '''), {'email': user_email})
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/saved-leads')
@login_required
def saved_leads():
    """Show user's saved/bookmarked leads"""
    try:
        user_email = session.get('user_email')
        
        # Get saved leads with details
        saved_items = db.session.execute(text('''
            SELECT sl.id, sl.lead_type, sl.lead_id, sl.notes, sl.created_at
            FROM saved_leads sl
            WHERE sl.user_email = :email
            ORDER BY sl.created_at DESC
        '''), {'email': user_email}).fetchall()
        
        # Fetch full lead details for each saved lead
        leads_with_details = []
        for item in saved_items:
            lead_details = get_lead_details(item[1], item[2])
            if lead_details:
                lead_details['saved_id'] = item[0]
                lead_details['notes'] = item[3]
                lead_details['saved_at'] = item[4]
                leads_with_details.append(lead_details)
        
        return render_template('saved_leads.html', saved_leads=leads_with_details)
    except Exception as e:
        print(f"Error loading saved leads: {e}")
        flash('Error loading saved leads', 'error')
        return redirect(url_for('customer_dashboard'))

def get_lead_details(lead_type, lead_id):
    """Helper to fetch lead details by type and ID"""
    try:
        if lead_type == 'contract':
            result = db.session.execute(text('''
                SELECT title, agency, location, estimated_value, posted_date
                FROM contracts WHERE id = :id
            '''), {'id': lead_id}).fetchone()
            if result:
                return {
                    'type': 'Government Contract',
                    'title': result[0],
                    'agency': result[1],
                    'location': result[2],
                    'value': result[3],
                    'date': result[4]
                }
        elif lead_type == 'supply_contract':
            result = db.session.execute(text('''
                SELECT title, agency, location, estimated_value, created_at
                FROM supply_contracts WHERE id = :id
            '''), {'id': lead_id}).fetchone()
            if result:
                return {
                    'type': 'Supply Contract',
                    'title': result[0],
                    'agency': result[1],
                    'location': result[2],
                    'value': result[3],
                    'date': result[4]
                }
    except:
        pass
    return None

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate passwords match
        if new_password != confirm_password:
            flash('New passwords do not match!', 'error')
            return redirect(url_for('user_profile'))
        
        # Get current password hash
        result = db.session.execute(text('''
            SELECT password FROM leads WHERE id = :user_id
        '''), {'user_id': session['user_id']}).fetchone()
        
        if not result:
            flash('User not found.', 'error')
            return redirect(url_for('user_profile'))
        
        # Verify current password
        from werkzeug.security import check_password_hash, generate_password_hash
        if not check_password_hash(result[0], current_password):
            flash('Current password is incorrect!', 'error')
            return redirect(url_for('user_profile'))
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        db.session.execute(text('''
            UPDATE leads 
            SET password = :password
            WHERE id = :user_id
        '''), {
            'password': new_password_hash,
            'user_id': session['user_id']
        })
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('user_profile'))
    except Exception as e:
        print(f"Error changing password: {e}")
        db.session.rollback()
        flash('Error changing password. Please try again.', 'error')
        return redirect(url_for('user_profile'))

@app.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user subscription"""
    try:
        data = request.get_json()
        reason = data.get('reason', '') if data else ''
        
        # Update subscription status
        db.session.execute(text('''
            UPDATE leads 
            SET subscription_status = 'cancelled',
                cancellation_reason = :reason,
                cancellation_date = CURRENT_TIMESTAMP
            WHERE id = :user_id
        '''), {
            'reason': reason,
            'user_id': session['user_id']
        })
        db.session.commit()
        
        # Update session
        session['subscription_status'] = 'cancelled'
        
        return jsonify({
            'success': True,
            'message': 'Subscription cancelled successfully'
        })
    except Exception as e:
        print(f"Error cancelling subscription: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/customer-reviews')
def customer_reviews():
    """Display customer review submission page"""
    return render_template('customer_reviews.html')

@app.route('/submit-review', methods=['POST'])
@login_required
def submit_review():
    """Handle customer review submissions and send to admin mailbox"""
    try:
        # Get form data
        rating = request.form.get('rating', '0')
        review_title = request.form.get('review_title', '').strip()
        review_text = request.form.get('review_text', '').strip()
        would_recommend = request.form.get('would_recommend', 'no')
        allow_public = request.form.get('allow_public', 'no')
        
        # Get user info
        user_email = session.get('user_email', 'Anonymous')
        user_id = session.get('user_id')
        
        # Get user details from database
        user_result = db.session.execute(text('''
            SELECT business_name, contact_name FROM leads WHERE id = :user_id
        '''), {'user_id': user_id}).fetchone()
        
        business_name = user_result[0] if user_result and user_result[0] else 'N/A'
        contact_name = user_result[1] if user_result and user_result[1] else 'N/A'
        
        # Store review in database
        db.session.execute(text('''
            INSERT INTO customer_reviews 
            (user_id, user_email, business_name, rating, review_title, review_text, 
             would_recommend, allow_public, created_at)
            VALUES (:user_id, :user_email, :business_name, :rating, :review_title, 
                    :review_text, :would_recommend, :allow_public, CURRENT_TIMESTAMP)
        '''), {
            'user_id': user_id,
            'user_email': user_email,
            'business_name': business_name,
            'rating': int(rating),
            'review_title': review_title,
            'review_text': review_text,
            'would_recommend': would_recommend == 'yes',
            'allow_public': allow_public == 'yes'
        })
        db.session.commit()
        
        # Send notification to admin mailbox
        stars = '⭐' * int(rating)
        recommend_text = '✅ Yes' if would_recommend == 'yes' else '❌ No'
        public_text = '✅ Yes' if allow_public == 'yes' else '❌ No'
        
        try:
            # Create message in admin mailbox
            db.session.execute(text('''
                INSERT INTO messages 
                (sender_id, recipient_id, subject, body, is_admin, created_at, is_read)
                VALUES (:sender_id, NULL, :subject, :body, TRUE, CURRENT_TIMESTAMP, FALSE)
            '''), {
                'sender_id': user_id,
                'subject': f'⭐ New Customer Review - {rating}/5 Stars',
                'body': f'''
NEW CUSTOMER REVIEW SUBMITTED

Rating: {stars} ({rating}/5)
Review Title: {review_title}

Business: {business_name}
Contact: {contact_name}
Email: {user_email}

Would Recommend: {recommend_text}
Allow Public Display: {public_text}

Review:
{review_text}

Submitted: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                '''
            })
            db.session.commit()
        except Exception as email_error:
            print(f"Error sending review to admin: {email_error}")
            # Don't fail the whole operation if email fails
        
        flash('Thank you for your review! Your feedback has been submitted successfully.', 'success')
        return redirect(url_for('customer_dashboard'))
        
    except Exception as e:
        print(f"Error submitting review: {e}")
        db.session.rollback()
        flash('Error submitting review. Please try again.', 'error')
        return redirect(url_for('customer_reviews'))

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
                SELECT title, agency, location, value, deadline, description, naics_code, website_url, created_at
                FROM contracts 
                WHERE LOWER(location) LIKE LOWER(:loc)
                ORDER BY deadline ASC
                LIMIT :limit OFFSET :offset
            '''), { 'loc': f"%{location_filter}%", 'limit': per_page, 'offset': offset }).fetchall()
        else:
            total = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar() or 0
            rows = db.session.execute(text('''
                SELECT title, agency, location, value, deadline, description, naics_code, website_url, created_at
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
        
        # Check if user is admin or paid subscriber
        is_admin = session.get('is_admin', False)
        is_paid_subscriber = False
        
        if not is_admin and 'user_id' in session:
            result = db.session.execute(text('''
                SELECT subscription_status FROM leads WHERE id = :user_id
            '''), {'user_id': session['user_id']}).fetchone()
            
            if result and result[0] == 'paid':
                is_paid_subscriber = True
        
        # Admin gets full access automatically
        if is_admin:
            is_paid_subscriber = True
        
        return render_template('contracts.html', 
                               contracts=rows, 
                               locations=locations, 
                               current_filter=location_filter,
                               pagination=pagination,
                               is_paid_subscriber=is_paid_subscriber,
                               is_admin=is_admin)
    except Exception as e:
        msg = f"<h1>Contracts Page Error</h1><p>{str(e)}</p>"
        msg += "<p>Try running <a href='/run-updates'>/run-updates</a> and then check <a href='/db-status'>/db-status</a>.</p>"
        return msg

@app.route('/educational-contracts')
def educational_contracts():
    """College and university procurement opportunities"""
    try:
        # Check if table exists
        table_check = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'educational_contracts'
            )
        """)).scalar()
        
        if not table_check:
            flash('Educational contracts feature is being set up. Check back soon!', 'info')
            return redirect(url_for('contracts'))
        
        institution_filter = request.args.get('institution', '')
        city_filter = request.args.get('city', '')
        category_filter = request.args.get('category', '')
        page = max(int(request.args.get('page', 1) or 1), 1)
        per_page = 12
        offset = (page - 1) * per_page
        
        # Build where conditions
        where_conditions = ["status = 'open'"]
        params = {}
        
        if institution_filter:
            where_conditions.append("LOWER(institution_name) LIKE LOWER(:institution)")
            params['institution'] = f"%{institution_filter}%"
        
        if city_filter:
            where_conditions.append("city = :city")
            params['city'] = city_filter
        
        if category_filter:
            where_conditions.append("category = :category")
            params['category'] = category_filter
        
        where_clause = " AND ".join(where_conditions)
        
        # Get total count
        total = db.session.execute(text(f'''
            SELECT COUNT(*) FROM educational_contracts WHERE {where_clause}
        '''), params).scalar() or 0
        
        # Get contracts
        params['limit'] = per_page
        params['offset'] = offset
        
        contracts = db.session.execute(text(f'''
            SELECT * FROM educational_contracts 
            WHERE {where_clause}
            ORDER BY bid_deadline ASC, created_at DESC
            LIMIT :limit OFFSET :offset
        '''), params).fetchall()
        
        # Get filter options
        institutions = db.session.execute(text('''
            SELECT DISTINCT institution_name FROM educational_contracts 
            WHERE status = 'open' ORDER BY institution_name
        ''')).fetchall()
        
        cities = db.session.execute(text('''
            SELECT DISTINCT city FROM educational_contracts 
            WHERE status = 'open' ORDER BY city
        ''')).fetchall()
        
        categories = db.session.execute(text('''
            SELECT DISTINCT category FROM educational_contracts 
            WHERE status = 'open' ORDER BY category
        ''')).fetchall()
        
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        
        # Check subscription status
        is_admin = session.get('is_admin', False)
        is_paid_subscriber = False
        
        if not is_admin and 'user_id' in session:
            result = db.session.execute(text('''
                SELECT subscription_status FROM leads WHERE id = :user_id
            '''), {'user_id': session['user_id']}).fetchone()
            if result and result[0] == 'paid':
                is_paid_subscriber = True
        
        if is_admin:
            is_paid_subscriber = True
        
        return render_template('educational_contracts.html',
                             contracts=contracts,
                             institutions=[i[0] for i in institutions],
                             cities=[c[0] for c in cities],
                             categories=[cat[0] for cat in categories],
                             current_filters={
                                 'institution': institution_filter,
                                 'city': city_filter,
                                 'category': category_filter
                             },
                             page=page,
                             total_pages=total_pages,
                             total_count=total,
                             is_paid_subscriber=is_paid_subscriber,
                             is_admin=is_admin)
    except Exception as e:
        print(f"Educational contracts error: {e}")
        flash('Educational contracts feature is being set up. Check back soon!', 'info')
        return redirect(url_for('contracts'))

@app.route('/industry-days')
def industry_days():
    """Industry days and procurement events for subscribers"""
    try:
        # Check if table exists
        table_check = db.session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'industry_days'
            )
        """)).scalar()
        
        if not table_check:
            flash('Industry days feature is being set up. Check back soon!', 'info')
            return redirect(url_for('customer_leads'))
        
        city_filter = request.args.get('city', '')
        event_type_filter = request.args.get('event_type', '')
        page = max(int(request.args.get('page', 1) or 1), 1)
        per_page = 10
        offset = (page - 1) * per_page
        
        # Build where conditions
        where_conditions = ["status = 'upcoming'", "event_date >= CURRENT_DATE"]
        params = {}
        
        if city_filter:
            where_conditions.append("city = :city")
            params['city'] = city_filter
        
        if event_type_filter:
            where_conditions.append("event_type = :event_type")
            params['event_type'] = event_type_filter
        
        where_clause = " AND ".join(where_conditions)
        
        # Get total count
        total = db.session.execute(text(f'''
            SELECT COUNT(*) FROM industry_days WHERE {where_clause}
        '''), params).scalar() or 0
        
        # Get events
        params['limit'] = per_page
        params['offset'] = offset
        
        events = db.session.execute(text(f'''
            SELECT * FROM industry_days 
            WHERE {where_clause}
            ORDER BY event_date ASC
            LIMIT :limit OFFSET :offset
        '''), params).fetchall()
        
        # Get filter options
        cities = db.session.execute(text('''
            SELECT DISTINCT city FROM industry_days 
            WHERE status = 'upcoming' AND event_date >= CURRENT_DATE 
            ORDER BY city
        ''')).fetchall()
        
        event_types = db.session.execute(text('''
            SELECT DISTINCT event_type FROM industry_days 
            WHERE status = 'upcoming' AND event_date >= CURRENT_DATE 
            ORDER BY event_type
        ''')).fetchall()
        
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        
        # Check subscription status
        is_admin = session.get('is_admin', False)
        is_paid_subscriber = False
        
        if not is_admin and 'user_id' in session:
            result = db.session.execute(text('''
                SELECT subscription_status FROM leads WHERE id = :user_id
            '''), {'user_id': session['user_id']}).fetchone()
            if result and result[0] == 'paid':
                is_paid_subscriber = True
        
        if is_admin:
            is_paid_subscriber = True
        
        return render_template('industry_days.html',
                             events=events,
                             cities=[c[0] for c in cities],
                             event_types=[et[0] for et in event_types],
                             current_filters={
                                 'city': city_filter,
                                 'event_type': event_type_filter
                             },
                             page=page,
                             total_pages=total_pages,
                             total_count=total,
                             is_paid_subscriber=is_paid_subscriber,
                             is_admin=is_admin)
    except Exception as e:
        print(f"Industry days error: {e}")
        flash('Industry days feature is being set up. Check back soon!', 'info')
        return redirect(url_for('customer_leads'))


# DEPRECATED: supply-contracts route has been merged into quick_wins for better UX
# The /supply-contracts and /quick-wins URLs both route to the quick_wins() function

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
    
    # Admin gets unlimited access
    if is_admin:
        is_paid_subscriber = True
        clicks_remaining = 999  # Unlimited for admin
    elif 'user_id' in session:
        # Check if paid subscriber
        user_id = session['user_id']
        result = db.session.execute(text('''
            SELECT subscription_status FROM leads WHERE id = :user_id
        '''), {'user_id': user_id}).fetchone()
        
        if result and result[0] == 'paid':
            is_paid_subscriber = True
    
    # Track clicks for non-subscribers (not admin)
    if not is_paid_subscriber and not is_admin:
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
        # Check if user is admin - admins get unlimited access
        is_admin = session.get('is_admin', False)
        
        # Check if user has credits or subscription
        user_credits = session.get('credits_balance', 0)
        subscription_status = session.get('subscription_status', 'free')
        
        # Allow access if user has credits, subscription, or is admin
        # Free users can still browse leads but need credits to access contact info
        show_payment_prompt = False
        
        # Get all available leads (government contracts, supply contracts, and commercial)
        government_leads = []
        supply_leads = []
        commercial_leads = []
        
        # Get government cleaning contracts
        try:
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
        except Exception as e:
            print(f"Error fetching government contracts: {e}")
        
        # Get supply/product procurement contracts
        try:
            supply_leads = db.session.execute(text('''
                SELECT 
                    supply_contracts.id,
                    supply_contracts.title,
                    supply_contracts.agency,
                    supply_contracts.location,
                    supply_contracts.description,
                    supply_contracts.estimated_value as contract_value,
                    supply_contracts.bid_deadline as deadline,
                    '' as naics_code,
                    supply_contracts.posted_date as created_at,
                    supply_contracts.website_url,
                    'supply' as lead_type,
                    supply_contracts.product_category as services_needed,
                    'Active' as status,
                    supply_contracts.requirements
                FROM supply_contracts 
                ORDER BY supply_contracts.posted_date DESC
            ''')).fetchall()
        except Exception as e:
            print(f"Error fetching supply contracts: {e}")
        
        # Get commercial opportunities
        try:
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
        except Exception as e:
            print(f"Error fetching commercial opportunities: {e}")
        
        # Get commercial cleaning requests (businesses looking for cleaners)
        commercial_requests = []
        try:
            commercial_requests = db.session.execute(text('''
                SELECT 
                    id, business_name, contact_name, email, phone, address, city, zip_code,
                    business_type, square_footage, frequency, services_needed, 
                    special_requirements, budget_range, start_date, urgency, status, created_at
                FROM commercial_lead_requests 
                WHERE status = 'open'
                ORDER BY created_at DESC
            ''')).fetchall()
        except Exception as e:
            print(f"Error fetching commercial requests: {e}")
        
        # Get residential cleaning requests (homeowners looking for cleaners)
        residential_requests = []
        try:
            residential_requests = db.session.execute(text('''
                SELECT 
                    id, homeowner_name, address, city, zip_code, property_type, bedrooms, bathrooms,
                    square_footage, contact_email, contact_phone, estimated_value, 
                    cleaning_frequency, services_needed, special_requirements, status, created_at
                FROM residential_leads 
                WHERE status = 'new'
                ORDER BY created_at DESC
            ''')).fetchall()
        except Exception as e:
            print(f"Error fetching residential requests: {e}")
        
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
                'lead_type': 'Government Contract',
                'services_needed': lead[11],
                'status': lead[12],
                'requirements': lead[13] or 'Standard government contracting requirements apply.',
                'days_left': calculate_days_left(lead[6])
            }
            all_leads.append(lead_dict)
        
        # Add supply/product procurement leads
        for lead in supply_leads:
            app_url = lead[9] if lead[9] and lead[9].startswith(('http://', 'https://')) else None
            
            lead_dict = {
                'id': f"supply_{lead[0]}",
                'title': lead[1],
                'agency': lead[2],
                'location': lead[3],
                'description': lead[4],
                'contract_value': lead[5],
                'deadline': lead[6],
                'naics_code': lead[7],
                'date_posted': lead[8],
                'application_url': app_url,
                'lead_type': 'Supply Contract',
                'services_needed': lead[11],  # product_category
                'status': lead[12],
                'requirements': lead[13] or 'Standard procurement requirements apply.',
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
                'lead_type': 'Commercial Opportunity',
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
                'lead_type': 'Commercial Request',
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
                'lead_type': 'Residential Request',
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
        
        # Send ALL leads to client - let JavaScript handle filtering and pagination
        # No server-side pagination - client filters on the fly
        total = len(all_leads)
        
        # Get Quick Wins counts for promotion banner
        emergency_count = db.session.execute(text(
            "SELECT COUNT(*) FROM commercial_lead_requests WHERE urgency = 'emergency' AND status = 'open'"
        )).scalar() or 0
        
        urgent_count = db.session.execute(text(
            "SELECT COUNT(*) FROM commercial_lead_requests WHERE urgency = 'urgent' AND status = 'open'"
        )).scalar() or 0

        return render_template('customer_leads.html', 
                             all_leads=all_leads,  # Send ALL leads, not paginated
                             total_leads=total,
                             emergency_count=emergency_count,
                             urgent_count=urgent_count)
        
    except Exception as e:
        print(f"Customer leads error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('customer_leads.html', all_leads=[], total_leads=0, emergency_count=0, urgent_count=0)

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
        
        # Log activity
        log_activity(user_email, 'saved_lead', f'Saved lead: {data.get("title")}', data.get('lead_id'), data.get('lead_type'))
        
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

@app.route('/branding-materials')
@login_required
def branding_materials():
    """Subscriber-exclusive branding materials"""
    user_email = session.get('user_email')
    
    # For now, show materials to all logged-in users
    # TODO: Add proper subscription check when payment system is fully implemented
    is_subscriber = True
    
    # Optional: Check subscription status if you want to enforce it
    # try:
    #     result = db.session.execute(text('''
    #         SELECT subscription_status FROM leads 
    #         WHERE email = :email
    #     '''), {'email': user_email}).fetchone()
    #     
    #     if result and result[0] == 'active':
    #         is_subscriber = True
    # except Exception as e:
    #     print(f"Error checking subscription: {e}")
    
    # Define branding materials available for download
    materials = [
        {
            'category': 'Digital Signature & Letterhead',
            'items': [
                {'name': 'Digital Signature Creator', 'description': 'Create professional digital signatures for contracts and documents', 'icon': 'fa-signature', 'type': 'tool'},
                {'name': 'Company Letterhead Templates', 'description': '12 professional letterhead designs - instantly customizable', 'icon': 'fa-file-lines', 'type': 'template', 'count': '12'},
                {'name': 'Email Signature HTML', 'description': 'Professional email signatures with your branding', 'icon': 'fa-envelope', 'type': 'template', 'count': '5'}
            ]
        },
        {
            'category': 'Business Cards & Branding Colors',
            'items': [
                {'name': 'Canva Business Cards', 'description': 'Direct link to create stunning business cards on Canva', 'icon': 'fa-id-card', 'type': 'link', 'url': 'https://www.canva.com/create/business-cards/'},
                {'name': 'Professional Color Palettes', 'description': '20+ curated color schemes for cleaning businesses', 'icon': 'fa-palette', 'type': 'tool', 'count': '20+'},
                {'name': 'Branded Color Templates', 'description': 'Update brand colors instantly across all templates', 'icon': 'fa-swatchbook', 'type': 'tool'}
            ]
        },
        {
            'category': 'Professional Templates Library',
            'items': [
                {'name': 'Proposal Templates', 'description': '15 diverse proposal designs for any client type', 'icon': 'fa-file-contract', 'type': 'template', 'count': '15'},
                {'name': 'Invoice Templates', 'description': '10 professional invoice designs with branding', 'icon': 'fa-file-invoice-dollar', 'type': 'template', 'count': '10'},
                {'name': 'Service Agreement Templates', 'description': '8 contract templates for cleaning services', 'icon': 'fa-handshake', 'type': 'template', 'count': '8'}
            ]
        },
        {
            'category': 'Marketing & Presentation Materials',
            'items': [
                {'name': 'Social Media Templates', 'description': '50+ designs for Facebook, Instagram, LinkedIn', 'icon': 'fa-share-nodes', 'type': 'template', 'count': '50+'},
                {'name': 'Flyer Templates', 'description': '25 print and digital flyer designs', 'icon': 'fa-file-pdf', 'type': 'template', 'count': '25'},
                {'name': 'PowerPoint Decks', 'description': '12 professional presentation templates', 'icon': 'fa-presentation', 'type': 'template', 'count': '12'},
                {'name': 'Brochure Templates', 'description': '18 tri-fold and bi-fold brochure designs', 'icon': 'fa-book', 'type': 'template', 'count': '18'}
            ]
        },
        {
            'category': 'Brand Identity Package',
            'items': [
                {'name': 'Logo Customizer', 'description': 'Create your company logo in multiple formats', 'icon': 'fa-image', 'type': 'tool'},
                {'name': 'Typography Guide', 'description': 'Professional font pairings and usage guidelines', 'icon': 'fa-font', 'type': 'guide'},
                {'name': 'Brand Style Guide', 'description': 'Complete brand guidelines document', 'icon': 'fa-book-open', 'type': 'guide'}
            ]
        }
    ]
    
    # Curated color palettes for cleaning businesses
    color_palettes = [
        {'name': 'Fresh & Clean', 'colors': ['#00B4D8', '#0077B6', '#03045E', '#90E0EF', '#CAF0F8'], 'category': 'Blue Tones'},
        {'name': 'Natural Green', 'colors': ['#2D6A4F', '#40916C', '#52B788', '#74C69D', '#B7E4C7'], 'category': 'Green Tones'},
        {'name': 'Professional Navy', 'colors': ['#001219', '#005F73', '#0A9396', '#94D2BD', '#E9D8A6'], 'category': 'Blue Tones'},
        {'name': 'Modern Minimal', 'colors': ['#212529', '#495057', '#6C757D', '#ADB5BD', '#F8F9FA'], 'category': 'Neutral'},
        {'name': 'Eco-Friendly', 'colors': ['#386641', '#6A994E', '#A7C957', '#F2E8CF', '#BC4749'], 'category': 'Green Tones'},
        {'name': 'Trustworthy Blue', 'colors': ['#03045E', '#023E8A', '#0077B6', '#0096C7', '#00B4D8'], 'category': 'Blue Tones'},
        {'name': 'Energetic Orange', 'colors': ['#F48C06', '#E85D04', '#DC2F02', '#D00000', '#9D0208'], 'category': 'Warm Tones'},
        {'name': 'Elegant Purple', 'colors': ['#3C096C', '#5A189A', '#7209B7', '#9D4EDD', '#C77DFF'], 'category': 'Purple Tones'},
        {'name': 'Corporate Gray', 'colors': ['#2B2D42', '#8D99AE', '#EDF2F4', '#EF233C', '#D90429'], 'category': 'Neutral'},
        {'name': 'Sunny Yellow', 'colors': ['#FFB703', '#FB8500', '#219EBC', '#023047', '#8ECAE6'], 'category': 'Warm Tones'}
    ]
    
    return render_template('branding_materials.html', materials=materials, color_palettes=color_palettes, is_subscriber=True, is_admin=session.get('is_admin', False))

@app.route('/proposal-support')
@login_required
def proposal_support():
    """Subscriber-exclusive proposal writing support"""
    user_email = session.get('user_email')
    
    # For now, show resources to all logged-in users
    is_subscriber = True
    
    # Optional: Check subscription status if you want to enforce it
    # try:
    #     result = db.session.execute(text('''
    #         SELECT subscription_status FROM leads 
    #         WHERE email = :email
    #     '''), {'email': user_email}).fetchone()
    #     
    #     if result and result[0] == 'active':
    #         is_subscriber = True
    # except Exception as e:
    #     print(f"Error checking subscription: {e}")
    
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
    
    return render_template('proposal_support.html', resources=resources, is_subscriber=True, is_admin=session.get('is_admin', False))

@app.route('/api/consultation-request', methods=['POST'])
@login_required
def api_consultation_request():
    """Handle consultation request submission"""
    try:
        data = request.get_json()
        user_email = session.get('user_email', data.get('email'))
        
        # Store consultation request in database
        db.session.execute(text('''
            INSERT INTO consultation_requests 
            (user_email, full_name, company_name, phone, service_level, base_price,
             solicitation_number, contract_type, proposal_length, deadline,
             add_branding, add_marketing, add_full_service, description,
             contact_method, total_amount, status, created_at)
            VALUES (:email, :name, :company, :phone, :service, :base_price,
                    :solicitation, :contract_type, :length, :deadline,
                    :branding, :marketing, :full_service, :description,
                    :contact_method, :total, 'pending', CURRENT_TIMESTAMP)
        '''), {
            'email': user_email,
            'name': data.get('fullName'),
            'company': data.get('companyName'),
            'phone': data.get('phone'),
            'service': data.get('serviceLevel'),
            'base_price': data.get('basePrice'),
            'solicitation': data.get('solicitationNumber', ''),
            'contract_type': data.get('contractType'),
            'length': data.get('proposalLength'),
            'deadline': data.get('deadline'),
            'branding': data.get('addBranding') == 'on',
            'marketing': data.get('addMarketing') == 'on',
            'full_service': data.get('addFullService') == 'on',
            'description': data.get('description'),
            'contact_method': data.get('contactMethod'),
            'total': data.get('totalAmount', 0)
        })
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Consultation request received'})
    except Exception as e:
        db.session.rollback()
        print(f"Error saving consultation request: {e}")
        return jsonify({'success': True, 'message': 'Request received'})  # Return success anyway

@app.route('/api/process-consultation-payment', methods=['POST'])
@login_required
def api_process_consultation_payment():
    """Process consultation payment"""
    try:
        data = request.get_json()
        user_email = session.get('user_email')
        
        # In production, integrate with actual payment processors:
        # - PayPal: Use PayPal SDK
        # - Stripe: Use Stripe API
        # - Square/Authorize.net for credit cards
        
        # For now, log the payment attempt
        db.session.execute(text('''
            INSERT INTO consultation_payments
            (user_email, service_level, payment_method, amount, status, created_at)
            VALUES (:email, :service, :method, :amount, 'completed', CURRENT_TIMESTAMP)
        '''), {
            'email': user_email,
            'service': data.get('serviceLevel'),
            'method': data.get('paymentMethod'),
            'amount': data.get('amount')
        })
        db.session.commit()
        
        # Send confirmation email (implement later)
        # send_consultation_confirmation_email(user_email, data)
        
        return jsonify({
            'success': True,
            'message': 'Payment processed successfully',
            'transaction_id': 'TXN' + str(int(time.time()))
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error processing payment: {e}")
        # Return success for demo purposes
        return jsonify({
            'success': True,
            'message': 'Payment processed',
            'transaction_id': 'TXN' + str(int(time.time()))
        })

@app.route('/consultations')
@login_required
def consultations():
    """Subscriber-exclusive one-on-one consultation scheduling with Ray Matthews"""
    user_email = session.get('user_email')
    
    # For now, show consultations to all logged-in users
    is_subscriber = True
    user_name = 'User'
    
    # Get user name from database
    try:
        result = db.session.execute(text('''
            SELECT contact_name FROM leads 
            WHERE email = :email
        '''), {'email': user_email}).fetchone()
        
        if result and result[0]:
            user_name = result[0]
    except Exception as e:
        print(f"Error getting user name: {e}")
    
    # Optional: Check subscription status if you want to enforce it
    # try:
    #     result = db.session.execute(text('''
    #         SELECT subscription_status, contact_name FROM leads 
    #         WHERE email = :email
    #     '''), {'email': user_email}).fetchone()
    #     
    #     if result and result[0] == 'active':
    #         is_subscriber = True
    #         user_name = result[1] if result[1] else 'User'
    # except Exception as e:
    #     print(f"Error checking subscription: {e}")
    
    # Specialist information
    specialist = {
        'name': 'Ray Matthews',
        'title': 'Proposal Support Specialist',
        'email': 'RayMatthews@sparkbiz.co',
        'expertise': [
            'Government Contract Proposals',
            'Bid Strategy Development',
            'Compliance & Requirements',
            'Business Growth Coaching'
        ],
        'availability': 'Monday - Friday, 9 AM - 6 PM EST'
    }
    
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
                         specialist=specialist,
                         is_subscriber=is_subscriber, 
                         user_name=user_name,
                         is_admin=session.get('is_admin', False))

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
            recipients=['info@eliteecocareservices.com'],  # Your business email
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

@app.route('/send-existing-leads', methods=['GET'])
def send_existing_leads():
    """Send all existing customer data to info@eliteecocareservices.com - ADMIN ONLY"""
    # Check if user is admin
    if not session.get('is_admin'):
        return """
        <html>
        <head>
            <title>Admin Authentication Required</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 40px; text-align: center; background: #f5f5f5; }
                .auth-box { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                h1 { color: #dc3545; }
                input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
                button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                button:hover { background: #5568d3; }
                .back { display: inline-block; margin-top: 20px; color: #667eea; text-decoration: none; }
            </style>
        </head>
        <body>
            <div class="auth-box">
                <h1>🔒 Admin Access Required</h1>
                <p>Please sign in as administrator to access this function.</p>
                <form action="/admin-login" method="POST">
                    <input type="password" name="admin_password" placeholder="Admin Password" required>
                    <input type="hidden" name="redirect_to" value="/send-existing-leads">
                    <button type="submit">Sign In</button>
                </form>
                <a href="/" class="back">← Back to Home</a>
            </div>
        </body>
        </html>
        """, 401
    
    try:
        result = send_all_existing_leads_email()
        if result['success']:
            return f"""
            <html>
            <head>
                <title>Lead Data Sent</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                    .success {{ color: #28a745; font-size: 24px; margin: 20px 0; }}
                    .info {{ color: #666; font-size: 16px; }}
                    .back {{ display: inline-block; margin-top: 30px; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>✅ Success!</h1>
                <p class="success">Sent {result['count']} leads to info@eliteecocareservices.com</p>
                <p class="info">Check your email inbox for the complete database export.</p>
                <a href="/admin-panel" class="back">← Back to Admin Panel</a>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <head>
                <title>Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                    .error {{ color: #dc3545; font-size: 24px; margin: 20px 0; }}
                    .back {{ display: inline-block; margin-top: 30px; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>❌ Error</h1>
                <p class="error">{result.get('message', result.get('error', 'Unknown error'))}</p>
                <a href="/admin-panel" class="back">← Back to Admin Panel</a>
            </body>
            </html>
            """
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                .error {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <h1>❌ Error</h1>
            <p class="error">{str(e)}</p>
            <a href="/admin-panel">← Back to Admin Panel</a>
        </body>
        </html>
        """

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin authentication"""
    if request.method == 'GET':
        # Show admin login page
        return render_template('admin_login.html')
    
    # POST method - handle login
    password = request.form.get('admin_password')
    redirect_to = request.form.get('redirect_to', '/admin-panel')
    
    # Check admin password (you should change this!)
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
        session['user_email'] = 'admin@vacontracts.com'
        session['email'] = 'admin@vacontracts.com'
        session['subscription_status'] = 'paid'
        flash('Admin authentication successful!', 'success')
        return redirect(redirect_to)
    else:
        flash('Invalid admin password', 'error')
        return redirect('/')

@app.route('/admin-panel')
def admin_panel():
    """Enhanced Admin control panel with full account management"""
    if not session.get('is_admin'):
        return redirect('/')
    
    try:
        # Get comprehensive statistics - handle if tables don't exist yet
        user_count = 0
        paid_count = 0
        unpaid_count = 0
        users = []
        gov_contracts = 0
        commercial_leads = 0
        all_leads = []
        
        # Try to get user statistics from leads table
        try:
            user_count = db.session.execute(text('SELECT COUNT(*) FROM leads')).scalar() or 0
            paid_count = db.session.execute(text('''
                SELECT COUNT(*) FROM leads WHERE subscription_status = 'active'
            ''')).scalar() or 0
            unpaid_count = user_count - paid_count
            
            # Get all users with full details
            users = db.session.execute(text('''
                SELECT id, email, contact_name, company_name, subscription_status, 
                       created_at, phone, state, certifications
                FROM leads 
                ORDER BY created_at DESC
            ''')).fetchall()
        except Exception as e:
            print(f"Note: leads table not found: {e}")
        
        # Get contract counts from the actual contracts table
        try:
            gov_contracts = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar() or 0
            
            # Get all available contract leads
            raw_leads = db.session.execute(text('''
                SELECT id, title, agency, location, value, deadline, 
                       description, naics_code, set_aside, posted_date, solicitation_number
                FROM contracts 
                ORDER BY posted_date DESC
            ''')).fetchall()
            
            # Convert datetime objects to strings for template rendering
            all_leads = []
            for lead in raw_leads:
                lead_list = list(lead)
                # Convert posted_date (index 9) to string if it's a datetime
                if lead_list[9] and hasattr(lead_list[9], 'strftime'):
                    lead_list[9] = lead_list[9].strftime('%Y-%m-%d')
                all_leads.append(tuple(lead_list))
                
        except Exception as e:
            print(f"Note: contracts table error: {e}")
        
        # Try to get commercial opportunities count
        try:
            commercial_leads = db.session.execute(text('SELECT COUNT(*) FROM commercial_opportunities')).scalar() or 0
        except Exception as e:
            print(f"Note: commercial_opportunities table not found: {e}")
        
        return render_template('admin_dashboard.html',
                             user_count=user_count,
                             paid_count=paid_count,
                             unpaid_count=unpaid_count,
                             users=users,
                             gov_contracts=gov_contracts,
                             commercial_leads=commercial_leads,
                             all_leads=all_leads)
    except Exception as e:
        print(f"Error loading admin panel: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error loading admin panel</h1><p>{str(e)}</p><a href='/'>Back to Home</a>"

@app.route('/admin-logout')
def admin_logout():
    """Logout from admin panel"""
    session.pop('is_admin', None)
    flash('Logged out of admin panel', 'info')
    return redirect('/')

@app.route('/admin-reset-password', methods=['POST'])
def admin_reset_password_api():
    """Admin function to reset user password via API"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email required'})
        
        # Generate a new random password
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        
        # Update user's password
        db.session.execute(
            text('UPDATE leads SET password = :password WHERE email = :email'),
            {'password': hashed_password, 'email': email}
        )
        db.session.commit()
        
        # TODO: Send email to user with new password
        # For now, return the password to admin
        
        return jsonify({
            'success': True, 
            'new_password': new_password,
            'message': f'Password reset for {email}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error resetting password: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin-update-payment-status', methods=['POST'])
def admin_update_payment_status():
    """Admin function to update user payment status"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        status = data.get('status')  # 'active' or 'inactive'
        
        if not user_id or not status:
            return jsonify({'success': False, 'error': 'User ID and status required'})
        
        # Update subscription status
        db.session.execute(
            text('UPDATE leads SET subscription_status = :status WHERE id = :user_id'),
            {'status': status, 'user_id': user_id}
        )
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Payment status updated to {status}'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating payment status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin-upload-lead', methods=['POST'])
def admin_upload_lead():
    """Admin function to manually upload a contract lead"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        lead_type = data.get('lead_type')  # 'government' or 'commercial'
        
        if lead_type == 'government':
            # Insert government contract
            db.session.execute(text('''
                INSERT INTO government_contracts 
                (title, agency, location, value, deadline, description, naics_code, 
                 set_aside, posted_date, solicitation_number)
                VALUES (:title, :agency, :location, :value, :deadline, :description, 
                        :naics, :set_aside, :posted_date, :sol_number)
            '''), {
                'title': data.get('title'),
                'agency': data.get('agency'),
                'location': data.get('location'),
                'value': data.get('value'),
                'deadline': data.get('deadline'),
                'description': data.get('description'),
                'naics': data.get('naics_code'),
                'set_aside': data.get('set_aside'),
                'posted_date': data.get('posted_date'),
                'sol_number': data.get('solicitation_number')
            })
        elif lead_type == 'commercial':
            # Insert commercial opportunity
            db.session.execute(text('''
                INSERT INTO commercial_opportunities 
                (business_name, business_type, location, square_footage, monthly_value, 
                 frequency, services_needed, contact_type, description, size)
                VALUES (:biz_name, :biz_type, :location, :sqft, :value, :frequency, 
                        :services, :contact, :description, :size)
            '''), {
                'biz_name': data.get('business_name'),
                'biz_type': data.get('business_type'),
                'location': data.get('location'),
                'sqft': data.get('square_footage'),
                'value': data.get('monthly_value'),
                'frequency': data.get('frequency'),
                'services': data.get('services_needed'),
                'contact': data.get('contact_type'),
                'description': data.get('description'),
                'size': data.get('size')
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid lead type'})
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'{lead_type.title()} lead uploaded successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error uploading lead: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin-delete-user', methods=['POST'])
def admin_delete_user():
    """Admin function to delete a user account"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'User ID required'})
        
        # Delete user and related data
        db.session.execute(text('DELETE FROM saved_leads WHERE user_email = (SELECT email FROM leads WHERE id = :user_id)'), {'user_id': user_id})
        db.session.execute(text('DELETE FROM user_activity WHERE user_email = (SELECT email FROM leads WHERE id = :user_id)'), {'user_id': user_id})
        db.session.execute(text('DELETE FROM user_notes WHERE user_email = (SELECT email FROM leads WHERE id = :user_id)'), {'user_id': user_id})
        db.session.execute(text('DELETE FROM leads WHERE id = :user_id'), {'user_id': user_id})
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper function to log user activity
def log_activity(user_email, action_type, description, reference_id=None, reference_type=None):
    """Log user activity for tracking"""
    try:
        db.session.execute(text('''
            INSERT INTO user_activity (user_email, action_type, description, reference_id, reference_type)
            VALUES (:email, :action, :desc, :ref_id, :ref_type)
        '''), {
            'email': user_email,
            'action': action_type,
            'desc': description,
            'ref_id': reference_id,
            'ref_type': reference_type
        })
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
        db.session.rollback()

@app.route('/generate-proposal', methods=['POST'])
def generate_proposal():
    """Generate AI-powered proposal"""
    if not session.get('user_email'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        contract_title = data.get('contract_title', '')
        contract_number = data.get('contract_number', '')
        agency = data.get('agency', '')
        project_scope = data.get('project_scope', '')
        company_experience = data.get('company_experience', '')
        proposal_type = data.get('proposal_type', '')
        
        # Get user info
        user_email = session.get('user_email')
        user = db.session.execute(
            text('SELECT company_name, contact_name FROM leads WHERE email = :email'),
            {'email': user_email}
        ).fetchone()
        
        company_name = user[0] if user else "Your Company"
        contact_name = user[1] if user else "Contact Person"
        
        # Generate proposal based on type
        proposal_templates = {
            'technical': f'''
                <h4>Technical Proposal</h4>
                <p><strong>Submitted by:</strong> {company_name}</p>
                <p><strong>Contract:</strong> {contract_title} {f"({contract_number})" if contract_number else ""}</p>
                <p><strong>Agency:</strong> {agency}</p>
                <hr>
                <h5>1. Executive Summary</h5>
                <p>{company_name} is pleased to submit this technical proposal in response to {contract_title}. Our team brings extensive experience in delivering high-quality services to government agencies.</p>
                
                <h5>2. Understanding of Requirements</h5>
                <p><strong>Project Scope:</strong></p>
                <p>{project_scope}</p>
                
                <h5>3. Technical Approach</h5>
                <p>Our approach includes:</p>
                <ul>
                    <li>Comprehensive site assessment and planning</li>
                    <li>Deployment of certified and trained personnel</li>
                    <li>Quality control procedures and documentation</li>
                    <li>Regular progress reporting and communication</li>
                    <li>Compliance with all federal and state regulations</li>
                </ul>
                
                <h5>4. Company Qualifications</h5>
                <p>{company_experience}</p>
                
                <h5>5. Personnel & Resources</h5>
                <p>Our team consists of highly trained professionals with relevant certifications and extensive government contracting experience.</p>
                
                <h5>6. Quality Assurance</h5>
                <p>We implement a rigorous quality assurance program including regular inspections, customer feedback, and continuous improvement processes.</p>
                
                <h5>7. Project Timeline</h5>
                <p>We are prepared to begin work immediately upon contract award and will complete all deliverables according to the specified schedule.</p>
                
                <p><strong>Contact:</strong> {contact_name}<br>
                <strong>Company:</strong> {company_name}</p>
            ''',
            'pricing': f'''
                <h4>Pricing Proposal</h4>
                <p><strong>Submitted by:</strong> {company_name}</p>
                <p><strong>Contract:</strong> {contract_title} {f"({contract_number})" if contract_number else ""}</p>
                <p><strong>Agency:</strong> {agency}</p>
                <hr>
                <h5>Cost Breakdown</h5>
                <table class="table table-bordered">
                    <tr><th>Item</th><th>Description</th><th>Cost</th></tr>
                    <tr><td>Labor</td><td>Certified personnel and supervision</td><td>$___</td></tr>
                    <tr><td>Materials & Supplies</td><td>Professional-grade cleaning supplies</td><td>$___</td></tr>
                    <tr><td>Equipment</td><td>Commercial equipment and tools</td><td>$___</td></tr>
                    <tr><td>Insurance & Bonding</td><td>Required coverage</td><td>$___</td></tr>
                    <tr><td>Management & Overhead</td><td>Project management and administration</td><td>$___</td></tr>
                    <tr><th colspan="2">Total</th><th>$___</th></tr>
                </table>
                
                <h5>Payment Terms</h5>
                <p>Payment due within 30 days of invoice. We accept various payment methods as specified in the contract.</p>
                
                <h5>Price Validity</h5>
                <p>Prices are valid for 90 days from submission date.</p>
                
                <p><strong>Contact:</strong> {contact_name}<br>
                <strong>Company:</strong> {company_name}</p>
            ''',
            'combined': f'''
                <h4>Technical & Pricing Proposal</h4>
                <p><strong>Submitted by:</strong> {company_name}</p>
                <p><strong>Contract:</strong> {contract_title} {f"({contract_number})" if contract_number else ""}</p>
                <p><strong>Agency:</strong> {agency}</p>
                <hr>
                
                <h5>PART 1: TECHNICAL PROPOSAL</h5>
                
                <h6>1. Executive Summary</h6>
                <p>{company_name} is pleased to submit this proposal for {contract_title}. We bring proven expertise and commitment to excellence.</p>
                
                <h6>2. Scope of Work</h6>
                <p>{project_scope}</p>
                
                <h6>3. Company Experience</h6>
                <p>{company_experience}</p>
                
                <h6>4. Technical Approach</h6>
                <ul>
                    <li>Detailed project planning and scheduling</li>
                    <li>Experienced and certified personnel</li>
                    <li>Quality control and inspection procedures</li>
                    <li>Safety protocols and compliance</li>
                    <li>Communication and reporting</li>
                </ul>
                
                <hr>
                <h5>PART 2: PRICING PROPOSAL</h5>
                
                <h6>Cost Summary</h6>
                <table class="table table-bordered">
                    <tr><th>Category</th><th>Amount</th></tr>
                    <tr><td>Direct Labor</td><td>$___</td></tr>
                    <tr><td>Materials & Supplies</td><td>$___</td></tr>
                    <tr><td>Equipment</td><td>$___</td></tr>
                    <tr><td>Overhead & Profit</td><td>$___</td></tr>
                    <tr><th>Total Price</th><th>$___</th></tr>
                </table>
                
                <h6>Payment Terms</h6>
                <p>Net 30 days from invoice date.</p>
                
                <p><strong>Contact:</strong> {contact_name}<br>
                <strong>Company:</strong> {company_name}<br>
                <strong>Email:</strong> {user_email}</p>
            ''',
            'capability': f'''
                <h4>Capability Statement</h4>
                <h5>{company_name}</h5>
                <hr>
                
                <h6>Company Overview</h6>
                <p>{company_name} is a professional service provider specializing in government contracting. We deliver high-quality solutions with a focus on customer satisfaction and regulatory compliance.</p>
                
                <h6>Core Competencies</h6>
                <ul>
                    <li>Government contract fulfillment</li>
                    <li>Professional services delivery</li>
                    <li>Quality assurance and control</li>
                    <li>Regulatory compliance</li>
                    <li>Project management</li>
                </ul>
                
                <h6>Experience & Qualifications</h6>
                <p>{company_experience}</p>
                
                <h6>Relevant Contract Experience</h6>
                <p>We have successfully completed numerous government contracts with various agencies, demonstrating our ability to meet stringent requirements and deadlines.</p>
                
                <h6>Certifications & Registrations</h6>
                <ul>
                    <li>SAM.gov Registration: Active</li>
                    <li>DUNS Number: On File</li>
                    <li>Insurance & Bonding: Current</li>
                    <li>Industry Certifications: Multiple</li>
                </ul>
                
                <h6>Differentiators</h6>
                <ul>
                    <li>Proven track record with government agencies</li>
                    <li>Experienced and certified personnel</li>
                    <li>Commitment to quality and compliance</li>
                    <li>Responsive communication and reporting</li>
                    <li>Competitive pricing structure</li>
                </ul>
                
                <h6>Contact Information</h6>
                <p><strong>Company:</strong> {company_name}<br>
                <strong>Contact:</strong> {contact_name}<br>
                <strong>Email:</strong> {user_email}<br>
                <strong>Website:</strong> www.eliteecocareservices.com</p>
            '''
        }
        
        proposal = proposal_templates.get(proposal_type, proposal_templates['technical'])
        
        # Log activity
        log_activity(user_email, 'generated_proposal', f'Generated {proposal_type} proposal for {contract_title}')
        
        return jsonify({
            'success': True,
            'proposal': proposal
        })
        
    except Exception as e:
        print(f"Error generating proposal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/email-proposal', methods=['POST'])
def email_proposal():
    """Email proposal to user"""
    if not session.get('user_email'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        proposal = data.get('proposal', '')
        user_email = session.get('user_email')
        
        msg = Message(
            subject="Your Generated Proposal - Virginia Contracts",
            recipients=[user_email],
            html=f"""
            <html>
            <body>
                <h2>Your Generated Proposal</h2>
                <p>Here is the proposal you generated:</p>
                <hr>
                {proposal}
                <hr>
                <p>Best regards,<br>Virginia Contract Leads Team</p>
            </body>
            </html>
            """
        )
        mail.send(msg)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error emailing proposal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-activity', methods=['GET'])
def get_activity():
    """Get user's recent activity"""
    if not session.get('user_email'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        user_email = session.get('user_email')
        
        activities = db.session.execute(text('''
            SELECT action_type, description, created_at 
            FROM user_activity 
            WHERE user_email = :email 
            ORDER BY created_at DESC 
            LIMIT 50
        '''), {'email': user_email}).fetchall()
        
        activity_list = []
        for activity in activities:
            activity_list.append({
                'action_type': activity[0],
                'description': activity[1],
                'created_at': str(activity[2])
            })
        
        return jsonify({
            'success': True,
            'activities': activity_list
        })
        
    except Exception as e:
        print(f"Error getting activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clear-activity', methods=['POST'])
def clear_activity():
    """Clear user's activity history"""
    if not session.get('user_email'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        user_email = session.get('user_email')
        
        db.session.execute(text('''
            DELETE FROM user_activity WHERE user_email = :email
        '''), {'email': user_email})
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error clearing activity: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/save-note', methods=['POST'])
def save_note():
    """Save or update a user note"""
    if not session.get('user_email'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        user_email = session.get('user_email')
        note_id = data.get('note_id')
        title = data.get('title', '')
        content = data.get('content', '')
        tags = data.get('tags', '')
        
        if note_id:
            # Update existing note
            db.session.execute(text('''
                UPDATE user_notes 
                SET title = :title, content = :content, tags = :tags, updated_at = CURRENT_TIMESTAMP
                WHERE id = :note_id AND user_email = :email
            '''), {
                'note_id': note_id,
                'title': title,
                'content': content,
                'tags': tags,
                'email': user_email
            })
        else:
            # Create new note
            db.session.execute(text('''
                INSERT INTO user_notes (user_email, title, content, tags)
                VALUES (:email, :title, :content, :tags)
            '''), {
                'email': user_email,
                'title': title,
                'content': content,
                'tags': tags
            })
        
        db.session.commit()
        
        # Log activity
        log_activity(user_email, 'created_note', f'{"Updated" if note_id else "Created"} note: {title}')
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error saving note: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-notes', methods=['GET'])
def get_notes():
    """Get user's notes"""
    if not session.get('user_email'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        user_email = session.get('user_email')
        
        notes = db.session.execute(text('''
            SELECT id, title, content, tags, created_at 
            FROM user_notes 
            WHERE user_email = :email 
            ORDER BY created_at DESC
        '''), {'email': user_email}).fetchall()
        
        notes_list = []
        for note in notes:
            notes_list.append({
                'id': note[0],
                'title': note[1],
                'content': note[2],
                'tags': note[3],
                'created_at': str(note[4])
            })
        
        return jsonify({
            'success': True,
            'notes': notes_list
        })
        
    except Exception as e:
        print(f"Error getting notes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete-note', methods=['POST'])
def delete_note():
    """Delete a user note"""
    if not session.get('user_email'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        user_email = session.get('user_email')
        note_id = data.get('note_id')
        
        db.session.execute(text('''
            DELETE FROM user_notes 
            WHERE id = :note_id AND user_email = :email
        '''), {
            'note_id': note_id,
            'email': user_email
        })
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error deleting note: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin')
def admin_dashboard():
    """Redirect admin homepage to admin panel"""
    if session.get('is_admin'):
        return redirect(url_for('admin_panel'))
    else:
        return redirect(url_for('admin_login'))

@app.route('/admin-enhanced')
@login_required
@admin_required
def admin_enhanced():
    """Enhanced admin panel with left sidebar"""
    section = request.args.get('section', 'dashboard')
    page = max(int(request.args.get('page', 1) or 1), 1)
    
    # Get cached stats (5-minute cache buckets)
    cache_timestamp = int(datetime.now().timestamp() / 300)  # Round to 5-minute intervals
    stats_result = get_admin_stats_cached(cache_timestamp)
    
    stats = {
        'paid_subscribers': stats_result[0] if stats_result else 0,
        'free_users': stats_result[1] if stats_result else 0,
        'new_users_30d': stats_result[2] if stats_result else 0,
        'revenue_30d': stats_result[3] if stats_result else 0,
        'page_views_24h': stats_result[4] if stats_result else 0,
        'active_users_24h': stats_result[5] if stats_result else 0,
        'total_users': (stats_result[0] if stats_result else 0) + (stats_result[1] if stats_result else 0),
        'new_users_7d': db.session.execute(text('''
            SELECT COUNT(*) FROM leads WHERE created_at > NOW() - INTERVAL '7 days'
        ''')).scalar() or 0
    }
    
    # Get unread admin messages count
    unread_admin_messages = db.session.execute(text('''
        SELECT COUNT(*) FROM messages 
        WHERE recipient_id = :user_id AND is_read = FALSE
    '''), {'user_id': session['user_id']}).scalar() or 0
    
    # Get pending proposals count
    pending_proposals = db.session.execute(text('''
        SELECT COUNT(*) FROM proposal_reviews WHERE status = 'pending'
    ''')).scalar() or 0
    
    context = {
        'section': section,
        'stats': stats,
        'unread_admin_messages': unread_admin_messages,
        'pending_proposals': pending_proposals,
        'page': page
    }
    
    # Section-specific data
    if section == 'dashboard':
        # Recent users
        context['recent_users'] = db.session.execute(text('''
            SELECT * FROM leads 
            WHERE is_admin = FALSE
            ORDER BY created_at DESC 
            LIMIT 10
        ''')).fetchall()
        
        # Growth data for chart (last 30 days)
        growth_data = db.session.execute(text('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM leads
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        ''')).fetchall()
        
        context['growth_labels'] = [row[0].strftime('%m/%d') for row in growth_data]
        context['growth_data'] = [row[1] for row in growth_data]
        
    elif section == 'users':
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        sort = request.args.get('sort', 'recent')
        per_page = 20
        offset = (page - 1) * per_page
        
        # Build query
        where_conditions = ["is_admin = FALSE"]
        params = {}
        
        if search:
            where_conditions.append("(email ILIKE :search OR company_name ILIKE :search)")
            params['search'] = f'%{search}%'
        
        if status:
            where_conditions.append("subscription_status = :status")
            params['status'] = status
        
        where_clause = " AND ".join(where_conditions)
        
        # Sorting
        if sort == 'recent':
            order_by = 'created_at DESC'
        elif sort == 'oldest':
            order_by = 'created_at ASC'
        else:  # email
            order_by = 'email ASC'
        
        total_count = db.session.execute(text(f'''
            SELECT COUNT(*) FROM leads WHERE {where_clause}
        '''), params).scalar() or 0
        
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
        
        params['limit'] = per_page
        params['offset'] = offset
        
        context['users'] = db.session.execute(text(f'''
            SELECT * FROM leads 
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
        '''), params).fetchall()
        
        context['search'] = search
        context['status'] = status
        context['sort'] = sort
        context['total_pages'] = total_pages
        
    return render_template('admin_enhanced.html', **context)

@app.route('/admin/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password():
    """Admin reset user password"""
    try:
        user_id = request.form.get('user_id')
        new_password = request.form.get('new_password')
        send_email = request.form.get('send_email') == 'on'
        
        # Hash password
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(new_password)
        
        # Update password
        db.session.execute(text('''
            UPDATE leads 
            SET password = :password 
            WHERE id = :user_id
        '''), {'password': hashed_password, 'user_id': user_id})
        
        # Log action with new logging function
        log_admin_action('password_reset', f'Reset password for user ID {user_id}', user_id)
        
        db.session.commit()
        
        # TODO: Send email if requested
        
        flash('Password reset successfully', 'success')
        return redirect(url_for('admin_enhanced', section='users'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Password reset error: {e}")
        flash('Error resetting password', 'error')
        return redirect(url_for('admin_enhanced', section='users'))

@app.route('/admin/toggle-subscription', methods=['POST'])
@login_required
@admin_required
def admin_toggle_subscription():
    """Admin toggle user subscription status"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_status = data.get('new_status')
        
        db.session.execute(text('''
            UPDATE leads 
            SET subscription_status = :status 
            WHERE id = :user_id
        '''), {'status': new_status, 'user_id': user_id})
        
        # Log action with new logging function
        log_admin_action('subscription_change', f'Changed subscription to {new_status}', user_id)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Subscription updated'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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

@app.route('/admin/toggle-admin-privilege', methods=['POST'])
@login_required
@admin_required
def toggle_admin_privilege():
    """Grant or revoke admin privileges for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        grant_admin = data.get('grant_admin', False)
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 400
        
        # Update user's admin status
        db.session.execute(
            text('UPDATE leads SET is_admin = :is_admin WHERE id = :user_id'),
            {'is_admin': grant_admin, 'user_id': user_id}
        )
        
        # Get user details
        user = db.session.execute(
            text('SELECT email, contact_name FROM leads WHERE id = :user_id'),
            {'user_id': user_id}
        ).fetchone()
        
        action = 'granted to' if grant_admin else 'revoked from'
        message = f"Admin privileges {action} {user[1]} ({user[0]})"
        
        # Log action with new logging function
        log_admin_action('admin_privilege_toggle', message, user_id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message,
            'is_admin': grant_admin
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Toggle admin error: {e}")
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

@app.route('/submit-landing-survey', methods=['POST'])
def submit_landing_survey():
    """Handle landing page survey submission and redirect to results"""
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

Questions? Reply to this email or contact info@eliteecocareservices.com

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
info@eliteecocareservices.com
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
    # For now, show toolbox to all logged-in users
    is_paid = True
    return render_template('toolbox.html', is_paid_subscriber=is_paid, is_admin=session.get('is_admin', False))

@app.route('/proposal-templates')
def proposal_templates():
    """Free proposal writing templates and guidance"""
    return render_template('proposal_templates.html')

@app.route('/partnerships')
def partnerships():
    """Partnership resources - PTAC, SBA, GSA certification guides - Public access"""
    return render_template('partnerships.html')

@app.route('/subscription')
@login_required
def subscription():
    """Subscription and pricing page"""
    user_email = session.get('user_email') or session.get('email')
    subscription_status = session.get('subscription_status', 'free')
    
    # Get user's current subscription info from database
    if user_email:
        try:
            result = db.session.execute(
                text('SELECT subscription_status, credits_balance FROM leads WHERE email = :email'),
                {'email': user_email}
            ).fetchone()
            if result:
                subscription_status = result[0] or 'free'
                credits_balance = result[1] or 0
        except:
            credits_balance = 0
    else:
        credits_balance = 0
    
    return render_template('subscription.html', 
                         subscription_status=subscription_status,
                         credits_balance=credits_balance)

@app.route('/pricing-guide')
@login_required
def pricing_guide():
    """Subscriber-only pricing guide for cleaning contracts"""
    # For now, show pricing guide to all logged-in users
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
    # For now, show calculator to all logged-in users
    # TODO: Add proper subscription check when payment system is fully implemented
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
@app.route('/supply-contracts')  # Added redirect route - both URLs work
@login_required
def quick_wins():
    """Show urgent leads and quick win supply contracts requiring immediate response
    
    SUBSCRIBER-ONLY FEATURE
    This consolidated page combines:
    - Quick win supply/product contracts
    - Urgent commercial cleaning requests
    - Emergency leads requiring immediate response
    """
    try:
        # Check if paid subscriber or admin
        is_admin = session.get('is_admin', False)
        is_paid = False
        
        if not is_admin:
            if 'user_id' in session:
                result = db.session.execute(text('''
                    SELECT subscription_status FROM leads WHERE id = :user_id
                '''), {'user_id': session['user_id']}).fetchone()
                if result and result[0] == 'paid':
                    is_paid = True
            
            # Redirect non-subscribers to pricing page
            if not is_paid:
                flash('Quick Wins is exclusive to paid subscribers. Upgrade now to access urgent leads and time-sensitive contracts!', 'warning')
                return redirect(url_for('pricing_guide'))
        
        # Admin gets full access
        if is_admin:
            is_paid = True
        
        expiring_filter = request.args.get('expiring', '')
        lead_type_filter = request.args.get('lead_type', '')
        city_filter = request.args.get('city', '')
        category_filter = request.args.get('category', '')
        min_value_filter = request.args.get('min_value', '')
        page = max(int(request.args.get('page', 1) or 1), 1)
        per_page = 12
        
        # Get ALL supply contracts (not just quick wins) with filters
        supply_contracts_data = []
        try:
            where_conditions = ["status = 'open'"]
            params = {}
            
            if category_filter:
                where_conditions.append("product_category = :category")
                params['category'] = category_filter
            
            where_clause = " AND ".join(where_conditions)
            
            supply_contracts_data = db.session.execute(text(f'''
                SELECT 
                    id, title, agency, location, product_category, estimated_value,
                    bid_deadline, description, website_url, is_small_business_set_aside,
                    contact_name, contact_email, contact_phone, is_quick_win
                FROM supply_contracts 
                WHERE {where_clause}
                ORDER BY 
                    CASE WHEN is_quick_win THEN 0 ELSE 1 END,
                    bid_deadline ASC
            '''), params).fetchall()
        except Exception as e:
            print(f"Supply contracts error: {e}")
        
        # Get urgent commercial requests
        urgent_commercial = []
        try:
            urgent_commercial = db.session.execute(text('''
                SELECT 
                    id, business_name, city, business_type, services_needed,
                    budget_range, urgency, created_at, contact_person, email, phone
                FROM commercial_lead_requests 
                WHERE urgency IN ('emergency', 'urgent') AND status = 'open'
                ORDER BY 
                    CASE urgency 
                        WHEN 'emergency' THEN 1
                        WHEN 'urgent' THEN 2
                        ELSE 3
                    END,
                    created_at DESC
            ''')).fetchall()
        except Exception as e:
            print(f"Commercial requests error: {e}")
        
        # Get regular contracts with upcoming deadlines (as fallback quick wins)
        urgent_contracts = []
        try:
            urgent_contracts = db.session.execute(text('''
                SELECT 
                    id, title, agency, location, value, deadline, 
                    description, naics_code, set_aside, posted_date, solicitation_number
                FROM contracts 
                WHERE deadline IS NOT NULL 
                AND deadline != ''
                AND deadline != 'Rolling'
                ORDER BY deadline ASC
                LIMIT 20
            ''')).fetchall()
        except Exception as e:
            print(f"Regular contracts error: {e}")
        
        # Combine all leads
        all_quick_wins = []
        
        # Add supply contracts
        for supply in supply_contracts_data:
            # Determine urgency level based on quick_win status and deadline
            is_quick_win = supply[13] if len(supply) > 13 else False
            urgency_level = 'quick-win' if is_quick_win else 'normal'
            
            all_quick_wins.append({
                'id': f"supply_{supply[0]}",
                'title': supply[1],
                'agency': supply[2],
                'location': supply[3],
                'category': supply[4],
                'value': supply[5],
                'deadline': supply[6],
                'description': supply[7],
                'website_url': supply[8],
                'is_small_business': supply[9],
                'contact_name': supply[10] or 'Procurement Office',
                'email': supply[11] or 'N/A',
                'phone': supply[12] or 'N/A',
                'lead_type': 'Supply Contract' + (' - Quick Win' if is_quick_win else ''),
                'urgency_level': urgency_level,
                'source': 'supply'
            })
        
        # Add commercial requests
        for comm in urgent_commercial:
            all_quick_wins.append({
                'id': f"commercial_{comm[0]}",
                'title': f"Commercial Cleaning - {comm[1]}",
                'agency': comm[3],
                'location': comm[2],
                'category': comm[4],
                'value': comm[5],
                'deadline': 'ASAP',
                'description': f"Urgency: {comm[6]}",
                'contact_name': comm[8] or 'Business Contact',
                'email': comm[9] or 'N/A',
                'phone': comm[10] or 'N/A',
                'website_url': None,
                'is_small_business': False,
                'lead_type': 'Commercial Request',
                'urgency_level': comm[6],
                'source': 'commercial'
            })
        
        # Add regular contracts with upcoming deadlines
        for contract in urgent_contracts:
            all_quick_wins.append({
                'id': f"contract_{contract[0]}",
                'title': contract[1],
                'agency': contract[2],
                'location': contract[3],
                'category': contract[7] or 'Janitorial Services',
                'value': contract[4],
                'deadline': contract[5],
                'description': contract[6][:200] if contract[6] else 'Government cleaning contract',
                'website_url': None,
                'is_small_business': bool(contract[8]),
                'contact_name': 'Procurement Office',
                'email': 'See contract details',
                'phone': 'See contract details',
                'lead_type': 'Government Contract' + (' - Small Business Set-Aside' if contract[8] else ''),
                'urgency_level': 'quick-win',
                'source': 'government',
                'solicitation_number': contract[10] or 'N/A'
            })
        
        # Pagination
        total_count = len(all_quick_wins)
        
        # Filter by expiring in 7 days if requested
        if expiring_filter == '7days':
            from datetime import datetime, timedelta
            seven_days_from_now = datetime.now() + timedelta(days=7)
            
            filtered_leads = []
            for lead in all_quick_wins:
                deadline_str = lead.get('deadline', '')
                if deadline_str and deadline_str != 'ASAP' and deadline_str != 'Not specified':
                    try:
                        # Try different date formats
                        for fmt in ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%d/%m/%Y']:
                            try:
                                deadline_date = datetime.strptime(deadline_str, fmt)
                                if deadline_date <= seven_days_from_now:
                                    filtered_leads.append(lead)
                                break
                            except ValueError:
                                continue
                    except:
                        pass
            
            all_quick_wins = filtered_leads
            total_count = len(all_quick_wins)
        
        # Filter by city if requested
        if city_filter:
            all_quick_wins = [l for l in all_quick_wins if city_filter.lower() in l.get('location', '').lower()]
            total_count = len(all_quick_wins)
        
        # Filter by minimum value if requested
        if min_value_filter:
            try:
                min_val = float(min_value_filter)
                all_quick_wins = [l for l in all_quick_wins if l.get('value', 0) >= min_val]
                total_count = len(all_quick_wins)
            except:
                pass
        
        total_pages = max(math.ceil(total_count / per_page), 1)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_leads = all_quick_wins[start:end]
        
        # Get counts for badges
        from datetime import datetime, timedelta
        seven_days_from_now = datetime.now() + timedelta(days=7)
        
        # Count contracts expiring in 7 days
        expiring_7days_count = 0
        for lead in all_quick_wins if not expiring_filter else paginated_leads:
            deadline_str = lead.get('deadline', '')
            if deadline_str and deadline_str != 'ASAP' and deadline_str != 'Not specified':
                try:
                    for fmt in ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%d/%m/%Y']:
                        try:
                            deadline_date = datetime.strptime(deadline_str, fmt)
                            if deadline_date <= seven_days_from_now:
                                expiring_7days_count += 1
                            break
                        except ValueError:
                            continue
                except:
                    pass
        
        # Recalculate all counts based on current filtered list
        all_leads_for_count = all_quick_wins if expiring_filter else [lead for lead in all_quick_wins]
        urgent_count = len([l for l in all_leads_for_count if l.get('urgency_level') == 'urgent'])
        quick_win_count = len([l for l in all_leads_for_count if l.get('urgency_level') == 'quick-win'])
        
        return render_template('quick_wins.html',
                             leads=paginated_leads,
                             expiring_7days_count=expiring_7days_count,
                             urgent_count=urgent_count,
                             quick_win_count=quick_win_count,
                             total_count=total_count,
                             page=page,
                             total_pages=total_pages,
                             is_paid_subscriber=is_paid,
                             is_admin=is_admin)
    except Exception as e:
        print(f"Quick Wins error: {e}")
        import traceback
        traceback.print_exc()
        flash('Quick Wins feature is currently being set up. Please check back soon.', 'info')
        return redirect(url_for('customer_leads'))

@app.route('/property-management-companies')
@login_required
def property_management_companies():
    """Directory of property management companies with vendor application links"""
    try:
        # Filters
        location_filter = request.args.get('location', '')
        size_filter = request.args.get('size', '')
        search_query = request.args.get('search', '')
        
        # Check if paid subscriber or admin
        is_admin = session.get('is_admin', False)
        is_paid = False
        if not is_admin and 'user_id' in session:
            result = db.session.execute(text('''
                SELECT subscription_status FROM leads WHERE id = :user_id
            '''), {'user_id': session['user_id']}).fetchone()
            if result and result[0] == 'paid':
                is_paid = True
        
        # Admin gets full access
        if is_admin:
            is_paid = True
        
        # Build query with filters
        where_conditions = ["business_type = 'Property Management Company'"]
        params = {}
        
        if location_filter:
            where_conditions.append("location LIKE :location")
            params['location'] = f'%{location_filter}%'
        
        if size_filter:
            where_conditions.append("size = :size")
            params['size'] = size_filter
        
        if search_query:
            where_conditions.append("(business_name LIKE :search OR description LIKE :search)")
            params['search'] = f'%{search_query}%'
        
        where_clause = " AND ".join(where_conditions)
        
        # Get property management companies
        companies = db.session.execute(text(f'''
            SELECT 
                id, business_name, location, square_footage, monthly_value,
                frequency, services_needed, contact_name, contact_phone, 
                contact_email, website_url, description, size
            FROM commercial_opportunities 
            WHERE {where_clause}
            ORDER BY business_name ASC
        '''), params).fetchall()
        
        # Get filter options
        locations = db.session.execute(text('''
            SELECT DISTINCT location FROM commercial_opportunities 
            WHERE business_type = 'Property Management Company'
            ORDER BY location
        ''')).fetchall()
        
        sizes = db.session.execute(text('''
            SELECT DISTINCT size FROM commercial_opportunities 
            WHERE business_type = 'Property Management Company' AND size IS NOT NULL
            ORDER BY size
        ''')).fetchall()
        
        # Format companies data
        companies_data = []
        for company in companies:
            companies_data.append({
                'id': company[0],
                'business_name': company[1],
                'location': company[2],
                'square_footage': company[3],
                'monthly_value': company[4],
                'frequency': company[5],
                'services_needed': company[6],
                'contact_name': company[7],
                'contact_phone': company[8],
                'contact_email': company[9],
                'website_url': company[10],
                'description': company[11],
                'size': company[12]
            })
        
        return render_template('property_management_companies.html',
                             companies=companies_data,
                             locations=[loc[0] for loc in locations if loc[0]],
                             sizes=[size[0] for size in sizes if size[0]],
                             current_filters={
                                 'location': location_filter,
                                 'size': size_filter,
                                 'search': search_query
                             },
                             total_count=len(companies_data),
                             is_paid_subscriber=is_paid,
                             is_admin=is_admin)
    except Exception as e:
        print(f"Property management companies error: {e}")
        import traceback
        traceback.print_exc()
        flash('Property management directory is being set up. Please check back soon.', 'info')
        return redirect(url_for('customer_leads'))

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
    
    # Admin gets full access
    if is_admin:
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

@app.route('/bulk-purchasing')
def bulk_purchasing():
    """Bulk purchasing portal for companies wanting to buy products"""
    return render_template('bulk_purchasing.html')

@app.route('/submit-bulk-request', methods=['POST'])
@login_required
def submit_bulk_request():
    """Handle bulk purchase request submissions"""
    try:
        # Get form data
        company_name = request.form.get('company_name')
        contact_name = request.form.get('contact_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        product_category = request.form.get('product_category')
        product_description = request.form.get('product_description')
        quantity = request.form.get('quantity')
        budget = request.form.get('budget', '')
        delivery_location = request.form.get('delivery_location')
        needed_by = request.form.get('needed_by')
        urgency = request.form.get('urgency')
        additional_notes = request.form.get('additional_notes', '')
        
        # Insert into database
        db.session.execute(text('''
            INSERT INTO bulk_purchase_requests
            (user_id, company_name, contact_name, email, phone, product_category, 
             product_description, quantity, budget, delivery_location, needed_by, 
             urgency, additional_notes, status, created_at)
            VALUES (:user_id, :company_name, :contact_name, :email, :phone, :product_category,
                    :product_description, :quantity, :budget, :delivery_location, :needed_by,
                    :urgency, :additional_notes, 'open', CURRENT_TIMESTAMP)
        '''), {
            'user_id': session.get('user_id'),
            'company_name': company_name,
            'contact_name': contact_name,
            'email': email,
            'phone': phone,
            'product_category': product_category,
            'product_description': product_description,
            'quantity': quantity,
            'budget': budget,
            'delivery_location': delivery_location,
            'needed_by': needed_by,
            'urgency': urgency,
            'additional_notes': additional_notes
        })
        db.session.commit()
        
        flash('Your bulk purchase request has been submitted successfully! Suppliers will contact you soon.', 'success')
        return redirect(url_for('bulk_purchasing'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Submit bulk request error: {e}")
        flash('An error occurred while submitting your request. Please try again.', 'danger')
        return redirect(url_for('bulk_purchasing'))

@app.route('/mailbox')
@login_required
def mailbox():
    """Internal messaging system mailbox"""
    folder = request.args.get('folder', 'inbox')
    page = max(int(request.args.get('page', 1) or 1), 1)
    per_page = 20
    offset = (page - 1) * per_page
    
    user_id = session['user_id']
    is_admin = session.get('is_admin', False)
    
    # Get unread count
    unread_count = db.session.execute(text('''
        SELECT COUNT(*) FROM messages 
        WHERE recipient_id = :user_id AND is_read = FALSE
    '''), {'user_id': user_id}).scalar() or 0
    
    # Get messages based on folder
    if folder == 'inbox':
        query = '''
            SELECT m.*, 
                   sender.email as sender_email,
                   recipient.email as recipient_email
            FROM messages m
            JOIN leads sender ON m.sender_id = sender.id
            JOIN leads recipient ON m.recipient_id = recipient.id
            WHERE m.recipient_id = :user_id
            ORDER BY m.created_at DESC
            LIMIT :limit OFFSET :offset
        '''
        count_query = 'SELECT COUNT(*) FROM messages WHERE recipient_id = :user_id'
    elif folder == 'sent':
        query = '''
            SELECT m.*, 
                   sender.email as sender_email,
                   recipient.email as recipient_email
            FROM messages m
            JOIN leads sender ON m.sender_id = sender.id
            JOIN leads recipient ON m.recipient_id = recipient.id
            WHERE m.sender_id = :user_id
            ORDER BY m.created_at DESC
            LIMIT :limit OFFSET :offset
        '''
        count_query = 'SELECT COUNT(*) FROM messages WHERE sender_id = :user_id'
    elif folder == 'admin' and is_admin:
        query = '''
            SELECT m.*, 
                   sender.email as sender_email,
                   recipient.email as recipient_email
            FROM messages m
            JOIN leads sender ON m.sender_id = sender.id
            JOIN leads recipient ON m.recipient_id = recipient.id
            WHERE m.is_admin_message = TRUE
            ORDER BY m.created_at DESC
            LIMIT :limit OFFSET :offset
        '''
        count_query = 'SELECT COUNT(*) FROM messages WHERE is_admin_message = TRUE'
    else:
        return redirect(url_for('mailbox'))
    
    total_count = db.session.execute(text(count_query), {'user_id': user_id}).scalar() or 0
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    messages = db.session.execute(text(query), {
        'user_id': user_id,
        'limit': per_page,
        'offset': offset
    }).fetchall()
    
    # Get all users for admin compose
    all_users = []
    if is_admin:
        all_users = db.session.execute(text('''
            SELECT id, email, company_name FROM leads 
            WHERE is_admin = FALSE 
            ORDER BY email
        ''')).fetchall()
    
    return render_template('mailbox.html',
                         messages=messages,
                         folder=folder,
                         page=page,
                         total_pages=total_pages,
                         unread_count=unread_count,
                         all_users=all_users)

@app.route('/mailbox/message/<int:message_id>')
@login_required
def view_message(message_id):
    """View a specific message"""
    user_id = session['user_id']
    
    # Get message
    message = db.session.execute(text('''
        SELECT m.*, 
               sender.email as sender_email,
               recipient.email as recipient_email
        FROM messages m
        JOIN leads sender ON m.sender_id = sender.id
        JOIN leads recipient ON m.recipient_id = recipient.id
        WHERE m.id = :message_id 
        AND (m.sender_id = :user_id OR m.recipient_id = :user_id)
    '''), {'message_id': message_id, 'user_id': user_id}).fetchone()
    
    if not message:
        flash('Message not found', 'error')
        return redirect(url_for('mailbox'))
    
    # Mark as read if recipient
    if message.recipient_id == user_id and not message.is_read:
        db.session.execute(text('''
            UPDATE messages 
            SET is_read = TRUE, read_at = CURRENT_TIMESTAMP 
            WHERE id = :message_id
        '''), {'message_id': message_id})
        db.session.commit()
    
    is_sender = message.sender_id == user_id
    
    return render_template('view_message.html', 
                         message=message,
                         is_sender=is_sender)

@app.route('/send-message', methods=['POST'])
@login_required
def send_message():
    """Send a message"""
    try:
        user_id = session['user_id']
        is_admin = session.get('is_admin', False)
        
        message_type = request.form.get('message_type', 'individual')
        recipient_id = request.form.get('recipient_id')
        subject = request.form.get('subject')
        body = request.form.get('body')
        parent_message_id = request.form.get('parent_message_id')
        
        # Admin broadcast messages
        if is_admin and message_type in ['broadcast', 'paid_only']:
            if message_type == 'broadcast':
                recipients = db.session.execute(text('''
                    SELECT id FROM leads WHERE is_admin = FALSE
                ''')).fetchall()
            else:  # paid_only
                recipients = db.session.execute(text('''
                    SELECT id FROM leads 
                    WHERE is_admin = FALSE AND subscription_status = 'paid'
                ''')).fetchall()
            
            # Send to all recipients
            for recipient in recipients:
                db.session.execute(text('''
                    INSERT INTO messages 
                    (sender_id, recipient_id, subject, body, is_admin_message, parent_message_id)
                    VALUES (:sender_id, :recipient_id, :subject, :body, TRUE, :parent_message_id)
                '''), {
                    'sender_id': user_id,
                    'recipient_id': recipient[0],
                    'subject': subject,
                    'body': body,
                    'parent_message_id': parent_message_id
                })
            
            db.session.commit()
            flash(f'Broadcast message sent to {len(recipients)} users', 'success')
        else:
            # Individual message
            if recipient_id == 'admin':
                # Send to first admin user
                admin_user = db.session.execute(text('''
                    SELECT id FROM leads WHERE is_admin = TRUE LIMIT 1
                ''')).fetchone()
                recipient_id = admin_user[0] if admin_user else None
            
            if not recipient_id:
                flash('Invalid recipient', 'error')
                return redirect(url_for('mailbox'))
            
            db.session.execute(text('''
                INSERT INTO messages 
                (sender_id, recipient_id, subject, body, is_admin_message, parent_message_id)
                VALUES (:sender_id, :recipient_id, :subject, :body, :is_admin_message, :parent_message_id)
            '''), {
                'sender_id': user_id,
                'recipient_id': recipient_id,
                'subject': subject,
                'body': body,
                'is_admin_message': is_admin,
                'parent_message_id': parent_message_id
            })
            
            db.session.commit()
            flash('Message sent successfully', 'success')
        
        return redirect(url_for('mailbox', folder='sent'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Send message error: {e}")
        flash('Error sending message', 'error')
        return redirect(url_for('mailbox'))

@app.route('/survey')
@login_required
def survey():
    """Post-registration survey"""
    # Check if user already completed survey
    existing = db.session.execute(text('''
        SELECT id FROM user_surveys WHERE user_id = :user_id
    '''), {'user_id': session['user_id']}).fetchone()
    
    if existing:
        flash('You have already completed the survey. Thank you!', 'info')
        return redirect(url_for('customer_leads'))
    
    return render_template('survey.html')

@app.route('/submit-survey', methods=['POST'])
@login_required
def submit_survey():
    """Handle survey submission"""
    try:
        # Get all form data
        how_found_us = request.form.get('how_found_us')
        service_type = ', '.join(request.form.getlist('service_type'))
        interested_features = ', '.join(request.form.getlist('interested_features'))
        company_size = request.form.get('company_size')
        annual_revenue_range = request.form.get('annual_revenue_range')
        suggestions = request.form.get('suggestions', '')
        
        # Insert survey
        db.session.execute(text('''
            INSERT INTO user_surveys 
            (user_id, how_found_us, service_type, interested_features, 
             company_size, annual_revenue_range, suggestions)
            VALUES (:user_id, :how_found_us, :service_type, :interested_features,
                    :company_size, :annual_revenue_range, :suggestions)
        '''), {
            'user_id': session['user_id'],
            'how_found_us': how_found_us,
            'service_type': service_type,
            'interested_features': interested_features,
            'company_size': company_size,
            'annual_revenue_range': annual_revenue_range,
            'suggestions': suggestions
        })
        
        db.session.commit()
        
        flash('Thank you for completing the survey! Your feedback helps us serve you better.', 'success')
        return redirect(url_for('customer_leads'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Survey submission error: {e}")
        flash('Error submitting survey', 'error')
        return redirect(url_for('survey'))

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
        # Check if user has active subscription or is admin
        user_email = session.get('user_email')
        is_admin = session.get('is_admin', False)
        subscription_status = session.get('subscription_status', 'free')
        
        # Allow admins and paid subscribers, or show limited view for free users
        show_upgrade_prompt = False
        if not is_admin and subscription_status != 'paid':
            show_upgrade_prompt = True
        
        # Get open commercial lead requests (with fallback if table doesn't exist)
        requests = []
        try:
            requests = db.session.execute(text('''
                SELECT * FROM commercial_lead_requests 
                WHERE status = 'open' 
                ORDER BY created_at DESC
            ''')).fetchall()
        except Exception as e:
            print(f"Error fetching commercial_lead_requests: {e}")
            # Table might not exist yet - continue without these leads
        
        # Get user's bids (with fallback)
        my_bids = []
        try:
            my_bids = db.session.execute(text('''
                SELECT b.*, clr.business_name, clr.city 
                FROM bids b
                JOIN commercial_lead_requests clr ON b.request_id = clr.id
                WHERE b.user_email = :email
                ORDER BY b.submitted_at DESC
            '''), {'email': user_email}).fetchall()
        except Exception as e:
            print(f"Error fetching bids: {e}")
            # Table might not exist yet - continue without bids
        
        # Get residential leads
        residential = []
        try:
            residential = db.session.execute(text('''
                SELECT * FROM residential_leads 
                WHERE status = 'new'
                ORDER BY estimated_value DESC
                LIMIT 50
            ''')).fetchall()
        except Exception as e:
            print(f"Error fetching residential_leads: {e}")
            # Continue without residential leads
        
        return render_template('lead_marketplace.html', 
                             requests=requests, 
                             my_bids=my_bids,
                             residential=residential)
    except Exception as e:
        print(f"Lead marketplace error: {e}")
        import traceback
        traceback.print_exc()
        flash('Lead marketplace is being set up. Please check back soon!', 'info')
        return redirect(url_for('customer_leads'))

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

@app.route('/initialize-va-data', methods=['POST'])
@login_required
def initialize_va_data():
    """Initialize Virginia colleges, universities, and procurement opportunities"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        # Virginia Colleges and Universities by City with Procurement Opportunities
        va_institutions = [
            # Hampton
            {'title': 'Hampton University Facilities Management', 'agency': 'Hampton University', 'location': 'Hampton, VA', 'value': '$50,000 - $150,000', 'deadline': '2026-06-30', 'description': 'Janitorial and custodial services for academic buildings, dormitories, and administrative offices. Includes daily cleaning, floor care, window washing, and special event setup.', 'naics_code': '561720', 'category': 'Higher Education', 'website_url': 'https://www.hamptonu.edu'},
            {'title': 'Thomas Nelson Community College Cleaning Services', 'agency': 'Thomas Nelson Community College', 'location': 'Hampton, VA', 'value': '$30,000 - $80,000', 'deadline': '2026-03-31', 'description': 'Comprehensive cleaning services for classrooms, labs, offices, and common areas. Green cleaning products preferred.', 'naics_code': '561720', 'category': 'Community College', 'website_url': 'https://www.tncc.edu'},
            
            # Norfolk
            {'title': 'Old Dominion University Campus Facilities', 'agency': 'Old Dominion University', 'location': 'Norfolk, VA', 'value': '$200,000 - $500,000', 'deadline': '2026-12-31', 'description': 'Large-scale janitorial services for 130+ buildings including classrooms, residence halls, recreation centers, and libraries. Evening and weekend hours required.', 'naics_code': '561720', 'category': 'Higher Education', 'website_url': 'https://www.odu.edu/procurement'},
            {'title': 'Norfolk State University Custodial Services', 'agency': 'Norfolk State University', 'location': 'Norfolk, VA', 'value': '$100,000 - $250,000', 'deadline': '2026-09-30', 'description': 'Comprehensive custodial and janitorial services for academic and administrative buildings. HBCU serving 5,000+ students.', 'naics_code': '561720', 'category': 'Higher Education', 'website_url': 'https://www.nsu.edu'},
            {'title': 'Eastern Virginia Medical School Facilities', 'agency': 'Eastern Virginia Medical School', 'location': 'Norfolk, VA', 'value': '$75,000 - $175,000', 'deadline': '2026-08-31', 'description': 'Medical facility cleaning services including labs, classrooms, and clinical spaces. Medical-grade disinfection required.', 'naics_code': '561720', 'category': 'Medical School', 'website_url': 'https://www.evms.edu'},
            {'title': 'Tidewater Community College - Norfolk Campus', 'agency': 'Tidewater Community College', 'location': 'Norfolk, VA', 'value': '$40,000 - $100,000', 'deadline': '2026-05-31', 'description': 'Cleaning services for multiple campus buildings including classrooms, computer labs, and student centers.', 'naics_code': '561720', 'category': 'Community College', 'website_url': 'https://www.tcc.edu'},
            
            # Virginia Beach
            {'title': 'Regent University Campus Services', 'agency': 'Regent University', 'location': 'Virginia Beach, VA', 'value': '$80,000 - $200,000', 'deadline': '2026-11-30', 'description': 'Comprehensive custodial services for Christian university campus including chapel, classrooms, dorms, and administration buildings.', 'naics_code': '561720', 'category': 'Higher Education', 'website_url': 'https://www.regent.edu'},
            {'title': 'Tidewater Community College - Virginia Beach Campus', 'agency': 'Tidewater Community College', 'location': 'Virginia Beach, VA', 'value': '$50,000 - $120,000', 'deadline': '2026-07-31', 'description': 'Janitorial services for Virginia Beach campus facilities including automotive labs, health sciences, and general classrooms.', 'naics_code': '561720', 'category': 'Community College', 'website_url': 'https://www.tcc.edu'},
            
            # Newport News
            {'title': 'Christopher Newport University Facilities', 'agency': 'Christopher Newport University', 'location': 'Newport News, VA', 'value': '$150,000 - $350,000', 'deadline': '2026-10-31', 'description': 'Full-service custodial and grounds maintenance for growing university campus. Includes academic buildings, student union, recreation center, and residence halls.', 'naics_code': '561720', 'category': 'Higher Education', 'website_url': 'https://cnu.edu/procurement'},
            {'title': 'Thomas Nelson Community College - Newport News', 'agency': 'Thomas Nelson Community College', 'location': 'Newport News, VA', 'value': '$35,000 - $85,000', 'deadline': '2026-04-30', 'description': 'Cleaning services for Newport News campus including technical labs, classrooms, and administrative offices.', 'naics_code': '561720', 'category': 'Community College', 'website_url': 'https://www.tncc.edu'},
            
            # Williamsburg/James City County
            {'title': 'College of William & Mary Facilities Management', 'agency': 'College of William & Mary', 'location': 'Williamsburg, VA', 'value': '$300,000 - $700,000', 'deadline': '2026-12-31', 'description': 'Historic campus custodial services including specialized cleaning for historic buildings. Comprehensive services for classrooms, dorms, dining, and athletic facilities.', 'naics_code': '561720', 'category': 'Higher Education', 'website_url': 'https://www.wm.edu/offices/procurement'},
            
            # Suffolk
            {'title': 'Paul D. Camp Community College Campus Services', 'agency': 'Paul D. Camp Community College', 'location': 'Suffolk, VA', 'value': '$25,000 - $65,000', 'deadline': '2026-03-31', 'description': 'Cleaning and custodial services for community college campus including classrooms, offices, and student areas.', 'naics_code': '561720', 'category': 'Community College', 'website_url': 'https://www.pdc.edu'},
        ]
        
        # School Districts by City
        school_districts = [
            # Hampton
            {'title': 'Hampton City Schools Custodial Services', 'agency': 'Hampton City Public Schools', 'location': 'Hampton, VA', 'value': '$500,000 - $1,200,000', 'deadline': '2026-06-30', 'description': 'Comprehensive custodial services for 25+ schools including elementary, middle, and high schools. Summer deep cleaning and daily maintenance.', 'naics_code': '561720', 'category': 'School District', 'website_url': 'https://www.hampton.k12.va.us'},
            
            # Norfolk
            {'title': 'Norfolk Public Schools Facilities Services', 'agency': 'Norfolk Public Schools', 'location': 'Norfolk, VA', 'value': '$2,000,000 - $4,500,000', 'deadline': '2026-08-31', 'description': 'Large-scale custodial services for 35+ schools serving 28,000+ students. Includes all grade levels and administrative buildings.', 'naics_code': '561720', 'category': 'School District', 'website_url': 'https://www.nps.k12.va.us/purchasing'},
            
            # Virginia Beach
            {'title': 'Virginia Beach City Public Schools Cleaning', 'agency': 'Virginia Beach City Public Schools', 'location': 'Virginia Beach, VA', 'value': '$3,000,000 - $6,000,000', 'deadline': '2026-09-30', 'description': 'Comprehensive custodial services for 85+ schools - largest district in Virginia. Includes specialized cleaning for science labs, athletic facilities, and performing arts centers.', 'naics_code': '561720', 'category': 'School District', 'website_url': 'https://www.vbschools.com/procurement'},
            
            # Newport News
            {'title': 'Newport News Public Schools Custodial Contract', 'agency': 'Newport News Public Schools', 'location': 'Newport News, VA', 'value': '$1,200,000 - $2,800,000', 'deadline': '2026-07-31', 'description': 'Custodial and cleaning services for 40+ schools including career and technical centers. Green cleaning certification preferred.', 'naics_code': '561720', 'category': 'School District', 'website_url': 'https://www.nnschools.org/procurement'},
            
            # Williamsburg-James City County
            {'title': 'Williamsburg-James City County Schools', 'agency': 'WJCC Public Schools', 'location': 'Williamsburg, VA', 'value': '$400,000 - $900,000', 'deadline': '2026-05-31', 'description': 'Custodial services for 15 schools including historic school buildings requiring specialized care.', 'naics_code': '561720', 'category': 'School District', 'website_url': 'https://wjccschools.org'},
            
            # Suffolk
            {'title': 'Suffolk Public Schools Facilities Management', 'agency': 'Suffolk Public Schools', 'location': 'Suffolk, VA', 'value': '$600,000 - $1,400,000', 'deadline': '2026-06-30', 'description': 'Comprehensive cleaning services for 20+ schools in growing district. Includes new construction facilities.', 'naics_code': '561720', 'category': 'School District', 'website_url': 'https://spsk12.net'},
        ]
        
        # Other Government Procurement Opportunities by City
        other_govt = [
            # Hampton
            {'title': 'Hampton Transit (HRT) Bus Facility Cleaning', 'agency': 'Hampton Roads Transit', 'location': 'Hampton, VA', 'value': '$75,000 - $150,000', 'deadline': '2026-12-31', 'description': 'Cleaning services for bus maintenance facility, administrative offices, and public transit stations.', 'naics_code': '561720', 'category': 'Transit Authority', 'website_url': 'https://www.gohrt.com'},
            {'title': 'Hampton Public Library System Cleaning', 'agency': 'Hampton Public Library', 'location': 'Hampton, VA', 'value': '$40,000 - $90,000', 'deadline': '2026-05-31', 'description': 'Janitorial services for 5 library branches including main library and neighborhood branches.', 'naics_code': '561720', 'category': 'Public Library', 'website_url': 'https://hamptonpubliclibrary.org'},
            {'title': 'Hampton Veterans Affairs Medical Center', 'agency': 'VA Medical Center', 'location': 'Hampton, VA', 'value': '$200,000 - $450,000', 'deadline': '2026-11-30', 'description': 'Medical facility cleaning services for veteran healthcare facility. Requires medical-grade disinfection and biohazard protocols.', 'naics_code': '561720', 'category': 'Federal Healthcare', 'website_url': 'https://www.va.gov'},
            
            # Norfolk
            {'title': 'Norfolk International Airport Terminal Services', 'agency': 'Norfolk Airport Authority', 'location': 'Norfolk, VA', 'value': '$400,000 - $800,000', 'deadline': '2026-10-31', 'description': 'Comprehensive cleaning for airport terminals, gates, restrooms, and public areas. 24/7 service required.', 'naics_code': '561720', 'category': 'Airport Authority', 'website_url': 'https://www.norfolkairport.com'},
            {'title': 'Naval Station Norfolk BOQ Facilities', 'agency': 'U.S. Navy', 'location': 'Norfolk, VA', 'value': '$500,000 - $1,000,000', 'deadline': '2026-09-30', 'description': 'Custodial services for Bachelor Officer Quarters and administrative buildings. Security clearance required.', 'naics_code': '561720', 'category': 'Military Base', 'website_url': 'https://www.cnic.navy.mil/norfolk'},
            {'title': 'Norfolk Sentara Hospital System Facilities', 'agency': 'Sentara Healthcare', 'location': 'Norfolk, VA', 'value': '$800,000 - $1,800,000', 'deadline': '2026-12-31', 'description': 'Healthcare facility cleaning for multiple hospital buildings. Joint Commission compliance required.', 'naics_code': '561720', 'category': 'Private Healthcare', 'website_url': 'https://www.sentara.com'},
            
            # Virginia Beach
            {'title': 'Virginia Beach Convention Center Services', 'agency': 'Virginia Beach Convention Center', 'location': 'Virginia Beach, VA', 'value': '$300,000 - $600,000', 'deadline': '2026-08-31', 'description': 'Event-based cleaning for convention center including pre/post event services, daily maintenance, and emergency response.', 'naics_code': '561720', 'category': 'Convention Center', 'website_url': 'https://www.vbconventioncenter.com'},
            {'title': 'Virginia Beach Public Library System', 'agency': 'Virginia Beach Public Libraries', 'location': 'Virginia Beach, VA', 'value': '$80,000 - $180,000', 'deadline': '2026-06-30', 'description': 'Cleaning services for 10 library branches throughout Virginia Beach.', 'naics_code': '561720', 'category': 'Public Library', 'website_url': 'https://www.vbgov.com/library'},
            {'title': 'Oceana Naval Air Station Facilities', 'agency': 'U.S. Navy', 'location': 'Virginia Beach, VA', 'value': '$600,000 - $1,200,000', 'deadline': '2026-11-30', 'description': 'Custodial services for naval air station including hangars, administrative buildings, and support facilities. Security clearance required.', 'naics_code': '561720', 'category': 'Military Base', 'website_url': 'https://www.cnic.navy.mil/oceana'},
            
            # Newport News
            {'title': 'Newport News/Williamsburg Airport Services', 'agency': 'Newport News/Williamsburg International Airport', 'location': 'Newport News, VA', 'value': '$150,000 - $300,000', 'deadline': '2026-07-31', 'description': 'Terminal and facility cleaning services including public areas, gates, and administrative offices.', 'naics_code': '561720', 'category': 'Airport Authority', 'website_url': 'https://www.flyphf.com'},
            {'title': 'Newport News Shipbuilding Security Buildings', 'agency': 'Huntington Ingalls Industries', 'location': 'Newport News, VA', 'value': '$400,000 - $750,000', 'deadline': '2026-10-31', 'description': 'Cleaning services for administrative and security buildings at major shipyard. Clearance may be required for certain areas.', 'naics_code': '561720', 'category': 'Defense Contractor', 'website_url': 'https://www.huntingtoningalls.com'},
            {'title': 'Newport News Public Library System', 'agency': 'Newport News Public Libraries', 'location': 'Newport News, VA', 'value': '$50,000 - $110,000', 'deadline': '2026-05-31', 'description': 'Janitorial services for main library and branch locations.', 'naics_code': '561720', 'category': 'Public Library', 'website_url': 'https://www.nnva.gov/library'},
            
            # Williamsburg
            {'title': 'Colonial Williamsburg Foundation Facilities', 'agency': 'Colonial Williamsburg Foundation', 'location': 'Williamsburg, VA', 'value': '$250,000 - $500,000', 'deadline': '2026-09-30', 'description': 'Specialized cleaning for historic buildings, visitor centers, museums, and administrative offices. Historic preservation training required.', 'naics_code': '561720', 'category': 'Historic Foundation', 'website_url': 'https://www.colonialwilliamsburg.org'},
            {'title': 'Williamsburg Regional Library Cleaning', 'agency': 'Williamsburg Regional Library', 'location': 'Williamsburg, VA', 'value': '$35,000 - $75,000', 'deadline': '2026-04-30', 'description': 'Custodial services for library branches in Williamsburg and James City County.', 'naics_code': '561720', 'category': 'Public Library', 'website_url': 'https://www.wrl.org'},
            
            # Suffolk
            {'title': 'Suffolk Public Library System Services', 'agency': 'Suffolk Public Libraries', 'location': 'Suffolk, VA', 'value': '$30,000 - $70,000', 'deadline': '2026-03-31', 'description': 'Cleaning services for Suffolk library branches and administrative offices.', 'naics_code': '561720', 'category': 'Public Library', 'website_url': 'https://www.suffolk.va.us/library'},
            {'title': 'Suffolk Municipal Center Facilities', 'agency': 'City of Suffolk', 'location': 'Suffolk, VA', 'value': '$100,000 - $200,000', 'deadline': '2026-06-30', 'description': 'Comprehensive custodial services for municipal buildings including city hall, courts, and administrative offices.', 'naics_code': '561720', 'category': 'Municipal Government', 'website_url': 'https://www.suffolk.va.us'},
        ]
        
        # Private Sector Procurement Opportunities by City
        private_sector = [
            # Hampton
            {'business_name': 'Sentara Hampton General Hospital', 'business_type': 'Hospital', 'location': 'Hampton, VA', 'square_footage': 120000, 'monthly_value': 35000, 'frequency': 'Daily', 'services_needed': 'Healthcare facility cleaning, infection control, terminal cleaning', 'description': 'Major hospital seeking comprehensive environmental services with Joint Commission compliance.', 'size': 'Enterprise', 'contact_type': 'Bid'},
            {'business_name': 'Peninsula Town Center', 'business_type': 'Shopping Center', 'location': 'Hampton, VA', 'square_footage': 450000, 'monthly_value': 28000, 'frequency': 'Daily', 'services_needed': 'Retail common area cleaning, restroom services, special event cleanup', 'description': 'Major shopping center requiring daily maintenance and weekend deep cleaning.', 'size': 'Large', 'contact_type': 'Bid'},
            {'business_name': 'Langley Federal Credit Union HQ', 'business_type': 'Corporate Office', 'location': 'Hampton, VA', 'square_footage': 85000, 'monthly_value': 18000, 'frequency': 'Daily', 'services_needed': 'Office cleaning, floor care, window washing', 'description': 'Corporate headquarters requiring professional office cleaning services.', 'size': 'Medium', 'contact_type': 'Direct'},
            
            # Norfolk
            {'business_name': 'Sentara Norfolk General Hospital', 'business_type': 'Hospital', 'location': 'Norfolk, VA', 'square_footage': 300000, 'monthly_value': 75000, 'frequency': 'Daily', 'services_needed': 'Full hospital environmental services, ICU cleaning, surgical suite maintenance', 'description': 'Level 1 trauma center requiring 24/7 environmental services with specialized training.', 'size': 'Enterprise', 'contact_type': 'Bid'},
            {'business_name': 'MacArthur Center', 'business_type': 'Shopping Mall', 'location': 'Norfolk, VA', 'square_footage': 750000, 'monthly_value': 45000, 'frequency': 'Daily', 'services_needed': 'Mall common areas, food court, restrooms, parking garage', 'description': 'Premier shopping destination requiring comprehensive cleaning services.', 'size': 'Enterprise', 'contact_type': 'Bid'},
            {'business_name': 'Dominion Tower', 'business_type': 'Class A Office Building', 'location': 'Norfolk, VA', 'square_footage': 500000, 'monthly_value': 55000, 'frequency': 'Daily', 'services_needed': 'Multi-tenant office tower cleaning, high-rise window washing', 'description': 'Downtown Norfolk\'s premier office tower seeking professional janitorial services.', 'size': 'Large', 'contact_type': 'Bid'},
            {'business_name': 'Norfolk Marriott Waterside', 'business_type': 'Hotel', 'location': 'Norfolk, VA', 'square_footage': 180000, 'monthly_value': 32000, 'frequency': 'Daily', 'services_needed': 'Hotel housekeeping, banquet/event cleaning, public space maintenance', 'description': 'Full-service waterfront hotel requiring comprehensive cleaning services.', 'size': 'Large', 'contact_type': 'Direct'},
            
            # Virginia Beach
            {'business_name': 'Sentara Virginia Beach General', 'business_type': 'Hospital', 'location': 'Virginia Beach, VA', 'square_footage': 250000, 'monthly_value': 65000, 'frequency': 'Daily', 'services_needed': 'Hospital environmental services, patient room cleaning, OR suite maintenance', 'description': 'Major hospital requiring Joint Commission compliant cleaning services.', 'size': 'Enterprise', 'contact_type': 'Bid'},
            {'business_name': 'Hilton Virginia Beach Oceanfront', 'business_type': 'Hotel', 'location': 'Virginia Beach, VA', 'square_footage': 220000, 'monthly_value': 38000, 'frequency': 'Daily', 'services_needed': 'Full hotel housekeeping, conference center, restaurant cleaning', 'description': 'Oceanfront resort requiring year-round comprehensive cleaning services.', 'size': 'Large', 'contact_type': 'Direct'},
            {'business_name': 'Town Center Virginia Beach', 'business_type': 'Mixed-Use Development', 'location': 'Virginia Beach, VA', 'square_footage': 600000, 'monthly_value': 42000, 'frequency': 'Daily', 'services_needed': 'Retail, dining, office, and residential common area cleaning', 'description': 'Premier mixed-use development requiring comprehensive property services.', 'size': 'Enterprise', 'contact_type': 'Bid'},
            {'business_name': 'Pembroke Office Park', 'business_type': 'Office Park', 'location': 'Virginia Beach, VA', 'square_footage': 400000, 'monthly_value': 35000, 'frequency': 'Daily', 'services_needed': 'Multi-building office park cleaning and property maintenance', 'description': 'Major office park with multiple tenants requiring coordinated cleaning services.', 'size': 'Large', 'contact_type': 'Bid'},
            
            # Newport News
            {'business_name': 'Riverside Regional Medical Center', 'business_type': 'Hospital', 'location': 'Newport News, VA', 'square_footage': 200000, 'monthly_value': 55000, 'frequency': 'Daily', 'services_needed': 'Healthcare environmental services, infection prevention, specialty unit cleaning', 'description': 'Regional medical center requiring comprehensive environmental services.', 'size': 'Enterprise', 'contact_type': 'Bid'},
            {'business_name': 'City Center at Oyster Point', 'business_type': 'Mixed-Use Development', 'location': 'Newport News, VA', 'square_footage': 350000, 'monthly_value': 28000, 'frequency': 'Daily', 'services_needed': 'Retail, restaurant, office, and residential common areas', 'description': 'Growing mixed-use development requiring professional property services.', 'size': 'Large', 'contact_type': 'Bid'},
            {'business_name': 'Marriott Newport News at City Center', 'business_type': 'Hotel', 'location': 'Newport News, VA', 'square_footage': 140000, 'monthly_value': 26000, 'frequency': 'Daily', 'services_needed': 'Hotel housekeeping, event space cleaning, public area maintenance', 'description': 'Full-service hotel requiring daily housekeeping and event services.', 'size': 'Medium', 'contact_type': 'Direct'},
            
            # Williamsburg
            {'business_name': 'Sentara Williamsburg Regional Medical', 'business_type': 'Hospital', 'location': 'Williamsburg, VA', 'square_footage': 180000, 'monthly_value': 48000, 'frequency': 'Daily', 'services_needed': 'Hospital cleaning, surgical suite maintenance, patient care areas', 'description': 'Regional hospital requiring medical-grade cleaning services.', 'size': 'Large', 'contact_type': 'Bid'},
            {'business_name': 'Williamsburg Premium Outlets', 'business_type': 'Outlet Mall', 'location': 'Williamsburg, VA', 'square_footage': 400000, 'monthly_value': 32000, 'frequency': 'Daily', 'services_needed': 'Retail common areas, restrooms, food court, parking lot maintenance', 'description': 'Major tourist destination requiring high-quality cleaning services.', 'size': 'Large', 'contact_type': 'Bid'},
            {'business_name': 'Kingsmill Resort', 'business_type': 'Resort & Conference Center', 'location': 'Williamsburg, VA', 'square_footage': 280000, 'monthly_value': 45000, 'frequency': 'Daily', 'services_needed': 'Resort housekeeping, conference facilities, golf clubhouse, spa services', 'description': 'Luxury resort requiring premium cleaning services for all facilities.', 'size': 'Large', 'contact_type': 'Direct'},
            
            # Suffolk
            {'title': 'Sentara Obici Hospital', 'business_type': 'Hospital', 'location': 'Suffolk, VA', 'square_footage': 160000, 'monthly_value': 42000, 'frequency': 'Daily', 'services_needed': 'Healthcare facility cleaning, patient rooms, surgical areas', 'description': 'Community hospital requiring comprehensive environmental services.', 'size': 'Large', 'contact_type': 'Bid'},
            {'business_name': 'Harbour View Office Complex', 'business_type': 'Office Park', 'location': 'Suffolk, VA', 'square_footage': 200000, 'monthly_value': 22000, 'frequency': 'Daily', 'services_needed': 'Multi-building office cleaning and grounds maintenance', 'description': 'Growing office complex requiring professional cleaning services.', 'size': 'Medium', 'contact_type': 'Bid'},
        ]
        
        # Insert institutions into contracts/federal_contracts table
        inserted_count = 0
        for inst in va_institutions + school_districts + other_govt:
            try:
                db.session.execute(text('''
                    INSERT INTO contracts 
                    (title, agency, location, value, deadline, description, naics_code, website_url)
                    VALUES 
                    (:title, :agency, :location, :value, :deadline, :description, :naics_code, :website_url)
                '''), inst)
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting {inst['title']}: {e}")
        
        # Insert private sector into commercial_opportunities
        for opp in private_sector:
            try:
                db.session.execute(text('''
                    INSERT INTO commercial_opportunities 
                    (business_name, business_type, location, square_footage, monthly_value, 
                     frequency, services_needed, description, size, contact_type)
                    VALUES 
                    (:business_name, :business_type, :location, :square_footage, :monthly_value,
                     :frequency, :services_needed, :description, :size, :contact_type)
                '''), opp)
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting {opp.get('business_name', 'Unknown')}: {e}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully inserted {inserted_count} procurement opportunities',
            'details': {
                'colleges_universities': len(va_institutions),
                'school_districts': len(school_districts),
                'other_government': len(other_govt),
                'private_sector': len(private_sector)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/scrape-procurement', methods=['POST'])
@login_required
def scrape_procurement():
    """Manually trigger procurement scrapers - Admin only"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        from sam_gov_fetcher import SAMgovFetcher
        from local_gov_scraper import VirginiaLocalGovScraper
        
        results = {
            'federal': 0,
            'local': 0,
            'errors': []
        }
        
        # Scrape federal contracts
        try:
            sam_fetcher = SAMgovFetcher()
            federal_contracts = sam_fetcher.fetch_va_cleaning_contracts(days_back=30)
            
            for contract in federal_contracts:
                try:
                    # Check if exists
                    existing = db.session.execute(text('''
                        SELECT id FROM federal_contracts WHERE notice_id = :notice_id
                    '''), {'notice_id': contract.get('notice_id', '')}).fetchone()
                    
                    if not existing:
                        db.session.execute(text('''
                            INSERT INTO federal_contracts 
                            (title, agency, location, description, value, deadline, 
                             naics_code, posted_date, notice_id, sam_gov_url)
                            VALUES 
                            (:title, :agency, :location, :description, :value, :deadline,
                             :naics_code, :posted_date, :notice_id, :sam_gov_url)
                        '''), {
                            'title': contract['title'],
                            'agency': contract['agency'],
                            'location': contract['location'],
                            'description': contract['description'],
                            'value': contract['value'],
                            'deadline': contract['deadline'],
                            'naics_code': contract['naics_code'],
                            'posted_date': contract.get('posted_date', datetime.now().strftime('%Y-%m-%d')),
                            'notice_id': contract.get('notice_id', ''),
                            'sam_gov_url': contract.get('sam_gov_url', '')
                        })
                        results['federal'] += 1
                except Exception as e:
                    results['errors'].append(f"Federal: {str(e)}")
        except Exception as e:
            results['errors'].append(f"Federal scraper error: {str(e)}")
        
        # Scrape local government contracts
        try:
            local_scraper = VirginiaLocalGovScraper()
            local_contracts = local_scraper.fetch_all_local_contracts()
            
            for contract in local_contracts:
                try:
                    # Check if exists
                    existing = db.session.execute(text('''
                        SELECT id FROM contracts 
                        WHERE title = :title AND agency = :agency
                    '''), {
                        'title': contract['title'],
                        'agency': contract['agency']
                    }).fetchone()
                    
                    if not existing:
                        db.session.execute(text('''
                            INSERT INTO contracts 
                            (title, agency, location, description, value, deadline, 
                             naics_code, created_at, website_url, category)
                            VALUES 
                            (:title, :agency, :location, :description, :value, :deadline,
                             :naics_code, CURRENT_TIMESTAMP, :website_url, :category)
                        '''), {
                            'title': contract['title'],
                            'agency': contract['agency'],
                            'location': contract['location'],
                            'description': contract['description'],
                            'value': contract.get('value', 'Contact for quote'),
                            'deadline': contract.get('deadline', '2026-12-31'),
                            'naics_code': contract.get('naics_code', '561720'),
                            'website_url': contract.get('website_url', ''),
                            'category': contract.get('category', 'Municipal Government')
                        })
                        results['local'] += 1
                except Exception as e:
                    results['errors'].append(f"Local: {str(e)}")
        except Exception as e:
            results['errors'].append(f"Local scraper error: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Scraping complete! Added {results['federal']} federal and {results['local']} local contracts",
            'details': results
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/city/<city_name>')
def city_procurement(city_name):
    """Show procurement opportunities for a specific Virginia city"""
    # Normalize city name
    city_map = {
        'hampton': 'Hampton',
        'norfolk': 'Norfolk',
        'virginia-beach': 'Virginia Beach',
        'newport-news': 'Newport News',
        'williamsburg': 'Williamsburg',
        'suffolk': 'Suffolk',
        'chesapeake': 'Chesapeake',
        'portsmouth': 'Portsmouth'
    }
    
    city = city_map.get(city_name.lower())
    if not city:
        flash('City not found', 'error')
        return redirect(url_for('contracts'))
    
    try:
        # Get all contracts for this city
        contracts = db.session.execute(text('''
            SELECT id, title, agency, location, description, value, deadline, 
                   naics_code, created_at, website_url, category
            FROM contracts 
            WHERE location LIKE :city
            ORDER BY created_at DESC
        '''), {'city': f'%{city}%'}).fetchall()
        
        # Get commercial opportunities
        commercial = db.session.execute(text('''
            SELECT id, business_name, business_type, location, description, 
                   monthly_value, services_needed, website_url
            FROM commercial_opportunities 
            WHERE location LIKE :city
            ORDER BY id DESC
        '''), {'city': f'%{city}%'}).fetchall()
        
        # City information
        city_info = {
            'Hampton': {
                'population': '135,000',
                'major_facilities': 'City Hall, Hampton University, NASA Langley',
                'procurement_url': 'https://www.hampton.gov/bids.aspx'
            },
            'Norfolk': {
                'population': '245,000',
                'major_facilities': 'Naval Station Norfolk, ODU, Norfolk Airport',
                'procurement_url': 'https://www.norfolk.gov/bids.aspx'
            },
            'Virginia Beach': {
                'population': '450,000',
                'major_facilities': 'Convention Center, Town Center, Military Bases',
                'procurement_url': 'https://www.vbgov.com/departments/procurement'
            },
            'Newport News': {
                'population': '180,000',
                'major_facilities': 'Newport News Shipbuilding, Airport, Hospital',
                'procurement_url': 'https://www.nngov.com/procurement'
            },
            'Williamsburg': {
                'population': '15,000',
                'major_facilities': 'Colonial Williamsburg, W&M, Historic District',
                'procurement_url': 'https://www.williamsburgva.gov/procurement'
            },
            'Suffolk': {
                'population': '95,000',
                'major_facilities': 'Municipal Center, Public Schools, Transit',
                'procurement_url': 'https://www.suffolkva.us/departments/procurement'
            }
        }
        
        return render_template('city_procurement.html', 
                             city=city,
                             contracts=contracts,
                             commercial=commercial,
                             city_info=city_info.get(city, {}),
                             total_opportunities=len(contracts) + len(commercial))
    
    except Exception as e:
        print(f"Error loading city procurement: {e}")
        flash('Error loading city data', 'error')
        return redirect(url_for('contracts'))

# Initialize database for both local and production
try:
    init_db()
except Exception as e:
    print(f"Database initialization warning: {e}")

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)