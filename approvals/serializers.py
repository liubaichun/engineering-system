from rest_framework import serializers
from .models import ApprovalFlow, ApprovalNode
from django.contrib.auth import get_user_model

User = get_user_model()


class ApprovalNodeSerializer(serializers.ModelSerializer):
    """审批节点序列化器"""
    approver_name = serializers.CharField(source='approver.username', read_only=True)
    approver_role = serializers.CharField(source='approver.role', read_only=True)

    class Meta:
        model = ApprovalNode
        fields = [
            'id', 'flow', 'approver', 'approver_name', 'approver_role',
            'node_order', 'status', 'comment', 'decided_at'
        ]
        read_only_fields = ['id', 'decided_at']


class ApprovalFlowListSerializer(serializers.ModelSerializer):
    """审批流列表序列化器（简化版）"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    flow_type_display = serializers.CharField(source='get_flow_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    expense_amount = serializers.DecimalField(
        source='expense.amount', max_digits=12, decimal_places=2,
        read_only=True, allow_null=True
    )
    current_node = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalFlow
        fields = [
            'id', 'name', 'flow_type', 'flow_type_display', 'status', 'status_display',
            'created_by', 'created_by_name', 'created_at',
            'project', 'project_name', 'expense', 'expense_amount',
            'amount', 'description', 'current_node'
        ]
        read_only_fields = ['id', 'created_at']

    def get_current_node(self, obj):
        """获取当前待审批节点"""
        pending_node = obj.nodes.filter(status='pending').order_by('node_order').first()
        if pending_node:
            return {
                'id': pending_node.id,
                'approver': pending_node.approver_id,
                'approver_name': pending_node.approver.username if pending_node.approver else None,
                'node_order': pending_node.node_order
            }
        return None


class ApprovalFlowDetailSerializer(serializers.ModelSerializer):
    """审批流详情序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    flow_type_display = serializers.CharField(source='get_flow_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    expense_amount = serializers.DecimalField(
        source='expense.amount', max_digits=12, decimal_places=2,
        read_only=True, allow_null=True
    )
    nodes = ApprovalNodeSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalFlow
        fields = [
            'id', 'name', 'flow_type', 'flow_type_display', 'status', 'status_display',
            'created_by', 'created_by_name', 'created_at',
            'project', 'project_name', 'expense', 'expense_amount',
            'amount', 'description', 'nodes'
        ]
        read_only_fields = ['id', 'created_at']


class ApprovalFlowCreateSerializer(serializers.ModelSerializer):
    """创建审批流序列化器"""

    class Meta:
        model = ApprovalFlow
        fields = ['id', 'name', 'flow_type', 'project', 'expense', 'amount', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        flow_type = attrs.get('flow_type')
        project = attrs.get('project')
        expense = attrs.get('expense')
        amount = attrs.get('amount')

        if flow_type == 'project' and not project:
            raise serializers.ValidationError({'project': '立项审批必须关联项目'})
        if flow_type == 'payment' and not expense:
            raise serializers.ValidationError({'expense': '付款审批必须关联支出记录'})
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({'amount': '审批金额必须大于零'})

        return attrs

    def create(self, validated_data):
        # 创建审批流
        flow = ApprovalFlow.objects.create(**validated_data)

        # 自动创建第一个审批节点（当前用户为审批人）
        request = self.context.get('request')
        if request and request.user:
            ApprovalNode.objects.create(
                flow=flow,
                approver=request.user,
                node_order=1,
                status='pending'
            )

        return flow


class ApprovalActionSerializer(serializers.Serializer):
    """审批操作序列化器（批准/拒绝）"""
    comment = serializers.CharField(required=False, allow_blank=True, default='')
