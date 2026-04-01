from django.db import models
from django.conf import settings


class ApprovalFlow(models.Model):
    """
    审批流主表
    """
    FLOW_TYPE_CHOICES = [
        ('payment', '付款审批'),
        ('project', '立项审批'),
        ('change', '变更审批'),
    ]
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
    ]

    name = models.CharField('审批名称', max_length=255)
    flow_type = models.CharField('审批类型', max_length=20, choices=FLOW_TYPE_CHOICES)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_approvals',
        verbose_name='申请人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    # 关联记录（可为null，取决于审批类型）
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approvals',
        verbose_name='关联项目'
    )
    expense = models.ForeignKey(
        'finance.Expense',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approvals',
        verbose_name='关联支出'
    )
    amount = models.DecimalField(
        '付款金额',
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='直接存储的付款金额（可选，与expense金额可不同）'
    )
    description = models.TextField(
        '审批说明',
        blank=True,
        default='',
        help_text='审批原因或备注'
    )

    class Meta:
        db_table = 'approval_flows'
        ordering = ['-created_at']
        verbose_name = '审批流'
        verbose_name_plural = '审批流'

    def __str__(self):
        return f"{self.get_flow_type_display()} - {self.name}"


class ApprovalNode(models.Model):
    """
    审批节点表
    """
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
    ]

    flow = models.ForeignKey(
        ApprovalFlow,
        on_delete=models.CASCADE,
        related_name='nodes',
        verbose_name='所属审批流'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_tasks',
        verbose_name='审批人'
    )
    node_order = models.IntegerField('审批顺序', default=1)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    comment = models.TextField('审批意见', blank=True, default='')
    decided_at = models.DateTimeField('审批时间', null=True, blank=True)

    class Meta:
        db_table = 'approval_nodes'
        ordering = ['node_order']
        verbose_name = '审批节点'
        verbose_name_plural = '审批节点'

    def __str__(self):
        return f"{self.flow.name} - 节点{self.node_order} - {self.approver}"
