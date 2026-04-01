from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from projects.models import Project
from .models import Task


class TaskCRUDTests(TestCase):
    """任务CRUD测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='taskuser', password='Test123456')
        self.project = Project.objects.create(name='测试项目', status='preparing')
        self.client.force_authenticate(user=self.user)

    def test_create_task(self):
        """创建任务"""
        data = {
            'name': '测试任务',
            'project': self.project.id,
            'status': 'pending',
            'priority': 'high'
        }
        response = self.client.post('/api/v1/tasks/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], '测试任务')

    def test_list_tasks(self):
        """列出任务"""
        Task.objects.create(name='任务A', project=self.project, status='pending')
        Task.objects.create(name='任务B', project=self.project, status='in_progress')
        response = self.client.get('/api/v1/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()['results']), 2)

    def test_filter_by_status(self):
        """按状态筛选"""
        Task.objects.create(name='待处理', project=self.project, status='pending')
        Task.objects.create(name='进行中', project=self.project, status='in_progress')
        response = self.client.get('/api/v1/tasks/?status=in_progress')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for t in response.json()['results']:
            self.assertEqual(t['status'], 'in_progress')

    def test_filter_by_project(self):
        """按项目筛选"""
        Task.objects.create(name='任务1', project=self.project, status='pending')
        response = self.client.get(f'/api/v1/tasks/?project={self.project.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_task(self):
        """更新任务"""
        task = Task.objects.create(name='旧任务', project=self.project, status='pending')
        data = {'name': '新任务', 'status': 'in_progress', 'progress': 50}
        response = self.client.patch(f'/api/v1/tasks/{task.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], '新任务')
        self.assertEqual(response.json()['progress'], 50)

    def test_delete_task(self):
        """删除任务"""
        task = Task.objects.create(name='待删除', project=self.project, status='pending')
        response = self.client.delete(f'/api/v1/tasks/{task.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_task_status_transitions(self):
        """任务状态流转"""
        task = Task.objects.create(name='状态测试', project=self.project, status='pending')
        # pending → in_progress
        self.client.patch(f'/api/v1/tasks/{task.id}/', {'status': 'in_progress'})
        task.refresh_from_db()
        self.assertEqual(task.status, 'in_progress')
        # in_progress → completed
        self.client.patch(f'/api/v1/tasks/{task.id}/', {'status': 'completed'})
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')

    def test_task_priority(self):
        """任务优先级"""
        task = Task.objects.create(name='优先级测试', project=self.project, priority='low')
        data = {'priority': 'high'}
        response = self.client.patch(f'/api/v1/tasks/{task.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['priority'], 'high')

    def test_unauthenticated_access(self):
        """未认证访问应被拒绝"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/tasks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_task_with_manager(self):
        """分配任务负责人"""
        data = {
            'name': '带负责人任务',
            'project': self.project.id,
            'manager': self.user.id,
            'status': 'pending'
        }
        response = self.client.post('/api/v1/tasks/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['manager'], self.user.id)
