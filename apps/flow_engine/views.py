"""
流程引擎 REST API 视图
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from apps.flow_engine.models import TaskFlowInstance, StageActivity
from apps.flow_engine.serializers import (
    TaskFlowInstanceSerializer,
    StageActivitySerializer,
    CreateFlowSerializer,
    TransitionFlowSerializer,
    TransferFlowSerializer,
    FlowProgressSerializer
)
from apps.flow_engine.engine import (
    FlowEngine, FlowNotFoundError, InvalidTransitionError,
    TransferError, NodeNotFoundError
)

logger = logging.getLogger(__name__)
User = get_user_model()


class FlowInstanceViewSet(viewsets.ModelViewSet):
    """
    流程实例视图集
    
    提供流程实例的 CRUD 操作以及流转、转交、完成等业务操作
    """
    queryset = TaskFlowInstance.objects.all()
    serializer_class = TaskFlowInstanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """支持过滤的查询集"""
        queryset = super().get_queryset()
        
        # 按任务过滤
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        # 按状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 按发起人过滤
        initiator_id = self.request.query_params.get('initiator_id')
        if initiator_id:
            queryset = queryset.filter(initiator_id=initiator_id)
        
        return queryset.select_related(
            'task', 'template', 'current_node', 'initiator'
        )
    
    @action(detail=False, methods=['post'])
    def create_flow(self, request):
        """
        发起流程
        
        POST /api/flow-engine/flows/create_flow/
        """
        serializer = CreateFlowSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        from tasks.models import Task
        
        task_id = serializer.validated_data['task_id']
        template_id = serializer.validated_data.get('template_id')
        context_data = serializer.validated_data.get('context_data', {})
        
        task = get_object_or_404(Task, id=task_id)
        
        # 获取模板
        template = None
        if template_id:
            from tasks.models import FlowTemplate
            template = get_object_or_404(FlowTemplate, id=template_id)
        
        engine = FlowEngine()
        
        try:
            flow_instance = engine.create_flow(
                task=task,
                template=template,
                initiator=request.user,
                context_data=context_data
            )
            
            response_serializer = TaskFlowInstanceSerializer(flow_instance)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except NodeNotFoundError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"创建流程失败: {e}")
            return Response(
                {'error': f'创建流程失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        """
        流转到下一节点
        
        POST /api/flow-engine/flows/{id}/transition/
        """
        flow_instance = self.get_object()
        
        serializer = TransitionFlowSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        engine = FlowEngine()
        
        try:
            new_stage = engine.transition_to(
                task=flow_instance.task,
                target_node_id=serializer.validated_data.get('target_node_id'),
                operator=request.user,
                action=serializer.validated_data.get('action', 'complete'),
                remark=serializer.validated_data.get('remark', '')
            )
            
            # 刷新流程实例
            flow_instance.refresh_from_db()
            
            response_serializer = TaskFlowInstanceSerializer(flow_instance)
            return Response({
                'message': '流转成功',
                'flow': response_serializer.data,
                'new_stage_id': new_stage.id
            })
            
        except FlowNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidTransitionError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"流转失败: {e}")
            return Response(
                {'error': f'流转失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """
        转交流程
        
        POST /api/flow-engine/flows/{id}/transfer/
        """
        flow_instance = self.get_object()
        
        serializer = TransferFlowSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        target_user_id = serializer.validated_data['target_user_id']
        target_user = get_object_or_404(User, id=target_user_id)
        
        engine = FlowEngine()
        
        try:
            engine.transfer_to(
                task=flow_instance.task,
                target_user=target_user,
                operator=request.user,
                remark=serializer.validated_data.get('remark', '')
            )
            
            flow_instance.refresh_from_db()
            response_serializer = TaskFlowInstanceSerializer(flow_instance)
            
            return Response({
                'message': '转交成功',
                'flow': response_serializer.data
            })
            
        except FlowNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except TransferError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"转交失败: {e}")
            return Response(
                {'error': f'转交失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        完成流程
        
        POST /api/flow-engine/flows/{id}/complete/
        """
        flow_instance = self.get_object()
        
        remark = request.data.get('remark', '')
        
        engine = FlowEngine()
        
        try:
            engine.complete_flow(
                task=flow_instance.task,
                operator=request.user,
                remark=remark
            )
            
            flow_instance.refresh_from_db()
            response_serializer = TaskFlowInstanceSerializer(flow_instance)
            
            return Response({
                'message': '流程已完成',
                'flow': response_serializer.data
            })
            
        except FlowNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"完成流程失败: {e}")
            return Response(
                {'error': f'完成流程失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        取消流程
        
        POST /api/flow-engine/flows/{id}/cancel/
        """
        flow_instance = self.get_object()
        
        remark = request.data.get('remark', '')
        
        engine = FlowEngine()
        
        try:
            engine.cancel_flow(
                task=flow_instance.task,
                operator=request.user,
                remark=remark
            )
            
            flow_instance.refresh_from_db()
            response_serializer = TaskFlowInstanceSerializer(flow_instance)
            
            return Response({
                'message': '流程已取消',
                'flow': response_serializer.data
            })
            
        except FlowNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidTransitionError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"取消流程失败: {e}")
            return Response(
                {'error': f'取消流程失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """
        暂停流程
        
        POST /api/flow-engine/flows/{id}/suspend/
        """
        flow_instance = self.get_object()
        
        remark = request.data.get('remark', '')
        
        engine = FlowEngine()
        
        try:
            engine.suspend_flow(
                task=flow_instance.task,
                operator=request.user,
                remark=remark
            )
            
            flow_instance.refresh_from_db()
            response_serializer = TaskFlowInstanceSerializer(flow_instance)
            
            return Response({
                'message': '流程已暂停',
                'flow': response_serializer.data
            })
            
        except FlowNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidTransitionError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"暂停流程失败: {e}")
            return Response(
                {'error': f'暂停流程失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """
        恢复流程
        
        POST /api/flow-engine/flows/{id}/resume/
        """
        flow_instance = self.get_object()
        
        remark = request.data.get('remark', '')
        
        engine = FlowEngine()
        
        try:
            engine.resume_flow(
                task=flow_instance.task,
                operator=request.user,
                remark=remark
            )
            
            flow_instance.refresh_from_db()
            response_serializer = TaskFlowInstanceSerializer(flow_instance)
            
            return Response({
                'message': '流程已恢复',
                'flow': response_serializer.data
            })
            
        except FlowNotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidTransitionError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"恢复流程失败: {e}")
            return Response(
                {'error': f'恢复流程失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        获取流程进度
        
        GET /api/flow-engine/flows/{id}/progress/
        """
        flow_instance = self.get_object()
        
        engine = FlowEngine()
        progress_data = engine.get_flow_progress(flow_instance.task)
        
        serializer = FlowProgressSerializer(progress_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """
        获取流程活动记录
        
        GET /api/flow-engine/flows/{id}/activities/
        """
        flow_instance = self.get_object()
        
        activities = StageActivity.objects.filter(
            stage_instance__task=flow_instance.task
        ).select_related(
            'stage_instance', 'operator'
        ).order_by('-created_at')
        
        # 支持分页
        page = self.paginate_queryset(activities)
        if page is not None:
            serializer = StageActivitySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = StageActivitySerializer(activities, many=True)
        return Response(serializer.data)


class StageActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    阶段活动记录视图集（只读）
    """
    queryset = StageActivity.objects.all()
    serializer_class = StageActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """支持过滤的查询集"""
        queryset = super().get_queryset()
        
        # 按阶段实例过滤
        stage_instance_id = self.request.query_params.get('stage_instance_id')
        if stage_instance_id:
            queryset = queryset.filter(stage_instance_id=stage_instance_id)
        
        # 按任务过滤
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(stage_instance__task_id=task_id)
        
        # 按操作类型过滤
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        return queryset.select_related('stage_instance', 'operator')
