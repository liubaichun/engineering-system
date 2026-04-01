from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Customer, Supplier, Client, Contract
from .serializers import (
    CustomerSerializer, SupplierSerializer,
    ClientSerializer, ContractSerializer
)


class CustomerViewSet(viewsets.ModelViewSet):
    """客户视图集"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    # 安全修复：要求用户登录才能访问
    permission_classes = [IsAuthenticated]


class SupplierViewSet(viewsets.ModelViewSet):
    """供应商视图集"""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    # 安全修复：要求用户登录才能访问
    permission_classes = [IsAuthenticated]


class ClientViewSet(viewsets.ModelViewSet):
    """客户视图集（兼容）"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    # 安全修复：要求用户登录才能访问
    permission_classes = [IsAuthenticated]


class ContractViewSet(viewsets.ModelViewSet):
    """合同视图集"""
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    # 安全修复：要求用户登录才能访问
    permission_classes = [IsAuthenticated]
