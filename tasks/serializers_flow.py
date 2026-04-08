"""
任务流程序列化器
"""

from rest_framework import serializers
from .models import (
    TaskType, FlowTemplate, FlowNodeTemplate, FlowTransition,
    TaskStageInstance, StageActivity
)
from .models import Task


class TaskTypeSerializer(serializers.ModelSerializer):
    """任务类型序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = TaskType
        fields = [
            'id', 'name', 'description', 'is_active',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class FlowNodeTemplateSerializer(serializers.ModelSerializer):
    """流程节点模板序列化器"""
    class Meta:
        model = FlowNodeTemplate
        fields = [
            'id', 'name', 'order', 'duration_hours',
            'responsible_type', 'responsible_users', 'responsible_roles',
            'allowed_actions', 'notify_on_assign', 'notify_on_overdue',
            'is_start', 'is_end'
        ]


class FlowTransitionSerializer(serializers.ModelSerializer):
    """流程连线序列化器"""
    from_node_name = serializers.CharField(source='from_node.name', read_only=True)
    to_node_name = serializers.CharField(source='to_node.name', read_only=True)
    
    class Meta:
        model = FlowTransition
        fields = [
            'id', 'from_node', 'from_node_name', 'to_node', 'to_node_name', 'condition'
        ]


class FlowTemplateSerializer(serializers.ModelSerializer):
    """流程模板序列化器"""
    task_type_name = serializers.CharField(source='task_type.name', read_only=True)
    nodes = FlowNodeTemplateSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FlowTemplate
        fields = [
            'id', 'name', 'task_type', 'task_type_name', 'description',
            'is_active', 'nodes', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class FlowTemplateCreateSerializer(serializers.ModelSerializer):
    """流程模板创建序列化器（包含节点）"""
    nodes = FlowNodeTemplateSerializer(many=True, required=False)
    
    class Meta:
        model = FlowTemplate
        fields = ['id', 'name', 'task_type', 'description', 'is_active', 'nodes']
    
    def create(self, validated_data):
        nodes_data = validated_data.pop('nodes', [])
        flow_template = FlowTemplate.objects.create(**validated_data)
        
        for i, node_data in enumerate(nodes_data):
            FlowNodeTemplate.objects.create(
                template=flow_template,
                order=i,
                **node_data
            )
        
        return flow_template


class StageActivitySerializer(serializers.ModelSerializer):
    """节点活动记录序列化器"""
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    
    class Meta:
        model = StageActivity
        fields = [
            'id', 'stage_instance', 'operator', 'operator_name',
            'action_type', 'content', 'attachments', 'ip_address', 'created_at'
        ]


class TaskStageInstanceSerializer(serializers.ModelSerializer):
    """任务阶段实例序列化器"""
    node_name = serializers.CharField(source='template_node.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    activities = StageActivitySerializer(many=True, read_only=True)
    
    class Meta:
        model = TaskStageInstance
        fields = [
            'id', 'task', 'template_node', 'node_name', 'order',
            'assigned_to', 'assigned_to_name', 'status',
            'started_at', 'completed_at', 'deadline', 'is_overdue',
            'activities', 'created_at', 'updated_at'
        ]


class TaskWithFlowSerializer(serializers.ModelSerializer):
    """带流程的任务序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    manager_name = serializers.CharField(source='manager.username', read_only=True, allow_null=True)
    stage_instances = TaskStageInstanceSerializer(many=True, read_only=True)
    task_type_name = serializers.CharField(source='task_type.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'name', 'project', 'project_name',
            'manager', 'manager_name',
            'task_type', 'task_type_name',
            'flow_template', 'current_stage',
            'status', 'priority', 'progress',
            'start_date', 'end_date', 'deadline',
            'description', 'stage_instances',
            'created_by', 'created_at', 'updated_at'
        ]
