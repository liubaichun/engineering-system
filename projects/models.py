from django.db import models
from django.conf import settings


class Project(models.Model):
    """项目模型"""
    
    STATUS_CHOICES = [
        ('preparing', '准备中'),
        ('construction', '建设中'),
        ('completed', '已完成'),
        ('acceptance', '验收中'),
        ('finished', '已结束'),
        ('suspended', '已暂停'),
    ]
    
    name = models.CharField(verbose_name='项目名称', max_length=200)
    client = models.ForeignKey(
        'crm.Customer',
        verbose_name='客户',
        on_delete=models.PROTECT,
        related_name='projects',
        blank=True,
        null=True
    )
    supplier = models.ForeignKey(
        'crm.Supplier',
        verbose_name='供应商',
        on_delete=models.PROTECT,
        related_name='projects',
        blank=True,
        null=True
    )
    status = models.CharField(verbose_name='项目状态', max_length=20, choices=STATUS_CHOICES, default='preparing')
    budget = models.DecimalField(verbose_name='预算金额', max_digits=14, decimal_places=2, default=0)
    start_date = models.DateField(verbose_name='开始日期', blank=True, null=True)
    end_date = models.DateField(verbose_name='结束日期', blank=True, null=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='项目经理',
        on_delete=models.PROTECT,
        related_name='managed_projects',
        blank=True,
        null=True
    )
    description = models.TextField(verbose_name='项目描述', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'projects'
        verbose_name = '项目'
        verbose_name_plural = '项目管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class SignInRecord(models.Model):
    """现场签到记录"""
    
    TYPE_CHOICES = [
        ('checkin', '签到'),
        ('checkout', '签退'),
    ]
    
    project = models.ForeignKey(
        'Project',
        verbose_name='关联项目',
        on_delete=models.CASCADE,
        related_name='signin_records',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='签到人',
        on_delete=models.CASCADE,
        related_name='signin_records',
        null=True,
        blank=True
    )
    # 签到人信息（便于现场人员不登录系统也能签到）
    person_name = models.CharField(verbose_name='签到人姓名', max_length=100, blank=True, default='')
    person_phone = models.CharField(verbose_name='签到人电话', max_length=20, blank=True, default='')
    person_company = models.CharField(verbose_name='单位/公司', max_length=200, blank=True, default='')
    
    sign_type = models.CharField(verbose_name='签到类型', max_length=20, choices=TYPE_CHOICES, default='checkin')
    sign_time = models.DateTimeField(verbose_name='签到时间', auto_now_add=True)
    
    # 位置信息
    location = models.CharField(verbose_name='签到地点', max_length=500, blank=True, default='')
    latitude = models.CharField(verbose_name='纬度', max_length=50, blank=True, default='')
    longitude = models.CharField(verbose_name='经度', max_length=50, blank=True, default='')
    
    # 二维码ID（扫描二维码签到时使用）
    qrcode_id = models.CharField(verbose_name='二维码ID', max_length=100, blank=True, default='')
    
    # 备注
    remark = models.TextField(verbose_name='备注', blank=True, default='')
    
    # 创建时间
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'projects_signin_record'
        verbose_name = '签到记录'
        verbose_name_plural = '签到记录'
        ordering = ['-sign_time']
    
    def __str__(self):
        return f"{self.person_name or self.user}-{self.get_sign_type_display()}-{self.sign_time}"


class SignInQRCode(models.Model):
    """签到二维码"""
    
    project = models.ForeignKey(
        'Project',
        verbose_name='关联项目',
        on_delete=models.CASCADE,
        related_name='signin_qrcodes'
    )
    name = models.CharField(verbose_name='二维码名称', max_length=200)
    # 二维码唯一标识
    code = models.CharField(verbose_name='二维码Code', max_length=100, unique=True)
    # 有效时间
    valid_from = models.DateTimeField(verbose_name='生效时间')
    valid_until = models.DateTimeField(verbose_name='失效时间')
    # 位置信息
    location_name = models.CharField(verbose_name='签到地点名称', max_length=500, blank=True, default='')
    latitude = models.CharField(verbose_name='纬度', max_length=50, blank=True, default='')
    longitude = models.CharField(verbose_name='经度', max_length=50, blank=True, default='')
    # 是否启用
    is_active = models.BooleanField(verbose_name='是否启用', default=True)
    # 创建信息
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='创建人',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_signin_qrcodes'
    )
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'projects_signin_qrcode'
        verbose_name = '签到二维码'
        verbose_name_plural = '签到二维码'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name}-{self.project.name}"
