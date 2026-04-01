from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .signin_views import signin_api, signin_qrcode_management, signin_records

router = DefaultRouter()
router.register(r'', views.ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
    # 扫码签到API（允许匿名访问）
    path('signin/', signin_api, name='signin-api'),
    # 签到二维码管理API（需要登录）
    path('signin/qrcode/', signin_qrcode_management, name='signin-qrcode'),
    # 签到记录查询（需要登录）
    path('signin/records/', signin_records, name='signin-records'),
]
