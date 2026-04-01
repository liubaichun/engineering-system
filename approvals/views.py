from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import ApprovalFlow, ApprovalNode
from .serializers import (
    ApprovalFlowListSerializer,
    ApprovalFlowDetailSerializer,
    ApprovalFlowCreateSerializer,
    ApprovalActionSerializer,
    ApprovalNodeSerializer
)


class ApprovalFlowViewSet(viewsets.ModelViewSet):
    """
    审批流 ViewSet

    list:       GET /api/v1/approvals/ - 列出当前用户的待审批列表
    create:     POST /api/v1/approvals/ - 创建审批
    retrieve:   GET /api/v1/approvals/{id}/ - 审批详情
    approve:    PATCH /api/v1/approvals/{id}/approve/ - 批准
    reject:     PATCH /api/v1/approvals/{id}/reject/ - 拒绝
    my:        GET /api/v1/approvals/my/ - 我发起的审批
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = ApprovalFlow.objects.all()

        # 默认显示待当前用户审批的记录
        if not self.action in ['my', 'list', 'retrieve']:
            return queryset

        # 过滤：当前用户是审批节点中待审批的审批人
        pending_approval_ids = ApprovalNode.objects.filter(
            approver=user,
            status='pending'
        ).values_list('flow_id', flat=True)

        return queryset.filter(id__in=pending_approval_ids)

    def get_serializer_class(self):
        if self.action == 'create':
            return ApprovalFlowCreateSerializer
        if self.action == 'list':
            return ApprovalFlowListSerializer
        if self.action == 'retrieve':
            return ApprovalFlowDetailSerializer
        if self.action in ['approve', 'reject']:
            return ApprovalActionSerializer
        return ApprovalFlowListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """
        批准审批
        PATCH /api/v1/approvals/{id}/approve/
        """
        flow = self.get_object()

        # 防止自己审批自己
        if flow.created_by == request.user:
            return Response({'error': '不能审批自己创建的申请'}, status=403)

        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 获取当前用户的待审批节点
        current_node = flow.nodes.filter(
            approver=request.user,
            status='pending'
        ).order_by('node_order').first()

        if not current_node:
            return Response(
                {'error': '您没有待审批的节点'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 更新节点状态
        current_node.status = 'approved'
        current_node.comment = serializer.validated_data.get('comment', '')
        current_node.decided_at = timezone.now()
        current_node.save()

        # 检查是否所有节点都已审批
        pending_nodes = flow.nodes.filter(status='pending').exists()
        if not pending_nodes:
            flow.status = 'approved'
            flow.save()

        return Response({
            'message': '审批已批准',
            'flow_status': flow.status,
            'node_status': current_node.status
        })

    @action(detail=True, methods=['patch'], url_path='reject')
    def reject(self, request, pk=None):
        """
        拒绝审批
        PATCH /api/v1/approvals/{id}/reject/
        """
        flow = self.get_object()

        # 防止自己审批自己
        if flow.created_by == request.user:
            return Response({'error': '不能审批自己创建的申请'}, status=403)

        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 获取当前用户的待审批节点
        current_node = flow.nodes.filter(
            approver=request.user,
            status='pending'
        ).order_by('node_order').first()

        if not current_node:
            return Response(
                {'error': '您没有待审批的节点'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 更新节点状态
        current_node.status = 'rejected'
        current_node.comment = serializer.validated_data.get('comment', '')
        current_node.decided_at = timezone.now()
        current_node.save()

        # 审批被拒绝，整个流程终止
        flow.status = 'rejected'
        flow.save()

        return Response({
            'message': '审批已拒绝',
            'flow_status': flow.status,
            'node_status': current_node.status
        })

    @action(detail=False, methods=['get'], url_path='my')
    def my(self, request):
        """
        我发起的审批
        GET /api/v1/approvals/my/
        """
        user = request.user
        queryset = ApprovalFlow.objects.filter(created_by=user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ApprovalFlowListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ApprovalFlowListSerializer(queryset, many=True)
        return Response(serializer.data)
