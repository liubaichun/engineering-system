"""
任务相关 Celery 定时任务
"""
import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def check_task_delay_warning():
    """
    任务延期预警检查
    每天9点扫描所有未完成任务，根据截止日期+优先级发送预警通知

    预警规则：
    - 已逾期（end_date < 今天）：所有优先级均通知
    - 今日到期（end_date == 今天）：所有优先级均通知
    - 1天内到期（end_date == 明天）：高优先级通知
    - 3天内到期：仅高优先级通知
    - 7天内到期：仅高优先级通知
    """
    try:
        from tasks.models import Task
        from notifications.models import Notification

        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        three_days = today + timedelta(days=3)
        seven_days = today + timedelta(days=7)

        # 查询所有未完成的任务
        pending_statuses = ['pending', 'in_progress', 'blocked']
        tasks = Task.objects.filter(
            status__in=pending_statuses,
            end_date__isnull=False
        ).select_related('project', 'manager')

        notify_count = 0

        for task in tasks:
            end_date = task.end_date
            priority = task.priority
            is_high = priority == 'high'

            # 判断预警级别
            if end_date < today:
                # 已逾期
                title = f"【任务逾期】{task.name}"
                content = f"任务「{task.name}」（项目：{task.project.name}）已逾期，请立即处理！"
                notify = True
            elif end_date == today:
                # 今日到期
                title = f"【今日到期】{task.name}"
                content = f"任务「{task.name}」（项目：{task.project.name}）今日到期，请抓紧完成！"
                notify = True
            elif end_date == tomorrow and is_high:
                # 明天到期 + 高优先级
                title = f"【即将逾期】{task.name}"
                content = f"任务「{task.name}」（项目：{task.project.name}）明天到期，高优先级任务请及时处理！"
                notify = True
            elif end_date <= three_days and is_high:
                # 3天内到期 + 高优先级
                days_left = (end_date - today).days
                title = f"【预警提醒】{task.name}"
                content = f"任务「{task.name}」（项目：{task.project.name}）还有{days_left}天到期，高优先级任务请关注！"
                notify = True
            elif end_date <= seven_days and is_high:
                # 7天内到期 + 高优先级
                days_left = (end_date - today).days
                title = f"【任务提醒】{task.name}"
                content = f"任务「{task.name}」（项目：{task.project.name}）还有{days_left}天到期，请关注进度！"
                notify = True
            else:
                notify = False

            if notify and task.manager:
                # 避免重复通知
                existing = Notification.objects.filter(
                    title=title,
                    is_read=False
                ).exists()

                if not existing:
                    Notification.objects.create(
                        user=task.manager,
                        title=title,
                        content=content,
                        notification_type='task_delay',
                        link=f'/tasks/{task.id}/'
                    )
                    notify_count += 1

        logger.info(f"任务延期预警检查完成，发送通知 {notify_count} 条")
        return f"任务延期预警检查完成，发送通知 {notify_count} 条"

    except Exception as e:
        logger.error(f"任务延期预警检查失败: {str(e)}")
        raise
