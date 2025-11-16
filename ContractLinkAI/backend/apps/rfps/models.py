"""
RFP (Request for Proposal) models for ContractLink AI.
Core data model for government procurement opportunities.
"""
from django.db import models
from django.utils import timezone
from apps.users.models import User


class RFP(models.Model):
    """
    Main RFP model storing government procurement opportunities.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('awarded', 'Awarded'),
        ('cancelled', 'Cancelled'),
    ]
    
    CATEGORY_CHOICES = [
        ('janitorial', 'Janitorial Services'),
        ('construction', 'Construction'),
        ('it_services', 'IT Services'),
        ('consulting', 'Consulting'),
        ('maintenance', 'Maintenance'),
        ('supplies', 'Supplies & Equipment'),
        ('professional_services', 'Professional Services'),
        ('transportation', 'Transportation'),
        ('other', 'Other'),
    ]
    
    # Identification
    rfp_number = models.CharField(max_length=255, unique=True, db_index=True)
    title = models.TextField()
    description = models.TextField(blank=True)
    
    # Source information
    source_url = models.URLField(max_length=500)
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('state_portal', 'State Portal'),
            ('city_portal', 'City Portal'),
            ('federal', 'Federal (SAM.gov)'),
            ('county', 'County Portal'),
        ],
        default='state_portal'
    )
    source_state = models.CharField(max_length=2, db_index=True)  # State code (e.g., 'VA')
    source_city = models.CharField(max_length=255, blank=True, db_index=True)
    issuing_agency = models.CharField(max_length=500, blank=True)
    
    # Classification
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        db_index=True
    )
    ai_classification_confidence = models.FloatField(null=True, blank=True)  # 0.0 to 1.0
    ai_classification_date = models.DateTimeField(null=True, blank=True)
    naics_codes = models.JSONField(default=list, blank=True)  # List of NAICS codes
    
    # Contract details
    estimated_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    contract_duration = models.CharField(max_length=255, blank=True)
    
    # Important dates
    posted_date = models.DateTimeField(db_index=True)
    due_date = models.DateTimeField(null=True, blank=True, db_index=True)
    response_deadline = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    
    # Contact information
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    
    # Additional metadata
    attachments = models.JSONField(default=list, blank=True)  # List of attachment URLs
    keywords = models.JSONField(default=list, blank=True)  # Extracted keywords
    requirements = models.TextField(blank=True)
    
    # Tracking
    view_count = models.IntegerField(default=0)
    bookmark_count = models.IntegerField(default=0)
    last_scraped = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rfps'
        ordering = ['-posted_date']
        indexes = [
            models.Index(fields=['source_state', 'status', '-posted_date']),
            models.Index(fields=['category', '-posted_date']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.rfp_number}: {self.title[:50]}"
    
    @property
    def is_active(self):
        """Check if RFP is still active (not expired)."""
        if self.status != 'active':
            return False
        if self.due_date and self.due_date < timezone.now():
            return False
        return True
    
    @property
    def days_until_due(self):
        """Calculate days remaining until due date."""
        if not self.due_date:
            return None
        delta = self.due_date - timezone.now()
        return max(0, delta.days)
    
    def increment_view_count(self):
        """Increment view counter."""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class SavedRFP(models.Model):
    """
    User bookmarks for RFPs.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_rfps')
    rfp = models.ForeignKey(RFP, on_delete=models.CASCADE, related_name='saved_by_users')
    
    # User notes
    notes = models.TextField(blank=True)
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low Priority'),
            ('medium', 'Medium Priority'),
            ('high', 'High Priority'),
            ('urgent', 'Urgent'),
        ],
        default='medium'
    )
    
    # Status tracking
    application_status = models.CharField(
        max_length=50,
        choices=[
            ('saved', 'Saved for Later'),
            ('reviewing', 'Under Review'),
            ('preparing', 'Preparing Bid'),
            ('submitted', 'Bid Submitted'),
            ('won', 'Contract Won'),
            ('lost', 'Did Not Win'),
        ],
        default='saved'
    )
    
    saved_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'saved_rfps'
        unique_together = ['user', 'rfp']
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.rfp.rfp_number}"


class RFPActivity(models.Model):
    """
    Track user activity on RFPs (views, clicks, etc.).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rfp_activities')
    rfp = models.ForeignKey(RFP, on_delete=models.CASCADE, related_name='activities')
    
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('view', 'Viewed'),
            ('click', 'Clicked Link'),
            ('download', 'Downloaded Attachment'),
            ('save', 'Bookmarked'),
            ('unsave', 'Removed Bookmark'),
        ]
    )
    
    # Additional context
    metadata = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'rfp_activities'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['rfp', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.activity_type} {self.rfp.rfp_number}"
