#!/usr/bin/env python3
"""
Quick script to populate federal contracts - run this in Render shell
Usage: python quick_populate.py
"""
import os
from sqlalchemy import create_engine, text

# Get database URL
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    exit(1)

# Fix postgres:// to postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
if 'postgresql://' in DATABASE_URL and '+psycopg' not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

print("Connecting to database...")
engine = create_engine(DATABASE_URL)

sample_contracts = [
    ('Janitorial Services - VA Medical Center Hampton', 'Department of Veterans Affairs', 'VA Medical Center', 'Hampton, VA', '$250,000', '2024-11-01', '2024-12-15', 'Comprehensive janitorial and cleaning services', '561720', 'https://sam.gov/opp/1', 'VA-001', 'Small Business'),
    ('Facility Cleaning - Naval Station Norfolk', 'Department of Defense', 'Department of the Navy', 'Norfolk, VA', '$500,000', '2024-11-02', '2024-12-20', 'Professional cleaning services for naval facilities', '561720', 'https://sam.gov/opp/2', 'DOD-002', ''),
    ('Building Maintenance - Newport News', 'General Services Administration', 'GSA Region 3', 'Newport News, VA', '$150,000', '2024-11-03', '2025-01-15', 'Janitorial and custodial services', '561720', 'https://sam.gov/opp/3', 'GSA-003', 'SDVOSB'),
    ('Cleaning - Virginia Beach Courthouse', 'U.S. Courts', 'Judicial Branch', 'Virginia Beach, VA', '$180,000', '2024-10-28', '2024-12-10', 'Daily cleaning for federal courthouse', '561720', 'https://sam.gov/opp/4', 'COURT-004', '8(a)'),
    ('Custodial Services - Suffolk', 'General Services Administration', 'GSA Region 3', 'Suffolk, VA', '$120,000', '2024-10-25', '2024-12-05', 'Custodial services for federal building', '561720', 'https://sam.gov/opp/5', 'GSA-005', 'WOSB'),
]

with engine.connect() as conn:
    added = 0
    for contract in sample_contracts:
        try:
            conn.execute(text("""
                INSERT INTO federal_contracts 
                (title, agency, department, location, value, posted_date, deadline, 
                 description, naics_code, sam_gov_url, notice_id, set_aside)
                VALUES (:t, :a, :d, :l, :v, :p, :dl, :desc, :n, :s, :nid, :sa)
            """), {
                't': contract[0], 'a': contract[1], 'd': contract[2], 'l': contract[3],
                'v': contract[4], 'p': contract[5], 'dl': contract[6], 'desc': contract[7],
                'n': contract[8], 's': contract[9], 'nid': contract[10], 'sa': contract[11]
            })
            conn.commit()
            added += 1
            print(f"✅ Added: {contract[0]}")
        except Exception as e:
            print(f"⚠️  Skipped (may exist): {contract[0]}")
    
    result = conn.execute(text("SELECT COUNT(*) FROM federal_contracts"))
    total = result.fetchone()[0]
    print(f"\n✅ Done! {added} added, {total} total contracts in database")
