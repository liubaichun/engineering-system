from django.db import models
from django.conf import settings


class MaterialNew(models.Model):
    """物料模型（新）"""
    
    UNIT_CHOICES = [
        ('pcs', '个'),
        ('kg', '千克'),
        ('m', '米'),
        ('set', '套'),
    ]
    
    name = models.CharField(verbose_name='物料名称', max_length=200)
    specification = models.CharField(verbose_name='规格型号', max_length=500, blank=True, default='')
    unit = models.CharField(verbose_name='单位', max_length=10, choices=UNIT_CHOICES, default='pcs')
    stock = models.DecimalField(verbose_name='当前库存', max_digits=12, decimal_places=2, default=0)
    alert_threshold = models.DecimalField(verbose_name='预警阈值', max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(verbose_name='单价（元）', max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(
        'crm.Supplier',
        verbose_name='供应商',
        on_delete=models.PROTECT,
        related_name='material_new_records',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'inventory_material_new'
        verbose_name = '物料（新）'
        verbose_name_plural = '物料管理（新）'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class MaterialIO(models.Model):
    """物料出入库模型"""
    
    TYPE_CHOICES = [
        ('in', '入库'),
        ('out', '出库'),
    ]
    
    material = models.ForeignKey(
        MaterialNew,
        verbose_name='物料',
        on_delete=models.CASCADE,
        related_name='io_records'
    )
    type = models.CharField(verbose_name='类型', max_length=10, choices=TYPE_CHOICES)
    quantity = models.DecimalField(verbose_name='数量', max_digits=12, decimal_places=2)
    project = models.ForeignKey(
        'projects.Project',
        verbose_name='关联项目',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='操作人',
        on_delete=models.PROTECT,
        related_name='material_io_records'
    )
    remark = models.TextField(verbose_name='备注', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_material_io'
        verbose_name = '物料出入库'
        verbose_name_plural = '物料出入库管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.material.name} - {self.get_type_display()} {self.quantity}"


class EquipmentNew(models.Model):
    """设备模型（新）"""
    
    STATUS_CHOICES = [
        ('idle', '闲置'),
        ('in_use', '使用中'),
        ('maintenance', '维修中'),
    ]
    
    name = models.CharField(verbose_name='设备名称', max_length=200)
    specification = models.CharField(verbose_name='规格型号', max_length=500, blank=True, default='')
    model = models.CharField(verbose_name='设备型号', max_length=200, blank=True, default='')
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='idle')
    location = models.CharField(verbose_name='存放地点', max_length=200, blank=True, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'inventory_equipment_new'
        verbose_name = '设备（新）'
        verbose_name_plural = '设备管理（新）'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class EquipmentIO(models.Model):
    """设备出入库模型"""
    
    TYPE_CHOICES = [
        ('borrow', '领用'),
        ('return', '归还'),
    ]
    
    equipment = models.ForeignKey(
        EquipmentNew,
        verbose_name='设备',
        on_delete=models.CASCADE,
        related_name='io_records'
    )
    type = models.CharField(verbose_name='类型', max_length=10, choices=TYPE_CHOICES)
    quantity = models.IntegerField(verbose_name='数量', default=1)
    project = models.ForeignKey(
        'projects.Project',
        verbose_name='关联项目',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='操作人',
        on_delete=models.PROTECT,
        related_name='equipment_io_records'
    )
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_equipment_io'
        verbose_name = '设备出入库'
        verbose_name_plural = '设备出入库管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.equipment.name} - {self.get_type_display()}"


# Keep existing models for backward compatibility
class MaterialCategory(models.Model):
    """物料分类模型"""
    
    name = models.CharField(verbose_name='分类名称', max_length=100)
    parent = models.ForeignKey(
        'self',
        verbose_name='父分类',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children'
    )
    description = models.TextField(verbose_name='描述', blank=True, default='')
    
    class Meta:
        db_table = 'material_categories'
        verbose_name = '物料分类（兼容）'
        verbose_name_plural = '物料分类管理（兼容）'
    
    def __str__(self):
        return self.name


class Material(models.Model):
    """物料模型（兼容）"""
    
    UNIT_CHOICES = [
        ('pcs', '个'),
        ('kg', '千克'),
        ('m', '米'),
        ('set', '套'),
    ]
    
    name = models.CharField(verbose_name='物料名称', max_length=200)
    code = models.CharField(verbose_name='物料编码', max_length=50, unique=True)
    category = models.ForeignKey(
        MaterialCategory,
        verbose_name='分类',
        on_delete=models.PROTECT,
        related_name='materials'
    )
    unit = models.CharField(verbose_name='单位', max_length=10, choices=UNIT_CHOICES, default='pcs')
    specification = models.CharField(verbose_name='规格型号', max_length=500, blank=True, default='')
    stock_quantity = models.DecimalField(verbose_name='当前库存', max_digits=12, decimal_places=2, default=0)
    min_stock = models.DecimalField(verbose_name='最低库存预警值', max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(verbose_name='单价', max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'materials'
        verbose_name = '物料（兼容）'
        verbose_name_plural = '物料管理（兼容）'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class MaterialStock(models.Model):
    """库存流水模型（兼容）"""
    
    TYPE_CHOICES = [
        ('in', '入库'),
        ('out', '出库'),
    ]
    
    material = models.ForeignKey(
        Material,
        verbose_name='物料',
        on_delete=models.CASCADE,
        related_name='stock_logs'
    )
    type = models.CharField(verbose_name='类型', max_length=10, choices=TYPE_CHOICES)
    quantity = models.DecimalField(verbose_name='数量', max_digits=12, decimal_places=2)
    project = models.ForeignKey(
        'projects.Project',
        verbose_name='关联项目',
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='操作人',
        on_delete=models.PROTECT,
        related_name='stock_operations'
    )
    remark = models.TextField(verbose_name='备注', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='操作时间', auto_now_add=True)
    
    class Meta:
        db_table = 'material_stocks'
        verbose_name = '库存流水（兼容）'
        verbose_name_plural = '库存流水管理（兼容）'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.material.name} - {self.get_type_display()} {self.quantity}"


class Equipment(models.Model):
    """设备模型（兼容）"""
    
    STATUS_CHOICES = [
        ('available', '可用'),
        ('in_use', '使用中'),
        ('maintenance', '维修中'),
        ('scrapped', '已报废'),
    ]
    
    name = models.CharField(verbose_name='设备名称', max_length=200)
    code = models.CharField(verbose_name='设备编码', max_length=50, unique=True)
    specification = models.CharField(verbose_name='规格型号', max_length=500, blank=True, default='')
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='available')
    purchase_date = models.DateField(verbose_name='采购日期', blank=True, null=True)
    purchase_price = models.DecimalField(verbose_name='采购价格', max_digits=10, decimal_places=2, default=0)
    current_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='当前使用人',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='assigned_equipment'
    )
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'equipment'
        verbose_name = '设备（兼容）'
        verbose_name_plural = '设备管理（兼容）'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class EquipmentLog(models.Model):
    """设备使用记录模型（兼容）"""
    
    ACTION_CHOICES = [
        ('assign', '领用'),
        ('return', '归还'),
        ('maintenance', '维修'),
    ]
    
    equipment = models.ForeignKey(
        Equipment,
        verbose_name='设备',
        on_delete=models.CASCADE,
        related_name='logs'
    )
    action = models.CharField(verbose_name='操作类型', max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='操作人',
        on_delete=models.PROTECT,
        related_name='equipment_logs'
    )
    remark = models.TextField(verbose_name='备注', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='操作时间', auto_now_add=True)
    
    class Meta:
        db_table = 'equipment_logs'
        verbose_name = '设备使用记录（兼容）'
        verbose_name_plural = '设备使用记录管理（兼容）'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.equipment.name} - {self.get_action_display()}"
