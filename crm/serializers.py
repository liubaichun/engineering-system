from rest_framework import serializers
from .models import Customer, Supplier, Client, Contract


class CustomerSerializer(serializers.ModelSerializer):
    """客户序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'contact', 'phone', 'email', 'status', 'status_display',
            'address', 'remark', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SupplierSerializer(serializers.ModelSerializer):
    """供应商序列化器"""
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact', 'phone', 'email', 'category',
            'address', 'remark', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClientSerializer(serializers.ModelSerializer):
    """客户序列化器（兼容）"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'code', 'contact_person', 'contact_phone',
            'contact_email', 'address', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContractSerializer(serializers.ModelSerializer):
    """合同序列化器"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Contract
        fields = [
            'id', 'client', 'client_name', 'name', 'code', 'type', 'type_display',
            'amount', 'signed_date', 'start_date', 'end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
