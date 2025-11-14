#!/usr/bin/env python3
"""
Test script to simulate admin2 login flow locally
"""
import os
os.environ['ADMIN2_AUTO_PROVISION'] = '1'
os.environ['ADMIN2_SEED_EMAIL'] = 'admin2@vacontracts.com'
os.environ['ADMIN2_SEED_USERNAME'] = 'admin2'
os.environ['ADMIN2_SEED_PASSWORD'] = 'admin2'

from app import app, _fetch_user_credentials, _is_admin2_identifier, ensure_admin2_account, ADMIN2_SEED_PASSWORD
from werkzeug.security import check_password_hash

print("=" * 60)
print("ADMIN2 LOGIN SIMULATION TEST")
print("=" * 60)

with app.app_context():
    username = 'admin2'
    password = 'admin2'
    
    print(f"\n1. Testing identifier recognition...")
    is_admin2 = _is_admin2_identifier(username)
    print(f"   ✓ '{username}' recognized as admin2: {is_admin2}")
    
    print(f"\n2. Fetching credentials for '{username}'...")
    result = _fetch_user_credentials(username)
    
    if not result:
        print(f"   ⚠ Account not found, triggering auto-provision...")
        ensure_admin2_account()
        result = _fetch_user_credentials(username)
    
    if result:
        print(f"   ✓ Account found:")
        print(f"     - ID: {result[0]}")
        print(f"     - Username: {result[1]}")
        print(f"     - Email: {result[2]}")
        print(f"     - Has password hash: {bool(result[3])}")
        print(f"     - Is admin: {result[6]}")
        
        print(f"\n3. Testing password validation...")
        if result[3]:
            password_valid = check_password_hash(result[3], password)
            print(f"   Password '{password}' validation: {password_valid}")
            
            if not password_valid:
                print(f"\n4. Testing fallback password logic...")
                fallback_password = ADMIN2_SEED_PASSWORD or ''
                print(f"   Fallback password configured: {bool(fallback_password)}")
                if fallback_password and password == fallback_password:
                    print(f"   ✓ Fallback password matches!")
                else:
                    print(f"   ✗ Fallback password does NOT match")
            else:
                print(f"\n   ✓ Primary password validation successful!")
        else:
            print(f"   ✗ No password hash stored")
    else:
        print(f"   ✗ Account still not found after provisioning")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
