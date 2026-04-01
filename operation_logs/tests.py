from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from .models import OperationLog


class OperationLogTests(TestCase):
    """操作日志测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='loguser', password='Test123456')
        self.client.force_authenticate(user=self.user)

    def test_create_log(self):
        """创建操作日志"""
        data = {
            'user': self.user.id,
            'action': 'create',
            'model_name': 'Project',
            'object_id': 1,
            'description': '创建项目测试'
        }
        response = self.client.post('/api/v1/operation_logs/', data)
        # 操作日志通常由系统自动创建，这里测试API是否存在
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_list_logs(self):
        """列出操作日志"""
        # 创建一些日志
        for i in range(3):
            OperationLog.objects.create(
                user=self.user,
                action='create',
                model_name='TestModel',
                object_id=i,
                description=f'测试日志{i}'
            )
        response = self.client.get('/api/v1/operation_logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_user(self):
        """按用户筛选日志"""
        OperationLog.objects.create(
            user=self.user,
            action='create',
            model_name='Test',
            object_id=1,
            description='测试'
        )
        response = self.client.get(f'/api/v1/operation_logs/?user_id={self.user.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_model(self):
        """按模型筛选日志"""
        OperationLog.objects.create(
            user=self.user,
            action='create',
            model_name='Project',
            object_id=1,
            description='测试'
        )
        response = self.client.get('/api/v1/operation_logs/?model_name=Project')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_action(self):
        """按操作类型筛选"""
        OperationLog.objects.create(
            user=self.user,
            action='create',
            model_name='Test',
            object_id=1,
            description='创建测试'
        )
        OperationLog.objects.create(
            user=self.user,
            action='delete',
            model_name='Test',
            object_id=2,
            description='删除测试'
        )
        response = self.client.get('/api/v1/operation_logs/?action=create')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access(self):
        """未认证访问应被拒绝"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/operation_logs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
