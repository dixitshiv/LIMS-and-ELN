from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Protocol, ProtocolCategory
from .serializers import (
    ProtocolCategorySerializer,
    ProtocolListSerializer,
    ProtocolDetailSerializer,
    ProtocolCreateSerializer,
    ProtocolVersionSerializer
)

class ProtocolCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProtocolCategory.objects.all()
    serializer_class = ProtocolCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ProtocolViewSet(viewsets.ModelViewSet):
    queryset = Protocol.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'is_active', 'created_by']
    search_fields = ['title', 'protocol_code', 'description', 'procedure']
    ordering_fields = ['created_at', 'updated_at', 'protocol_code', 'title', 'times_used']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return ProtocolListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProtocolCreateSerializer
        else:
            return ProtocolDetailSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a protocol"""
        protocol = self.get_object()
        
        if protocol.status == 'APPROVED':
            return Response(
                {'message': 'Protocol is already approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        protocol.approve(request.user)
        
        serializer = self.get_serializer(protocol)
        return Response({
            'message': f'Protocol {protocol.protocol_code} approved successfully',
            'protocol': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a protocol"""
        protocol = self.get_object()
        
        if protocol.status == 'ARCHIVED':
            return Response(
                {'message': 'Protocol is already archived'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        protocol.archive()
        
        serializer = self.get_serializer(protocol)
        return Response({
            'message': f'Protocol {protocol.protocol_code} archived successfully',
            'protocol': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """Create a new version of this protocol"""
        protocol = self.get_object()
        
        new_protocol = protocol.create_new_version(request.user)
        
        serializer = self.get_serializer(new_protocol)
        return Response({
            'message': f'New version created: {new_protocol.protocol_code} v{new_protocol.version}',
            'protocol': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone this protocol as a new independent protocol"""
        protocol = self.get_object()
        new_title = request.data.get('title')
        
        if not new_title:
            return Response(
                {'error': 'title is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_protocol = protocol.clone_for_new_protocol(new_title, request.user)
        
        serializer = self.get_serializer(new_protocol)
        return Response({
            'message': f'Protocol cloned successfully as {new_protocol.protocol_code}',
            'protocol': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get all versions of this protocol"""
        protocol = self.get_object()
        versions = protocol.get_all_versions()
        
        serializer = ProtocolVersionSerializer(versions, many=True)
        return Response({
            'protocol_code': protocol.protocol_code,
            'version_count': versions.count(),
            'versions': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active protocols"""
        active_protocols = Protocol.objects.filter(is_active=True)
        
        # Apply filters
        filtered = self.filter_queryset(active_protocols)
        
        page = self.paginate_queryset(filtered)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(filtered, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def approved(self, request):
        """Get only approved protocols"""
        approved_protocols = Protocol.objects.filter(status='APPROVED', is_active=True)
        
        # Apply filters
        filtered = self.filter_queryset(approved_protocols)
        
        page = self.paginate_queryset(filtered)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(filtered, many=True)
        return Response(serializer.data)