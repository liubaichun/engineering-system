from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from .models import Notification


class NotificationTests(TestCase):
    """通知测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='notifyuser', password='Test123456')
        self.client.force_authenticate(user=self.user)

    def test_list_notifications(self):
        """获取通知列表"""
        Notification.objects.create(
            user=self.user,
            title='测试通知',
            content='这是一条测试通知'
        )
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_notification(self):
        """创建通知"""
        data = {
            'title': '新通知',
            'content': '通知内容',
            'notification_type': 'info'
        }
        response = self.client.post('/api/v1/notifications/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_mark_as_read(self):
        """标记已读"""
        notif = Notification.objects.create(
            user=self.user,
            title='未读通知',
            content='内容'
        )
        response = self.client.patch(f'/api/v1/notifications/{notif.id}/mark_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_unauthenticated_access(self):
        """未认证访问应被拒绝"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
