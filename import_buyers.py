#!/usr/bin/env python3
"""
Import 600 buyers from buyers_list.txt directly into database
Uses Flask app context for proper database connection
"""

from app import app, db
from sqlalchemy import text
from quick_research_contacts import generate_contacts
import sys

def import_buyers():
    """Import all buyers from buyers_list.txt"""
    
    with app.app_context():
        try:
            # Ensure supply_contracts table exists
            print("🔧 Checking/creating supply_contracts table...")
            db.session.execute(text('''CREATE TABLE IF NOT EXISTS supply_contracts
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          title TEXT NOT NULL,
                          agency TEXT NOT NULL,
                          location TEXT NOT NULL,
                          product_category TEXT,
                          estimated_value TEXT,
                          bid_deadline TEXT,
                          description TEXT,
                          website_url TEXT,
                          is_small_business_set_aside INTEGER DEFAULT 0,
                          contact_name TEXT,
                          contact_email TEXT,
                          contact_phone TEXT,
                          is_quick_win INTEGER DEFAULT 0,
                          status TEXT DEFAULT 'open',
                          posted_date TEXT,
                          created_at TEXT DEFAULT CURRENT_TIMESTAMP)'''))
            db.session.commit()
            print("✅ Table ready\n")
            
            # Read buyers list
            with open('buyers_list.txt', 'r') as f:
                lines = f.readlines()
            
            print(f"📥 Processing {len(lines)} buyer entries...")
            print("=" * 80)
            
            inserted = 0
            errors = []
            
            for idx, line in enumerate(lines, 1):
                try:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        vendor_name = parts[0]
                        state = parts[-1]  # Last column is state code
                        
                        # Generate contact info
                        contact_info = generate_contacts(vendor_name, state)
                        
                        # Map to SQL parameters
                        from datetime import datetime, timedelta
                        deadline = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
                        
                        params = {
                            'title': f'{vendor_name} - Janitorial Supply Contract',
                            'agency': vendor_name,
                            'location': contact_info['address'],
                            'category': parts[2] if len(parts) > 2 else 'General Supplies',  # product_category
                            'value': contact_info['estimated_value'],
                            'deadline': deadline,
                            'description': contact_info['description'],
                            'url': contact_info['website'],
                            'contact_name': contact_info['contact_name'],
                            'contact_email': contact_info['email'],
                            'contact_phone': contact_info['phone'],
                            'is_quick_win': True,
                            'status': 'open',
                            'posted_date': datetime.now().strftime('%Y-%m-%d')
                        }
                        
                        # Insert into database
                        db.session.execute(text('''
                            INSERT INTO supply_contracts 
                            (title, agency, location, product_category, estimated_value, bid_deadline, 
                             description, website_url, contact_name, contact_email, contact_phone, 
                             is_quick_win, status, posted_date)
                            VALUES (:title, :agency, :location, :category, :value, :deadline,
                                    :description, :url, :contact_name, :contact_email, :contact_phone,
                                    :is_quick_win, :status, :posted_date)
                        '''), params)
                        
                        inserted += 1
                        
                        # Progress indicator
                        if inserted % 50 == 0:
                            db.session.commit()
                            print(f"✅ Inserted {inserted}/{len(lines)} records...")
                            
                except Exception as e:
                    errors.append(f"Row {idx} ({vendor_name[:50]}): {str(e)}")
                    continue
            
            # Final commit
            db.session.commit()
            
            print("=" * 80)
            print(f"\n🎉 SUCCESS: Inserted {inserted} supply contracts!")
            
            if errors:
                print(f"\n⚠️  {len(errors)} errors encountered:")
                for error in errors[:10]:  # Show first 10 errors
                    print(f"   - {error}")
                if len(errors) > 10:
                    print(f"   ... and {len(errors) - 10} more")
            
            # Verify count
            total = db.session.execute(text('SELECT COUNT(*) FROM supply_contracts')).scalar()
            print(f"\n📊 Total supply contracts in database: {total}")
            print(f"   - Expected: ~616 (16 pre-populated + 600 imported)")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("=" * 80)
    print("SUPPLY BUYERS IMPORT TOOL")
    print("=" * 80)
    print()
    
    success = import_buyers()
    sys.exit(0 if success else 1)
