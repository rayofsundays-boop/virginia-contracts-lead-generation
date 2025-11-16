#!/usr/bin/env python3
"""
Create database tables for 1099 Cleaner Requests feature
Run this script once to set up all required tables
"""

import sqlite3
from datetime import datetime

def create_tables():
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    print("Creating 1099 Cleaner Request tables...")
    
    # Table 1: cleaner_requests (main request data)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cleaner_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            service_category TEXT NOT NULL,
            description TEXT NOT NULL,
            pay_rate TEXT NOT NULL,
            start_date TEXT NOT NULL,
            urgency TEXT NOT NULL,
            background_check_required TEXT NOT NULL,
            equipment_required TEXT NOT NULL,
            status TEXT DEFAULT 'pending_review',
            denial_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by TEXT,
            denied_at TIMESTAMP,
            denied_by TEXT
        )
    ''')
    print("✅ Created cleaner_requests table")
    
    # Table 2: cleaner_request_notes (admin internal notes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cleaner_request_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id TEXT UNIQUE NOT NULL,
            request_id TEXT NOT NULL,
            admin_email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES cleaner_requests(request_id)
        )
    ''')
    print("✅ Created cleaner_request_notes table")
    
    # Table 3: cleaner_request_messages (two-way messaging)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cleaner_request_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            request_id TEXT NOT NULL,
            sender_type TEXT NOT NULL,
            sender_email TEXT NOT NULL,
            sender_name TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES cleaner_requests(request_id)
        )
    ''')
    print("✅ Created cleaner_request_messages table")
    
    # Table 4: cleaner_request_forum_posts (published to community forum)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cleaner_request_forum_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT UNIQUE NOT NULL,
            request_id TEXT NOT NULL,
            title TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            service_category TEXT NOT NULL,
            pay_rate TEXT NOT NULL,
            description TEXT NOT NULL,
            urgency TEXT NOT NULL,
            background_check_required TEXT NOT NULL,
            equipment_required TEXT NOT NULL,
            start_date TEXT NOT NULL,
            contact_email TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            company_name TEXT NOT NULL,
            published INTEGER DEFAULT 1,
            views INTEGER DEFAULT 0,
            responses INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES cleaner_requests(request_id)
        )
    ''')
    print("✅ Created cleaner_request_forum_posts table")
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cleaner_requests_status ON cleaner_requests(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cleaner_requests_email ON cleaner_requests(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cleaner_messages_request ON cleaner_request_messages(request_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_forum_posts_published ON cleaner_request_forum_posts(published)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_forum_posts_category ON cleaner_request_forum_posts(service_category)')
    print("✅ Created database indexes")
    
    conn.commit()
    conn.close()
    
    print("\n✅ All tables created successfully!")
    print("\nTables created:")
    print("  1. cleaner_requests - Main request data")
    print("  2. cleaner_request_notes - Admin internal notes")
    print("  3. cleaner_request_messages - Two-way messaging")
    print("  4. cleaner_request_forum_posts - Published forum posts")
    print("\nYou can now run the Flask application.")

if __name__ == '__main__':
    create_tables()
