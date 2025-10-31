import os
import json
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mail import Mail, Message
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'virginia-contracting-fallback-key-2024')

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

# Credit management functions
def get_user_credits(email):
    """Get user's current credit balance"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT credits_balance FROM leads WHERE email = ?', (email,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"Error getting user credits: {e}")
        return 0

def deduct_credits(email, credits_amount, action_type, opportunity_id=None, opportunity_name=None):
    """Deduct credits from user's balance and log usage"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get current balance
        c.execute('SELECT credits_balance, credits_used FROM leads WHERE email = ?', (email,))
        result = c.fetchone()
        if not result:
            return False, "User not found"
        
        current_balance, total_used = result
        
        if current_balance < credits_amount:
            return False, "Insufficient credits"
        
        # Update user's credit balance and usage
        new_balance = current_balance - credits_amount
        new_total_used = total_used + credits_amount
        
        c.execute('''UPDATE leads 
                     SET credits_balance = ?, credits_used = ?, low_credits_alert_sent = ?
                     WHERE email = ?''', 
                  (new_balance, new_total_used, False if new_balance >= 10 else True, email))
        
        # Log the credit usage
        c.execute('''INSERT INTO credits_usage 
                     (user_email, credits_used, action_type, opportunity_id, opportunity_name, usage_date)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (email, credits_amount, action_type, opportunity_id, opportunity_name, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return True, new_balance
        
    except Exception as e:
        print(f"Error deducting credits: {e}")
        return False, str(e)

def add_credits(email, credits_amount, purchase_type, amount_paid, transaction_id=None):
    """Add credits to user's balance and log purchase"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get current balance
        c.execute('SELECT credits_balance FROM leads WHERE email = ?', (email,))
        result = c.fetchone()
        if not result:
            return False, "User not found"
        
        current_balance = result[0]
        new_balance = current_balance + credits_amount
        
        # Update user's credit balance
        c.execute('''UPDATE leads 
                     SET credits_balance = ?, last_credit_purchase_date = ?, low_credits_alert_sent = ?
                     WHERE email = ?''', 
                  (new_balance, datetime.now().isoformat(), False, email))
        
        # Log the credit purchase
        c.execute('''INSERT INTO credits_purchases 
                     (user_email, credits_purchased, amount_paid, purchase_type, transaction_id, purchase_date)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (email, credits_amount, amount_paid, purchase_type, transaction_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return True, new_balance
        
    except Exception as e:
        print(f"Error adding credits: {e}")
        return False, str(e)

def check_low_credits(email):
    """Check if user has low credits and hasn't been alerted"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT credits_balance, low_credits_alert_sent FROM leads WHERE email = ?', (email,))
        result = c.fetchone()
        conn.close()
        
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

# Database setup
def get_db_connection():
    db_path = os.environ.get('DATABASE_URL', 'leads.db')
    # Handle PostgreSQL URL format if needed
    if db_path.startswith('postgresql://'):
        db_path = 'leads.db'  # Fallback to SQLite for now
    return sqlite3.connect(db_path)

def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Create leads table
        c.execute('''CREATE TABLE IF NOT EXISTS leads
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      company_name TEXT NOT NULL,
                      contact_name TEXT NOT NULL,
                      email TEXT NOT NULL,
                      phone TEXT,
                      state TEXT,
                      experience_years TEXT,
                      certifications TEXT,
                      registration_date TEXT,
                      lead_source TEXT DEFAULT 'website',
                      survey_responses TEXT,
                      proposal_support BOOLEAN DEFAULT FALSE,
                      free_leads_remaining INTEGER DEFAULT 3,
                      subscription_status TEXT DEFAULT 'free_trial',
                      credits_balance INTEGER DEFAULT 0,
                      credits_used INTEGER DEFAULT 0,
                      last_credit_purchase_date TEXT,
                      low_credits_alert_sent BOOLEAN DEFAULT FALSE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
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
                      description TEXT,
                      size TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        
        # Add sample Virginia contracts
        # Sample contract data with website URLs - 50+ Government Contracts
        sample_contracts = [
            ('Hampton City Hall Cleaning Services', 'City of Hampton', 'Hampton, VA', '$120,000', '2025-11-15', 'Comprehensive cleaning services for city hall including offices, conference rooms, and public areas. Must include floor waxing and window cleaning.', '561720', 'https://www.hampton.gov/bids'),
            ('Suffolk Municipal Building Janitorial', 'City of Suffolk', 'Suffolk, VA', '$95,000', '2025-11-30', 'Comprehensive janitorial services for municipal buildings including floor care, window cleaning, and waste management.', '561720', 'https://www.suffolkva.us/departments/procurement'),
            ('Virginia Beach Convention Center Cleaning', 'City of Virginia Beach', 'Virginia Beach, VA', '$350,000', '2025-12-31', 'Large-scale cleaning contract for convention center, meeting rooms, and event spaces. Must handle high-volume events.', '561720', 'https://www.vbgov.com/departments/procurement'),
            ('Newport News Library System Maintenance', 'Newport News Public Library', 'Newport News, VA', '$75,000', '2025-11-15', 'Cleaning and maintenance services for 4 library branches including carpet cleaning and HVAC maintenance.', '561720', 'https://www.nngov.com/procurement'),
            ('Williamsburg Historic Area Grounds Keeping', 'Colonial Williamsburg Foundation', 'Williamsburg, VA', '$180,000', '2025-12-18', 'Grounds keeping and facility cleaning for historic buildings and visitor centers. Requires sensitivity to historic preservation.', '561730', 'https://www.colonialwilliamsburg.org/vendors'),
            ('Hampton Roads Transit Facility Cleaning', 'Hampton Roads Transit', 'Hampton, VA', '$220,000', '2025-12-01', 'Cleaning services for bus maintenance facilities, administrative offices, and passenger terminals.', '561720', 'https://www.gohrt.com/about/procurement'),
            ('Suffolk Public Schools Custodial Services', 'Suffolk Public Schools', 'Suffolk, VA', '$450,000', '2025-11-20', 'Custodial services for 5 elementary schools including classrooms, gymnasiums, cafeterias, and administrative areas.', '561720', 'https://www.spsk12.net/departments/procurement'),
            ('Virginia Beach Police Department Cleaning', 'Virginia Beach Police Dept', 'Virginia Beach, VA', '$85,000', '2025-12-10', 'Specialized cleaning services for police facilities including evidence rooms, holding cells, and administrative offices.', '561720', 'https://www.vbgov.com/departments/police/procurement'),
            ('Newport News Shipyard Office Cleaning', 'Newport News Shipbuilding', 'Newport News, VA', '$275,000', '2025-12-20', 'Office cleaning services for shipyard administrative buildings. Security clearance may be required.', '561720', 'https://www.huntingtoningalls.com/suppliers'),
            ('Williamsburg Court House Maintenance', 'James City County', 'Williamsburg, VA', '$65,000', '2025-11-25', 'Cleaning and maintenance services for county courthouse including courtrooms, offices, and public areas.', '561720', 'https://www.jamescitycountyva.gov/procurement'),
            
            # Additional 40 Government Contracts
            ('Hampton Veterans Affairs Medical Center', 'U.S. Department of Veterans Affairs', 'Hampton, VA', '$420,000', '2025-12-05', 'Comprehensive cleaning services for medical facilities including patient rooms, operating areas, and administrative offices.', '561720', 'https://www.va.gov/oal/business/'),
            ('Norfolk Naval Base Housing Cleaning', 'U.S. Navy', 'Norfolk, VA', '$680,000', '2025-11-28', 'Housing cleaning services for military families including interior and exterior maintenance.', '561720', 'https://www.navy.mil/Resources/Doing-Business/'),
            ('Virginia Beach Fire Department Facilities', 'Virginia Beach Fire Dept', 'Virginia Beach, VA', '$145,000', '2025-12-15', 'Cleaning services for 20 fire stations including apparatus bays, living quarters, and training facilities.', '561720', 'https://www.vbgov.com/departments/fire/procurement'),
            ('Portsmouth Naval Hospital Cleaning', 'U.S. Navy Medical Center', 'Portsmouth, VA', '$525,000', '2025-12-22', 'Medical facility cleaning including sterile areas, patient rooms, and laboratory spaces.', '561720', 'https://www.med.navy.mil/Portsmouth/'),
            ('Chesapeake Public Works Building', 'City of Chesapeake', 'Chesapeake, VA', '$78,000', '2025-11-18', 'Municipal building cleaning including vehicle maintenance areas and administrative offices.', '561720', 'https://www.cityofchesapeake.net/procurement'),
            ('Hampton University Research Center', 'Hampton University', 'Hampton, VA', '$165,000', '2025-12-30', 'University research facility cleaning including laboratories, classrooms, and administrative areas.', '561720', 'https://www.hamptonu.edu/purchasing/'),
            ('Suffolk Waste Management Facility', 'City of Suffolk', 'Suffolk, VA', '$95,000', '2025-11-22', 'Specialized cleaning for waste management and recycling facilities including vehicle cleaning.', '561720', 'https://www.suffolkva.us/departments/procurement'),
            ('Newport News Park Facilities', 'Newport News Parks & Recreation', 'Newport News, VA', '$125,000', '2025-12-08', 'Cleaning services for park buildings, visitor centers, and recreational facilities.', '561720', 'https://www.nngov.com/parks'),
            ('Virginia Beach Schools Administration', 'Virginia Beach City Schools', 'Virginia Beach, VA', '$385,000', '2025-12-12', 'Administrative building cleaning for school district headquarters and satellite offices.', '561720', 'https://www.vbschools.com/departments/purchasing'),
            ('Williamsburg Regional Library', 'Williamsburg Regional Library', 'Williamsburg, VA', '$89,000', '2025-11-30', 'Multi-branch library system cleaning including computer labs and reading areas.', '561720', 'https://www.wrl.org/about/procurement'),
            ('Hampton Social Services Building', 'Hampton Dept of Social Services', 'Hampton, VA', '$112,000', '2025-12-03', 'Social services facility cleaning including waiting areas, interview rooms, and offices.', '561720', 'https://www.hampton.gov/departments/social-services'),
            ('Norfolk International Airport Terminal', 'Norfolk Airport Authority', 'Norfolk, VA', '$750,000', '2025-12-18', 'Airport terminal cleaning including gates, baggage areas, restaurants, and administrative offices.', '561720', 'https://www.norfolkairport.com/business/'),
            ('Portsmouth City Hall Complex', 'City of Portsmouth', 'Portsmouth, VA', '$135,000', '2025-11-25', 'City hall and municipal complex cleaning including council chambers and public areas.', '561720', 'https://www.portsmouthva.gov/procurement'),
            ('Chesapeake Regional Medical Center', 'Chesapeake Regional Healthcare', 'Chesapeake, VA', '$485,000', '2025-12-28', 'Hospital cleaning services including patient rooms, surgery suites, and emergency department.', '561720', 'https://www.chesapeakeregional.com/vendors'),
            ('Virginia Beach Convention & Visitors Bureau', 'Virginia Beach CVB', 'Virginia Beach, VA', '$67,000', '2025-11-20', 'Tourism office cleaning including visitor center and administrative areas.', '561720', 'https://www.visitvirginiabeach.com/about/'),
            ('Hampton Roads Bridge-Tunnel Commission', 'HRBT Commission', 'Hampton, VA', '$195,000', '2025-12-14', 'Bridge-tunnel facility cleaning including toll plazas and maintenance buildings.', '561720', 'https://www.hrbt.org/procurement/'),
            ('Suffolk Fire & EMS Headquarters', 'Suffolk Fire & EMS', 'Suffolk, VA', '$88,000', '2025-11-28', 'Fire department headquarters and training facility cleaning.', '561720', 'https://www.suffolkva.us/departments/fire-ems'),
            ('Newport News City Farm', 'Newport News Parks', 'Newport News, VA', '$45,000', '2025-12-01', 'Agricultural facility cleaning including visitor center and education buildings.', '561720', 'https://www.nngov.com/1449/City-Farm'),
            ('Williamsburg Community Health Center', 'Peninsula Health District', 'Williamsburg, VA', '$125,000', '2025-12-10', 'Public health facility cleaning including clinic areas and administrative offices.', '561720', 'https://www.vdh.virginia.gov/peninsula/'),
            ('Virginia Beach Juvenile Detention Center', 'Virginia Beach Sheriff', 'Virginia Beach, VA', '$245,000', '2025-12-20', 'Secure facility cleaning including housing units, administrative areas, and visiting rooms.', '561720', 'https://www.vbgov.com/departments/sheriff/'),
            ('Hampton Coliseum Entertainment Complex', 'Hampton Coliseum', 'Hampton, VA', '$320,000', '2025-12-06', 'Large venue cleaning including arena, concourses, and event spaces.', '561720', 'https://www.hamptoncoliseum.org/business/'),
            ('Norfolk Botanical Garden Facilities', 'Norfolk Botanical Garden', 'Norfolk, VA', '$98,000', '2025-11-24', 'Botanical garden facility cleaning including visitor center and greenhouse complexes.', '561720', 'https://norfolkbotanicalgarden.org/about/'),
            ('Portsmouth Naval Shipyard Museum', 'Portsmouth Museums', 'Portsmouth, VA', '$52,000', '2025-12-02', 'Museum facility cleaning including exhibit areas and administrative offices.', '561720', 'https://www.portsmouthva.gov/museums'),
            ('Chesapeake Bay Bridge Commission', 'CBBT Commission', 'Virginia Beach, VA', '$275,000', '2025-12-16', 'Bridge facility cleaning including visitor center and maintenance areas.', '561720', 'https://www.cbbt.com/about/procurement'),
            ('Suffolk Animal Control Facility', 'Suffolk Animal Control', 'Suffolk, VA', '$85,000', '2025-11-26', 'Animal shelter cleaning including kennels, veterinary areas, and administrative offices.', '561720', 'https://www.suffolkva.us/departments/animal-control'),
            ('Newport News One City Center', 'Newport News Economic Development', 'Newport News, VA', '$155,000', '2025-12-11', 'Municipal office complex cleaning including business development offices.', '561720', 'https://www.nngov.com/economic-development'),
            ('Williamsburg Police Department', 'Williamsburg Police', 'Williamsburg, VA', '$76,000', '2025-11-29', 'Police facility cleaning including evidence rooms and administrative areas.', '561720', 'https://www.williamsburgva.gov/police'),
            ('Virginia Beach Public Works Complex', 'Virginia Beach Public Works', 'Virginia Beach, VA', '$185,000', '2025-12-13', 'Public works facility cleaning including vehicle maintenance and administrative areas.', '561720', 'https://www.vbgov.com/departments/public-works'),
            ('Hampton Roads Regional Jail', 'Hampton Roads Regional Jail', 'Portsmouth, VA', '$385,000', '2025-12-24', 'Correctional facility cleaning including housing units and administrative areas.', '561720', 'https://www.hrrj.org/procurement'),
            ('Norfolk State University Campus', 'Norfolk State University', 'Norfolk, VA', '$425,000', '2025-12-19', 'University campus cleaning including academic buildings and dormitories.', '561720', 'https://www.nsu.edu/purchasing/'),
            ('Portsmouth General Hospital', 'Portsmouth General Hospital', 'Portsmouth, VA', '$465,000', '2025-12-27', 'Hospital cleaning services including all patient care areas and support facilities.', '561720', 'https://www.portsmouthgeneralhospital.com/vendors'),
            ('Chesapeake Arboretum Visitor Center', 'Chesapeake Parks', 'Chesapeake, VA', '$42,000', '2025-11-21', 'Nature center and arboretum facility cleaning including trails and education center.', '561720', 'https://www.cityofchesapeake.net/parks'),
            ('Virginia Beach Oceanfront Hotels Inspection', 'Virginia Beach Health Dept', 'Virginia Beach, VA', '$95,000', '2025-12-09', 'Health department facility cleaning including inspection offices and laboratories.', '561720', 'https://www.vdh.virginia.gov/virginia-beach/'),
            ('Suffolk Nansemond River High School', 'Suffolk Public Schools', 'Suffolk, VA', '$285,000', '2025-12-04', 'High school facility cleaning including classrooms, gymnasium, and cafeteria.', '561720', 'https://www.spsk12.net/departments/procurement'),
            ('Newport News Christopher Newport University', 'Christopher Newport University', 'Newport News, VA', '$365,000', '2025-12-21', 'University campus cleaning including academic and residential buildings.', '561720', 'https://cnu.edu/purchasing/'),
            ('Williamsburg Premium Outlets Management', 'Premium Outlets', 'Williamsburg, VA', '$225,000', '2025-12-07', 'Retail complex cleaning including common areas and restroom facilities.', '561720', 'https://www.premiumoutlets.com/williamsburg'),
            ('Hampton VA Medical Center Outpatient', 'Veterans Affairs', 'Hampton, VA', '$285,000', '2025-12-17', 'VA outpatient clinic cleaning including medical areas and administrative offices.', '561720', 'https://www.va.gov/hampton-virginia-health-care/'),
            ('Norfolk International Terminals', 'Norfolk International Terminals', 'Norfolk, VA', '$485,000', '2025-12-23', 'Port facility cleaning including administrative buildings and maintenance areas.', '561720', 'https://www.norfolkinterminals.com/business/'),
            ('Portsmouth Children\'s Hospital', 'Children\'s Hospital of The King\'s Daughters', 'Portsmouth, VA', '$395,000', '2025-12-26', 'Pediatric hospital cleaning including patient rooms and specialized care areas.', '561720', 'https://www.chkd.org/about/doing-business/'),
            ('Chesapeake Conference Center', 'Chesapeake Conference Center', 'Chesapeake, VA', '$165,000', '2025-12-15', 'Conference facility cleaning including meeting rooms and event spaces.', '561720', 'https://www.chesapeakeconferencecenter.com/vendors'),
            ('Virginia Beach Aquarium & Marine Science', 'Virginia Aquarium Foundation', 'Virginia Beach, VA', '$275,000', '2025-12-29', 'Aquarium facility cleaning including exhibit areas and research laboratories.', '561720', 'https://www.virginiaaquarium.com/about/')
        ]
        
        # Check if contracts already exist
        c.execute('SELECT COUNT(*) FROM contracts')
        if c.fetchone()[0] == 0:
            c.executemany('''INSERT INTO contracts (title, agency, location, value, deadline, description, naics_code, website_url)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', sample_contracts)
            conn.commit()
        
        # Add sample commercial opportunities - 100+ Commercial Leads
        sample_commercial = [
            ('Coastal Dental Group', 'medical', '1234 Hampton Blvd', 'Hampton', 4500, 2800, 'daily', 'General cleaning, sanitization, medical waste disposal', 'HIPAA compliance required, medical-grade disinfectants', 'Office Manager', 'Busy dental practice with 6 operatories requiring daily deep cleaning and sanitization', 'small'),
            ('Hampton Family Fitness', 'fitness', '567 Fitness Way', 'Hampton', 12000, 4200, 'daily', 'Locker rooms, equipment cleaning, floor mopping', 'Early morning access (5 AM), equipment sanitization', 'Facility Manager', 'Full-service gym with locker rooms, pool area, and cardio/weight equipment', 'medium'),
            ('Suffolk Legal Associates', 'legal', '890 Professional Dr', 'Suffolk', 6500, 1800, 'weekly', 'Office cleaning, conference rooms, reception area', 'Confidentiality agreement required, after-hours preferred', 'Managing Partner', 'Law firm specializing in real estate and business law with 12 attorneys', 'medium'),
            ('Oceanfront Medical Center', 'medical', '456 Shore Dr', 'Virginia Beach', 8500, 5200, 'daily', 'Patient rooms, waiting areas, surgical suite cleaning', 'Medical waste handling, infection control protocols', 'Facility Director', 'Urgent care facility with surgical capabilities and imaging department', 'medium'),
            ('Beach Fitness & Wellness', 'fitness', '789 Atlantic Ave', 'Virginia Beach', 15000, 6800, 'daily', 'Gym equipment, locker rooms, pool deck, yoga studios', '24/7 access facility, specialized floor care for pool area', 'General Manager', 'Premier fitness facility with pool, spa, and group fitness studios', 'large'),
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
            ('Hampton Medical Complex', 'medical', '357 Medical Complex Dr', 'Hampton', 24000, 9800, 'daily', 'Hospital outpatient, specialty clinics, diagnostic center', 'Medical complex, hospital standards, multiple specialties', 'Complex Administrator', 'Medical complex with outpatient hospital services', 'large'),
            ('Virginia Beach Corporate Campus', 'office', '486 Corporate Campus Dr', 'Virginia Beach', 35000, 7500, 'weekly', 'Corporate headquarters, training center, cafeteria', 'Corporate campus, multiple buildings, executive standards', 'Campus Facilities Manager', 'Corporate campus with headquarters and training facilities', 'large'),
            ('Suffolk Rehabilitation Hospital', 'medical', '789 Rehabilitation Dr', 'Suffolk', 18000, 8500, 'daily', 'Patient rooms, therapy areas, exercise facilities', 'Rehabilitation hospital, patient mobility, therapeutic equipment', 'Hospital Administrator', 'Rehabilitation hospital with inpatient and outpatient services', 'large'),
            ('Newport News Convention Hotel', 'hospitality', '123 Convention Hotel Dr', 'Newport News', 38000, 13500, 'daily', 'Hotel rooms, convention center, restaurants, retail', 'Convention hotel, large events, multiple dining venues', 'Hotel General Manager', '300-room convention hotel with attached convention center', 'large'),
            ('Williamsburg Medical Center', 'medical', '654 Medical Center Dr', 'Williamsburg', 26000, 11000, 'daily', 'Emergency department, inpatient units, surgical suites', 'Hospital facility, emergency services, surgical standards', 'Chief Operating Officer', 'Regional medical center with emergency and surgical services', 'large'),
            ('Chesapeake Business Campus', 'office', '321 Business Campus Dr', 'Chesapeake', 28000, 6200, 'weekly', 'Multiple office buildings, shared amenities, conference center', 'Business campus, multiple companies, shared services', 'Campus Property Manager', 'Business campus with 50 companies and shared facilities', 'large'),
            ('Portsmouth Regional Hospital', 'medical', '789 Hospital Dr', 'Portsmouth', 45000, 18000, 'daily', 'Patient rooms, operating rooms, emergency department', 'Full-service hospital, all departments, 24/7 operations', 'Director of Environmental Services', '250-bed regional hospital with full medical services', 'large'),
            ('Virginia Beach Medical University', 'education', '456 University Dr', 'Virginia Beach', 55000, 12000, 'weekly', 'Medical school, research labs, clinical facilities', 'Medical university, research standards, clinical training', 'University Facilities Director', 'Medical university with research and clinical training', 'large'),
            ('Norfolk Regional Medical Center', 'medical', '147 Regional Dr', 'Norfolk', 62000, 22000, 'daily', 'All hospital departments, research facilities, medical offices', 'Major medical center, trauma center, research hospital', 'Vice President of Operations', '400-bed academic medical center with trauma services', 'large')
        ]
        
        # Check if commercial opportunities already exist
        c.execute('SELECT COUNT(*) FROM commercial_opportunities')
        if c.fetchone()[0] == 0:
            c.executemany('''INSERT INTO commercial_opportunities 
                             (business_name, business_type, address, location, square_footage, monthly_value, 
                              frequency, services_needed, special_requirements, contact_type, description, size)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', sample_commercial)
            conn.commit()
        
        conn.close()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Continue anyway - app might still work

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get government contracts
        c.execute('SELECT * FROM contracts ORDER BY deadline ASC LIMIT 6')
        contracts = c.fetchall()
        
        # Get commercial opportunities  
        c.execute('SELECT * FROM commercial_opportunities ORDER BY monthly_value DESC LIMIT 6')
        commercial_rows = c.fetchall()
        
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
        
        # Get total commercial count
        c.execute('SELECT COUNT(*) FROM commercial_opportunities')
        commercial_count = c.fetchone()[0]
        
        conn.close()
        return render_template('index.html', 
                             contracts=contracts, 
                             commercial_opportunities=commercial_opportunities,
                             commercial_count=commercial_count)
    except Exception as e:
        # If database doesn't exist, try to initialize it
        if "no such table" in str(e).lower():
            try:
                init_db()
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT * FROM contracts ORDER BY deadline ASC LIMIT 6')
                contracts = c.fetchall()
                c.execute('SELECT * FROM commercial_opportunities ORDER BY monthly_value DESC LIMIT 6')
                commercial_rows = c.fetchall()
                
                commercial_opportunities = []
                for row in commercial_rows:
                    commercial_opportunities.append({
                        'id': row[0], 'business_name': row[1], 'business_type': row[2],
                        'address': row[3], 'location': row[4], 'square_footage': row[5],
                        'monthly_value': row[6], 'frequency': row[7], 'services_needed': row[8],
                        'special_requirements': row[9], 'contact_type': row[10], 
                        'description': row[11], 'size': row[12]
                    })
                
                c.execute('SELECT COUNT(*) FROM commercial_opportunities')
                commercial_count = c.fetchone()[0]
                
                conn.close()
                return render_template('index.html', 
                                     contracts=contracts, 
                                     commercial_opportunities=commercial_opportunities,
                                     commercial_count=commercial_count)
            except Exception as e2:
                return f"<h1>Database Setup Error</h1><p>Error: {str(e2)}</p><p>Try visiting <a href='/init-db'>/init-db</a> to manually initialize the database.</p>"
        return f"<h1>Debug Info</h1><p>Error: {str(e)}</p><p>Flask is working!</p>"

@app.route('/test')
def test():
    return "<h1>Flask Test Route Working!</h1><p>If you see this, Flask is running correctly.</p>"

@app.route('/init-db')
def manual_init_db():
    try:
        init_db()
        return "<h1>Database Initialized!</h1><p>Tables created and sample data loaded.</p>"
    except Exception as e:
        return f"<h1>Database Error</h1><p>Error: {str(e)}</p>"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        company_name = request.form['company_name']
        contact_name = request.form['contact_name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        state = request.form.get('state', '')
        experience_years = request.form.get('experience_years', 0)
        certifications = request.form.get('certifications', '')
        
        # Save to database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO leads (company_name, contact_name, email, phone, 
                     state, experience_years, certifications, free_leads_remaining, credits_balance)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (company_name, contact_name, email, phone, state, 
                   experience_years, certifications, 3, 0))  # Give 3 free leads
        conn.commit()
        conn.close()
        
        # Send email notification
        lead_data = {
            'company_name': company_name,
            'contact_name': contact_name,
            'email': email,
            'phone': phone,
            'state': state,
            'experience_years': experience_years,
            'certifications': certifications
        }
        
        email_sent = send_lead_notification(lead_data)
        if email_sent:
            flash('Registration successful! You can now sign in to access more leads.', 'success')
        else:
            flash('Registration successful! You can now sign in to access more leads.', 'success')
        
        return redirect(url_for('signin', registered='true'))
    
    return render_template('register.html')

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

@app.route('/commercial-contracts')
def commercial_contracts():
    """Commercial cleaning opportunities page"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM commercial_opportunities ORDER BY monthly_value DESC')
    opportunities = []
    
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
    return render_template('commercial_contracts.html', opportunities=opportunities)

@app.route('/request-commercial-contact', methods=['POST'])
def request_commercial_contact():
    """Handle commercial contact requests with credit system"""
    try:
        data = request.get_json()
        opportunity_id = data.get('opportunity_id')
        business_name = data.get('business_name')
        user_email = data.get('user_email', 'demo@example.com')  # In real app, get from session
        
        # Check if user has free leads remaining
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT free_leads_remaining, credits_balance, subscription_status FROM leads WHERE email = ?', (user_email,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return {'success': False, 'message': 'User not found. Please register first.'}, 404
        
        free_leads, credits_balance, subscription_status = result
        
        # If user has free leads, use those first
        if free_leads > 0:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('UPDATE leads SET free_leads_remaining = ? WHERE email = ?', 
                     (free_leads - 1, user_email))
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'Contact information for {business_name} sent to your email!',
                'remaining_free_leads': free_leads - 1,
                'credits_balance': credits_balance,
                'payment_required': False
            }
        
        # Check if user has enough credits (5 credits per lead)
        credits_needed = 5
        if credits_balance < credits_needed:
            return {
                'success': False,
                'message': 'Insufficient credits! You need 5 credits to access this contact information.',
                'credits_balance': credits_balance,
                'credits_needed': credits_needed,
                'payment_required': True,
                'low_credits': True
            }
        
        # Deduct credits
        success, new_balance = deduct_credits(
            user_email, 
            credits_needed, 
            'contact_request', 
            opportunity_id, 
            business_name
        )
        
        if not success:
            return {
                'success': False,
                'message': f'Error processing request: {new_balance}',
                'payment_required': True
            }
        
        # Send contact information (in real implementation)
        # send_contact_email(user_email, business_name, contact_info)
        
        # Check if credits are now low
        low_credits_warning = new_balance <= 10
        out_of_credits = new_balance == 0
        
        response = {
            'success': True,
            'message': f'Contact information for {business_name} sent to your email!',
            'credits_balance': new_balance,
            'credits_used': credits_needed,
            'payment_required': False
        }
        
        if out_of_credits:
            response['out_of_credits'] = True
            response['alert_message'] = 'You\'re out of credits! Purchase more to continue accessing leads.'
        elif low_credits_warning:
            response['low_credits'] = True
            response['alert_message'] = f'Low credits warning! You have {new_balance} credits remaining.'
        
        return response
        
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

@app.route('/customer-leads')
def customer_leads():
    """Customer portal for accessing all leads with advanced features"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get all available leads (both government and commercial)
        government_leads = c.execute('''
            SELECT 
                contracts.id,
                contracts.title,
                contracts.agency,
                contracts.location,
                contracts.description,
                contracts.contract_value,
                contracts.deadline,
                contracts.naics_code,
                contracts.date_posted,
                contracts.website_url,
                'government' as lead_type,
                'General Cleaning' as services_needed,
                'Active' as status,
                contracts.requirements
            FROM contracts 
            ORDER BY contracts.date_posted DESC
        ''').fetchall()
        
        commercial_leads = c.execute('''
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
                '' as website_url,
                'commercial' as lead_type,
                commercial_opportunities.services_needed,
                'Active' as status,
                commercial_opportunities.special_requirements as requirements
            FROM commercial_opportunities 
            ORDER BY commercial_opportunities.id DESC
        ''').fetchall()
        
        # Combine and format leads
        all_leads = []
        
        # Add government leads
        for lead in government_leads:
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
                'application_url': lead[9],
                'lead_type': lead[10],
                'services_needed': lead[11],
                'status': lead[12],
                'requirements': lead[13] or 'Standard government contracting requirements apply.',
                'days_left': calculate_days_left(lead[6])
            }
            all_leads.append(lead_dict)
        
        # Add commercial leads
        for lead in commercial_leads:
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
                'application_url': lead[9],
                'lead_type': lead[10],
                'services_needed': lead[11],
                'status': lead[12],
                'requirements': lead[13] or 'Standard commercial cleaning requirements.',
                'days_left': 30  # Commercial leads are ongoing
            }
            all_leads.append(lead_dict)
        
        conn.close()
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

@app.route('/signin')
def signin():
    """Sign in page for registered users"""
    return render_template('signin.html')

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

# Initialize database for both local and production
try:
    init_db()
except Exception as e:
    print(f"Database initialization warning: {e}")

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)