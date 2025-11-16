"""
URL configuration for ContractLink AI backend.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

# API Router
router = routers.DefaultRouter()

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Authentication
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),
    path('api/auth/', include('apps.users.urls')),
    
    # API Endpoints
    path('api/', include(router.urls)),
    path('api/rfps/', include('apps.rfps.urls')),
    path('api/states/', include('apps.states.urls')),
    path('api/cities/', include('apps.scrapers.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/vendor-status/', include('apps.states.urls')),
    
    # API Root
    path('api/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "ContractLink AI Admin"
admin.site.site_title = "ContractLink AI"
admin.site.index_title = "Welcome to ContractLink AI Administration"
