"""
Serializers for User API.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.models import UserSettings

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User profile serializer."""
    
    is_subscribed = serializers.ReadOnlyField()
    days_until_subscription_expires = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'company_name', 'phone_number',
            'subscription_plan', 'is_subscription_active', 'is_subscribed',
            'subscription_start_date', 'subscription_end_date',
            'days_until_subscription_expires',
            'email_notifications_enabled', 'notification_frequency',
            'preferred_states', 'preferred_categories', 'minimum_contract_value',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['date_joined', 'last_login', 'is_subscribed', 'days_until_subscription_expires']
        extra_kwargs = {'password': {'write_only': True}}


class UserSettingsSerializer(serializers.ModelSerializer):
    """User settings serializer."""
    
    class Meta:
        model = UserSettings
        fields = [
            'id', 'exclude_keywords', 'include_keywords',
            'ai_classification_enabled', 'auto_bookmark_relevant', 'relevance_threshold',
            'dashboard_layout', 'show_expired_rfps', 'default_sort',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'company_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user
