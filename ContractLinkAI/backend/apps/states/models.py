"""
State and City Portal models for ContractLink AI.
Manages procurement portal information and vendor registrations.
"""
from django.db import models
from apps.users.models import User


class StatePortal(models.Model):
    """
    State-level procurement portal information.
    """
    # Basic information
    state_code = models.CharField(max_length=2, unique=True, db_index=True)
    state_name = models.CharField(max_length=100)
    
    # Portal details
    portal_name = models.CharField(max_length=255)
    portal_url = models.URLField(max_length=500)
    registration_url = models.URLField(max_length=500, blank=True)
    search_url = models.URLField(max_length=500, blank=True)
    
    # Technical details for scraping
    scraper_type = models.CharField(
        max_length=50,
        choices=[
            ('html', 'HTML Parsing'),
            ('api', 'API Integration'),
            ('rss', 'RSS Feed'),
            ('manual', 'Manual Check'),
        ],
        default='html'
    )
    scraper_config = models.JSONField(default=dict, blank=True)  # CSS selectors, API keys, etc.
    
    # Status
    is_active = models.BooleanField(default=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    scrape_frequency_hours = models.IntegerField(default=24)  # How often to scrape
    
    # Statistics
    total_rfps_found = models.IntegerField(default=0)
    successful_scrapes = models.IntegerField(default=0)
    failed_scrapes = models.IntegerField(default=0)
    
    # Notes
    notes = models.TextField(blank=True)
    contact_info = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'state_portals'
        ordering = ['state_name']
    
    def __str__(self):
        return f"{self.state_name} ({self.state_code}) - {self.portal_name}"


class CityPortal(models.Model):
    """
    City/municipality-level procurement portal information.
    Discovered dynamically using AI.
    """
    # Location
    state_portal = models.ForeignKey(
        StatePortal,
        on_delete=models.CASCADE,
        related_name='city_portals'
    )
    city_name = models.CharField(max_length=255, db_index=True)
    county_name = models.CharField(max_length=255, blank=True)
    
    # Portal details
    portal_name = models.CharField(max_length=255)
    portal_url = models.URLField(max_length=500)
    registration_url = models.URLField(max_length=500, blank=True)
    
    # Discovery information
    discovered_by_ai = models.BooleanField(default=True)
    discovery_date = models.DateTimeField(auto_now_add=True)
    discovery_confidence = models.FloatField(null=True, blank=True)  # AI confidence 0.0-1.0
    
    # Technical details
    scraper_type = models.CharField(
        max_length=50,
        choices=[
            ('html', 'HTML Parsing'),
            ('api', 'API Integration'),
            ('pdf', 'PDF Listings'),
            ('manual', 'Manual Check'),
        ],
        default='html'
    )
    scraper_config = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)  # Manually verified by admin
    last_scraped = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_rfps_found = models.IntegerField(default=0)
    successful_scrapes = models.IntegerField(default=0)
    
    # Additional info
    population = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'city_portals'
        ordering = ['state_portal', 'city_name']
        unique_together = ['state_portal', 'city_name']
    
    def __str__(self):
        return f"{self.city_name}, {self.state_portal.state_code} - {self.portal_name}"


class VendorRegistration(models.Model):
    """
    Track user vendor registrations with state/city portals.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_registrations')
    
    # Portal reference (either state or city)
    state_portal = models.ForeignKey(
        StatePortal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vendor_registrations'
    )
    city_portal = models.ForeignKey(
        CityPortal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vendor_registrations'
    )
    
    # Registration details
    vendor_id = models.CharField(max_length=255, blank=True)
    registration_status = models.CharField(
        max_length=50,
        choices=[
            ('not_started', 'Not Started'),
            ('in_progress', 'In Progress'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('expired', 'Expired'),
        ],
        default='not_started'
    )
    
    # Important dates
    registration_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True)
    
    # Additional information
    certifications = models.JSONField(default=list, blank=True)  # Small business, minority-owned, etc.
    commodity_codes = models.JSONField(default=list, blank=True)  # What services they provide
    notes = models.TextField(blank=True)
    
    # Tracking
    last_checked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_registrations'
        ordering = ['-created_at']
    
    def __str__(self):
        portal_name = self.state_portal or self.city_portal
        return f"{self.user.username} - {portal_name}"
    
    @property
    def portal_name(self):
        """Get the portal name (state or city)."""
        if self.state_portal:
            return self.state_portal.portal_name
        elif self.city_portal:
            return self.city_portal.portal_name
        return "Unknown Portal"
    
    @property
    def is_expired(self):
        """Check if registration has expired."""
        if not self.expiration_date:
            return False
        from django.utils import timezone
        return self.expiration_date < timezone.now().date()
