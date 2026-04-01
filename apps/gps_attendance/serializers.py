"""
GPS定位与考勤签到模块 - API序列化器

提供REST API的请求/响应数据序列化
"""

from rest_framework import serializers
from decimal import Decimal
from .models import (
    ProjectGPSSettings, Worker, WorkerGroup, 
    AttendanceQRCode, AttendanceRecord
)


class LocationValidateSerializer(serializers.Serializer):
    """位置校验请求参数"""
    project_id = serializers.IntegerField(required=True, help_text='项目ID')
    latitude = serializers.DecimalField(
        max_digits=10, decimal_places=7, 
        required=True, help_text='纬度'
    )
    longitude = serializers.DecimalField(
        max_digits=10, decimal_places=7,
        required=True, help_text='经度'
    )
    
    def validate_latitude(self, value):
        if value < Decimal('-90') or value > Decimal('90'):
            raise serializers.ValidationError('纬度必须在-90到90之间')
        return value
    
    def validate_longitude(self, value):
        if value < Decimal('-180') or value > Decimal('180'):
            raise serializers.ValidationError('经度必须在-180到180之间')
        return value


class GPSConfigSerializer(serializers.ModelSerializer):
    """GPS配置序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ProjectGPSSettings
        fields = [
            'project_id', 'project_name', 
            'center_latitude', 'center_longitude',
            'radius_meters', 'is_enabled', 'address'
        ]


class GPSConfigUpdateSerializer(serializers.Serializer):
    """GPS配置更新请求参数"""
    center_latitude = serializers.DecimalField(
        max_digits=10, decimal_places=7,
        required=True, help_text='工地中心纬度'
    )
    center_longitude = serializers.DecimalField(
        max_digits=10, decimal_places=7,
        required=True, help_text='工地中心经度'
    )
    radius_meters = serializers.IntegerField(
        min_value=50, max_value=5000,
        default=500, help_text='允许签到半径（米）'
    )
    is_enabled = serializers.BooleanField(default=True, help_text='是否启用GPS校验')
    address = serializers.CharField(max_length=500, required=False, default='')


class CheckInSerializer(serializers.Serializer):
    """签到请求参数"""
    qr_id = serializers.CharField(max_length=64, required=True, help_text='二维码ID')
    worker_id = serializers.IntegerField(required=True, help_text='施工人员ID')
    latitude = serializers.DecimalField(
        max_digits=10, decimal_places=7,
        required=True, help_text='签到纬度'
    )
    longitude = serializers.DecimalField(
        max_digits=10, decimal_places=7,
        required=True, help_text='签到经度'
    )
    check_in_time = serializers.DateTimeField(required=False, help_text='签到时间')
    
    def validate_latitude(self, value):
        if value < Decimal('-90') or value > Decimal('90'):
            raise serializers.ValidationError('纬度必须在-90到90之间')
        return value
    
    def validate_longitude(self, value):
        if value < Decimal('-180') or value > Decimal('180'):
            raise serializers.ValidationError('经度必须在-180到180之间')
        return value


class CheckOutSerializer(serializers.Serializer):
    """签退请求参数"""
    record_id = serializers.IntegerField(required=True, help_text='签到记录ID')
    latitude = serializers.DecimalField(
        max_digits=10, decimal_places=7,
        required=True, help_text='签退纬度'
    )
    longitude = serializers.DecimalField(
        max_digits=10, decimal_places=7,
        required=True, help_text='签退经度'
    )
    check_out_time = serializers.DateTimeField(required=False, help_text='签退时间')


class QRCodeGenerateSerializer(serializers.Serializer):
    """生成二维码请求参数"""
    project_id = serializers.IntegerField(required=True, help_text='项目ID')
    group_id = serializers.IntegerField(required=False, help_text='班组ID')
    valid_hours = serializers.IntegerField(
        min_value=1, max_value=72,
        default=24, help_text='有效期小时数'
    )


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """考勤记录序列化器"""
    worker_name = serializers.CharField(source='worker.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)
    status_text = serializers.CharField(source='get_status_display', read_only=True)
    working_hours = serializers.FloatField(read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'record_id', 'worker_name', 'project_name', 'group_name',
            'check_in_time', 'check_out_time', 'working_hours',
            'check_in_location_valid', 'check_out_location_valid',
            'status', 'status_text', 'created_at'
        ]


class CheckInResponseSerializer(serializers.Serializer):
    """签到响应数据"""
    record_id = serializers.IntegerField()
    worker_name = serializers.CharField()
    project_name = serializers.CharField()
    check_in_time = serializers.DateTimeField()
    location = serializers.DictField()
    status = serializers.CharField()
    status_text = serializers.CharField()


class CheckOutResponseSerializer(serializers.Serializer):
    """签退响应数据"""
    record_id = serializers.IntegerField()
    worker_name = serializers.CharField()
    check_in_time = serializers.DateTimeField()
    check_out_time = serializers.DateTimeField()
    working_hours = serializers.FloatField()
    location = serializers.DictField()
    status = serializers.CharField()
    status_text = serializers.CharField()


class QRCodeResponseSerializer(serializers.Serializer):
    """二维码生成响应数据"""
    qr_id = serializers.CharField()
    qr_content = serializers.CharField()
    project_name = serializers.CharField()
    group_name = serializers.CharField(allow_null=True)
    valid_from = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    qr_image_base64 = serializers.CharField()


class TodayRecordsResponseSerializer(serializers.Serializer):
    """今日记录响应数据"""
    date = serializers.CharField()
    records = AttendanceRecordSerializer(many=True)
