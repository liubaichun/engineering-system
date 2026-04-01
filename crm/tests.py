from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from .models import Customer, Supplier


class CustomerTests(TestCase):
    """客户管理测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='crmuser', password='Test123456')
        self.client.force_authenticate(user=self.user)

    def test_create_customer(self):
        """创建客户"""
        data = {
            'name': '测试客户',
            'contact': '13800138000',
            'status': 'active'
        }
        response = self.client.post('/api/v1/crm/customers/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], '测试客户')

    def test_list_customers(self):
        """列出客户"""
        Customer.objects.create(name='客户A', contact='13800001', status='active')
        Customer.objects.create(name='客户B', contact='13800002', status='potential')
        response = self.client.get('/api/v1/crm/customers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_customer(self):
        """更新客户"""
        customer = Customer.objects.create(name='旧客户', contact='13800001', status='potential')
        data = {'name': '新客户', 'status': 'active'}
        response = self.client.patch(f'/api/v1/crm/customers/{customer.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], '新客户')

    def test_delete_customer(self):
        """删除客户"""
        customer = Customer.objects.create(name='待删除', contact='13800001', status='potential')
        response = self.client.delete(f'/api/v1/crm/customers/{customer.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_customer_filter_by_status(self):
        """按状态筛选客户"""
        Customer.objects.create(name='活跃客户', status='active')
        Customer.objects.create(name='潜在客户', status='potential')
        response = self.client.get('/api/v1/crm/customers/?status=active')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_search(self):
        """客户搜索"""
        Customer.objects.create(name='北京公司', contact='13800001', status='active')
        response = self.client.get('/api/v1/crm/customers/?search=北京')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access(self):
        """未认证访问应被拒绝"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/crm/customers/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SupplierTests(TestCase):
    """供应商管理测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='supuser', password='Test123456')
        self.client.force_authenticate(user=self.user)

    def test_create_supplier(self):
        """创建供应商"""
        data = {
            'name': '测试供应商',
            'contact': '13900139000',
            'status': 'active'
        }
        response = self.client.post('/api/v1/crm/suppliers/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], '测试供应商')

    def test_list_suppliers(self):
        """列出供应商"""
        Supplier.objects.create(name='供应商A', contact='13900001', status='active')
        response = self.client.get('/api/v1/crm/suppliers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_supplier(self):
        """更新供应商"""
        supplier = Supplier.objects.create(name='旧供应商', contact='13900001', status='potential')
        data = {'name': '新供应商', 'status': 'active'}
        response = self.client.patch(f'/api/v1/crm/suppliers/{supplier.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_supplier(self):
        """删除供应商"""
        supplier = Supplier.objects.create(name='待删除', contact='13900001', status='potential')
        response = self.client.delete(f'/api/v1/crm/suppliers/{supplier.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_supplier_filter_by_status(self):
        """按状态筛选供应商"""
        Supplier.objects.create(name='活跃供应商', status='active')
        Supplier.objects.create(name='潜在供应商', status='potential')
        response = self.client.get('/api/v1/crm/suppliers/?status=active')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_supplier_search(self):
        """供应商搜索"""
        Supplier.objects.create(name='建材供应商', contact='13900001', status='active')
        response = self.client.get('/api/v1/crm/suppliers/?search=建材')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access(self):
        """未认证访问应被拒绝"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/crm/suppliers/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
