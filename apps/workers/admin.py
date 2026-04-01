# ============================================================
# 6. admin.py（Django Admin 后台注册）
# ============================================================

from django.contrib import admin
from .models import Project, WorkerGroup, Worker


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "status", "start_date", "end_date", "created_at"]
    list_filter = ["status"]
    search_fields = ["name", "code", "address"]
    ordering = ["-created_at"]


@admin.register(WorkerGroup)
class WorkerGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "leader", "phone", "project", "worker_count", "created_at"]
    list_filter = ["project"]
    search_fields = ["name", "phone"]
    autocomplete_fields = ["leader", "project"]


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = [
        "name", "id_card", "phone",
        "work_type", "skill_level",
        "group", "status",
        "entry_date", "leave_date",
    ]
    list_filter = ["status", "work_type", "skill_level", "group"]
    search_fields = ["name", "id_card", "phone"]
    autocomplete_fields = ["group"]
    date_hierarchy = "entry_date"
