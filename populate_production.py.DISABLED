"""
Populate Production Database with Federal Contracts
Run this script to upload contracts from local database to production (Render.com)
"""
import os
import sys
import requests
from datetime import datetime

def get_local_contracts():
    """Get contracts from local SQLite database"""
    import sqlite3
    
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT title, agency, department, description, location, 
               contract_value, posted_date, deadline, contact_info, bid_link
        FROM federal_contracts
    """)
    
    contracts = []
    for row in cursor.fetchall():
        contracts.append({
            'title': row[0],
            'agency': row[1],
            'department': row[2],
            'description': row[3],
            'location': row[4],
            'contract_value': row[5],
            'posted_date': row[6],
            'deadline': row[7],
            'contact_info': row[8],
            'bid_link': row[9]
        })
    
    conn.close()
    return contracts

def upload_to_production(contracts, production_url):
    """Upload contracts to production via API endpoint"""
    print(f"\n📤 Uploading {len(contracts)} contracts to production...")
    
    # This would require creating an admin API endpoint on your app
    # For now, let's show the SQL that needs to be run
    
    print("\n" + "="*70)
    print("SQL TO RUN ON RENDER.COM POSTGRESQL DATABASE:")
    print("="*70)
    
    for i, contract in enumerate(contracts, 1):
        print(f"\nINSERT INTO federal_contracts (")
        print(f"    title, agency, department, description, location,")
        print(f"    contract_value, posted_date, deadline, contact_info, bid_link")
        print(f") VALUES (")
        print(f"    '{contract['title'].replace("'", "''")}',")
        print(f"    '{contract['agency'].replace("'", "''")}',")
        print(f"    '{contract['department'].replace("'", "''")}',")
        print(f"    '{contract['description'].replace("'", "''")}',")
        print(f"    '{contract['location'].replace("'", "''")}',")
        print(f"    '{contract['contract_value']}',")
        print(f"    '{contract['posted_date']}',")
        print(f"    '{contract['deadline']}',")
        print(f"    '{contract['contact_info']}',")
        print(f"    '{contract['bid_link']}'")
        print(f");")
        
        if i >= 5:
            print(f"\n... and {len(contracts) - 5} more contracts")
            break
    
    print("\n" + "="*70)

def main():
    """Main function"""
    print("🔄 Federal Contracts Production Upload Tool")
    print("="*70)
    
    # Get local contracts
    contracts = get_local_contracts()
    print(f"✅ Found {len(contracts)} contracts in local database")
    
    # Production URL
    production_url = "https://virginia-contracts-lead-generation.onrender.com"
    
    print(f"\n📍 Production URL: {production_url}")
    
    # Option 1: Use the existing scraper on production
    print("\n" + "="*70)
    print("RECOMMENDED SOLUTION:")
    print("="*70)
    print("\n1. SSH into your Render.com service (or use Render Shell)")
    print("2. Run the scraper directly on production:")
    print("   python scrape_datagov_direct.py")
    print("\nThis will fetch fresh contracts directly into the production database.")
    
    # Option 2: Show SQL for manual upload
    print("\n" + "="*70)
    print("ALTERNATIVE: Manual SQL Upload")
    print("="*70)
    choice = input("\nWould you like to see the SQL to manually upload contracts? (y/n): ")
    
    if choice.lower() == 'y':
        upload_to_production(contracts, production_url)
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
