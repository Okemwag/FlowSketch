"""
Unit tests for diagram validation and error handling.
"""

import pytest

from core.services.diagram_engine import (
    DiagramEngine,
    DiagramGenerationError,
    DiagramValidationError,
    ValidationSeverity,
)
from core.services.text_parser import (
    DiagramType,
    Entity,
    EntityType,
    ParsedContent,
    Relationship,
)


class TestDiagramValidation:
    """Test cases for diagram validation and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DiagramEngine()

        # Valid sample content
        self.valid_content = ParsedContent(
            entities=[
                Entity("User", EntityType.ACTOR, {}, 0.9, 0, 4),
                Entity("System", EntityType.SYSTEM, {}, 0.9, 5, 11),
            ],
            relationships=[
                Relationship("User", "System", "uses", "interacts with", 0.9),
            ],
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.8},
            confidence=0.8,
            raw_text="User uses System",
        )

    def test_valid_diagram_validation(self):
        """Test validation of a valid diagram."""
        diagram_data = self.engine.generate_diagram(self.valid_content)
        validation_result = self.engine.validate_diagram_comprehensive(diagram_data)

        assert validation_result.is_valid is True
        assert len(validation_result.issues) == 0
        assert "node_count" in validation_result.metadata
        assert "edge_count" in validation_result.metadata

    def test_empty_content_validation_error(self):
        """Test validation error for empty content."""
        empty_content = ParsedContent(
            entities=[],
            relationships=[],
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.5},
            confidence=0.3,
            raw_text="",
        )

        with pytest.raises(DiagramGenerationError) as exc_info:
            self.engine.generate_diagram(empty_content)

        assert exc_info.value.stage == "input_validation"
        assert "empty" in str(exc_info.value).lower()

    def test_low_confidence_validation_error(self):
        """Test validation error for low confidence content."""
        low_confidence_content = ParsedContent(
            entities=[Entity("Test", EntityType.OBJECT, {}, 0.9, 0, 4)],
            relationships=[],
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.05},
            confidence=0.05,  # Very low confidence
            raw_text="Test entity",
        )

        with pytest.raises(DiagramGenerationError) as exc_info:
            self.engine.generate_diagram(low_confidence_content)

        assert exc_info.value.stage == "input_validation"
        assert "confidence" in str(exc_info.value).lower()

    def test_no_entities_validation_error(self):
        """Test validation error when no entities are found."""
        no_entities_content = ParsedContent(
            entities=[],
            relationships=[],
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.5},
            confidence=0.5,
            raw_text="Some text with no entities",
        )

        with pytest.raises(DiagramGenerationError) as exc_info:
            self.engine.generate_diagram(no_entities_content)

        assert exc_info.value.stage == "input_validation"
        assert "no entities" in str(exc_info.value).lower()

    def test_empty_labels_validation(self):
        """Test validation of nodes with empty labels."""
        # Create content that would generate empty labels
        empty_label_content = ParsedContent(
            entities=[
                Entity("", EntityType.OBJECT, {}, 0.9, 0, 0),  # Empty name
                Entity("Valid", EntityType.OBJECT, {}, 0.9, 1, 6),
            ],
            relationships=[],
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.8},
            confidence=0.8,
            raw_text="Empty and Valid entities",
        )

        with pytest.raises(DiagramValidationError) as exc_info:
            self.engine.generate_diagram(empty_label_content)

        validation_result = exc_info.value.validation_result
        assert not validation_result.is_valid

        # Check for empty labels error
        empty_label_issues = [
            issue for issue in validation_result.issues if issue.code == "EMPTY_LABELS"
        ]
        assert len(empty_label_issues) > 0

    def test_orphaned_edges_validation(self):
        """Test validation of edges referencing non-existent nodes."""
        # Create a scenario with orphaned edges by manipulating the engine
        diagram_data = self.engine.generate_diagram(self.valid_content)

        # Add an edge that references a non-existent node
        from core.services.diagram_engine import Edge

        orphaned_edge = Edge(
            source_id="nonexistent_source",
            target_id="nonexistent_target",
            label="orphaned",
            arrow_type="-->",
            relationship_type="invalid",
        )
        diagram_data.edges.append(orphaned_edge)

        validation_result = self.engine.validate_diagram_comprehensive(diagram_data)

        assert not validation_result.is_valid
        orphaned_issues = [
            issue
            for issue in validation_result.issues
            if issue.code == "ORPHANED_EDGES"
        ]
        assert len(orphaned_issues) > 0

    def test_overlapping_nodes_warning(self):
        """Test warning for overlapping node positions."""
        diagram_data = self.engine.generate_diagram(self.valid_content)

        # Force nodes to have overlapping positions
        from core.services.diagram_engine import Position

        if len(diagram_data.nodes) >= 2:
            diagram_data.nodes[0].position = Position(100, 100)
            diagram_data.nodes[1].position = Position(110, 110)  # Very close

        validation_result = self.engine.validate_diagram_comprehensive(diagram_data)

        # Should still be valid but have warnings
        overlapping_warnings = [
            warning
            for warning in validation_result.warnings
            if warning.code == "OVERLAPPING_NODES"
        ]
        assert len(overlapping_warnings) > 0

    def test_isolated_nodes_warning(self):
        """Test warning for isolated nodes."""
        isolated_content = ParsedContent(
            entities=[
                Entity("Connected1", EntityType.OBJECT, {}, 0.9, 0, 10),
                Entity("Connected2", EntityType.OBJECT, {}, 0.9, 11, 21),
                Entity("Isolated", EntityType.OBJECT, {}, 0.9, 22, 30),
            ],
            relationships=[
                Relationship("Connected1", "Connected2", "uses", "", 0.9),
                # No relationship for "Isolated"
            ],
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.8},
            confidence=0.8,
            raw_text="Connected1 uses Connected2. Isolated exists.",
        )

        diagram_data = self.engine.generate_diagram(isolated_content)
        validation_result = self.engine.validate_diagram_comprehensive(diagram_data)

        isolated_warnings = [
            warning
            for warning in validation_result.warnings
            if warning.code == "ISOLATED_NODES"
        ]
        assert len(isolated_warnings) > 0

    def test_high_complexity_warning(self):
        """Test warning for high complexity diagrams."""
        # Create a complex diagram with many nodes and edges
        complex_entities = [
            Entity(f"Entity{i}", EntityType.OBJECT, {}, 0.9, i * 5, i * 5 + 5)
            for i in range(25)  # Many entities
        ]

        complex_relationships = []
        # Create many relationships (high edge density)
        for i in range(len(complex_entities) - 1):
            for j in range(i + 1, min(i + 4, len(complex_entities))):
                complex_relationships.append(
                    Relationship(f"Entity{i}", f"Entity{j}", "uses", "", 0.9)
                )

        complex_content = ParsedContent(
            entities=complex_entities,
            relationships=complex_relationships,
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.8},
            confidence=0.8,
            raw_text="Complex system with many entities",
        )

        diagram_data = self.engine.generate_diagram(complex_content)
        validation_result = self.engine.validate_diagram_comprehensive(diagram_data)

        complexity_warnings = [
            warning
            for warning in validation_result.warnings
            if warning.code == "HIGH_COMPLEXITY"
        ]
        assert len(complexity_warnings) > 0

    def test_inappropriate_diagram_type_warning(self):
        """Test warning for inappropriate diagram type."""
        # Create content that's not suitable for ERD but force ERD type
        process_content = ParsedContent(
            entities=[
                Entity("Start Process", EntityType.PROCESS, {}, 0.9, 0, 13),
                Entity("End Process", EntityType.PROCESS, {}, 0.9, 14, 25),
            ],
            relationships=[
                Relationship("Start Process", "End Process", "flows_to", "", 0.9),
            ],
            suggested_diagram_type=DiagramType.ERD,  # Wrong type for process entities
            diagram_type_suggestions={"erd": 0.6},
            confidence=0.8,
            raw_text="Start Process flows to End Process",
        )

        diagram_data = self.engine.generate_diagram(process_content)
        validation_result = self.engine.validate_diagram_comprehensive(diagram_data)

        inappropriate_warnings = [
            warning
            for warning in validation_result.warnings
            if warning.code == "INAPPROPRIATE_TYPE"
        ]
        assert len(inappropriate_warnings) > 0

    def test_complexity_score_calculation(self):
        """Test complexity score calculation."""
        # Test with simple diagram
        simple_data = self.engine.generate_diagram(self.valid_content)
        simple_score = self.engine._calculate_complexity_score(simple_data)
        assert 0.0 <= simple_score <= 1.0
        assert simple_score < 0.5  # Should be low complexity

        # Test with complex diagram
        complex_entities = [
            Entity(f"E{i}", EntityType.OBJECT, {}, 0.9, 0, 1) for i in range(30)
        ]
        complex_relationships = [
            Relationship(f"E{i}", f"E{j}", "uses", "", 0.9)
            for i in range(29)
            for j in range(i + 1, min(i + 5, 30))
        ]

        complex_content = ParsedContent(
            entities=complex_entities,
            relationships=complex_relationships,
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.8},
            confidence=0.8,
            raw_text="Complex system",
        )

        complex_data = self.engine.generate_diagram(complex_content)
        complex_score = self.engine._calculate_complexity_score(complex_data)
        assert complex_score > simple_score

    def test_validation_metadata(self):
        """Test that validation metadata is properly populated."""
        diagram_data = self.engine.generate_diagram(self.valid_content)
        validation_result = self.engine.validate_diagram_comprehensive(diagram_data)

        expected_metadata_keys = [
            "node_count",
            "edge_count",
            "syntax_length",
            "has_positions",
            "error_count",
            "warning_count",
            "complexity_score",
        ]

        for key in expected_metadata_keys:
            assert key in validation_result.metadata

        assert validation_result.metadata["node_count"] == len(diagram_data.nodes)
        assert validation_result.metadata["edge_count"] == len(diagram_data.edges)

    def test_validation_issue_structure(self):
        """Test that validation issues have proper structure."""
        # Create content that will generate validation issues
        problematic_content = ParsedContent(
            entities=[Entity("", EntityType.OBJECT, {}, 0.9, 0, 0)],  # Empty name
            relationships=[],
            suggested_diagram_type=DiagramType.FLOWCHART,
            diagram_type_suggestions={"flowchart": 0.8},
            confidence=0.8,
            raw_text="Empty entity",
        )

        try:
            self.engine.generate_diagram(problematic_content)
        except DiagramValidationError as e:
            validation_result = e.validation_result

            for issue in validation_result.issues:
                assert hasattr(issue, "severity")
                assert hasattr(issue, "code")
                assert hasattr(issue, "message")
                assert issue.severity in [
                    ValidationSeverity.ERROR,
                    ValidationSeverity.WARNING,
                    ValidationSeverity.INFO,
                ]
                assert isinstance(issue.code, str)
                assert isinstance(issue.message, str)

    def test_legacy_validation_compatibility(self):
        """Test that legacy validation method still works."""
        diagram_data = self.engine.generate_diagram(self.valid_content)
        legacy_result = self.engine.validate_diagram(diagram_data)

        assert isinstance(legacy_result, dict)
        assert "is_valid" in legacy_result
        assert "has_nodes" in legacy_result
        assert "has_valid_syntax" in legacy_result

    def test_error_handling_in_generation_stages(self):
        """Test error handling in different generation stages."""
        # Test with content that might cause issues in different stages

        # This should work fine
        normal_result = self.engine.generate_diagram(self.valid_content)
        assert normal_result is not None

        # Test with None content
        with pytest.raises(DiagramGenerationError) as exc_info:
            self.engine.generate_diagram(None)
        assert exc_info.value.stage == "input_validation"
