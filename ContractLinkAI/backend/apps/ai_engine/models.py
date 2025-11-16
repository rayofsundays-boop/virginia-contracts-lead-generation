"""
AI Engine models for ContractLink AI.
Track AI classification results and confidence scores.
"""
from django.db import models
from apps.rfps.models import RFP


class AIClassification(models.Model):
    """
    Track AI classification results for RFPs.
    """
    rfp = models.ForeignKey(RFP, on_delete=models.CASCADE, related_name='ai_classifications')
    
    # Classification results
    predicted_category = models.CharField(max_length=50)
    confidence_score = models.FloatField()  # 0.0 to 1.0
    
    # Multi-label predictions (top 3)
    top_predictions = models.JSONField(default=list)  # [{'category': 'janitorial', 'confidence': 0.85}, ...]
    
    # Explanation
    reasoning = models.TextField(blank=True)
    extracted_keywords = models.JSONField(default=list)
    
    # Model information
    model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50, blank=True)
    
    # Processing details
    processing_time_ms = models.IntegerField(null=True, blank=True)
    tokens_used = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_classifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rfp', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.rfp.rfp_number} - {self.predicted_category} ({self.confidence_score:.2f})"


class AIPortalDiscovery(models.Model):
    """
    Track AI-discovered city procurement portals.
    """
    # Location
    city_name = models.CharField(max_length=255)
    state_code = models.CharField(max_length=2)
    
    # Discovery results
    portal_url = models.URLField(max_length=500, blank=True)
    portal_name = models.CharField(max_length=255, blank=True)
    confidence_score = models.FloatField()  # 0.0 to 1.0
    
    # AI reasoning
    reasoning = models.TextField(blank=True)
    search_queries_used = models.JSONField(default=list)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.CharField(max_length=100, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Processing details
    model_name = models.CharField(max_length=100)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_portal_discoveries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state_code', 'city_name']),
            models.Index(fields=['is_verified', '-confidence_score']),
        ]
    
    def __str__(self):
        return f"{self.city_name}, {self.state_code} - {self.portal_name or 'Unknown'}"
