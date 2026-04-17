"""
流程引擎单元测试
"""
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class TestFlowEngineModels(TestCase):
    """测试流程引擎模型"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from tasks.models import TaskType, FlowTemplate, FlowNodeTemplate
        
        # 创建任务类型
        cls.task_type = TaskType.objects.create(
            name='测试任务类型',
            description='测试用任务类型'
        )
        
        # 创建流程模板
        cls.template = FlowTemplate.objects.create(
            name='测试流程模板',
            task_type=cls.task_type
        )
        
        # 创建起始节点
        cls.start_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='开始',
            order=0,
            is_start=True,
            duration_hours=24,
            allowed_actions=['complete']
        )
        
        # 创建中间节点
        cls.middle_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='处理中',
            order=1,
            duration_hours=48,
            allowed_actions=['complete', 'reject']
        )
        
        # 创建结束节点
        cls.end_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='完成',
            order=2,
            is_end=True,
            duration_hours=24,
            allowed_actions=['complete']
        )
        
        # 创建连线
        from tasks.models import FlowTransition
        FlowTransition.objects.create(
            template=cls.template,
            from_node=cls.start_node,
            to_node=cls.middle_node
        )
        FlowTransition.objects.create(
            template=cls.template,
            from_node=cls.middle_node,
            to_node=cls.end_node
        )
        
        # 创建项目
        from projects.models import Project
        cls.project = Project.objects.create(
            name='测试项目',
            manager=cls.user
        )
        
        # 创建任务
        from tasks.models import Task
        cls.task = Task.objects.create(
            name='测试任务',
            project=cls.project,
            manager=cls.user,
            flow_template=cls.template,
            status='pending'
        )
    
    def test_stage_activity_creation(self):
        """测试StageActivity创建"""
        from apps.flow_engine.models import StageActivity
        from tasks.models import TaskStageInstance
        
        # 创建阶段实例
        stage = TaskStageInstance.objects.create(
            task=self.task,
            template_node=self.start_node,
            order=0,
            assigned_to=self.user,
            status='in_progress'
        )
        
        # 创建活动记录
        activity = StageActivity.objects.create(
            stage_instance=stage,
            operator=self.user,
            action_type='create',
            content='测试活动'
        )
        
        self.assertEqual(activity.action_type, 'create')
        self.assertEqual(activity.content, '测试活动')
        self.assertIsNotNone(activity.created_at)
    
    def test_task_flow_instance_creation(self):
        """测试TaskFlowInstance创建"""
        from apps.flow_engine.models import TaskFlowInstance
        
        flow_instance = TaskFlowInstance.objects.create(
            task=self.task,
            template=self.template,
            status='active',
            initiator=self.user,
            current_node=self.start_node
        )
        
        self.assertEqual(flow_instance.status, 'active')
        self.assertEqual(flow_instance.task, self.task)
        self.assertEqual(flow_instance.current_node, self.start_node)


class TestFlowEngineCreateFlow(TestCase):
    """测试流程创建"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from tasks.models import TaskType, FlowTemplate, FlowNodeTemplate
        
        cls.task_type = TaskType.objects.create(name='测试任务类型')
        cls.template = FlowTemplate.objects.create(
            name='测试流程模板',
            task_type=cls.task_type
        )
        
        cls.start_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='开始',
            order=0,
            is_start=True,
            duration_hours=24
        )
        
        from projects.models import Project
        cls.project = Project.objects.create(
            name='测试项目',
            manager=cls.user
        )
        
        from tasks.models import Task
        cls.task = Task.objects.create(
            name='测试任务',
            project=cls.project,
            manager=cls.user,
            flow_template=cls.template,
            status='pending'
        )
    
    def test_create_flow_success(self):
        """测试成功创建流程"""
        from apps.flow_engine.engine import FlowEngine
        
        engine = FlowEngine()
        flow_instance = engine.create_flow(
            task=self.task,
            template=self.template,
            initiator=self.user
        )
        
        self.assertIsNotNone(flow_instance)
        self.assertEqual(flow_instance.status, 'active')
        self.assertEqual(flow_instance.task, self.task)
        self.assertEqual(flow_instance.current_node, self.start_node)
        
        # 验证任务已更新
        self.task.refresh_from_db()
        self.assertEqual(self.task.current_stage, self.start_node)
    
    def test_create_flow_no_start_node(self):
        """测试创建流程时没有起始节点"""
        from tasks.models import FlowNodeTemplate
        from apps.flow_engine.engine import FlowEngine, NodeNotFoundError
        
        # 创建一个没有起始节点的模板
        template = FlowTemplate.objects.create(
            name='无起始节点模板',
            task_type=self.task_type
        )
        FlowNodeTemplate.objects.create(
            template=template,
            name='中间节点',
            order=0,
            duration_hours=24
        )
        
        engine = FlowEngine()
        
        with self.assertRaises(NodeNotFoundError):
            engine.create_flow(task=self.task, template=template)


