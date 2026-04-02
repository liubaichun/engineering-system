from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import timedelta
from django.utils import timezone


class User(AbstractUser):
    """扩展用户模型"""
    
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('pm', '项目经理'),
        ('dev', '开发人员'),
        ('business', '商务人员'),
        ('finance', '财务人员'),
    ]
    
    email = models.EmailField(verbose_name='邮箱', blank=True, null=True, unique=True)
    phone = models.CharField(verbose_name='联系电话', max_length=20, blank=True, default='')
    role = models.CharField(verbose_name='角色', max_length=20, choices=ROLE_CHOICES, default='dev')
    is_active = models.BooleanField(verbose_name='是否启用', default=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    # 登录失败锁定相关字段
    failed_login_attempts = models.IntegerField(verbose_name='连续登录失败次数', default=0)
    lock_until = models.DateTimeField(verbose_name='锁定截止时间', blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_locked(self):
        """检查用户是否被锁定"""
        if self.lock_until and self.lock_until > timezone.now():
            return True
        return False
    
    def increment_failed_login(self):
        """增加登录失败计数"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 3:
            self.lock_until = timezone.now() + timedelta(minutes=15)
        self.save()
    
    def reset_failed_login(self):
        """重置登录失败计数"""
        self.failed_login_attempts = 0
        self.lock_until = None
        self.save()
