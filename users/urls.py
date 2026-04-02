from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterApprovalView.as_view(), name='user-register'),
    path('register/old/', views.RegisterView.as_view(), name='user-register-old'),
    path('pending/', views.PendingUserListView.as_view(), name='pending-users'),
    path('pending/<int:pending_id>/activate/', views.PendingUserActivateView.as_view(), name='pending-activate'),
    path('pending/<int:pending_id>/reject/', views.PendingUserRejectView.as_view(), name='pending-reject'),
    
    # Phase 3: Approval Flow
    path('approvals/', views.ApprovalFlowCreateView.as_view(), name='approval-create'),
    path('approvals/list/', views.ApprovalFlowListView.as_view(), name='approval-list'),
    path('approvals/<int:flow_id>/', views.ApprovalFlowDetailView.as_view(), name='approval-detail'),
    path('approvals/<int:flow_id>/approve/', views.ApprovalFlowApproveView.as_view(), name='approval-approve'),
    path('approvals/<int:flow_id>/reject/', views.ApprovalFlowRejectView.as_view(), name='approval-reject'),
    path('approvals/manager_pending/', views.ManagerPendingListView.as_view(), name='approval-manager-pending'),
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('logout/', views.LogoutView.as_view(), name='user-logout'),
    path('me/', views.MeView.as_view(), name='user-me'),
    path('change_password/', views.ChangePasswordView.as_view(), name='user-change-password'),
    path('', views.user_list, name='user-list'),
    path('<int:pk>/', views.user_detail, name='user-detail'),
]
