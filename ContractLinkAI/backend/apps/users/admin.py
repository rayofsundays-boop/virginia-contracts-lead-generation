"""
Admin configuration for User models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import User, UserSettings


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'subscription_plan', 'is_subscription_active', 'date_joined']
    list_filter = ['subscription_plan', 'is_subscription_active', 'is_staff']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_start_date', 'subscription_end_date', 'is_subscription_active')
        }),
        ('Preferences', {
            'fields': ('preferred_states', 'preferred_categories', 'minimum_contract_value', 
                      'email_notifications_enabled', 'notification_frequency')
        }),
        ('Additional Info', {
            'fields': ('company_name', 'phone_number', 'last_login_ip')
        }),
    )


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'ai_classification_enabled', 'auto_bookmark_relevant', 'dashboard_layout']
    search_fields = ['user__username', 'user__email']
