from django.db import models
from django.conf import settings


class Task(models.Model):
    """任务模型"""
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('blocked', '已阻塞'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    name = models.CharField(verbose_name='任务名称', max_length=300)
    project = models.ForeignKey(
        'projects.Project',
        verbose_name='所属项目',
        on_delete=models.CASCADE,
        related_name='tasks',
        blank=True,
        null=True
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='负责人',
        on_delete=models.PROTECT,
        related_name='managed_tasks',
        blank=True,
        null=True
    )
    manager_display = models.CharField(
        verbose_name='负责人显示名',
        max_length=100,
        blank=True,
        default='',
        help_text='负责人显示名（自由文本，不关联用户表）'
    )
    task_type = models.ForeignKey(
        'TaskType',
        verbose_name='任务类型',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tasks'
    )
    flow_template = models.ForeignKey(
        'FlowTemplate',
        verbose_name='流程模板',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tasks'
    )
    current_stage = models.ForeignKey(
        'FlowNodeTemplate',
        verbose_name='当前阶段',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='current_tasks'
    )
    status = models.CharField(verbose_name='任务状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(verbose_name='优先级', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    progress = models.IntegerField(verbose_name='进度', default=0)
    start_date = models.DateField(verbose_name='开始日期', blank=True, null=True)
    end_date = models.DateField(verbose_name='结束日期', blank=True, null=True)
    description = models.TextField(verbose_name='任务描述', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        verbose_name = '任务'
        verbose_name_plural = '任务管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 确保进度在0-100之间
        if self.progress < 0:
            self.progress = 0
        elif self.progress > 100:
            self.progress = 100
        super().save(*args, **kwargs)


# ============== 任务流程模型 ==============

class TaskType(models.Model):
    """任务类型"""
    name = models.CharField(max_length=100, verbose_name='类型名称')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_task_types'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks_tasktype'
        verbose_name = '任务类型'
        verbose_name_plural = '任务类型'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class FlowTemplate(models.Model):
    """流程模板"""
    name = models.CharField(max_length=200, verbose_name='模板名称')
    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.CASCADE,
        related_name='flow_templates',
        verbose_name='任务类型'
    )
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_flow_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks_flowtemplate'
        verbose_name = '流程模板'
        verbose_name_plural = '流程模板'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task_type.name} - {self.name}"


class FlowNodeTemplate(models.Model):
    """流程节点模板"""
    ACTION_CHOICES = [
        ('upload', '文件上传'),
        ('signoff', '签收确认'),
        ('approve', '审批通过'),
        ('reject', '驳回'),
        ('comment', '评论'),
        ('transfer', '转交'),
    ]
    
    template = models.ForeignKey(
        FlowTemplate,
        on_delete=models.CASCADE,
        related_name='nodes',
        verbose_name='所属模板'
    )
    name = models.CharField(max_length=100, verbose_name='节点名称')
    order = models.IntegerField(default=0, verbose_name='顺序')
    duration_hours = models.IntegerField(default=24, verbose_name='规定处理时长(小时)')
    
    responsible_type = models.CharField(
        max_length=20,
        choices=[
            ('any', '任意人员'),
            ('user', '指定人员'),
            ('role', '角色关联'),
        ],
        default='any',
        verbose_name='负责人类型'
    )
    responsible_users = models.JSONField(default=list, blank=True, verbose_name='指定人员列表')
    responsible_roles = models.JSONField(default=list, blank=True, verbose_name='指定角色列表')
    
    allowed_actions = models.JSONField(
        default=list,
        verbose_name='允许的操作'
    )
    
    notify_on_assign = models.BooleanField(default=True, verbose_name='分配时通知')
    notify_on_overdue = models.BooleanField(default=True, verbose_name='超时提醒')
    
    is_start = models.BooleanField(default=False, verbose_name='是否为起点')
    is_end = models.BooleanField(default=False, verbose_name='是否为终点')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks_flownodetemplate'
        verbose_name = '流程节点模板'
        verbose_name_plural = '流程节点模板'
        ordering = ['template', 'order']

    def __str__(self):
        return f"{self.template.name} - {self.name}"


class FlowTransition(models.Model):
    """流程连线"""
    template = models.ForeignKey(
        FlowTemplate,
        on_delete=models.CASCADE,
        related_name='transitions'
    )
    from_node = models.ForeignKey(
        FlowNodeTemplate,
        on_delete=models.CASCADE,
        related_name='outgoing_transitions',
        verbose_name='起始节点'
    )
    to_node = models.ForeignKey(
        FlowNodeTemplate,
        on_delete=models.CASCADE,
        related_name='incoming_transitions',
        verbose_name='目标节点'
    )
    condition = models.JSONField(default=dict, blank=True, verbose_name='流转条件')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tasks_flowtransition'
        verbose_name = '流程连线'
        verbose_name_plural = '流程连线'
        unique_together = ['template', 'from_node', 'to_node']

    def __str__(self):
        return f"{self.from_node.name} → {self.to_node.name}"


class TaskStageInstance(models.Model):
    """任务阶段实例"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '处理中'),
        ('completed', '已完成'),
        ('skipped', '已跳过'),
        ('rejected', '已驳回'),
    ]
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='stage_instances'
    )
    template_node = models.ForeignKey(
        FlowNodeTemplate,
        on_delete=models.CASCADE,
        verbose_name='关联节点模板'
    )
    order = models.IntegerField(default=0, verbose_name='顺序')
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_stages'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    
    is_overdue = models.BooleanField(default=False, verbose_name='是否超时')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks_taskstageinstance'
        verbose_name = '任务阶段实例'
        verbose_name_plural = '任务阶段实例'
        ordering = ['task', 'order']

    def __str__(self):
        return f"{self.task.name} - {self.template_node.name}"


class StageActivity(models.Model):
    """节点活动记录"""
    ACTION_CHOICES = [
        ('create', '创建'),
        ('start', '开始处理'),
        ('complete', '完成'),
        ('upload', '上传文件'),
        ('signoff', '签收'),
        ('approve', '审批通过'),
        ('reject', '驳回'),
        ('comment', '评论'),
        ('transfer', '转交'),
        ('system', '系统操作'),
    ]
    
    stage_instance = models.ForeignKey(
        TaskStageInstance,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stage_activities'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    content = models.TextField(blank=True, verbose_name='活动内容')
    attachments = models.JSONField(default=list, blank=True, verbose_name='附件')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tasks_stageactivity'
        verbose_name = '节点活动记录'
        verbose_name_plural = '节点活动记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.stage_instance} - {self.action_type}"
