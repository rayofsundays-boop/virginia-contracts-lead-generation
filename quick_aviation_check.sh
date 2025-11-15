#!/bin/bash
# Quick Aviation Diagnostic - Run on Render Shell
# Usage: bash quick_aviation_check.sh

echo "🔍 Quick Aviation Diagnostic"
echo "=============================="
echo ""

python3 << 'PYTHON_EOF'
import os
import sys

# Add parent directory to path
sys.path.insert(0, '/opt/render/project/src/..')

try:
    from app import app, db
    from sqlalchemy import text
    
    with app.app_context():
        print("✅ App import successful")
        
        # Check table
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM aviation_cleaning_leads"))
            count = result.scalar()
            print(f"✅ Table exists with {count} records")
            
            # Get sample
            result = db.session.execute(text("""
                SELECT company_name, city, state 
                FROM aviation_cleaning_leads 
                LIMIT 3
            """))
            print("\n📊 Sample data:")
            for i, row in enumerate(result, 1):
                print(f"   {i}. {row[0][:40]} - {row[1]}, {row[2]}")
                
        except Exception as e:
            print(f"❌ Table error: {e}")
            print("\n🔧 Try running: python auto_import_aviation.py")
            
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
PYTHON_EOF
