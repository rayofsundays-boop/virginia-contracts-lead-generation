"""
Views for State and City Portal API.
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.states.models import StatePortal, CityPortal, VendorRegistration
from apps.states.serializers import (
    StatePortalSerializer, CityPortalSerializer, VendorRegistrationSerializer
)


class StatePortalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing state procurement portals.
    """
    queryset = StatePortal.objects.filter(is_active=True)
    serializer_class = StatePortalSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['state_code', 'is_active']
    search_fields = ['state_name', 'portal_name']
    ordering = ['state_name']
    
    @action(detail=True, methods=['get'])
    def cities(self, request, pk=None):
        """Get all cities for a specific state."""
        state_portal = self.get_object()
        cities = CityPortal.objects.filter(state_portal=state_portal, is_active=True)
        serializer = CityPortalSerializer(cities, many=True)
        return Response(serializer.data)


class CityPortalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing city procurement portals.
    """
    queryset = CityPortal.objects.filter(is_active=True)
    serializer_class = CityPortalSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['state_portal__state_code', 'is_verified', 'discovered_by_ai']
    search_fields = ['city_name', 'portal_name', 'county_name']
    ordering = ['city_name']


class VendorRegistrationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing vendor registrations.
    """
    serializer_class = VendorRegistrationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['registration_status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only return current user's registrations."""
        return VendorRegistration.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set user when creating registration."""
        serializer.save(user=self.request.user)
