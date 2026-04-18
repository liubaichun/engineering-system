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

    EXPENSE_TYPE_CHOICES = [
        ('expense', '费用报销'),
        ('advance', '预付款'),
        ('deposit', '押金'),
    ]

    amount = models.DecimalField(verbose_name='金额', max_digits=14, decimal_places=2)
    expense_type = models.CharField(
        verbose_name='支出类型', max_length=20,
        choices=EXPENSE_TYPE_CHOICES, default='expense'
    )
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


class Company(models.Model):
    """公司模型 - GREEN版本"""
    name = models.CharField(verbose_name='公司名称', max_length=100)
    code = models.CharField(verbose_name='公司代码', max_length=20, unique=True)
    is_active = models.BooleanField(verbose_name='是否启用', default=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        db_table = 'finance_companies'
        verbose_name = '公司'
        verbose_name_plural = '公司管理'
        ordering = ['name']

    def __str__(self):
        return self.name


class Salary(models.Model):
    """工资单模型 - GREEN版本"""

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待审核'),
        ('approved', '已批准'),
        ('paid', '已发放'),
    ]

    company = models.ForeignKey(
        Company,
        verbose_name='公司',
        on_delete=models.CASCADE,
        related_name='salaries'
    )
    employee_id = models.CharField(verbose_name='员工ID', max_length=20)
    salary_month = models.CharField(verbose_name='月份', max_length=7, help_text='格式：YYYY-MM')
    department = models.CharField(verbose_name='部门', max_length=50, blank=True, default='')
    position = models.CharField(verbose_name='职位', max_length=50, blank=True, default='')
    base_salary = models.DecimalField(verbose_name='基本工资', max_digits=12, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(verbose_name='加班小时', max_digits=6, decimal_places=2, default=0)
    overtime_rate = models.DecimalField(verbose_name='加班费率', max_digits=4, decimal_places=2, default=1.5)
    overtime_pay = models.DecimalField(verbose_name='加班费', max_digits=12, decimal_places=2, default=0)
    attendance_days = models.DecimalField(verbose_name='出勤天数', max_digits=5, decimal_places=1, default=0)
    leave_days = models.DecimalField(verbose_name='请假天数', max_digits=5, decimal_places=1, default=0)
    bonus = models.DecimalField(verbose_name='奖金', max_digits=12, decimal_places=2, default=0)
    deduction_other = models.DecimalField(verbose_name='其他扣款', max_digits=12, decimal_places=2, default=0)
    social_security = models.DecimalField(verbose_name='社保', max_digits=12, decimal_places=2, default=0)
    housing_fund = models.DecimalField(verbose_name='公积金', max_digits=12, decimal_places=2, default=0)
    tax_before = models.DecimalField(verbose_name='税前工资', max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(verbose_name='个税', max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(verbose_name='实发工资', max_digits=12, decimal_places=2, default=0)
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='draft')
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='审批人',
        on_delete=models.SET_NULL,
        related_name='approved_salaries',
        blank=True,
        null=True
    )
    approved_at = models.DateTimeField(verbose_name='审批时间', blank=True, null=True)
    paid_at = models.DateTimeField(verbose_name='支付时间', blank=True, null=True)
    remarks = models.TextField(verbose_name='备注', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    class Meta:
        db_table = 'finance_salaries'
        verbose_name = '工资单'
        verbose_name_plural = '工资管理'
        ordering = ['-salary_month', 'company__name', 'employee_id']
        unique_together = ['employee_id', 'salary_month']

    def __str__(self):
        return "%s - %s" % (self.employee_name, self.month)

    def calculate_tax_and_net(self):
        """计算个税和实发工资"""
        # 应纳税所得额 = 基本工资 + 加班费 + 奖金 - 社保 - 公积金 - 5000
        gross = float(self.base_salary) + float(self.overtime_pay or 0) + float(self.bonus or 0)
        deductions = float(self.social_security or 0) + float(self.housing_fund or 0)
        taxable_income = gross - deductions - 5000

        if taxable_income <= 0:
            self.tax = 0
        else:
            # 中国7级超额累进税率表
            thresholds = [0, 3000, 12000, 25000, 35000, 55000, 80000]
            rates = [3, 10, 20, 25, 30, 35, 45]
            deductions_tbl = [0, 210, 1410, 2660, 4410, 7160, 15160]
            for i in range(len(thresholds) - 1, -1, -1):
                if taxable_income > thresholds[i]:
                    self.tax = round(taxable_income * rates[i] / 100 - deductions_tbl[i], 2)
                    break

        other_ded = float(self.deduction_other or 0)
        self.net_salary = round(
            gross - deductions - float(self.tax or 0) - other_ded, 2
        )
        self.tax_before = gross

    def save(self, *args, **kwargs):
        self.calculate_tax_and_net()
        super(Salary, self).save(*args, **kwargs)
