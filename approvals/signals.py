"""
Django Signals for Approvals
设备维保到期和物料低库存时自动创建通知
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta


@receiver(post_save)
def check_equipment_maintenance(sender, instance, created, **kwargs):
    """
    当设备保存后，检查是否维保到期并创建通知
    """
    if sender.__name__ != 'Equipment':
        return

    # 避免在创建时重复检查（创建时会单独处理）
    if created:
        return

    # 只有在更新 maintenance_due 字段时才检查
    if not hasattr(instance, '_maintenance_due_changed'):
        return

    try:
        from notifications.models import Notification

        if instance.maintenance_due:
            days_until_due = (instance.maintenance_due - timezone.now().date()).days

            if days_until_due <= 7:
                if days_until_due < 0:
                    title = f"【维保过期】{instance.name}"
                    message = f"设备「{instance.name}」的维保已于{days_until_due * -1}天前过期，请尽快处理！"
                else:
                    title = f"【维保即将到期】{instance.name}"
                    message = f"设备「{instance.name}」的维保将在{days_until_due}天后到期，请及时处理！"

                # 检查是否已存在
                existing = Notification.objects.filter(
                    title=title,
                    is_read=False
                ).exists()

                if not existing:
                    Notification.objects.create(
                        title=title,
                        message=message,
                        notification_type='equipment_maintenance',
                        related_id=instance.id
                    )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"设备维保通知创建失败: {str(e)}")


@receiver(post_save)
def check_material_low_stock(sender, instance, created, **kwargs):
    """
    当物料保存后，检查是否低库存并创建通知
    """
    if sender.__name__ != 'Material':
        return

    try:
        from notifications.models import Notification

        threshold = instance.low_stock_threshold or 10

        if instance.stock < threshold:
            title = f"【库存不足】{instance.name}"
            message = f"物料「{instance.name}」当前库存({instance.stock})低于阈值({threshold})，请及时补充！"

            # 检查是否已存在
            existing = Notification.objects.filter(
                title=title,
                is_read=False
            ).exists()

            if not existing:
                Notification.objects.create(
                    title=title,
                    message=message,
                    notification_type='low_stock',
                    related_id=instance.id
                )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"物料库存通知创建失败: {str(e)}")
