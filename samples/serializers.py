from rest_framework import serializers
from .models import Sample, StorageLocation
from .models import Sample, StorageLocation, QuantityLog

class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = '__all__'

class SampleSerializer(serializers.ModelSerializer):
    storage_location = StorageLocationSerializer(read_only=True)
    storage_location_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Sample
        fields = '__all__'
        read_only_fields = ('sample_id',)

class QuantityLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    sample_id = serializers.CharField(source='sample.sample_id', read_only=True)
    
    class Meta:
        model = QuantityLog
        fields = '__all__'
        read_only_fields = ('changed_at',)