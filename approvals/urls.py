from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApprovalFlowViewSet
from .views_reg import UserRegistrationApprovalViewSet

router = DefaultRouter()
router.register(r'approvals', ApprovalFlowViewSet, basename='approval')

urlpatterns = [
    path('', include(router.urls)),
    # 用户注册审批（独立路由）
    path('register/', UserRegistrationApprovalViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='register-approval'),
    path('register/<int:pk>/', UserRegistrationApprovalViewSet.as_view({
        'get': 'retrieve',
    }), name='register-approval-detail'),
    path('register/<int:pk>/approve/', UserRegistrationApprovalViewSet.as_view({
        'post': 'approve'
    }), name='register-approval-approve'),
    path('register/<int:pk>/reject/', UserRegistrationApprovalViewSet.as_view({
        'post': 'reject'
    }), name='register-approval-reject'),
    path('register/my_pending/', UserRegistrationApprovalViewSet.as_view({
        'get': 'my_pending'
    }), name='register-approval-my-pending'),
    path('register/my_applied/', UserRegistrationApprovalViewSet.as_view({
        'get': 'my_applied'
    }), name='register-approval-my-applied'),
]
