"""
Admin configuration for State models.
"""
from django.contrib import admin
from apps.states.models import StatePortal, CityPortal, VendorRegistration


@admin.register(StatePortal)
class StatePortalAdmin(admin.ModelAdmin):
    list_display = ['state_code', 'state_name', 'portal_name', 'is_active', 'total_rfps_found', 'last_scraped']
    list_filter = ['is_active', 'scraper_type']
    search_fields = ['state_name', 'portal_name']
    ordering = ['state_code']


@admin.register(CityPortal)
class CityPortalAdmin(admin.ModelAdmin):
    list_display = ['city_name', 'state_portal', 'portal_name', 'is_verified', 'is_active', 'total_rfps_found']
    list_filter = ['is_verified', 'is_active', 'discovered_by_ai', 'state_portal__state_code']
    search_fields = ['city_name', 'portal_name', 'county_name']
    ordering = ['state_portal', 'city_name']


@admin.register(VendorRegistration)
class VendorRegistrationAdmin(admin.ModelAdmin):
    list_display = ['user', 'portal_name', 'registration_status', 'registration_date', 'expiration_date']
    list_filter = ['registration_status']
    search_fields = ['user__username', 'user__email', 'vendor_id']
    date_hierarchy = 'registration_date'