class TestFlowEngineTransition(TestCase):
    """测试流程流转"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from tasks.models import TaskType, FlowTemplate, FlowNodeTemplate, FlowTransition
        
        cls.task_type = TaskType.objects.create(name='测试任务类型')
        cls.template = FlowTemplate.objects.create(
            name='测试流程模板',
            task_type=cls.task_type
        )
        
        cls.start_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='开始',
            order=0,
            is_start=True,
            duration_hours=24
        )
        
        cls.middle_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='处理中',
            order=1,
            duration_hours=48
        )
        
        cls.end_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='完成',
            order=2,
            is_end=True,
            duration_hours=24
        )
        
        # 创建连线
        FlowTransition.objects.create(
            template=cls.template,
            from_node=cls.start_node,
            to_node=cls.middle_node
        )
        FlowTransition.objects.create(
            template=cls.template,
            from_node=cls.middle_node,
            to_node=cls.end_node
        )
        
        from projects.models import Project
        cls.project = Project.objects.create(
            name='测试项目',
            manager=cls.user
        )
        
        from tasks.models import Task
        cls.task = Task.objects.create(
            name='测试任务',
            project=cls.project,
            manager=cls.user,
            flow_template=cls.template,
            status='pending'
        )
    
    def test_transition_to_next_node(self):
        """测试流转到下一节点"""
        from apps.flow_engine.engine import FlowEngine
        
        engine = FlowEngine()
        
        # 先创建流程
        engine.create_flow(task=self.task, template=self.template, initiator=self.user)
        
        # 流转到下一节点
        new_stage = engine.transition_to(
            task=self.task,
            target_node=self.middle_node,
            operator=self.user,
            action='complete'
        )
        
        self.assertIsNotNone(new_stage)
        self.assertEqual(new_stage.template_node, self.middle_node)
        
        # 验证流程实例已更新
        self.task.refresh_from_db()
        self.assertEqual(self.task.current_stage, self.middle_node)
    
    def test_transition_flow_not_found(self):
        """测试流转时流程不存在"""
        from apps.flow_engine.engine import FlowEngine, FlowNotFoundError
        from tasks.models import Task
        
        # 创建一个没有流程的任务
        task = Task.objects.create(
            name='无流程任务',
            project=self.project,
            manager=self.user,
            status='pending'
        )
        
        engine = FlowEngine()
        
        with self.assertRaises(FlowNotFoundError):
            engine.transition_to(task=task)


class TestFlowEngineTransfer(TestCase):
    """测试流程转交"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cls.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        from tasks.models import TaskType, FlowTemplate, FlowNodeTemplate
        
        cls.task_type = TaskType.objects.create(name='测试任务类型')
        cls.template = FlowTemplate.objects.create(
            name='测试流程模板',
            task_type=cls.task_type
        )
        
        cls.start_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='开始',
            order=0,
            is_start=True,
            duration_hours=24
        )
        
        from projects.models import Project
        cls.project = Project.objects.create(
            name='测试项目',
            manager=cls.user
        )
        
        from tasks.models import Task
        cls.task = Task.objects.create(
            name='测试任务',
            project=cls.project,
            manager=cls.user,
            flow_template=cls.template,
            status='pending'
        )
    
    def test_transfer_success(self):
        """测试成功转交"""
        from apps.flow_engine.engine import FlowEngine
        
        engine = FlowEngine()
        
        # 先创建流程
        engine.create_flow(task=self.task, template=self.template, initiator=self.user)
        
        # 转交给另一个用户
        stage = engine.transfer_to(
            task=self.task,
            target_user=self.user2,
            operator=self.user,
            remark='测试转交'
        )
        
        self.assertIsNotNone(stage)
        self.assertEqual(stage.assigned_to, self.user2)


