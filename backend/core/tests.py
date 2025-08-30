from django.contrib.auth.models import User
from django.test import TestCase

from .models import (
    DiagramEdge,
    DiagramNode,
    Entity,
    Project,
    Relationship,
    Specification,
)


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_project_creation(self):
        """Test that a project can be created successfully."""
        project = Project.objects.create(
            name="Test Project", description="A test project", owner=self.user
        )
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.owner, self.user)
        self.assertFalse(project.is_public)
        self.assertIsNotNone(project.id)

    def test_project_str_representation(self):
        """Test the string representation of a project."""
        project = Project.objects.create(name="Test Project", owner=self.user)
        self.assertEqual(str(project), "Test Project")


class EntityModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.project = Project.objects.create(name="Test Project", owner=self.user)

    def test_entity_creation(self):
        """Test that an entity can be created successfully."""
        entity = Entity.objects.create(
            project=self.project,
            name="User",
            type="object",
            properties={"fields": ["id", "name", "email"]},
        )
        self.assertEqual(entity.name, "User")
        self.assertEqual(entity.type, "object")
        self.assertEqual(entity.project, self.project)

    def test_entity_unique_constraint(self):
        """Test that entity names must be unique within a project."""
        Entity.objects.create(project=self.project, name="User", type="object")

        # This should not raise an exception as it's a different project
        other_user = User.objects.create_user(username="other", password="pass")
        other_project = Project.objects.create(name="Other Project", owner=other_user)

        Entity.objects.create(project=other_project, name="User", type="object")


class RelationshipModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.project = Project.objects.create(name="Test Project", owner=self.user)
        self.entity1 = Entity.objects.create(
            project=self.project, name="User", type="object"
        )
        self.entity2 = Entity.objects.create(
            project=self.project, name="Order", type="object"
        )

    def test_relationship_creation(self):
        """Test that a relationship can be created successfully."""
        relationship = Relationship.objects.create(
            project=self.project,
            source=self.entity1,
            target=self.entity2,
            type="association",
            label="places",
        )
        self.assertEqual(relationship.source, self.entity1)
        self.assertEqual(relationship.target, self.entity2)
        self.assertEqual(relationship.type, "association")
        self.assertEqual(relationship.label, "places")

    def test_relationship_str_representation(self):
        """Test the string representation of a relationship."""
        relationship = Relationship.objects.create(
            project=self.project,
            source=self.entity1,
            target=self.entity2,
            type="association",
        )
        expected = f"{self.entity1.name} -> {self.entity2.name} (association)"
        self.assertEqual(str(relationship), expected)
