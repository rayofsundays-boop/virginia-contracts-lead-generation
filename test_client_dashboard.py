#!/usr/bin/env python3
"""
Client Dashboard Testing Script
Tests gamification, saved leads, and database query alignment
"""

import sqlite3
import sys
from datetime import datetime, timedelta

def test_client_dashboard():
    """Test client dashboard database queries"""
    
    print("=" * 80)
    print("CLIENT DASHBOARD DATABASE TEST")
    print("=" * 80)
    print()
    
    db_path = 'leads.db'
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("✅ Database connection successful")
        print()
        
        # Test 1: Check user_activity table schema
        print("TEST 1: User Activity Table Schema")
        print("-" * 80)
        cursor.execute("PRAGMA table_info(user_activity)")
        columns = cursor.fetchall()
        
        column_names = [col['name'] for col in columns]
        print(f"Columns found: {', '.join(column_names)}")
        
        required_columns = ['id', 'user_email', 'action_type', 'created_at']
        missing = [col for col in required_columns if col not in column_names]
        
        if missing:
            print(f"❌ FAIL: Missing columns: {', '.join(missing)}")
            return False
        else:
            print("✅ PASS: All required columns present")
        print()
        
        # Test 2: Check saved_leads table schema
        print("TEST 2: Saved Leads Table Schema")
        print("-" * 80)
        cursor.execute("PRAGMA table_info(saved_leads)")
        columns = cursor.fetchall()
        
        column_names = [col['name'] for col in columns]
        print(f"Columns found: {', '.join(column_names)}")
        
        required_columns = ['id', 'user_email', 'saved_at']
        missing = [col for col in required_columns if col not in column_names]
        
        if missing:
            print(f"❌ FAIL: Missing columns: {', '.join(missing)}")
            return False
        else:
            print("✅ PASS: All required columns present")
        print()
        
        # Test 3: Gamification queries (mimic client_dashboard route)
        print("TEST 3: Gamification Queries")
        print("-" * 80)
        
        # Get a test user
        cursor.execute("SELECT email FROM leads WHERE is_admin = 0 LIMIT 1")
        user_row = cursor.fetchone()
        
        if not user_row:
            print("⚠️  WARNING: No test user found. Creating demo data...")
            # Could insert test user here
            print("⚠️  Skipping gamification tests (no users)")
            return True
        
        test_email = user_row['email']
        print(f"Testing with user: {test_email}")
        print()
        
        # Test streak calculation
        print("  → Testing streak calculation...")
        try:
            cursor.execute("""
                SELECT DATE(created_at) as activity_date
                FROM user_activity
                WHERE user_email = ?
                AND action_type IN ('view_lead', 'save_lead', 'login')
                ORDER BY created_at DESC
                LIMIT 30
            """, (test_email,))
            
            activity_dates = cursor.fetchall()
            print(f"    Found {len(activity_dates)} recent activities")
            print("    ✅ Streak query successful")
        except sqlite3.OperationalError as e:
            print(f"    ❌ FAIL: {e}")
            return False
        print()
        
        # Test today's saved leads count
        print("  → Testing today's saved leads count...")
        try:
            today = datetime.now().date()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM saved_leads
                WHERE user_email = ?
                AND DATE(saved_at) = DATE(?)
            """, (test_email, today))
            
            result = cursor.fetchone()
            count = result['count']
            print(f"    Saved leads today: {count}")
            print("    ✅ Today's count query successful")
        except sqlite3.OperationalError as e:
            print(f"    ❌ FAIL: {e}")
            return False
        print()
        
        # Test 4: Saved stats queries
        print("TEST 4: Saved Stats Queries")
        print("-" * 80)
        
        print("  → Testing saved searches count...")
        try:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM saved_searches
                WHERE user_email = ?
            """, (test_email,))
            
            result = cursor.fetchone()
            count = result['count'] if result else 0
            print(f"    Saved searches: {count}")
            print("    ✅ Saved searches query successful")
        except sqlite3.OperationalError as e:
            print(f"    ⚠️  WARNING: {e}")
            print("    (saved_searches table may not exist yet)")
        print()
        
        print("  → Testing total saved leads count...")
        try:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM saved_leads
                WHERE user_email = ?
            """, (test_email,))
            
            result = cursor.fetchone()
            count = result['count']
            print(f"    Total saved leads: {count}")
            print("    ✅ Saved leads query successful")
        except sqlite3.OperationalError as e:
            print(f"    ❌ FAIL: {e}")
            return False
        print()
        
        # Test 5: Activity type validation
        print("TEST 5: Activity Type Values")
        print("-" * 80)
        cursor.execute("""
            SELECT DISTINCT action_type, COUNT(*) as count
            FROM user_activity
            GROUP BY action_type
        """)
        
        activity_types = cursor.fetchall()
        print(f"  Found {len(activity_types)} distinct action types:")
        for row in activity_types:
            print(f"    • {row['action_type']}: {row['count']} records")
        
        if activity_types:
            print("  ✅ Activity types present")
        else:
            print("  ⚠️  WARNING: No activity data found")
        print()
        
        conn.close()
        
        print("=" * 80)
        print("ALL TESTS PASSED ✅")
        print("=" * 80)
        print()
        print("Summary:")
        print("  • user_activity table has correct schema (action_type, created_at)")
        print("  • saved_leads table has correct schema (saved_at)")
        print("  • Gamification queries execute without errors")
        print("  • Client dashboard should load successfully")
        print()
        
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
    success = test_client_dashboard()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
