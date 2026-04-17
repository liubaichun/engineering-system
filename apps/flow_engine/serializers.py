"""
流程引擎 REST API 序列化器
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from tasks.models import StageActivity, TaskStageInstance, Task, FlowTemplate, FlowNodeTemplate

User = get_user_model()


class StageActivitySerializer(serializers.ModelSerializer):
    """节点活动记录序列化器"""
    operator_name = serializers.CharField(source='operator.username', read_only=True, allow_null=True)
    stage_name = serializers.CharField(source='stage_instance.template_node.name', read_only=True)
    
    class Meta:
        model = StageActivity
        fields = [
            'id', 'stage_instance', 'stage_name', 'operator', 'operator_name',
            'action_type', 'content', 'attachments', 'ip_address', 'created_at'
        ]


class TaskFlowInstanceSerializer(serializers.ModelSerializer):
    """流程实例序列化器"""
    task_name = serializers.CharField(source='task.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True, allow_null=True)
    current_node_name = serializers.CharField(source='current_node.name', read_only=True, allow_null=True)
    initiator_name = serializers.CharField(source='initiator.username', read_only=True, allow_null=True)
    
    class Meta:
        from apps.flow_engine.models import TaskFlowInstance
        model = TaskFlowInstance
        fields = [
            'id', 'task', 'task_name', 'template', 'template_name', 'status',
            'initiator', 'initiator_name', 'current_node', 'current_node_name',
            'started_at', 'completed_at', 'deadline', 'is_overdue',
            'overdue_notified', 'context_data', 'created_at', 'updated_at'
        ]


class CreateFlowSerializer(serializers.Serializer):
    """创建流程序列化器"""
    task_id = serializers.IntegerField()
    template_id = serializers.IntegerField(required=False, allow_null=True)
    context_data = serializers.JSONField(required=False, default=dict)


class TransitionFlowSerializer(serializers.Serializer):
    """流转流程序列化器"""
    target_node_id = serializers.IntegerField(required=False, allow_null=True)
    action = serializers.ChoiceField(choices=['complete', 'reject'], default='complete')
    remark = serializers.CharField(required=False, allow_blank=True, default='')


class TransferFlowSerializer(serializers.Serializer):
    """转交流程序列化器"""
    target_user_id = serializers.IntegerField()
    remark = serializers.CharField(required=False, allow_blank=True, default='')


class FlowProgressSerializer(serializers.Serializer):
    """流程进度序列化器"""
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    progress = serializers.FloatField()


class FlowNodeTemplateSerializer(serializers.Serializer):
    """流程节点模板序列化器"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    order = serializers.IntegerField()
    duration_hours = serializers.IntegerField()
    responsible_type = serializers.CharField()
    allowed_actions = serializers.ListField()
    is_start = serializers.BooleanField()
    is_end = serializers.BooleanField()
