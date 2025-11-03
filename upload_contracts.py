"""
Manual Contract Upload Tool
Upload real federal contracts to the database
"""
import sys
from datetime import datetime
from app import app, db
from sqlalchemy import text

def upload_contract():
    """Interactive contract upload"""
    print("=" * 70)
    print("MANUAL CONTRACT UPLOAD")
    print("=" * 70)
    print()
    
    contracts = []
    
    while True:
        print("\n📝 Enter contract details (or 'done' to finish):\n")
        
        title = input("Title: ").strip()
        if title.lower() == 'done':
            break
        
        if not title:
            print("❌ Title is required!")
            continue
        
        agency = input("Agency: ").strip() or "Unknown Agency"
        department = input("Department (optional): ").strip()
        location = input("Location (e.g., Norfolk, VA): ").strip() or "Virginia"
        value = input("Value (e.g., $500,000): ").strip()
        deadline = input("Deadline (YYYY-MM-DD): ").strip()
        naics_code = input("NAICS Code (e.g., 561720): ").strip()
        set_aside = input("Set-Aside Type (optional): ").strip()
        sam_gov_url = input("SAM.gov URL (optional): ").strip()
        
        # Description
        print("\nDescription (press Enter twice when done):")
        description_lines = []
        while True:
            line = input()
            if line:
                description_lines.append(line)
            else:
                if description_lines:
                    break
        description = "\n".join(description_lines)
        
        # Generate notice_id
        notice_id = f"MANUAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        posted_date = datetime.now().strftime('%Y-%m-%d')
        
        contract = {
            'title': title,
            'agency': agency,
            'department': department,
            'location': location,
            'value': value,
            'deadline': deadline if deadline else None,
            'description': description or title,
            'naics_code': naics_code,
            'sam_gov_url': sam_gov_url,
            'notice_id': notice_id,
            'set_aside': set_aside,
            'posted_date': posted_date
        }
        
        contracts.append(contract)
        print(f"\n✅ Contract '{title}' added!")
        
        another = input("\nAdd another contract? (y/n): ").strip().lower()
        if another != 'y':
            break
    
    if not contracts:
        print("\n❌ No contracts to upload.")
        return
    
    # Upload to database
    print(f"\n💾 Uploading {len(contracts)} contract(s) to database...")
    
    with app.app_context():
        # Remove demo data first
        deleted = db.session.execute(text('''
            DELETE FROM federal_contracts WHERE description LIKE '%DEMO DATA%'
        ''')).rowcount
        
        if deleted > 0:
            print(f"   Removed {deleted} demo contracts")
        
        # Insert new contracts
        inserted = 0
        for contract in contracts:
            try:
                db.session.execute(text('''
                    INSERT INTO federal_contracts 
                    (title, agency, department, location, value, deadline, description, 
                     naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                    VALUES (:title, :agency, :department, :location, :value, :deadline, 
                            :description, :naics_code, :sam_gov_url, :notice_id, 
                            :set_aside, :posted_date)
                '''), contract)
                inserted += 1
                print(f"   ✅ {contract['title']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        db.session.commit()
        print(f"\n✅ Successfully uploaded {inserted} contract(s)!")

def upload_from_csv():
    """Upload contracts from CSV file"""
    import csv
    
    print("=" * 70)
    print("CSV CONTRACT UPLOAD")
    print("=" * 70)
    print()
    
    csv_file = input("Enter CSV file path: ").strip()
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            contracts = []
            
            for row in reader:
                notice_id = row.get('notice_id') or f"CSV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                contracts.append({
                    'title': row.get('title', 'Untitled'),
                    'agency': row.get('agency', 'Unknown'),
                    'department': row.get('department', ''),
                    'location': row.get('location', 'Virginia'),
                    'value': row.get('value', ''),
                    'deadline': row.get('deadline') or None,
                    'description': row.get('description', ''),
                    'naics_code': row.get('naics_code', ''),
                    'sam_gov_url': row.get('sam_gov_url', ''),
                    'notice_id': notice_id,
                    'set_aside': row.get('set_aside', ''),
                    'posted_date': row.get('posted_date', datetime.now().strftime('%Y-%m-%d'))
                })
        
        print(f"\n📊 Found {len(contracts)} contracts in CSV")
        
        proceed = input("Upload these contracts? (y/n): ").strip().lower()
        if proceed != 'y':
            print("❌ Upload cancelled")
            return
        
        with app.app_context():
            # Remove demo data
            deleted = db.session.execute(text('''
                DELETE FROM federal_contracts WHERE description LIKE '%DEMO DATA%'
            ''')).rowcount
            
            if deleted > 0:
                print(f"   Removed {deleted} demo contracts")
            
            # Insert contracts
            inserted = 0
            for contract in contracts:
                try:
                    db.session.execute(text('''
                        INSERT INTO federal_contracts 
                        (title, agency, department, location, value, deadline, description, 
                         naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                        VALUES (:title, :agency, :department, :location, :value, :deadline, 
                                :description, :naics_code, :sam_gov_url, :notice_id, 
                                :set_aside, :posted_date)
                    '''), contract)
                    inserted += 1
                except Exception as e:
                    print(f"   ❌ Error with {contract['title']}: {e}")
            
            db.session.commit()
            print(f"\n✅ Successfully uploaded {inserted} contract(s)!")
            
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("\n🗂️  CONTRACT UPLOAD TOOL")
    print("\nChoose upload method:")
    print("1. Interactive (enter contracts manually)")
    print("2. CSV file")
    print("3. Exit")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == '1':
        upload_contract()
    elif choice == '2':
        upload_from_csv()
    else:
        print("Goodbye!")
        return
    
    print("\n" + "=" * 70)
    print("✅ Upload complete! Refresh your federal contracts page.")
    print("=" * 70)

if __name__ == '__main__':
    main()
