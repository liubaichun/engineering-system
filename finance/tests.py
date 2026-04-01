from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from projects.models import Project
from crm.models import Customer, Supplier
from .models import Income, Expense, InvoiceNew


class IncomeTests(TestCase):
    """收入记录测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='finuser', password='Test123456', role='finance')
        self.project = Project.objects.create(name='财务测试项目', status='ongoing')
        self.customer = Customer.objects.create(name='测试客户', status='active', contact='13800138000')
        self.client.force_authenticate(user=self.user)

    def test_create_income(self):
        """创建收入记录"""
        data = {
            'amount': 50000.00,
            'project': self.project.id,
            'customer': self.customer.id,
            'description': '测试收入'
        }
        response = self.client.post('/api/v1/finance/income/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.json()['amount']), 50000.00)

    def test_list_income(self):
        """列出收入记录"""
        Income.objects.create(amount=10000, project=self.project, customer=self.customer, operator=self.user)
        Income.objects.create(amount=20000, project=self.project, customer=self.customer, operator=self.user)
        response = self.client.get('/api/v1/finance/income/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 2)

    def test_update_income(self):
        """更新收入记录"""
        income = Income.objects.create(
            amount=10000, project=self.project, customer=self.customer, operator=self.user
        )
        data = {'amount': 15000}
        response = self.client.patch(f'/api/v1/finance/income/{income.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.json()['amount']), 15000.00)

    def test_delete_income(self):
        """删除收入记录"""
        income = Income.objects.create(
            amount=10000, project=self.project, customer=self.customer, operator=self.user
        )
        response = self.client.delete(f'/api/v1/finance/income/{income.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ExpenseTests(TestCase):
    """支出记录测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='finuser2', password='Test123456', role='finance')
        self.project = Project.objects.create(name='支出测试项目', status='ongoing')
        self.supplier = Supplier.objects.create(name='测试供应商', status='active', contact='13900139000')
        self.client.force_authenticate(user=self.user)

    def test_create_expense(self):
        """创建支出记录"""
        data = {
            'amount': 30000.00,
            'project': self.project.id,
            'supplier': self.supplier.id,
            'description': '测试支出'
        }
        response = self.client.post('/api/v1/finance/expense/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_expense(self):
        """列出支出记录"""
        Expense.objects.create(amount=5000, project=self.project, supplier=self.supplier, operator=self.user)
        response = self.client.get('/api/v1/finance/expense/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_expense(self):
        """更新支出记录"""
        expense = Expense.objects.create(
            amount=5000, project=self.project, supplier=self.supplier, operator=self.user
        )
        data = {'amount': 8000}
        response = self.client.patch(f'/api/v1/finance/expense/{expense.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class InvoiceTests(TestCase):
    """发票管理测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='invuser', password='Test123456', role='finance')
        self.project = Project.objects.create(name='发票测试项目', status='ongoing')
        self.client.force_authenticate(user=self.user)

    def test_create_invoice(self):
        """创建发票"""
        data = {
            'invoice_number': 'INV-2026-001',
            'project': self.project.id,
            'amount': 100000.00,
            'status': 'issued'
        }
        response = self.client.post('/api/v1/finance/invoice_new/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_invoice(self):
        """列出发票"""
        InvoiceNew.objects.create(
            invoice_number='INV-001', project=self.project, amount=50000, status='issued', created_by=self.user
        )
        response = self.client.get('/api/v1/finance/invoice_new/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invoice_status_update(self):
        """发票状态更新"""
        invoice = InvoiceNew.objects.create(
            invoice_number='INV-002', project=self.project, amount=50000, status='issued', created_by=self.user
        )
        data = {'status': 'paid'}
        response = self.client.patch(f'/api/v1/finance/invoice_new/{invoice.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FinanceBoundaryTests(TestCase):
    """财务边界测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='finboundary', password='Test123456', role='finance')
        self.project = Project.objects.create(name='边界测试', status='ongoing')
        self.client.force_authenticate(user=self.user)

    def test_negative_amount_income(self):
        """负数收入（当前无校验，记录为已知问题）"""
        data = {'amount': -10000, 'project': self.project.id}
        response = self.client.post('/api/v1/finance/income/', data)
        # 当前返回201，这是已知Bug
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_negative_amount_expense(self):
        """负数支出"""
        data = {'amount': -5000, 'project': self.project.id}
        response = self.client.post('/api/v1/finance/expense/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_zero_amount(self):
        """零金额"""
        data = {'amount': 0, 'project': self.project.id}
        response = self.client.post('/api/v1/finance/income/', data)
        # 当前无校验
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_very_large_amount(self):
        """超大金额"""
        data = {'amount': 999999999999.99, 'project': self.project.id}
        response = self.client.post('/api/v1/finance/income/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class FinancePermissionTests(TestCase):
    """财务权限测试"""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='finadmin', password='Test123456', role='admin')
        self.dev = User.objects.create_user(username='findev', password='Test123456', role='dev')
        self.finance = User.objects.create_user(username='finonly', password='Test123456', role='finance')
        self.project = Project.objects.create(name='权限测试', status='ongoing')

    def test_finance_role_can_access(self):
        """finance角色可访问"""
        self.client.force_authenticate(user=self.finance)
        response = self.client.get('/api/v1/finance/income/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dev_role_cannot_access(self):
        """dev角色不可访问财务"""
        self.client.force_authenticate(user=self.dev)
        response = self.client.get('/api/v1/finance/income/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_role_can_access(self):
        """admin角色可访问"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/finance/income/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
