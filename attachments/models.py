from django.db import models
from django.conf import settings


class AttachmentCategory(models.Model):
    """文档分类"""
    name = models.CharField(max_length=100, verbose_name='分类名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='分类代码')
    project_type = models.CharField(max_length=50, blank=True, verbose_name='适用项目类型')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '文档分类'
        verbose_name_plural = '文档分类'
        ordering = ['order']

    def __str__(self):
        return self.name


class Attachment(models.Model):
    """统一附件模型"""

    FILE_TYPE_CHOICES = [
        ('image', '图片'),
        ('video', '视频'),
        ('document', '文档'),
        ('other', '其他'),
    ]

    name = models.CharField(verbose_name='文件名', max_length=300)
    file = models.FileField(verbose_name='文件', upload_to='attachments/%Y/%m/')
    file_type = models.CharField(verbose_name='文件类型', max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    file_size = models.BigIntegerField(verbose_name='文件大小（字节）', default=0)
    md5 = models.CharField(verbose_name='MD5', max_length=32, blank=True, default='')
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='上传人',
        on_delete=models.PROTECT,
        related_name='uploaded_attachments'
    )
    created_at = models.DateTimeField(verbose_name='上传时间', auto_now_add=True)
    # 文档分类
    category = models.ForeignKey(
        AttachmentCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='文档分类'
    )
    sub_category = models.CharField(max_length=50, blank=True, verbose_name='子分类')
    thumbnail = models.ImageField(
        upload_to='attachments/thumbnails/',
        null=True, blank=True, verbose_name='缩略图'
    )

    class Meta:
        db_table = 'attachments'
        verbose_name = '附件'
        verbose_name_plural = '附件管理'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ProjectAttachment(models.Model):
    """项目附件中间表"""
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    attachment = models.ForeignKey(
        Attachment,
        on_delete=models.CASCADE,
        related_name='project_attachments'
    )

    class Meta:
        db_table = 'project_attachments'
        verbose_name = '项目附件'
        verbose_name_plural = '项目附件'


class TaskAttachment(models.Model):
    """任务附件中间表"""
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    attachment = models.ForeignKey(
        Attachment,
        on_delete=models.CASCADE,
        related_name='task_attachments'
    )

    class Meta:
        db_table = 'task_attachments'
        verbose_name = '任务附件'
        verbose_name_plural = '任务附件'


class ProjectFileFolder(models.Model):
    """项目文件目录结构（树形）"""
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='file_folders')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    name = models.CharField(max_length=200, verbose_name='文件夹名称')
    category = models.ForeignKey(AttachmentCategory, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='关联分类')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_folders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '项目文件夹'
        verbose_name_plural = '项目文件夹'
        ordering = ['name']


class AttachmentVersion(models.Model):
    """附件版本"""
    attachment = models.ForeignKey(
        'Attachment',
        related_name='versions',
        on_delete=models.CASCADE
    )
    version = models.IntegerField(verbose_name='版本号')
    file = models.FileField(upload_to='attachments/versions/%Y/%m/', verbose_name='文件')
    file_size = models.BigIntegerField(verbose_name='文件大小', default=0)
    checksum = models.CharField(max_length=64, blank=True, verbose_name='MD5')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='上传人')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    change_log = models.CharField(max_length=500, blank=True, verbose_name='变更说明')

    class Meta:
        verbose_name = '附件版本'
        verbose_name_plural = '附件版本'
        unique_together = ['attachment', 'version']
        ordering = ['-version']

    def __str__(self):
        return f"{self.attachment.name} v{self.version}"


class AttachmentDownloadLog(models.Model):
    """附件下载日志"""
    attachment = models.ForeignKey(
        'Attachment',
        related_name='download_logs',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='操作用户')
    downloaded_at = models.DateTimeField(auto_now_add=True, verbose_name='下载时间')
    ip_address = models.GenericIPAddressField(null=True, verbose_name='IP地址')
    user_agent = models.CharField(max_length=500, blank=True, verbose_name='User-Agent')
    action = models.CharField(max_length=20, default='download', verbose_name='操作类型')

    class Meta:
        verbose_name = '下载日志'
        verbose_name_plural = '下载日志'
        ordering = ['-downloaded_at']

    def __str__(self):
        return f"{self.attachment.name} - {self.action} by {self.user}"
