from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User


class UserRegistrationTests(TestCase):
    """用户注册测试"""

    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        """正常注册"""
        data = {
            'username': 'testuser',
            'password': 'Test123456',
            'password_confirm': 'Test123456'
        }
        response = self.client.post('/api/v1/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.json())
        self.assertEqual(response.json()['user']['role'], 'dev')

    def test_register_password_mismatch(self):
        """密码不一致"""
        data = {
            'username': 'testuser2',
            'password': 'Test123456',
            'password_confirm': 'WrongPassword'
        }
        response = self.client.post('/api/v1/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        """重复用户名"""
        User.objects.create_user(username='existing', password='Test123456')
        data = {
            'username': 'existing',
            'password': 'Test123456',
            'password_confirm': 'Test123456'
        }
        response = self.client.post('/api/v1/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_role_cannot_be_admin(self):
        """注册时role字段被忽略，强制为dev"""
        data = {
            'username': 'adminhack',
            'password': 'Test123456',
            'password_confirm': 'Test123456',
            'role': 'admin'  # 尝试伪造管理员
        }
        response = self.client.post('/api/v1/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['user']['role'], 'dev')


class UserLoginTests(TestCase):
    """用户登录测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='loginuser', password='Test123456')

    def test_login_success(self):
        """正常登录"""
        data = {'username': 'loginuser', 'password': 'Test123456'}
        response = self.client.post('/api/v1/users/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json())

    def test_login_wrong_password(self):
        """错误密码"""
        data = {'username': 'loginuser', 'password': 'WrongPassword'}
        response = self.client.post('/api/v1/users/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """不存在的用户"""
        data = {'username': 'nonexistent', 'password': 'Test123456'}
        response = self.client.post('/api/v1/users/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserMeTests(TestCase):
    """当前用户信息测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='meuser', password='Test123456')

    def test_me_with_auth(self):
        """带认证获取当前用户"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['username'], 'meuser')

    def test_me_without_auth(self):
        """无认证应被拒绝"""
        response = self.client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        """登出"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/users/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
