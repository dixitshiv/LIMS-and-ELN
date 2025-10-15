from rest_framework import serializers
from .models import Sample, StorageLocation, QuantityLog

class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = '__all__'

class SampleSerializer(serializers.ModelSerializer):
    storage_location = StorageLocationSerializer(read_only=True)
    storage_location_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    # Parent-child relationship fields
    parent_sample_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    parent_sample_info = serializers.SerializerMethodField(read_only=True)
    children_count = serializers.SerializerMethodField(read_only=True)
    is_parent = serializers.SerializerMethodField(read_only=True)
    is_child = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Sample
        fields = '__all__'
        read_only_fields = ('sample_id',)
    
    def get_parent_sample_info(self, obj):
        """Return basic info about parent sample"""
        if obj.parent_sample:
            return {
                'id': str(obj.parent_sample.id),
                'sample_id': obj.parent_sample.sample_id,
                'name': obj.parent_sample.name,
                'sample_type': obj.parent_sample.sample_type,
                'relationship_type': obj.relationship_type
            }
        return None
    
    def get_children_count(self, obj):
        """Return count of child samples"""
        return obj.child_samples.count()
    
    def get_is_parent(self, obj):
        """Return if sample has children"""
        return obj.is_parent()
    
    def get_is_child(self, obj):
        """Return if sample has a parent"""
        return obj.is_child()
    
    def create(self, validated_data):
        """Handle parent_sample_id during creation"""
        parent_sample_id = validated_data.pop('parent_sample_id', None)
        
        if parent_sample_id:
            try:
                parent = Sample.objects.get(id=parent_sample_id)
                validated_data['parent_sample'] = parent
            except Sample.DoesNotExist:
                raise serializers.ValidationError({'parent_sample_id': 'Parent sample not found'})
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Handle parent_sample_id during update"""
        parent_sample_id = validated_data.pop('parent_sample_id', None)
        
        if parent_sample_id:
            try:
                parent = Sample.objects.get(id=parent_sample_id)
                validated_data['parent_sample'] = parent
            except Sample.DoesNotExist:
                raise serializers.ValidationError({'parent_sample_id': 'Parent sample not found'})
        
        return super().update(instance, validated_data)

class LineageSerializer(serializers.ModelSerializer):
    """Simplified serializer for lineage display"""
    class Meta:
        model = Sample
        fields = ['id', 'sample_id', 'name', 'sample_type', 'relationship_type']

class ChildSampleSerializer(serializers.ModelSerializer):
    """Serializer for displaying child samples"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Sample
        fields = ['id', 'sample_id', 'name', 'sample_type', 'relationship_type', 
                  'quantity', 'unit', 'created_by_name', 'created_at']

class QuantityLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    sample_id = serializers.CharField(source='sample.sample_id', read_only=True)
    
    class Meta:
        model = QuantityLog
        fields = '__all__'
        read_only_fields = ('changed_at',)