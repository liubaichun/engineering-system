from django.db import models
from django.conf import settings


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
        'TaskStageInstance',
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
        db_table = 'flow_engine_stageactivity'
        verbose_name = '节点活动记录'
        verbose_name_plural = '节点活动记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.stage_instance} - {self.action_type}"


class TaskFlowInstance(models.Model):
    """流程实例"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('suspended', '已暂停'),
    ]
    
    task = models.OneToOneField(
        'tasks.Task',
        on_delete=models.CASCADE,
        related_name='flow_instance'
    )
    template = models.ForeignKey(
        'tasks.FlowTemplate',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='instances'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='initiated_flows'
    )
    
    current_node = models.ForeignKey(
        'tasks.FlowNodeTemplate',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='current_instances'
    )
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    
    is_overdue = models.BooleanField(default=False, verbose_name='是否超时')
    overdue_notified = models.BooleanField(default=False, verbose_name='超时通知已发送')
    
    context_data = models.JSONField(default=dict, blank=True, verbose_name='流程上下文数据')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'flow_engine_taskflowinstance'
        verbose_name = '流程实例'
        verbose_name_plural = '流程实例'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task.name} - {self.status}"
