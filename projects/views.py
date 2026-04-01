from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models
from .models import Project
from .serializers import ProjectSerializer
from operation_logs.models import OperationLog


class ProjectViewSet(viewsets.ModelViewSet):
    """项目视图集"""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
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
            queryset = Project.objects.all()
        else:
            # dev用户只能看到与自己关联的项目（仅manager字段关联）
            queryset = Project.objects.filter(manager=user)

        # 支持状态过滤
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        obj = serializer.save()
        OperationLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='create',
            model_name='Project',
            object_id=obj.id,
            description=f"创建了项目：{obj.name}",
            ip_address=self.get_client_ip()
        )

    def perform_update(self, serializer):
        obj = serializer.save()
        OperationLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='update',
            model_name='Project',
            object_id=obj.id,
            description=f"更新了项目：{obj.name}",
            ip_address=self.get_client_ip()
        )

    def perform_destroy(self, instance):
        project_name = instance.name
        project_id = instance.id
        instance.delete()
        OperationLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='delete',
            model_name='Project',
            object_id=project_id,
            description=f"删除了项目：{project_name}",
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

    def destroy(self, request, *args, **kwargs):
        """删除项目 - 仅限系统管理员"""
        user = request.user
        if not user.is_authenticated:
            return Response({'detail': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
        # 检查管理员权限
        if hasattr(user, 'role') and user.role != 'admin':
            return Response({'detail': '只有系统管理员可以删除项目'}, status=status.HTTP_403_FORBIDDEN)
        if not user.is_superuser and (not hasattr(user, 'role') or user.role != 'admin'):
            return Response({'detail': '只有系统管理员可以删除项目'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
