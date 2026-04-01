from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, WorkerGroupViewSet, WorkerViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"groups",   WorkerGroupViewSet, basename="group")
router.register(r"workers",  WorkerViewSet,       basename="worker")

urlpatterns = [
    path("", include(router.urls)),
]
