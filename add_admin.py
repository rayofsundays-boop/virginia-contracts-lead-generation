#!/usr/bin/env python3
"""
Script to add a new admin user to the database
Usage: python add_admin.py
"""

from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text
import os

def add_admin():
    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Please set it in your .env file or environment")
        return
    
    # Fix postgres:// to postgresql:// if needed
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print("🔐 Add New Admin User")
    print("=" * 50)
    
    # Get admin details
    email = input("Admin Email: ").strip()
    if not email:
        print("❌ Email is required")
        return
    
    password = input("Admin Password: ").strip()
    if not password:
        print("❌ Password is required")
        return
    
    contact_name = input("Contact Name (optional): ").strip() or "Admin"
    company_name = input("Company Name (optional): ").strip() or "Admin Account"
    
    # Generate password hash
    password_hash = generate_password_hash(password)
    
    print("\n📝 Creating admin account...")
    print(f"Email: {email}")
    print(f"Name: {contact_name}")
    print(f"Company: {company_name}")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if user already exists
            result = conn.execute(
                text("SELECT email FROM leads WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if result:
                print(f"\n⚠️  User with email {email} already exists!")
                update = input("Update to admin status? (y/n): ").strip().lower()
                if update == 'y':
                    conn.execute(
                        text("""
                            UPDATE leads 
                            SET subscription_status = 'admin', 
                                password_hash = :password_hash
                            WHERE email = :email
                        """),
                        {"email": email, "password_hash": password_hash}
                    )
                    conn.commit()
                    print("✅ User updated to admin status!")
                return
            
            # Insert new admin user
            conn.execute(
                text("""
                    INSERT INTO leads (
                        company_name, contact_name, email, password_hash,
                        subscription_status, created_at
                    ) VALUES (
                        :company_name, :contact_name, :email, :password_hash,
                        'admin', CURRENT_TIMESTAMP
                    )
                """),
                {
                    "company_name": company_name,
                    "contact_name": contact_name,
                    "email": email,
                    "password_hash": password_hash
                }
            )
            conn.commit()
            
            print("\n✅ Admin user created successfully!")
            print(f"\n📧 Login at: https://virginia-contracts-lead-generation.onrender.com/login")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print("\n⚠️  IMPORTANT: Save these credentials securely!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_admin()
