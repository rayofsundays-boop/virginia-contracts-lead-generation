"""
State and City Portal API serializers.
"""
from rest_framework import serializers
from apps.states.models import StatePortal, CityPortal, VendorRegistration


class StatePortalSerializer(serializers.ModelSerializer):
    """Serializer for state portals."""
    
    class Meta:
        model = StatePortal
        fields = [
            'id', 'state_code', 'state_name', 'portal_name', 'portal_url',
            'registration_url', 'search_url', 'is_active',
            'total_rfps_found', 'last_scraped', 'notes', 'contact_info'
        ]


class CityPortalSerializer(serializers.ModelSerializer):
    """Serializer for city portals."""
    
    state_name = serializers.CharField(source='state_portal.state_name', read_only=True)
    state_code = serializers.CharField(source='state_portal.state_code', read_only=True)
    
    class Meta:
        model = CityPortal
        fields = [
            'id', 'city_name', 'county_name', 'state_name', 'state_code',
            'portal_name', 'portal_url', 'registration_url',
            'discovered_by_ai', 'discovery_confidence', 'is_verified',
            'total_rfps_found', 'last_scraped', 'population'
        ]


class VendorRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for vendor registrations."""
    
    portal_name = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = VendorRegistration
        fields = [
            'id', 'state_portal', 'city_portal', 'portal_name',
            'vendor_id', 'registration_status',
            'registration_date', 'approval_date', 'expiration_date', 'renewal_date',
            'certifications', 'commodity_codes', 'notes',
            'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
