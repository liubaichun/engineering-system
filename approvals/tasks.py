"""
Celery Tasks for Approvals and Notifications
设备维保到期提醒 + 物料低库存预警
"""
from celery import shared_task
from django.utils import timezone
from django.db import models
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_equipment_maintenance_due():
    """
    定时任务：检查设备维修状态
    每天执行一次，当设备状态为维修中时发送提醒
    """
    try:
        from inventory.models import Equipment
        from notifications.models import Notification

        # 查找处于维修状态的设备
        maintenance_equipment = Equipment.objects.filter(status='maintenance')

        created_count = 0
        for equipment in maintenance_equipment:
            title = f"【设备维修中】{equipment.name}"
            message = f"设备「{equipment.name}」（编码：{equipment.code}）当前处于维修状态，请关注进度！"

            existing = Notification.objects.filter(
                title=title,
                is_read=False
            ).exists()

            if not existing:
                Notification.objects.create(
                    title=title,
                    message=message,
                    notification_type='equipment_maintenance',
                    related_id=equipment.id
                )
                created_count += 1

        logger.info(f"设备维修检查完成: 检查了{len(maintenance_equipment)}台设备，创建了{created_count}条通知")
        return {
            'checked': len(maintenance_equipment),
            'created': created_count
        }
    except Exception as e:
        logger.error(f"设备维修检查任务失败: {str(e)}")
        raise


@shared_task
def check_material_low_stock():
    """
    定时任务：检查物料低库存
    当物料 stock <= alert_threshold 时自动创建通知
    """
    try:
        from inventory.models import MaterialNew
        from notifications.models import Notification

        # 查找低库存物料（stock <= alert_threshold）
        low_stock_materials = MaterialNew.objects.filter(
            stock__lte=models.F('alert_threshold')
        )

        created_count = 0
        for material in low_stock_materials:
            title = f"【库存不足】{material.name}"
            message = f"物料「{material.name}」当前库存({material.stock})低于或等于预警阈值({material.alert_threshold})，请及时补充！"

            existing = Notification.objects.filter(
                title=title,
                is_read=False
            ).exists()

            if not existing:
                Notification.objects.create(
                    title=title,
                    message=message,
                    notification_type='low_stock',
                    related_id=material.id
                )
                created_count += 1

        logger.info(f"物料库存检查完成: 检查了{len(low_stock_materials)}种物料，创建了{created_count}条通知")
        return {
            'checked': len(low_stock_materials),
            'created': created_count
        }
    except Exception as e:
        logger.error(f"物料库存检查任务失败: {str(e)}")
        raise


@shared_task
def check_project_budget_warning():
    """
    定时任务：检查项目预算超支预警
    当项目支出超过预算的80%时发送预警
    """
    try:
        from projects.models import Project
        from finance.models import Expense
        from notifications.models import Notification
        from django.db.models import Sum

        # 只检查进行中的项目（construction状态）
        projects = Project.objects.filter(status='construction')

        created_count = 0
        for project in projects:
            total_expense = Expense.objects.filter(project=project.id).aggregate(
                total=Sum('amount')
            )['total'] or 0

            if project.budget and float(project.budget) > 0:
                usage_ratio = float(total_expense) / float(project.budget)

                if usage_ratio >= 0.8:
                    existing = Notification.objects.filter(
                        title__contains=f"【预算预警】{project.name}",
                        is_read=False
                    ).exists()

                    if not existing:
                        percentage = int(usage_ratio * 100)
                        title = f"【预算预警】{project.name}"
                        message = f"项目「{project.name}」支出已达预算的{percentage}%（{total_expense}/{project.budget}），请关注！"

                        Notification.objects.create(
                            title=title,
                            message=message,
                            notification_type='budget_warning',
                            related_id=project.id
                        )
                        created_count += 1

        logger.info(f"项目预算检查完成: 检查了{len(projects)}个项目，创建了{created_count}条通知")
        return {
            'checked': len(projects),
            'created': created_count
        }
    except Exception as e:
        logger.error(f"项目预算检查任务失败: {str(e)}")
        raise
