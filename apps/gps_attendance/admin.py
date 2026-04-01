from django.contrib import admin
from .models import ProjectGPSSettings, WorkerGroup, Worker, AttendanceQRCode, AttendanceRecord


@admin.register(ProjectGPSSettings)
class ProjectGPSSettingsAdmin(admin.ModelAdmin):
    list_display = ['project', 'is_enabled', 'radius_meters', 'center_latitude', 'center_longitude', 'created_at']
    list_filter = ['is_enabled']
    search_fields = ['project__name']


@admin.register(WorkerGroup)
class WorkerGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'leader', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'project__name']


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ['name', 'id_card_number', 'phone', 'work_type', 'group', 'status', 'created_at']
    list_filter = ['status', 'work_type']
    search_fields = ['name', 'id_card_number', 'phone']


@admin.register(AttendanceQRCode)
class AttendanceQRCodeAdmin(admin.ModelAdmin):
    list_display = ['qr_id', 'project', 'group', 'valid_from', 'valid_until', 'is_used', 'created_at']
    list_filter = ['is_used']
    search_fields = ['qr_id', 'project__name']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['worker', 'project', 'group', 'check_in_time', 'check_out_time', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['worker__name', 'project__name']
    ordering = ['-created_at']
