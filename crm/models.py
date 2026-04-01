from django.db import models


class Customer(models.Model):
    """客户模型"""
    
    STATUS_CHOICES = [
        ('potential', '潜在客户'),
        ('active', '活跃客户'),
        ('finished', '已结束'),
    ]
    
    name = models.CharField(verbose_name='客户名称', max_length=200)
    contact = models.CharField(verbose_name='联系人', max_length=100, blank=True, default='')
    phone = models.CharField(verbose_name='联系电话', max_length=20, blank=True, default='')
    email = models.EmailField(verbose_name='邮箱', blank=True, null=True)
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='potential')
    address = models.TextField(verbose_name='地址', blank=True, default='')
    remark = models.TextField(verbose_name='备注', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'crm_customers'
        verbose_name = '客户'
        verbose_name_plural = '客户管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Supplier(models.Model):
    """供应商模型"""
    
    name = models.CharField(verbose_name='供应商名称', max_length=200)
    contact = models.CharField(verbose_name='联系人', max_length=100, blank=True, default='')
    phone = models.CharField(verbose_name='联系电话', max_length=20, blank=True, default='')
    email = models.EmailField(verbose_name='邮箱', blank=True, null=True)
    category = models.CharField(verbose_name='供应品类', max_length=100, blank=True, default='')
    address = models.TextField(verbose_name='地址', blank=True, default='')
    remark = models.TextField(verbose_name='备注', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'crm_suppliers'
        verbose_name = '供应商'
        verbose_name_plural = '供应商管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


# Keep existing models for backward compatibility with other parts of the system
class Client(models.Model):
    """客户模型（兼容）"""
    
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '不活跃'),
        ('blacklisted', '已拉黑'),
    ]
    
    name = models.CharField(verbose_name='客户名称', max_length=200)
    code = models.CharField(verbose_name='客户编码', max_length=50, unique=True)
    contact_person = models.CharField(verbose_name='联系人', max_length=100, blank=True, default='')
    contact_phone = models.CharField(verbose_name='联系电话', max_length=20, blank=True, default='')
    contact_email = models.EmailField(verbose_name='联系邮箱', blank=True, null=True)
    address = models.TextField(verbose_name='地址', blank=True, default='')
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'clients'
        verbose_name = '客户（兼容）'
        verbose_name_plural = '客户管理（兼容）'
    
    def __str__(self):
        return self.name


class Contract(models.Model):
    """合同模型"""
    
    TYPE_CHOICES = [
        ('sale', '销售合同'),
        ('purchase', '采购合同'),
        ('service', '服务合同'),
    ]
    
    client = models.ForeignKey(
        Client,
        verbose_name='关联客户',
        on_delete=models.CASCADE,
        related_name='contracts'
    )
    name = models.CharField(verbose_name='合同名称', max_length=300)
    code = models.CharField(verbose_name='合同编号', max_length=50, unique=True)
    type = models.CharField(verbose_name='合同类型', max_length=20, choices=TYPE_CHOICES, default='sale')
    amount = models.DecimalField(verbose_name='合同金额', max_digits=14, decimal_places=2, default=0)
    signed_date = models.DateField(verbose_name='签订日期', blank=True, null=True)
    start_date = models.DateField(verbose_name='开始日期', blank=True, null=True)
    end_date = models.DateField(verbose_name='结束日期', blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'contracts'
        verbose_name = '合同'
        verbose_name_plural = '合同管理'
    
    def __str__(self):
        return f"{self.name} ({self.code})"
