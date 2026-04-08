from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """任务序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # assignee 直接读写 manager_display 字段（自由文本）
    assignee = serializers.CharField(
        source='manager_display',
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text='负责人（自由文本）'
    )

    class Meta:
        model = Task
        fields = [
            'id', 'name', 'project', 'project_name', 'manager', 'manager_display',
            'status', 'status_display', 'priority', 'progress', 'start_date', 'end_date',
            'description', 'assignee', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
