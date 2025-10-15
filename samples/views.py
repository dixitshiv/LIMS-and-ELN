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
    
    @action(detail=True, methods=['post'])
    def create_aliquot(self, request, pk=None):
        """
        Create an aliquot from this sample
        
        Expected payload:
        {
            "name": "Aliquot name",
            "quantity": 10.5,
            "relationship_type": "ALIQUOT",
            "derivation_notes": "Notes about creation",
            "storage_location_id": 1  (optional)
        }
        """
        from decimal import Decimal
        parent_sample = self.get_object()
        
        # Validate required fields
        name = request.data.get('name')
        quantity = request.data.get('quantity')
        
        if not name:
            return Response({'error': 'Name is required'}, status=400)
        if not quantity:
            return Response({'error': 'Quantity is required'}, status=400)
        
        try:
            quantity = Decimal(str(quantity))
        except:
            return Response({'error': 'Invalid quantity format'}, status=400)
        
        # Check if parent has enough quantity
        if quantity > parent_sample.quantity:
            return Response({
                'error': f'Parent sample only has {parent_sample.quantity} {parent_sample.unit} available'
            }, status=400)
        
        # Get optional fields
        relationship_type = request.data.get('relationship_type', 'ALIQUOT')
        derivation_notes = request.data.get('derivation_notes', '')
        storage_location_id = request.data.get('storage_location_id')
        
        # Create child sample
        child_sample = Sample.objects.create(
            name=name,
            sample_type=parent_sample.sample_type,
            quantity=quantity,
            unit=parent_sample.unit,
            created_by=request.user,
            parent_sample=parent_sample,
            relationship_type=relationship_type,
            derivation_notes=derivation_notes,
            storage_location_id=storage_location_id
        )
        
        # Reduce parent quantity
        parent_sample.use_quantity(
            amount=quantity,
            changed_by=request.user,
            reason=f'Created aliquot: {child_sample.sample_id}'
        )
        
        from .serializers import SampleSerializer
        serializer = SampleSerializer(child_sample)
        
        return Response({
            'message': 'Aliquot created successfully',
            'parent_sample': {
                'id': str(parent_sample.id),
                'sample_id': parent_sample.sample_id,
                'new_quantity': float(parent_sample.quantity)
            },
            'child_sample': serializer.data
        }, status=201)
    
    @action(detail=True, methods=['post'])
    def create_derivative(self, request, pk=None):
        """
        Create a derivative sample from this sample
        
        Expected payload:
        {
            "name": "Derivative name",
            "sample_type": "DNA",
            "quantity": 5.0,
            "unit": "µg",
            "derivation_notes": "Extracted using protocol X",
            "parent_quantity_used": 10.0  (optional - how much parent was consumed),
            "storage_location_id": 1  (optional)
        }
        """
        from decimal import Decimal
        parent_sample = self.get_object()
        
        # Validate required fields
        name = request.data.get('name')
        sample_type = request.data.get('sample_type')
        quantity = request.data.get('quantity')
        unit = request.data.get('unit')
        
        if not all([name, sample_type, quantity, unit]):
            return Response({
                'error': 'name, sample_type, quantity, and unit are required'
            }, status=400)
        
        try:
            quantity = Decimal(str(quantity))
        except:
            return Response({'error': 'Invalid quantity format'}, status=400)
        
        # Handle parent quantity usage (if specified)
        parent_quantity_used = request.data.get('parent_quantity_used')
        if parent_quantity_used:
            try:
                parent_quantity_used = Decimal(str(parent_quantity_used))
                if parent_quantity_used > parent_sample.quantity:
                    return Response({
                        'error': f'Parent sample only has {parent_sample.quantity} {parent_sample.unit} available'
                    }, status=400)
            except:
                return Response({'error': 'Invalid parent_quantity_used format'}, status=400)
        
        # Get optional fields
        derivation_notes = request.data.get('derivation_notes', '')
        storage_location_id = request.data.get('storage_location_id')
        
        # Create derivative sample
        derivative_sample = Sample.objects.create(
            name=name,
            sample_type=sample_type,
            quantity=quantity,
            unit=unit,
            created_by=request.user,
            parent_sample=parent_sample,
            relationship_type='DERIVATIVE',
            derivation_notes=derivation_notes,
            storage_location_id=storage_location_id
        )
        
        # Reduce parent quantity if specified
        if parent_quantity_used:
            parent_sample.use_quantity(
                amount=parent_quantity_used,
                changed_by=request.user,
                reason=f'Used to create derivative: {derivative_sample.sample_id}'
            )
        
        from .serializers import SampleSerializer
        serializer = SampleSerializer(derivative_sample)
        
        return Response({
            'message': 'Derivative sample created successfully',
            'parent_sample': {
                'id': str(parent_sample.id),
                'sample_id': parent_sample.sample_id,
                'new_quantity': float(parent_sample.quantity)
            },
            'derivative_sample': serializer.data
        }, status=201)
    
    @action(detail=True, methods=['get'])
    def lineage(self, request, pk=None):
        """Get complete lineage (ancestry chain) for this sample"""
        sample = self.get_object()
        lineage = sample.get_lineage()
        
        from .serializers import LineageSerializer
        serializer = LineageSerializer(lineage, many=True)
        
        return Response({
            'sample_id': sample.sample_id,
            'lineage': serializer.data,
            'depth': len(lineage)
        })
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get all direct children of this sample"""
        sample = self.get_object()
        children = sample.child_samples.all()
        
        from .serializers import ChildSampleSerializer
        serializer = ChildSampleSerializer(children, many=True)
        
        return Response({
            'sample_id': sample.sample_id,
            'children_count': children.count(),
            'children': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """Get all descendants (children, grandchildren, etc.) of this sample"""
        sample = self.get_object()
        descendants = sample.get_all_descendants()
        
        from .serializers import ChildSampleSerializer
        serializer = ChildSampleSerializer(descendants, many=True)
        
        return Response({
            'sample_id': sample.sample_id,
            'descendants_count': len(descendants),
            'descendants': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def root_samples(self, request):
        """Get all samples that have no parent (root samples)"""
        root_samples = Sample.objects.filter(parent_sample__isnull=True)
        serializer = self.get_serializer(root_samples, many=True)
        
        return Response({
            'count': root_samples.count(),
            'samples': serializer.data
        })