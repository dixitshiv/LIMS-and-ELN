from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Sample, StorageLocation
from .serializers import SampleSerializer, StorageLocationSerializer
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response

class StorageLocationViewSet(viewsets.ModelViewSet):
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer
    permission_classes = [IsAuthenticated]

class SampleViewSet(viewsets.ModelViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    permission_classes = [IsAuthenticated]
    
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