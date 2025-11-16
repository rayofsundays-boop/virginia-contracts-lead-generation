"""
Celery configuration for ContractLink AI.
Handles background tasks: scraping, AI classification, notifications.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractlink_backend.settings')

app = Celery('contractlink_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule - Automated background tasks
app.conf.beat_schedule = {
    # Scrape all 50 state portals hourly
    'hourly-state-scrape': {
        'task': 'scrapers.tasks.hourly_state_scrape',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    
    # Discover new city procurement portals nightly using AI
    'nightly-city-discovery': {
        'task': 'scrapers.tasks.nightly_city_discovery',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
    },
    
    # Classify newly discovered RFPs using AI
    'classify-new-rfps': {
        'task': 'ai_engine.tasks.classify_new_rfps',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    
    # Send digest email notifications to subscribers
    'send-notification-emails': {
        'task': 'notifications.tasks.send_notification_emails',
        'schedule': crontab(hour=8, minute=0),  # 8:00 AM daily
    },
    
    # Clean up old RFPs (older than 90 days)
    'cleanup-old-rfps': {
        'task': 'rfps.tasks.cleanup_old_rfps',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3:00 AM
    },
}

app.conf.timezone = 'America/New_York'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery configuration."""
    print(f'Request: {self.request!r}')
