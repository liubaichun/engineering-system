"""
GPS定位与考勤签到模块 - 数据模型

提供施工人员考勤签到功能，支持GPS位置校验与二维码集成
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import math

User = get_user_model()


class ProjectGPSSettings(models.Model):
    """
    项目GPS配置表
    存储每个项目的工地中心坐标和允许签到半径
    """
    
    class Meta:
        db_table = 'attendance_project_gps_settings'
        verbose_name = '项目GPS配置'
        verbose_name_plural = '项目GPS配置'
    
    project = models.OneToOneField(
        'projects.Project',
        on_delete=models.PROTECT,
        related_name='gps_settings',
        verbose_name='关联项目'
    )
    center_latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7,
        verbose_name='工地中心纬度'
    )
    center_longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7,
        verbose_name='工地中心经度'
    )
    radius_meters = models.IntegerField(
        default=500,
        verbose_name='允许签到半径（米）'
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name='GPS校验是否启用'
    )
    address = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='工地地址描述'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.project.name} - GPS配置"
    
    def get_coordinates(self):
        """获取工地中心坐标"""
        return float(self.center_latitude), float(self.center_longitude)
    
    def validate_location(self, latitude, longitude):
        """
        校验位置是否在工地范围内
        
        Args:
            latitude: 用户纬度
            longitude: 用户经度
            
        Returns:
            dict: {
                'is_within_range': bool,
                'distance_meters': int,
                'allowed_radius': int
            }
        """
        if not self.is_enabled:
            return {
                'is_within_range': True,
                'distance_meters': 0,
                'allowed_radius': self.radius_meters
            }
        
        distance = self.calculate_distance(
            float(self.center_latitude),
            float(self.center_longitude),
            latitude,
            longitude
        )
        
        return {
            'is_within_range': distance <= self.radius_meters,
            'distance_meters': int(distance),
            'allowed_radius': self.radius_meters
        }
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """
        使用Haversine公式计算两点间的地球表面距离
        
        Args:
            lat1, lon1: 第一个点的经纬度
            lat2, lon2: 第二个点的经纬度
            
        Returns:
            float: 距离（米）
        """
        R = 6371000  # 地球半径（米）
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 + 
             math.cos(phi1) * math.cos(phi2) * 
             math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


class WorkerGroup(models.Model):
    """
    班组表
    """
    
    class Meta:
        db_table = 'attendance_worker_groups'
        verbose_name = '班组'
        verbose_name_plural = '班组'
    
    name = models.CharField(max_length=100, verbose_name='班组名称')
    leader = models.ForeignKey(
        'Worker',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='led_groups',
        verbose_name='班组长'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='worker_groups',
        verbose_name='所属项目'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        return self.workers.filter(is_active=True).count()


class Worker(models.Model):
    """
    施工人员表
    """
    
    class Meta:
        db_table = 'attendance_workers'
        verbose_name = '施工人员'
        verbose_name_plural = '施工人员'
    
    class IDCardType(models.TextChoices):
        ID_CARD = 'id_card', '身份证'
        PASSPORT = 'passport', '护照'
    
    class WorkType(models.TextChoices):
        REBAR = 'rebar', '钢筋工'
        CARPENTER = 'carpenter', '木工'
        PLUMBER = 'plumber', '水电工'
        ELECTRICIAN = 'electrician', '电工'
        PAINTER = 'painter', '油漆工'
        GENERAL = 'general', '杂工'
        DRIVER = 'driver', '司机'
        FOREMAN = 'foreman', '工长'
    
    class SkillLevel(models.TextChoices):
        JUNIOR = 'junior', '初级'
        INTERMEDIATE = 'intermediate', '中级'
        SENIOR = 'senior', '高级'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', '在职'
        INACTIVE = 'inactive', '离职'
        SUSPENDED = 'suspended', '暂停'
    
    name = models.CharField(max_length=50, verbose_name='姓名')
    id_card_number = models.CharField(max_length=18, unique=True, verbose_name='身份证号')
    phone = models.CharField(max_length=20, verbose_name='手机号')
    id_card_type = models.CharField(
        max_length=20,
        choices=IDCardType.choices,
        default=IDCardType.ID_CARD,
        verbose_name='证件类型'
    )
    work_type = models.CharField(
        max_length=20,
        choices=WorkType.choices,
        blank=True,
        verbose_name='工种'
    )
    skill_level = models.CharField(
        max_length=20,
        choices=SkillLevel.choices,
        default=SkillLevel.JUNIOR,
        verbose_name='技能等级'
    )
    group = models.ForeignKey(
        WorkerGroup,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='workers',
        verbose_name='所属班组'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='状态'
    )
    entry_date = models.DateField(null=True, blank=True, verbose_name='入场日期')
    exit_date = models.DateField(null=True, blank=True, verbose_name='退场日期')
    avatar = models.ImageField(upload_to='workers/avatars/', null=True, blank=True, verbose_name='头像')
    is_deleted = models.BooleanField(default=False, verbose_name='软删除')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_work_type_display()})"


class AttendanceQRCode(models.Model):
    """
    二维码签到表
    班组长生成的签到二维码
    """
    
    class Meta:
        db_table = 'attendance_qr_codes'
        verbose_name = '签到二维码'
        verbose_name_plural = '签到二维码'
    
    qr_id = models.CharField(max_length=64, unique=True, verbose_name='二维码唯一ID')
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.PROTECT,
        related_name='attendance_qrcodes',
        verbose_name='关联项目'
    )
    group = models.ForeignKey(
        WorkerGroup,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='attendance_qrcodes',
        verbose_name='班组'
    )
    valid_from = models.DateTimeField(verbose_name='有效期起始')
    valid_until = models.DateTimeField(verbose_name='有效期截止')
    is_used = models.BooleanField(default=False, verbose_name='是否已使用')
    used_by = models.ForeignKey(
        Worker,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='used_qrcodes',
        verbose_name='使用人'
    )
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用时间')
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_qrcodes',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.qr_id} - {self.project.name}"
    
    def save(self, *args, **kwargs):
        if not self.qr_id:
            self.qr_id = f"qr_{uuid.uuid4().hex[:24]}"
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """检查二维码是否有效"""
        now = timezone.now()
        return (
            not self.is_used and 
            self.valid_from <= now <= self.valid_until
        )
    
    def mark_used(self, worker):
        """标记二维码已使用"""
        self.is_used = True
        self.used_by = worker
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_by', 'used_at'])


class AttendanceRecord(models.Model):
    """
    考勤签到记录表
    记录工人的签到和签退信息，包含GPS位置
    """
    
    class Meta:
        db_table = 'attendance_records'
        verbose_name = '考勤记录'
        verbose_name_plural = '考勤记录'
        ordering = ['-created_at']
    
    class Status(models.TextChoices):
        NORMAL = 'normal', '正常'
        LATE = 'late', '迟到'
        EARLY_LEAVE = 'early_leave', '早退'
        ABSENT = 'absent', '缺勤'
    
    worker = models.ForeignKey(
        Worker,
        on_delete=models.PROTECT,
        related_name='attendance_records',
        verbose_name='施工人员'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.PROTECT,
        related_name='attendance_records',
        verbose_name='签到项目'
    )
    group = models.ForeignKey(
        WorkerGroup,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='attendance_records',
        verbose_name='班组'
    )
    
    # 签到信息
    check_in_time = models.DateTimeField(null=True, blank=True, verbose_name='签到时间')
    check_in_latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        verbose_name='签到纬度'
    )
    check_in_longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        verbose_name='签到经度'
    )
    check_in_location_valid = models.BooleanField(default=True, verbose_name='签到位置是否有效')
    check_in_distance_meters = models.IntegerField(null=True, blank=True, verbose_name='签到距工地距离')
    
    # 签退信息
    check_out_time = models.DateTimeField(null=True, blank=True, verbose_name='签退时间')
    check_out_latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        verbose_name='签退纬度'
    )
    check_out_longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True,
        verbose_name='签退经度'
    )
    check_out_location_valid = models.BooleanField(default=True, verbose_name='签退位置是否有效')
    check_out_distance_meters = models.IntegerField(null=True, blank=True, verbose_name='签退距工地距离')
    
    # 关联二维码
    qr_code = models.ForeignKey(
        AttendanceQRCode,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='attendance_records',
        verbose_name='签到二维码'
    )
    
    # 状态
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NORMAL,
        verbose_name='考勤状态'
    )
    
    remark = models.TextField(blank=True, verbose_name='备注')
    is_deleted = models.BooleanField(default=False, verbose_name='软删除')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.worker.name} - {self.check_in_time.date() if self.check_in_time else 'N/A'}"
    
    @property
    def working_hours(self):
        """计算工作时长（小时）"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            return round(delta.total_seconds() / 3600, 1)
        return None
    
    def update_status(self):
        """根据签到时间自动更新状态"""
        if not self.project:
            return
        
        # 获取项目配置的正常上班时间
        # 这里简化处理，实际应从项目配置读取
        normal_start_hour = 9
        normal_end_hour = 18
        
        if self.check_in_time and self.check_in_time.hour > normal_start_hour:
            self.status = self.Status.LATE
        
        if self.check_out_time and self.check_out_time.hour < normal_end_hour:
            self.status = self.Status.EARLY_LEAVE
