"""
Celery Configuration for Approvals App
配置定时任务调度
"""
from celery import Celery
from celery.schedules import crontab

# 设置 Celery Beat 定时任务
CELERY_BEAT_SCHEDULE = {
    # 每天早上9点检查设备维保到期情况
    'check-equipment-maintenance-daily': {
        'task': 'approvals.tasks.check_equipment_maintenance_due',
        'schedule': crontab(hour=9, minute=0),  # 每天9:00执行
    },
    # 每天早上9点检查物料低库存
    'check-material-low-stock-daily': {
        'task': 'approvals.tasks.check_material_low_stock',
        'schedule': crontab(hour=9, minute=0),  # 每天9:00执行
    },
    # 每周一早上9点检查项目预算
    'check-project-budget-weekly': {
        'task': 'approvals.tasks.check_project_budget_warning',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # 每周一9:00执行
    },
}
