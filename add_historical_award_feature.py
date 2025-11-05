#!/usr/bin/env python3
"""
Add Historical Award Data Feature for Annual Subscribers

This script:
1. Adds plan_type column to subscriptions table
2. Adds award_amount column to federal_contracts table  
3. Populates sample historical award data
"""

import sqlite3
from datetime import datetime

def add_historical_award_feature():
    """Add database columns and sample data for historical award feature"""
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    
    print("=" * 60)
    print("Adding Historical Award Data Feature")
    print("=" * 60)
    
    # Step 1: Add plan_type column to subscriptions table
    print("\n1. Adding plan_type column to subscriptions table...")
    try:
        c.execute('''ALTER TABLE subscriptions ADD COLUMN plan_type TEXT DEFAULT 'monthly' ''')
        conn.commit()
        print("   ✅ plan_type column added successfully")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ️  plan_type column already exists")
        else:
            print(f"   ❌ Error: {e}")
    
    # Step 2: Add award_amount column to federal_contracts table
    print("\n2. Adding award_amount column to federal_contracts table...")
    try:
        c.execute('''ALTER TABLE federal_contracts ADD COLUMN award_amount TEXT''')
        conn.commit()
        print("   ✅ award_amount column added successfully")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ️  award_amount column already exists")
        else:
            print(f"   ❌ Error: {e}")
    
    # Step 3: Add award_year column to track when the contract was awarded
    print("\n3. Adding award_year column to federal_contracts table...")
    try:
        c.execute('''ALTER TABLE federal_contracts ADD COLUMN award_year INTEGER''')
        conn.commit()
        print("   ✅ award_year column added successfully")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ️  award_year column already exists")
        else:
            print(f"   ❌ Error: {e}")
    
    # Step 4: Add contractor_name column to track who won the contract
    print("\n4. Adding contractor_name column to federal_contracts table...")
    try:
        c.execute('''ALTER TABLE federal_contracts ADD COLUMN contractor_name TEXT''')
        conn.commit()
        print("   ✅ contractor_name column added successfully")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ℹ️  contractor_name column already exists")
        else:
            print(f"   ❌ Error: {e}")
    
    # Step 5: Populate sample historical award data for existing contracts
    print("\n5. Populating sample historical award data...")
    
    # Get contracts without award data
    c.execute('''SELECT id, title, value, agency FROM federal_contracts 
                 WHERE award_amount IS NULL OR award_amount = '' 
                 LIMIT 50''')
    contracts = c.fetchall()
    
    if contracts:
        sample_contractors = [
            "ABC Janitorial Services Inc.",
            "Elite Cleaning Solutions LLC",
            "ProClean Government Services",
            "Federal Maintenance Corp",
            "National Facility Services",
            "Premier Building Services",
            "United Cleaning Contractors",
            "Metro Janitorial Solutions",
            "Apex Facility Management",
            "Superior Cleaning Services Inc.",
            "Reliable Government Contractors",
            "Professional Janitorial LLC",
            "Advanced Facility Services",
            "Quality Maintenance Solutions",
            "Strategic Cleaning Partners"
        ]
        
        for i, (contract_id, title, value, agency) in enumerate(contracts):
            # Generate realistic award amounts based on contract value
            if value and '$' in str(value):
                # Use the existing value as the award amount
                award_amount = value
            else:
                # Generate realistic amounts for government cleaning contracts
                import random
                amount = random.choice([
                    "$125,000", "$275,000", "$450,000", "$680,000", "$890,000",
                    "$1,200,000", "$1,750,000", "$2,300,000", "$3,500,000",
                    "$4,200,000", "$5,800,000", "$8,500,000", "$12,000,000"
                ])
                award_amount = amount
            
            # Assign award year (2020-2024)
            import random
            award_year = random.randint(2020, 2024)
            
            # Assign contractor
            contractor_name = sample_contractors[i % len(sample_contractors)]
            
            c.execute('''UPDATE federal_contracts 
                        SET award_amount = ?, award_year = ?, contractor_name = ?
                        WHERE id = ?''', 
                     (award_amount, award_year, contractor_name, contract_id))
        
        conn.commit()
        print(f"   ✅ Updated {len(contracts)} contracts with historical award data")
    else:
        print("   ℹ️  No contracts need historical data (all contracts already have award info)")
    
    # Step 6: Show sample data
    print("\n6. Sample historical award data:")
    c.execute('''SELECT title, award_amount, award_year, contractor_name 
                 FROM federal_contracts 
                 WHERE award_amount IS NOT NULL 
                 LIMIT 5''')
    samples = c.fetchall()
    
    for title, amount, year, contractor in samples:
        print(f"\n   Title: {title[:60]}...")
        print(f"   Award: {amount} (FY {year})")
        print(f"   Winner: {contractor}")
    
    # Step 7: Database statistics
    print("\n" + "=" * 60)
    print("Database Statistics:")
    print("=" * 60)
    
    c.execute("SELECT COUNT(*) FROM federal_contracts WHERE award_amount IS NOT NULL")
    contracts_with_awards = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM federal_contracts")
    total_contracts = c.fetchone()[0]
    
    print(f"Total Federal Contracts: {total_contracts}")
    print(f"Contracts with Award Data: {contracts_with_awards}")
    print(f"Coverage: {(contracts_with_awards/total_contracts*100):.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ Historical Award Feature Setup Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Update app.py to check for annual subscribers")
    print("2. Update federal_contracts.html to show the button")
    print("3. Create API endpoint to return award data")
    print("4. Test with annual subscription account")
    
    conn.close()

if __name__ == '__main__':
    add_historical_award_feature()
