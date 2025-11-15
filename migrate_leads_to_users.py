#!/usr/bin/env python3
"""
Migrate user data from leads table to users table.
This preserves all authentication and user data while transitioning to the new structure.

Run: python migrate_leads_to_users.py
"""

import os
from datetime import datetime
from sqlalchemy import text
from app import app, db

def migrate_leads_to_users():
    """Migrate user data from leads table to users table"""
    
    with app.app_context():
        try:
            print("=" * 70)
            print("MIGRATING USERS FROM LEADS TO USERS TABLE")
            print("=" * 70)
            
            # Check if users table exists
            try:
                users_count = db.session.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
                print(f"✅ Users table exists with {users_count} records")
            except:
                print("❌ Users table doesn't exist. Run create_users_table.py first!")
                return
            
            # Get all users from leads table
            leads = db.session.execute(text("""
                SELECT 
                    id, username, email, password_hash, contact_name, company_name,
                    phone, is_admin, subscription_status, credits_balance, credits_used,
                    twofa_enabled, twofa_secret, email_notifications, sms_notifications,
                    registration_date, lead_source, created_at, free_leads_remaining,
                    is_beta_tester, beta_expiry_date
                FROM leads
                WHERE username IS NOT NULL AND email IS NOT NULL
                ORDER BY id
            """)).fetchall()
            
            print(f"\n📊 Found {len(leads)} user accounts in leads table")
            
            if len(leads) == 0:
                print("⚠️  No users to migrate")
                return
            
            migrated = 0
            skipped = 0
            errors = 0
            
            print("\n🔄 Starting migration...")
            print("-" * 70)
            
            for lead in leads:
                try:
                    lead_id, username, email, password_hash, contact_name, company_name, phone, \
                    is_admin, subscription_status, credits_balance, credits_used, \
                    twofa_enabled, twofa_secret, email_notifications, sms_notifications, \
                    registration_date, lead_source, created_at, free_credits_remaining, \
                    is_beta_tester, beta_expiry_date = lead
                    
                    # Check if user already exists in users table
                    existing = db.session.execute(text("""
                        SELECT id FROM users WHERE email = :email OR username = :username
                    """), {'email': email, 'username': username}).fetchone()
                    
                    if existing:
                        print(f"⏭️  Skipping {username} ({email}) - already exists in users table")
                        skipped += 1
                        continue
                    
                    # Parse name
                    first_name = None
                    last_name = None
                    full_name = contact_name
                    
                    if contact_name and ' ' in contact_name:
                        parts = contact_name.split(' ', 1)
                        first_name = parts[0]
                        last_name = parts[1] if len(parts) > 1 else None
                    else:
                        first_name = contact_name
                    
                    # Determine subscription tier
                    subscription_tier = 'free'
                    if subscription_status == 'paid':
                        subscription_tier = 'premium'
                    elif is_beta_tester:
                        subscription_tier = 'beta'
                    
                    # Insert into users table
                    db.session.execute(text("""
                        INSERT INTO users (
                            username, email, password_hash, first_name, last_name, full_name,
                            phone, company_name, is_active, is_verified, is_admin, is_superuser,
                            subscription_status, subscription_tier, subscription_end_date,
                            credits_balance, credits_used, free_credits_remaining,
                            twofa_enabled, twofa_secret, email_notifications, sms_notifications,
                            lead_source, created_at, updated_at
                        ) VALUES (
                            :username, :email, :password_hash, :first_name, :last_name, :full_name,
                            :phone, :company_name, 1, 1, :is_admin, 0,
                            :subscription_status, :subscription_tier, :subscription_end_date,
                            :credits_balance, :credits_used, :free_credits_remaining,
                            :twofa_enabled, :twofa_secret, :email_notifications, :sms_notifications,
                            :lead_source, :created_at, :updated_at
                        )
                    """), {
                        'username': username,
                        'email': email,
                        'password_hash': password_hash,
                        'first_name': first_name,
                        'last_name': last_name,
                        'full_name': full_name,
                        'phone': phone,
                        'company_name': company_name,
                        'is_admin': bool(is_admin),
                        'subscription_status': subscription_status or 'free',
                        'subscription_tier': subscription_tier,
                        'subscription_end_date': beta_expiry_date,
                        'credits_balance': credits_balance or 0,
                        'credits_used': credits_used or 0,
                        'free_credits_remaining': free_credits_remaining or 0,
                        'twofa_enabled': bool(twofa_enabled),
                        'twofa_secret': twofa_secret,
                        'email_notifications': bool(email_notifications) if email_notifications is not None else True,
                        'sms_notifications': bool(sms_notifications) if sms_notifications is not None else False,
                        'lead_source': lead_source or 'website',
                        'created_at': created_at or registration_date or datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    })
                    
                    db.session.commit()
                    print(f"✅ Migrated: {username} ({email}) - {subscription_tier}")
                    migrated += 1
                    
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Error migrating {email}: {e}")
                    errors += 1
            
            print("-" * 70)
            print(f"\n📊 MIGRATION SUMMARY")
            print("=" * 70)
            print(f"Total users in leads:  {len(leads)}")
            print(f"✅ Successfully migrated: {migrated}")
            print(f"⏭️  Skipped (duplicates):  {skipped}")
            print(f"❌ Errors:                {errors}")
            print("=" * 70)
            
            # Verify migration
            final_count = db.session.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
            print(f"\n✅ Users table now has {final_count} records")
            
            if migrated > 0:
                print("\n⚠️  IMPORTANT:")
                print("1. Update authentication routes to use 'users' table instead of 'leads'")
                print("2. Test login functionality thoroughly")
                print("3. Consider keeping 'leads' table for non-user lead management")
                print("4. Update session management to reference 'users.id'")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    migrate_leads_to_users()
