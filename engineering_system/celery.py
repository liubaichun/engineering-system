"""
Celery configuration for engineering_system project.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engineering_system.settings')

app = Celery('engineering_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Load task modules from installed apps
app.autodiscover_tasks(['approvals', 'tasks'])

# Celery Beat schedule
app.conf.beat_schedule = {
    'check-equipment-maintenance-daily': {
        'task': 'approvals.tasks.check_equipment_maintenance_due',
        'schedule': crontab(hour=9, minute=0),
    },
    'check-material-low-stock-daily': {
        'task': 'approvals.tasks.check_material_low_stock',
        'schedule': crontab(hour=9, minute=0),
    },
    'check-project-budget-weekly': {
        'task': 'approvals.tasks.check_project_budget_warning',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
    'check-task-delay-daily': {
        'task': 'tasks.tasks.check_task_delay_warning',
        'schedule': crontab(hour=9, minute=0),
    },
}
