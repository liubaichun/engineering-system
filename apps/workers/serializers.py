from rest_framework import serializers
from .models import Project, WorkerGroup, Worker
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


# ------------ WorkerGroup Serializer ------------

class WorkerGroupListSerializer(serializers.ModelSerializer):
    """班组列表（轻量，含 worker_count）"""
    worker_count = serializers.IntegerField(read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True, default="")
    leader_name = serializers.CharField(source="leader.name", read_only=True, default="")

    class Meta:
        model = WorkerGroup
        fields = [
            "id", "name", "phone",
            "leader", "leader_name",
            "project", "project_name",
            "worker_count",
            "created_at",
        ]


class WorkerGroupDetailSerializer(serializers.ModelSerializer):
    """班组详情（含人员列表）"""
    worker_count = serializers.IntegerField(read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True, default="")
    leader_detail = WorkerGroupListSerializer(source="leader", read_only=True)
    workers = serializers.SerializerMethodField()

    class Meta:
        model = WorkerGroup
        fields = [
            "id", "name", "phone",
            "leader", "leader_detail",
            "project", "project_name",
            "worker_count", "workers",
            "remark",
            "created_at", "updated_at",
        ]

    def get_workers(self, obj):
        workers = obj.workers.all()
        return WorkerListSerializer(workers, many=True).data


class WorkerGroupWriteSerializer(serializers.ModelSerializer):
    """班组创建/更新"""

    class Meta:
        model = WorkerGroup
        fields = [
            "id", "name", "leader", "phone",
            "project", "remark",
        ]

    def validate_leader(self, value):
        if value and value.group and value.group != self.instance:
            # 若 leader 已有班组且不是当前班组，报错
            # （允许 leader=None 的新建场景）
            if self.instance and value.group != self.instance:
                raise serializers.ValidationError("班组长必须属于本班组")
        return value


# ------------ Worker Serializer ------------

class WorkerListSerializer(serializers.ModelSerializer):
    """人员列表（轻量）"""
    group_name = serializers.CharField(source="group.name", read_only=True, default="")
    work_type_display = serializers.CharField(source="get_work_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    skill_level_display = serializers.CharField(source="get_skill_level_display", read_only=True, default="")

    class Meta:
        model = Worker
        fields = [
            "id", "name", "phone",
            "work_type", "work_type_display",
            "skill_level", "skill_level_display",
            "group", "group_name",
            "status", "status_display",
            "entry_date",
        ]


class WorkerDetailSerializer(serializers.ModelSerializer):
    """人员详情"""
    group_name = serializers.CharField(source="group.name", read_only=True, default="")
    work_type_display = serializers.CharField(source="get_work_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    skill_level_display = serializers.CharField(source="get_skill_level_display", read_only=True, default="")
    leader_of_group = serializers.SerializerMethodField()

    class Meta:
        model = Worker
        fields = [
            # 基本信息
            "id", "name", "id_card", "phone",
            # 务工信息
            "work_type", "work_type_display",
            "skill_level", "skill_level_display",
            # 组织
            "group", "group_name",
            "leader_of_group",
            # 状态 & 日期
            "status", "status_display",
            "entry_date", "leave_date",
            # 扩展
            "emergency_contact", "emergency_phone",
            "health_cert", "safety_cert",
            "remark",
            # 审计
            "created_at", "updated_at",
        ]

    def get_leader_of_group(self, obj):
        """是否担任班组长"""
        if obj.led_groups.exists():
            return WorkerGroupListSerializer(obj.led_groups.all(), many=True).data
        return []


class WorkerWriteSerializer(serializers.ModelSerializer):
    """人员创建/更新"""

    class Meta:
        model = Worker
        fields = [
            # 基本信息
            "id", "name", "id_card", "phone",
            # 务工信息
            "work_type", "skill_level",
            # 组织
            "group",
            # 状态 & 日期
            "status", "entry_date", "leave_date",
            # 扩展
            "emergency_contact", "emergency_phone",
            "health_cert", "safety_cert",
            "remark",
        ]

    def validate(self, attrs):
        leave_date = attrs.get("leave_date")
        entry_date = attrs.get("entry_date")
        if leave_date and entry_date and leave_date < entry_date:
            raise serializers.ValidationError({"leave_date": "退场日期不能早于入场日期"})
        return attrs
