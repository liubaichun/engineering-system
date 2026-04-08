"""
任务流程模块数据模型

参考飞书项目节点流设计，支持：
1. 任务类型自建
2. 可视化流程配置
3. 节点灵活流转
4. 活动轨迹记录
"""

from django.db import models
from django.conf import settings


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
        verbose_name='允许的操作',
        help_text='["upload", "signoff", "approve", "comment"]'
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
        'Task',
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
