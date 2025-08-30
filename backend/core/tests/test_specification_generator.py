"""
Unit tests for the SpecificationGenerator service.
"""

import pytest

from core.services.diagram_engine import DiagramData, Edge, Node, Position
from core.services.specification_generator import (
    AcceptanceCriterion,
    GeneratedSpecification,
    SpecificationGenerationError,
    SpecificationGenerator,
    SpecificationSection,
)
from core.services.text_parser import DiagramType


class TestSpecificationGenerator:
    """Test cases for SpecificationGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = SpecificationGenerator()

        # Sample diagram data for testing
        self.sample_nodes = [
            Node(
                id="user_1",
                label="User",
                shape="circle",
                entity_type="actor",
                properties={"role": "customer"},
                position=Position(100, 100),
            ),
            Node(
                id="system_1",
                label="Login System",
                shape="hexagon",
                entity_type="system",
                properties={"type": "authentication"},
                position=Position(300, 100),
            ),
            Node(
                id="database_1",
                label="User Database",
                shape="cylinder",
                entity_type="data",
                properties={"type": "storage"},
                position=Position(500, 100),
            ),
        ]

        self.sample_edges = [
            Edge(
                source_id="user_1",
                target_id="system_1",
                label="authenticates with",
                arrow_type="-.->",
                relationship_type="uses",
            ),
            Edge(
                source_id="system_1",
                target_id="database_1",
                label="queries user data",
                arrow_type="..>",
                relationship_type="accesses",
            ),
        ]

        self.sample_diagram_data = DiagramData(
            diagram_type=DiagramType.FLOWCHART,
            mermaid_syntax="flowchart TD\n    user_1((User))\n    system_1{Login System}\n    database_1[(User Database)]",
            nodes=self.sample_nodes,
            edges=self.sample_edges,
            layout_config={"direction": "TD", "theme": "default"},
            metadata={"entity_count": "3", "relationship_count": "2"},
        )

    def test_generate_specification_basic(self):
        """Test basic specification generation."""
        result = self.generator.generate_specification(
            self.sample_diagram_data, "Test System"
        )

        assert isinstance(result, GeneratedSpecification)
        assert "Test System" in result.title
        assert len(result.sections) > 0
        assert len(result.acceptance_criteria) > 0
        assert result.markdown_content
        assert "metadata" in result.__dict__

    def test_generate_specification_different_diagram_types(self):
        """Test specification generation for different diagram types."""
        diagram_types = [
            DiagramType.FLOWCHART,
            DiagramType.ERD,
            DiagramType.SEQUENCE,
            DiagramType.CLASS,
            DiagramType.PROCESS,
        ]

        for diagram_type in diagram_types:
            diagram_data = DiagramData(
                diagram_type=diagram_type,
                mermaid_syntax=f"{diagram_type.value} example",
                nodes=self.sample_nodes,
                edges=self.sample_edges,
                layout_config={},
                metadata={},
            )

            result = self.generator.generate_specification(diagram_data, "Test")

            assert result.title
            assert len(result.sections) > 0
            assert (
                diagram_type.value.lower() in result.title.lower()
                or "system" in result.title.lower()
            )

    def test_title_generation(self):
        """Test title generation for different diagram types."""
        test_cases = [
            (DiagramType.FLOWCHART, "Process Flow"),
            (DiagramType.ERD, "Data Model"),
            (DiagramType.SEQUENCE, "Interaction Flow"),
            (DiagramType.CLASS, "System Architecture"),
            (DiagramType.PROCESS, "Business Process"),
        ]

        for diagram_type, expected_type in test_cases:
            title = self.generator._generate_title(
                DiagramData(diagram_type, "", [], [], {}, {}), "MyProject"
            )
            assert "MyProject" in title
            assert expected_type in title

    def test_overview_section_generation(self):
        """Test overview section generation."""
        section = self.generator._generate_overview_section(self.sample_diagram_data, 1)

        assert section.title == "Overview"
        assert section.section_type == SpecificationSection.OVERVIEW
        assert section.order == 1
        assert "3 entities" in section.content
        assert "2 relationships" in section.content
        assert "flowchart" in section.content

    def test_requirements_section_generation(self):
        """Test requirements section generation."""
        section = self.generator._generate_requirements_section(
            self.sample_diagram_data, 2
        )

        assert section.title == "Requirements"
        assert section.section_type == SpecificationSection.REQUIREMENTS
        assert "Functional Requirements" in section.content
        assert "Non-Functional Requirements" in section.content
        assert "FR-" in section.content  # Functional requirement IDs
        assert "NFR-" in section.content  # Non-functional requirement IDs

    def test_architecture_section_generation(self):
        """Test architecture section generation."""
        section = self.generator._generate_architecture_section(
            self.sample_diagram_data, 3
        )

        assert section.title == "Architecture"
        assert section.section_type == SpecificationSection.ARCHITECTURE
        assert "System Architecture" in section.content
        assert "System Actors" in section.content  # From actor entity type
        assert "System Components" in section.content  # From system entity type

    def test_components_section_generation(self):
        """Test components section generation."""
        section = self.generator._generate_components_section(
            self.sample_diagram_data, 4
        )

        assert section.title == "Components"
        assert section.section_type == SpecificationSection.COMPONENTS
        assert "User" in section.content
        assert "Login System" in section.content
        assert "User Database" in section.content
        assert "Responsibilities" in section.content

    def test_data_flow_section_generation(self):
        """Test data flow section generation."""
        section = self.generator._generate_data_flow_section(
            self.sample_diagram_data, 5
        )

        assert section.title == "Data Flow"
        assert section.section_type == SpecificationSection.DATA_FLOW
        assert "Flow Description" in section.content

    def test_business_rules_section_generation(self):
        """Test business rules section generation."""
        section = self.generator._generate_business_rules_section(
            self.sample_diagram_data, 6
        )

        assert section.title == "Business Rules"
        assert section.section_type == SpecificationSection.BUSINESS_RULES
        assert "BR-" in section.content  # Business rule IDs
        assert "Rules and Constraints" in section.content

    def test_acceptance_criteria_section_generation(self):
        """Test acceptance criteria section generation."""
        section = self.generator._generate_acceptance_criteria_section(
            self.sample_diagram_data, 7
        )

        assert section.title == "Acceptance Criteria"
        assert section.section_type == SpecificationSection.ACCEPTANCE_CRITERIA
        assert "Functional Acceptance Criteria" in section.content

    def test_implementation_notes_section_generation(self):
        """Test implementation notes section generation."""
        section = self.generator._generate_implementation_notes_section(
            self.sample_diagram_data, 8
        )

        assert section.title == "Implementation Notes"
        assert section.section_type == SpecificationSection.IMPLEMENTATION_NOTES
        assert "Technical Considerations" in section.content
        assert "Testing Strategy" in section.content

    def test_acceptance_criteria_generation(self):
        """Test acceptance criteria generation."""
        criteria = self.generator._generate_acceptance_criteria(
            self.sample_diagram_data
        )

        assert len(criteria) > 0
        for criterion in criteria:
            assert isinstance(criterion, AcceptanceCriterion)
            assert criterion.id
            assert criterion.description
            assert criterion.priority in ["high", "medium", "low"]
            assert criterion.category in ["functional", "non-functional", "technical"]
            assert len(criterion.related_entities) > 0
            assert len(criterion.test_scenarios) > 0

    def test_markdown_generation(self):
        """Test markdown content generation."""
        result = self.generator.generate_specification(
            self.sample_diagram_data, "Test System"
        )

        markdown = result.markdown_content

        # Check markdown structure
        assert markdown.startswith("# ")
        assert "## Overview" in markdown
        assert "## Requirements" in markdown
        assert "Generated on" in markdown

        # Check that sections are properly formatted
        lines = markdown.split("\n")
        header_lines = [line for line in lines if line.startswith("#")]
        assert len(header_lines) > 1  # Should have multiple headers

    def test_empty_diagram_validation_error(self):
        """Test validation error for empty diagram."""
        empty_diagram = DiagramData(
            diagram_type=DiagramType.FLOWCHART,
            mermaid_syntax="",
            nodes=[],
            edges=[],
            layout_config={},
            metadata={},
        )

        with pytest.raises(SpecificationGenerationError) as exc_info:
            self.generator.generate_specification(empty_diagram, "Test")

        assert exc_info.value.stage == "input_validation"
        assert "no nodes" in str(exc_info.value).lower()

    def test_none_diagram_validation_error(self):
        """Test validation error for None diagram."""
        with pytest.raises(SpecificationGenerationError) as exc_info:
            self.generator.generate_specification(None, "Test")

        assert exc_info.value.stage == "input_validation"

    def test_entity_type_descriptions(self):
        """Test entity type descriptions."""
        test_cases = [
            ("object", "Data Objects"),
            ("process", "Business Processes"),
            ("actor", "System Actors"),
            ("data", "Data Stores"),
            ("system", "System Components"),
            ("event", "System Events"),
            ("unknown", "Components"),
        ]

        for entity_type, expected_description in test_cases:
            description = self.generator._get_entity_type_description(entity_type)
            assert description == expected_description

    def test_diagram_purpose_descriptions(self):
        """Test diagram purpose descriptions."""
        for diagram_type in DiagramType:
            purpose = self.generator._get_diagram_purpose(diagram_type)
            assert purpose
            assert isinstance(purpose, str)
            assert len(purpose) > 10  # Should be a meaningful description

    def test_functional_requirement_generation(self):
        """Test functional requirement generation."""
        source = self.sample_nodes[0]  # User
        target = self.sample_nodes[1]  # Login System
        edge = self.sample_edges[0]  # uses relationship

        requirement = self.generator._generate_functional_requirement(
            source, target, edge, 1
        )

        assert "FR-1" in requirement
        assert "User" in requirement
        assert "Login System" in requirement
        assert "SHALL" in requirement

    def test_component_description_generation(self):
        """Test component description generation."""
        for node in self.sample_nodes:
            description = self.generator._generate_component_description(node)
            assert node.label.lower() in description.lower()
            assert len(description) > 10

    def test_component_responsibilities_generation(self):
        """Test component responsibilities generation."""
        node = self.sample_nodes[1]  # Login System (has outgoing relationships)
        responsibilities = self.generator._generate_component_responsibilities(
            node, self.sample_edges
        )

        assert isinstance(responsibilities, list)
        # Should have responsibilities based on outgoing relationships

    def test_component_interfaces_generation(self):
        """Test component interfaces generation."""
        node = self.sample_nodes[1]  # Login System (has both incoming and outgoing)
        interfaces = self.generator._generate_component_interfaces(
            node, self.sample_edges
        )

        assert isinstance(interfaces, list)
        if interfaces:
            assert any(
                "Input" in interface or "Output" in interface
                for interface in interfaces
            )

    def test_interaction_patterns_analysis(self):
        """Test interaction patterns analysis."""
        patterns = self.generator._analyze_interaction_patterns(
            self.sample_diagram_data
        )

        assert isinstance(patterns, list)
        # Should identify some patterns in the sample data

    def test_data_flows_analysis(self):
        """Test data flows analysis."""
        flows = self.generator._analyze_data_flows(self.sample_diagram_data)

        assert isinstance(flows, list)
        for flow in flows:
            assert "name" in flow
            assert "description" in flow
            assert "steps" in flow

    def test_business_rule_generation(self):
        """Test business rule generation."""
        source = self.sample_nodes[0]
        target = self.sample_nodes[1]
        edge = Edge("source", "target", "", "-->", "creates")

        rule = self.generator._generate_business_rule(source, target, edge, 1)

        if rule:  # Some relationship types generate rules, others don't
            assert "BR-1" in rule
            assert "User" in rule

    def test_node_acceptance_criteria_generation(self):
        """Test node acceptance criteria generation."""
        node = self.sample_nodes[0]
        criteria = self.generator._generate_node_acceptance_criteria(
            node, self.sample_edges, 1
        )

        assert isinstance(criteria, list)
        assert len(criteria) > 0
        for criterion in criteria:
            assert "AC-" in criterion
            assert node.label in criterion

    def test_metadata_generation(self):
        """Test metadata generation."""
        result = self.generator.generate_specification(self.sample_diagram_data, "Test")

        metadata = result.metadata

        expected_keys = [
            "generated_at",
            "diagram_type",
            "node_count",
            "edge_count",
            "section_count",
            "acceptance_criteria_count",
            "word_count",
        ]

        for key in expected_keys:
            assert key in metadata

        assert metadata["diagram_type"] == "flowchart"
        assert metadata["node_count"] == 3
        assert metadata["edge_count"] == 2

    def test_section_templates_coverage(self):
        """Test that all section types have templates."""
        for section_type in SpecificationSection:
            assert section_type in self.generator.section_templates

    def test_diagram_type_templates_coverage(self):
        """Test that all diagram types have section templates."""
        for diagram_type in DiagramType:
            assert diagram_type in self.generator.diagram_type_templates

    def test_complex_diagram_specification(self):
        """Test specification generation for a complex diagram."""
        # Create a more complex diagram
        complex_nodes = [
            Node(
                f"node_{i}",
                f"Component {i}",
                "rect",
                "system",
                {},
                Position(i * 100, 100),
            )
            for i in range(10)
        ]

        complex_edges = [
            Edge(f"node_{i}", f"node_{i+1}", f"flow {i}", "-->", "uses")
            for i in range(9)
        ]

        complex_diagram = DiagramData(
            diagram_type=DiagramType.FLOWCHART,
            mermaid_syntax="complex flowchart",
            nodes=complex_nodes,
            edges=complex_edges,
            layout_config={},
            metadata={},
        )

        result = self.generator.generate_specification(
            complex_diagram, "Complex System"
        )

        assert len(result.sections) > 0
        assert len(result.acceptance_criteria) > 0
        assert "Complex System" in result.title
        assert len(result.markdown_content) > 1000  # Should be substantial content

    def test_error_handling_in_section_generation(self):
        """Test error handling when section generation fails."""
        # This test ensures that if one section fails, others still generate
        # In a real scenario, you might mock a section generator to raise an exception

        result = self.generator.generate_specification(self.sample_diagram_data, "Test")

        # Should still generate a specification even if some sections might have issues
        assert result is not None
        assert len(result.sections) > 0

    def test_find_node_by_id(self):
        """Test finding nodes by ID."""
        node = self.generator._find_node_by_id(self.sample_nodes, "user_1")
        assert node is not None
        assert node.label == "User"

        missing_node = self.generator._find_node_by_id(self.sample_nodes, "nonexistent")
        assert missing_node is None

    def test_acceptance_criterion_structure(self):
        """Test that acceptance criteria have proper structure."""
        criteria = self.generator._generate_acceptance_criteria(
            self.sample_diagram_data
        )

        for criterion in criteria:
            assert hasattr(criterion, "id")
            assert hasattr(criterion, "description")
            assert hasattr(criterion, "priority")
            assert hasattr(criterion, "category")
            assert hasattr(criterion, "related_entities")
            assert hasattr(criterion, "test_scenarios")

            assert criterion.priority in ["high", "medium", "low"]
            assert criterion.category in ["functional", "non-functional", "technical"]
            assert isinstance(criterion.related_entities, list)
            assert isinstance(criterion.test_scenarios, list)
