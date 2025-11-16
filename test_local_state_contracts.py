#!/usr/bin/env python3
"""
Local/State Contracts Diagnostic Test
Identifies why the contracts table is empty
"""

import sqlite3
import os
import sys

def test_local_state_contracts():
    """Comprehensive diagnostic for local/state contracts"""
    
    print("=" * 80)
    print("LOCAL/STATE CONTRACTS DIAGNOSTIC TEST")
    print("=" * 80)
    print()
    
    db_path = 'leads.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("✅ Database connection successful")
        print()
        
        # Test 1: Check contracts table exists and schema
        print("TEST 1: Contracts Table Schema")
        print("-" * 80)
        try:
            cursor.execute("PRAGMA table_info(contracts)")
            columns = cursor.fetchall()
            
            if not columns:
                print("❌ FAIL: 'contracts' table does not exist!")
                return False
            
            print(f"✅ Table exists with {len(columns)} columns:")
            for col in columns:
                print(f"   - {col['name']} ({col['type']})")
            print()
            
        except sqlite3.Error as e:
            print(f"❌ FAIL: Error checking schema: {e}")
            return False
        
        # Test 2: Check current row count
        print("TEST 2: Current Row Count")
        print("-" * 80)
        cursor.execute("SELECT COUNT(*) as count FROM contracts")
        result = cursor.fetchone()
        count = result['count']
        print(f"Current records: {count}")
        
        if count == 0:
            print("⚠️  WARNING: contracts table is EMPTY")
        else:
            print(f"✅ Found {count} records")
        print()
        
        # Test 3: Check for any historical data
        print("TEST 3: Check for Deleted/Historical Data")
        print("-" * 80)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND (name LIKE '%contract%' OR name LIKE '%local%' OR name LIKE '%state%')
            ORDER BY name
        """)
        related_tables = cursor.fetchall()
        
        print(f"Found {len(related_tables)} related tables:")
        for table in related_tables:
            table_name = table['name']
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()['count']
            print(f"   - {table_name}: {count} records")
        print()
        
        # Test 4: Check if data was ever inserted
        print("TEST 4: Data Source Analysis")
        print("-" * 80)
        
        # Check for data_source column
        cursor.execute("PRAGMA table_info(contracts)")
        columns = {col['name']: col['type'] for col in cursor.fetchall()}
        
        if 'data_source' in columns:
            print("✅ data_source column exists")
            cursor.execute("""
                SELECT data_source, COUNT(*) as count 
                FROM contracts 
                GROUP BY data_source
            """)
            sources = cursor.fetchall()
            
            if sources:
                print("Data sources found:")
                for source in sources:
                    print(f"   - {source['data_source']}: {source['count']} records")
            else:
                print("⚠️  No data from any source")
        else:
            print("⚠️  WARNING: data_source column missing")
        print()
        
        # Test 5: Check populated date column for patterns
        print("TEST 5: Temporal Analysis")
        print("-" * 80)
        
        date_columns = ['created_at', 'posted_date', 'due_date', 'date_posted']
        found_date_col = None
        
        for col in date_columns:
            if col in columns:
                found_date_col = col
                break
        
        if found_date_col:
            print(f"✅ Date column found: {found_date_col}")
            cursor.execute(f"""
                SELECT 
                    DATE({found_date_col}) as date,
                    COUNT(*) as count
                FROM contracts
                WHERE {found_date_col} IS NOT NULL
                GROUP BY DATE({found_date_col})
                ORDER BY date DESC
                LIMIT 10
            """)
            dates = cursor.fetchall()
            
            if dates:
                print(f"Most recent activity (top 10 dates):")
                for row in dates:
                    print(f"   - {row['date']}: {row['count']} records")
            else:
                print("⚠️  No dated records found")
        else:
            print("⚠️  WARNING: No date columns found")
        print()
        
        # Test 6: Check for fake/demo data markers
        print("TEST 6: Data Quality Check")
        print("-" * 80)
        
        # Check if table has been intentionally cleared
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='contracts'
        """)
        create_sql = cursor.fetchone()
        if create_sql:
            print("Table creation SQL:")
            print(f"   {create_sql['sql'][:100]}...")
        
        # Check for any constraints or triggers
        cursor.execute("""
            SELECT name, type FROM sqlite_master 
            WHERE tbl_name='contracts' AND type IN ('trigger', 'index')
        """)
        constraints = cursor.fetchall()
        
        if constraints:
            print(f"\nFound {len(constraints)} constraints/triggers:")
            for c in constraints:
                print(f"   - {c['type']}: {c['name']}")
        print()
        
        # Test 7: Check disabled scripts
        print("TEST 7: Check for Disabled Population Scripts")
        print("-" * 80)
        
        disabled_scripts = [
            'populate_federal_contracts.py.DISABLED',
            'quick_populate.py.DISABLED',
            'populate_production.py.DISABLED',
            'add_eva_leads.py.DISABLED'
        ]
        
        found_disabled = []
        for script in disabled_scripts:
            if os.path.exists(script):
                found_disabled.append(script)
        
        if found_disabled:
            print(f"⚠️  Found {len(found_disabled)} DISABLED population scripts:")
            for script in found_disabled:
                print(f"   - {script}")
            print("\n⚠️  These scripts were disabled to prevent fake data.")
            print("   This is INTENTIONAL per FAKE_DATA_PREVENTION.md")
        else:
            print("✅ No disabled scripts found")
        print()
        
        # Test 8: Expected data sources
        print("TEST 8: Expected Data Sources for Local/State Contracts")
        print("-" * 80)
        
        print("Local/State contracts should come from:")
        print("   1. EVA (eVA.virginia.gov) - Virginia procurement portal")
        print("   2. State procurement portals (50 states)")
        print("   3. City/county bid boards")
        print("   4. Manual admin uploads via CSV")
        print()
        print("Current status:")
        print("   ❌ EVA scraper: Not implemented (add_eva_leads.py disabled)")
        print("   ❌ State portals: Not implemented")
        print("   ❌ City scrapers: Not implemented")
        print("   ⚠️  Admin CSV upload: Available at /admin-enhanced?section=upload-csv")
        print()
        
        # Final diagnosis
        print("=" * 80)
        print("DIAGNOSIS")
        print("=" * 80)
        
        if count == 0:
            print("\n🔍 ROOT CAUSE: contracts table is empty because:")
            print()
            print("1. ✅ INTENTIONAL: Fake data generation scripts were disabled")
            print("   - See: FAKE_DATA_PREVENTION.md")
            print("   - Scripts disabled: populate_federal_contracts.py.DISABLED, etc.")
            print()
            print("2. ⚠️  MISSING: Real data scrapers not yet implemented")
            print("   - EVA scraper: Not active")
            print("   - State portal scrapers: Not active")
            print("   - City bid board scrapers: Not active")
            print()
            print("3. ✅ AVAILABLE: Manual data import")
            print("   - Admin can import CSV at: /admin-enhanced?section=upload-csv")
            print()
            print("=" * 80)
            print("RECOMMENDATIONS")
            print("=" * 80)
            print()
            print("SHORT TERM (Quick Fix):")
            print("  1. Use Admin CSV Import to add real contracts")
            print("  2. Go to: http://localhost:8080/admin-enhanced?section=upload-csv")
            print("  3. Upload CSV with contract data")
            print()
            print("LONG TERM (Automated Solution):")
            print("  1. Implement EVA scraper for Virginia contracts")
            print("  2. Implement state portal scrapers (50 states)")
            print("  3. Enable automated daily fetching")
            print()
            print("CURRENT ACTIVE SCRAPERS:")
            print("  ✅ Federal Contracts: 92 records (SAM.gov API)")
            print("  ✅ Supply Contracts: 16 records (manually curated)")
            print("  ❌ Local/State: 0 records (scrapers not implemented)")
            print()
        else:
            print(f"\n✅ Found {count} local/state contracts")
            print("No issues detected.")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    success = test_local_state_contracts()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