class TestFlowEngineComplete(TestCase):
    """测试流程完成"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from tasks.models import TaskType, FlowTemplate, FlowNodeTemplate
        
        cls.task_type = TaskType.objects.create(name='测试任务类型')
        cls.template = FlowTemplate.objects.create(
            name='测试流程模板',
            task_type=cls.task_type
        )
        
        cls.start_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='开始',
            order=0,
            is_start=True,
            is_end=True,
            duration_hours=24
        )
        
        from projects.models import Project
        cls.project = Project.objects.create(
            name='测试项目',
            manager=cls.user
        )
        
        from tasks.models import Task
        cls.task = Task.objects.create(
            name='测试任务',
            project=cls.project,
            manager=cls.user,
            flow_template=cls.template,
            status='pending'
        )
    
    def test_complete_flow(self):
        """测试完成流程"""
        from apps.flow_engine.engine import FlowEngine
        
        engine = FlowEngine()
        
        # 先创建流程
        engine.create_flow(task=self.task, template=self.template, initiator=self.user)
        
        # 完成流程
        flow_instance = engine.complete_flow(
            task=self.task,
            operator=self.user,
            remark='测试完成'
        )
        
        self.assertEqual(flow_instance.status, 'completed')
        
        # 验证任务状态已更新
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'completed')


class TestFlowProgress(TestCase):
    """测试流程进度"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from tasks.models import TaskType, FlowTemplate, FlowNodeTemplate
        
        cls.task_type = TaskType.objects.create(name='测试任务类型')
        cls.template = FlowTemplate.objects.create(
            name='测试流程模板',
            task_type=cls.task_type
        )
        
        cls.start_node = FlowNodeTemplate.objects.create(
            template=cls.template,
            name='开始',
            order=0,
            is_start=True,
            duration_hours=24
        )
        
        from projects.models import Project
        cls.project = Project.objects.create(
            name='测试项目',
            manager=cls.user
        )
        
        from tasks.models import Task
        cls.task = Task.objects.create(
            name='测试任务',
            project=cls.project,
            manager=cls.user,
            flow_template=cls.template,
            status='pending'
        )
    
    def test_get_flow_progress(self):
        """测试获取流程进度"""
        from apps.flow_engine.engine import FlowEngine
        
        engine = FlowEngine()
        
        # 创建流程
        engine.create_flow(task=self.task, template=self.template, initiator=self.user)
        
        # 获取进度
        progress = engine.get_flow_progress(self.task)
        
        self.assertEqual(progress['total_nodes'], 1)
        self.assertEqual(progress['completed_nodes'], 0)
        self.assertEqual(progress['current_node'], '开始')


class TestFlowEngineExceptions(TestCase):
    """测试流程引擎异常"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_flow_not_found_error(self):
        """测试FlowNotFoundError"""
        from apps.flow_engine.engine import FlowNotFoundError
        
        error = FlowNotFoundError("流程不存在")
        self.assertEqual(str(error), "流程不存在")
    
    def test_invalid_transition_error(self):
        """测试InvalidTransitionError"""
        from apps.flow_engine.engine import InvalidTransitionError
        
        error = InvalidTransitionError("无效的流转")
        self.assertEqual(str(error), "无效的流转")
    
    def test_transfer_error(self):
        """测试TransferError"""
        from apps.flow_engine.engine import TransferError
        
        error = TransferError("转交失败")
        self.assertEqual(str(error), "转交失败")


class TestCeleryTasks(TestCase):
    """测试Celery任务"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_check_overdue_flows(self):
        """测试超时检测任务"""
        from apps.flow_engine.tasks import check_overdue_flows
        
        # 执行任务
        result = check_overdue_flows()
        
        self.assertIn('flows_checked', result)
        self.assertIn('flows_overdue', result)
        self.assertIn('stages_checked', result)
        self.assertIn('stages_overdue', result)
    
    def test_sync_task_status(self):
        """测试状态同步任务"""
        from apps.flow_engine.tasks import sync_task_status
        
        result = sync_task_status()
        
        self.assertIn('tasks_checked', result)
        self.assertIn('tasks_updated', result)
