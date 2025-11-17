"""
Add Stripe payment columns to leads table for unified checkout system.
Run this script once to add the necessary columns for Stripe integration.
"""

import sqlite3
from datetime import datetime

def add_stripe_columns():
    """Add Stripe customer and subscription ID columns to leads table"""
    
    try:
        # Connect to database
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        
        # Add Stripe customer ID column
        try:
            cursor.execute('''
                ALTER TABLE leads 
                ADD COLUMN stripe_customer_id TEXT
            ''')
            print("✅ Added stripe_customer_id column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  stripe_customer_id column already exists")
            else:
                raise
        
        # Add Stripe subscription ID column
        try:
            cursor.execute('''
                ALTER TABLE leads 
                ADD COLUMN stripe_subscription_id TEXT
            ''')
            print("✅ Added stripe_subscription_id column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  stripe_subscription_id column already exists")
            else:
                raise
        
        # Add subscription plan column (monthly/annual)
        try:
            cursor.execute('''
                ALTER TABLE leads 
                ADD COLUMN subscription_plan TEXT
            ''')
            print("✅ Added subscription_plan column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  subscription_plan column already exists")
            else:
                raise
        
        # Add subscription start date column
        try:
            cursor.execute('''
                ALTER TABLE leads 
                ADD COLUMN subscription_start_date TIMESTAMP
            ''')
            print("✅ Added subscription_start_date column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  subscription_start_date column already exists")
            else:
                raise
        
        # Add PayPal subscription ID column (if not exists)
        try:
            cursor.execute('''
                ALTER TABLE leads 
                ADD COLUMN paypal_subscription_id TEXT
            ''')
            print("✅ Added paypal_subscription_id column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️  paypal_subscription_id column already exists")
            else:
                raise
        
        # Commit changes
        conn.commit()
        print("\n✅ Database schema updated successfully!")
        print("   All payment processing columns are now available.")
        
        # Verify columns exist
        cursor.execute("PRAGMA table_info(leads)")
        columns = cursor.fetchall()
        payment_cols = [col for col in columns if any(term in col[1] 
                       for term in ['stripe', 'paypal', 'subscription_plan', 'subscription_start'])]
        
        print(f"\n📊 Payment-related columns in leads table:")
        for col in payment_cols:
            print(f"   - {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        raise

if __name__ == '__main__':
    print("🔧 Adding Stripe payment columns to database...\n")
    add_stripe_columns()
    print("\n✨ Migration complete! You can now use the unified checkout system.")
