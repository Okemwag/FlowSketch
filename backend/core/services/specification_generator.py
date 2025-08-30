"""
Specification generator service for creating structured documentation from diagram data.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from .diagram_engine import DiagramData, Edge, Node
from .text_parser import DiagramType


class SpecificationSection(Enum):
    """Standard specification sections."""

    OVERVIEW = "overview"
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    COMPONENTS = "components"
    DATA_FLOW = "data_flow"
    BUSINESS_RULES = "business_rules"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    IMPLEMENTATION_NOTES = "implementation_notes"


class ProgrammingLanguage(Enum):
    """Supported programming languages for test generation."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"


class TestType(Enum):
    """Types of tests to generate."""

    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "e2e"
    PERFORMANCE = "performance"


@dataclass
class AcceptanceCriterion:
    """Represents an acceptance criterion."""

    id: str
    description: str
    priority: str  # "high", "medium", "low"
    category: str  # "functional", "non-functional", "technical"
    related_entities: List[str]
    test_scenarios: List[str]


@dataclass
class SpecSection:
    """Represents a specification section."""

    title: str
    content: str
    section_type: SpecificationSection
    order: int
    subsections: Optional[List["SpecSection"]] = None


@dataclass
class TestCase:
    """Represents a generated test case."""

    name: str
    description: str
    test_type: TestType
    setup_code: str
    test_code: str
    teardown_code: str
    assertions: List[str]
    related_acceptance_criteria: List[str]


@dataclass
class TestFile:
    """Represents a generated test file."""

    filename: str
    language: ProgrammingLanguage
    imports: List[str]
    setup_code: str
    test_cases: List[TestCase]
    helper_methods: List[str]
    full_content: str


@dataclass
class TestScaffold:
    """Container for generated test scaffold."""

    language: ProgrammingLanguage
    test_files: List[TestFile]
    setup_instructions: str
    run_instructions: str
    dependencies: List[str]
    metadata: Dict[str, Union[str, int, float]]


@dataclass
class GeneratedSpecification:
    """Container for generated specification data."""

    title: str
    sections: List[SpecSection]
    acceptance_criteria: List[AcceptanceCriterion]
    metadata: Dict[str, Union[str, int, float]]
    markdown_content: str
    test_scaffold: Optional[TestScaffold] = None


