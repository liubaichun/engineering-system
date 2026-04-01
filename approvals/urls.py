from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApprovalFlowViewSet

router = DefaultRouter()
router.register(r'approvals', ApprovalFlowViewSet, basename='approval')

urlpatterns = [
    path('', include(router.urls)),
]
