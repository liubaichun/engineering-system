from django.db import models
from django.conf import settings


class TaskFlowInstance(models.Model):
    """流程实例 - 统一管理任务流程"""
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