class SpecificationGenerationError(Exception):
    """Exception raised when specification generation fails."""

    def __init__(self, message: str, stage: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.stage = stage
        self.details = details or {}


class SpecificationGenerator:
    """Service for generating structured specifications from diagram data."""

    def __init__(self):
        """Initialize the specification generator."""
        self.section_templates = {
            SpecificationSection.OVERVIEW: self._generate_overview_section,
            SpecificationSection.REQUIREMENTS: self._generate_requirements_section,
            SpecificationSection.ARCHITECTURE: self._generate_architecture_section,
            SpecificationSection.COMPONENTS: self._generate_components_section,
            SpecificationSection.DATA_FLOW: self._generate_data_flow_section,
            SpecificationSection.BUSINESS_RULES: self._generate_business_rules_section,
            SpecificationSection.ACCEPTANCE_CRITERIA: self._generate_acceptance_criteria_section,
            SpecificationSection.IMPLEMENTATION_NOTES: self._generate_implementation_notes_section,
        }

        # Templates for different diagram types
        self.diagram_type_templates = {
            DiagramType.FLOWCHART: [
                SpecificationSection.OVERVIEW,
                SpecificationSection.REQUIREMENTS,
                SpecificationSection.DATA_FLOW,
                SpecificationSection.BUSINESS_RULES,
                SpecificationSection.ACCEPTANCE_CRITERIA,
                SpecificationSection.IMPLEMENTATION_NOTES,
            ],
            DiagramType.ERD: [
                SpecificationSection.OVERVIEW,
                SpecificationSection.REQUIREMENTS,
                SpecificationSection.ARCHITECTURE,
                SpecificationSection.COMPONENTS,
                SpecificationSection.ACCEPTANCE_CRITERIA,
                SpecificationSection.IMPLEMENTATION_NOTES,
            ],
            DiagramType.SEQUENCE: [
                SpecificationSection.OVERVIEW,
                SpecificationSection.REQUIREMENTS,
                SpecificationSection.DATA_FLOW,
                SpecificationSection.ACCEPTANCE_CRITERIA,
                SpecificationSection.IMPLEMENTATION_NOTES,
            ],
            DiagramType.CLASS: [
                SpecificationSection.OVERVIEW,
                SpecificationSection.REQUIREMENTS,
                SpecificationSection.ARCHITECTURE,
                SpecificationSection.COMPONENTS,
                SpecificationSection.ACCEPTANCE_CRITERIA,
                SpecificationSection.IMPLEMENTATION_NOTES,
            ],
            DiagramType.PROCESS: [
                SpecificationSection.OVERVIEW,
                SpecificationSection.REQUIREMENTS,
                SpecificationSection.DATA_FLOW,
                SpecificationSection.BUSINESS_RULES,
                SpecificationSection.ACCEPTANCE_CRITERIA,
                SpecificationSection.IMPLEMENTATION_NOTES,
            ],
        }

    def generate_specification(
        self,
        diagram_data: DiagramData,
        project_name: str = "System",
        include_tests: bool = True,
        test_language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    ) -> GeneratedSpecification:
        """Generate a complete specification from diagram data."""
        try:
            # Validate input
            self._validate_diagram_data(diagram_data)

            # Generate title
            title = self._generate_title(diagram_data, project_name)

            # Determine sections to generate based on diagram type
            section_types = self.diagram_type_templates.get(
                diagram_data.diagram_type,
                self.diagram_type_templates[DiagramType.FLOWCHART],
            )

            # Generate sections
            sections = []
            for i, section_type in enumerate(section_types):
                try:
                    section = self.section_templates[section_type](diagram_data, i + 1)
                    sections.append(section)
                except Exception as e:
                    # Log error but continue with other sections
                    print(
                        f"Warning: Failed to generate {section_type.value} section: {e}"
                    )

            # Generate acceptance criteria
            acceptance_criteria = self._generate_acceptance_criteria(diagram_data)

            # Generate test scaffold if requested
            test_scaffold = None
            if include_tests:
                try:
                    test_scaffold = self.generate_test_scaffold(
                        diagram_data, acceptance_criteria, test_language
                    )
                except Exception as e:
                    # Log error but continue without tests
                    print(f"Warning: Failed to generate test scaffold: {e}")

            # Generate markdown content
            markdown_content = self._generate_markdown(
                title, sections, acceptance_criteria
            )

            # Create metadata
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "diagram_type": diagram_data.diagram_type.value,
                "node_count": len(diagram_data.nodes),
                "edge_count": len(diagram_data.edges),
                "section_count": len(sections),
                "acceptance_criteria_count": len(acceptance_criteria),
                "word_count": len(markdown_content.split()),
                "includes_tests": include_tests,
                "test_language": test_language.value if include_tests else None,
            }

            return GeneratedSpecification(
                title=title,
                sections=sections,
                acceptance_criteria=acceptance_criteria,
                metadata=metadata,
                markdown_content=markdown_content,
                test_scaffold=test_scaffold,
            )

        except Exception as e:
            if isinstance(e, SpecificationGenerationError):
                raise
            raise SpecificationGenerationError(
                f"Unexpected error during specification generation: {str(e)}",
                "unknown",
                {"error_type": type(e).__name__},
            )

    def _validate_diagram_data(self, diagram_data: DiagramData) -> None:
        """Validate input diagram data."""
        if not diagram_data:
            raise SpecificationGenerationError(
                "Diagram data is None", "input_validation"
            )

        if not diagram_data.nodes:
            raise SpecificationGenerationError(
                "Diagram has no nodes", "input_validation"
            )

        if not diagram_data.mermaid_syntax:
            raise SpecificationGenerationError(
                "Diagram has no Mermaid syntax", "input_validation"
            )

    def _generate_title(self, diagram_data: DiagramData, project_name: str) -> str:
        """Generate a title for the specification."""
        diagram_type_names = {
            DiagramType.FLOWCHART: "Process Flow",
            DiagramType.ERD: "Data Model",
            DiagramType.SEQUENCE: "Interaction Flow",
            DiagramType.CLASS: "System Architecture",
            DiagramType.PROCESS: "Business Process",
        }

        type_name = diagram_type_names.get(diagram_data.diagram_type, "System")
        return f"{project_name} - {type_name} Specification"

    def _generate_overview_section(
        self, diagram_data: DiagramData, order: int
    ) -> SpecSection:
        """Generate the overview section."""
        entity_count = len(diagram_data.nodes)
        relationship_count = len(diagram_data.edges)

        # Analyze entity types
        entity_types = {}
        for node in diagram_data.nodes:
            entity_type = node.entity_type
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        # Generate overview content
        content_parts = [
            "## Overview",
            "",
            f"This specification describes a {diagram_data.diagram_type.value} containing {entity_count} entities and {relationship_count} relationships.",
            "",
        ]

        if entity_types:
            content_parts.extend(
                [
                    "### System Components",
                    "",
                    "The system consists of the following components:",
                    "",
                ]
            )

            for entity_type, count in entity_types.items():
                type_description = self._get_entity_type_description(entity_type)
                content_parts.append(
                    f"- **{type_description}**: {count} component{'s' if count != 1 else ''}"
                )

            content_parts.append("")

        # Add purpose based on diagram type
        purpose = self._get_diagram_purpose(diagram_data.diagram_type)
        if purpose:
            content_parts.extend(
                [
                    "### Purpose",
                    "",
                    purpose,
                    "",
                ]
            )

        return SpecSection(
            title="Overview",
            content="\n".join(content_parts),
            section_type=SpecificationSection.OVERVIEW,
            order=order,
        )

    def _generate_requirements_section(
        self, diagram_data: DiagramData, order: int
    ) -> SpecSection:
        """Generate the requirements section."""
        content_parts = [
            "## Requirements",
            "",
            "### Functional Requirements",
            "",
        ]

        # Generate requirements based on relationships
        req_counter = 1
        for edge in diagram_data.edges:
            source_node = self._find_node_by_id(diagram_data.nodes, edge.source_id)
            target_node = self._find_node_by_id(diagram_data.nodes, edge.target_id)

            if source_node and target_node:
                requirement = self._generate_functional_requirement(
                    source_node, target_node, edge, req_counter
                )
                content_parts.append(requirement)
                req_counter += 1

        # Add non-functional requirements
        content_parts.extend(
            [
                "",
                "### Non-Functional Requirements",
                "",
                f"**NFR-1**: The system SHALL handle up to {len(diagram_data.nodes) * 100} concurrent operations",
                f"**NFR-2**: All {diagram_data.diagram_type.value} operations SHALL complete within 2 seconds",
                "**NFR-3**: The system SHALL maintain 99.9% availability",
                "**NFR-4**: All data SHALL be validated before processing",
                "",
            ]
        )

        return SpecSection(
            title="Requirements",
            content="\n".join(content_parts),
            section_type=SpecificationSection.REQUIREMENTS,
            order=order,
        )

    def _generate_architecture_section(
        self, diagram_data: DiagramData, order: int
    ) -> SpecSection:
        """Generate the architecture section."""
        content_parts = [
            "## Architecture",
            "",
            "### System Architecture",
            "",
            f"The system follows a {diagram_data.diagram_type.value}-based architecture with the following key components:",
            "",
        ]

        # Group nodes by entity type
        components_by_type = {}
        for node in diagram_data.nodes:
            entity_type = node.entity_type
            if entity_type not in components_by_type:
                components_by_type[entity_type] = []
            components_by_type[entity_type].append(node)

        # Describe each component type
        for entity_type, nodes in components_by_type.items():
            type_description = self._get_entity_type_description(entity_type)
            content_parts.extend(
                [
                    f"#### {type_description} Layer",
                    "",
                ]
            )

            for node in nodes:
                content_parts.append(
                    f"- **{node.label}**: {self._generate_component_description(node)}"
                )

            content_parts.append("")

        # Add interaction patterns
        if diagram_data.edges:
            content_parts.extend(
                [
                    "### Interaction Patterns",
                    "",
                    "The system components interact through the following patterns:",
                    "",
                ]
            )

            interaction_patterns = self._analyze_interaction_patterns(diagram_data)
            for pattern in interaction_patterns:
                content_parts.append(f"- {pattern}")

            content_parts.append("")

        return SpecSection(
            title="Architecture",
            content="\n".join(content_parts),
            section_type=SpecificationSection.ARCHITECTURE,
            order=order,
        )

    def _generate_components_section(
        self, diagram_data: DiagramData, order: int
    ) -> SpecSection:
        """Generate the components section."""
        content_parts = [
            "## Components",
            "",
            "### Component Specifications",
            "",
        ]

        for node in diagram_data.nodes:
            content_parts.extend(
                [
                    f"#### {node.label}",
                    "",
                    f"**Type**: {self._get_entity_type_description(node.entity_type)}",
                    f"**Description**: {self._generate_component_description(node)}",
                    "",
                ]
            )

            # Add responsibilities
            responsibilities = self._generate_component_responsibilities(
                node, diagram_data.edges
            )
            if responsibilities:
                content_parts.extend(
                    [
                        "**Responsibilities**:",
                        "",
                    ]
                )
                for responsibility in responsibilities:
                    content_parts.append(f"- {responsibility}")
                content_parts.append("")

            # Add interfaces
            interfaces = self._generate_component_interfaces(node, diagram_data.edges)
            if interfaces:
                content_parts.extend(
                    [
                        "**Interfaces**:",
                        "",
                    ]
                )
                for interface in interfaces:
                    content_parts.append(f"- {interface}")
                content_parts.append("")

        return SpecSection(
            title="Components",
            content="\n".join(content_parts),
            section_type=SpecificationSection.COMPONENTS,
            order=order,
        )

    def _generate_data_flow_section(
        self, diagram_data: DiagramData, order: int
    ) -> SpecSection:
        """Generate the data flow section."""
        content_parts = [
            "## Data Flow",
            "",
            "### Flow Description",
            "",
            "The following describes the primary data flows within the system:",
            "",
        ]

        # Analyze flows
        flows = self._analyze_data_flows(diagram_data)

        for i, flow in enumerate(flows, 1):
            content_parts.extend(
                [
                    f"#### Flow {i}: {flow['name']}",
                    "",
                    f"**Description**: {flow['description']}",
                    "",
                    "**Steps**:",
                    "",
                ]
            )

            for j, step in enumerate(flow["steps"], 1):
                content_parts.append(f"{j}. {step}")

            content_parts.append("")

        return SpecSection(
            title="Data Flow",
            content="\n".join(content_parts),
            section_type=SpecificationSection.DATA_FLOW,
            order=order,
        )

    def _generate_business_rules_section(
        self, diagram_data: DiagramData, order: int
    ) -> SpecSection:
        """Generate the business rules section."""
        content_parts = [
            "## Business Rules",
            "",
            "### Rules and Constraints",
            "",
        ]

        # Generate business rules based on relationships
        rule_counter = 1
        for edge in diagram_data.edges:
            source_node = self._find_node_by_id(diagram_data.nodes, edge.source_id)
            target_node = self._find_node_by_id(diagram_data.nodes, edge.target_id)

            if source_node and target_node:
                rule = self._generate_business_rule(
                    source_node, target_node, edge, rule_counter
                )
                if rule:
                    content_parts.append(rule)
                    rule_counter += 1

        # Add general rules
        content_parts.extend(
            [
                "",
                "### General Rules",
                "",
                f"**BR-{rule_counter}**: All {diagram_data.diagram_type.value} operations must be logged",
                f"**BR-{rule_counter + 1}**: Invalid data must be rejected with appropriate error messages",
                f"**BR-{rule_counter + 2}**: System state must remain consistent after each operation",
                "",
            ]
        )

        return SpecSection(
            title="Business Rules",
            content="\n".join(content_parts),
            section_type=SpecificationSection.BUSINESS_RULES,
            order=order,
        )

    def _generate_acceptance_criteria_section(
        self, diagram_data: DiagramData, order: int
    ) -> SpecSection:
        """Generate the acceptance criteria section."""
        content_parts = [
            "## Acceptance Criteria",
            "",
            "### Functional Acceptance Criteria",
            "",
        ]

        # Generate criteria based on components and relationships
        criteria_counter = 1
        for node in diagram_data.nodes:
            criteria = self._generate_node_acceptance_criteria(
                node, diagram_data.edges, criteria_counter
            )
            content_parts.extend(criteria)
            criteria_counter += len(criteria)

        return SpecSection(
            title="Acceptance Criteria",
            content="\n".join(content_parts),
            section_type=SpecificationSection.ACCEPTANCE_CRITERIA,
            order=order,
        )

    def _generate_implementation_notes_section(
        self, diagram_data: DiagramData, order: int
    ) -> SpecSection:
        """Generate the implementation notes section."""
        content_parts = [
            "## Implementation Notes",
            "",
            "### Technical Considerations",
            "",
        ]

        # Add implementation notes based on diagram type
        if diagram_data.diagram_type == DiagramType.ERD:
            content_parts.extend(
                [
                    "- Implement proper database indexing for performance",
                    "- Consider data migration strategies for schema changes",
                    "- Implement referential integrity constraints",
                    "- Plan for data archiving and cleanup procedures",
                ]
            )
        elif diagram_data.diagram_type == DiagramType.SEQUENCE:
            content_parts.extend(
                [
                    "- Implement proper error handling for each interaction",
                    "- Consider timeout handling for external calls",
                    "- Implement retry mechanisms for failed operations",
                    "- Add logging for debugging interaction flows",
                ]
            )
        elif diagram_data.diagram_type == DiagramType.PROCESS:
            content_parts.extend(
                [
                    "- Implement process state management",
                    "- Consider parallel processing opportunities",
                    "- Add process monitoring and metrics",
                    "- Implement process rollback capabilities",
                ]
            )
        else:
            content_parts.extend(
                [
                    "- Follow established coding standards and patterns",
                    "- Implement comprehensive error handling",
                    "- Add appropriate logging and monitoring",
                    "- Consider scalability and performance requirements",
                ]
            )

        content_parts.extend(
            [
                "",
                "### Testing Strategy",
                "",
                "- Unit tests for individual components",
                "- Integration tests for component interactions",
                "- End-to-end tests for complete workflows",
                "- Performance tests for scalability validation",
                "",
            ]
        )

        return SpecSection(
            title="Implementation Notes",
            content="\n".join(content_parts),
            section_type=SpecificationSection.IMPLEMENTATION_NOTES,
            order=order,
        )

    def _generate_acceptance_criteria(
        self, diagram_data: DiagramData
    ) -> List[AcceptanceCriterion]:
        """Generate acceptance criteria from diagram data."""
        criteria = []
        criterion_counter = 1

        # Generate criteria for each node
        for node in diagram_data.nodes:
            node_criteria = self._generate_node_criteria(
                node, diagram_data.edges, criterion_counter
            )
            criteria.extend(node_criteria)
            criterion_counter += len(node_criteria)

        # Generate criteria for relationships
        for edge in diagram_data.edges:
            edge_criteria = self._generate_edge_criteria(
                edge, diagram_data.nodes, criterion_counter
            )
            if edge_criteria:
                criteria.append(edge_criteria)
                criterion_counter += 1

        return criteria

    def _generate_markdown(
        self,
        title: str,
        sections: List[SpecSection],
        criteria: List[AcceptanceCriterion],
    ) -> str:
        """Generate complete markdown content."""
        content_parts = [
            f"# {title}",
            "",
            f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
        ]

        # Add sections
        for section in sections:
            content_parts.append(section.content)
            content_parts.append("")

        # Add acceptance criteria summary if not already included
        if not any(
            section.section_type == SpecificationSection.ACCEPTANCE_CRITERIA
            for section in sections
        ):
            content_parts.extend(
                [
                    "## Acceptance Criteria Summary",
                    "",
                    f"Total acceptance criteria: {len(criteria)}",
                    "",
                    "### High Priority Criteria",
                    "",
                ]
            )

            high_priority_criteria = [c for c in criteria if c.priority == "high"]
            for criterion in high_priority_criteria[:5]:  # Show top 5
                content_parts.append(
                    f"- **AC-{criterion.id}**: {criterion.description}"
                )

            content_parts.append("")

        return "\n".join(content_parts)

    # Helper methods
    def _get_entity_type_description(self, entity_type: str) -> str:
        """Get human-readable description for entity type."""
        descriptions = {
            "object": "Data Objects",
            "process": "Business Processes",
            "actor": "System Actors",
            "data": "Data Stores",
            "system": "System Components",
            "event": "System Events",
        }
        return descriptions.get(entity_type, "Components")

    def _get_diagram_purpose(self, diagram_type: DiagramType) -> str:
        """Get purpose description for diagram type."""
        purposes = {
            DiagramType.FLOWCHART: "This flowchart illustrates the process flow and decision points within the system.",
            DiagramType.ERD: "This entity relationship diagram defines the data model and relationships between entities.",
            DiagramType.SEQUENCE: "This sequence diagram shows the interactions between system components over time.",
            DiagramType.CLASS: "This class diagram represents the system's object-oriented structure and relationships.",
            DiagramType.PROCESS: "This process diagram outlines the business processes and their interconnections.",
        }
        return purposes.get(
            diagram_type,
            "This diagram represents the system structure and relationships.",
        )

    def _find_node_by_id(self, nodes: List[Node], node_id: str) -> Optional[Node]:
        """Find a node by its ID."""
        return next((node for node in nodes if node.id == node_id), None)

    def _generate_functional_requirement(
        self, source: Node, target: Node, edge: Edge, req_num: int
    ) -> str:
        """Generate a functional requirement from a relationship."""
        relationship_templates = {
            "uses": f"**FR-{req_num}**: {source.label} SHALL be able to use {target.label}",
            "creates": f"**FR-{req_num}**: {source.label} SHALL be able to create {target.label}",
            "manages": f"**FR-{req_num}**: {source.label} SHALL manage {target.label}",
            "accesses": f"**FR-{req_num}**: {source.label} SHALL have access to {target.label}",
            "processes": f"**FR-{req_num}**: {source.label} SHALL process {target.label}",
            "sends": f"**FR-{req_num}**: {source.label} SHALL send data to {target.label}",
            "receives": f"**FR-{req_num}**: {source.label} SHALL receive data from {target.label}",
        }

        template = relationship_templates.get(
            edge.relationship_type,
            f"**FR-{req_num}**: {source.label} SHALL interact with {target.label}",
        )

        if edge.label:
            template += f" ({edge.label})"

        return template

    def _generate_component_description(self, node: Node) -> str:
        """Generate a description for a component."""
        type_descriptions = {
            "object": f"A data object that represents {node.label.lower()} information",
            "process": f"A business process that handles {node.label.lower()} operations",
            "actor": f"An external actor that represents {node.label.lower()}",
            "data": f"A data store that contains {node.label.lower()} data",
            "system": f"A system component that provides {node.label.lower()} functionality",
            "event": f"A system event that triggers {node.label.lower()} actions",
        }

        return type_descriptions.get(
            node.entity_type, f"A system component for {node.label.lower()}"
        )

    def _generate_component_responsibilities(
        self, node: Node, edges: List[Edge]
    ) -> List[str]:
        """Generate responsibilities for a component."""
        responsibilities = []

        # Outgoing relationships (what this component does)
        outgoing = [edge for edge in edges if edge.source_id == node.id]
        for edge in outgoing:
            if edge.relationship_type == "creates":
                responsibilities.append(
                    f"Create and manage {edge.label or 'related data'}"
                )
            elif edge.relationship_type == "processes":
                responsibilities.append(f"Process {edge.label or 'incoming data'}")
            elif edge.relationship_type == "manages":
                responsibilities.append(f"Manage {edge.label or 'system resources'}")

        # Incoming relationships (what this component handles)
        incoming = [edge for edge in edges if edge.target_id == node.id]
        for edge in incoming:
            if edge.relationship_type == "uses":
                responsibilities.append(
                    f"Provide services for {edge.label or 'system operations'}"
                )

        return responsibilities[:3]  # Limit to top 3 responsibilities

    def _generate_component_interfaces(
        self, node: Node, edges: List[Edge]
    ) -> List[str]:
        """Generate interfaces for a component."""
        interfaces = []

        # Input interfaces
        incoming = [edge for edge in edges if edge.target_id == node.id]
        if incoming:
            interfaces.append(
                f"Input: Receives data from {len(incoming)} source{'s' if len(incoming) != 1 else ''}"
            )

        # Output interfaces
        outgoing = [edge for edge in edges if edge.source_id == node.id]
        if outgoing:
            interfaces.append(
                f"Output: Sends data to {len(outgoing)} target{'s' if len(outgoing) != 1 else ''}"
            )

        return interfaces

    def _analyze_interaction_patterns(self, diagram_data: DiagramData) -> List[str]:
        """Analyze interaction patterns in the diagram."""
        patterns = []

        # Analyze common patterns
        if len(diagram_data.edges) > len(diagram_data.nodes):
            patterns.append("High interconnectivity between components")

        # Find hub nodes (nodes with many connections)
        connection_counts = {}
        for edge in diagram_data.edges:
            connection_counts[edge.source_id] = (
                connection_counts.get(edge.source_id, 0) + 1
            )
            connection_counts[edge.target_id] = (
                connection_counts.get(edge.target_id, 0) + 1
            )

        hub_nodes = [
            node_id for node_id, count in connection_counts.items() if count > 3
        ]
        if hub_nodes:
            patterns.append(
                f"Central hub pattern with {len(hub_nodes)} highly connected component{'s' if len(hub_nodes) != 1 else ''}"
            )

        # Analyze relationship types
        relationship_types = [edge.relationship_type for edge in diagram_data.edges]
        if "creates" in relationship_types and "uses" in relationship_types:
            patterns.append("Producer-consumer pattern identified")

        return patterns

    def _analyze_data_flows(self, diagram_data: DiagramData) -> List[Dict]:
        """Analyze data flows in the diagram."""
        flows = []

        # Find potential flow chains
        visited = set()
        for node in diagram_data.nodes:
            if node.id not in visited:
                flow = self._trace_flow_from_node(node, diagram_data.edges, visited)
                if len(flow) > 1:
                    flows.append(
                        {
                            "name": f"{flow[0].label} to {flow[-1].label}",
                            "description": f"Data flow from {flow[0].label} through the system to {flow[-1].label}",
                            "steps": [
                                f"{flow[i].label} → {flow[i+1].label}"
                                for i in range(len(flow) - 1)
                            ],
                        }
                    )

        return flows[:3]  # Limit to top 3 flows

    def _trace_flow_from_node(
        self, start_node: Node, edges: List[Edge], visited: set
    ) -> List[Node]:
        """Trace a flow starting from a node."""
        # This is a simplified flow tracing - in a real implementation,
        # you might want more sophisticated graph traversal
        flow = [start_node]
        visited.add(start_node.id)

        # Find next node in flow
        outgoing = [edge for edge in edges if edge.source_id == start_node.id]
        if outgoing:
            # Take the first outgoing edge for simplicity
            next_edge = outgoing[0]
            next_node = self._find_node_by_id(
                [n for n in flow if n.id != start_node.id], next_edge.target_id
            )
            if next_node and next_node.id not in visited:
                flow.extend(self._trace_flow_from_node(next_node, edges, visited))

        return flow

    def _generate_business_rule(
        self, source: Node, target: Node, edge: Edge, rule_num: int
    ) -> Optional[str]:
        """Generate a business rule from a relationship."""
        rule_templates = {
            "creates": f"**BR-{rule_num}**: Only authorized {source.label} can create {target.label}",
            "manages": f"**BR-{rule_num}**: {source.label} must validate all {target.label} operations",
            "accesses": f"**BR-{rule_num}**: {source.label} access to {target.label} must be logged",
            "processes": f"**BR-{rule_num}**: {source.label} must validate {target.label} before processing",
        }

        return rule_templates.get(edge.relationship_type)

    def _generate_node_acceptance_criteria(
        self, node: Node, edges: List[Edge], start_num: int
    ) -> List[str]:
        """Generate acceptance criteria for a node."""
        criteria = []

        # Basic existence criteria
        criteria.append(
            f"**AC-{start_num}**: {node.label} component must be properly initialized"
        )

        # Functional criteria based on relationships
        outgoing = [edge for edge in edges if edge.source_id == node.id]
        if outgoing:
            criteria.append(
                f"**AC-{start_num + 1}**: {node.label} must successfully interact with {len(outgoing)} connected component{'s' if len(outgoing) != 1 else ''}"
            )

        return criteria[:2]  # Limit to 2 criteria per node

    def _generate_node_criteria(
        self, node: Node, edges: List[Edge], start_num: int
    ) -> List[AcceptanceCriterion]:
        """Generate AcceptanceCriterion objects for a node."""
        criteria = []

        # Basic functionality criterion
        criteria.append(
            AcceptanceCriterion(
                id=str(start_num),
                description=f"{node.label} must be properly initialized and functional",
                priority="high",
                category="functional",
                related_entities=[node.label],
                test_scenarios=[
                    f"Verify {node.label} initialization",
                    f"Test {node.label} basic operations",
                ],
            )
        )

        # Interaction criteria
        connected_edges = [
            edge
            for edge in edges
            if edge.source_id == node.id or edge.target_id == node.id
        ]
        if connected_edges:
            criteria.append(
                AcceptanceCriterion(
                    id=str(start_num + 1),
                    description=f"{node.label} must successfully interact with connected components",
                    priority="medium",
                    category="functional",
                    related_entities=[node.label],
                    test_scenarios=[
                        f"Test {node.label} interactions",
                        f"Verify {node.label} error handling",
                    ],
                )
            )

        return criteria

    def _generate_edge_criteria(
        self, edge: Edge, nodes: List[Node], criterion_num: int
    ) -> Optional[AcceptanceCriterion]:
        """Generate AcceptanceCriterion for an edge."""
        source_node = self._find_node_by_id(nodes, edge.source_id)
        target_node = self._find_node_by_id(nodes, edge.target_id)

        if not source_node or not target_node:
            return None

        return AcceptanceCriterion(
            id=str(criterion_num),
            description=f"{source_node.label} must successfully {edge.relationship_type} {target_node.label}",
            priority="medium",
            category="functional",
            related_entities=[source_node.label, target_node.label],
            test_scenarios=[
                f"Test {edge.relationship_type} operation",
                f"Verify error handling for failed {edge.relationship_type}",
            ],
        )

    def generate_test_scaffold(
        self,
        diagram_data: DiagramData,
        acceptance_criteria: List[AcceptanceCriterion],
        language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    ) -> TestScaffold:
        """Generate test scaffold from diagram data and acceptance criteria."""
        try:
            # Generate test files
            test_files = []

            # Generate unit tests
            unit_test_file = self._generate_unit_test_file(
                diagram_data, acceptance_criteria, language
            )
            test_files.append(unit_test_file)

            # Generate integration tests
            integration_test_file = self._generate_integration_test_file(
                diagram_data, acceptance_criteria, language
            )
            test_files.append(integration_test_file)

            # Generate end-to-end tests if applicable
            if len(diagram_data.edges) > 2:  # Complex enough for E2E tests
                e2e_test_file = self._generate_e2e_test_file(
                    diagram_data, acceptance_criteria, language
                )
                test_files.append(e2e_test_file)

            # Generate setup and run instructions
            setup_instructions = self._generate_setup_instructions(language)
            run_instructions = self._generate_run_instructions(language)
            dependencies = self._get_test_dependencies(language)

            # Create metadata
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "language": language.value,
                "test_file_count": len(test_files),
                "total_test_cases": sum(len(file.test_cases) for file in test_files),
                "diagram_type": diagram_data.diagram_type.value,
            }

            return TestScaffold(
                language=language,
                test_files=test_files,
                setup_instructions=setup_instructions,
                run_instructions=run_instructions,
                dependencies=dependencies,
                metadata=metadata,
            )

        except Exception as e:
            raise SpecificationGenerationError(
                f"Failed to generate test scaffold: {str(e)}",
                "test_generation",
                {"language": language.value},
            )

    def _generate_unit_test_file(
        self,
        diagram_data: DiagramData,
        acceptance_criteria: List[AcceptanceCriterion],
        language: ProgrammingLanguage,
    ) -> TestFile:
        """Generate unit test file."""
        test_cases = []

        # Generate test cases for each node (component)
        for node in diagram_data.nodes:
            node_test_cases = self._generate_node_unit_tests(
                node, acceptance_criteria, language
            )
            test_cases.extend(node_test_cases)

        # Generate imports and setup
        imports = self._get_unit_test_imports(language)
        setup_code = self._get_unit_test_setup(language)
        helper_methods = self._get_unit_test_helpers(language)

        # Generate full file content
        full_content = self._generate_test_file_content(
            "unit_tests", imports, setup_code, test_cases, helper_methods, language
        )

        return TestFile(
            filename=self._get_unit_test_filename(language),
            language=language,
            imports=imports,
            setup_code=setup_code,
            test_cases=test_cases,
            helper_methods=helper_methods,
            full_content=full_content,
        )

    def _generate_integration_test_file(
        self,
        diagram_data: DiagramData,
        acceptance_criteria: List[AcceptanceCriterion],
        language: ProgrammingLanguage,
    ) -> TestFile:
        """Generate integration test file."""
        test_cases = []

        # Generate test cases for relationships (integrations)
        for edge in diagram_data.edges:
            edge_test_cases = self._generate_edge_integration_tests(
                edge, diagram_data.nodes, acceptance_criteria, language
            )
            test_cases.extend(edge_test_cases)

        # Generate imports and setup
        imports = self._get_integration_test_imports(language)
        setup_code = self._get_integration_test_setup(language)
        helper_methods = self._get_integration_test_helpers(language)

        # Generate full file content
        full_content = self._generate_test_file_content(
            "integration_tests",
            imports,
            setup_code,
            test_cases,
            helper_methods,
            language,
        )

        return TestFile(
            filename=self._get_integration_test_filename(language),
            language=language,
            imports=imports,
            setup_code=setup_code,
            test_cases=test_cases,
            helper_methods=helper_methods,
            full_content=full_content,
        )

    def _generate_e2e_test_file(
        self,
        diagram_data: DiagramData,
        acceptance_criteria: List[AcceptanceCriterion],
        language: ProgrammingLanguage,
    ) -> TestFile:
        """Generate end-to-end test file."""
        test_cases = []

        # Generate E2E test cases for complete workflows
        workflows = self._identify_workflows(diagram_data)
        for workflow in workflows:
            workflow_test_cases = self._generate_workflow_e2e_tests(
                workflow, acceptance_criteria, language
            )
            test_cases.extend(workflow_test_cases)

        # Generate imports and setup
        imports = self._get_e2e_test_imports(language)
        setup_code = self._get_e2e_test_setup(language)
        helper_methods = self._get_e2e_test_helpers(language)

        # Generate full file content
        full_content = self._generate_test_file_content(
            "e2e_tests", imports, setup_code, test_cases, helper_methods, language
        )

        return TestFile(
            filename=self._get_e2e_test_filename(language),
            language=language,
            imports=imports,
            setup_code=setup_code,
            test_cases=test_cases,
            helper_methods=helper_methods,
            full_content=full_content,
        )

    def _generate_node_unit_tests(
        self,
        node: Node,
        acceptance_criteria: List[AcceptanceCriterion],
        language: ProgrammingLanguage,
    ) -> List[TestCase]:
        """Generate unit tests for a node."""
        test_cases = []

        # Find related acceptance criteria
        related_criteria = [
            criterion
            for criterion in acceptance_criteria
            if node.label in criterion.related_entities
        ]

        # Generate basic functionality test
        basic_test = self._generate_basic_functionality_test(node, language)
        test_cases.append(basic_test)

        # Generate validation test
        validation_test = self._generate_validation_test(node, language)
        test_cases.append(validation_test)

        # Generate error handling test
        error_test = self._generate_error_handling_test(node, language)
        test_cases.append(error_test)

        # Generate tests for specific acceptance criteria
        for criterion in related_criteria[:2]:  # Limit to 2 criteria per node
            criterion_test = self._generate_acceptance_criteria_test(
                node, criterion, language
            )
            test_cases.append(criterion_test)

        return test_cases

    def _generate_edge_integration_tests(
        self,
        edge: Edge,
        nodes: List[Node],
        acceptance_criteria: List[AcceptanceCriterion],
        language: ProgrammingLanguage,
    ) -> List[TestCase]:
        """Generate integration tests for an edge."""
        test_cases = []

        source_node = self._find_node_by_id(nodes, edge.source_id)
        target_node = self._find_node_by_id(nodes, edge.target_id)

        if not source_node or not target_node:
            return test_cases

        # Generate successful interaction test
        success_test = self._generate_successful_interaction_test(
            source_node, target_node, edge, language
        )
        test_cases.append(success_test)

        # Generate failure handling test
        failure_test = self._generate_interaction_failure_test(
            source_node, target_node, edge, language
        )
        test_cases.append(failure_test)

        return test_cases

    def _generate_workflow_e2e_tests(
        self,
        workflow: List[Node],
        acceptance_criteria: List[AcceptanceCriterion],
        language: ProgrammingLanguage,
    ) -> List[TestCase]:
        """Generate E2E tests for a workflow."""
        test_cases = []

        if len(workflow) < 2:
            return test_cases

        # Generate happy path test
        happy_path_test = self._generate_happy_path_test(workflow, language)
        test_cases.append(happy_path_test)

        # Generate error path test
        error_path_test = self._generate_error_path_test(workflow, language)
        test_cases.append(error_path_test)

        return test_cases

    # Language-specific test generation methods
    def _generate_basic_functionality_test(
        self, node: Node, language: ProgrammingLanguage
    ) -> TestCase:
        """Generate basic functionality test for a node."""
        test_templates = {
            ProgrammingLanguage.PYTHON: {
                "setup": f"        # Setup {node.label} instance\n        self.{node.label.lower().replace(' ', '_')} = {node.label.replace(' ', '')}()",
                "test": f"        # Test basic {node.label} functionality\n        result = self.{node.label.lower().replace(' ', '_')}.process()\n        self.assertIsNotNone(result)",
                "teardown": f"        # Cleanup {node.label}\n        self.{node.label.lower().replace(' ', '_')} = None",
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "setup": f"        // Setup {node.label} instance\n        this.{node.label.toLowerCase().replace(' ', '')} = new {node.label.replace(' ', '')}();",
                "test": f"        // Test basic {node.label} functionality\n        const result = this.{node.label.toLowerCase().replace(' ', '')}.process();\n        expect(result).toBeDefined();",
                "teardown": f"        // Cleanup {node.label}\n        this.{node.label.toLowerCase().replace(' ', '')} = null;",
            },
            ProgrammingLanguage.JAVA: {
                "setup": f"        // Setup {node.label} instance\n        {node.label.replace(' ', '')} {node.label.toLowerCase().replace(' ', '')} = new {node.label.replace(' ', '')}();",
                "test": f"        // Test basic {node.label} functionality\n        Object result = {node.label.toLowerCase().replace(' ', '')}.process();\n        assertNotNull(result);",
                "teardown": f"        // Cleanup {node.label}\n        {node.label.toLowerCase().replace(' ', '')} = null;",
            },
        }

        template = test_templates.get(
            language, test_templates[ProgrammingLanguage.PYTHON]
        )

        return TestCase(
            name=f"test_{node.label.lower().replace(' ', '_')}_basic_functionality",
            description=f"Test basic functionality of {node.label}",
            test_type=TestType.UNIT,
            setup_code=template["setup"],
            test_code=template["test"],
            teardown_code=template["teardown"],
            assertions=[f"Verify {node.label} processes correctly"],
            related_acceptance_criteria=[],
        )

    def _generate_validation_test(
        self, node: Node, language: ProgrammingLanguage
    ) -> TestCase:
        """Generate validation test for a node."""
        test_templates = {
            ProgrammingLanguage.PYTHON: {
                "setup": f"        # Setup {node.label} with invalid data\n        self.{node.label.lower().replace(' ', '_')} = {node.label.replace(' ', '')}()",
                "test": f"        # Test {node.label} validation\n        with self.assertRaises(ValidationError):\n            self.{node.label.lower().replace(' ', '_')}.process(invalid_data)",
                "teardown": "",
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "setup": f"        // Setup {node.label} with invalid data\n        this.{node.label.toLowerCase().replace(' ', '')} = new {node.label.replace(' ', '')}();",
                "test": f"        // Test {node.label} validation\n        expect(() => {{\n            this.{node.label.toLowerCase().replace(' ', '')}.process(invalidData);\n        }}).toThrow();",
                "teardown": "",
            },
            ProgrammingLanguage.JAVA: {
                "setup": f"        // Setup {node.label} with invalid data\n        {node.label.replace(' ', '')} {node.label.toLowerCase().replace(' ', '')} = new {node.label.replace(' ', '')}();",
                "test": f"        // Test {node.label} validation\n        assertThrows(ValidationException.class, () -> {{\n            {node.label.toLowerCase().replace(' ', '')}.process(invalidData);\n        }});",
                "teardown": "",
            },
        }

        template = test_templates.get(
            language, test_templates[ProgrammingLanguage.PYTHON]
        )

        return TestCase(
            name=f"test_{node.label.lower().replace(' ', '_')}_validation",
            description=f"Test validation logic of {node.label}",
            test_type=TestType.UNIT,
            setup_code=template["setup"],
            test_code=template["test"],
            teardown_code=template["teardown"],
            assertions=[f"Verify {node.label} validates input correctly"],
            related_acceptance_criteria=[],
        )

    def _generate_error_handling_test(
        self, node: Node, language: ProgrammingLanguage
    ) -> TestCase:
        """Generate error handling test for a node."""
        test_templates = {
            ProgrammingLanguage.PYTHON: {
                "setup": f"        # Setup {node.label} for error scenario\n        self.{node.label.lower().replace(' ', '_')} = {node.label.replace(' ', '')}()",
                "test": f"        # Test {node.label} error handling\n        result = self.{node.label.lower().replace(' ', '_')}.handle_error()\n        self.assertIsInstance(result, ErrorResponse)",
                "teardown": "",
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "setup": f"        // Setup {node.label} for error scenario\n        this.{node.label.toLowerCase().replace(' ', '')} = new {node.label.replace(' ', '')}();",
                "test": f"        // Test {node.label} error handling\n        const result = this.{node.label.toLowerCase().replace(' ', '')}.handleError();\n        expect(result).toBeInstanceOf(ErrorResponse);",
                "teardown": "",
            },
            ProgrammingLanguage.JAVA: {
                "setup": f"        // Setup {node.label} for error scenario\n        {node.label.replace(' ', '')} {node.label.toLowerCase().replace(' ', '')} = new {node.label.replace(' ', '')}();",
                "test": f"        // Test {node.label} error handling\n        ErrorResponse result = {node.label.toLowerCase().replace(' ', '')}.handleError();\n        assertTrue(result instanceof ErrorResponse);",
                "teardown": "",
            },
        }

        template = test_templates.get(
            language, test_templates[ProgrammingLanguage.PYTHON]
        )

        return TestCase(
            name=f"test_{node.label.lower().replace(' ', '_')}_error_handling",
            description=f"Test error handling of {node.label}",
            test_type=TestType.UNIT,
            setup_code=template["setup"],
            test_code=template["test"],
            teardown_code=template["teardown"],
            assertions=[f"Verify {node.label} handles errors gracefully"],
            related_acceptance_criteria=[],
        )

    def _generate_acceptance_criteria_test(
        self, node: Node, criterion: AcceptanceCriterion, language: ProgrammingLanguage
    ) -> TestCase:
        """Generate test for specific acceptance criterion."""
        test_name = f"test_{node.label.lower().replace(' ', '_')}_ac_{criterion.id}"

        test_templates = {
            ProgrammingLanguage.PYTHON: {
                "setup": f"        # Setup for AC-{criterion.id}\n        self.{node.label.lower().replace(' ', '_')} = {node.label.replace(' ', '')}()",
                "test": f"        # Test AC-{criterion.id}: {criterion.description}\n        result = self.{node.label.lower().replace(' ', '_')}.validate_acceptance_criteria()\n        self.assertTrue(result)",
                "teardown": "",
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "setup": f"        // Setup for AC-{criterion.id}\n        this.{node.label.toLowerCase().replace(' ', '')} = new {node.label.replace(' ', '')}();",
                "test": f"        // Test AC-{criterion.id}: {criterion.description}\n        const result = this.{node.label.toLowerCase().replace(' ', '')}.validateAcceptanceCriteria();\n        expect(result).toBe(true);",
                "teardown": "",
            },
            ProgrammingLanguage.JAVA: {
                "setup": f"        // Setup for AC-{criterion.id}\n        {node.label.replace(' ', '')} {node.label.toLowerCase().replace(' ', '')} = new {node.label.replace(' ', '')}();",
                "test": f"        // Test AC-{criterion.id}: {criterion.description}\n        boolean result = {node.label.toLowerCase().replace(' ', '')}.validateAcceptanceCriteria();\n        assertTrue(result);",
                "teardown": "",
            },
        }

        template = test_templates.get(
            language, test_templates[ProgrammingLanguage.PYTHON]
        )

        return TestCase(
            name=test_name,
            description=f"Test acceptance criterion: {criterion.description}",
            test_type=TestType.UNIT,
            setup_code=template["setup"],
            test_code=template["test"],
            teardown_code=template["teardown"],
            assertions=[criterion.description],
            related_acceptance_criteria=[criterion.id],
        )

    def _generate_successful_interaction_test(
        self, source: Node, target: Node, edge: Edge, language: ProgrammingLanguage
    ) -> TestCase:
        """Generate successful interaction test."""
        test_templates = {
            ProgrammingLanguage.PYTHON: {
                "setup": f"        # Setup {source.label} and {target.label}\n        self.source = {source.label.replace(' ', '')}()\n        self.target = {target.label.replace(' ', '')}()",
                "test": f"        # Test successful {edge.relationship_type} interaction\n        result = self.source.{edge.relationship_type}(self.target)\n        self.assertTrue(result.success)",
                "teardown": "",
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "setup": f"        // Setup {source.label} and {target.label}\n        this.source = new {source.label.replace(' ', '')}();\n        this.target = new {target.label.replace(' ', '')}();",
                "test": f"        // Test successful {edge.relationship_type} interaction\n        const result = this.source.{edge.relationship_type}(this.target);\n        expect(result.success).toBe(true);",
                "teardown": "",
            },
            ProgrammingLanguage.JAVA: {
                "setup": f"        // Setup {source.label} and {target.label}\n        {source.label.replace(' ', '')} source = new {source.label.replace(' ', '')}();\n        {target.label.replace(' ', '')} target = new {target.label.replace(' ', '')}();",
                "test": f"        // Test successful {edge.relationship_type} interaction\n        Result result = source.{edge.relationship_type}(target);\n        assertTrue(result.isSuccess());",
                "teardown": "",
            },
        }

        template = test_templates.get(
            language, test_templates[ProgrammingLanguage.PYTHON]
        )

        return TestCase(
            name=f"test_{source.label.lower().replace(' ', '_')}_{edge.relationship_type}_{target.label.lower().replace(' ', '_')}_success",
            description=f"Test successful {edge.relationship_type} between {source.label} and {target.label}",
            test_type=TestType.INTEGRATION,
            setup_code=template["setup"],
            test_code=template["test"],
            teardown_code=template["teardown"],
            assertions=[
                f"Verify {source.label} can {edge.relationship_type} {target.label}"
            ],
            related_acceptance_criteria=[],
        )

    def _generate_interaction_failure_test(
        self, source: Node, target: Node, edge: Edge, language: ProgrammingLanguage
    ) -> TestCase:
        """Generate interaction failure test."""
        test_templates = {
            ProgrammingLanguage.PYTHON: {
                "setup": f"        # Setup {source.label} and {target.label} for failure\n        self.source = {source.label.replace(' ', '')}()\n        self.target = None  # Simulate failure",
                "test": f"        # Test {edge.relationship_type} failure handling\n        result = self.source.{edge.relationship_type}(self.target)\n        self.assertFalse(result.success)",
                "teardown": "",
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "setup": f"        // Setup {source.label} and {target.label} for failure\n        this.source = new {source.label.replace(' ', '')}();\n        this.target = null; // Simulate failure",
                "test": f"        // Test {edge.relationship_type} failure handling\n        const result = this.source.{edge.relationship_type}(this.target);\n        expect(result.success).toBe(false);",
                "teardown": "",
            },
            ProgrammingLanguage.JAVA: {
                "setup": f"        // Setup {source.label} and {target.label} for failure\n        {source.label.replace(' ', '')} source = new {source.label.replace(' ', '')}();\n        {target.label.replace(' ', '')} target = null; // Simulate failure",
                "test": f"        // Test {edge.relationship_type} failure handling\n        Result result = source.{edge.relationship_type}(target);\n        assertFalse(result.isSuccess());",
                "teardown": "",
            },
        }

        template = test_templates.get(
            language, test_templates[ProgrammingLanguage.PYTHON]
        )

        return TestCase(
            name=f"test_{source.label.lower().replace(' ', '_')}_{edge.relationship_type}_{target.label.lower().replace(' ', '_')}_failure",
            description=f"Test {edge.relationship_type} failure between {source.label} and {target.label}",
            test_type=TestType.INTEGRATION,
            setup_code=template["setup"],
            test_code=template["test"],
            teardown_code=template["teardown"],
            assertions=[
                f"Verify {source.label} handles {edge.relationship_type} failure gracefully"
            ],
            related_acceptance_criteria=[],
        )

    def _generate_happy_path_test(
        self, workflow: List[Node], language: ProgrammingLanguage
    ) -> TestCase:
        """Generate happy path E2E test."""
        workflow_name = "_to_".join(
            [node.label.lower().replace(" ", "_") for node in workflow[:3]]
        )

        test_templates = {
            ProgrammingLanguage.PYTHON: {
                "setup": "        # Setup complete workflow\n        self.workflow = WorkflowManager()",
                "test": f"        # Test complete {workflow[0].label} to {workflow[-1].label} workflow\n        result = self.workflow.execute_complete_flow()\n        self.assertTrue(result.success)",
                "teardown": "        # Cleanup workflow\n        self.workflow.cleanup()",
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "setup": "        // Setup complete workflow\n        this.workflow = new WorkflowManager();",
                "test": f"        // Test complete {workflow[0].label} to {workflow[-1].label} workflow\n        const result = this.workflow.executeCompleteFlow();\n        expect(result.success).toBe(true);",
                "teardown": "        // Cleanup workflow\n        this.workflow.cleanup();",
            },
            ProgrammingLanguage.JAVA: {
                "setup": "        // Setup complete workflow\n        WorkflowManager workflow = new WorkflowManager();",
                "test": f"        // Test complete {workflow[0].label} to {workflow[-1].label} workflow\n        Result result = workflow.executeCompleteFlow();\n        assertTrue(result.isSuccess());",
                "teardown": "        // Cleanup workflow\n        workflow.cleanup();",
            },
        }

        template = test_templates.get(
            language, test_templates[ProgrammingLanguage.PYTHON]
        )

        return TestCase(
            name=f"test_{workflow_name}_happy_path",
            description=f"Test complete workflow from {workflow[0].label} to {workflow[-1].label}",
            test_type=TestType.END_TO_END,
            setup_code=template["setup"],
            test_code=template["test"],
            teardown_code=template["teardown"],
            assertions=["Verify complete workflow executes successfully"],
            related_acceptance_criteria=[],
        )

    def _generate_error_path_test(
        self, workflow: List[Node], language: ProgrammingLanguage
    ) -> TestCase:
        """Generate error path E2E test."""
        workflow_name = "_to_".join(
            [node.label.lower().replace(" ", "_") for node in workflow[:3]]
        )

        test_templates = {
            ProgrammingLanguage.PYTHON: {
                "setup": "        # Setup workflow with error condition\n        self.workflow = WorkflowManager()\n        self.workflow.inject_error()",
                "test": f"        # Test {workflow[0].label} to {workflow[-1].label} error handling\n        result = self.workflow.execute_with_error()\n        self.assertFalse(result.success)\n        self.assertIsNotNone(result.error_message)",
                "teardown": "        # Cleanup workflow\n        self.workflow.cleanup()",
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "setup": "        // Setup workflow with error condition\n        this.workflow = new WorkflowManager();\n        this.workflow.injectError();",
                "test": f"        // Test {workflow[0].label} to {workflow[-1].label} error handling\n        const result = this.workflow.executeWithError();\n        expect(result.success).toBe(false);\n        expect(result.errorMessage).toBeDefined();",
                "teardown": "        // Cleanup workflow\n        this.workflow.cleanup();",
            },
            ProgrammingLanguage.JAVA: {
                "setup": "        // Setup workflow with error condition\n        WorkflowManager workflow = new WorkflowManager();\n        workflow.injectError();",
                "test": f"        // Test {workflow[0].label} to {workflow[-1].label} error handling\n        Result result = workflow.executeWithError();\n        assertFalse(result.isSuccess());\n        assertNotNull(result.getErrorMessage());",
                "teardown": "        // Cleanup workflow\n        workflow.cleanup();",
            },
        }

        template = test_templates.get(
            language, test_templates[ProgrammingLanguage.PYTHON]
        )

        return TestCase(
            name=f"test_{workflow_name}_error_path",
            description=f"Test error handling in workflow from {workflow[0].label} to {workflow[-1].label}",
            test_type=TestType.END_TO_END,
            setup_code=template["setup"],
            test_code=template["test"],
            teardown_code=template["teardown"],
            assertions=[f"Verify workflow handles errors gracefully"],
            related_acceptance_criteria=[],
        )

    # Helper methods for test file generation
    def _get_unit_test_imports(self, language: ProgrammingLanguage) -> List[str]:
        """Get imports for unit test files."""
        imports = {
            ProgrammingLanguage.PYTHON: [
                "import unittest",
                "from unittest.mock import Mock, patch",
                "import pytest",
            ],
            ProgrammingLanguage.JAVASCRIPT: [
                "const { describe, it, expect, beforeEach, afterEach } = require('@jest/globals');",
                "const { jest } = require('@jest/globals');",
            ],
            ProgrammingLanguage.JAVA: [
                "import org.junit.jupiter.api.Test;",
                "import org.junit.jupiter.api.BeforeEach;",
                "import org.junit.jupiter.api.AfterEach;",
                "import static org.junit.jupiter.api.Assertions.*;",
            ],
        }
        return imports.get(language, imports[ProgrammingLanguage.PYTHON])

    def _get_integration_test_imports(self, language: ProgrammingLanguage) -> List[str]:
        """Get imports for integration test files."""
        imports = {
            ProgrammingLanguage.PYTHON: [
                "import unittest",
                "from unittest.mock import Mock, patch",
                "import pytest",
                "import requests",
            ],
            ProgrammingLanguage.JAVASCRIPT: [
                "const { describe, it, expect, beforeEach, afterEach } = require('@jest/globals');",
                "const axios = require('axios');",
            ],
            ProgrammingLanguage.JAVA: [
                "import org.junit.jupiter.api.Test;",
                "import org.junit.jupiter.api.BeforeEach;",
                "import org.junit.jupiter.api.AfterEach;",
                "import static org.junit.jupiter.api.Assertions.*;",
                "import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;",
            ],
        }
        return imports.get(language, imports[ProgrammingLanguage.PYTHON])

    def _get_e2e_test_imports(self, language: ProgrammingLanguage) -> List[str]:
        """Get imports for E2E test files."""
        imports = {
            ProgrammingLanguage.PYTHON: [
                "import unittest",
                "from selenium import webdriver",
                "import pytest",
                "import requests",
            ],
            ProgrammingLanguage.JAVASCRIPT: [
                "const { describe, it, expect, beforeEach, afterEach } = require('@jest/globals');",
                "const puppeteer = require('puppeteer');",
            ],
            ProgrammingLanguage.JAVA: [
                "import org.junit.jupiter.api.Test;",
                "import org.junit.jupiter.api.BeforeEach;",
                "import org.junit.jupiter.api.AfterEach;",
                "import static org.junit.jupiter.api.Assertions.*;",
                "import org.openqa.selenium.WebDriver;",
            ],
        }
        return imports.get(language, imports[ProgrammingLanguage.PYTHON])

    def _get_unit_test_setup(self, language: ProgrammingLanguage) -> str:
        """Get setup code for unit tests."""
        setup = {
            ProgrammingLanguage.PYTHON: "class TestComponents(unittest.TestCase):\n    def setUp(self):\n        # Setup test fixtures\n        pass",
            ProgrammingLanguage.JAVASCRIPT: "describe('Component Tests', () => {\n    beforeEach(() => {\n        // Setup test fixtures\n    });",
            ProgrammingLanguage.JAVA: "public class ComponentTests {\n    @BeforeEach\n    void setUp() {\n        // Setup test fixtures\n    }",
        }
        return setup.get(language, setup[ProgrammingLanguage.PYTHON])

    def _get_integration_test_setup(self, language: ProgrammingLanguage) -> str:
        """Get setup code for integration tests."""
        setup = {
            ProgrammingLanguage.PYTHON: "class TestIntegrations(unittest.TestCase):\n    def setUp(self):\n        # Setup integration test environment\n        pass",
            ProgrammingLanguage.JAVASCRIPT: "describe('Integration Tests', () => {\n    beforeEach(() => {\n        // Setup integration test environment\n    });",
            ProgrammingLanguage.JAVA: "public class IntegrationTests {\n    @BeforeEach\n    void setUp() {\n        // Setup integration test environment\n    }",
        }
        return setup.get(language, setup[ProgrammingLanguage.PYTHON])

    def _get_e2e_test_setup(self, language: ProgrammingLanguage) -> str:
        """Get setup code for E2E tests."""
        setup = {
            ProgrammingLanguage.PYTHON: "class TestEndToEnd(unittest.TestCase):\n    def setUp(self):\n        # Setup E2E test environment\n        self.driver = webdriver.Chrome()",
            ProgrammingLanguage.JAVASCRIPT: "describe('End-to-End Tests', () => {\n    let browser, page;\n    beforeEach(async () => {\n        browser = await puppeteer.launch();\n        page = await browser.newPage();\n    });",
            ProgrammingLanguage.JAVA: "public class EndToEndTests {\n    private WebDriver driver;\n    @BeforeEach\n    void setUp() {\n        // Setup E2E test environment\n        driver = new ChromeDriver();\n    }",
        }
        return setup.get(language, setup[ProgrammingLanguage.PYTHON])

    def _get_unit_test_helpers(self, language: ProgrammingLanguage) -> List[str]:
        """Get helper methods for unit tests."""
        helpers = {
            ProgrammingLanguage.PYTHON: [
                '    def create_mock_data(self):\n        """Create mock data for testing."""\n        return {\'test\': \'data\'}',
                '    def assert_valid_response(self, response):\n        """Assert response is valid."""\n        self.assertIsNotNone(response)\n        self.assertTrue(hasattr(response, \'success\'))',
            ],
            ProgrammingLanguage.JAVASCRIPT: [
                "    function createMockData() {\n        // Create mock data for testing\n        return { test: 'data' };\n    }",
                "    function assertValidResponse(response) {\n        // Assert response is valid\n        expect(response).toBeDefined();\n        expect(response).toHaveProperty('success');\n    }",
            ],
            ProgrammingLanguage.JAVA: [
                "    private Object createMockData() {\n        // Create mock data for testing\n        return new Object();\n    }",
                "    private void assertValidResponse(Object response) {\n        // Assert response is valid\n        assertNotNull(response);\n    }",
            ],
        }
        return helpers.get(language, helpers[ProgrammingLanguage.PYTHON])

    def _get_integration_test_helpers(self, language: ProgrammingLanguage) -> List[str]:
        """Get helper methods for integration tests."""
        helpers = {
            ProgrammingLanguage.PYTHON: [
                '    def setup_test_database(self):\n        """Setup test database."""\n        pass',
                '    def cleanup_test_database(self):\n        """Cleanup test database."""\n        pass',
            ],
            ProgrammingLanguage.JAVASCRIPT: [
                "    function setupTestDatabase() {\n        // Setup test database\n    }",
                "    function cleanupTestDatabase() {\n        // Cleanup test database\n    }",
            ],
            ProgrammingLanguage.JAVA: [
                "    private void setupTestDatabase() {\n        // Setup test database\n    }",
                "    private void cleanupTestDatabase() {\n        // Cleanup test database\n    }",
            ],
        }
        return helpers.get(language, helpers[ProgrammingLanguage.PYTHON])

    def _get_e2e_test_helpers(self, language: ProgrammingLanguage) -> List[str]:
        """Get helper methods for E2E tests."""
        helpers = {
            ProgrammingLanguage.PYTHON: [
                '    def navigate_to_page(self, url):\n        """Navigate to a page."""\n        self.driver.get(url)',
                '    def wait_for_element(self, selector):\n        """Wait for element to appear."""\n        from selenium.webdriver.support.ui import WebDriverWait\n        from selenium.webdriver.support import expected_conditions as EC\n        from selenium.webdriver.common.by import By\n        return WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))',
            ],
            ProgrammingLanguage.JAVASCRIPT: [
                "    async function navigateToPage(url) {\n        // Navigate to a page\n        await page.goto(url);\n    }",
                "    async function waitForElement(selector) {\n        // Wait for element to appear\n        await page.waitForSelector(selector);\n    }",
            ],
            ProgrammingLanguage.JAVA: [
                "    private void navigateToPage(String url) {\n        // Navigate to a page\n        driver.get(url);\n    }",
                "    private WebElement waitForElement(String selector) {\n        // Wait for element to appear\n        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));\n        return wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector(selector)));\n    }",
            ],
        }
        return helpers.get(language, helpers[ProgrammingLanguage.PYTHON])

    def _get_unit_test_filename(self, language: ProgrammingLanguage) -> str:
        """Get filename for unit test file."""
        filenames = {
            ProgrammingLanguage.PYTHON: "test_components.py",
            ProgrammingLanguage.JAVASCRIPT: "components.test.js",
            ProgrammingLanguage.JAVA: "ComponentTests.java",
        }
        return filenames.get(language, filenames[ProgrammingLanguage.PYTHON])

    def _get_integration_test_filename(self, language: ProgrammingLanguage) -> str:
        """Get filename for integration test file."""
        filenames = {
            ProgrammingLanguage.PYTHON: "test_integrations.py",
            ProgrammingLanguage.JAVASCRIPT: "integrations.test.js",
            ProgrammingLanguage.JAVA: "IntegrationTests.java",
        }
        return filenames.get(language, filenames[ProgrammingLanguage.PYTHON])

    def _get_e2e_test_filename(self, language: ProgrammingLanguage) -> str:
        """Get filename for E2E test file."""
        filenames = {
            ProgrammingLanguage.PYTHON: "test_e2e.py",
            ProgrammingLanguage.JAVASCRIPT: "e2e.test.js",
            ProgrammingLanguage.JAVA: "EndToEndTests.java",
        }
        return filenames.get(language, filenames[ProgrammingLanguage.PYTHON])

    def _generate_test_file_content(
        self,
        test_type: str,
        imports: List[str],
        setup_code: str,
        test_cases: List[TestCase],
        helper_methods: List[str],
        language: ProgrammingLanguage,
    ) -> str:
        """Generate complete test file content."""
        content_parts = []

        # Add file header
        content_parts.extend(
            [
                f"# Generated {test_type} tests",
                f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
            ]
        )

        # Add imports
        content_parts.extend(imports)
        content_parts.append("")

        # Add setup code
        content_parts.append(setup_code)
        content_parts.append("")

        # Add test cases
        for test_case in test_cases:
            content_parts.extend(self._format_test_case(test_case, language))
            content_parts.append("")

        # Add helper methods
        if helper_methods:
            content_parts.extend(helper_methods)
            content_parts.append("")

        # Add closing for class-based languages
        if language in [ProgrammingLanguage.PYTHON, ProgrammingLanguage.JAVA]:
            content_parts.append("")
        elif language == ProgrammingLanguage.JAVASCRIPT:
            content_parts.append("});")

        return "\n".join(content_parts)

    def _format_test_case(
        self, test_case: TestCase, language: ProgrammingLanguage
    ) -> List[str]:
        """Format a test case for the specific language."""
        if language == ProgrammingLanguage.PYTHON:
            return [
                f"    def {test_case.name}(self):",
                f'        """',
                f"        {test_case.description}",
                f'        """',
                test_case.setup_code,
                test_case.test_code,
                test_case.teardown_code,
            ]
        elif language == ProgrammingLanguage.JAVASCRIPT:
            return [
                f"    it('{test_case.description}', () => {{",
                test_case.setup_code,
                test_case.test_code,
                test_case.teardown_code,
                "    });",
            ]
        elif language == ProgrammingLanguage.JAVA:
            return [
                "    @Test",
                f"    void {test_case.name}() {{",
                f"        // {test_case.description}",
                test_case.setup_code,
                test_case.test_code,
                test_case.teardown_code,
                "    }",
            ]
        else:
            return [f"// {test_case.name}: {test_case.description}"]

    def _generate_setup_instructions(self, language: ProgrammingLanguage) -> str:
        """Generate setup instructions for the test scaffold."""
        instructions = {
            ProgrammingLanguage.PYTHON: """# Test Setup Instructions

## Prerequisites
- Python 3.8+
- pip package manager

## Installation
1. Install test dependencies:
   ```bash
   pip install -r test-requirements.txt
   ```

2. Setup test environment:
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

## Configuration
- Update test configuration in `test_config.py`
- Set environment variables for test database
- Configure mock services as needed
""",
            ProgrammingLanguage.JAVASCRIPT: """# Test Setup Instructions

## Prerequisites
- Node.js 16+
- npm or yarn package manager

## Installation
1. Install test dependencies:
   ```bash
   npm install --save-dev jest @jest/globals puppeteer
   ```

2. Setup test environment:
   ```bash
   npm run test:setup
   ```

## Configuration
- Update Jest configuration in `jest.config.js`
- Set environment variables in `.env.test`
- Configure test database connection
""",
            ProgrammingLanguage.JAVA: """# Test Setup Instructions

## Prerequisites
- Java 11+
- Maven or Gradle build tool

## Installation
1. Add test dependencies to `pom.xml` or `build.gradle`
2. Setup test environment:
   ```bash
   mvn test-compile
   ```

## Configuration
- Update test configuration in `application-test.properties`
- Configure test database connection
- Setup mock services as needed
""",
        }
        return instructions.get(language, instructions[ProgrammingLanguage.PYTHON])

    def _generate_run_instructions(self, language: ProgrammingLanguage) -> str:
        """Generate run instructions for the test scaffold."""
        instructions = {
            ProgrammingLanguage.PYTHON: """# Running Tests

## All Tests
```bash
python -m pytest
```

## Specific Test Types
```bash
# Unit tests only
python -m pytest test_components.py

# Integration tests only
python -m pytest test_integrations.py

# E2E tests only
python -m pytest test_e2e.py
```

## With Coverage
```bash
python -m pytest --cov=src --cov-report=html
```

## Parallel Execution
```bash
python -m pytest -n auto
```
""",
            ProgrammingLanguage.JAVASCRIPT: """# Running Tests

## All Tests
```bash
npm test
```

## Specific Test Types
```bash
# Unit tests only
npm run test:unit

# Integration tests only
npm run test:integration

# E2E tests only
npm run test:e2e
```

## With Coverage
```bash
npm run test:coverage
```

## Watch Mode
```bash
npm run test:watch
```
""",
            ProgrammingLanguage.JAVA: """# Running Tests

## All Tests
```bash
mvn test
```

## Specific Test Types
```bash
# Unit tests only
mvn test -Dtest=ComponentTests

# Integration tests only
mvn test -Dtest=IntegrationTests

# E2E tests only
mvn test -Dtest=EndToEndTests
```

## With Coverage
```bash
mvn test jacoco:report
```

## Parallel Execution
```bash
mvn test -DforkCount=4
```
""",
        }
        return instructions.get(language, instructions[ProgrammingLanguage.PYTHON])

    def _get_test_dependencies(self, language: ProgrammingLanguage) -> List[str]:
        """Get test dependencies for the language."""
        dependencies = {
            ProgrammingLanguage.PYTHON: [
                "pytest>=7.0.0",
                "pytest-cov>=4.0.0",
                "pytest-xdist>=3.0.0",
                "selenium>=4.0.0",
                "requests>=2.28.0",
                "mock>=4.0.0",
            ],
            ProgrammingLanguage.JAVASCRIPT: [
                "jest>=29.0.0",
                "@jest/globals>=29.0.0",
                "puppeteer>=19.0.0",
                "axios>=1.0.0",
                "supertest>=6.0.0",
            ],
            ProgrammingLanguage.JAVA: [
                "org.junit.jupiter:junit-jupiter:5.9.0",
                "org.mockito:mockito-core:4.6.0",
                "org.springframework.boot:spring-boot-starter-test:2.7.0",
                "org.seleniumhq.selenium:selenium-java:4.5.0",
                "org.testcontainers:junit-jupiter:1.17.0",
            ],
        }
        return dependencies.get(language, dependencies[ProgrammingLanguage.PYTHON])

    def _identify_workflows(self, diagram_data: DiagramData) -> List[List[Node]]:
        """Identify workflows in the diagram for E2E testing."""
        workflows = []

        # Simple workflow identification - find chains of connected nodes
        visited = set()
        for node in diagram_data.nodes:
            if node.id not in visited:
                workflow = self._trace_workflow_from_node(
                    node, diagram_data.edges, visited
                )
                if len(workflow) > 1:
                    workflows.append(workflow)

        return workflows[:3]  # Limit to top 3 workflows

    def _trace_workflow_from_node(
        self, start_node: Node, edges: List[Edge], visited: set
    ) -> List[Node]:
        """Trace a workflow starting from a node."""
        workflow = [start_node]
        visited.add(start_node.id)

        # Find next node in workflow
        outgoing = [edge for edge in edges if edge.source_id == start_node.id]
        for edge in outgoing:
            target_node = self._find_node_by_id(
                [n for n in workflow if n.id != start_node.id], edge.target_id
            )
            if target_node and target_node.id not in visited:
                workflow.extend(
                    self._trace_workflow_from_node(target_node, edges, visited)
                )
                break  # Only follow one path for simplicity

        return workflow
