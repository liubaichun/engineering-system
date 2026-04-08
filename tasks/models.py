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
