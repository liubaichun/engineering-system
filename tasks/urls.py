from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.TaskViewSet, basename='task')

# 动态导入flow视图避免循环导入
def get_flow_urls():
    from .views_flow import (
        TaskTypeViewSet, FlowTemplateViewSet, FlowNodeTemplateViewSet,
        TaskFlowViewSet, StageActivityViewSet
    )
    
    flow_router = DefaultRouter()
    flow_router.register(r'types', TaskTypeViewSet, basename='task-type')
    flow_router.register(r'flows/templates', FlowTemplateViewSet, basename='flow-template')
    flow_router.register(r'flows/nodes', FlowNodeTemplateViewSet, basename='flow-node')
    flow_router.register(r'flows', TaskFlowViewSet, basename='task-flow')
    flow_router.register(r'activities', StageActivityViewSet, basename='stage-activity')
    
    return flow_router.urls

urlpatterns = [
    path('', include(router.urls)),
    path('flow/', include(get_flow_urls())),
]
