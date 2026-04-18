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


# =============================================================================
# 文件管理模块扩展 - GREEN版本
# =============================================================================

class FileCategory(models.Model):
    """文件分类 - GREEN版本
    
    支持的文件分类：
    - company_system: 公司制度
    - company_qualification: 公司资质
    - company_contract: 公司合同
    - project_photo: 项目照片
    - invoice: 发票
    - other: 其他
    """
    
    CATEGORY_CHOICES = [
        ('company_system', '公司制度'),
        ('company_qualification', '公司资质'),
        ('company_contract', '公司合同'),
        ('project_photo', '项目照片'),
        ('invoice', '发票'),
        ('other', '其他'),
    ]
    
    name = models.CharField(verbose_name='分类名称', max_length=100)
    code = models.CharField(
        verbose_name='分类代码', 
        max_length=50, 
        unique=True,
        choices=CATEGORY_CHOICES
    )
    description = models.TextField(verbose_name='分类描述', blank=True, default='')
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name='父分类'
    )
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(verbose_name='是否启用', default=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'file_categories'
        verbose_name = '文件分类'
        verbose_name_plural = '文件分类管理'
        ordering = ['order', 'code']
    
    def __str__(self):
        return self.name
    
    def get_display_name(self):
        """获取分类的中文显示名称"""
        for code, name in self.CATEGORY_CHOICES:
            if code == self.code:
                return name
        return self.name


class CompanyFile(models.Model):
    """公司文件关联模型 - GREEN版本
    
    用于管理公司层面的文件，支持：
    - 按公司分类文件
    - 文件元数据：谁上传、什么时候上传
    - 关联文件分类
    """
    
    company = models.ForeignKey(
        'finance.Company',
        verbose_name='所属公司',
        on_delete=models.CASCADE,
        related_name='company_files',
        null=True,
        blank=True,
        help_text='所属公司，为空则表示系统级文件'
    )
    attachment = models.ForeignKey(
        Attachment,
        verbose_name='附件',
        on_delete=models.CASCADE,
        related_name='company_files'
    )
    category = models.ForeignKey(
        FileCategory,
        verbose_name='文件分类',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='company_files'
    )
    title = models.CharField(verbose_name='文件标题', max_length=300, blank=True, default='')
    description = models.TextField(verbose_name='文件描述', blank=True, default='')
    
    # 上传信息
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='上传人',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_company_files'
    )
    uploaded_at = models.DateTimeField(verbose_name='上传时间', auto_now_add=True)
    
    # 权限控制
    is_public = models.BooleanField(
        verbose_name='是否公开', 
        default=False,
        help_text='公开文件所有成员可见，否则仅限有权限成员'
    )
    is_active = models.BooleanField(verbose_name='是否启用', default=True)
    
    # 有效期
    valid_from = models.DateTimeField(verbose_name='生效时间', null=True, blank=True)
    valid_until = models.DateTimeField(verbose_name='失效时间', null=True, blank=True)
    
    # 审核状态
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已审核'),
        ('rejected', '已拒绝'),
    ]
    status = models.CharField(
        verbose_name='审核状态', 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='approved'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='审核人',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_company_files'
    )
    reviewed_at = models.DateTimeField(verbose_name='审核时间', null=True, blank=True)
    
    # 标签
    tags = models.CharField(
        verbose_name='标签', 
        max_length=500, 
        blank=True, 
        default='',
        help_text='多个标签用逗号分隔'
    )
    
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'company_files'
        verbose_name = '公司文件'
        verbose_name_plural = '公司文件管理'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['company', 'category']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['-uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.title or self.attachment.name} ({self.category})"
    
    def save(self, *args, **kwargs):
        # 如果标题为空，使用附件名称
        if not self.title:
            self.title = self.attachment.name
        super().save(*args, **kwargs)


class CompanyFileAccessLog(models.Model):
    """公司文件访问日志"""
    
    ACTION_CHOICES = [
        ('view', '查看'),
        ('download', '下载'),
        ('share', '分享'),
        ('delete', '删除'),
    ]
    
    company_file = models.ForeignKey(
        CompanyFile,
        verbose_name='公司文件',
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='操作用户',
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(
        verbose_name='操作类型',
        max_length=20,
        choices=ACTION_CHOICES,
        default='view'
    )
    ip_address = models.GenericIPAddressField(null=True, verbose_name='IP地址')
    user_agent = models.CharField(max_length=500, blank=True, verbose_name='User-Agent')
    accessed_at = models.DateTimeField(verbose_name='访问时间', auto_now_add=True)
    
    class Meta:
        db_table = 'company_file_access_logs'
        verbose_name = '文件访问日志'
        verbose_name_plural = '文件访问日志'
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"{self.company_file} - {self.action} by {self.user}"
