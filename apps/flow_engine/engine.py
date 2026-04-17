"""
任务流程引擎
实现流程的创建、流转、转交、完成等核心功能
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.conf import settings

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
    ) -> 'TaskFlowInstance':
        """
        发起流程
        
        Args:
            task: 关联的任务实例
            template: 流程模板（可选）
            initiator: 流程发起人
            context_data: 流程上下文数据
            start_node: 起始节点（可选，默认使用模板的起始节点）
        
        Returns:
            TaskFlowInstance: 创建的流程实例
        """
        from apps.flow_engine.models import TaskFlowInstance, StageActivity
        from tasks.models import FlowTemplate, FlowNodeTemplate, TaskStageInstance
        
        with transaction.atomic():
            # 如果没有指定模板，尝试从任务获取
            if template is None:
                template = task.flow_template
            
            # 确定起始节点
            if start_node is None and template:
                start_node = template.nodes.filter(is_start=True).first()
            
            if start_node is None:
                raise NodeNotFoundError("未找到流程起始节点")
            
            # 计算截止时间
            deadline = self.now + timedelta(hours=start_node.duration_hours) if start_node.duration_hours else None
            
            # 创建流程实例
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
            
            # 创建阶段实例
            stage_instance = TaskStageInstance.objects.create(
                task=task,
                template_node=start_node,
                order=start_node.order,
                assigned_to=self._resolve_responsible_user(start_node, task, initiator),
                status='in_progress',
                started_at=self.now,
                deadline=deadline
            )
            
            # 更新任务的当前阶段
            task.current_stage = start_node
            task.save(update_fields=['current_stage'])
            
            # 记录活动
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
    ) -> 'TaskStageInstance':
        """
        流转到下一节点
        
        Args:
            task: 任务实例
            target_node: 目标节点对象（可选）
            target_node_id: 目标节点ID（可选）
            operator: 操作人
            action: 操作类型 (complete/reject)
            remark: 备注
        
        Returns:
            TaskStageInstance: 新的阶段实例
        """
        from apps.flow_engine.models import TaskFlowInstance, StageActivity
        from tasks.models import TaskStageInstance, FlowNodeTemplate
        
        with transaction.atomic():
            # 获取当前流程实例
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status != 'active':
                raise InvalidTransitionError(f"流程状态不允许流转，当前状态：{flow_instance.status}")
            
            # 获取目标节点
            if target_node is None:
                if target_node_id:
                    target_node = FlowNodeTemplate.objects.get(id=target_node_id)
                else:
                    # 自动查找下一节点
                    current_node = flow_instance.current_node
                    target_node = self._get_next_node(current_node, action)
            
            if target_node is None:
                # 如果没有下一节点，则流程结束
                return self.complete_flow(task, operator)
            
            # 完成当前阶段
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage:
                current_stage.status = 'completed' if action == 'complete' else 'rejected'
                current_stage.completed_at = self.now
                current_stage.save()
                
                # 记录当前节点活动
                StageActivity.objects.create(
                    stage_instance=current_stage,
                    operator=operator,
                    action_type=action,
                    content=remark or f'节点已完成，转入：{target_node.name}'
                )
            
            # 创建新的阶段实例
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
            
            # 更新流程实例
            flow_instance.current_node = target_node
            flow_instance.deadline = deadline
            flow_instance.save()
            
            # 更新任务当前阶段
            task.current_stage = target_node
            task.save(update_fields=['current_stage'])
            
            # 记录新节点活动
            StageActivity.objects.create(
                stage_instance=new_stage,
                operator=operator,
                action_type='start',
                content=f'进入节点：{target_node.name}'
            )
            
            logger.info(f"流程流转成功: task={task.id}, node={target_node.name}, action={action}")
            
        return new_stage
    
    def _get_next_node(self, current_node, action: str = 'complete') -> Optional['FlowNodeTemplate']:
        """获取下一节点"""
        from tasks.models import FlowTransition
        
        transitions = FlowTransition.objects.filter(
            from_node=current_node
        ).order_by('from_node__order')
        
        for transition in transitions:
            # 根据action筛选目标节点
            if action == 'complete':
                # 完成操作通常流向下一个正常节点
                if not transition.to_node.is_end:
                    return transition.to_node
            elif action == 'reject':
                # 驳回操作可能流向驳回节点
                if transition.to_node.name in ['驳回', '重试', 'reject']:
                    return transition.to_node
        
        # 如果没找到特定节点，返回第一个可用的
        for transition in transitions:
            return transition.to_node
        
        return None
    
    def _resolve_responsible_user(self, node, task, operator=None):
        """解析节点负责人"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        if node.responsible_type == 'user':
            # 指定人员
            user_ids = node.responsible_users or []
            if user_ids:
                return User.objects.filter(id__in=user_ids).first()
        
        elif node.responsible_type == 'role':
            # 角色关联 - 简化处理，返回任务的原负责人
            pass
        
        # 默认返回任务负责人或操作人
        return task.manager or operator
    
    def transfer_to(
        self,
        task,
        target_user,
        operator=None,
        remark: str = ''
    ) -> 'TaskStageInstance':
        """
        转交流程给其他人
        
        Args:
            task: 任务实例
            target_user: 目标用户
            operator: 操作人
            remark: 转交原因
        
        Returns:
            TaskStageInstance: 当前阶段实例
        """
        from apps.flow_engine.models import TaskFlowInstance, StageActivity
        from tasks.models import TaskStageInstance
        
        with transaction.atomic():
            # 获取当前流程实例
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status != 'active':
                raise TransferError(f"流程状态不允许转交，当前状态：{flow_instance.status}")
            
            # 获取当前阶段
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage is None:
                raise TransferError("未找到进行中的阶段")
            
            old_assignee = current_stage.assigned_to
            
            # 更新阶段负责人
            current_stage.assigned_to = target_user
            current_stage.save()
            
            # 记录转交活动
            StageActivity.objects.create(
                stage_instance=current_stage,
                operator=operator,
                action_type='transfer',
                content=remark or f'任务已从 {old_assignee} 转交给 {target_user}'
            )
            
            logger.info(f"任务转交成功: task={task.id}, from={old_assignee}, to={target_user}")
            
        return current_stage
    
    def complete_flow(
        self,
        task,
        operator=None,
        remark: str = ''
    ) -> 'TaskFlowInstance':
        """
        完成流程
        
        Args:
            task: 任务实例
            operator: 操作人
            remark: 备注
        
        Returns:
            TaskFlowInstance: 完成的流程实例
        """
        from apps.flow_engine.models import TaskFlowInstance, StageActivity
        from tasks.models import TaskStageInstance
        
        with transaction.atomic():
            # 获取当前流程实例
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            # 完成当前阶段
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage:
                current_stage.status = 'completed'
                current_stage.completed_at = self.now
                current_stage.save()
                
                # 记录活动
                StageActivity.objects.create(
                    stage_instance=current_stage,
                    operator=operator,
                    action_type='complete',
                    content=remark or '流程已完成'
                )
            
            # 更新流程实例状态
            flow_instance.status = 'completed'
            flow_instance.completed_at = self.now
            flow_instance.save()
            
            # 更新任务状态
            task.status = 'completed'
            task.current_stage = None
            task.save(update_fields=['status', 'current_stage'])
            
            logger.info(f"流程已完成: task={task.id}")
            
        return flow_instance
    
    def cancel_flow(
        self,
        task,
        operator=None,
        remark: str = ''
    ) -> 'TaskFlowInstance':
        """
        取消流程
        
        Args:
            task: 任务实例
            operator: 操作人
            remark: 取消原因
        
        Returns:
            TaskFlowInstance: 取消的流程实例
        """
        from apps.flow_engine.models import TaskFlowInstance, StageActivity
        from tasks.models import TaskStageInstance
        
        with transaction.atomic():
            # 获取当前流程实例
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status not in ['active', 'draft']:
                raise InvalidTransitionError(f"流程状态不允许取消，当前状态：{flow_instance.status}")
            
            # 完成当前阶段（如果有）
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
            
            # 更新流程实例
            flow_instance.status = 'cancelled'
            flow_instance.completed_at = self.now
            flow_instance.save()
            
            # 更新任务状态
            task.status = 'blocked'
            task.save(update_fields=['status'])
            
            logger.info(f"流程已取消: task={task.id}")
            
        return flow_instance
    
    def suspend_flow(
        self,
        task,
        operator=None,
        remark: str = ''
    ) -> 'TaskFlowInstance':
        """
        暂停流程
        
        Args:
            task: 任务实例
            operator: 操作人
            remark: 暂停原因
        
        Returns:
            TaskFlowInstance: 暂停的流程实例
        """
        from apps.flow_engine.models import TaskFlowInstance, StageActivity
        from tasks.models import TaskStageInstance
        
        with transaction.atomic():
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status != 'active':
                raise InvalidTransitionError(f"流程状态不允许暂停，当前状态：{flow_instance.status}")
            
            # 完成当前阶段
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
            
            # 更新流程实例
            flow_instance.status = 'suspended'
            flow_instance.save()
            
            logger.info(f"流程已暂停: task={task.id}")
            
        return flow_instance
    
    def resume_flow(
        self,
        task,
        operator=None,
        remark: str = ''
    ) -> 'TaskFlowInstance':
        """
        恢复已暂停的流程
        
        Args:
            task: 任务实例
            operator: 操作人
            remark: 备注
        
        Returns:
            TaskFlowInstance: 恢复的流程实例
        """
        from apps.flow_engine.models import TaskFlowInstance, StageActivity
        from tasks.models import TaskStageInstance
        
        with transaction.atomic():
            try:
                flow_instance = task.flow_instance
            except TaskFlowInstance.DoesNotExist:
                raise FlowNotFoundError("任务未关联流程实例")
            
            if flow_instance.status != 'suspended':
                raise InvalidTransitionError(f"流程状态不允许恢复，当前状态：{flow_instance.status}")
            
            # 重新激活当前阶段
            current_stage = TaskStageInstance.objects.filter(
                task=task,
                status='in_progress'
            ).first()
            
            if current_stage is None:
                # 如果没有进行中的阶段，创建新的
                current_node = flow_instance.current_node
                if current_node:
                    deadline = self.now + timedelta(hours=current_node.duration_hours) if current_node.duration_hours else None
                    current_stage = TaskStageInstance.objects.create(
                        task=task,
                        template_node=current_node,
                        order=current_node.order,
                        assigned_to=self._resolve_responsible_user(current_node, task, operator),
                        status='in_progress',
                        started_at=self.now,
                        deadline=deadline
                    )
            
            if current_stage:
                StageActivity.objects.create(
                    stage_instance=current_stage,
                    operator=operator,
                    action_type='system',
                    content=f'流程已恢复: {remark}'
                )
            
            # 更新流程实例
            flow_instance.status = 'active'
            flow_instance.save()
            
            logger.info(f"流程已恢复: task={task.id}")
            
        return flow_instance
    
    def get_flow_progress(self, task) -> Dict[str, Any]:
        """
        获取流程进度
        
        Args:
            task: 任务实例
        
        Returns:
            Dict: 进度信息
        """
        from tasks.models import TaskStageInstance
        
        total_nodes = 0
        completed_nodes = 0
        
        if task.flow_instance and task.flow_instance.template:
            total_nodes = task.flow_instance.template.nodes.count()
        
        completed_nodes = TaskStageInstance.objects.filter(
            task=task,
            status='completed'
        ).count()
        
        progress = 0
        if total_nodes > 0:
            progress = int((completed_nodes / total_nodes) * 100)
        
        return {
            'total_nodes': total_nodes,
            'completed_nodes': completed_nodes,
            'progress': progress,
            'current_node': task.current_stage.name if task.current_stage else None,
            'flow_status': task.flow_instance.status if task.flow_instance else None
        }
