"""
任务流程API视图
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import (
    TaskType, FlowTemplate, FlowNodeTemplate, FlowTransition,
    TaskStageInstance, StageActivity
)
from .models import Task
from .serializers_flow import (
    TaskTypeSerializer, FlowTemplateSerializer, FlowTemplateCreateSerializer,
    FlowNodeTemplateSerializer, FlowTransitionSerializer,
    TaskStageInstanceSerializer, StageActivitySerializer,
    TaskWithFlowSerializer
)


class TaskTypeViewSet(viewsets.ModelViewSet):
    """任务类型管理"""
    queryset = TaskType.objects.all()
    serializer_class = TaskTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return TaskType.objects.all()
        return TaskType.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FlowTemplateViewSet(viewsets.ModelViewSet):
    """流程模板管理"""
    queryset = FlowTemplate.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FlowTemplateCreateSerializer
        return FlowTemplateSerializer
    
    def get_queryset(self):
        queryset = FlowTemplate.objects.select_related('task_type', 'created_by')
        queryset = queryset.prefetch_related('nodes')
        
        task_type = self.request.query_params.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type_id=task_type)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FlowNodeTemplateViewSet(viewsets.ModelViewSet):
    """流程节点模板管理"""
    queryset = FlowNodeTemplate.objects.all()
    serializer_class = FlowNodeTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        template_id = self.request.query_params.get('template')
        if template_id:
            return FlowNodeTemplate.objects.filter(template_id=template_id)
        return FlowNodeTemplate.objects.none()


class TaskFlowViewSet(viewsets.ModelViewSet):
    """任务流程管理"""
    queryset = Task.objects.all()
    serializer_class = TaskWithFlowSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def start_flow(self, request, pk=None):
        """启动任务流程"""
        task = self.get_object()
        
        if task.current_stage:
            return Response({'detail': '任务流程已启动'}, status=status.HTTP_400_BAD_REQUEST)
        
        template_id = request.data.get('template_id')
        if not template_id:
            return Response({'detail': '需要指定流程模板'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            template = FlowTemplate.objects.get(id=template_id)
        except FlowTemplate.DoesNotExist:
            return Response({'detail': '流程模板不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        nodes = template.nodes.order_by('order')
        first_node = None
        
        for node in nodes:
            stage_instance = TaskStageInstance.objects.create(
                task=task,
                template_node=node,
                order=node.order,
                deadline=timezone.now() + timedelta(hours=node.duration_hours) if node.duration_hours else None
            )
            
            if node.is_start:
                first_node = stage_instance
        
        task.flow_template = template
        task.current_stage = first_node.template_node_id if first_node else nodes.first().id
        task.status = 'active'
        task.save()
        
        return Response({'detail': '流程已启动', 'current_stage': task.current_stage})
    
    @action(detail=True, methods=['post'])
    def complete_node(self, request, pk=None):
        """完成当前节点"""
        task = self.get_object()
        
        current_instance = task.stage_instances.filter(
            status__in=['pending', 'in_progress']
        ).order_by('order').first()
        
        if not current_instance:
            return Response({'detail': '没有进行中的节点'}, status=status.HTTP_400_BAD_REQUEST)
        
        action_type = request.data.get('action', 'complete')
        content = request.data.get('content', '')
        
        StageActivity.objects.create(
            stage_instance=current_instance,
            operator=request.user,
            action_type=action_type,
            content=content,
            ip_address=self.get_client_ip(request)
        )
        
        current_instance.status = 'completed'
        current_instance.completed_at = timezone.now()
        current_instance.save()
        
        next_instance = task.stage_instances.filter(
            order__gt=current_instance.order,
            status='pending'
        ).order_by('order').first()
        
        if next_instance:
            task.current_stage = next_instance.template_node_id
            next_instance.status = 'in_progress'
            next_instance.started_at = timezone.now()
            next_instance.save()
        else:
            task.current_stage = None
            task.status = 'completed'
            task.completed_at = timezone.now()
        
        task.save()
        
        return Response({
            'detail': '节点已完成',
            'next_stage': task.current_stage,
            'task_status': task.status
        })
    
    @action(detail=True, methods=['post'])
    def transfer_node(self, request, pk=None):
        """转交节点"""
        task = self.get_object()
        
        current_instance = task.stage_instances.filter(
            status='in_progress'
        ).first()
        
        if not current_instance:
            return Response({'detail': '没有进行中的节点'}, status=status.HTTP_400_BAD_REQUEST)
        
        new_assignee_id = request.data.get('assignee_id')
        if not new_assignee_id:
            return Response({'detail': '需要指定接收人'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            new_assignee = User.objects.get(id=new_assignee_id)
        except User.DoesNotExist:
            return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        StageActivity.objects.create(
            stage_instance=current_instance,
            operator=request.user,
            action_type='transfer',
            content=f'转交给 {new_assignee.username}',
            ip_address=self.get_client_ip(request)
        )
        
        current_instance.assigned_to = new_assignee
        current_instance.save()
        
        return Response({'detail': '已转交', 'assignee': new_assignee.username})
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class StageActivityViewSet(viewsets.ModelViewSet):
    """节点活动记录"""
    queryset = StageActivity.objects.all()
    serializer_class = StageActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        stage_id = self.request.query_params.get('stage')
        if stage_id:
            return StageActivity.objects.filter(stage_instance_id=stage_id)
        return StageActivity.objects.none()
