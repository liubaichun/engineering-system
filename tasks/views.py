from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .models import Task
from .serializers import TaskSerializer
from operation_logs.models import OperationLog


class TaskViewSet(viewsets.ModelViewSet):
    """任务视图集"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    # 安全修复：要求用户登录才能访问API
    permission_classes = [IsAuthenticated]

    def get_client_ip(self):
        """获取客户端IP"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            queryset = Task.objects.all()
        else:
            # 非admin用户：看分配给自己的任务 OR 自己管理的项目下的任务 OR 未分配负责人的任务
            queryset = Task.objects.filter(
                Q(manager=user) | Q(project__manager=user) | Q(manager__isnull=True)
            )
        
        # 支持状态过滤
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        # 支持项目过滤
        project_id = self.request.query_params.get('project', None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        # 支持负责人过滤
        manager_id = self.request.query_params.get('manager', None)
        if manager_id:
            queryset = queryset.filter(manager_id=manager_id)
        return queryset

    def perform_create(self, serializer):
        obj = serializer.save()
        OperationLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='create',
            model_name='Task',
            object_id=obj.id,
            description=f"创建了任务：{obj.name}",
            ip_address=self.get_client_ip()
        )

    def perform_update(self, serializer):
        obj = serializer.save()
        OperationLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='update',
            model_name='Task',
            object_id=obj.id,
            description=f"更新了任务：{obj.name}",
            ip_address=self.get_client_ip()
        )

    def perform_destroy(self, instance):
        task_name = instance.name
        task_id = instance.id
        instance.delete()
        OperationLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='delete',
            model_name='Task',
            object_id=task_id,
            description=f"删除了任务：{task_name}",
            ip_address=self.get_client_ip()
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
