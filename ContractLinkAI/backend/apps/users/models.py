"""
Custom User model for ContractLink AI.
Extends Django's AbstractUser to add subscription and preferences fields.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model with subscription and notification preferences.
    """
    SUBSCRIPTION_CHOICES = [
        ('free', 'Free Trial'),
        ('basic', 'Basic Plan'),
        ('pro', 'Professional Plan'),
        ('enterprise', 'Enterprise Plan'),
    ]
    
    email = models.EmailField(unique=True)
    company_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Subscription details
    subscription_plan = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_CHOICES,
        default='free'
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    is_subscription_active = models.BooleanField(default=False)
    
    # Notification preferences
    email_notifications_enabled = models.BooleanField(default=True)
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('realtime', 'Real-time'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Summary'),
        ],
        default='daily'
    )
    
    # User preferences
    preferred_states = models.JSONField(default=list, blank=True)  # List of state codes
    preferred_categories = models.JSONField(default=list, blank=True)  # RFP categories
    minimum_contract_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    @property
    def is_subscribed(self):
        """Check if user has an active subscription."""
        if not self.is_subscription_active:
            return False
        if self.subscription_end_date and self.subscription_end_date < timezone.now():
            return False
        return True
    
    @property
    def days_until_subscription_expires(self):
        """Calculate days remaining in subscription."""
        if not self.subscription_end_date:
            return None
        delta = self.subscription_end_date - timezone.now()
        return max(0, delta.days)


class UserSettings(models.Model):
    """
    Extended user settings for advanced features.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Advanced filters
    exclude_keywords = models.JSONField(default=list, blank=True)  # Keywords to exclude
    include_keywords = models.JSONField(default=list, blank=True)  # Required keywords
    
    # AI preferences
    ai_classification_enabled = models.BooleanField(default=True)
    auto_bookmark_relevant = models.BooleanField(default=False)  # Auto-save relevant RFPs
    relevance_threshold = models.IntegerField(default=70)  # 0-100 confidence score
    
    # Dashboard preferences
    dashboard_layout = models.CharField(max_length=20, default='grid')  # grid, list, compact
    show_expired_rfps = models.BooleanField(default=False)
    default_sort = models.CharField(max_length=50, default='-posted_date')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_settings'
    
    def __str__(self):
        return f"Settings for {self.user.username}"
