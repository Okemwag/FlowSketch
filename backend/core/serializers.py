from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (CanonicalModel, DiagramEdge, DiagramNode, Entity, Project,
                     Relationship, Specification)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class EntitySerializer(serializers.ModelSerializer):
    """Serializer for Entity model."""
    class Meta:
        model = Entity
        fields = [
            'id', 'project', 'name', 'type', 'properties', 
            'position_x', 'position_y', 'metadata', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RelationshipSerializer(serializers.ModelSerializer):
    """Serializer for Relationship model."""
    source_name = serializers.CharField(source='source.name', read_only=True)
    target_name = serializers.CharField(source='target.name', read_only=True)
    
    class Meta:
        model = Relationship
        fields = [
            'id', 'project', 'source', 'target', 'source_name', 'target_name',
            'type', 'label', 'properties', 'metadata', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'source_name', 'target_name']


class DiagramNodeSerializer(serializers.ModelSerializer):
    """Serializer for DiagramNode model."""
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    entity_type = serializers.CharField(source='entity.type', read_only=True)
    
    class Meta:
        model = DiagramNode
        fields = [
            'id', 'entity', 'entity_name', 'entity_type',
            'position_x', 'position_y', 'width', 'height', 
            'style', 'label', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'entity_name', 'entity_type']


class DiagramEdgeSerializer(serializers.ModelSerializer):
    """Serializer for DiagramEdge model."""
    relationship_type = serializers.CharField(source='relationship.type', read_only=True)
    source_label = serializers.CharField(source='source_node.label', read_only=True)
    target_label = serializers.CharField(source='target_node.label', read_only=True)
    
    class Meta:
        model = DiagramEdge
        fields = [
            'id', 'relationship', 'relationship_type', 'source_node', 'target_node',
            'source_label', 'target_label', 'style', 'label', 'path',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'relationship_type', 
            'source_label', 'target_label'
        ]


class SpecificationSerializer(serializers.ModelSerializer):
    """Serializer for Specification model."""
    class Meta:
        model = Specification
        fields = [
            'id', 'project', 'title', 'content', 'sections', 
            'acceptance_criteria', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CanonicalModelSerializer(serializers.ModelSerializer):
    """Serializer for CanonicalModel model."""
    class Meta:
        model = CanonicalModel
        fields = [
            'id', 'project', 'entities_data', 'relationships_data', 
            'business_rules', 'version', 'last_modified'
        ]
        read_only_fields = ['id', 'last_modified']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model."""
    owner = UserSerializer(read_only=True)
    entities = EntitySerializer(many=True, read_only=True)
    relationships = RelationshipSerializer(many=True, read_only=True)
    specification = SpecificationSerializer(read_only=True)
    canonical_model = CanonicalModelSerializer(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'owner', 'created_at', 'updated_at',
            'is_public', 'share_token', 'entities', 'relationships', 
            'specification', 'canonical_model'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating projects."""
    class Meta:
        model = Project
        fields = ['name', 'description', 'is_public']
        
    def create(self, validated_data):
        # Set the owner to the current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class DiagramDataSerializer(serializers.Serializer):
    """Serializer for complete diagram data including nodes and edges."""
    nodes = DiagramNodeSerializer(many=True, read_only=True)
    edges = DiagramEdgeSerializer(many=True, read_only=True)
    metadata = serializers.JSONField(default=dict)
    
    class Meta:
        fields = ['nodes', 'edges', 'metadata']


# Text Parsing Serializers

class TextParseRequestSerializer(serializers.Serializer):
    """Serializer for text parsing requests."""
    text = serializers.CharField(
        max_length=10000,
        help_text="The unstructured text to parse for entities and relationships"
    )


class ParsedEntitySerializer(serializers.Serializer):
    """Serializer for parsed entities from text parsing service."""
    name = serializers.CharField()
    type = serializers.CharField()
    properties = serializers.DictField()
    confidence = serializers.FloatField()
    start_pos = serializers.IntegerField()
    end_pos = serializers.IntegerField()


class ParsedRelationshipSerializer(serializers.Serializer):
    """Serializer for parsed relationships from text parsing service."""
    source = serializers.CharField()
    target = serializers.CharField()
    type = serializers.CharField()
    label = serializers.CharField()
    confidence = serializers.FloatField()


class ParsedContentSerializer(serializers.Serializer):
    """Serializer for parsed content response."""
    entities = ParsedEntitySerializer(many=True)
    relationships = ParsedRelationshipSerializer(many=True)
    suggested_diagram_type = serializers.CharField()
    confidence = serializers.FloatField()
    raw_text = serializers.CharField()