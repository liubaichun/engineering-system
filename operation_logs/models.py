from django.db import models
from django.conf import settings


class OperationLog(models.Model):
    ACTION_CHOICES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='操作用户'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='操作类型'
    )
    model_name = models.CharField(
        max_length=50,
        verbose_name='模型名称'
    )  # 如 'Project', 'Task', 'Expense'
    object_id = models.PositiveIntegerField(
        verbose_name='对象ID'
    )  # 被操作的对象ID
    description = models.TextField(
        verbose_name='操作描述'
    )  # 操作描述，如"创建了项目XXX"
    ip_address = models.GenericIPAddressField(
        null=True,
        verbose_name='IP地址'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    class Meta:
        db_table = 'operation_logs'
        ordering = ['-created_at']
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.model_name} #{self.object_id}"
