from rest_framework import serializers
from .models import Protocol, ProtocolCategory

class ProtocolCategorySerializer(serializers.ModelSerializer):
    protocol_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProtocolCategory
        fields = '__all__'
    
    def get_protocol_count(self, obj):
        """Return count of protocols in this category"""
        return obj.protocols.filter(is_active=True).count()


class ProtocolListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for protocol list views"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = Protocol
        fields = ['id', 'protocol_code', 'title', 'description', 'status', 'version', 
                  'is_active', 'category_name', 'category_color', 'created_by_name', 
                  'approved_by_name', 'times_used', 'created_at', 'updated_at']


class ProtocolDetailSerializer(serializers.ModelSerializer):
    """Full serializer with all protocol content"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    parent_protocol_code = serializers.CharField(source='parent_protocol.protocol_code', read_only=True)
    version_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Protocol
        fields = '__all__'
        read_only_fields = ('protocol_code', 'created_at', 'updated_at', 'times_used', 'approved_at')
    
    def get_version_count(self, obj):
        """Return total number of versions"""
        return obj.get_all_versions().count()


class ProtocolCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new protocols"""
    
    class Meta:
        model = Protocol
        fields = ['title', 'category', 'description', 'objective', 'materials', 
                  'procedure', 'safety_notes', 'troubleshooting', 'references', 'notes']
    
    def create(self, validated_data):
        # Set created_by from request context
        validated_data['created_by'] = self.context['request'].user
        validated_data['status'] = 'DRAFT'
        validated_data['is_active'] = True
        validated_data['version'] = 1
        return super().create(validated_data)


class ProtocolVersionSerializer(serializers.ModelSerializer):
    """Simplified serializer for version history"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = Protocol
        fields = ['id', 'protocol_code', 'version', 'status', 'is_active', 
                  'created_by_name', 'approved_by_name', 'created_at', 'updated_at']