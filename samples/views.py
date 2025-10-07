from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Sample, StorageLocation
from .serializers import SampleSerializer, StorageLocationSerializer

class StorageLocationViewSet(viewsets.ModelViewSet):
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location_type']
    search_fields = ['name', 'location_type', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class SampleViewSet(viewsets.ModelViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sample_type', 'storage_location', 'created_by']
    search_fields = ['sample_id', 'name', 'sample_type']
    ordering_fields = ['created_at', 'sample_id', 'name', 'updated_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def barcode(self, request, pk=None):
        """Generate and return barcode for sample"""
        sample = self.get_object()
        barcode_bytes = sample.generate_barcode()
    
        response = HttpResponse(barcode_bytes, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{sample.sample_id}_barcode.png"'
        return response

    @action(detail=True, methods=['get'])
    def barcode_preview(self, request, pk=None):
        """Return base64 barcode for preview"""
        sample = self.get_object()
        barcode_base64 = sample.get_barcode_base64()
        return Response({
            'sample_id': sample.sample_id,
            'barcode': f'data:image/png;base64,{barcode_base64}'
        })
    
    @action(detail=True, methods=['post'])
    def use_quantity(self, request, pk=None):
        """Use/consume quantity from sample"""
        sample = self.get_object()
        amount = request.data.get('amount')
        reason = request.data.get('reason', '')
        
        if not amount:
            return Response({'error': 'Amount is required'}, status=400)
        
        try:
            new_quantity = sample.use_quantity(amount, request.user, reason)
            return Response({
                'message': 'Quantity used successfully',
                'new_quantity': new_quantity,
                'sample_id': sample.sample_id
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'])
    def add_quantity(self, request, pk=None):
        """Add quantity to sample"""
        sample = self.get_object()
        amount = request.data.get('amount')
        reason = request.data.get('reason', '')
        
        if not amount:
            return Response({'error': 'Amount is required'}, status=400)
        
        try:
            new_quantity = sample.add_quantity(amount, request.user, reason)
            return Response({
                'message': 'Quantity added successfully',
                'new_quantity': new_quantity,
                'sample_id': sample.sample_id
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'])
    def adjust_quantity(self, request, pk=None):
        """Manually adjust sample quantity"""
        sample = self.get_object()
        amount = request.data.get('amount')
        reason = request.data.get('reason', '')
        
        if not amount:
            return Response({'error': 'Amount is required'}, status=400)
        
        try:
            new_quantity = sample.adjust_quantity(amount, request.user, reason)
            return Response({
                'message': 'Quantity adjusted successfully',
                'new_quantity': new_quantity,
                'sample_id': sample.sample_id
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['get'])
    def quantity_history(self, request, pk=None):
        """Get quantity change history for a sample"""
        from .serializers import QuantityLogSerializer
        sample = self.get_object()
        logs = sample.quantity_logs.all()
        serializer = QuantityLogSerializer(logs, many=True)
        return Response({
            'sample_id': sample.sample_id,
            'current_quantity': sample.quantity,
            'unit': sample.unit,
            'history': serializer.data
        })