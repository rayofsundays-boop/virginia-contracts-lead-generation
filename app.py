import os
import json
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mail import Mail, Message
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'virginia-contracting-fallback-key-2024')

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'noreply@vacontracts.com')

mail = Mail(app)

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
                      next_billing_date TEXT,
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
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        
        # Add sample Virginia contracts
        sample_contracts = [
            ('Hampton City Hall Cleaning Services', 'City of Hampton', 'Hampton, VA', '$125,000', '2025-12-15', 'Daily cleaning services for City Hall including offices, restrooms, and common areas. 5-year contract with annual renewal options.', '561720'),
            ('Suffolk Municipal Building Janitorial', 'City of Suffolk', 'Suffolk, VA', '$95,000', '2025-11-30', 'Comprehensive janitorial services for municipal buildings including floor care, window cleaning, and waste management.', '561720'),
            ('Virginia Beach Convention Center Cleaning', 'City of Virginia Beach', 'Virginia Beach, VA', '$350,000', '2025-12-31', 'Large-scale cleaning contract for convention center, meeting rooms, and event spaces. Must handle high-volume events.', '561720'),
            ('Newport News Library System Maintenance', 'Newport News Public Library', 'Newport News, VA', '$75,000', '2025-11-15', 'Cleaning and maintenance services for 4 library branches including carpet cleaning and HVAC maintenance.', '561720'),
            ('Williamsburg Historic Area Grounds Keeping', 'Colonial Williamsburg Foundation', 'Williamsburg, VA', '$180,000', '2025-12-18', 'Grounds keeping and facility cleaning for historic buildings and visitor centers. Requires sensitivity to historic preservation.', '561730'),
            ('Hampton Roads Transit Facility Cleaning', 'Hampton Roads Transit', 'Hampton, VA', '$220,000', '2025-12-01', 'Cleaning services for bus maintenance facilities, administrative offices, and passenger terminals.', '561720'),
            ('Suffolk Public Schools Custodial Services', 'Suffolk Public Schools', 'Suffolk, VA', '$450,000', '2025-11-20', 'Custodial services for 5 elementary schools including classrooms, gymnasiums, cafeterias, and administrative areas.', '561720'),
            ('Virginia Beach Police Department Cleaning', 'Virginia Beach Police Dept', 'Virginia Beach, VA', '$85,000', '2025-12-10', 'Specialized cleaning services for police facilities including evidence rooms, holding cells, and administrative offices.', '561720'),
            ('Newport News Shipyard Office Cleaning', 'Newport News Shipbuilding', 'Newport News, VA', '$275,000', '2025-12-20', 'Office cleaning services for shipyard administrative buildings. Security clearance may be required.', '561720'),
            ('Williamsburg Court House Maintenance', 'James City County', 'Williamsburg, VA', '$65,000', '2025-11-25', 'Cleaning and maintenance services for county courthouse including courtrooms, offices, and public areas.', '561720')
        ]
        
        # Check if contracts already exist
        c.execute('SELECT COUNT(*) FROM contracts')
        if c.fetchone()[0] == 0:
            c.executemany('''INSERT INTO contracts (title, agency, location, value, deadline, description, naics_code)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''', sample_contracts)
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
        c.execute('SELECT * FROM contracts ORDER BY deadline ASC LIMIT 10')
        contracts = c.fetchall()
        conn.close()
        return render_template('index.html', contracts=contracts)
    except Exception as e:
        # If database doesn't exist, try to initialize it
        if "no such table" in str(e).lower():
            try:
                init_db()
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT * FROM contracts ORDER BY deadline ASC LIMIT 10')
                contracts = c.fetchall()
                conn.close()
                return render_template('index.html', contracts=contracts)
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
                     state, experience_years, certifications)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (company_name, contact_name, email, phone, state, 
                   experience_years, certifications))
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
            flash('Registration successful! We\'ll send you contract opportunities.', 'success')
        else:
            flash('Registration successful! We\'ll send you contract opportunities. (Email notification pending)', 'success')
        
        return redirect(url_for('index'))
    
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

# Initialize database for both local and production
try:
    init_db()
except Exception as e:
    print(f"Database initialization warning: {e}")

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)