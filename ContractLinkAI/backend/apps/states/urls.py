"""
URL configuration for States API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.states.views import StatePortalViewSet, CityPortalViewSet, VendorRegistrationViewSet

router = DefaultRouter()
router.register(r'', StatePortalViewSet, basename='state-portal')
router.register(r'cities', CityPortalViewSet, basename='city-portal')
router.register(r'vendor-registrations', VendorRegistrationViewSet, basename='vendor-registration')

urlpatterns = [
    path('', include(router.urls)),
]
