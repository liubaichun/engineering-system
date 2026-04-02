from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db import models
from .models import Project
from .serializers import ProjectSerializer
from operation_logs.models import OperationLog


@method_decorator(cache_page(60 * 5), name='dispatch')
class ProjectViewSet(viewsets.ModelViewSet):
    """项目视图集 - 5分钟缓存"""
    queryset = Project.objects.select_related('manager', 'client', 'supplier').all()
    serializer_class = ProjectSerializer
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
        # 仅对 list 动作启用 queryset 级别缓存
        if self.action != 'list':
            return self._get_base_queryset()

        user = self.request.user
        status_filter = self.request.query_params.get('status', None)
        search = self.request.query_params.get('search', '')

        # 缓存 key: projects_project_{user_id}_{status}_{search}
        cache_key = f"projects_project_{user.id}_{status_filter or ''}_{search or ''}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            # 返回序列化数据的标记，由 list response 处理
            # 这里返回queryset，但将data存入request以供list renderer使用
            self._cached_response_data = cached_data
            return self._get_base_queryset().filter(
                models.Q(manager=user) | models.Q(manager__isnull=True)
            ) if user.role != 'admin' else self._get_base_queryset()

        queryset = self._get_base_queryset()
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # 序列化后缓存data（不缓存queryset）
        from .serializers import ProjectSerializer
        data = ProjectSerializer(queryset, many=True).data
        cache.set(cache_key, data, 60 * 5)  # 5分钟
        return queryset

    def list(self, request, *args, **kwargs):
        # 如果有缓存的序列化数据，直接返回
        if hasattr(self, '_cached_response_data'):
            return Response(self._cached_response_data)
        return super().list(request, *args, **kwargs)

    def _get_base_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Project.objects.select_related('manager', 'client', 'supplier').all()
        return Project.objects.filter(models.Q(manager=user) | models.Q(manager__isnull=True)).select_related('manager', 'client', 'supplier')

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

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取项目统计信息"""
        project = self.get_object()
        return Response({
            'id': project.id,
            'name': project.name,
            'status': project.status,
        })
