"""
URL configuration for RFP API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.rfps.views import RFPViewSet, SavedRFPViewSet

router = DefaultRouter()
router.register(r'', RFPViewSet, basename='rfp')
router.register(r'saved', SavedRFPViewSet, basename='saved-rfp')

urlpatterns = [
    path('', include(router.urls)),
]
