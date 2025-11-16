"""
Celery tasks for RFP management.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from apps.rfps.models import RFP

logger = logging.getLogger('rfps')


@shared_task(name='rfps.tasks.cleanup_old_rfps')
def cleanup_old_rfps():
    """
    Clean up old RFPs (>90 days old and expired).
    Runs weekly on Sunday at 3:00 AM.
    """
    logger.info("Starting cleanup of old RFPs")
    
    cutoff_date = timezone.now() - timedelta(days=90)
    
    # Mark old RFPs as expired
    expired_count = RFP.objects.filter(
        due_date__lt=cutoff_date,
        status='active'
    ).update(status='expired')
    
    logger.info(f"Marked {expired_count} RFPs as expired")
    
    # Optionally delete very old RFPs (older than 1 year)
    # very_old_cutoff = timezone.now() - timedelta(days=365)
    # deleted_count = RFP.objects.filter(
    #     created_at__lt=very_old_cutoff,
    #     status='expired'
    # ).delete()[0]
    # logger.info(f"Deleted {deleted_count} very old RFPs")
    
    return {'expired_count': expired_count}
