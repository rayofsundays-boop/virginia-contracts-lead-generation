"""
Database utility functions for PostgreSQL/SQLite compatibility
"""
import os

def init_db_with_sqlalchemy(app):
    """Initialize database with SQLAlchemy for PostgreSQL/SQLite compatibility"""
    from sqlalchemy import text
    from app import db
    
    with app.app_context():
        try:
            # Create all tables using SQLAlchemy
            # For PostgreSQL, use SERIAL; for SQLite, use AUTOINCREMENT
            is_postgres = 'postgresql' in str(db.engine.url)
            
            if is_postgres:
                id_type = "SERIAL PRIMARY KEY"
            else:
                id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
            
            queries = [
                # Leads table
                f"""CREATE TABLE IF NOT EXISTS leads (
                    id {id_type},
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                
                # Credits purchases table
                f"""CREATE TABLE IF NOT EXISTS credits_purchases (
                    id {id_type},
                    user_email TEXT NOT NULL,
                    credits_purchased INTEGER NOT NULL,
                    amount_paid REAL NOT NULL,
                    purchase_type TEXT NOT NULL,
                    transaction_id TEXT,
                    payment_method TEXT DEFAULT 'credit_card',
                    payment_reference TEXT,
                    purchase_date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                
                # Credits usage table
                f"""CREATE TABLE IF NOT EXISTS credits_usage (
                    id {id_type},
                    user_email TEXT NOT NULL,
                    credits_used INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    opportunity_id TEXT,
                    opportunity_name TEXT,
                    usage_date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                
                # Survey responses table
                f"""CREATE TABLE IF NOT EXISTS survey_responses (
                    id {id_type},
                    biggest_challenge TEXT,
                    annual_revenue TEXT,
                    company_size TEXT,
                    contract_experience TEXT,
                    main_focus TEXT,
                    pain_point_scenario TEXT,
                    submission_date TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                
                # Subscriptions table
                f"""CREATE TABLE IF NOT EXISTS subscriptions (
                    id {id_type},
                    email TEXT NOT NULL,
                    cardholder_name TEXT,
                    total_amount TEXT,
                    proposal_support BOOLEAN DEFAULT FALSE,
                    subscription_date TEXT,
                    status TEXT DEFAULT 'active',
                    monthly_credits INTEGER DEFAULT 50,
                    next_billing_date TEXT,
                    last_credits_allocated_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                
                # Contracts table
                f"""CREATE TABLE IF NOT EXISTS contracts (
                    id {id_type},
                    title TEXT NOT NULL,
                    agency TEXT NOT NULL,
                    location TEXT,
                    value TEXT,
                    deadline DATE,
                    description TEXT,
                    naics_code TEXT,
                    website_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
                
                # Commercial opportunities table
                f"""CREATE TABLE IF NOT EXISTS commercial_opportunities (
                    id {id_type},
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
                    website_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            ]
            
            for query in queries:
                db.session.execute(text(query))
            
            db.session.commit()
            print("✅ Database tables created successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            db.session.rollback()
            return False
