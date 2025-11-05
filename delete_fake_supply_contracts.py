#!/usr/bin/env python3
"""
Delete all fake/synthetic supply contracts from database
Keeps only real data fetched from actual APIs
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def delete_fake_supply_contracts():
    """Delete all fake/synthetic supply contract data"""
    with app.app_context():
        try:
            print("🔍 Checking supply_contracts table...")
            
            # Count current records
            count_result = db.session.execute(text('SELECT COUNT(*) FROM supply_contracts')).fetchone()
            current_count = count_result[0] if count_result else 0
            
            if current_count == 0:
                print("ℹ️  No supply contracts found - table is already empty")
                return
            
            print(f"📊 Found {current_count} supply contracts")
            
            # Show some examples of what will be deleted
            examples = db.session.execute(text('''
                SELECT title, agency, website_url FROM supply_contracts LIMIT 5
            ''')).fetchall()
            
            print("\n📋 Examples of contracts to be deleted:")
            for ex in examples:
                print(f"  - {ex[0]}")
                print(f"    Agency: {ex[1]}")
                print(f"    URL: {ex[2] or 'None'}")
            
            # Ask for confirmation
            print(f"\n⚠️  About to DELETE all {current_count} supply contracts")
            print("   These appear to be synthetic/fake data with placeholder websites")
            confirm = input("   Type 'DELETE' to confirm: ")
            
            if confirm != 'DELETE':
                print("❌ Deletion cancelled")
                return
            
            # Create backup
            backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            print(f"\n💾 Creating backup: supply_contracts_backup_{backup_time}.sql")
            
            # Export to backup file
            backup_data = db.session.execute(text('SELECT * FROM supply_contracts')).fetchall()
            with open(f'supply_contracts_backup_{backup_time}.txt', 'w') as f:
                f.write(f"Backup created: {datetime.now()}\n")
                f.write(f"Total records: {current_count}\n\n")
                for row in backup_data:
                    f.write(f"{dict(row)}\n")
            
            print(f"✅ Backup saved to: supply_contracts_backup_{backup_time}.txt")
            
            # Delete all records
            print("\n🗑️  Deleting all supply contracts...")
            db.session.execute(text('DELETE FROM supply_contracts'))
            db.session.commit()
            
            # Verify deletion
            verify_count = db.session.execute(text('SELECT COUNT(*) FROM supply_contracts')).fetchone()[0]
            
            if verify_count == 0:
                print(f"✅ SUCCESS: Deleted all {current_count} fake supply contracts")
                print("\n📝 Next steps:")
                print("   1. Supply contracts page will now show 0 quick wins (correct)")
                print("   2. You can fetch REAL data from SAM.gov API if needed")
                print("   3. Only add verified, real opportunities going forward")
            else:
                print(f"⚠️  WARNING: {verify_count} records still remain")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    delete_fake_supply_contracts()
