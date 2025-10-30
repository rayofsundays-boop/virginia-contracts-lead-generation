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
        
        # Add sample commercial opportunities
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
            ('Hampton Shared Workspace', 'office', '753 Cowork St', 'Hampton', 8000, 2200, 'daily', 'Open workspace, private offices, meeting rooms, kitchen', 'Flexible membership space, technology cleaning, phone booth sanitization', 'Community Manager', 'Modern coworking space for entrepreneurs and remote workers', 'medium'),
            ('Little Learners Academy', 'childcare', '624 Academy Ave', 'Newport News', 6200, 3100, 'daily', 'Infant rooms, toddler areas, preschool classrooms, playground equipment', 'State licensing requirements, outdoor equipment cleaning, meal prep areas', 'Assistant Director', 'Full-service daycare and preschool with infant care and after-school programs', 'medium'),
            ('Norfolk Wellness Center', 'medical', '795 Wellness Way', 'Norfolk', 9500, 5800, 'daily', 'Treatment rooms, hydrotherapy pool, rehabilitation gym, offices', 'Medical equipment cleaning, pool chemical balance, physical therapy equipment', 'Clinical Coordinator', 'Comprehensive rehabilitation center with pool therapy and sports medicine', 'medium')
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
    """Handle commercial contact requests"""
    try:
        data = request.get_json()
        opportunity_id = data.get('opportunity_id')
        business_name = data.get('business_name')
        
        # In a real implementation, you would:
        # 1. Check user's remaining free leads
        # 2. Provide actual contact information
        # 3. Update user's lead count
        # 4. Send email with contact details
        
        # For demo purposes, simulate the response
        return {
            'success': True,
            'message': f'Contact information for {business_name} sent to your email!',
            'remaining_leads': 2  # Simulate remaining leads
        }
        
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

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