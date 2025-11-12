"""
Migration script to add website_url column to commercial_opportunities table
This fixes SELECT query failures when trying to display commercial leads.

Run this script to fix commercial leads display errors.
"""

import sqlite3

def migrate_database():
    """Add website_url column to commercial_opportunities table"""
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    print("🔧 Adding website_url column to commercial_opportunities...")
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(commercial_opportunities)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'website_url' in columns:
        print("ℹ️  website_url column already exists")
    else:
        try:
            cursor.execute("""
                ALTER TABLE commercial_opportunities 
                ADD COLUMN website_url TEXT
            """)
            conn.commit()
            print("✅ Added website_url column")
        except Exception as e:
            print(f"❌ Error adding website_url column: {e}")
            conn.rollback()
            return False
    
    # Verify the column was added
    cursor.execute("PRAGMA table_info(commercial_opportunities)")
    columns = [column[1] for column in cursor.fetchall()]
    
    print(f"\n✅ Migration completed successfully!")
    print(f"\ncommercial_opportunities table now has {len(columns)} columns:")
    for col in columns:
        print(f"  • {col}")
    
    conn.close()
    return True

if __name__ == '__main__':
    success = migrate_database()
    if success:
        print("\n🎉 Commercial leads should now display properly!")
    else:
        print("\n⚠️  Migration encountered errors. Check output above.")
