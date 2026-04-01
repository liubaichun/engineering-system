from django.db import models
from django.conf import settings


class Notification(models.Model):
    """系统通知模型"""
    TYPE_CHOICES = [
        ('info', '通知'),
        ('warning', '警告'),
        ('success', '成功'),
        ('danger', '危险'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='用户'
    )
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容', blank=True, default='')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info', verbose_name='类型')
    is_read = models.BooleanField(default=False, verbose_name='已读')
    link = models.CharField(max_length=500, blank=True, default='', verbose_name='跳转链接')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = '通知'
        verbose_name_plural = '通知管理'

    def __str__(self):
        return f'{self.user.username} - {self.title}'
