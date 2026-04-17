"""
流程引擎 Celery 任务
包括超时检测、状态同步等定时任务
"""
import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)


@shared_task(name='flow_engine.check_overdue_flows')
def check_overdue_flows():
    """
    检查超时流程
    检测所有进行中的流程和阶段是否超时，更新超时状态
    """
    from apps.flow_engine.models import TaskFlowInstance
    from tasks.models import TaskStageInstance
    
    now = timezone.now()
    results = {
        'flows_checked': 0,
        'flows_overdue': 0,
        'stages_checked': 0,
        'stages_overdue': 0,
        'notified': 0
    }
    
    # 检查流程实例超时
    active_flows = TaskFlowInstance.objects.filter(
        status='active',
        deadline__isnull=False
    ).select_related('task', 'current_node')
    
    for flow in active_flows:
        results['flows_checked'] += 1
        
        if flow.deadline and flow.deadline < now:
            if not flow.is_overdue:
                flow.is_overdue = True
                flow.save(update_fields=['is_overdue'])
                results['flows_overdue'] += 1
                logger.warning(f"流程超时: flow_id={flow.id}, task={flow.task.name}, deadline={flow.deadline}")
            
            # 发送超时通知（仅发送一次）
            if not flow.overdue_notified and flow.current_node and flow.current_node.notify_on_overdue:
                _send_overdue_notification(flow, 'flow')
                flow.overdue_notified = True
                flow.save(update_fields=['overdue_notified'])
                results['notified'] += 1
    
    # 检查阶段实例超时
    active_stages = TaskStageInstance.objects.filter(
        status='in_progress',
        deadline__isnull=False
    ).select_related('task', 'template_node')
    
    for stage in active_stages:
        results['stages_checked'] += 1
        
        if stage.deadline and stage.deadline < now:
            if not stage.is_overdue:
                stage.is_overdue = True
                stage.save(update_fields=['is_overdue'])
                results['stages_overdue'] += 1
                logger.warning(f"阶段超时: stage_id={stage.id}, task={stage.task.name}, deadline={stage.deadline}")
    
    logger.info(f"超时检查完成: {results}")
    return results


@shared_task(name='flow_engine.sync_task_status')
def sync_task_status():
    """
    同步任务状态
    确保任务状态与流程实例状态保持一致
    """
    from apps.flow_engine.models import TaskFlowInstance
    from tasks.models import Task
    
    results = {
        'tasks_checked': 0,
        'tasks_updated': 0
    }
    
    # 查找状态不一致的任务
    # 流程已完成但任务状态不是 completed
    inconsistent_tasks = Task.objects.filter(
        flow_instance__status='completed',
        status__in=['pending', 'in_progress']
    )
    
    for task in inconsistent_tasks:
        results['tasks_checked'] += 1
        task.status = 'completed'
        task.save(update_fields=['status'])
        results['tasks_updated'] += 1
        logger.info(f"任务状态已同步: task_id={task.id}")
    
    # 流程已取消但任务状态不是 blocked
    cancelled_tasks = Task.objects.filter(
        flow_instance__status='cancelled',
        status__in=['pending', 'in_progress', 'completed']
    )
    
    for task in cancelled_tasks:
        results['tasks_checked'] += 1
        task.status = 'blocked'
        task.save(update_fields=['status'])
        results['tasks_updated'] += 1
        logger.info(f"任务状态已同步(取消): task_id={task.id}")
    
    logger.info(f"状态同步完成: {results}")
    return results


@shared_task(name='flow_engine.cleanup_completed_flows')
def cleanup_completed_flows(days: int = 90):
    """
    清理已完成的流程记录
    默认保留90天内的记录
    
    Args:
        days: 保留天数
    """
    from apps.flow_engine.models import TaskFlowInstance
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # 只清理已完成的流程
    old_flows = TaskFlowInstance.objects.filter(
        status='completed',
        completed_at__lt=cutoff_date
    )
    
    count = old_flows.count()
    old_flows.delete()
    
    logger.info(f"已清理 {count} 条历史流程记录")
    return {'deleted_count': count, 'cutoff_date': cutoff_date.isoformat()}


@shared_task(name='flow_engine.notify_upcoming_deadlines')
def notify_upcoming_deadlines(hours_before: int = 24):
    """
    发送即将到期提醒
    在截止时间前指定小时数发送提醒
    
    Args:
        hours_before: 提前多少小时发送提醒
    """
    from apps.flow_engine.models import TaskFlowInstance
    from tasks.models import TaskStageInstance
    
    now = timezone.now()
    notify_time = now + timedelta(hours=hours_before)
    notify_window_start = notify_time - timedelta(minutes=5)
    notify_window_end = notify_time + timedelta(minutes=5)
    
    results = {
        'flow_notified': 0,
        'stage_notified': 0
    }
    
    # 查找即将到期的流程
    upcoming_flows = TaskFlowInstance.objects.filter(
        status='active',
        deadline__gte=notify_window_start,
        deadline__lte=notify_window_end,
        overdue_notified=False
    ).select_related('task', 'current_node')
    
    for flow in upcoming_flows:
        _send_upcoming_notification(flow, 'flow')
        results['flow_notified'] += 1
    
    # 查找即将到期的阶段
    upcoming_stages = TaskStageInstance.objects.filter(
        status='in_progress',
        deadline__gte=notify_window_start,
        deadline__lte=notify_window_end
    ).select_related('task', 'template_node')
    
    for stage in upcoming_stages:
        _send_upcoming_notification(stage, 'stage')
        results['stage_notified'] += 1
    
    logger.info(f"即将到期提醒已发送: {results}")
    return results


def _send_overdue_notification(instance, instance_type: str):
    """发送超时通知（实际实现需要根据通知系统）"""
    # TODO: 实现实际的通知发送逻辑
    # 可以集成 notifications 模块发送邮件/站内信/短信等
    logger.info(
        f"发送超时通知: type={instance_type}, "
        f"id={instance.id}, "
        f"task={instance.task.name if hasattr(instance, 'task') else instance.template_node.task.name}"
    )


def _send_upcoming_notification(instance, instance_type: str):
    """发送即将到期通知"""
    logger.info(
        f"发送即将到期提醒: type={instance_type}, "
        f"id={instance.id}, "
        f"deadline={instance.deadline}"
    )
