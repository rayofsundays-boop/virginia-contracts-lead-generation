#!/usr/bin/env python3
"""
Delete all fake commercial lead requests created by migration scripts.

These are demo/test leads with 757-555-XXXX phone numbers that were added
for testing purposes but should not appear in production.
"""

import sqlite3
from datetime import datetime

def delete_fake_commercial_leads():
    """Remove all fake commercial leads from the database"""
    
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    print('🔍 Checking for fake commercial leads...\n')
    
    # Get current fake leads
    cursor.execute('''
        SELECT business_name, phone, email, created_at
        FROM commercial_lead_requests
        WHERE phone LIKE '757-555-%'
    ''')
    
    fake_leads = cursor.fetchall()
    
    if not fake_leads:
        print('✅ No fake leads found! Database is clean.')
        conn.close()
        return
    
    print(f'⚠️  Found {len(fake_leads)} fake commercial leads:\n')
    for lead in fake_leads:
        print(f'   🚫 {lead[0]} - {lead[1]} ({lead[2]})')
    
    print(f'\n🗑️  Deleting {len(fake_leads)} fake leads...')
    
    # Delete all leads with 555 phone numbers (reserved for fictional use)
    cursor.execute('''
        DELETE FROM commercial_lead_requests
        WHERE phone LIKE '757-555-%'
    ''')
    
    deleted_count = cursor.rowcount
    conn.commit()
    
    print(f'✅ Successfully deleted {deleted_count} fake commercial leads')
    
    # Verify cleanup
    cursor.execute('SELECT COUNT(*) FROM commercial_lead_requests')
    remaining = cursor.fetchone()[0]
    print(f'📊 Remaining commercial leads: {remaining}')
    
    conn.close()
    
    # Create log entry
    log_file = 'FAKE_DATA_CLEANUP_LOG.txt'
    with open(log_file, 'a') as f:
        f.write(f'\n{"="*80}\n')
        f.write(f'Fake Commercial Leads Cleanup - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'{"="*80}\n\n')
        f.write(f'Deleted {deleted_count} fake commercial leads:\n')
        for lead in fake_leads:
            f.write(f'  - {lead[0]} ({lead[1]})\n')
        f.write(f'\nRemaining leads: {remaining}\n')
    
    print(f'\n📝 Cleanup logged to {log_file}')

if __name__ == '__main__':
    print('🚨 FAKE COMMERCIAL LEADS CLEANUP TOOL\n')
    print('This will permanently delete all commercial leads with 757-555-XXXX phone numbers.')
    print('These are demo/test leads created by migration scripts.\n')
    
    response = input('Continue? (yes/no): ').strip().lower()
    
    if response == 'yes':
        delete_fake_commercial_leads()
        print('\n✅ Cleanup complete!')
    else:
        print('\n❌ Cleanup cancelled')
