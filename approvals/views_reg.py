"""
独立的用户注册审批视图（使用users app的模型）
与现有的付款/立项审批系统完全分离
"""
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from users.models import ApprovalFlow, ApprovalRecord, User


class ApprovalFlowSerializer(serializers.ModelSerializer):
    """审批流序列化器"""
    applicant_name = serializers.CharField(source='applicant.username', read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalFlow
        fields = [
            'id', 'applicant', 'applicant_name', 'flow_type',
            'target_object_type', 'target_object_id',
            'status', 'status_display', 'current_node',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_status_display(self, obj):
        choices = {'pending': '待审批', 'approved': '已通过', 'rejected': '已拒绝', 'cancelled': '已取消'}
        return choices.get(obj.status, obj.status)


class ApprovalRecordSerializer(serializers.ModelSerializer):
    """审批记录序列化器"""
    approver_name = serializers.CharField(source='approver.username', read_only=True, allow_null=True)
    action_display = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalRecord
        fields = ['id', 'flow', 'approver', 'approver_name', 'node', 'action', 'action_display', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_action_display(self, obj):
        choices = {'approve': '批准', 'reject': '拒绝', 'transfer': '转交', 'pending': '待处理'}
        return choices.get(obj.action, obj.action)


class UserRegistrationApprovalViewSet(viewsets.ViewSet):
    """
    用户注册审批API（独立于业务审批）

    POST   /api/v1/approvals/register/          创建注册审批流
    GET    /api/v1/approvals/register/          列表（my_pending/my_applied/all）
    GET    /api/v1/approvals/register/{id}/     详情
    POST   /api/v1/approvals/register/{id}/approve/  审批通过
    POST   /api/v1/approvals/register/{id}/reject/  审批拒绝
    """
    permission_classes = [IsAuthenticated]

    def _find_approver(self, applicant, flow_type):
        """找审批人：管理员 > 项目经理"""
        # 管理员
        admin = User.objects.filter(role='admin', is_active=True).first()
        if admin:
            return admin
        # 项目经理
        pm = User.objects.filter(role='pm', is_active=True).first()
        if pm:
            return pm
        return None

    def list(self, request):
        user = request.user
        filter_type = request.query_params.get('filter', 'my_pending')

        qs = ApprovalFlow.objects.filter(flow_type='user_registration').order_by('-created_at')

        if filter_type == 'my_pending':
            qs = qs.filter(status='pending', records__approver=user, records__action='pending')
        elif filter_type == 'my_applied':
            qs = qs.filter(applicant=user)
        elif filter_type == 'all' and user.role == 'admin':
            pass
        else:
            qs = qs.filter(applicant=user)

        return Response(ApprovalFlowSerializer(qs.distinct(), many=True).data)

    def create(self, request):
        """创建注册审批流（用户注册时调用）"""
        from users.models import UsersPendingApproval
        from users.serializers import UserRegistrationSerializer

        # 直接使用User数据创建审批流
        data = request.data
        username = data.get('username')
        email = data.get('email', '')
        role = data.get('role', 'worker')

        if not username:
            return Response({'detail': '用户名必填'}, status=400)

        # 检查是否已有待审批或已通过的用户
        existing = User.objects.filter(username=username).exists()
        pending = UsersPendingApproval.objects.filter(username=username, status='pending').exists()
        if existing or pending:
            return Response({'detail': '用户名已存在'}, status=400)

        # 创建审批流
        flow = ApprovalFlow.objects.create(
            applicant=request.user,
            flow_type='user_registration',
            target_object_type='User',
            target_object_id=None,
            status='pending',
            current_node=1,
        )

        # 找审批人
        first_approver = self._find_approver(request.user, 'user_registration')
        if not first_approver:
            return Response({'detail': '系统无审批人配置，请联系管理员'}, status=500)

        # 创建审批记录
        ApprovalRecord.objects.create(
            flow=flow,
            approver=first_approver,
            node=1,
            action='pending',
            comment='用户注册待审批',
        )

        return Response(ApprovalFlowSerializer(flow).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        try:
            flow = ApprovalFlow.objects.get(pk=pk)
        except ApprovalFlow.DoesNotExist:
            return Response({'detail': '不存在'}, status=404)

        records = ApprovalRecord.objects.filter(flow=flow).order_by('node', 'created_at')
        data = ApprovalFlowSerializer(flow).data
        data['records'] = ApprovalRecordSerializer(records, many=True).data
        return Response(data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        try:
            flow = ApprovalFlow.objects.get(pk=pk)
        except ApprovalFlow.DoesNotExist:
            return Response({'detail': '不存在'}, status=404)

        # 权限检查
        if flow.status != 'pending':
            return Response({'detail': '流程已处理'}, status=400)

        current_record = ApprovalRecord.objects.filter(
            flow=flow, node=flow.current_node, approver=request.user, action='pending'
        ).first()
        if not current_record:
            return Response({'detail': '您不是当前审批人'}, status=403)

        comment = request.data.get('comment', '')

        # 记录审批
        current_record.action = 'approve'
        current_record.comment = comment
        current_record.save()

        # 完成流程
        flow.status = 'approved'
        flow.save()

        return Response({'detail': '审批通过', 'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        try:
            flow = ApprovalFlow.objects.get(pk=pk)
        except ApprovalFlow.DoesNotExist:
            return Response({'detail': '不存在'}, status=404)

        if flow.status != 'pending':
            return Response({'detail': '流程已处理'}, status=400)

        current_record = ApprovalRecord.objects.filter(
            flow=flow, node=flow.current_node, approver=request.user, action='pending'
        ).first()
        if not current_record:
            return Response({'detail': '您不是当前审批人'}, status=403)

        comment = request.data.get('comment', '')
        current_record.action = 'reject'
        current_record.comment = comment
        current_record.save()

        flow.status = 'rejected'
        flow.save()

        return Response({'detail': '已拒绝', 'status': 'rejected'})

    @action(detail=False, methods=['get'])
    def my_pending(self, request):
        """我的待审批列表"""
        user = request.user
        flows = ApprovalFlow.objects.filter(
            status='pending',
            records__approver=user,
            records__action='pending'
        ).distinct().order_by('-created_at')
        return Response(ApprovalFlowSerializer(flows, many=True).data)

    @action(detail=False, methods=['get'])
    def my_applied(self, request):
        """我发起的审批"""
        flows = ApprovalFlow.objects.filter(applicant=request.user).order_by('-created_at')
        return Response(ApprovalFlowSerializer(flows, many=True).data)
