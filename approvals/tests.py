from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from projects.models import Project
from finance.models import Expense
from .models import ApprovalFlow, ApprovalNode


class ApprovalFlowTests(TestCase):
    """审批流测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='approver', password='Test123456')
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(name='审批测试项目', status='preparing')

    def test_create_approval_flow(self):
        """创建审批流"""
        data = {
            'name': '测试付款审批',
            'flow_type': 'payment',
            'amount': 50000
        }
        response = self.client.post('/api/v1/approvals/approvals/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], '测试付款审批')

    def test_approve_approval(self):
        """批准审批"""
        # 创建审批流
        flow = ApprovalFlow.objects.create(
            name='待批准审批',
            flow_type='payment',
            created_by=self.user
        )
        ApprovalNode.objects.create(
            flow=flow,
            approver=self.user,
            node_order=1,
            status='pending'
        )
        data = {'comment': '同意'}
        response = self.client.patch(f'/api/v1/approvals/approvals/{flow.id}/approve/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reject_approval(self):
        """拒绝审批"""
        flow = ApprovalFlow.objects.create(
            name='待拒绝审批',
            flow_type='payment',
            created_by=self.user
        )
        ApprovalNode.objects.create(
            flow=flow,
            approver=self.user,
            node_order=1,
            status='pending'
        )
        data = {'comment': '不同意'}
        response = self.client.patch(f'/api/v1/approvals/approvals/{flow.id}/reject/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access(self):
        """未认证访问应被拒绝"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/approvals/approvals/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_pending_node_cannot_approve(self):
        """非pending节点不能审批"""
        flow = ApprovalFlow.objects.create(
            name='已完成审批',
            flow_type='payment',
            status='approved',
            created_by=self.user
        )
        node = ApprovalNode.objects.create(
            flow=flow,
            approver=self.user,
            node_order=1,
            status='approved'
        )
        data = {'comment': '再次审批'}
        response = self.client.patch(f'/api/v1/approvals/approvals/{flow.id}/approve/', data)
        # 应该提示没有待审批节点
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
