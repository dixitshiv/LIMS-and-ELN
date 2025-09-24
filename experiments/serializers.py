from rest_framework import serializers
from .models import Experiment
from samples.serializers import SampleSerializer

class ExperimentSerializer(serializers.ModelSerializer):
    samples = SampleSerializer(many=True, read_only=True)
    sample_ids = serializers.ListField(
        child=serializers.UUIDField(), 
        write_only=True, 
        required=False
    )
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Experiment
        fields = '__all__'
        
    def create(self, validated_data):
        sample_ids = validated_data.pop('sample_ids', [])
        experiment = Experiment.objects.create(**validated_data)
        if sample_ids:
            experiment.samples.set(sample_ids)
        return experiment