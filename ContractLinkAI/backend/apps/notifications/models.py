"""
Notification models for ContractLink AI.
Manages user notifications and email digests.
"""
from django.db import models
from apps.users.models import User
from apps.rfps.models import RFP


class Notification(models.Model):
    """
    In-app notifications for users.
    """
    NOTIFICATION_TYPES = [
        ('new_rfp', 'New RFP Match'),
        ('rfp_expiring', 'RFP Expiring Soon'),
        ('rfp_awarded', 'RFP Awarded'),
        ('system', 'System Announcement'),
        ('account', 'Account Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification details
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related objects
    rfp = models.ForeignKey(
        RFP,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Action link
    action_url = models.URLField(max_length=500, blank=True)
    action_text = models.CharField(max_length=100, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class EmailDigest(models.Model):
    """
    Track email digests sent to users.
    """
    DIGEST_TYPES = [
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Summary'),
        ('immediate', 'Immediate Alert'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_digests')
    
    # Digest details
    digest_type = models.CharField(max_length=20, choices=DIGEST_TYPES)
    subject = models.CharField(max_length=255)
    
    # Content
    rfps_included = models.ManyToManyField(RFP, related_name='email_digests')
    total_rfps = models.IntegerField(default=0)
    
    # Status
    sent_at = models.DateTimeField(auto_now_add=True)
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked = models.BooleanField(default=False)
    
    # Email service tracking
    email_service_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'email_digests'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', '-sent_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.digest_type} on {self.sent_at}"
