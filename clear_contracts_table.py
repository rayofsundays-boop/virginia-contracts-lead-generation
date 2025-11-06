#!/usr/bin/env python3
"""
Clear ALL contracts from contracts table
Run this to remove all potentially fake local/state contracts
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

with app.app_context():
    print("⚠️  WARNING: This will DELETE ALL contracts from the contracts table")
    print("This includes all local and state government contracts")
    
    # Count before deletion
    count_before = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar()
    print(f"\n📊 Current count: {count_before} contracts")
    
    confirm = input("\nType 'DELETE ALL' to confirm: ")
    
    if confirm == "DELETE ALL":
        db.session.execute(text('DELETE FROM contracts'))
        db.session.commit()
        
        count_after = db.session.execute(text('SELECT COUNT(*) FROM contracts')).scalar()
        print(f"\n✅ Deleted {count_before} contracts")
        print(f"✅ Remaining contracts: {count_after}")
        print("\n✅ Contracts table is now EMPTY")
        print("\n💡 Next: /contracts page will show 'No contracts available'")
        print("   Add real contracts from verified sources only")
    else:
        print("\n❌ Deletion cancelled")
