"""
Scraper models for ContractLink AI.
Track scraping jobs and errors.
"""
from django.db import models


class ScrapeJob(models.Model):
    """
    Track individual scraping jobs.
    """
    JOB_TYPE_CHOICES = [
        ('state', 'State Portal Scrape'),
        ('city', 'City Portal Scrape'),
        ('city_discovery', 'AI City Discovery'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Target information
    target_state_code = models.CharField(max_length=2, blank=True, db_index=True)
    target_city_name = models.CharField(max_length=255, blank=True)
    target_url = models.URLField(max_length=500, blank=True)
    
    # Results
    rfps_found = models.IntegerField(default=0)
    rfps_new = models.IntegerField(default=0)
    rfps_updated = models.IntegerField(default=0)
    
    # Execution details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Metadata
    celery_task_id = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'scrape_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['job_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.job_type} - {self.status} ({self.created_at})"


class ScrapeError(models.Model):
    """
    Track scraping errors for debugging and monitoring.
    """
    scrape_job = models.ForeignKey(
        ScrapeJob,
        on_delete=models.CASCADE,
        related_name='errors',
        null=True,
        blank=True
    )
    
    # Error details
    error_type = models.CharField(max_length=255)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True)
    
    # Context
    target_url = models.URLField(max_length=500, blank=True)
    http_status_code = models.IntegerField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'scrape_errors'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.error_type} at {self.timestamp}"
