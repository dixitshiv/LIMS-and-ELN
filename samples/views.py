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
    
    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Get all samples with active alerts"""
        samples = Sample.objects.all()
        
        alerts_data = {
            'critical': [],
            'warning': [],
            'summary': {
                'expired': 0,
                'expiring_soon': 0,
                'low_quantity': 0,
                'out_of_stock': 0,
                'total_alerts': 0
            }
        }
        
        for sample in samples:
            sample_alerts = sample.get_alert_status()
            
            if sample_alerts:
                sample_data = {
                    'id': str(sample.id),
                    'sample_id': sample.sample_id,
                    'name': sample.name,
                    'sample_type': sample.sample_type,
                    'quantity': float(sample.quantity),
                    'unit': sample.unit,
                    'storage_location': sample.storage_location.name if sample.storage_location else None,
                    'alerts': sample_alerts
                }
                
                # Categorize by severity
                has_critical = any(alert['severity'] == 'critical' for alert in sample_alerts)
                if has_critical:
                    alerts_data['critical'].append(sample_data)
                else:
                    alerts_data['warning'].append(sample_data)
                
                # Update summary counts
                for alert in sample_alerts:
                    if alert['type'] == 'EXPIRED':
                        alerts_data['summary']['expired'] += 1
                    elif alert['type'] == 'EXPIRING_SOON':
                        alerts_data['summary']['expiring_soon'] += 1
                    elif alert['type'] == 'LOW_QUANTITY':
                        alerts_data['summary']['low_quantity'] += 1
                    elif alert['type'] == 'OUT_OF_STOCK':
                        alerts_data['summary']['out_of_stock'] += 1
                
                alerts_data['summary']['total_alerts'] += len(sample_alerts)
        
        return Response(alerts_data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get samples with low quantity"""
        samples = Sample.objects.all()
        low_stock_samples = []
        
        for sample in samples:
            if sample.is_low_quantity():
                low_stock_samples.append({
                    'id': str(sample.id),
                    'sample_id': sample.sample_id,
                    'name': sample.name,
                    'sample_type': sample.sample_type,
                    'quantity': float(sample.quantity),
                    'min_quantity': float(sample.min_quantity) if sample.min_quantity else None,
                    'unit': sample.unit,
                    'storage_location': sample.storage_location.name if sample.storage_location else None
                })
        
        return Response({
            'count': len(low_stock_samples),
            'samples': low_stock_samples
        })
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get expired samples"""
        samples = Sample.objects.all()
        expired_samples = []
        
        for sample in samples:
            if sample.is_expired():
                expired_samples.append({
                    'id': str(sample.id),
                    'sample_id': sample.sample_id,
                    'name': sample.name,
                    'sample_type': sample.sample_type,
                    'expiration_date': sample.expiration_date,
                    'storage_location': sample.storage_location.name if sample.storage_location else None
                })
        
        return Response({
            'count': len(expired_samples),
            'samples': expired_samples
        })
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get samples expiring within specified days (default 30)"""
        days = int(request.query_params.get('days', 30))
        samples = Sample.objects.all()
        expiring_samples = []
        
        for sample in samples:
            if sample.is_expiring_soon(days=days):
                from datetime import datetime
                days_until = (sample.expiration_date - datetime.now().date()).days
                expiring_samples.append({
                    'id': str(sample.id),
                    'sample_id': sample.sample_id,
                    'name': sample.name,
                    'sample_type': sample.sample_type,
                    'expiration_date': sample.expiration_date,
                    'days_until_expiration': days_until,
                    'storage_location': sample.storage_location.name if sample.storage_location else None
                })
        
        return Response({
            'count': len(expiring_samples),
            'days_threshold': days,
            'samples': expiring_samples
        })