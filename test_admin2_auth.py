from app import app, db
from sqlalchemy import text
from werkzeug.security import check_password_hash

with app.app_context():
    # Simulate what happens in signin route
    username = "admin2"
    password = "Admin2!Secure123"
    
    print(f"[TEST] Testing authentication for: {username}")
    
    # Step 1: Fetch credentials (same as _fetch_user_credentials)
    result = db.session.execute(
        text('''SELECT id, username, email, password_hash, contact_name, credits_balance,
                       is_admin, subscription_status, is_beta_tester, beta_expiry_date,
                       COALESCE(twofa_enabled, FALSE) as twofa_enabled
               FROM leads WHERE lower(username) = lower(:username) OR lower(email) = lower(:username)'''),
        {'username': username}
    ).fetchone()
    
    if result:
        print(f"[TEST] ✅ User found: id={result[0]}, username={result[1]}, email={result[2]}")
        print(f"[TEST]    is_admin={result[6]}, has_password_hash={bool(result[3])}")
        
        # Step 2: Check password
        if result[3]:
            password_valid = check_password_hash(result[3], password)
            print(f"[TEST] Password check result: {password_valid}")
            
            if password_valid:
                print(f"[TEST] ✅ AUTHENTICATION SUCCESSFUL!")
                print(f"[TEST]    User would be logged in with:")
                print(f"[TEST]    - user_id: {result[0]}")
                print(f"[TEST]    - username: {result[1]}")
                print(f"[TEST]    - email: {result[2]}")
                print(f"[TEST]    - is_admin: {result[6]}")
                print(f"[TEST]    - subscription_status: {result[7]}")
            else:
                print(f"[TEST] ❌ PASSWORD MISMATCH")
        else:
            print(f"[TEST] ❌ No password hash in database")
    else:
        print(f"[TEST] ❌ User not found")
