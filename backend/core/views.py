from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema, extend_schema_view)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (CanonicalModel, DiagramEdge, DiagramNode, Entity, Project,
                     Relationship, Specification)
from .serializers import (CanonicalModelSerializer, DiagramDataSerializer,
                          DiagramEdgeSerializer,
                          DiagramErrorResponseSerializer,
                          DiagramGenerationRequestSerializer,
                          DiagramNodeSerializer, EntitySerializer,
                          GeneratedDiagramSerializer,
                          GeneratedSpecificationSerializer,
                          ParsedContentSerializer, ProjectCreateSerializer,
                          ProjectSerializer, RelationshipSerializer,
                          SpecificationGenerationRequestSerializer,
                          SpecificationSerializer, TextParseRequestSerializer)
from .services.diagram_engine import (DiagramEngine, DiagramGenerationError,
                                      DiagramValidationError)
from .services.specification_generator import (SpecificationGenerationError,
                                               SpecificationGenerator)
from .services.text_parser import DiagramType, TextParserService


@extend_schema_view(
    list=extend_schema(
        summary="List projects",
        description="Retrieve a list of projects owned by the authenticated user.",
        tags=["Projects"],
    ),
    create=extend_schema(
        summary="Create project",
        description="Create a new project for the authenticated user.",
        tags=["Projects"],
    ),
    retrieve=extend_schema(
        summary="Get project",
        description="Retrieve a specific project by ID.",
        tags=["Projects"],
    ),
    update=extend_schema(
        summary="Update project",
        description="Update a project's details.",
        tags=["Projects"],
    ),
    partial_update=extend_schema(
        summary="Partially update project",
        description="Partially update a project's details.",
        tags=["Projects"],
    ),
    destroy=extend_schema(
        summary="Delete project",
        description="Delete a project and all associated data.",
        tags=["Projects"],
    ),
)
class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for managing projects."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        return ProjectSerializer

    @extend_schema(
        summary="Get project diagram",
        description="Retrieve the complete diagram data (nodes and edges) for a project.",
        responses={200: DiagramDataSerializer},
        tags=["Projects", "Diagrams"],
    )
    @action(detail=True, methods=["get"])
    def diagram(self, request, pk=None):
        """Get diagram data for a project."""
        project = self.get_object()
        nodes = DiagramNode.objects.filter(entity__project=project)
        edges = DiagramEdge.objects.filter(relationship__project=project)

        data = {
            "nodes": DiagramNodeSerializer(nodes, many=True).data,
            "edges": DiagramEdgeSerializer(edges, many=True).data,
            "metadata": {},
        }
        return Response(data)

    @extend_schema(
        summary="Get project specification",
        description="Retrieve the generated specification document for a project.",
        responses={200: SpecificationSerializer, 404: OpenApiTypes.OBJECT},
        tags=["Projects", "Specifications"],
    )
    @action(detail=True, methods=["get"])
    def specification(self, request, pk=None):
        """Get specification for a project."""
        project = self.get_object()
        try:
            spec = project.specification
            serializer = SpecificationSerializer(spec)
            return Response(serializer.data)
        except Specification.DoesNotExist:
            return Response(
                {"detail": "Specification not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        summary="Parse text for entities and relationships",
        description="Parse unstructured text using NLP to extract entities, relationships, and suggest appropriate diagram types.",
        request=TextParseRequestSerializer,
        responses={
            200: ParsedContentSerializer,
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Simple business process",
                summary="Parse a simple business process description",
                description="Example of parsing a basic user workflow",
                value={
                    "text": "User creates an order and the system validates payment information. The order is then sent to the fulfillment service."
                },
                request_only=True,
            ),
            OpenApiExample(
                "Database schema description",
                summary="Parse database schema text",
                description="Example of parsing database-related text",
                value={
                    "text": "The user table contains user information and has a relationship with the order table. Each order belongs to a user."
                },
                request_only=True,
            ),
        ],
        tags=["Projects", "Text Parsing", "AI"],
    )
    @action(detail=True, methods=["post"])
    def parse_text(self, request, pk=None):
        """Parse unstructured text to extract entities and relationships."""
        project = self.get_object()

        # Validate input
        serializer = TextParseRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        text = serializer.validated_data["text"]

        try:
            # Initialize text parser service
            parser_service = TextParserService()

            # Parse the text
            parsed_content = parser_service.parse_text(text)

            # Serialize the response
            response_serializer = ParsedContentSerializer(
                {
                    "entities": [
                        {
                            "name": entity.name,
                            "type": entity.type.value,
                            "properties": entity.properties,
                            "confidence": entity.confidence,
                            "start_pos": entity.start_pos,
                            "end_pos": entity.end_pos,
                        }
                        for entity in parsed_content.entities
                    ],
                    "relationships": [
                        {
                            "source": rel.source,
                            "target": rel.target,
                            "type": rel.type,
                            "label": rel.label,
                            "confidence": rel.confidence,
                        }
                        for rel in parsed_content.relationships
                    ],
                    "suggested_diagram_type": parsed_content.suggested_diagram_type.value,
                    "diagram_type_suggestions": parsed_content.diagram_type_suggestions,
                    "confidence": parsed_content.confidence,
                    "raw_text": parsed_content.raw_text,
                }
            )

            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except RuntimeError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"error": "An error occurred while parsing the text"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Generate diagram from text",
        description="Parse unstructured text and generate a complete Mermaid diagram with auto-layout positioning.",
        request=DiagramGenerationRequestSerializer,
        responses={
            200: GeneratedDiagramSerializer,
            400: OpenApiTypes.OBJECT,
            422: "DiagramErrorResponseSerializer",
            500: "DiagramErrorResponseSerializer",
        },
        examples=[
            OpenApiExample(
                "User workflow",
                summary="Generate flowchart from user workflow",
                description="Example of generating a flowchart from user workflow description",
                value={
                    "text": "User logs into the system, creates an order, and the payment service processes the payment. The order is then sent to fulfillment."
                },
                request_only=True,
            ),
            OpenApiExample(
                "Database schema",
                summary="Generate ERD from database description",
                description="Example of generating an ERD from database schema description",
                value={
                    "text": "User table has many orders. Each order belongs to one user and contains multiple order items. Products are referenced by order items.",
                    "diagram_type": "erd",
                },
                request_only=True,
            ),
        ],
        tags=["Projects", "Diagrams", "AI"],
    )
    @action(detail=True, methods=["post"])
    def generate_diagram(self, request, pk=None):
        """Generate a complete diagram from unstructured text."""
        project = self.get_object()

        # Validate input
        serializer = DiagramGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        text = serializer.validated_data["text"]
        forced_diagram_type = serializer.validated_data.get("diagram_type")

        try:
            # Initialize services
            parser_service = TextParserService()
            diagram_engine = DiagramEngine()

            # Parse the text
            parsed_content = parser_service.parse_text(text)

            # Override diagram type if specified
            if forced_diagram_type:
                try:
                    parsed_content.suggested_diagram_type = DiagramType(
                        forced_diagram_type.lower()
                    )
                except ValueError:
                    return Response(
                        {
                            "error": f"Invalid diagram type: {forced_diagram_type}. Valid types: flowchart, erd, sequence, class, process"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Generate the diagram
            diagram_data = diagram_engine.generate_diagram(parsed_content)

            # Get comprehensive validation results
            validation_result = diagram_engine.validate_diagram_comprehensive(
                diagram_data
            )

            # Serialize the response
            response_data = {
                "diagram_type": diagram_data.diagram_type.value,
                "mermaid_syntax": diagram_data.mermaid_syntax,
                "nodes": [
                    {
                        "id": node.id,
                        "label": node.label,
                        "shape": node.shape,
                        "entity_type": node.entity_type,
                        "properties": node.properties,
                        "position": (
                            {"x": node.position.x, "y": node.position.y}
                            if node.position
                            else None
                        ),
                    }
                    for node in diagram_data.nodes
                ],
                "edges": [
                    {
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "label": edge.label,
                        "arrow_type": edge.arrow_type,
                        "relationship_type": edge.relationship_type,
                    }
                    for edge in diagram_data.edges
                ],
                "layout_config": diagram_data.layout_config,
                "metadata": {
                    **diagram_data.metadata,
                    "validation": {
                        "is_valid": validation_result.is_valid,
                        "error_count": len(validation_result.issues),
                        "warning_count": len(validation_result.warnings),
                        "issues": [
                            {
                                "severity": issue.severity.value,
                                "code": issue.code,
                                "message": issue.message,
                                "details": issue.details,
                                "suggested_fix": issue.suggested_fix,
                            }
                            for issue in validation_result.issues
                            + validation_result.warnings
                        ],
                        "metadata": validation_result.metadata,
                    },
                },
            }

            response_serializer = GeneratedDiagramSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except DiagramValidationError as e:
            return Response(
                {
                    "error": str(e),
                    "error_type": "validation_error",
                    "validation_details": {
                        "is_valid": e.validation_result.is_valid,
                        "issues": [
                            {
                                "severity": issue.severity.value,
                                "code": issue.code,
                                "message": issue.message,
                                "details": issue.details,
                                "suggested_fix": issue.suggested_fix,
                            }
                            for issue in e.validation_result.issues
                        ],
                    },
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except DiagramGenerationError as e:
            return Response(
                {
                    "error": str(e),
                    "error_type": "generation_error",
                    "stage": e.stage,
                    "details": e.details,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except RuntimeError as e:
            return Response(
                {"error": str(e), "error_type": "runtime_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {
                    "error": "An unexpected error occurred while generating the diagram",
                    "error_type": "unknown_error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @extend_schema(
        summary="Generate specification from text",
        description="Parse unstructured text, generate a diagram, and create a comprehensive specification document with acceptance criteria.",
        request=SpecificationGenerationRequestSerializer,
        responses={
            200: GeneratedSpecificationSerializer,
            400: OpenApiTypes.OBJECT,
            422: "DiagramErrorResponseSerializer",
            500: "DiagramErrorResponseSerializer"
        },
        examples=[
            OpenApiExample(
                'User authentication flow',
                summary='Generate specification from authentication workflow',
                description='Example of generating a complete specification from user authentication description',
                value={
                    'text': 'User enters credentials, system validates against database, generates JWT token, and returns success response with user profile.',
                    'project_name': 'Authentication System'
                },
                request_only=True,
            ),
            OpenApiExample(
                'E-commerce order process',
                summary='Generate specification from order processing',
                description='Example of generating specification from e-commerce workflow',
                value={
                    'text': 'Customer adds items to cart, proceeds to checkout, payment service processes payment, inventory is updated, and order confirmation is sent.',
                    'project_name': 'E-commerce Platform',
                    'diagram_type': 'process'
                },
                request_only=True,
            ),
            OpenApiExample(
                'API with JavaScript tests',
                summary='Generate specification with JavaScript test scaffold',
                description='Example of generating specification with JavaScript/Jest test files',
                value={
                    'text': 'API receives request, validates input, processes data, and returns response.',
                    'project_name': 'REST API',
                    'include_tests': True,
                    'test_language': 'javascript'
                },
                request_only=True,
            ),
        ],
        tags=["Projects", "Specifications", "AI"]
    )
    @action(detail=True, methods=['post'])
    def generate_specification(self, request, pk=None):
        """Generate a complete specification document from unstructured text."""
        project = self.get_object()
        
        # Validate input
        serializer = SpecificationGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        text = serializer.validated_data['text']
        project_name = serializer.validated_data.get('project_name', project.name)
        forced_diagram_type = serializer.validated_data.get('diagram_type')
        include_tests = serializer.validated_data.get('include_tests', True)
        test_language_str = serializer.validated_data.get('test_language', 'python')
        
        try:
            # Initialize services
            parser_service = TextParserService()
            diagram_engine = DiagramEngine()
            spec_generator = SpecificationGenerator()
            
            # Validate test language
            try:
                from core.services.specification_generator import \
                    ProgrammingLanguage
                test_language = ProgrammingLanguage(test_language_str.lower())
            except ValueError:
                return Response(
                    {'error': f'Invalid test language: {test_language_str}. Valid languages: python, javascript, java, csharp, go, rust'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse the text
            parsed_content = parser_service.parse_text(text)
            
            # Override diagram type if specified
            if forced_diagram_type:
                try:
                    parsed_content.suggested_diagram_type = DiagramType(forced_diagram_type.lower())
                except ValueError:
                    return Response(
                        {'error': f'Invalid diagram type: {forced_diagram_type}. Valid types: flowchart, erd, sequence, class, process'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Generate the diagram
            diagram_data = diagram_engine.generate_diagram(parsed_content)
            
            # Generate the specification
            specification = spec_generator.generate_specification(
                diagram_data, 
                project_name,
                include_tests=include_tests,
                test_language=test_language
            )
            
            # Serialize the response
            response_data = {
                'title': specification.title,
                'sections': [
                    {
                        'title': section.title,
                        'content': section.content,
                        'section_type': section.section_type.value,
                        'order': section.order
                    }
                    for section in specification.sections
                ],
                'acceptance_criteria': [
                    {
                        'id': criterion.id,
                        'description': criterion.description,
                        'priority': criterion.priority,
                        'category': criterion.category,
                        'related_entities': criterion.related_entities,
                        'test_scenarios': criterion.test_scenarios
                    }
                    for criterion in specification.acceptance_criteria
                ],
                'metadata': {
                    **specification.metadata,
                    'diagram_info': {
                        'type': diagram_data.diagram_type.value,
                        'node_count': len(diagram_data.nodes),
                        'edge_count': len(diagram_data.edges)
                    }
                },
                'markdown_content': specification.markdown_content,
                'test_scaffold': {
                    'language': specification.test_scaffold.language.value,
                    'test_files': [
                        {
                            'filename': file.filename,
                            'language': file.language.value,
                            'imports': file.imports,
                            'setup_code': file.setup_code,
                            'test_cases': [
                                {
                                    'name': case.name,
                                    'description': case.description,
                                    'test_type': case.test_type.value,
                                    'setup_code': case.setup_code,
                                    'test_code': case.test_code,
                                    'teardown_code': case.teardown_code,
                                    'assertions': case.assertions,
                                    'related_acceptance_criteria': case.related_acceptance_criteria
                                }
                                for case in file.test_cases
                            ],
                            'helper_methods': file.helper_methods,
                            'full_content': file.full_content
                        }
                        for file in specification.test_scaffold.test_files
                    ],
                    'setup_instructions': specification.test_scaffold.setup_instructions,
                    'run_instructions': specification.test_scaffold.run_instructions,
                    'dependencies': specification.test_scaffold.dependencies,
                    'metadata': specification.test_scaffold.metadata
                } if specification.test_scaffold else None
            }
            
            response_serializer = GeneratedSpecificationSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except SpecificationGenerationError as e:
            return Response(
                {
                    'error': str(e),
                    'error_type': 'specification_generation_error',
                    'stage': e.stage,
                    'details': e.details
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except DiagramValidationError as e:
            return Response(
                {
                    'error': f'Diagram validation failed: {str(e)}',
                    'error_type': 'diagram_validation_error',
                    'validation_details': {
                        'is_valid': e.validation_result.is_valid,
                        'issues': [
                            {
                                'severity': issue.severity.value,
                                'code': issue.code,
                                'message': issue.message,
                                'details': issue.details,
                                'suggested_fix': issue.suggested_fix
                            }
                            for issue in e.validation_result.issues
                        ]
                    }
                }, 
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except DiagramGenerationError as e:
            return Response(
                {
                    'error': f'Diagram generation failed: {str(e)}',
                    'error_type': 'diagram_generation_error',
                    'stage': e.stage,
                    'details': e.details
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except RuntimeError as e:
            return Response(
                {'error': str(e), 'error_type': 'runtime_error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {
                    'error': 'An unexpected error occurred while generating the specification',
                    'error_type': 'unknown_error'
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        summary="List entities",
        description="Retrieve all entities from projects owned by the authenticated user.",
        tags=["Entities"],
    ),
    create=extend_schema(
        summary="Create entity",
        description="Create a new entity in a project.",
        tags=["Entities"],
    ),
    retrieve=extend_schema(
        summary="Get entity",
        description="Retrieve a specific entity by ID.",
        tags=["Entities"],
    ),
    update=extend_schema(
        summary="Update entity",
        description="Update an entity's details.",
        tags=["Entities"],
    ),
    partial_update=extend_schema(
        summary="Partially update entity",
        description="Partially update an entity's details.",
        tags=["Entities"],
    ),
    destroy=extend_schema(
        summary="Delete entity",
        description="Delete an entity and its associated diagram node.",
        tags=["Entities"],
    ),
)
class EntityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing entities."""

    serializer_class = EntitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Entity.objects.filter(project__owner=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List relationships",
        description="Retrieve all relationships from projects owned by the authenticated user.",
        tags=["Relationships"],
    ),
    create=extend_schema(
        summary="Create relationship",
        description="Create a new relationship between entities.",
        tags=["Relationships"],
    ),
    retrieve=extend_schema(
        summary="Get relationship",
        description="Retrieve a specific relationship by ID.",
        tags=["Relationships"],
    ),
    update=extend_schema(
        summary="Update relationship",
        description="Update a relationship's details.",
        tags=["Relationships"],
    ),
    partial_update=extend_schema(
        summary="Partially update relationship",
        description="Partially update a relationship's details.",
        tags=["Relationships"],
    ),
    destroy=extend_schema(
        summary="Delete relationship",
        description="Delete a relationship and its associated diagram edge.",
        tags=["Relationships"],
    ),
)
class RelationshipViewSet(viewsets.ModelViewSet):
    """ViewSet for managing relationships."""

    serializer_class = RelationshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Relationship.objects.filter(project__owner=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List diagram nodes",
        description="Retrieve all diagram nodes from projects owned by the authenticated user.",
        tags=["Diagrams"],
    ),
    create=extend_schema(
        summary="Create diagram node",
        description="Create a new diagram node for an entity.",
        tags=["Diagrams"],
    ),
    retrieve=extend_schema(
        summary="Get diagram node",
        description="Retrieve a specific diagram node by ID.",
        tags=["Diagrams"],
    ),
    update=extend_schema(
        summary="Update diagram node",
        description="Update a diagram node's position and styling.",
        tags=["Diagrams"],
    ),
    partial_update=extend_schema(
        summary="Partially update diagram node",
        description="Partially update a diagram node's details.",
        tags=["Diagrams"],
    ),
    destroy=extend_schema(
        summary="Delete diagram node",
        description="Delete a diagram node.",
        tags=["Diagrams"],
    ),
)
class DiagramNodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing diagram nodes."""

    serializer_class = DiagramNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DiagramNode.objects.filter(entity__project__owner=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List diagram edges",
        description="Retrieve all diagram edges from projects owned by the authenticated user.",
        tags=["Diagrams"],
    ),
    create=extend_schema(
        summary="Create diagram edge",
        description="Create a new diagram edge for a relationship.",
        tags=["Diagrams"],
    ),
    retrieve=extend_schema(
        summary="Get diagram edge",
        description="Retrieve a specific diagram edge by ID.",
        tags=["Diagrams"],
    ),
    update=extend_schema(
        summary="Update diagram edge",
        description="Update a diagram edge's styling and path.",
        tags=["Diagrams"],
    ),
    partial_update=extend_schema(
        summary="Partially update diagram edge",
        description="Partially update a diagram edge's details.",
        tags=["Diagrams"],
    ),
    destroy=extend_schema(
        summary="Delete diagram edge",
        description="Delete a diagram edge.",
        tags=["Diagrams"],
    ),
)
class DiagramEdgeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing diagram edges."""

    serializer_class = DiagramEdgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DiagramEdge.objects.filter(
            relationship__project__owner=self.request.user
        )


@extend_schema_view(
    list=extend_schema(
        summary="List specifications",
        description="Retrieve all specifications from projects owned by the authenticated user.",
        tags=["Specifications"],
    ),
    create=extend_schema(
        summary="Create specification",
        description="Create a new specification document for a project.",
        tags=["Specifications"],
    ),
    retrieve=extend_schema(
        summary="Get specification",
        description="Retrieve a specific specification by ID.",
        tags=["Specifications"],
    ),
    update=extend_schema(
        summary="Update specification",
        description="Update a specification document.",
        tags=["Specifications"],
    ),
    partial_update=extend_schema(
        summary="Partially update specification",
        description="Partially update a specification document.",
        tags=["Specifications"],
    ),
    destroy=extend_schema(
        summary="Delete specification",
        description="Delete a specification document.",
        tags=["Specifications"],
    ),
)
class SpecificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing specifications."""

    serializer_class = SpecificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Specification.objects.filter(project__owner=self.request.user)
