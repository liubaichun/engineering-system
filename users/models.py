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

    # 审批流程扩展字段
    is_approved = models.BooleanField(verbose_name='是否审批通过', default=False)
    approval_status = models.CharField(verbose_name='审批状态', max_length=20, default='pending')

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


class UsersPendingApproval(models.Model):
    """待审核用户申请表"""
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]

    username = models.CharField(verbose_name='用户名', max_length=150, unique=True)
    password = models.CharField(verbose_name='密码', max_length=255)
    email = models.EmailField(verbose_name='邮箱')
    role = models.CharField(verbose_name='申请角色', max_length=20, default='worker')
    phone = models.CharField(verbose_name='手机号', max_length=20, blank=True, default='')
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(verbose_name='拒绝原因', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='申请时间', auto_now_add=True)
    reviewed_at = models.DateTimeField(verbose_name='审核时间', blank=True, null=True)
    reviewed_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL,
        related_name='reviewed_users',
        blank=True, null=True, verbose_name='审核人'
    )

    class Meta:
        db_table = 'users_pending_approval'
        verbose_name = '待审核用户'
        verbose_name_plural = '待审核用户'

    def __str__(self):
        return f"{self.username} ({self.get_status_display()})"


class ApprovalFlow(models.Model):
    """审批流程主表"""
    FLOW_TYPE_CHOICES = [
        ('user_registration', '用户注册审批'),
        ('role_change', '角色变更审批'),
    ]
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    ]

    applicant = models.ForeignKey(
        'User', on_delete=models.CASCADE,
        related_name='approval_flows', verbose_name='申请人'
    )
    flow_type = models.CharField(verbose_name='流程类型', max_length=20, choices=FLOW_TYPE_CHOICES)
    target_object_type = models.CharField(verbose_name='目标对象类型', max_length=50, blank=True, default='')
    target_object_id = models.IntegerField(verbose_name='目标对象ID', blank=True, null=True)
    status = models.CharField(verbose_name='状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    current_node = models.IntegerField(verbose_name='当前节点', default=1)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    class Meta:
        db_table = 'approval_flow'
        verbose_name = '审批流程'
        verbose_name_plural = '审批流程'

    def __str__(self):
        return f"{self.get_flow_type_display()} - {self.applicant.username}"


class ApprovalRecord(models.Model):
    """审批记录明细表"""
    ACTION_CHOICES = [
        ('approve', '批准'),
        ('reject', '拒绝'),
        ('transfer', '转交'),
    ]

    flow = models.ForeignKey(
        'ApprovalFlow', on_delete=models.CASCADE,
        related_name='records', verbose_name='所属流程'
    )
    approver = models.ForeignKey(
        'User', on_delete=models.SET_NULL,
        related_name='approval_records',
        blank=True, null=True, verbose_name='审批人'
    )
    node = models.IntegerField(verbose_name='节点序号', default=1)
    action = models.CharField(verbose_name='操作', max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(verbose_name='审批意见', blank=True, default='')
    created_at = models.DateTimeField(verbose_name='操作时间', auto_now_add=True)

    class Meta:
        db_table = 'approval_record'
        verbose_name = '审批记录'
        verbose_name_plural = '审批记录'

    def __str__(self):
        return f"{self.flow.applicant.username} - {self.get_action_display()}"


class UserRoleAssignment(models.Model):
    """用户角色分配表"""
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE,
        related_name='role_assignments', verbose_name='用户'
    )
    role = models.CharField(verbose_name='角色', max_length=20)
    assigned_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL,
        related_name='role_assignments_given',
        blank=True, null=True, verbose_name='分配人'
    )
    assigned_at = models.DateTimeField(verbose_name='分配时间', auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name='过期时间', blank=True, null=True)

    class Meta:
        db_table = 'user_role_assignment'
        verbose_name = '用户角色分配'
        verbose_name_plural = '用户角色分配'

    def __str__(self):
        return f"{self.user.username} -> {self.role}"


class RolePermission(models.Model):
    """角色权限表"""
    PERMISSION_TYPE_CHOICES = [
        ('allow', '允许'),
        ('deny', '拒绝'),
    ]
    ACTION_CHOICES = [
        ('read', '读取'),
        ('write', '写入'),
        ('delete', '删除'),
        ('admin', '管理'),
    ]

    role = models.CharField(verbose_name='角色', max_length=20)
    resource = models.CharField(verbose_name='资源路径', max_length=100)
    action = models.CharField(verbose_name='操作类型', max_length=20, choices=ACTION_CHOICES)
    permission_type = models.CharField(verbose_name='权限类型', max_length=20, choices=PERMISSION_TYPE_CHOICES, default='allow')


