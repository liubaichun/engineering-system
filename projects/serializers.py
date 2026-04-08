from rest_framework import serializers
from .models import Project
from users.serializers import UserSerializer


class ProjectSerializer(serializers.ModelSerializer):
    """项目序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # 使用 manager_display 自由文本字段显示
    manager_name = serializers.CharField(source='manager_display', read_only=True, allow_null=True, allow_blank=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'client', 'supplier', 'status', 'status_display',
            'budget', 'start_date', 'end_date', 'manager', 'manager_display', 'manager_name',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
