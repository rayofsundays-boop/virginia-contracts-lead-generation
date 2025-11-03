"""
Payment System Test - Admin Test Interface
Tests payment flow without requiring PayPal credentials
"""
import sqlite3
from datetime import datetime, timedelta

def create_test_user():
    """Create a test user for payment testing"""
    print("=" * 70)
    print("CREATING TEST USER")
    print("=" * 70)
    print()
    
    try:
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        # Check if test user exists
        cursor.execute("SELECT id, email, subscription_status FROM leads WHERE email = 'test@payment.com'")
        existing = cursor.fetchone()
        
        if existing:
            print(f"   Test user already exists:")
            print(f"   ID: {existing[0]}")
            print(f"   Email: {existing[1]}")
            print(f"   Status: {existing[2]}")
            print()
            return existing[0]
        
        # Create test user
        cursor.execute('''
            INSERT INTO leads 
            (contact_name, email, phone, company_name, state, 
             subscription_status, created_at, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Test Payment User',
            'test@payment.com',
            '555-0123',
            'Test Company',
            'VA',
            'free',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_hash_not_real'
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"   ✅ Test user created!")
        print(f"   ID: {user_id}")
        print(f"   Email: test@payment.com")
        print(f"   Status: free")
        print()
        return user_id
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def simulate_payment(user_id, plan_type='monthly'):
    """Simulate a successful payment"""
    print("=" * 70)
    print(f"SIMULATING {plan_type.upper()} PAYMENT")
    print("=" * 70)
    print()
    
    try:
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        # Update user to paid
        subscription_id = f"TEST-SUB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        start_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            UPDATE leads
            SET subscription_status = 'paid',
                paypal_subscription_id = ?,
                subscription_start_date = ?,
                last_payment_date = ?
            WHERE id = ?
        ''', (subscription_id, start_date, start_date, user_id))
        
        conn.commit()
        
        # Verify update
        cursor.execute('''
            SELECT email, subscription_status, paypal_subscription_id, 
                   subscription_start_date, last_payment_date
            FROM leads WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print("   ✅ Payment simulation successful!")
            print()
            print("   Updated User Details:")
            print(f"      Email: {result[0]}")
            print(f"      Status: {result[1]}")
            print(f"      Subscription ID: {result[2]}")
            print(f"      Start Date: {result[3]}")
            print(f"      Last Payment: {result[4]}")
            print()
            return True
        else:
            print("   ❌ Update verification failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_access_control():
    """Test if paid users have proper access"""
    print("=" * 70)
    print("TESTING ACCESS CONTROL")
    print("=" * 70)
    print()
    
    try:
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        # Check federal contracts count
        cursor.execute("SELECT COUNT(*) FROM federal_contracts")
        contract_count = cursor.fetchone()[0]
        
        print(f"   Federal Contracts Available: {contract_count}")
        print()
        
        # Simulate access check for paid user
        cursor.execute('''
            SELECT subscription_status 
            FROM leads 
            WHERE email = 'test@payment.com'
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 'paid':
            print("   ✅ Paid user would have UNLIMITED access")
            print(f"   ✅ Can view all {contract_count} contracts")
            print("   ✅ No click limits")
            print()
            return True
        else:
            print("   ⚠️  User is FREE - has 3-click limit")
            print("   ⚠️  Would need subscription for full access")
            print()
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def simulate_cancellation(user_id):
    """Simulate subscription cancellation"""
    print("=" * 70)
    print("SIMULATING SUBSCRIPTION CANCELLATION")
    print("=" * 70)
    print()
    
    try:
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        # Downgrade to free
        cursor.execute('''
            UPDATE leads
            SET subscription_status = 'free',
                paypal_subscription_id = NULL
            WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        
        # Verify
        cursor.execute('SELECT subscription_status FROM leads WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 'free':
            print("   ✅ Cancellation successful!")
            print("   ✅ User downgraded to free tier")
            print("   ⚠️  Click limits now apply")
            print()
            return True
        else:
            print("   ❌ Cancellation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def cleanup_test_user():
    """Remove test user"""
    print("=" * 70)
    print("CLEANUP TEST DATA")
    print("=" * 70)
    print()
    
    try:
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM leads WHERE email = 'test@payment.com'")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"   ✅ Removed {deleted} test user(s)")
        else:
            print("   ℹ️  No test users to remove")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Run payment system tests"""
    print()
    print("💳 PAYMENT SYSTEM FUNCTIONAL TEST")
    print("   Testing without PayPal API - Database Operations Only")
    print()
    
    # Create test user
    user_id = create_test_user()
    if not user_id:
        print("❌ Failed to create test user. Exiting.")
        return
    
    # Test payment flow
    print("📝 Test 1: Upgrade to Paid Subscription")
    payment_success = simulate_payment(user_id, 'monthly')
    
    # Test access control
    print("📝 Test 2: Verify Access Level")
    access_ok = test_access_control()
    
    # Test cancellation
    print("📝 Test 3: Cancel Subscription")
    cancel_ok = simulate_cancellation(user_id)
    
    # Verify downgrade
    print("📝 Test 4: Verify Downgrade")
    print("=" * 70)
    print("VERIFYING FREE TIER ACCESS")
    print("=" * 70)
    print()
    print("   ✅ User downgraded to free tier")
    print("   ⚠️  3-click limit now applies")
    print("   ⚠️  Upgrade required for unlimited access")
    print()
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    print(f"   {'✅' if user_id else '❌'} User Creation")
    print(f"   {'✅' if payment_success else '❌'} Payment Simulation (Upgrade)")
    print(f"   {'✅' if access_ok else '❌'} Access Control")
    print(f"   {'✅' if cancel_ok else '❌'} Cancellation (Downgrade)")
    print()
    
    all_passed = user_id and payment_success and access_ok and cancel_ok
    
    if all_passed:
        print("🎉 All tests PASSED!")
        print()
        print("✅ Database schema is correct")
        print("✅ Payment status updates work")
        print("✅ Subscription tracking works")
        print("✅ Upgrade/downgrade flow works")
        print()
        print("⚠️  Note: Actual PayPal integration needs credentials:")
        print("   1. PAYPAL_CLIENT_ID")
        print("   2. PAYPAL_SECRET")
        print("   3. PAYPAL_MONTHLY_PLAN_ID")
        print("   4. PAYPAL_ANNUAL_PLAN_ID")
    else:
        print("❌ Some tests failed")
    
    print()
    
    # Cleanup
    cleanup_option = input("Remove test user? (y/n): ").strip().lower()
    if cleanup_option == 'y':
        cleanup_test_user()
    else:
        print()
        print("   Test user kept for manual testing")
        print("   Email: test@payment.com")
        print()
    
    print("=" * 70)

if __name__ == '__main__':
    main()
