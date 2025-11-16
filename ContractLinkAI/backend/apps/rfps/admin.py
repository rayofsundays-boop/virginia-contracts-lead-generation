"""
Admin configuration for RFP models.
"""
from django.contrib import admin
from apps.rfps.models import RFP, SavedRFP, RFPActivity


@admin.register(RFP)
class RFPAdmin(admin.ModelAdmin):
    list_display = ['rfp_number', 'title', 'source_state', 'category', 'status', 'posted_date', 'due_date']
    list_filter = ['status', 'category', 'source_state', 'source_type']
    search_fields = ['rfp_number', 'title', 'description', 'issuing_agency']
    readonly_fields = ['created_at', 'updated_at', 'last_scraped', 'view_count', 'bookmark_count']
    date_hierarchy = 'posted_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('rfp_number', 'title', 'description', 'status')
        }),
        ('Source', {
            'fields': ('source_url', 'source_type', 'source_state', 'source_city', 'issuing_agency')
        }),
        ('Classification', {
            'fields': ('category', 'ai_classification_confidence', 'ai_classification_date', 'naics_codes', 'keywords')
        }),
        ('Contract Details', {
            'fields': ('estimated_value', 'contract_duration', 'requirements')
        }),
        ('Dates', {
            'fields': ('posted_date', 'due_date', 'response_deadline')
        }),
        ('Contact', {
            'fields': ('contact_name', 'contact_email', 'contact_phone')
        }),
        ('Statistics', {
            'fields': ('view_count', 'bookmark_count', 'last_scraped', 'created_at', 'updated_at')
        }),
    )


@admin.register(SavedRFP)
class SavedRFPAdmin(admin.ModelAdmin):
    list_display = ['user', 'rfp', 'priority', 'application_status', 'saved_at']
    list_filter = ['priority', 'application_status']
    search_fields = ['user__username', 'user__email', 'rfp__rfp_number', 'rfp__title']
    date_hierarchy = 'saved_at'


@admin.register(RFPActivity)
class RFPActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'rfp', 'activity_type', 'timestamp']
    list_filter = ['activity_type']
    search_fields = ['user__username', 'rfp__rfp_number']
    date_hierarchy = 'timestamp'
