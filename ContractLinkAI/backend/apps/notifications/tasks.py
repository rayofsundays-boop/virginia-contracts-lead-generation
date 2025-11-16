"""
Celery tasks for notifications and email digests.
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging
from apps.users.models import User
from apps.rfps.models import RFP
from apps.notifications.models import Notification, EmailDigest

logger = logging.getLogger('notifications')


@shared_task(name='notifications.tasks.send_notification_emails')
def send_notification_emails():
    """
    Send daily digest emails to subscribed users.
    Runs daily at 8:00 AM.
    """
    logger.info("Starting daily notification emails")
    
    # Get users who want daily digests
    daily_users = User.objects.filter(
        email_notifications_enabled=True,
        notification_frequency='daily',
        is_subscription_active=True
    )
    
    sent_count = 0
    
    for user in daily_users:
        try:
            # Get new RFPs matching user preferences
            rfps = get_relevant_rfps_for_user(user, days_back=1)
            
            if rfps.count() == 0:
                logger.info(f"No new RFPs for {user.username}, skipping email")
                continue
            
            # Send email
            subject = f"ContractLink AI: {rfps.count()} New Opportunities"
            message = build_email_message(user, rfps)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            # Track email digest
            digest = EmailDigest.objects.create(
                user=user,
                digest_type='daily',
                subject=subject,
                total_rfps=rfps.count()
            )
            digest.rfps_included.set(rfps)
            
            sent_count += 1
            logger.info(f"Sent daily digest to {user.username}")
            
        except Exception as e:
            logger.error(f"Error sending email to {user.username}: {str(e)}")
    
    logger.info(f"Daily emails complete: {sent_count} sent")
    return {'sent_count': sent_count}


def get_relevant_rfps_for_user(user: User, days_back: int = 1):
    """
    Get RFPs relevant to user's preferences.
    """
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(days=days_back)
    
    rfps = RFP.objects.filter(
        created_at__gte=cutoff,
        status='active'
    )
    
    # Filter by preferred states
    if user.preferred_states:
        rfps = rfps.filter(source_state__in=user.preferred_states)
    
    # Filter by preferred categories
    if user.preferred_categories:
        rfps = rfps.filter(category__in=user.preferred_categories)
    
    # Filter by minimum contract value
    if user.minimum_contract_value:
        rfps = rfps.filter(estimated_value__gte=user.minimum_contract_value)
    
    return rfps


def build_email_message(user: User, rfps):
    """
    Build email message content.
    """
    message = f"""Hello {user.first_name or user.username},

Here are {rfps.count()} new government procurement opportunities matching your preferences:

"""
    
    for rfp in rfps[:10]:  # Show top 10
        message += f"""
Title: {rfp.title}
Agency: {rfp.issuing_agency}
State: {rfp.source_state}
Due Date: {rfp.due_date.strftime('%Y-%m-%d') if rfp.due_date else 'N/A'}
View: {rfp.source_url}

---
"""
    
    if rfps.count() > 10:
        message += f"\n... and {rfps.count() - 10} more opportunities.\n"
    
    message += f"""
View all opportunities: https://contractlink.ai/rfps

Best regards,
ContractLink AI Team
"""
    
    return message
