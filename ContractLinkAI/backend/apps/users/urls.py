"""
URL configuration for User API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, register_user

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', register_user, name='register'),
]
