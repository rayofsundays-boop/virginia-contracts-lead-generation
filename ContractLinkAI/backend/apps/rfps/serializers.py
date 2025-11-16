"""
Serializers for RFP API.
"""
from rest_framework import serializers
from apps.rfps.models import RFP, SavedRFP, RFPActivity


class RFPSerializer(serializers.ModelSerializer):
    """Main RFP serializer for list/detail views."""
    
    days_until_due = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    is_bookmarked = serializers.SerializerMethodField()
    
    class Meta:
        model = RFP
        fields = [
            'id', 'rfp_number', 'title', 'description',
            'source_url', 'source_type', 'source_state', 'source_city',
            'issuing_agency', 'category', 'ai_classification_confidence',
            'estimated_value', 'contract_duration',
            'posted_date', 'due_date', 'response_deadline',
            'status', 'contact_name', 'contact_email', 'contact_phone',
            'attachments', 'keywords', 'requirements', 'naics_codes',
            'view_count', 'bookmark_count',
            'days_until_due', 'is_active', 'is_bookmarked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['rfp_number', 'view_count', 'bookmark_count', 'created_at', 'updated_at']
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this RFP."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedRFP.objects.filter(user=request.user, rfp=obj).exists()
        return False


class RFPListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    
    days_until_due = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = RFP
        fields = [
            'id', 'rfp_number', 'title', 'source_state', 'source_city',
            'category', 'estimated_value', 'posted_date', 'due_date',
            'status', 'days_until_due', 'is_active'
        ]


class SavedRFPSerializer(serializers.ModelSerializer):
    """Serializer for saved/bookmarked RFPs."""
    
    rfp = RFPSerializer(read_only=True)
    rfp_id = serializers.PrimaryKeyRelatedField(
        queryset=RFP.objects.all(),
        source='rfp',
        write_only=True
    )
    
    class Meta:
        model = SavedRFP
        fields = [
            'id', 'rfp', 'rfp_id', 'notes', 'priority',
            'application_status', 'saved_at', 'updated_at'
        ]
        read_only_fields = ['saved_at', 'updated_at']


class RFPActivitySerializer(serializers.ModelSerializer):
    """Serializer for RFP activity tracking."""
    
    rfp_number = serializers.CharField(source='rfp.rfp_number', read_only=True)
    rfp_title = serializers.CharField(source='rfp.title', read_only=True)
    
    class Meta:
        model = RFPActivity
        fields = [
            'id', 'rfp', 'rfp_number', 'rfp_title',
            'activity_type', 'metadata', 'timestamp'
        ]
        read_only_fields = ['timestamp']
