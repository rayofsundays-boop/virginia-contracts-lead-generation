#!/usr/bin/env python3
"""
Reset admin2 account - Delete and recreate with new credentials
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import text

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Flask app and database
from app import app, db

# New admin2 credentials
NEW_ADMIN2_USERNAME = "admin2"
NEW_ADMIN2_EMAIL = "admin2@vacontracts.com"
NEW_ADMIN2_PASSWORD = "Admin2!Secure123"  # Change this to your desired password

def reset_admin2():
    """Delete existing admin2 account and create a new one with fresh credentials"""
    
    with app.app_context():
        try:
            print("=" * 60)
            print("ADMIN2 ACCOUNT RESET")
            print("=" * 60)
            
            # Step 1: Check if admin2 exists
            print("\n1️⃣ Checking for existing admin2 account...")
            existing = db.session.execute(text("""
                SELECT id, email, username, is_admin, subscription_status
                FROM leads 
                WHERE LOWER(email) = LOWER(:email) OR LOWER(username) = LOWER(:username)
            """), {
                'email': NEW_ADMIN2_EMAIL,
                'username': NEW_ADMIN2_USERNAME
            }).fetchone()
            
            if existing:
                print(f"   ✅ Found existing account:")
                print(f"      ID: {existing[0]}")
                print(f"      Email: {existing[1]}")
                print(f"      Username: {existing[2]}")
                print(f"      Is Admin: {existing[3]}")
                print(f"      Status: {existing[4]}")
                
                # Step 2: Delete the account
                print(f"\n2️⃣ Deleting admin2 account (ID: {existing[0]})...")
                db.session.execute(text("""
                    DELETE FROM leads WHERE id = :id
                """), {'id': existing[0]})
                db.session.commit()
                print("   ✅ Successfully deleted old admin2 account")
            else:
                print("   ℹ️  No existing admin2 account found")
            
            # Step 3: Create new admin2 account
            print(f"\n3️⃣ Creating new admin2 account...")
            print(f"   Username: {NEW_ADMIN2_USERNAME}")
            print(f"   Email: {NEW_ADMIN2_EMAIL}")
            print(f"   Password: {'*' * len(NEW_ADMIN2_PASSWORD)}")
            
            hashed_password = generate_password_hash(NEW_ADMIN2_PASSWORD)
            
            result = db.session.execute(text("""
                INSERT INTO leads (
                    company_name, 
                    contact_name, 
                    email, 
                    username, 
                    password_hash,
                    subscription_status, 
                    credits_balance, 
                    is_admin, 
                    free_leads_remaining,
                    registration_date, 
                    lead_source, 
                    twofa_enabled, 
                    sms_notifications,
                    email_notifications,
                    created_at
                )
                VALUES (
                    :company, 
                    :contact, 
                    :email, 
                    :username, 
                    :password_hash,
                    'paid', 
                    999999, 
                    TRUE, 
                    0,
                    :registration_date, 
                    'system_reset', 
                    FALSE, 
                    FALSE,
                    TRUE,
                    :created_at
                ) RETURNING id, email, username
            """), {
                'company': 'Admin Operations',
                'contact': 'Admin2 Support',
                'email': NEW_ADMIN2_EMAIL,
                'username': NEW_ADMIN2_USERNAME,
                'password_hash': hashed_password,
                'registration_date': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow()
            })
            
            new_account = result.fetchone()
            db.session.commit()
            
            print("   ✅ Successfully created new admin2 account!")
            print(f"      ID: {new_account[0]}")
            print(f"      Email: {new_account[1]}")
            print(f"      Username: {new_account[2]}")
            
            # Step 4: Verify the account
            print(f"\n4️⃣ Verifying new account...")
            verify = db.session.execute(text("""
                SELECT id, username, email, is_admin, subscription_status, credits_balance
                FROM leads WHERE id = :id
            """), {'id': new_account[0]}).fetchone()
            
            if verify:
                print("   ✅ Account verified in database:")
                print(f"      ID: {verify[0]}")
                print(f"      Username: {verify[1]}")
                print(f"      Email: {verify[2]}")
                print(f"      Is Admin: {verify[3]}")
                print(f"      Status: {verify[4]}")
                print(f"      Credits: {verify[5]}")
            else:
                print("   ❌ ERROR: Could not verify account!")
                return False
            
            print("\n" + "=" * 60)
            print("✅ ADMIN2 RESET COMPLETE!")
            print("=" * 60)
            print(f"\nNew Login Credentials:")
            print(f"  URL: https://virginia-contracts-lead-generation.onrender.com/signin")
            print(f"  Username: {NEW_ADMIN2_USERNAME}")
            print(f"  Password: {NEW_ADMIN2_PASSWORD}")
            print("\n⚠️  IMPORTANT: Update your .env file with:")
            print(f"  ADMIN2_SEED_USERNAME={NEW_ADMIN2_USERNAME}")
            print(f"  ADMIN2_SEED_EMAIL={NEW_ADMIN2_EMAIL}")
            print(f"  ADMIN2_SEED_PASSWORD={NEW_ADMIN2_PASSWORD}")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("\n⚠️  WARNING: This will delete and recreate the admin2 account!")
    print(f"New password will be: {NEW_ADMIN2_PASSWORD}")
    response = input("\nProceed? (yes/no): ").strip().lower()
    
    if response == 'yes':
        success = reset_admin2()
        sys.exit(0 if success else 1)
    else:
        print("❌ Operation cancelled")
        sys.exit(0)
