from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Income, Expense, InvoiceNew, FinancialRecord, Invoice
from .serializers import (
    IncomeSerializer, ExpenseSerializer,
    InvoiceNewSerializer, FinancialRecordSerializer, InvoiceSerializer
)
from .permissions import IsFinanceOnly
from operation_logs.models import OperationLog


class IncomeViewSet(viewsets.ModelViewSet):
    """收入视图集"""
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    permission_classes = [IsAuthenticated, IsFinanceOnly]

    def get_client_ip(self):
        """获取客户端IP"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def perform_create(self, serializer):
        # Auto-set operator from request user
        obj = serializer.save(operator=self.request.user)
        desc = f"创建了收入记录：金额 {obj.amount}"
        if obj.project:
            desc += f"，项目：{obj.project.name}"
        OperationLog.objects.create(
            user=self.request.user,
            action='create',
            model_name='Income',
            object_id=obj.id,
            description=desc,
            ip_address=self.get_client_ip()
        )

    def perform_update(self, serializer):
        obj = serializer.save()
        desc = f"更新了收入记录：金额 {obj.amount}"
        if obj.project:
            desc += f"，项目：{obj.project.name}"
        OperationLog.objects.create(
            user=self.request.user,
            action='update',
            model_name='Income',
            object_id=obj.id,
            description=desc,
            ip_address=self.get_client_ip()
        )

    def perform_destroy(self, instance):
        amount = instance.amount
        instance.delete()
        OperationLog.objects.create(
            user=self.request.user,
            action='delete',
            model_name='Income',
            object_id=instance.id,
            description=f"删除了收入记录：金额 {amount}",
            ip_address=self.get_client_ip()
        )


class ExpenseViewSet(viewsets.ModelViewSet):
    """支出视图集"""
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated, IsFinanceOnly]

    def get_client_ip(self):
        """获取客户端IP"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    def perform_create(self, serializer):
        # Auto-set operator from request user
        obj = serializer.save(operator=self.request.user)
        desc = f"创建了支出记录：金额 {obj.amount}"
        if obj.project:
            desc += f"，项目：{obj.project.name}"
        OperationLog.objects.create(
            user=self.request.user,
            action='create',
            model_name='Expense',
            object_id=obj.id,
            description=desc,
            ip_address=self.get_client_ip()
        )

    def perform_update(self, serializer):
        obj = serializer.save()
        desc = f"更新了支出记录：金额 {obj.amount}"
        if obj.project:
            desc += f"，项目：{obj.project.name}"
        OperationLog.objects.create(
            user=self.request.user,
            action='update',
            model_name='Expense',
            object_id=obj.id,
            description=desc,
            ip_address=self.get_client_ip()
        )

    def perform_destroy(self, instance):
        expense_id = instance.id
        amount = instance.amount
        instance.delete()
        OperationLog.objects.create(
            user=self.request.user,
            action='delete',
            model_name='Expense',
            object_id=expense_id,
            description=f"删除了支出记录：金额 {amount}",
            ip_address=self.get_client_ip()
        )


class InvoiceNewViewSet(viewsets.ModelViewSet):
    """发票视图集（新）"""
    queryset = InvoiceNew.objects.all()
    serializer_class = InvoiceNewSerializer
    permission_classes = [IsAuthenticated, IsFinanceOnly]


class FinancialRecordViewSet(viewsets.ModelViewSet):
    """财务记录视图集（兼容）"""
    queryset = FinancialRecord.objects.all()
    serializer_class = FinancialRecordSerializer
    permission_classes = [IsAuthenticated, IsFinanceOnly]


class InvoiceViewSet(viewsets.ModelViewSet):
    """发票视图集（兼容）"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsFinanceOnly]
