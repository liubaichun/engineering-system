from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='user-register'),
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('logout/', views.LogoutView.as_view(), name='user-logout'),
    path('me/', views.MeView.as_view(), name='user-me'),
    path('change_password/', views.ChangePasswordView.as_view(), name='user-change-password'),
    path('', views.user_list, name='user-list'),
    path('<int:pk>/', views.user_detail, name='user-detail'),
]
