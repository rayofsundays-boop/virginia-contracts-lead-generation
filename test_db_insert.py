"""
Test database insertion for federal contracts
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, text

# Get database URL from environment or use local
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///leads.db')

# Fix postgres:// to postgresql://
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if DATABASE_URL and 'postgresql://' in DATABASE_URL and '+psycopg' not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

print(f"Database URL: {DATABASE_URL[:50]}...")

# Create engine
engine = create_engine(DATABASE_URL)

# Test data
test_contracts = [
    {
        'title': 'Janitorial Services - VA Hospital',
        'agency': 'Department of Veterans Affairs',
        'department': 'VA Medical Center',
        'location': 'Hampton, VA',
        'contract_value': '$50,000',
        'posted_date': '2024-11-01',
        'deadline': '2024-12-01',
        'description': 'Comprehensive janitorial services for VA medical facility',
        'contact_info': 'VA Contracting Office',
        'bid_link': 'https://www.usaspending.gov/award/TEST001'
    },
    {
        'title': 'Cleaning Services - Federal Building',
        'agency': 'General Services Administration',
        'department': 'GSA Region 3',
        'location': 'Newport News, VA',
        'contract_value': '$75,000',
        'posted_date': '2024-11-02',
        'deadline': '2024-12-15',
        'description': 'Daily cleaning and maintenance services',
        'contact_info': 'GSA Contracting',
        'bid_link': 'https://www.usaspending.gov/award/TEST002'
    },
    {
        'title': 'Facility Maintenance Contract',
        'agency': 'Department of Defense',
        'department': 'Navy',
        'location': 'Virginia Beach, VA',
        'contract_value': '$100,000',
        'posted_date': '2024-11-03',
        'deadline': '2024-12-20',
        'description': 'Facility cleaning and maintenance for naval station',
        'contact_info': 'Navy Contracting Office',
        'bid_link': 'https://www.usaspending.gov/award/TEST003'
    }
]

print("\n" + "="*70)
print("TESTING DATABASE INSERT")
print("="*70)

try:
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT COUNT(*) FROM federal_contracts
        """))
        count = result.fetchone()[0]
        print(f"\n✅ Connection successful!")
        print(f"📊 Current contracts in database: {count}")
        
        # Insert test contracts
        print(f"\n📝 Inserting {len(test_contracts)} test contracts...")
        
        for contract in test_contracts:
            # Check if already exists
            check = conn.execute(text("""
                SELECT COUNT(*) FROM federal_contracts WHERE title = :title
            """), {'title': contract['title']})
            
            if check.fetchone()[0] == 0:
                conn.execute(text("""
                    INSERT INTO federal_contracts 
                    (title, agency, department, location, contract_value, posted_date, 
                     deadline, description, contact_info, bid_link)
                    VALUES (:title, :agency, :department, :location, :contract_value, 
                            :posted_date, :deadline, :description, :contact_info, :bid_link)
                """), contract)
                print(f"   ✅ Inserted: {contract['title']}")
            else:
                print(f"   ⏭️  Skipped (exists): {contract['title']}")
        
        conn.commit()
        
        # Check final count
        result = conn.execute(text("SELECT COUNT(*) FROM federal_contracts"))
        final_count = result.fetchone()[0]
        print(f"\n✅ Final count: {final_count} contracts in database")
        
        # Show sample
        print(f"\n📋 Sample contracts:")
        result = conn.execute(text("SELECT title, agency, location FROM federal_contracts LIMIT 5"))
        for row in result:
            print(f"   • {row[0]} - {row[1]} ({row[2]})")
        
        print("\n" + "="*70)
        print("✅ TEST COMPLETE - Check /federal-contracts page")
        print("="*70)
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
