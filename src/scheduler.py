"""
Scheduler for VA Contracts Lead Generation Platform
Handles automated daily email briefings using APScheduler
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from email_service import send_email
import email_templates

# Global scheduler instance
scheduler = None

def fetch_daily_leads():
    """
    Fetch leads from the last 24 hours from the database
    
    Returns:
        list: List of lead dictionaries
    """
    from database import get_db
    
    db = get_db()
    cursor = db.cursor()
    
    # Get leads from last 24 hours
    cursor.execute("""
        SELECT title, state, estimated_value, deadline, description
        FROM federal_contracts
        WHERE created_at >= datetime('now', '-1 day')
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    # Format leads for email template
    leads = []
    for row in rows:
        leads.append({
            'project': row[0] or 'Unnamed Project',
            'state': row[1] or 'N/A',
            'value': f"${row[2]:,.0f}" if row[2] else 'N/A',
            'deadline': row[3] or 'N/A',
            'description': row[4] or 'No description available.'
        })
    
    return leads

def get_subscriber_emails():
    """
    Fetch all active subscriber email addresses from the database
    
    Returns:
        list: List of email addresses
    """
    from database import get_db
    
    db = get_db()
    cursor = db.cursor()
    
    # Get all users with active subscriptions
    cursor.execute("""
        SELECT email
        FROM users
        WHERE subscription_status = 'active'
        AND email IS NOT NULL
        AND email != ''
    """)
    
    rows = cursor.fetchall()
    return [row[0] for row in rows]

def daily_briefing_job():
    """
    Job function that runs daily at 8 AM EST
    Sends briefing emails to all active subscribers
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running daily briefing job...")
    
    # Fetch leads
    leads = fetch_daily_leads()
    print(f"Found {len(leads)} leads from the last 24 hours")
    
    # Fetch subscriber emails
    subscriber_emails = get_subscriber_emails()
    print(f"Found {len(subscriber_emails)} active subscribers")
    
    if not subscriber_emails:
        print("No active subscribers found. Skipping email send.")
        return
    
    # Send daily briefing to each subscriber
    success_count = 0
    for email in subscriber_emails:
        try:
            success = send_email(
                to=email,
                subject=f"📊 Daily Briefing: {len(leads)} New Lead{'s' if len(leads) != 1 else ''}",
                html=email_templates.daily_briefing(leads)
            )
            if success:
                success_count += 1
        except Exception as e:
            print(f"Error sending daily briefing to {email}: {e}")
    
    print(f"Daily briefing completed. Sent to {success_count}/{len(subscriber_emails)} subscribers.")

def start_scheduler():
    """
    Initialize and start the background scheduler
    Schedules daily briefing emails at 8 AM EST
    """
    global scheduler
    
    if scheduler is not None:
        print("⚠️ Scheduler already running. Skipping initialization.")
        return
    
    scheduler = BackgroundScheduler(daemon=True)
    
    # Schedule daily briefing at 8:00 AM EST
    scheduler.add_job(
        daily_briefing_job,
        'cron',
        hour=8,
        minute=0,
        timezone='America/New_York',
        id='daily_briefing',
        replace_existing=True
    )
    
    scheduler.start()
    print(f"✅ Scheduler started. Daily briefing scheduled for 8:00 AM EST.")
    print(f"   Next run: {scheduler.get_job('daily_briefing').next_run_time}")

def stop_scheduler():
    """
    Stop the background scheduler
    Used during application shutdown
    """
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        print("✅ Scheduler stopped successfully.")
