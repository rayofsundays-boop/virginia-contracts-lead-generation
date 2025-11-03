#!/usr/bin/env python3
"""
Script to populate federal_contracts table with sample data for testing.
Run this script to add sample federal contracts to your database.
"""

import sqlite3
from datetime import datetime, timedelta

# Sample federal contracts data
sample_contracts = [
    {
        'title': 'Custodial Services - VA Medical Center',
        'agency': 'Department of Veterans Affairs',
        'department': 'Veterans Health Administration',
        'location': 'Hampton, VA',
        'value': '$500,000 - $1,000,000',
        'deadline': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        'description': 'Comprehensive custodial and janitorial services for VA Medical Center including daily cleaning, floor care, and specialized medical facility cleaning.',
        'naics_code': '561720',
        'sam_gov_url': 'https://sam.gov/opp/example1',
        'notice_id': 'VA-2025-001',
        'set_aside': 'Small Business',
        'posted_date': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'title': 'Building Maintenance and Cleaning - Naval Station Norfolk',
        'agency': 'Department of Defense',
        'department': 'U.S. Navy',
        'location': 'Norfolk, VA',
        'value': '$750,000 - $1,500,000',
        'deadline': (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
        'description': 'Full-service building maintenance and cleaning for Naval Station Norfolk facilities including administrative buildings, training centers, and support facilities.',
        'naics_code': '561720',
        'sam_gov_url': 'https://sam.gov/opp/example2',
        'notice_id': 'DOD-NAVY-2025-002',
        'set_aside': 'Service-Disabled Veteran-Owned',
        'posted_date': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'title': 'Janitorial Services - Coast Guard Base Portsmouth',
        'agency': 'Department of Homeland Security',
        'department': 'U.S. Coast Guard',
        'location': 'Portsmouth, VA',
        'value': '$250,000 - $500,000',
        'deadline': (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
        'description': 'Daily janitorial services for Coast Guard Base Portsmouth including office cleaning, restroom maintenance, and facility upkeep.',
        'naics_code': '561720',
        'sam_gov_url': 'https://sam.gov/opp/example3',
        'notice_id': 'DHS-USCG-2025-003',
        'set_aside': 'Unrestricted',
        'posted_date': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'title': 'Federal Building Custodial Services - Newport News',
        'agency': 'General Services Administration',
        'department': 'Public Buildings Service',
        'location': 'Newport News, VA',
        'value': '$400,000 - $800,000',
        'deadline': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
        'description': 'Custodial services for GSA-managed federal buildings in Newport News including routine cleaning, floor care, window cleaning, and waste management.',
        'naics_code': '561720',
        'sam_gov_url': 'https://sam.gov/opp/example4',
        'notice_id': 'GSA-PBS-2025-004',
        'set_aside': 'Women-Owned Small Business',
        'posted_date': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'title': 'Specialized Cleaning Services - NASA Langley Research Center',
        'agency': 'National Aeronautics and Space Administration',
        'department': 'Langley Research Center',
        'location': 'Hampton, VA',
        'value': '$600,000 - $1,200,000',
        'deadline': (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d'),
        'description': 'Specialized cleaning services for NASA Langley Research Center including cleanroom maintenance, laboratory cleaning, and general facility services.',
        'naics_code': '561720',
        'sam_gov_url': 'https://sam.gov/opp/example5',
        'notice_id': 'NASA-LARC-2025-005',
        'set_aside': 'Small Business',
        'posted_date': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'title': 'Post Office Cleaning Services - Virginia Beach',
        'agency': 'United States Postal Service',
        'department': 'Facilities Management',
        'location': 'Virginia Beach, VA',
        'value': '$150,000 - $300,000',
        'deadline': (datetime.now() + timedelta(days=28)).strftime('%Y-%m-%d'),
        'description': 'Daily cleaning and maintenance services for USPS facilities in Virginia Beach including lobby areas, sorting facilities, and employee areas.',
        'naics_code': '561720',
        'sam_gov_url': 'https://sam.gov/opp/example6',
        'notice_id': 'USPS-2025-006',
        'set_aside': 'HUBZone',
        'posted_date': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'title': 'Federal Courthouse Janitorial Services',
        'agency': 'U.S. Courts',
        'department': 'Administrative Office',
        'location': 'Norfolk, VA',
        'value': '$450,000 - $900,000',
        'deadline': (datetime.now() + timedelta(days=50)).strftime('%Y-%m-%d'),
        'description': 'Comprehensive janitorial services for federal courthouse including courtrooms, offices, public areas, and secure facilities.',
        'naics_code': '561720',
        'sam_gov_url': 'https://sam.gov/opp/example7',
        'notice_id': 'USCOURTS-2025-007',
        'set_aside': 'Small Business',
        'posted_date': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'title': 'Military Base Housing Cleaning - Fort Eustis',
        'agency': 'Department of Defense',
        'department': 'U.S. Army',
        'location': 'Newport News, VA',
        'value': '$350,000 - $700,000',
        'deadline': (datetime.now() + timedelta(days=40)).strftime('%Y-%m-%d'),
        'description': 'Cleaning services for military base housing and common areas at Fort Eustis including move-in/move-out cleaning and regular maintenance.',
        'naics_code': '561720',
        'sam_gov_url': 'https://sam.gov/opp/example8',
        'notice_id': 'DOD-ARMY-2025-008',
        'set_aside': 'Service-Disabled Veteran-Owned',
        'posted_date': datetime.now().strftime('%Y-%m-%d')
    }
]

def populate_database():
    """Populate the federal_contracts table with sample data."""
    try:
        # Connect to database
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        print("📊 Populating federal_contracts table with sample data...")
        print(f"   Adding {len(sample_contracts)} sample contracts...")
        
        inserted = 0
        skipped = 0
        
        for contract in sample_contracts:
            try:
                cursor.execute('''
                    INSERT INTO federal_contracts 
                    (title, agency, department, location, value, deadline, description, 
                     naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    contract['title'],
                    contract['agency'],
                    contract['department'],
                    contract['location'],
                    contract['value'],
                    contract['deadline'],
                    contract['description'],
                    contract['naics_code'],
                    contract['sam_gov_url'],
                    contract['notice_id'],
                    contract['set_aside'],
                    contract['posted_date']
                ))
                inserted += 1
            except sqlite3.IntegrityError:
                # Contract with this notice_id already exists
                skipped += 1
                continue
        
        conn.commit()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM federal_contracts')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Successfully populated federal contracts!")
        print(f"   Inserted: {inserted} new contracts")
        print(f"   Skipped: {skipped} (already exist)")
        print(f"   Total in database: {total} contracts")
        print("\n🎉 Database is ready! Refresh your federal contracts page to see the data.")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        return False
    
    return True

if __name__ == '__main__':
    populate_database()
