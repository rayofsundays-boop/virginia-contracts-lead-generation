from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'virginia-contracting-secret-key-2024'

# Database setup
def init_db():
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    
    # Create leads table
    c.execute('''CREATE TABLE IF NOT EXISTS leads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  company_name TEXT NOT NULL,
                  contact_name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  phone TEXT,
                  state TEXT,
                  experience_years INTEGER,
                  certifications TEXT,
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

@app.route('/')
def index():
    try:
        conn = sqlite3.connect('leads.db')
        c = conn.cursor()
        c.execute('SELECT * FROM contracts ORDER BY deadline ASC LIMIT 10')
        contracts = c.fetchall()
        conn.close()
        return render_template('index.html', contracts=contracts)
    except Exception as e:
        return f"<h1>Debug Info</h1><p>Error: {str(e)}</p><p>Flask is working!</p>"

@app.route('/test')
def test():
    return "<h1>Flask Test Route Working!</h1><p>If you see this, Flask is running correctly.</p>"

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
        
        conn = sqlite3.connect('leads.db')
        c = conn.cursor()
        c.execute('''INSERT INTO leads (company_name, contact_name, email, phone, 
                     state, experience_years, certifications)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (company_name, contact_name, email, phone, state, 
                   experience_years, certifications))
        conn.commit()
        conn.close()
        
        flash('Registration successful! We\'ll send you contract opportunities.', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/contracts')
def contracts():
    location_filter = request.args.get('location', '')
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    
    if location_filter:
        c.execute('SELECT * FROM contracts WHERE location LIKE ? ORDER BY deadline ASC', 
                  (f'%{location_filter}%',))
    else:
        c.execute('SELECT * FROM contracts ORDER BY deadline ASC')
    
    all_contracts = c.fetchall()
    conn.close()
    
    # Get unique locations for filter dropdown
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT location FROM contracts ORDER BY location')
    locations = [row[0] for row in c.fetchall()]
    conn.close()
    
    return render_template('contracts.html', contracts=all_contracts, locations=locations, current_filter=location_filter)

@app.route('/leads')
def leads():
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute('SELECT * FROM leads ORDER BY created_at DESC')
    all_leads = c.fetchall()
    conn.close()
    return render_template('leads.html', leads=all_leads)

if __name__ == '__main__':
    init_db()
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)