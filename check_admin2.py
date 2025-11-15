#!/usr/bin/env python3
"""
Force admin2 provisioning in production database
This should be run on Render or with production DATABASE_URL
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Flask app and database
from app import app, db

# Admin2 credentials from environment or defaults
ADMIN2_USERNAME = os.getenv('ADMIN2_SEED_USERNAME', 'admin2')
ADMIN2_EMAIL = os.getenv('ADMIN2_SEED_EMAIL', 'admin2@vacontracts.com')
ADMIN2_PASSWORD = os.getenv('ADMIN2_SEED_PASSWORD', 'Admin2!Secure123')

def check_admin2():
    """Check admin2 status and credentials"""
    
    with app.app_context():
        try:
            print("=" * 70)
            print("ADMIN2 ACCOUNT STATUS CHECK")
            print("=" * 70)
            print(f"Database: {os.getenv('DATABASE_URL', 'SQLite (local)')[:50]}...")
            print(f"Looking for: {ADMIN2_USERNAME} / {ADMIN2_EMAIL}")
            print("=" * 70)
            
            # Check if admin2 exists
            result = db.session.execute(text("""
                SELECT id, email, username, password_hash, is_admin, 
                       subscription_status, credits_balance, created_at
                FROM leads 
                WHERE LOWER(email) = LOWER(:email) OR LOWER(username) = LOWER(:username)
            """), {
                'email': ADMIN2_EMAIL,
                'username': ADMIN2_USERNAME
            }).fetchone()
            
            if result:
                print("\n✅ ADMIN2 ACCOUNT FOUND:")
                print(f"   ID: {result[0]}")
                print(f"   Email: {result[1]}")
                print(f"   Username: {result[2]}")
                print(f"   Has Password: {'Yes' if result[3] else 'NO - MISSING!'}")
                print(f"   Is Admin: {'Yes' if result[4] else 'NO'}")
                print(f"   Status: {result[5]}")
                print(f"   Credits: {result[6]}")
                print(f"   Created: {result[7]}")
                
                # Test password
                if result[3]:
                    password_valid = check_password_hash(result[3], ADMIN2_PASSWORD)
                    print(f"\n🔐 Password Test:")
                    print(f"   Testing password: {'*' * len(ADMIN2_PASSWORD)}")
                    if password_valid:
                        print(f"   ✅ PASSWORD MATCHES - Login should work!")
                    else:
                        print(f"   ❌ PASSWORD DOES NOT MATCH")
                        print(f"   The password '{ADMIN2_PASSWORD}' doesn't match the hash in database")
                        print(f"\n💡 Fix: Update the password hash...")
                        
                        response = input("\nUpdate password hash? (yes/no): ").strip().lower()
                        if response == 'yes':
                            new_hash = generate_password_hash(ADMIN2_PASSWORD)
                            db.session.execute(text("""
                                UPDATE leads 
                                SET password_hash = :hash,
                                    is_admin = TRUE,
                                    subscription_status = 'paid',
                                    credits_balance = 999999
                                WHERE id = :id
                            """), {'hash': new_hash, 'id': result[0]})
                            db.session.commit()
                            print("   ✅ Password updated successfully!")
                            print(f"\n   Try logging in now with:")
                            print(f"   Username: {ADMIN2_USERNAME}")
                            print(f"   Password: {ADMIN2_PASSWORD}")
                else:
                    print(f"\n   ❌ NO PASSWORD HASH - Cannot log in!")
                    
                    response = input("\nSet password hash? (yes/no): ").strip().lower()
                    if response == 'yes':
                        new_hash = generate_password_hash(ADMIN2_PASSWORD)
                        db.session.execute(text("""
                            UPDATE leads 
                            SET password_hash = :hash,
                                is_admin = TRUE,
                                subscription_status = 'paid',
                                credits_balance = 999999
                            WHERE id = :id
                        """), {'hash': new_hash, 'id': result[0]})
                        db.session.commit()
                        print("   ✅ Password set successfully!")
                        
            else:
                print("\n❌ ADMIN2 ACCOUNT NOT FOUND")
                print(f"\nSearched for:")
                print(f"   Username: {ADMIN2_USERNAME}")
                print(f"   Email: {ADMIN2_EMAIL}")
                
                response = input("\nCreate admin2 account? (yes/no): ").strip().lower()
                if response == 'yes':
                    print(f"\n📝 Creating admin2 account...")
                    hashed_password = generate_password_hash(ADMIN2_PASSWORD)
                    
                    new_result = db.session.execute(text("""
                        INSERT INTO leads (
                            company_name, contact_name, email, username, password_hash,
                            subscription_status, credits_balance, is_admin, free_leads_remaining,
                            registration_date, lead_source, twofa_enabled, sms_notifications,
                            email_notifications, created_at
                        )
                        VALUES (
                            :company, :contact, :email, :username, :password_hash,
                            'paid', 999999, TRUE, 0,
                            :registration_date, 'system_provision', FALSE, FALSE,
                            TRUE, CURRENT_TIMESTAMP
                        ) RETURNING id, email, username
                    """), {
                        'company': 'Admin Operations',
                        'contact': 'Admin2 Support',
                        'email': ADMIN2_EMAIL,
                        'username': ADMIN2_USERNAME,
                        'password_hash': hashed_password,
                        'registration_date': datetime.utcnow().isoformat()
                    })
                    
                    new_account = new_result.fetchone()
                    db.session.commit()
                    
                    print(f"   ✅ Created successfully!")
                    print(f"      ID: {new_account[0]}")
                    print(f"      Email: {new_account[1]}")
                    print(f"      Username: {new_account[2]}")
                    print(f"\n   Login credentials:")
                    print(f"   Username: {ADMIN2_USERNAME}")
                    print(f"   Password: {ADMIN2_PASSWORD}")
            
            print("\n" + "=" * 70)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    check_admin2()
