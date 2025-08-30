from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DiagramEdgeViewSet,
    DiagramNodeViewSet,
    EntityViewSet,
    ProjectViewSet,
    RelationshipViewSet,
    SpecificationViewSet,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"entities", EntityViewSet, basename="entity")
router.register(r"relationships", RelationshipViewSet, basename="relationship")
router.register(r"diagram-nodes", DiagramNodeViewSet, basename="diagramnode")
router.register(r"diagram-edges", DiagramEdgeViewSet, basename="diagramedge")
router.register(r"specifications", SpecificationViewSet, basename="specification")

urlpatterns = [
    path("api/", include(router.urls)),
]
