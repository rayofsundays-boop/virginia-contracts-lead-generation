#!/usr/bin/env python3
"""Test updated authentication system with users table"""

from app import app, db, _fetch_user_credentials
from werkzeug.security import check_password_hash

with app.app_context():
    print("=" * 70)
    print("TESTING UPDATED AUTHENTICATION SYSTEM")
    print("=" * 70)
    
    # Test admin2
    print("\n1. Testing admin2 authentication:")
    result = _fetch_user_credentials('admin2')
    if result:
        print(f"   ✅ User found via _fetch_user_credentials")
        print(f"   ID: {result[0]}")
        print(f"   Username: {result[1]}")
        print(f"   Email: {result[2]}")
        print(f"   Is Admin: {result[6]}")
        
        # Test password
        password_valid = check_password_hash(result[3], 'Admin2!Secure123')
        print(f"   Password valid: {password_valid}")
    else:
        print(f"   ❌ User NOT found")
    
    # Test testuser
    print("\n2. Testing testuser authentication:")
    result = _fetch_user_credentials('test@example.com')
    if result:
        print(f"   ✅ User found via _fetch_user_credentials")
        print(f"   ID: {result[0]}")
        print(f"   Username: {result[1]}")
        print(f"   Email: {result[2]}")
        print(f"   Is Admin: {result[6]}")
    else:
        print(f"   ❌ User NOT found")
    
    # Check both tables
    print("\n3. Database status:")
    from sqlalchemy import text
    
    users_count = db.session.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
    leads_count = db.session.execute(text("SELECT COUNT(*) FROM leads WHERE username IS NOT NULL")).fetchone()[0]
    
    print(f"   Users table: {users_count} records")
    print(f"   Leads table: {leads_count} user records")
    
    print("\n" + "=" * 70)
    print("✅ AUTHENTICATION SYSTEM TEST COMPLETE")
    print("=" * 70)
