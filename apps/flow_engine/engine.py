"""
任务流程引擎
实现流程的创建、流转、转交、完成等核心功能
"""
import logging
from datetime import timedelta
from typing import Optional, Dict
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class FlowEngineError(Exception):
    """流程引擎异常基类"""
    pass


class InvalidTransitionError(FlowEngineError):
    """无效的流转异常"""
    pass


class FlowNotFoundError(FlowEngineError):
    """流程未找到异常"""
    pass


class NodeNotFoundError(FlowEngineError):
    """节点未找到异常"""
    pass


class TransferError(FlowEngineError):
    """转交异常"""
    pass


class FlowEngine:
    """
    任务流程引擎
    负责流程实例的创建、节点流转、转交、完成等操作
    """
    
    def __init__(self):
        self.now = timezone.now()
    
    def create_flow(
        self,
        task,
        template=None,
        initiator=None,
        context_data: Optional[Dict] = None,
        start_node=None
    ):
        """发起流程"""
        from apps.flow_engine.models import TaskFlowInstance
        from tasks.models import StageActivity, FlowNodeTemplate, TaskStageInstance
        
        with transaction.atomic():
            if template is None:
                template = task.flow_template
            
            if start_node is None and template:
                start_node = template.nodes.filter(is_start=True).first()
            
            if start_node is None:
                raise NodeNotFoundError("未找到流程起始节点")
            
            deadline = self.now + timedelta(hours=start_node.duration_hours) if start_node.duration_hours else None
            
            flow_instance = TaskFlowInstance.objects.create(
                task=task,
                template=template,
                status='active',
                initiator=initiator or task.manager,
                current_node=start_node,
                started_at=self.now,
                deadline=deadline,
                context_data=context_data or {}
            )
            
            stage_instance = TaskStageInstance.objects.create(
                task=task,
                template_node=start_node,
                order=start_node.order,
                assigned_to=self._resolve_responsible_user(start_node, task, initiator),
                status='in_progress',
                started_at=self.now,
                deadline=deadline
            )
            
            task.current_stage = start_node
            task.save(update_fields=['current_stage'])
            
            StageActivity.objects.create(
                stage_instance=stage_instance,
                operator=initiator or task.manager,
                action_type='create',
                content=f'流程已发起，当前节点：{start_node.name}'
            )
            
            logger.info(f"流程创建成功: task={task.id}, flow={flow_instance.id}, node={start_node.name}")
            
        return flow_instance
    
    def transition_to(
        self,
        task,
        target_node=None,
        target_node_id: Optional[int] = None,
        operator=None,
        action: str = 'complete',
        remark: str = ''
    ):
        """流转到下一节点"""
        from apps.flow_engine.models import TaskFlowInstance
        from tasks.models import StageActivity, FlowNodeTemplate, TaskStageInstance
        
        with transaction.atomic():
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status != 'active':
                raise InvalidTransitionError(f"流程状态不允许流转，当前状态：{flow_instance.status}")
            
            if target_node is None:
                if target_node_id:
                    target_node = FlowNodeTemplate.objects.get(id=target_node_id)
                else:
                    current_node = flow_instance.current_node
                    target_node = self._get_next_node(current_node, action)
            
            if target_node is None:
                return self.complete_flow(task, operator)
            
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage:
                current_stage.status = 'completed' if action == 'complete' else 'rejected'
                current_stage.completed_at = self.now
                current_stage.save()
                
                StageActivity.objects.create(
                    stage_instance=current_stage,
                    operator=operator,
                    action_type=action,
                    content=remark or f'节点已完成，转入：{target_node.name}'
                )
            
            deadline = self.now + timedelta(hours=target_node.duration_hours) if target_node.duration_hours else None
            
            new_stage = TaskStageInstance.objects.create(
                task=task,
                template_node=target_node,
                order=target_node.order,
                assigned_to=self._resolve_responsible_user(target_node, task, operator),
                status='in_progress',
                started_at=self.now,
                deadline=deadline
            )
            
            flow_instance.current_node = target_node
            flow_instance.deadline = deadline
            flow_instance.save()
            
            task.current_stage = target_node
            task.save(update_fields=['current_stage'])
            
            StageActivity.objects.create(
                stage_instance=new_stage,
                operator=operator,
                action_type='start',
                content=f'进入节点：{target_node.name}'
            )
            
            logger.info(f"流程流转成功: task={task.id}, node={target_node.name}, action={action}")
            
        return new_stage
    
    def _get_next_node(self, current_node, action: str = 'complete'):
        """获取下一节点"""
        from tasks.models import FlowTransition
        
        transitions = FlowTransition.objects.filter(
            from_node=current_node
        ).order_by('from_node__order')
        
        for transition in transitions:
            if action == 'complete':
                if not transition.to_node.is_end:
                    return transition.to_node
            elif action == 'reject':
                if transition.to_node.name in ['驳回', '重试', 'reject']:
                    return transition.to_node
        
        for transition in transitions:
            return transition.to_node
        
        return None
    
    def _resolve_responsible_user(self, node, task, operator=None):
        """解析节点负责人"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        if node.responsible_type == 'user':
            user_ids = node.responsible_users or []
            if user_ids:
                return User.objects.filter(id__in=user_ids).first()
        
        return task.manager or operator
    
    def transfer_to(
        self,
        task,
        target_user,
        operator=None,
        remark: str = ''
    ):
        """转交流程给其他人"""
        from apps.flow_engine.models import TaskFlowInstance
        from tasks.models import StageActivity, TaskStageInstance
        
        with transaction.atomic():
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status != 'active':
                raise TransferError(f"流程状态不允许转交，当前状态：{flow_instance.status}")
            
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage is None:
                raise TransferError("未找到进行中的阶段")
            
            old_assignee = current_stage.assigned_to
            
            current_stage.assigned_to = target_user
            current_stage.save()
            
            StageActivity.objects.create(
                stage_instance=current_stage,
                operator=operator,
                action_type='transfer',
                content=remark or f'任务已从 {old_assignee} 转交给 {target_user}'
            )
            
            logger.info(f"任务转交成功: task={task.id}, from={old_assignee}, to={target_user}")
            
        return current_stage
    
    def complete_flow(self, task, operator=None, remark: str = ''):
        """完成流程"""
        from apps.flow_engine.models import TaskFlowInstance
        from tasks.models import StageActivity, TaskStageInstance
        
        with transaction.atomic():
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage:
                current_stage.status = 'completed'
                current_stage.completed_at = self.now
                current_stage.save()
                
                StageActivity.objects.create(
                    stage_instance=current_stage,
                    operator=operator,
                    action_type='complete',
                    content=remark or '流程已完成'
                )
            
            flow_instance.status = 'completed'
            flow_instance.completed_at = self.now
            flow_instance.save()
            
            task.status = 'completed'
            task.current_stage = None
            task.save(update_fields=['status', 'current_stage'])
            
            logger.info(f"流程已完成: task={task.id}")
            
        return flow_instance
    
    def cancel_flow(self, task, operator=None, remark: str = ''):
        """取消流程"""
        from apps.flow_engine.models import TaskFlowInstance
        from tasks.models import StageActivity, TaskStageInstance
        
        with transaction.atomic():
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status not in ['active', 'draft']:
                raise InvalidTransitionError(f"流程状态不允许取消，当前状态：{flow_instance.status}")
            
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage:
                current_stage.status = 'skipped'
                current_stage.completed_at = self.now
                current_stage.save()
                
                StageActivity.objects.create(
                    stage_instance=current_stage,
                    operator=operator,
                    action_type='system',
                    content=f'流程已取消: {remark}'
                )
            
            flow_instance.status = 'cancelled'
            flow_instance.completed_at = self.now
            flow_instance.save()
            
            task.status = 'blocked'
            task.save(update_fields=['status'])
            
            logger.info(f"流程已取消: task={task.id}")
            
        return flow_instance
    
    def suspend_flow(self, task, operator=None, remark: str = ''):
        """暂停流程"""
        from apps.flow_engine.models import TaskFlowInstance
        from tasks.models import StageActivity, TaskStageInstance
        
        with transaction.atomic():
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status != 'active':
                raise InvalidTransitionError(f"流程状态不允许暂停，当前状态：{flow_instance.status}")
            
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage:
                StageActivity.objects.create(
                    stage_instance=current_stage,
                    operator=operator,
                    action_type='system',
                    content=f'流程已暂停: {remark}'
                )
            
            flow_instance.status = 'suspended'
            flow_instance.save()
            
            logger.info(f"流程已暂停: task={task.id}")
            
        return flow_instance
    
    def resume_flow(self, task, operator=None, remark: str = ''):
        """恢复流程"""
        from apps.flow_engine.models import TaskFlowInstance
        from tasks.models import StageActivity, TaskStageInstance
        
        with transaction.atomic():
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status != 'suspended':
                raise InvalidTransitionError(f"流程状态不允许恢复，当前状态：{flow_instance.status}")
            
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage:
                StageActivity.objects.create(
                    stage_instance=current_stage,
                    operator=operator,
                    action_type='system',
                    content=f'流程已恢复: {remark}'
                )
            
            flow_instance.status = 'active'
            flow_instance.save()
            
            logger.info(f"流程已恢复: task={task.id}")
            
        return flow_instance
    
    def get_flow_progress(self, task):
        """获取流程进度"""
        from tasks.models import TaskStageInstance, FlowNodeTemplate
        
        stages = TaskStageInstance.objects.filter(task=task).order_by('order')
        total = stages.count()
        if total == 0:
            return {'total': 0, 'completed': 0, 'progress': 0}
        
        completed = stages.filter(status='completed').count()
        
        return {
            'total': total,
            'completed': completed,
            'progress': round(completed / total * 100, 1)
        }
