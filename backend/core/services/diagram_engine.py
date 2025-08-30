"""
Diagram generation engine for converting parsed content to Mermaid syntax.
"""

import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union

from .text_parser import DiagramType, Entity, ParsedContent, Relationship


@dataclass
class Position:
    """Represents a 2D position."""

    x: float
    y: float


@dataclass
class Node:
    """Represents a diagram node."""

    id: str
    label: str
    shape: str
    entity_type: str
    properties: Dict[str, str]
    position: Optional[Position] = None


@dataclass
class Edge:
    """Represents a diagram edge/connection."""

    source_id: str
    target_id: str
    label: str
    arrow_type: str
    relationship_type: str


@dataclass
class DiagramData:
    """Container for generated diagram data."""

    diagram_type: DiagramType
    mermaid_syntax: str
    nodes: List[Node]
    edges: List[Edge]
    layout_config: Dict[str, str]
    metadata: Dict[str, str]


class MermaidShapes(Enum):
    """Mermaid node shapes."""

    RECTANGLE = "rect"
    ROUNDED = "round"
    CIRCLE = "circle"
    RHOMBUS = "rhombus"
    HEXAGON = "hexagon"
    CYLINDER = "cylinder"
    CLOUD = "cloud"


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    
    severity: ValidationSeverity
    code: str
    message: str
    details: Optional[Dict[str, str]] = None
    suggested_fix: Optional[str] = None


@dataclass
class ValidationResult:
    """Comprehensive validation result."""
    
    is_valid: bool
    issues: List[ValidationIssue]
    warnings: List[ValidationIssue]
    metadata: Dict[str, Union[str, int, float]]


class DiagramValidationError(Exception):
    """Exception raised when diagram validation fails."""
    
    def __init__(self, message: str, validation_result: ValidationResult):
        super().__init__(message)
        self.validation_result = validation_result


