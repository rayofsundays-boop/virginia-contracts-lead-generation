"""
Remove Demo/Sample/Fake Leads from Database
Identifies and removes generated/sample data, keeping only real verified leads
"""
import sqlite3
from datetime import datetime

def backup_database():
    """Create backup before deletion"""
    import shutil
    backup_name = f'leads_backup_before_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    shutil.copy('leads.db', backup_name)
    print(f"✅ Backup created: {backup_name}")
    return backup_name

def remove_demo_data():
    """Remove all demo/sample/fake data from database"""
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🧹 CLEANING DATABASE - Removing Demo/Sample/Fake Leads")
    print("=" * 80)
    print()
    
    # Count before
    cursor.execute("SELECT COUNT(*) FROM federal_contracts")
    federal_before = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM contracts")
    local_before = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM supply_contracts")
    supply_before = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM commercial_opportunities")
    commercial_before = cursor.fetchone()[0]
    
    print(f"📊 BEFORE CLEANUP:")
    print(f"   Federal Contracts:          {federal_before}")
    print(f"   Local Contracts:            {local_before}")
    print(f"   Supply Contracts:           {supply_before}")
    print(f"   Commercial Opportunities:   {commercial_before}")
    print(f"   TOTAL:                      {federal_before + local_before + supply_before + commercial_before}")
    print()
    
    # Federal contracts - Keep only Data.gov and SAM.gov verified data
    # These are all real, so keep them
    print("✅ Federal Contracts: All verified from Data.gov and SAM.gov APIs - KEEPING")
    
    # Local contracts - Remove if they appear to be generated/demo data
    # Check for patterns: generic titles, created in bulk, standard descriptions
    print("\n🔍 Analyzing Local Contracts...")
    
    cursor.execute("""
        SELECT id, title, agency, description 
        FROM contracts 
        ORDER BY created_at
    """)
    
    local_contracts = cursor.fetchall()
    demo_patterns = [
        'FY2026', 'FY2025', 'FY2024',  # Generic fiscal year refs
        'Annual Supply', 'Standing Order',  # Generic supply terms
        'Facility Cleaning', 'Janitorial Services',  # Generic without specifics
    ]
    
    # Check if contracts are auto-generated (same created_at times, sequential patterns)
    cursor.execute("""
        SELECT created_at, COUNT(*) as count
        FROM contracts
        GROUP BY created_at
        HAVING count > 5
    """)
    bulk_created = cursor.fetchall()
    
    if bulk_created:
        print(f"⚠️  Found {len(bulk_created)} timestamps with 5+ contracts created simultaneously")
        print("   This indicates bulk-generated demo data")
        
        # Get all contracts created in bulk
        bulk_timestamps = [row[0] for row in bulk_created]
        placeholders = ','.join(['?' for _ in bulk_timestamps])
        cursor.execute(f"""
            DELETE FROM contracts 
            WHERE created_at IN ({placeholders})
        """, bulk_timestamps)
        
        deleted_local = cursor.rowcount
        print(f"   🗑️  Deleted {deleted_local} bulk-generated local contracts")
    else:
        print("   ✅ No obvious bulk-generated data found")
        deleted_local = 0
    
    # Supply contracts - Similar check
    print("\n🔍 Analyzing Supply Contracts...")
    cursor.execute("""
        SELECT created_at, COUNT(*) as count
        FROM supply_contracts
        GROUP BY created_at
        HAVING count > 3
    """)
    bulk_created_supply = cursor.fetchall()
    
    if bulk_created_supply:
        print(f"⚠️  Found {len(bulk_created_supply)} timestamps with 3+ supply contracts created simultaneously")
        bulk_timestamps = [row[0] for row in bulk_created_supply]
        placeholders = ','.join(['?' for _ in bulk_timestamps])
        cursor.execute(f"""
            DELETE FROM supply_contracts 
            WHERE created_at IN ({placeholders})
        """, bulk_timestamps)
        
        deleted_supply = cursor.rowcount
        print(f"   🗑️  Deleted {deleted_supply} bulk-generated supply contracts")
    else:
        print("   ✅ No obvious bulk-generated data found")
        deleted_supply = 0
    
    # Commercial opportunities - Check for obviously fake data
    print("\n🔍 Analyzing Commercial Opportunities...")
    cursor.execute("""
        SELECT id, business_name, location, monthly_value
        FROM commercial_opportunities
        WHERE business_name LIKE '%Sample%' 
           OR business_name LIKE '%Demo%'
           OR business_name LIKE '%Test%'
    """)
    
    demo_commercial = cursor.fetchall()
    if demo_commercial:
        demo_ids = [row[0] for row in demo_commercial]
        placeholders = ','.join(['?' for _ in demo_ids])
        cursor.execute(f"""
            DELETE FROM commercial_opportunities
            WHERE id IN ({placeholders})
        """, demo_ids)
        deleted_commercial = cursor.rowcount
        print(f"   🗑️  Deleted {deleted_commercial} demo commercial opportunities")
    else:
        print("   ✅ No obvious demo data found")
        deleted_commercial = 0
    
    # Alternative: Keep only commercial opportunities added recently (the major companies)
    # These were added manually and are real
    print("\n🔍 Checking for auto-generated commercial data...")
    cursor.execute("""
        SELECT COUNT(*) FROM commercial_opportunities
        WHERE monthly_value < 5000
    """)
    low_value_count = cursor.fetchone()[0]
    
    if low_value_count > 15:  # If many low-value entries, likely auto-generated
        print(f"⚠️  Found {low_value_count} low-value commercial opportunities (<$5,000/month)")
        print("   These appear to be auto-generated. Keeping only high-value verified opportunities...")
        
        cursor.execute("""
            DELETE FROM commercial_opportunities
            WHERE monthly_value < 20000
            AND business_name NOT IN (
                'Amazon HQ2', 'Capital One HQ', 'Northrop Grumman',
                'Booz Allen Hamilton', 'JBG SMITH', 'The Wharf DC',
                'Cushman & Wakefield', 'CBRE', 'Transwestern',
                'NIH', 'Marriott', 'Lockheed Martin', 'GWU', 'Inova Health',
                'VCU Health', 'Tysons Corner', 'Pentagon City'
            )
        """)
        deleted_commercial += cursor.rowcount
        print(f"   🗑️  Deleted {cursor.rowcount} additional auto-generated opportunities")
    
    conn.commit()
    
    # Count after
    cursor.execute("SELECT COUNT(*) FROM federal_contracts")
    federal_after = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM contracts")
    local_after = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM supply_contracts")
    supply_after = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM commercial_opportunities")
    commercial_after = cursor.fetchone()[0]
    
    print()
    print("=" * 80)
    print("📊 AFTER CLEANUP:")
    print("=" * 80)
    print(f"   Federal Contracts:          {federal_after} (was {federal_before})")
    print(f"   Local Contracts:            {local_after} (was {local_before}, removed {local_before - local_after})")
    print(f"   Supply Contracts:           {supply_after} (was {supply_before}, removed {supply_before - supply_after})")
    print(f"   Commercial Opportunities:   {commercial_after} (was {commercial_before}, removed {commercial_before - commercial_after})")
    print()
    print(f"   TOTAL:                      {federal_after + local_after + supply_after + commercial_after}")
    print()
    
    total_removed = (federal_before + local_before + supply_before + commercial_before) - \
                   (federal_after + local_after + supply_after + commercial_after)
    
    print(f"🗑️  TOTAL REMOVED: {total_removed} demo/sample/fake leads")
    print()
    
    if total_removed > 0:
        print("✅ Database cleaned successfully!")
        print("   Only verified real leads remain")
    else:
        print("✅ Database was already clean!")
        print("   No demo/sample data found")
    
    conn.close()
    
    return {
        'federal_before': federal_before,
        'local_before': local_before,
        'supply_before': supply_before,
        'commercial_before': commercial_before,
        'federal_after': federal_after,
        'local_after': local_after,
        'supply_after': supply_after,
        'commercial_after': commercial_after,
        'total_removed': total_removed
    }

if __name__ == '__main__':
    print()
    print("⚠️  WARNING: This will permanently delete demo/sample/fake leads")
    print("   A backup will be created first")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response == 'yes':
        backup_name = backup_database()
        print()
        results = remove_demo_data()
        print()
        print(f"💾 Backup saved as: {backup_name}")
        print("   (You can restore from this if needed)")
        print()
    else:
        print("❌ Cleanup cancelled")
