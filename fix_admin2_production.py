#!/usr/bin/env python3
"""
Fix admin2 password in production database.
Run this on Render via: python fix_admin2_production.py
"""

import os
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

def fix_admin2_password():
    """Fix admin2 password hash in production database"""
    
    with app.app_context():
        try:
            print("=" * 70)
            print("FIXING ADMIN2 PASSWORD IN PRODUCTION")
            print("=" * 70)
            print(f"Database: {str(db.engine.url)[:80]}...")
            print(f"Target account: {ADMIN2_USERNAME} / {ADMIN2_EMAIL}")
            print(f"Password to set: {ADMIN2_PASSWORD}")
            print("=" * 70)
            
            # Check if admin2 exists
            result = db.session.execute(text("""
                SELECT id, email, username, password_hash, is_admin
                FROM leads 
                WHERE LOWER(email) = LOWER(:email) OR LOWER(username) = LOWER(:username)
            """), {
                'email': ADMIN2_EMAIL,
                'username': ADMIN2_USERNAME
            }).fetchone()
            
            if result:
                print(f"\n✅ Admin2 account found (ID: {result[0]})")
                print(f"   Email: {result[1]}")
                print(f"   Username: {result[2]}")
                print(f"   Current is_admin: {result[4]}")
                
                # Test current password
                if result[3]:
                    current_works = check_password_hash(result[3], ADMIN2_PASSWORD)
                    print(f"   Current password works: {current_works}")
                    
                    if current_works:
                        print("\n✅ Password already correct! No fix needed.")
                        return
                else:
                    print("   ⚠️  No password hash set")
                
                # Generate new hash
                print(f"\n🔧 Generating new password hash...")
                new_hash = generate_password_hash(ADMIN2_PASSWORD)
                print(f"   New hash: {new_hash[:60]}...")
                
                # Update the password and ensure is_admin is True
                print(f"\n💾 Updating database...")
                db.session.execute(text("""
                    UPDATE leads 
                    SET password_hash = :hash,
                        is_admin = TRUE,
                        subscription_status = 'paid',
                        credits_balance = 999999
                    WHERE id = :id
                """), {
                    'hash': new_hash,
                    'id': result[0]
                })
                db.session.commit()
                
                # Verify the fix
                print(f"\n✅ Database updated. Verifying...")
                verify = db.session.execute(text("""
                    SELECT password_hash, is_admin 
                    FROM leads WHERE id = :id
                """), {'id': result[0]}).fetchone()
                
                final_check = check_password_hash(verify[0], ADMIN2_PASSWORD)
                print(f"   Password verification: {final_check}")
                print(f"   is_admin flag: {verify[1]}")
                
                if final_check:
                    print("\n✅ ✅ ✅ SUCCESS! Admin2 password fixed!")
                    print(f"\nYou can now login with:")
                    print(f"   Username: {ADMIN2_USERNAME}")
                    print(f"   Password: {ADMIN2_PASSWORD}")
                else:
                    print("\n❌ Verification failed - password still doesn't work")
                    
            else:
                print("\n⚠️  Admin2 account doesn't exist - creating it...")
                
                # Create admin2 account
                pw_hash = generate_password_hash(ADMIN2_PASSWORD)
                
                db.session.execute(text("""
                    INSERT INTO leads (
                        company_name, contact_name, email, username, password_hash,
                        subscription_status, credits_balance, is_admin, free_leads_remaining,
                        registration_date, lead_source, twofa_enabled, sms_notifications,
                        email_notifications
                    ) VALUES (
                        :company, :contact, :email, :username, :password_hash,
                        'paid', 999999, TRUE, 0,
                        :registration_date, 'system_bootstrap', FALSE, FALSE, TRUE
                    )
                """), {
                    'company': 'Admin Operations',
                    'contact': 'Admin2 Support',
                    'email': ADMIN2_EMAIL,
                    'username': ADMIN2_USERNAME,
                    'password_hash': pw_hash,
                    'registration_date': datetime.utcnow().isoformat()
                })
                db.session.commit()
                print('✅ Admin2 account created successfully!')
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    fix_admin2_password()
