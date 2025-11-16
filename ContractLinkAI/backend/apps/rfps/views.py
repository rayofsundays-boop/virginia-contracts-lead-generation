"""
Views for RFP API.
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from apps.rfps.models import RFP, SavedRFP, RFPActivity
from apps.rfps.serializers import (
    RFPSerializer, RFPListSerializer, SavedRFPSerializer, RFPActivitySerializer
)


class RFPViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing RFPs.
    Supports filtering by state, category, status, and search.
    """
    queryset = RFP.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source_state', 'source_city', 'category', 'status', 'source_type']
    search_fields = ['title', 'description', 'rfp_number', 'issuing_agency', 'keywords']
    ordering_fields = ['posted_date', 'due_date', 'estimated_value', 'view_count']
    ordering = ['-posted_date']
    
    def get_serializer_class(self):
        """Use lightweight serializer for list views."""
        if self.action == 'list':
            return RFPListSerializer
        return RFPSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Filter by user's preferred states
        if self.request.user.is_authenticated:
            user = self.request.user
            if user.preferred_states:
                states_filter = self.request.query_params.get('my_states', 'false')
                if states_filter.lower() == 'true':
                    queryset = queryset.filter(source_state__in=user.preferred_states)
            
            # Filter by minimum contract value
            if user.minimum_contract_value:
                queryset = queryset.filter(
                    Q(estimated_value__gte=user.minimum_contract_value) |
                    Q(estimated_value__isnull=True)
                )
        
        # Filter by active status
        active_only = self.request.query_params.get('active_only', 'false')
        if active_only.lower() == 'true':
            queryset = queryset.filter(status='active')
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Track view activity when user views RFP detail."""
        instance = self.get_object()
        instance.increment_view_count()
        
        # Track user activity
        if request.user.is_authenticated:
            RFPActivity.objects.create(
                user=request.user,
                rfp=instance,
                activity_type='view'
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_bookmarks(self, request):
        """Get user's bookmarked RFPs."""
        saved_rfps = SavedRFP.objects.filter(user=request.user).select_related('rfp')
        serializer = SavedRFPSerializer(saved_rfps, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):
        """Bookmark/save an RFP."""
        rfp = self.get_object()
        saved_rfp, created = SavedRFP.objects.get_or_create(
            user=request.user,
            rfp=rfp,
            defaults={
                'notes': request.data.get('notes', ''),
                'priority': request.data.get('priority', 'medium')
            }
        )
        
        if created:
            # Increment bookmark count
            rfp.bookmark_count += 1
            rfp.save(update_fields=['bookmark_count'])
            
            # Track activity
            RFPActivity.objects.create(
                user=request.user,
                rfp=rfp,
                activity_type='save'
            )
            
            return Response({'message': 'RFP bookmarked successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'RFP already bookmarked'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unbookmark(self, request, pk=None):
        """Remove bookmark from an RFP."""
        rfp = self.get_object()
        deleted_count, _ = SavedRFP.objects.filter(user=request.user, rfp=rfp).delete()
        
        if deleted_count > 0:
            # Decrement bookmark count
            rfp.bookmark_count = max(0, rfp.bookmark_count - 1)
            rfp.save(update_fields=['bookmark_count'])
            
            # Track activity
            RFPActivity.objects.create(
                user=request.user,
                rfp=rfp,
                activity_type='unsave'
            )
            
            return Response({'message': 'Bookmark removed successfully'})
        else:
            return Response({'message': 'RFP was not bookmarked'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get RFP statistics."""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total': queryset.count(),
            'active': queryset.filter(status='active').count(),
            'by_state': {},
            'by_category': {},
        }
        
        # Count by state
        for state_count in queryset.values('source_state').distinct():
            state_code = state_count['source_state']
            count = queryset.filter(source_state=state_code).count()
            stats['by_state'][state_code] = count
        
        # Count by category
        for category_count in queryset.values('category').distinct():
            category = category_count['category']
            count = queryset.filter(category=category).count()
            stats['by_category'][category] = count
        
        return Response(stats)


class SavedRFPViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing saved/bookmarked RFPs.
    """
    serializer_class = SavedRFPSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only return current user's saved RFPs."""
        return SavedRFP.objects.filter(user=self.request.user).select_related('rfp')
    
    def perform_create(self, serializer):
        """Set user when creating saved RFP."""
        serializer.save(user=self.request.user)
