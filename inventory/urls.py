from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Register longer prefixes first to avoid conflict with <pk> patterns
router.register(r'materials/io', views.MaterialIOViewSet, basename='material-io')
router.register(r'materials', views.MaterialViewSet, basename='material')
router.register(r'equipment/io', views.EquipmentIOViewSet, basename='equipment-io')
router.register(r'equipment', views.EquipmentViewSet, basename='equipment')

urlpatterns = [
    path('', include(router.urls)),
]
