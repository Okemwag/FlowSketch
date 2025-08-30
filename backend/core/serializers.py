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
    diagram_type_suggestions = serializers.DictField(
        child=serializers.FloatField(),
        help_text="Confidence scores for each diagram type"
    )
    confidence = serializers.FloatField()
    raw_text = serializers.CharField()


# Diagram Generation Serializers

class PositionSerializer(serializers.Serializer):
    """Serializer for node positions."""
    x = serializers.FloatField()
    y = serializers.FloatField()


class DiagramNodeDataSerializer(serializers.Serializer):
    """Serializer for diagram node data from engine."""
    id = serializers.CharField()
    label = serializers.CharField()
    shape = serializers.CharField()
    entity_type = serializers.CharField()
    properties = serializers.DictField()
    position = PositionSerializer(allow_null=True, required=False)


class DiagramEdgeDataSerializer(serializers.Serializer):
    """Serializer for diagram edge data from engine."""
    source_id = serializers.CharField()
    target_id = serializers.CharField()
    label = serializers.CharField()
    arrow_type = serializers.CharField()
    relationship_type = serializers.CharField()


class ValidationIssueSerializer(serializers.Serializer):
    """Serializer for validation issues."""
    severity = serializers.CharField()
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False, allow_null=True)
    suggested_fix = serializers.CharField(required=False, allow_null=True)


class ValidationResultSerializer(serializers.Serializer):
    """Serializer for validation results."""
    is_valid = serializers.BooleanField()
    error_count = serializers.IntegerField()
    warning_count = serializers.IntegerField()
    issues = ValidationIssueSerializer(many=True)
    metadata = serializers.DictField()


class GeneratedDiagramSerializer(serializers.Serializer):
    """Serializer for generated diagram data."""
    diagram_type = serializers.CharField()
    mermaid_syntax = serializers.CharField()
    nodes = DiagramNodeDataSerializer(many=True)
    edges = DiagramEdgeDataSerializer(many=True)
    layout_config = serializers.DictField()
    metadata = serializers.DictField()


class DiagramGenerationRequestSerializer(serializers.Serializer):
    """Serializer for diagram generation requests."""
    text = serializers.CharField(
        max_length=10000,
        help_text="The unstructured text to convert into a diagram"
    )
    diagram_type = serializers.CharField(
        required=False,
        help_text="Optional: Force a specific diagram type (flowchart, erd, sequence, class, process)"
    )


class DiagramErrorResponseSerializer(serializers.Serializer):
    """Serializer for diagram generation error responses."""
    error = serializers.CharField()
    error_type = serializers.CharField()
    stage = serializers.CharField(required=False)
    details = serializers.DictField(required=False)
    validation_details = ValidationResultSerializer(required=False)


# Specification Generation Serializers

class AcceptanceCriterionSerializer(serializers.Serializer):
    """Serializer for acceptance criteria."""
    id = serializers.CharField()
    description = serializers.CharField()
    priority = serializers.CharField()
    category = serializers.CharField()
    related_entities = serializers.ListField(child=serializers.CharField())
    test_scenarios = serializers.ListField(child=serializers.CharField())


class SpecSectionSerializer(serializers.Serializer):
    """Serializer for specification sections."""
    title = serializers.CharField()
    content = serializers.CharField()
    section_type = serializers.CharField()
    order = serializers.IntegerField()


class GeneratedSpecificationSerializer(serializers.Serializer):
    """Serializer for generated specification data."""
    title = serializers.CharField()
    sections = SpecSectionSerializer(many=True)
    acceptance_criteria = AcceptanceCriterionSerializer(many=True)
    metadata = serializers.DictField()
    markdown_content = serializers.CharField()


class TestCaseSerializer(serializers.Serializer):
    """Serializer for test cases."""
    name = serializers.CharField()
    description = serializers.CharField()
    test_type = serializers.CharField()
    setup_code = serializers.CharField()
    test_code = serializers.CharField()
    teardown_code = serializers.CharField()
    assertions = serializers.ListField(child=serializers.CharField())
    related_acceptance_criteria = serializers.ListField(child=serializers.CharField())


class TestFileSerializer(serializers.Serializer):
    """Serializer for test files."""
    filename = serializers.CharField()
    language = serializers.CharField()
    imports = serializers.ListField(child=serializers.CharField())
    setup_code = serializers.CharField()
    test_cases = TestCaseSerializer(many=True)
    helper_methods = serializers.ListField(child=serializers.CharField())
    full_content = serializers.CharField()


class TestScaffoldSerializer(serializers.Serializer):
    """Serializer for test scaffolds."""
    language = serializers.CharField()
    test_files = TestFileSerializer(many=True)
    setup_instructions = serializers.CharField()
    run_instructions = serializers.CharField()
    dependencies = serializers.ListField(child=serializers.CharField())
    metadata = serializers.DictField()


class GeneratedSpecificationSerializer(serializers.Serializer):
    """Serializer for generated specification data."""
    title = serializers.CharField()
    sections = SpecSectionSerializer(many=True)
    acceptance_criteria = AcceptanceCriterionSerializer(many=True)
    metadata = serializers.DictField()
    markdown_content = serializers.CharField()
    test_scaffold = TestScaffoldSerializer(required=False, allow_null=True)


class SpecificationGenerationRequestSerializer(serializers.Serializer):
    """Serializer for specification generation requests."""
    text = serializers.CharField(
        max_length=10000,
        help_text="The unstructured text to convert into a specification"
    )
    project_name = serializers.CharField(
        max_length=255,
        default="System",
        help_text="Name of the project for the specification title"
    )
    diagram_type = serializers.CharField(
        required=False,
        help_text="Optional: Force a specific diagram type (flowchart, erd, sequence, class, process)"
    )
    include_tests = serializers.BooleanField(
        default=True,
        help_text="Whether to generate test scaffolds"
    )
    test_language = serializers.CharField(
        default="python",
        help_text="Programming language for test generation (python, javascript, java, etc.)"
    )