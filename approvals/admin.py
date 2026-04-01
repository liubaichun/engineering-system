from django.contrib import admin
from .models import ApprovalFlow, ApprovalNode


@admin.register(ApprovalFlow)
class ApprovalFlowAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'flow_type', 'status', 'created_by', 'created_at']
    list_filter = ['flow_type', 'status', 'created_at']
    search_fields = ['name', 'created_by__username']
    raw_id_fields = ['created_by', 'project', 'expense']
    readonly_fields = ['created_at']


@admin.register(ApprovalNode)
class ApprovalNodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'flow', 'approver', 'node_order', 'status', 'decided_at']
    list_filter = ['status', 'node_order']
    raw_id_fields = ['flow', 'approver']
