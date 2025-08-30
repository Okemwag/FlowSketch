"""
Unit tests for the DiagramEngine service.
"""

import pytest

from core.services.diagram_engine import DiagramData, DiagramEngine, Edge, Node
from core.services.text_parser import (
    DiagramType,
    Entity,
    EntityType,
    ParsedContent,
    Relationship,
)


class TestDiagramEngine:
    """Test cases for DiagramEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DiagramEngine()

        # Sample entities for testing
        self.sample_entities = [
            Entity(
                name="User",
                type=EntityType.ACTOR,
                properties={"role": "customer"},
                confidence=0.9,
                start_pos=0,
                end_pos=4,
            ),
            Entity(
                name="Login System",
                type=EntityType.SYSTEM,
                properties={"type": "authentication"},
                confidence=0.8,
                start_pos=5,
                end_pos=17,
            ),
            Entity(
                name="Database",
                type=EntityType.DATA,
                properties={"type": "storage"},
                confidence=0.85,
                start_pos=18,
                end_pos=26,
            ),
        ]

        # Sample relationships for testing
        self.sample_relationships = [
            Relationship(
                source="User",
                target="Login System",
                type="uses",
                label="authenticates with",
                confidence=0.9,
            ),
            Relationship(
                source="Login System",
                target="Database",
                type="accesses",
                label="queries user data",
                confidence=0.8,
            ),
        ]

        # Sample parsed content
        self.sample_content = ParsedContent(
            entities=self.sample_entities,
            relationships=self.sample_relationships,
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={
                "flowchart": 0.8,
                "sequence": 0.6,
                "erd": 0.4,
            },
            confidence=0.75,
            raw_text="User uses Login System to access Database",
        )

    def test_generate_diagram_basic(self):
        """Test basic diagram generation."""
        result = self.engine.generate_diagram(self.sample_content)

        assert isinstance(result, DiagramData)
        assert result.diagram_type == DiagramType.FLOWCHART
        assert len(result.nodes) == 3
        assert len(result.edges) == 2
        assert result.mermaid_syntax.startswith("flowchart TD")
        assert "metadata" in result.__dict__

    def test_generate_nodes_from_entities(self):
        """Test node generation from entities."""
        nodes = self.engine._generate_nodes(self.sample_entities)

        assert len(nodes) == 3

        # Check User node
        user_node = next(node for node in nodes if "User" in node.label)
        assert user_node.entity_type == "actor"
        assert user_node.shape == "circle"

        # Check Login System node
        system_node = next(node for node in nodes if "Login System" in node.label)
        assert system_node.entity_type == "system"
        assert system_node.shape == "hexagon"

        # Check Database node
        db_node = next(node for node in nodes if "Database" in node.label)
        assert db_node.entity_type == "data"
        assert db_node.shape == "cylinder"

    def test_generate_edges_from_relationships(self):
        """Test edge generation from relationships."""
        # First generate nodes to populate node_id_map
        self.engine._generate_nodes(self.sample_entities)

        edges = self.engine._generate_edges(self.sample_relationships)

        assert len(edges) == 2

        # Check first edge
        first_edge = edges[0]
        assert first_edge.relationship_type == "uses"
        assert first_edge.label == "authenticates with"
        assert (
            first_edge.arrow_type == "-.->"
        ), f"Expected '-.->',  got '{first_edge.arrow_type}'"

        # Check second edge
        second_edge = edges[1]
        assert second_edge.relationship_type == "accesses"
        assert second_edge.label == "queries user data"
        assert second_edge.arrow_type == "..>"

    def test_flowchart_syntax_generation(self):
        """Test Mermaid flowchart syntax generation."""
        result = self.engine.generate_diagram(self.sample_content)

        syntax = result.mermaid_syntax
        lines = syntax.split("\n")

        # Check header
        assert lines[0] == "flowchart TD"

        # Check that nodes are defined
        node_lines = [
            line
            for line in lines
            if line.strip()
            and not line.startswith("    classDef")
            and not line.startswith("    class")
        ]
        assert (
            len([line for line in node_lines if "((User))" in line or "[User]" in line])
            >= 1
        )

        # Check that edges are defined
        edge_lines = [
            line for line in lines if "-.->|" in line or "..>|" in line or "-->" in line
        ]
        assert len(edge_lines) >= 2

    def test_erd_syntax_generation(self):
        """Test ERD syntax generation."""
        # Create ERD-specific content
        erd_content = ParsedContent(
            entities=self.sample_entities,
            relationships=self.sample_relationships,
            suggested_diagram_type=DiagramType.ERD,
            diagram_type_suggestions={"erd": 0.9},
            confidence=0.8,
            raw_text="User has Database records",
        )

        result = self.engine.generate_diagram(erd_content)

        assert result.diagram_type == DiagramType.ERD
        assert result.mermaid_syntax.startswith("erDiagram")

        # Check for entity definitions
        assert "{" in result.mermaid_syntax
        assert "}" in result.mermaid_syntax

    def test_sequence_syntax_generation(self):
        """Test sequence diagram syntax generation."""
        sequence_content = ParsedContent(
            entities=self.sample_entities,
            relationships=self.sample_relationships,
            suggested_diagram_type=DiagramType.SEQUENCE,
            diagram_type_suggestions={"sequence": 0.9},
            confidence=0.8,
            raw_text="User sends request to Login System",
        )

        result = self.engine.generate_diagram(sequence_content)

        assert result.diagram_type == DiagramType.SEQUENCE
        assert result.mermaid_syntax.startswith("sequenceDiagram")

        # Check for participant definitions
        assert "participant" in result.mermaid_syntax
        assert "->>" in result.mermaid_syntax

    def test_class_syntax_generation(self):
        """Test class diagram syntax generation."""
        class_content = ParsedContent(
            entities=self.sample_entities,
            relationships=self.sample_relationships,
            suggested_diagram_type=DiagramType.CLASS,
            diagram_type_suggestions={"class": 0.9},
            confidence=0.8,
            raw_text="User class inherits from Person",
        )

        result = self.engine.generate_diagram(class_content)

        assert result.diagram_type == DiagramType.CLASS
        assert result.mermaid_syntax.startswith("classDiagram")

        # Check for class definitions
        assert "class" in result.mermaid_syntax

    def test_process_syntax_generation(self):
        """Test process diagram syntax generation."""
        process_content = ParsedContent(
            entities=self.sample_entities,
            relationships=self.sample_relationships,
            suggested_diagram_type=DiagramType.PROCESS,
            diagram_type_suggestions={"process": 0.9},
            confidence=0.8,
            raw_text="Process starts with User input",
        )

        result = self.engine.generate_diagram(process_content)

        assert result.diagram_type == DiagramType.PROCESS
        assert result.mermaid_syntax.startswith("flowchart LR")

    def test_node_id_generation(self):
        """Test node ID generation and mapping."""
        # Test clean ID generation
        node_id1 = self.engine._get_or_create_node_id("User Account")
        node_id2 = self.engine._get_or_create_node_id("User Account")  # Same entity
        node_id3 = self.engine._get_or_create_node_id("Login System")

        # Same entity should get same ID
        assert node_id1 == node_id2

        # Different entities should get different IDs
        assert node_id1 != node_id3

        # IDs should be clean (no spaces or special chars except underscore)
        assert " " not in node_id1
        assert node_id1.replace("_", "").isalnum()

    def test_label_cleaning(self):
        """Test label cleaning functionality."""
        # Test normal label
        clean_label = self.engine._clean_label("User Account")
        assert clean_label == "User Account"

        # Test label with extra whitespace
        clean_label = self.engine._clean_label("  User   Account  ")
        assert clean_label == "User Account"

        # Test long label truncation
        long_label = "This is a very long label that should be truncated"
        clean_label = self.engine._clean_label(long_label)
        assert len(clean_label) <= 30
        assert clean_label.endswith("...")

    def test_shape_syntax_generation(self):
        """Test Mermaid shape syntax generation."""
        # Test different shapes
        rect_syntax = self.engine._get_shape_syntax("rect", "Test")
        assert rect_syntax == "[Test]"

        round_syntax = self.engine._get_shape_syntax("round", "Test")
        assert round_syntax == "(Test)"

        circle_syntax = self.engine._get_shape_syntax("circle", "Test")
        assert circle_syntax == "((Test))"

        rhombus_syntax = self.engine._get_shape_syntax("rhombus", "Test")
        assert rhombus_syntax == "{Test}"

    def test_diagram_validation(self):
        """Test diagram validation functionality."""
        result = self.engine.generate_diagram(self.sample_content)
        validation = self.engine.validate_diagram(result)

        assert validation["has_nodes"] is True
        assert validation["has_valid_syntax"] is True
        assert validation["nodes_have_labels"] is True
        assert validation["edges_reference_valid_nodes"] is True
        assert validation["is_valid"] is True

    def test_empty_content_handling(self):
        """Test handling of empty content."""
        empty_content = ParsedContent(
            entities=[],
            relationships=[],
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.5},
            confidence=0.3,
            raw_text="",
        )

        result = self.engine.generate_diagram(empty_content)

        assert len(result.nodes) == 0
        assert len(result.edges) == 0
        assert result.mermaid_syntax.startswith("flowchart TD")

    def test_relationship_arrow_mapping(self):
        """Test relationship to arrow type mapping."""
        # Test various relationship types
        test_relationships = [
            Relationship("A", "B", "creates", "creates", 0.9),
            Relationship("A", "B", "uses", "uses", 0.9),
            Relationship("A", "B", "contains", "contains", 0.9),
            Relationship("A", "B", "unknown_type", "unknown", 0.9),
        ]

        # Generate nodes first
        test_entities = [
            Entity("A", EntityType.OBJECT, {}, 0.9, 0, 1),
            Entity("B", EntityType.OBJECT, {}, 0.9, 2, 3),
        ]
        self.engine._generate_nodes(test_entities)

        edges = self.engine._generate_edges(test_relationships)

        # Check arrow types
        assert edges[0].arrow_type == "-->"  # creates
        assert (
            edges[1].arrow_type == "-.->"
        ), f"Expected '-.->',  got '{edges[1].arrow_type}'"  # uses
        assert edges[2].arrow_type == "==>"  # contains
        assert edges[3].arrow_type == "-->"  # unknown defaults to -->

    def test_layout_config_generation(self):
        """Test layout configuration generation."""
        # Test flowchart layout
        flowchart_config = self.engine._generate_layout_config(DiagramType.FLOWCHART)
        assert flowchart_config["direction"] == "TD"

        # Test sequence layout
        sequence_config = self.engine._generate_layout_config(DiagramType.SEQUENCE)
        assert sequence_config["direction"] == "LR"

        # Test process layout
        process_config = self.engine._generate_layout_config(DiagramType.PROCESS)
        assert process_config["direction"] == "LR"

    def test_metadata_generation(self):
        """Test metadata generation."""
        result = self.engine.generate_diagram(self.sample_content)

        assert "entity_count" in result.metadata
        assert "relationship_count" in result.metadata
        assert "confidence" in result.metadata
        assert "original_text_length" in result.metadata

        assert result.metadata["entity_count"] == "3"
        assert result.metadata["relationship_count"] == "2"
        assert result.metadata["confidence"] == "0.75"

    def test_counter_reset(self):
        """Test that counters are properly reset between diagram generations."""
        # Generate first diagram
        result1 = self.engine.generate_diagram(self.sample_content)
        first_node_ids = [node.id for node in result1.nodes]

        # Generate second diagram
        result2 = self.engine.generate_diagram(self.sample_content)
        second_node_ids = [node.id for node in result2.nodes]

        # Node IDs should be the same (counters reset)
        assert first_node_ids == second_node_ids

    def test_styling_generation(self):
        """Test CSS styling generation for flowcharts."""
        nodes = self.engine._generate_nodes(self.sample_entities)
        styling = self.engine._generate_flowchart_styling(nodes)

        # Should have styling for each entity type
        assert len(styling) > 0
        assert any("classDef" in line for line in styling)
        assert any("class" in line for line in styling)

    def test_complex_diagram_generation(self):
        """Test generation of a more complex diagram."""
        # Create a more complex scenario
        complex_entities = [
            Entity("Frontend", EntityType.SYSTEM, {}, 0.9, 0, 8),
            Entity("API Gateway", EntityType.SYSTEM, {}, 0.9, 9, 20),
            Entity("Auth Service", EntityType.SYSTEM, {}, 0.9, 21, 33),
            Entity("Database", EntityType.DATA, {}, 0.9, 34, 42),
            Entity("User", EntityType.ACTOR, {}, 0.9, 43, 47),
            Entity("Cache", EntityType.DATA, {}, 0.9, 48, 53),
        ]

        complex_relationships = [
            Relationship("User", "Frontend", "uses", "interacts with", 0.9),
            Relationship("Frontend", "API Gateway", "sends", "API calls", 0.9),
            Relationship("API Gateway", "Auth Service", "uses", "authentication", 0.9),
            Relationship("Auth Service", "Database", "accesses", "user data", 0.9),
            Relationship("API Gateway", "Cache", "uses", "caching", 0.8),
        ]

        complex_content = ParsedContent(
            entities=complex_entities,
            relationships=complex_relationships,
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.9},
            confidence=0.85,
            raw_text="Complex system architecture",
        )

        result = self.engine.generate_diagram(complex_content)

        assert len(result.nodes) == 6
        assert len(result.edges) == 5
        assert (
            result.mermaid_syntax.count("-->")
            + result.mermaid_syntax.count("-.->")
            + result.mermaid_syntax.count("..>")
            >= 5
        )

        validation = self.engine.validate_diagram(result)
        assert validation["is_valid"] is True

    def test_auto_layout_positioning(self):
        """Test that auto-layout assigns positions to nodes."""
        result = self.engine.generate_diagram(self.sample_content)

        # All nodes should have positions assigned
        for node in result.nodes:
            assert node.position is not None
            assert isinstance(node.position.x, (int, float))
            assert isinstance(node.position.y, (int, float))
            assert node.position.x >= 0
            assert node.position.y >= 0

    def test_hierarchical_layout(self):
        """Test hierarchical layout algorithm."""
        # Create a clear hierarchy
        hierarchical_entities = [
            Entity("Root", EntityType.SYSTEM, {}, 0.9, 0, 4),
            Entity("Child1", EntityType.PROCESS, {}, 0.9, 5, 11),
            Entity("Child2", EntityType.PROCESS, {}, 0.9, 12, 18),
            Entity("Grandchild", EntityType.DATA, {}, 0.9, 19, 29),
        ]

        hierarchical_relationships = [
            Relationship("Root", "Child1", "creates", "", 0.9),
            Relationship("Root", "Child2", "creates", "", 0.9),
            Relationship("Child1", "Grandchild", "uses", "", 0.9),
        ]

        hierarchical_content = ParsedContent(
            entities=hierarchical_entities,
            relationships=hierarchical_relationships,
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.9},
            confidence=0.9,
            raw_text="Hierarchical structure",
        )

        result = self.engine.generate_diagram(hierarchical_content)

        # Check that nodes are positioned hierarchically
        root_node = next(node for node in result.nodes if "Root" in node.label)
        child_nodes = [node for node in result.nodes if "Child" in node.label]

        # Root should be at the top (lower y value)
        for child in child_nodes:
            assert root_node.position.y < child.position.y

    def test_sequence_layout(self):
        """Test sequence diagram layout."""
        sequence_content = ParsedContent(
            entities=self.sample_entities,
            relationships=self.sample_relationships,
            suggested_diagram_type=DiagramType.SEQUENCE,
            diagram_type_suggestions={"sequence": 0.9},
            confidence=0.8,
            raw_text="User interacts with system",
        )

        result = self.engine.generate_diagram(sequence_content)

        # Check that actors are positioned horizontally
        actor_nodes = [node for node in result.nodes if node.entity_type == "actor"]
        system_nodes = [node for node in result.nodes if node.entity_type == "system"]

        if len(actor_nodes) > 1:
            # Actors should have different x positions
            x_positions = [node.position.x for node in actor_nodes]
            assert len(set(x_positions)) == len(x_positions)

    def test_force_directed_layout(self):
        """Test force-directed layout algorithm."""
        # Create content that would use force-directed layout (ERD)
        erd_content = ParsedContent(
            entities=self.sample_entities,
            relationships=self.sample_relationships,
            suggested_diagram_type=DiagramType.ERD,
            diagram_type_suggestions={"erd": 0.9},
            confidence=0.8,
            raw_text="Database entities",
        )

        result = self.engine.generate_diagram(erd_content)

        # Check that nodes have reasonable positions
        for node in result.nodes:
            assert node.position is not None
            # Positions should be within reasonable bounds
            assert 0 <= node.position.x <= 1000
            assert 0 <= node.position.y <= 1000

    def test_grid_layout_fallback(self):
        """Test grid layout as fallback."""
        # Create entities without relationships (should fall back to grid)
        grid_entities = [
            Entity(f"Entity{i}", EntityType.OBJECT, {}, 0.9, i * 5, i * 5 + 5)
            for i in range(4)
        ]

        grid_content = ParsedContent(
            entities=grid_entities,
            relationships=[],  # No relationships
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.5},
            confidence=0.5,
            raw_text="Isolated entities",
        )

        result = self.engine.generate_diagram(grid_content)

        # Should arrange in a grid pattern
        assert len(result.nodes) == 4
        for node in result.nodes:
            assert node.position is not None

    def test_layout_config_application(self):
        """Test that layout configuration is properly applied."""
        result = self.engine.generate_diagram(self.sample_content)

        # Check layout config is present
        assert "direction" in result.layout_config
        assert "theme" in result.layout_config
        assert "background" in result.layout_config

        # Check that spacing is respected in positioning
        positions = [(node.position.x, node.position.y) for node in result.nodes]

        # No two nodes should have exactly the same position
        assert len(set(positions)) == len(positions)