class DiagramGenerationError(Exception):
    """Exception raised when diagram generation fails."""
    
    def __init__(self, message: str, stage: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.stage = stage
        self.details = details or {}


class DiagramEngine:
    """Service for generating Mermaid diagrams from parsed content."""

    def __init__(self):
        """Initialize the diagram engine."""
        self.node_counter = 0
        self.node_id_map = {}  # Maps entity names to node IDs

        # Shape mapping based on entity types
        self.entity_shape_map = {
            "object": MermaidShapes.RECTANGLE,
            "process": MermaidShapes.ROUNDED,
            "actor": MermaidShapes.CIRCLE,
            "data": MermaidShapes.CYLINDER,
            "system": MermaidShapes.HEXAGON,
            "event": MermaidShapes.RHOMBUS,
        }

        # Arrow types for different relationships
        self.relationship_arrow_map = {
            "creates": "-->",
            "uses": "-.->",
            "contains": "==>",
            "inherits": "---|>",
            "depends_on": "..>",
            "flows_to": "-->",
            "triggers": "==>",
            "sends": "-.->",
            "receives": "<-.-",
            "manages": "==>",
            "processes": "-->",
            "stores": "-.->",
            "accesses": "..>",
        }

        # Layout configuration
        self.layout_config = {
            "node_width": 120,
            "node_height": 60,
            "horizontal_spacing": 200,
            "vertical_spacing": 100,
            "margin": 50,
        }

    def generate_diagram(self, content: ParsedContent) -> DiagramData:
        """Generate a complete diagram from parsed content."""
        try:
            # Validate input content
            self._validate_input_content(content)
            
            self._reset_counters()
            
            # Generate nodes from entities
            try:
                nodes = self._generate_nodes(content.entities)
            except Exception as e:
                raise DiagramGenerationError(
                    f"Failed to generate nodes: {str(e)}", 
                    "node_generation",
                    {"entity_count": len(content.entities)}
                )
            
            # Generate edges from relationships
            try:
                edges = self._generate_edges(content.relationships)
            except Exception as e:
                raise DiagramGenerationError(
                    f"Failed to generate edges: {str(e)}", 
                    "edge_generation",
                    {"relationship_count": len(content.relationships)}
                )
            
            # Generate Mermaid syntax based on diagram type
            try:
                mermaid_syntax = self._generate_mermaid_syntax(
                    content.suggested_diagram_type, nodes, edges
                )
            except Exception as e:
                raise DiagramGenerationError(
                    f"Failed to generate Mermaid syntax: {str(e)}", 
                    "syntax_generation",
                    {"diagram_type": content.suggested_diagram_type.value}
                )
            
            # Create layout configuration
            layout_config = self._generate_layout_config(content.suggested_diagram_type)
            
            # Create metadata
            metadata = {
                "entity_count": str(len(content.entities)),
                "relationship_count": str(len(content.relationships)),
                "confidence": str(content.confidence),
                "original_text_length": str(len(content.raw_text)),
            }
            
            # Apply auto-layout positioning
            try:
                positioned_nodes = self._apply_auto_layout(
                    nodes, edges, content.suggested_diagram_type
                )
            except Exception as e:
                raise DiagramGenerationError(
                    f"Failed to apply auto-layout: {str(e)}", 
                    "layout_generation",
                    {"node_count": len(nodes), "edge_count": len(edges)}
                )
            
            # Create diagram data
            diagram_data = DiagramData(
                diagram_type=content.suggested_diagram_type,
                mermaid_syntax=mermaid_syntax,
                nodes=positioned_nodes,
                edges=edges,
                layout_config=layout_config,
                metadata=metadata,
            )
            
            # Validate the generated diagram
            validation_result = self.validate_diagram_comprehensive(diagram_data)
            if not validation_result.is_valid:
                # Check if we have critical errors
                critical_errors = [
                    issue for issue in validation_result.issues 
                    if issue.severity == ValidationSeverity.ERROR
                ]
                if critical_errors:
                    raise DiagramValidationError(
                        f"Generated diagram failed validation with {len(critical_errors)} critical errors",
                        validation_result
                    )
            
            return diagram_data
            
        except (DiagramGenerationError, DiagramValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Catch any unexpected errors
            raise DiagramGenerationError(
                f"Unexpected error during diagram generation: {str(e)}", 
                "unknown",
                {"error_type": type(e).__name__}
            )

    def _reset_counters(self):
        """Reset internal counters for new diagram generation."""
        self.node_counter = 0
        self.node_id_map = {}

    def _generate_nodes(self, entities: List[Entity]) -> List[Node]:
        """Generate diagram nodes from entities."""
        nodes = []

        for entity in entities:
            node_id = self._get_or_create_node_id(entity.name)
            shape = self.entity_shape_map.get(
                entity.type.value, MermaidShapes.RECTANGLE
            ).value

            # Clean label for display
            label = self._clean_label(entity.name)

            node = Node(
                id=node_id,
                label=label,
                shape=shape,
                entity_type=entity.type.value,
                properties=entity.properties,
            )
            nodes.append(node)

        return nodes

    def _generate_edges(self, relationships: List[Relationship]) -> List[Edge]:
        """Generate diagram edges from relationships."""
        edges = []

        for relationship in relationships:
            source_id = self._get_or_create_node_id(relationship.source)
            target_id = self._get_or_create_node_id(relationship.target)

            arrow_type = self.relationship_arrow_map.get(relationship.type, "-->")

            # Clean label for display
            label = self._clean_label(relationship.label) if relationship.label else ""

            edge = Edge(
                source_id=source_id,
                target_id=target_id,
                label=label,
                arrow_type=arrow_type,
                relationship_type=relationship.type,
            )
            edges.append(edge)

        return edges

    def _generate_mermaid_syntax(
        self, diagram_type: DiagramType, nodes: List[Node], edges: List[Edge]
    ) -> str:
        """Generate Mermaid syntax based on diagram type."""
        if diagram_type == DiagramType.FLOWCHART:
            return self._generate_flowchart_syntax(nodes, edges)
        elif diagram_type == DiagramType.ERD:
            return self._generate_erd_syntax(nodes, edges)
        elif diagram_type == DiagramType.SEQUENCE:
            return self._generate_sequence_syntax(nodes, edges)
        elif diagram_type == DiagramType.CLASS:
            return self._generate_class_syntax(nodes, edges)
        elif diagram_type == DiagramType.PROCESS:
            return self._generate_process_syntax(nodes, edges)
        else:
            # Default to flowchart
            return self._generate_flowchart_syntax(nodes, edges)

    def _generate_flowchart_syntax(self, nodes: List[Node], edges: List[Edge]) -> str:
        """Generate Mermaid flowchart syntax."""
        lines = ["flowchart TD"]

        # Add node definitions with shapes
        for node in nodes:
            shape_syntax = self._get_shape_syntax(node.shape, node.label)
            lines.append(f"    {node.id}{shape_syntax}")

        # Add edges
        for edge in edges:
            if edge.label:
                lines.append(
                    f"    {edge.source_id} {edge.arrow_type}|{edge.label}| {edge.target_id}"
                )
            else:
                lines.append(f"    {edge.source_id} {edge.arrow_type} {edge.target_id}")

        # Add styling based on entity types
        lines.extend(self._generate_flowchart_styling(nodes))

        return "\n".join(lines)

    def _generate_erd_syntax(self, nodes: List[Node], edges: List[Edge]) -> str:
        """Generate Mermaid ERD syntax."""
        lines = ["erDiagram"]

        # Group nodes by entity type for ERD
        entities = [node for node in nodes if node.entity_type in ["object", "data"]]

        # Add entity definitions
        for node in entities:
            lines.append(f"    {node.id} {{")
            # Add basic attributes if available in properties
            if node.properties:
                for key, value in node.properties.items():
                    lines.append(f"        string {key}")
            else:
                lines.append(f"        string id")
            lines.append("    }")

        # Add relationships
        for edge in edges:
            # Convert to ERD relationship syntax
            relationship_type = self._convert_to_erd_relationship(
                edge.relationship_type
            )
            if edge.label:
                lines.append(
                    f'    {edge.source_id} {relationship_type} {edge.target_id} : "{edge.label}"'
                )
            else:
                lines.append(
                    f'    {edge.source_id} {relationship_type} {edge.target_id} : ""'
                )

        return "\n".join(lines)

    def _generate_sequence_syntax(self, nodes: List[Node], edges: List[Edge]) -> str:
        """Generate Mermaid sequence diagram syntax."""
        lines = ["sequenceDiagram"]

        # Add participants (actors and systems)
        actors = [node for node in nodes if node.entity_type in ["actor", "system"]]
        for actor in actors:
            lines.append(f"    participant {actor.id} as {actor.label}")

        # Add interactions
        for edge in edges:
            if edge.label:
                lines.append(f"    {edge.source_id}->>+{edge.target_id}: {edge.label}")
            else:
                lines.append(f"    {edge.source_id}->>+{edge.target_id}: interaction")

        return "\n".join(lines)

    def _generate_class_syntax(self, nodes: List[Node], edges: List[Edge]) -> str:
        """Generate Mermaid class diagram syntax."""
        lines = ["classDiagram"]

        # Add class definitions
        for node in nodes:
            lines.append(f"    class {node.id} {{")
            # Add basic methods/attributes
            if node.properties:
                for key, value in node.properties.items():
                    lines.append(f"        +{key} : {value}")
            lines.append("    }")

        # Add relationships
        for edge in edges:
            relationship_type = self._convert_to_class_relationship(
                edge.relationship_type
            )
            lines.append(f"    {edge.source_id} {relationship_type} {edge.target_id}")

        return "\n".join(lines)

    def _generate_process_syntax(self, nodes: List[Node], edges: List[Edge]) -> str:
        """Generate Mermaid process flow syntax (similar to flowchart but with process focus)."""
        lines = ["flowchart LR"]

        # Add process nodes with specific styling
        for node in nodes:
            if node.entity_type == "process":
                lines.append(f"    {node.id}[{node.label}]")
            elif node.entity_type == "data":
                lines.append(f"    {node.id}[({node.label})]")
            else:
                lines.append(f"    {node.id}[{node.label}]")

        # Add process flows
        for edge in edges:
            if edge.label:
                lines.append(
                    f"    {edge.source_id} --> |{edge.label}| {edge.target_id}"
                )
            else:
                lines.append(f"    {edge.source_id} --> {edge.target_id}")

        # Add process-specific styling
        lines.extend(self._generate_process_styling(nodes))

        return "\n".join(lines)

    def _get_shape_syntax(self, shape: str, label: str) -> str:
        """Get Mermaid shape syntax for a node."""
        shape_map = {
            "rect": f"[{label}]",
            "round": f"({label})",
            "circle": f"(({label}))",
            "rhombus": f"{{{label}}}",
            "hexagon": f"{{{{{label}}}}}",
            "cylinder": f"[({label})]",
            "cloud": f">>{label}]",
        }
        return shape_map.get(shape, f"[{label}]")

    def _generate_flowchart_styling(self, nodes: List[Node]) -> List[str]:
        """Generate CSS styling for flowchart nodes."""
        styling = []

        # Define colors for different entity types
        color_map = {
            "object": "#e1f5fe",
            "process": "#f3e5f5",
            "actor": "#e8f5e8",
            "data": "#fff3e0",
            "system": "#fce4ec",
            "event": "#f1f8e9",
        }

        for node in nodes:
            color = color_map.get(node.entity_type, "#f5f5f5")
            styling.append(f"    classDef {node.entity_type}Style fill:{color}")
            styling.append(f"    class {node.id} {node.entity_type}Style")

        return styling

    def _generate_process_styling(self, nodes: List[Node]) -> List[str]:
        """Generate CSS styling for process diagrams."""
        styling = []

        # Process-specific colors
        color_map = {
            "process": "#bbdefb",
            "data": "#ffccbc",
            "system": "#c8e6c9",
        }

        for node in nodes:
            if node.entity_type in color_map:
                color = color_map[node.entity_type]
                styling.append(f"    classDef {node.entity_type}Style fill:{color}")
                styling.append(f"    class {node.id} {node.entity_type}Style")

        return styling

    def _convert_to_erd_relationship(self, relationship_type: str) -> str:
        """Convert relationship type to ERD syntax."""
        erd_map = {
            "contains": "||--o{",
            "uses": "}o--||",
            "creates": "||--||",
            "depends_on": "}o..o{",
        }
        return erd_map.get(relationship_type, "||--||")

    def _convert_to_class_relationship(self, relationship_type: str) -> str:
        """Convert relationship type to class diagram syntax."""
        class_map = {
            "inherits": "<|--",
            "uses": "<--",
            "contains": "*--",
            "depends_on": "<..",
        }
        return class_map.get(relationship_type, "--")

    def _get_or_create_node_id(self, entity_name: str) -> str:
        """Get existing node ID or create a new one."""
        if entity_name not in self.node_id_map:
            self.node_counter += 1
            # Create clean ID from entity name
            clean_id = re.sub(r"[^a-zA-Z0-9]", "", entity_name.replace(" ", "_"))
            node_id = f"{clean_id}_{self.node_counter}"
            self.node_id_map[entity_name] = node_id

        return self.node_id_map[entity_name]

    def _clean_label(self, label: str) -> str:
        """Clean label for display in diagram."""
        # Remove extra whitespace and limit length
        cleaned = re.sub(r"\s+", " ", label.strip())
        if len(cleaned) > 30:
            cleaned = cleaned[:27] + "..."
        return cleaned

    def _generate_layout_config(self, diagram_type: DiagramType) -> Dict[str, str]:
        """Generate layout configuration for the diagram."""
        base_config = {
            "direction": "TD",
            "theme": "default",
            "background": "white",
        }

        if diagram_type == DiagramType.SEQUENCE:
            base_config["direction"] = "LR"
        elif diagram_type == DiagramType.PROCESS:
            base_config["direction"] = "LR"
        elif diagram_type == DiagramType.ERD:
            base_config["direction"] = "TB"

        return base_config

    def _apply_auto_layout(
        self, nodes: List[Node], edges: List[Edge], diagram_type: DiagramType
    ) -> List[Node]:
        """Apply automatic layout positioning to nodes."""
        if not nodes:
            return nodes

        if diagram_type == DiagramType.FLOWCHART:
            return self._apply_hierarchical_layout(nodes, edges)
        elif diagram_type == DiagramType.SEQUENCE:
            return self._apply_sequence_layout(nodes, edges)
        elif diagram_type == DiagramType.ERD:
            return self._apply_erd_layout(nodes, edges)
        elif diagram_type == DiagramType.CLASS:
            return self._apply_class_layout(nodes, edges)
        elif diagram_type == DiagramType.PROCESS:
            return self._apply_process_layout(nodes, edges)
        else:
            return self._apply_grid_layout(nodes)

    def _apply_hierarchical_layout(
        self, nodes: List[Node], edges: List[Edge]
    ) -> List[Node]:
        """Apply hierarchical layout for flowcharts."""
        # Build adjacency list to understand node relationships
        adjacency = self._build_adjacency_list(nodes, edges)

        # Find root nodes (nodes with no incoming edges)
        root_nodes = self._find_root_nodes(nodes, edges)

        if not root_nodes:
            # If no clear roots, use the first node
            root_nodes = [nodes[0]]

        # Assign levels using BFS
        levels = self._assign_levels_bfs(root_nodes, adjacency)

        # Position nodes based on levels
        positioned_nodes = []
        for node in nodes:
            level = levels.get(node.id, 0)
            nodes_at_level = [n for n in nodes if levels.get(n.id, 0) == level]
            position_in_level = nodes_at_level.index(node)

            # Calculate position
            x = self.layout_config["margin"] + (
                position_in_level * self.layout_config["horizontal_spacing"]
            )
            y = self.layout_config["margin"] + (
                level * self.layout_config["vertical_spacing"]
            )

            positioned_node = Node(
                id=node.id,
                label=node.label,
                shape=node.shape,
                entity_type=node.entity_type,
                properties=node.properties,
                position=Position(x, y),
            )
            positioned_nodes.append(positioned_node)

        return positioned_nodes

    def _apply_sequence_layout(
        self, nodes: List[Node], edges: List[Edge]
    ) -> List[Node]:
        """Apply sequence layout for sequence diagrams."""
        # Separate actors from other nodes
        actors = [node for node in nodes if node.entity_type in ["actor", "system"]]
        other_nodes = [
            node for node in nodes if node.entity_type not in ["actor", "system"]
        ]

        positioned_nodes = []

        # Position actors horizontally at the top
        for i, actor in enumerate(actors):
            x = self.layout_config["margin"] + (
                i * self.layout_config["horizontal_spacing"]
            )
            y = self.layout_config["margin"]

            positioned_node = Node(
                id=actor.id,
                label=actor.label,
                shape=actor.shape,
                entity_type=actor.entity_type,
                properties=actor.properties,
                position=Position(x, y),
            )
            positioned_nodes.append(positioned_node)

        # Position other nodes below
        for i, node in enumerate(other_nodes):
            x = self.layout_config["margin"] + (
                i * self.layout_config["horizontal_spacing"]
            )
            y = self.layout_config["margin"] + self.layout_config["vertical_spacing"]

            positioned_node = Node(
                id=node.id,
                label=node.label,
                shape=node.shape,
                entity_type=node.entity_type,
                properties=node.properties,
                position=Position(x, y),
            )
            positioned_nodes.append(positioned_node)

        return positioned_nodes

    def _apply_erd_layout(self, nodes: List[Node], edges: List[Edge]) -> List[Node]:
        """Apply ERD layout for entity relationship diagrams."""
        # Use force-directed layout for ERDs
        return self._apply_force_directed_layout(nodes, edges)

    def _apply_class_layout(self, nodes: List[Node], edges: List[Edge]) -> List[Node]:
        """Apply class diagram layout."""
        # Group related classes and use hierarchical layout
        return self._apply_hierarchical_layout(nodes, edges)

    def _apply_process_layout(self, nodes: List[Node], edges: List[Edge]) -> List[Node]:
        """Apply process flow layout."""
        # Use left-to-right flow layout
        adjacency = self._build_adjacency_list(nodes, edges)
        root_nodes = self._find_root_nodes(nodes, edges)

        if not root_nodes:
            root_nodes = [nodes[0]]

        # Assign levels horizontally
        levels = self._assign_levels_bfs(root_nodes, adjacency)

        positioned_nodes = []
        for node in nodes:
            level = levels.get(node.id, 0)
            nodes_at_level = [n for n in nodes if levels.get(n.id, 0) == level]
            position_in_level = nodes_at_level.index(node)

            # Horizontal flow (left to right)
            x = self.layout_config["margin"] + (
                level * self.layout_config["horizontal_spacing"]
            )
            y = self.layout_config["margin"] + (
                position_in_level * self.layout_config["vertical_spacing"]
            )

            positioned_node = Node(
                id=node.id,
                label=node.label,
                shape=node.shape,
                entity_type=node.entity_type,
                properties=node.properties,
                position=Position(x, y),
            )
            positioned_nodes.append(positioned_node)

        return positioned_nodes

    def _apply_grid_layout(self, nodes: List[Node]) -> List[Node]:
        """Apply simple grid layout as fallback."""
        positioned_nodes = []
        grid_size = math.ceil(math.sqrt(len(nodes)))

        for i, node in enumerate(nodes):
            row = i // grid_size
            col = i % grid_size

            x = self.layout_config["margin"] + (
                col * self.layout_config["horizontal_spacing"]
            )
            y = self.layout_config["margin"] + (
                row * self.layout_config["vertical_spacing"]
            )

            positioned_node = Node(
                id=node.id,
                label=node.label,
                shape=node.shape,
                entity_type=node.entity_type,
                properties=node.properties,
                position=Position(x, y),
            )
            positioned_nodes.append(positioned_node)

        return positioned_nodes

    def _apply_force_directed_layout(
        self, nodes: List[Node], edges: List[Edge]
    ) -> List[Node]:
        """Apply force-directed layout algorithm."""
        if len(nodes) <= 1:
            return self._apply_grid_layout(nodes)

        # Initialize random positions
        positioned_nodes = []
        for i, node in enumerate(nodes):
            angle = (2 * math.pi * i) / len(nodes)
            radius = 100
            x = self.layout_config["margin"] + 200 + radius * math.cos(angle)
            y = self.layout_config["margin"] + 200 + radius * math.sin(angle)

            positioned_node = Node(
                id=node.id,
                label=node.label,
                shape=node.shape,
                entity_type=node.entity_type,
                properties=node.properties,
                position=Position(x, y),
            )
            positioned_nodes.append(positioned_node)

        # Simple force-directed iterations
        for iteration in range(50):
            forces = {node.id: Position(0, 0) for node in positioned_nodes}

            # Repulsive forces between all nodes
            for i, node1 in enumerate(positioned_nodes):
                for j, node2 in enumerate(positioned_nodes):
                    if i != j:
                        dx = node1.position.x - node2.position.x
                        dy = node1.position.y - node2.position.y
                        distance = math.sqrt(dx * dx + dy * dy)

                        if distance > 0:
                            force = 1000 / (distance * distance)
                            forces[node1.id].x += force * dx / distance
                            forces[node1.id].y += force * dy / distance

            # Attractive forces for connected nodes
            for edge in edges:
                node1 = next(n for n in positioned_nodes if n.id == edge.source_id)
                node2 = next(n for n in positioned_nodes if n.id == edge.target_id)

                dx = node2.position.x - node1.position.x
                dy = node2.position.y - node1.position.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 0:
                    force = distance * 0.01
                    forces[node1.id].x += force * dx / distance
                    forces[node1.id].y += force * dy / distance
                    forces[node2.id].x -= force * dx / distance
                    forces[node2.id].y -= force * dy / distance

            # Apply forces with damping
            damping = 0.9
            for node in positioned_nodes:
                node.position.x += forces[node.id].x * damping
                node.position.y += forces[node.id].y * damping

        return positioned_nodes

    def _build_adjacency_list(
        self, nodes: List[Node], edges: List[Edge]
    ) -> Dict[str, List[str]]:
        """Build adjacency list from edges."""
        adjacency = {node.id: [] for node in nodes}

        for edge in edges:
            if edge.source_id in adjacency:
                adjacency[edge.source_id].append(edge.target_id)

        return adjacency

    def _find_root_nodes(self, nodes: List[Node], edges: List[Edge]) -> List[Node]:
        """Find nodes with no incoming edges."""
        incoming = set()
        for edge in edges:
            incoming.add(edge.target_id)

        root_nodes = [node for node in nodes if node.id not in incoming]
        return root_nodes

    def _assign_levels_bfs(
        self, root_nodes: List[Node], adjacency: Dict[str, List[str]]
    ) -> Dict[str, int]:
        """Assign levels to nodes using breadth-first search."""
        levels = {}
        queue = [(node.id, 0) for node in root_nodes]
        visited = set()

        while queue:
            node_id, level = queue.pop(0)

            if node_id in visited:
                continue

            visited.add(node_id)
            levels[node_id] = level

            # Add children to queue
            for child_id in adjacency.get(node_id, []):
                if child_id not in visited:
                    queue.append((child_id, level + 1))

        return levels

    def validate_diagram(self, diagram_data: DiagramData) -> Dict[str, bool]:
        """Validate the generated diagram for structural correctness (legacy method)."""
        validation_result = {
            "has_nodes": len(diagram_data.nodes) > 0,
            "has_valid_syntax": self._validate_mermaid_syntax(
                diagram_data.mermaid_syntax
            ),
            "nodes_have_labels": all(node.label.strip() for node in diagram_data.nodes),
            "edges_reference_valid_nodes": self._validate_edge_references(
                diagram_data.nodes, diagram_data.edges
            ),
        }

        validation_result["is_valid"] = all(validation_result.values())
        return validation_result
    
    def validate_diagram_comprehensive(self, diagram_data: DiagramData) -> ValidationResult:
        """Comprehensive validation of the generated diagram."""
        issues = []
        warnings = []
        metadata = {}
        
        # Basic structural validation
        if len(diagram_data.nodes) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="NO_NODES",
                message="Diagram has no nodes",
                suggested_fix="Ensure input text contains identifiable entities"
            ))
        
        # Validate Mermaid syntax
        if not self._validate_mermaid_syntax(diagram_data.mermaid_syntax):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="INVALID_SYNTAX",
                message="Generated Mermaid syntax is invalid",
                details={"first_line": diagram_data.mermaid_syntax.split('\n')[0] if diagram_data.mermaid_syntax else ""},
                suggested_fix="Check diagram type and syntax generation logic"
            ))
        
        # Validate node labels
        empty_label_nodes = [node for node in diagram_data.nodes if not node.label.strip()]
        if empty_label_nodes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="EMPTY_LABELS",
                message=f"{len(empty_label_nodes)} nodes have empty labels",
                details={"node_ids": [node.id for node in empty_label_nodes]},
                suggested_fix="Ensure all entities have meaningful names"
            ))
        
        # Validate edge references
        if not self._validate_edge_references(diagram_data.nodes, diagram_data.edges):
            orphaned_edges = self._find_orphaned_edges(diagram_data.nodes, diagram_data.edges)
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="ORPHANED_EDGES",
                message=f"{len(orphaned_edges)} edges reference non-existent nodes",
                details={"orphaned_edges": [f"{edge.source_id}->{edge.target_id}" for edge in orphaned_edges]},
                suggested_fix="Ensure all relationships reference valid entities"
            ))
        
        # Validate node positions
        unpositioned_nodes = [node for node in diagram_data.nodes if node.position is None]
        if unpositioned_nodes:
            warnings.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="UNPOSITIONED_NODES",
                message=f"{len(unpositioned_nodes)} nodes lack position information",
                details={"node_ids": [node.id for node in unpositioned_nodes]},
                suggested_fix="Apply auto-layout to position nodes"
            ))
        
        # Check for overlapping nodes
        overlapping_pairs = self._find_overlapping_nodes(diagram_data.nodes)
        if overlapping_pairs:
            warnings.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="OVERLAPPING_NODES",
                message=f"{len(overlapping_pairs)} pairs of nodes have overlapping positions",
                details={"overlapping_pairs": overlapping_pairs},
                suggested_fix="Adjust layout spacing or apply force-directed layout"
            ))
        
        # Check diagram complexity
        complexity_score = self._calculate_complexity_score(diagram_data)
        metadata["complexity_score"] = complexity_score
        
        if complexity_score > 0.8:
            warnings.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="HIGH_COMPLEXITY",
                message="Diagram has high complexity and may be difficult to read",
                details={"complexity_score": str(complexity_score)},
                suggested_fix="Consider breaking into multiple diagrams or simplifying relationships"
            ))
        
        # Check for isolated nodes
        isolated_nodes = self._find_isolated_nodes(diagram_data.nodes, diagram_data.edges)
        if isolated_nodes:
            warnings.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                code="ISOLATED_NODES",
                message=f"{len(isolated_nodes)} nodes have no connections",
                details={"isolated_nodes": [node.id for node in isolated_nodes]},
                suggested_fix="Consider adding relationships or removing isolated entities"
            ))
        
        # Validate diagram type appropriateness
        type_validation = self._validate_diagram_type_appropriateness(diagram_data)
        if not type_validation["is_appropriate"]:
            warnings.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="INAPPROPRIATE_TYPE",
                message=f"Current diagram type may not be optimal for this content",
                details=type_validation,
                suggested_fix=f"Consider using {type_validation.get('suggested_type', 'a different')} diagram type"
            ))
        
        # Calculate metadata
        metadata.update({
            "node_count": len(diagram_data.nodes),
            "edge_count": len(diagram_data.edges),
            "syntax_length": len(diagram_data.mermaid_syntax),
            "has_positions": sum(1 for node in diagram_data.nodes if node.position is not None),
            "error_count": len(issues),
            "warning_count": len(warnings),
        })
        
        # Determine overall validity
        is_valid = len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            metadata=metadata
        )

    def _validate_mermaid_syntax(self, syntax: str) -> bool:
        """Basic validation of Mermaid syntax."""
        if not syntax.strip():
            return False

        # Check for valid diagram type declaration
        valid_declarations = [
            "flowchart",
            "graph",
            "sequenceDiagram",
            "classDiagram",
            "erDiagram",
            "gitgraph",
        ]

        first_line = syntax.split("\n")[0].strip()
        return any(first_line.startswith(decl) for decl in valid_declarations)

    def _validate_edge_references(self, nodes: List[Node], edges: List[Edge]) -> bool:
        """Validate that all edges reference existing nodes."""
        node_ids = {node.id for node in nodes}

        for edge in edges:
            if edge.source_id not in node_ids or edge.target_id not in node_ids:
                return False

        return True
    
    def _validate_input_content(self, content: ParsedContent) -> None:
        """Validate input parsed content."""
        if not content:
            raise DiagramGenerationError("Input content is None", "input_validation")
        
        if not content.raw_text or not content.raw_text.strip():
            raise DiagramGenerationError("Input text is empty", "input_validation")
        
        if not content.entities and not content.relationships:
            raise DiagramGenerationError(
                "No entities or relationships found in input", 
                "input_validation",
                {"text_length": len(content.raw_text)}
            )
        
        if content.confidence < 0.1:
            raise DiagramGenerationError(
                f"Input parsing confidence too low: {content.confidence}", 
                "input_validation",
                {"confidence": content.confidence}
            )
    
    def _find_orphaned_edges(self, nodes: List[Node], edges: List[Edge]) -> List[Edge]:
        """Find edges that reference non-existent nodes."""
        node_ids = {node.id for node in nodes}
        orphaned = []
        
        for edge in edges:
            if edge.source_id not in node_ids or edge.target_id not in node_ids:
                orphaned.append(edge)
        
        return orphaned
    
    def _find_overlapping_nodes(self, nodes: List[Node]) -> List[str]:
        """Find pairs of nodes with overlapping positions."""
        overlapping = []
        positioned_nodes = [node for node in nodes if node.position is not None]
        
        for i, node1 in enumerate(positioned_nodes):
            for node2 in positioned_nodes[i+1:]:
                # Check if nodes are too close (within 50 pixels)
                dx = abs(node1.position.x - node2.position.x)
                dy = abs(node1.position.y - node2.position.y)
                
                if dx < 50 and dy < 50:
                    overlapping.append(f"{node1.id}-{node2.id}")
        
        return overlapping
    
    def _find_isolated_nodes(self, nodes: List[Node], edges: List[Edge]) -> List[Node]:
        """Find nodes that have no connections."""
        connected_nodes = set()
        
        for edge in edges:
            connected_nodes.add(edge.source_id)
            connected_nodes.add(edge.target_id)
        
        isolated = [node for node in nodes if node.id not in connected_nodes]
        return isolated
    
    def _calculate_complexity_score(self, diagram_data: DiagramData) -> float:
        """Calculate a complexity score for the diagram (0.0 to 1.0)."""
        node_count = len(diagram_data.nodes)
        edge_count = len(diagram_data.edges)
        
        if node_count == 0:
            return 0.0
        
        # Base complexity on node count and edge density
        node_complexity = min(node_count / 20.0, 1.0)  # 20+ nodes = high complexity
        edge_density = edge_count / max(node_count, 1)
        edge_complexity = min(edge_density / 3.0, 1.0)  # 3+ edges per node = high complexity
        
        # Combine factors
        complexity = (node_complexity * 0.6) + (edge_complexity * 0.4)
        return min(complexity, 1.0)
    
    def _validate_diagram_type_appropriateness(self, diagram_data: DiagramData) -> Dict[str, Union[bool, str]]:
        """Validate if the chosen diagram type is appropriate for the content."""
        node_types = [node.entity_type for node in diagram_data.nodes]
        edge_types = [edge.relationship_type for edge in diagram_data.edges]
        
        # Count entity types
        type_counts = {}
        for node_type in node_types:
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        current_type = diagram_data.diagram_type
        
        # Rules for diagram type appropriateness
        if current_type == DiagramType.ERD:
            # ERD should have mostly data/object entities
            data_entities = type_counts.get("data", 0) + type_counts.get("object", 0)
            total_entities = len(diagram_data.nodes)
            
            if total_entities > 0 and data_entities / total_entities < 0.5:
                return {
                    "is_appropriate": False,
                    "reason": "ERD should primarily contain data entities",
                    "suggested_type": "flowchart"
                }
        
        elif current_type == DiagramType.SEQUENCE:
            # Sequence diagrams should have actors and systems
            actor_entities = type_counts.get("actor", 0) + type_counts.get("system", 0)
            total_entities = len(diagram_data.nodes)
            
            if total_entities > 0 and actor_entities / total_entities < 0.3:
                return {
                    "is_appropriate": False,
                    "reason": "Sequence diagrams should have actors or systems",
                    "suggested_type": "flowchart"
                }
        
        elif current_type == DiagramType.PROCESS:
            # Process diagrams should have process entities
            process_entities = type_counts.get("process", 0)
            total_entities = len(diagram_data.nodes)
            
            if total_entities > 0 and process_entities / total_entities < 0.3:
                return {
                    "is_appropriate": False,
                    "reason": "Process diagrams should contain process entities",
                    "suggested_type": "flowchart"
                }
        
        return {"is_appropriate": True}
