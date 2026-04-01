from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class Project(models.Model):
    """项目表（支撑班组关联）"""
    name = models.CharField("项目名称", max_length=200)
    code = models.CharField("项目编号", max_length=50, unique=True)
    address = models.CharField("项目地址", max_length=300, blank=True)
    start_date = models.DateField("开工日期", null=True, blank=True)
    end_date = models.DateField("竣工日期", null=True, blank=True)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=[
            ("planning", "筹备中"),
            ("ongoing", "进行中"),
            ("suspended", "已停工"),
            ("completed", "已竣工"),
        ],
        default="planning",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "worker_projects"
        verbose_name = "项目"
        verbose_name_plural = "项目列表"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class WorkerGroup(models.Model):
    """班组表"""
    name = models.CharField("班组名称", max_length=100)
    leader = models.ForeignKey(
        "Worker",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_groups",
        verbose_name="班组长",
    )
    phone = models.CharField(
        "联系电话",
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(regex=r"^1[3-9]\d{9}$", message="手机号格式不正确")
        ],
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
        verbose_name="当前项目",
    )
    remark = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "worker_groups"
        verbose_name = "班组"
        verbose_name_plural = "班组列表"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def worker_count(self):
        """自动计算班组人数（关联的Worker记录数）"""
        return self.workers.filter(status="active").count()

    def clean(self):
        if self.leader and self.leader.group != self:
            if self.leader.group and self.leader.group != self:
                raise ValidationError({"leader": "班组长必须属于本班组"})


class Worker(models.Model):
    """施工人员档案"""

    WORK_TYPE_CHOICES = [
        ("rebar",      "钢筋工"),
        ("carpenter",  "木工"),
        ("concrete",   "混凝土工"),
        ("plumber",    "水电工"),
        ("painter",    "油漆工"),
        ("scaffolder", "架子工"),
        ("laborer",    "杂工"),
    ]

    SKILL_LEVEL_CHOICES = [
        ("junior",    "初级"),
        ("intermediate", "中级"),
        ("senior",    "高级"),
        ("master",    "技师"),
    ]

    STATUS_CHOICES = [
        ("active",   "在职"),
        ("inactive", "离职"),
        ("paused",   "暂停"),
    ]

    name = models.CharField("姓名", max_length=50)
    id_card = models.CharField(
        "身份证号",
        max_length=18,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\d{17}[\dXx]$",
                message="身份证号格式不正确（应为18位）"
            )
        ],
    )
    phone = models.CharField(
        "手机号",
        max_length=11,
        validators=[
            RegexValidator(regex=r"^1[3-9]\d{9}$", message="手机号格式不正确")
        ],
    )

    work_type = models.CharField(
        "工种",
        max_length=20,
        choices=WORK_TYPE_CHOICES,
    )
    skill_level = models.CharField(
        "技能等级",
        max_length=20,
        choices=SKILL_LEVEL_CHOICES,
        blank=True,
    )

    group = models.ForeignKey(
        WorkerGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workers",
        verbose_name="所属班组",
    )

    status = models.CharField(
        "状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    entry_date = models.DateField("入场日期", null=True, blank=True)
    leave_date = models.DateField("退场日期", null=True, blank=True)

    emergency_contact = models.CharField("紧急联系人", max_length=50, blank=True)
    emergency_phone = models.CharField("紧急联系电话", max_length=11, blank=True)
    health_cert = models.CharField("健康证号", max_length=50, blank=True)
    safety_cert = models.CharField("安全证号", max_length=50, blank=True)
    remark = models.TextField("备注", blank=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "workers"
        verbose_name = "施工人员"
        verbose_name_plural = "施工人员列表"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["id_card"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["status"]),
            models.Index(fields=["work_type"]),
        ]

    def __str__(self):
        return f"{self.name}（{self.get_work_type_display()}）"

    def clean(self):
        if self.leave_date and self.entry_date and self.leave_date < self.entry_date:
            raise ValidationError({"leave_date": "退场日期不能早于入场日期"})
