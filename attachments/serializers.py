from rest_framework import serializers
from .models import Attachment, ProjectAttachment, TaskAttachment, AttachmentCategory, ProjectFileFolder, AttachmentVersion, AttachmentDownloadLog


class AttachmentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttachmentCategory
        fields = ['id', 'name', 'code', 'project_type', 'parent', 'order']
        read_only_fields = ['id']


class AttachmentSerializer(serializers.ModelSerializer):
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    uploader_name = serializers.CharField(source='uploader.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    category_code = serializers.CharField(source='category.code', read_only=True, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=AttachmentCategory.objects.all(), required=False, allow_null=True, write_only=True
    )
    # uploader 字段不再前端传递，后端自动从 request.user 获取
    uploader = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Attachment
        fields = [
            'id', 'name', 'file', 'file_type', 'file_type_display',
            'file_size', 'md5', 'uploader', 'uploader_name', 'created_at',
            'category', 'category_name', 'category_code', 'sub_category'
        ]
        read_only_fields = ['id', 'created_at', 'uploader']

    def create(self, validated_data):
        # 自动设置 uploader 为当前登录用户
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['uploader'] = request.user
        return super().create(validated_data)


class ProjectAttachmentSerializer(serializers.ModelSerializer):
    attachment_detail = AttachmentSerializer(source='attachment', read_only=True)

    class Meta:
        model = ProjectAttachment
        fields = ['id', 'project', 'attachment', 'attachment_detail']


class TaskAttachmentSerializer(serializers.ModelSerializer):
    attachment_detail = AttachmentSerializer(source='attachment', read_only=True)

    class Meta:
        model = TaskAttachment
        fields = ['id', 'task', 'attachment', 'attachment_detail']


class ProjectFileFolderSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=AttachmentCategory.objects.all(), required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = ProjectFileFolder
        fields = ['id', 'project', 'parent', 'name', 'category', 'category_name', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class AttachmentVersionSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, allow_null=True)

    class Meta:
        model = AttachmentVersion
        fields = ['id', 'attachment', 'version', 'file', 'file_size', 'checksum', 'uploaded_by', 'uploaded_by_name', 'uploaded_at', 'change_log']
        read_only_fields = ['id', 'uploaded_at']


class AttachmentDownloadLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True, allow_null=True)

    class Meta:
        model = AttachmentDownloadLog
        fields = ['id', 'attachment', 'user', 'user_name', 'downloaded_at', 'ip_address', 'user_agent', 'action']
        read_only_fields = ['id', 'downloaded_at']


class AttachmentListSerializer(serializers.ModelSerializer):
    """附件列表序列化器（含缩略图）"""
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    uploader_name = serializers.CharField(source='uploader.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    category_code = serializers.CharField(source='category.code', read_only=True, allow_null=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            'id', 'name', 'file_type', 'file_type_display',
            'file_size', 'uploader_name', 'created_at',
            'category_name', 'category_code', 'sub_category',
            'thumbnail', 'thumbnail_url'
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/media/{obj.thumbnail}')
        return None
