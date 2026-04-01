from rest_framework import serializers
from .models import OperationLog


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器"""
    username = serializers.CharField(source='user.username', read_only=True, default='')
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = OperationLog
        fields = [
            'id',
            'user',
            'username',
            'action',
            'action_display',
            'model_name',
            'object_id',
            'description',
            'ip_address',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
