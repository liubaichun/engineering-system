from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import TokenAuthentication
from .models import OperationLog
from .serializers import OperationLogSerializer


class OperationLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    操作日志视图集（只读）
    - GET /api/v1/operation_logs/ — 列出操作日志（分页）
    - 管理员(admin)和项目经理(pm)可查看所有日志
    - 普通用户只能查看自己的日志
    """
    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = OperationLogPagination

    def get_queryset(self):
        user = self.request.user
        queryset = OperationLog.objects.all()

        # 普通用户只看自己的日志
        if not user.is_superuser and not (hasattr(user, 'role') and user.role in ('admin', 'pm')):
            queryset = queryset.filter(user=user)

        # 支持 model_name 过滤
        model_name = self.request.query_params.get('model_name', None)
        if model_name:
            queryset = queryset.filter(model_name=model_name)

        # 支持 action 过滤
        action = self.request.query_params.get('action', None)
        if action:
            queryset = queryset.filter(action=action)

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
