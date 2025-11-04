"""
Create proposal_reviews table for Render PostgreSQL database
Run this in Render shell: python create_proposal_reviews_table.py
"""

import os
import psycopg
from urllib.parse import urlparse

# Get database URL from environment
database_url = os.environ.get('DATABASE_URL')

if not database_url:
    print("❌ DATABASE_URL environment variable not set")
    exit(1)

# Parse the URL
url = urlparse(database_url)

# Connect to PostgreSQL
conn = psycopg.connect(
    dbname=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

try:
    cursor = conn.cursor()
    
    # Create proposal_reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proposal_reviews (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
            user_email TEXT NOT NULL,
            client_name TEXT NOT NULL,
            business_name TEXT,
            phone TEXT,
            title TEXT NOT NULL,
            solicitation_number TEXT,
            contract_type TEXT NOT NULL,
            proposal_length TEXT,
            deadline TEXT,
            description TEXT,
            service_level TEXT DEFAULT 'standard',
            base_price DECIMAL(10,2),
            total_amount DECIMAL(10,2),
            writer_fee DECIMAL(10,2),
            status TEXT DEFAULT 'pending',
            submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_date TIMESTAMP,
            completed_date TIMESTAMP,
            payment_status TEXT DEFAULT 'pending',
            client_rating INTEGER,
            client_feedback TEXT,
            admin_response TEXT,
            proposal_content TEXT,
            proposal_file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_proposal_reviews_user_id 
        ON proposal_reviews(user_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_proposal_reviews_status 
        ON proposal_reviews(status)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_proposal_reviews_payment_status 
        ON proposal_reviews(payment_status)
    ''')
    
    conn.commit()
    print("✅ Proposal reviews table created successfully!")
    
    # Verify table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'proposal_reviews'
        )
    """)
    exists = cursor.fetchone()[0]
    
    if exists:
        print("✅ Verified: Table exists in database")
    else:
        print("❌ Warning: Table creation may have failed")
    
except Exception as e:
    print(f"❌ Error creating table: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
