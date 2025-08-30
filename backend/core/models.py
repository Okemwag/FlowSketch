import uuid

from django.contrib.auth.models import User
from django.db import models


class Project(models.Model):
    """
    Represents a FlowSketch project containing diagrams and specifications.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True, null=True, unique=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class Entity(models.Model):
    """
    Represents an entity in the canonical data model (e.g., User, Order, Process).
    """

    ENTITY_TYPES = [
        ("object", "Object"),
        ("process", "Process"),
        ("actor", "Actor"),
        ("data", "Data"),
        ("system", "System"),
        ("event", "Event"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="entities"
    )
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    properties = models.JSONField(default=dict)  # Store entity properties as JSON
    position_x = models.FloatField(null=True, blank=True)  # Diagram position
    position_y = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict)  # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["project", "name"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.type})"


class Relationship(models.Model):
    """
    Represents a relationship between two entities.
    """

    RELATIONSHIP_TYPES = [
        ("association", "Association"),
        ("composition", "Composition"),
        ("aggregation", "Aggregation"),
        ("inheritance", "Inheritance"),
        ("dependency", "Dependency"),
        ("flow", "Flow"),
        ("sequence", "Sequence"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="relationships"
    )
    source = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="outgoing_relationships"
    )
    target = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="incoming_relationships"
    )
    type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    label = models.CharField(max_length=255, blank=True)
    properties = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["project", "source", "target", "type"]

    def __str__(self):
        return f"{self.source.name} -> {self.target.name} ({self.type})"


class DiagramNode(models.Model):
    """
    Represents a visual node in the diagram corresponding to an entity.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.OneToOneField(
        Entity, on_delete=models.CASCADE, related_name="diagram_node"
    )
    position_x = models.FloatField()
    position_y = models.FloatField()
    width = models.FloatField(default=120)
    height = models.FloatField(default=60)
    style = models.JSONField(default=dict)  # Node styling (color, shape, etc.)
    label = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Node: {self.label}"


class DiagramEdge(models.Model):
    """
    Represents a visual edge in the diagram corresponding to a relationship.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relationship = models.OneToOneField(
        Relationship, on_delete=models.CASCADE, related_name="diagram_edge"
    )
    source_node = models.ForeignKey(
        DiagramNode, on_delete=models.CASCADE, related_name="outgoing_edges"
    )
    target_node = models.ForeignKey(
        DiagramNode, on_delete=models.CASCADE, related_name="incoming_edges"
    )
    style = models.JSONField(default=dict)  # Edge styling (color, thickness, etc.)
    label = models.CharField(max_length=255, blank=True)
    path = models.JSONField(default=list)  # Path points for curved edges
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Edge: {self.source_node.label} -> {self.target_node.label}"


class Specification(models.Model):
    """
    Represents the generated specification document for a project.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="specification"
    )
    title = models.CharField(max_length=255)
    content = models.TextField()  # Markdown content
    sections = models.JSONField(default=list)  # Structured sections
    acceptance_criteria = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Spec: {self.title}"


class CanonicalModel(models.Model):
    """
    Represents the canonical data model that maintains sync between diagram and spec.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="canonical_model"
    )
    entities_data = models.JSONField(default=list)  # Serialized entities
    relationships_data = models.JSONField(default=list)  # Serialized relationships
    business_rules = models.JSONField(default=list)
    version = models.IntegerField(default=1)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Canonical Model v{self.version} for {self.project.name}"
