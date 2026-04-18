"""
流程引擎 URL 配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.flow_engine.views import FlowInstanceViewSet, StageActivityViewSet

app_name = 'flow_engine'

router = DefaultRouter()
router.register(r'flows', FlowInstanceViewSet, basename='flow-instance')
router.register(r'activities', StageActivityViewSet, basename='stage-activity')

urlpatterns = [
    path('', include(router.urls)),
]
