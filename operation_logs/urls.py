from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OperationLogViewSet

router = DefaultRouter()
router.register(r'', OperationLogViewSet, basename='operationlog')

urlpatterns = [
    path('', include(router.urls)),
]
