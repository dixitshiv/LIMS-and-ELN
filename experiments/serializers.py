from rest_framework import serializers
from .models import Experiment
from .file_serializers import FileAttachmentSerializer
from samples.serializers import SampleSerializer

class ExperimentSerializer(serializers.ModelSerializer):
    samples = SampleSerializer(many=True, read_only=True)
    sample_ids = serializers.ListField(
        child=serializers.UUIDField(), 
        write_only=True, 
        required=False
    )
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    attachments = FileAttachmentSerializer(many=True, read_only=True)
    attachment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Experiment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_attachment_count(self, obj):
        """Return count of file attachments"""
        return obj.attachments.count()
    
    def create(self, validated_data):
        sample_ids = validated_data.pop('sample_ids', [])
        experiment = Experiment.objects.create(**validated_data)
        if sample_ids:
            experiment.samples.set(sample_ids)
        return experiment
    
    def update(self, instance, validated_data):
        sample_ids = validated_data.pop('sample_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if sample_ids is not None:
            instance.samples.set(sample_ids)
        
        return instance


class ExperimentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    sample_count = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Experiment
        fields = ['id', 'title', 'description', 'status', 'start_date', 'end_date', 
                  'created_by_name', 'sample_count', 'attachment_count', 'created_at', 'updated_at']
    
    def get_sample_count(self, obj):
        return obj.samples.count()
    
    def get_attachment_count(self, obj):
        return obj.attachments.count()