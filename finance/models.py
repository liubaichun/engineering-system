from django.db import models
from django.conf import settings


class Income(models.Model):
    """收入模型"""
    
    amount = models.DecimalField(verbose_name='金额', max_digits=14, decimal_places=2)
    date = models.DateField(verbose_name='日期')
    project = models.ForeignKey(
        'projects.Project',
        verbose_name='关联项目',
        on_delete=models.PROTECT,
        related_name='incomes',
        blank=True,
        null=True
    )
    customer = models.ForeignKey(
        'crm.Customer',
        verbose_name='客户',
        on_delete=models.PROTECT,
        related_name='incomes',
        blank=True,
        null=True
    )
    description = models.TextField(verbose_name='描述', blank=True, default='')
    attachment = models.CharField(verbose_name='附件', max_length=500, blank=True, default='')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='录入人',
        on_delete=models.PROTECT,
        related_name='income_records',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'finance_incomes'
        verbose_name = '收入'
        verbose_name_plural = '收入管理'
        ordering = ['-date']
    
    def __str__(self):
        return f"收入 {self.amount} - {self.date}"


class Expense(models.Model):
    """支出模型"""
    
    amount = models.DecimalField(verbose_name='金额', max_digits=14, decimal_places=2)
    date = models.DateField(verbose_name='日期')
    project = models.ForeignKey(
        'projects.Project',
        verbose_name='关联项目',
        on_delete=models.PROTECT,
        related_name='expenses',
        blank=True,
        null=True
    )
    supplier = models.ForeignKey(
        'crm.Supplier',
        verbose_name='供应商',
        on_delete=models.PROTECT,
        related_name='expenses',
        blank=True,
        null=True
    )
    description = models.TextField(verbose_name='描述', blank=True, default='')
    attachment = models.CharField(verbose_name='附件', max_length=500, blank=True, default='')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='录入人',
        on_delete=models.PROTECT,
        related_name='expense_records',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'finance_expenses'
        verbose_name = '支出'
        verbose_name_plural = '支出管理'
        ordering = ['-date']
    
    def __str__(self):
        return f"支出 {self.amount} - {self.date}"


class InvoiceNew(models.Model):
    """发票模型（新）"""
    
    TYPE_CHOICES = [
        ('income', '收入发票'),
        ('expense', '支出发票'),
    ]
    
    STATUS_CHOICES = [
        ('issued', '已开票'),
        ('paid', '已支付'),
        ('cancelled', '已作废'),
    ]
    
    invoice_no = models.CharField(verbose_name='发票号', max_length=50, unique=True)
    type = models.CharField(verbose_name='类型', max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(verbose_name='金额', max_digits=14, decimal_places=2)
    project = models.ForeignKey(
        'projects.Project',
        verbose_name='关联项目',
        on_delete=models.CASCADE,
        related_name='invoices_new',
        blank=True,
        null=True
    )
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='issued')
    issue_date = models.DateField(verbose_name='开票日期', blank=True, null=True)
    due_date = models.DateField(verbose_name='到期日期', blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'finance_invoices_new'
        verbose_name = '发票（新）'
        verbose_name_plural = '发票管理（新）'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.invoice_no


# Keep existing models for backward compatibility
class FinancialRecord(models.Model):
    """财务记录模型（兼容）"""
    
    TYPE_CHOICES = [
        ('income', '收入'),
        ('expense', '支出'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('reconciled', '已对账'),
        ('cancelled', '已取消'),
    ]
    
    project = models.ForeignKey(
        'projects.Project',
        verbose_name='关联项目',
        on_delete=models.PROTECT,
        related_name='financial_records',
        blank=True,
        null=True
    )
    type = models.CharField(verbose_name='类型', max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(verbose_name='金额', max_digits=14, decimal_places=2, default=0)
    category = models.CharField(verbose_name='收支分类', max_length=100, blank=True, default='')
    description = models.TextField(verbose_name='描述', blank=True, default='')
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    is_locked = models.BooleanField(verbose_name='是否锁定', default=False)
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='录入人',
        on_delete=models.PROTECT,
        related_name='financial_records'
    )
    record_date = models.DateField(verbose_name='发生日期')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'financial_records'
        verbose_name = '财务记录（兼容）'
        verbose_name_plural = '财务管理（兼容）'
        ordering = ['-record_date']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.amount}"


class Invoice(models.Model):
    """发票模型（兼容）"""
    
    STATUS_CHOICES = [
        ('pending', '待开票'),
        ('issued', '已开票'),
        ('verified', '已核销'),
        ('void', '已作废'),
    ]
    
    record = models.OneToOneField(
        FinancialRecord,
        verbose_name='收支记录',
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    invoice_number = models.CharField(verbose_name='发票号', max_length=50, unique=True)
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    invoice_date = models.DateField(verbose_name='开票日期', blank=True, null=True)
    amount = models.DecimalField(verbose_name='发票金额', max_digits=14, decimal_places=2, default=0)
    verified_at = models.DateTimeField(verbose_name='核销时间', blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        verbose_name = '发票（兼容）'
        verbose_name_plural = '发票管理（兼容）'
    
    def __str__(self):
        return self.invoice_number
