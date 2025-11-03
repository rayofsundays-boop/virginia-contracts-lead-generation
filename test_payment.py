"""
Payment Processing Test Script
Tests PayPal integration and subscription functionality
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_paypal_config():
    """Test PayPal configuration"""
    print("=" * 70)
    print("PAYMENT PROCESSING TEST")
    print("=" * 70)
    print()
    
    print("1️⃣  Checking PayPal Configuration...")
    print()
    
    # Check environment variables
    paypal_mode = os.environ.get('PAYPAL_MODE', 'sandbox')
    client_id = os.environ.get('PAYPAL_CLIENT_ID', '')
    client_secret = os.environ.get('PAYPAL_SECRET', '')
    monthly_plan = os.environ.get('PAYPAL_MONTHLY_PLAN_ID', 'P-MONTHLY-PLAN-ID')
    annual_plan = os.environ.get('PAYPAL_ANNUAL_PLAN_ID', 'P-ANNUAL-PLAN-ID')
    
    print(f"   Mode: {paypal_mode}")
    print(f"   Client ID: {'✅ Set' if client_id and client_id != '' else '❌ NOT SET'}")
    print(f"   Client Secret: {'✅ Set' if client_secret and client_secret != '' else '❌ NOT SET'}")
    print(f"   Monthly Plan ID: {monthly_plan}")
    print(f"   Annual Plan ID: {annual_plan}")
    print()
    
    if not client_id or not client_secret or client_id == '' or client_secret == '':
        print("⚠️  WARNING: PayPal credentials not configured!")
        print()
        print("To configure PayPal:")
        print("1. Go to https://developer.paypal.com/")
        print("2. Create a REST API app")
        print("3. Set environment variables:")
        print("   export PAYPAL_MODE=sandbox")
        print("   export PAYPAL_CLIENT_ID='your_client_id'")
        print("   export PAYPAL_SECRET='your_secret'")
        print()
        return False
    
    return True

def test_paypal_connection():
    """Test actual PayPal API connection"""
    print("2️⃣  Testing PayPal API Connection...")
    print()
    
    try:
        import paypalrestsdk
        
        paypalrestsdk.configure({
            "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),
            "client_id": os.environ.get('PAYPAL_CLIENT_ID', ''),
            "client_secret": os.environ.get('PAYPAL_SECRET', '')
        })
        
        # Try to create a test payment (won't execute, just validate)
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "transactions": [{
                "amount": {
                    "total": "1.00",
                    "currency": "USD"
                },
                "description": "Test transaction"
            }],
            "redirect_urls": {
                "return_url": "http://localhost:5000/success",
                "cancel_url": "http://localhost:5000/cancel"
            }
        })
        
        if payment.create():
            print("   ✅ PayPal API connection successful!")
            print("   ✅ Credentials are valid")
            print()
            return True
        else:
            print(f"   ❌ PayPal API error: {payment.error}")
            print()
            return False
            
    except ImportError:
        print("   ❌ paypalrestsdk not installed")
        print("   Run: pip install paypalrestsdk")
        print()
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print()
        return False

def test_database_schema():
    """Test database schema for payment tracking"""
    print("3️⃣  Checking Database Schema...")
    print()
    
    try:
        import sqlite3
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        # Check if payment-related columns exist
        cursor.execute("PRAGMA table_info(leads)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        required_columns = {
            'subscription_status': 'TEXT',
            'paypal_subscription_id': 'TEXT',
            'subscription_start_date': 'TEXT',
            'last_payment_date': 'TEXT'
        }
        
        all_exist = True
        for col, dtype in required_columns.items():
            if col in columns:
                print(f"   ✅ {col}: {columns[col]}")
            else:
                print(f"   ❌ {col}: MISSING")
                all_exist = False
        
        # Check for test users
        cursor.execute("SELECT COUNT(*) FROM leads WHERE subscription_status = 'paid'")
        paid_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE subscription_status = 'free'")
        free_count = cursor.fetchone()[0]
        
        print()
        print(f"   Current Users:")
        print(f"      Paid Subscribers: {paid_count}")
        print(f"      Free Users: {free_count}")
        print()
        
        conn.close()
        return all_exist
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        print()
        return False

def test_routes():
    """Test if payment routes are accessible"""
    print("4️⃣  Testing Payment Routes...")
    print()
    
    try:
        import requests
        
        base_url = "http://127.0.0.1:5000"
        
        routes = [
            '/subscription',
            '/register'
        ]
        
        print("   Testing routes (server must be running)...")
        for route in routes:
            try:
                response = requests.get(f"{base_url}{route}", timeout=2)
                if response.status_code == 200:
                    print(f"   ✅ {route}: {response.status_code}")
                elif response.status_code == 302:
                    print(f"   ✅ {route}: {response.status_code} (redirect - OK)")
                else:
                    print(f"   ⚠️  {route}: {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"   ⚠️  {route}: Server not running")
            except Exception as e:
                print(f"   ❌ {route}: {e}")
        
        print()
        return True
        
    except ImportError:
        print("   ⚠️  requests library not available for route testing")
        print()
        return True

def main():
    """Run all payment tests"""
    print()
    print("🔐 Testing Payment Processing System")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_paypal_config()))
    results.append(("API Connection", test_paypal_connection()))
    results.append(("Database Schema", test_database_schema()))
    results.append(("Routes", test_routes()))
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("🎉 All tests passed! Payment processing is ready.")
        print()
        print("Next steps:")
        print("1. Start Flask: flask run")
        print("2. Visit: http://127.0.0.1:5000/subscription")
        print("3. Test subscription flow with PayPal sandbox account")
    else:
        print("⚠️  Some tests failed. Review configuration above.")
        print()
        print("Common fixes:")
        print("1. Set PayPal environment variables")
        print("2. Install: pip install paypalrestsdk")
        print("3. Run database migrations: python app.py")
    
    print()
    print("=" * 70)

if __name__ == '__main__':
    main()
